from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import date, datetime, timedelta
import os
import shutil
import csv
import json

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from .models import Base, Transaction, Category, Budget, RecurringRule, Setting

DATABASE_URL = "sqlite:///spent.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ========== DB INIT ==========

def init_db() -> None:
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        defaults = [
            ("General", "expense"),
            ("Food", "expense"),
            ("Transport", "expense"),
            ("Shopping", "expense"),
            ("Salary", "income"),
            ("Freelance", "income"),
            ("Other", "income"),
        ]

        for name, type_ in defaults:
            exists = session.execute(
                select(Category).where(Category.name == name, Category.type == type_)
            ).scalar_one_or_none()

            if not exists:
                session.add(Category(name=name, type=type_))

        session.commit()

    # Apply any recurring rules that are due (generate transactions)
    try:
        apply_recurring_rules()
    except Exception:
        # don't crash the app during init if recurring logic fails
        pass


# ========== CATEGORY HELPERS ==========

def get_categories(type_filter: Optional[str] = None) -> List[Dict]:
    with SessionLocal() as session:
        stmt = select(Category)
        if type_filter:
            stmt = stmt.where(Category.type == type_filter)
        stmt = stmt.order_by(Category.type.asc(), Category.name.asc())

        rows = session.execute(stmt).scalars().all()
        return [{"id": c.id, "name": c.name, "type": c.type} for c in rows]


def create_category(name: str, type_: str) -> bool:
    name = (name or "").strip()
    type_ = (type_ or "").strip().lower()
    if not name or type_ not in ("income", "expense"):
        return False

    with SessionLocal() as session:
        exists = session.execute(
            select(Category).where(Category.name == name, Category.type == type_)
        ).scalar_one_or_none()
        if exists:
            return False

        session.add(Category(name=name, type=type_))
        session.commit()
        return True


def update_category(cat_id: int, new_name: str, new_type: Optional[str] = None) -> bool:
    new_name = (new_name or "").strip()
    if not new_name:
        return False

    with SessionLocal() as session:
        cat = session.get(Category, cat_id)
        if not cat:
            return False

        cat.name = new_name
        if new_type:
            nt = new_type.strip().lower()
            if nt in ("income", "expense"):
                cat.type = nt

        session.commit()
        return True


def delete_category(cat_id: int) -> bool:
    with SessionLocal() as session:
        cat = session.get(Category, cat_id)
        if not cat:
            return False

        session.query(Transaction).filter(
            Transaction.category_id == cat_id
        ).update({"category_id": None})

        session.delete(cat)
        session.commit()
        return True


# ========== TRANSACTIONS ==========

def add_transaction(data: Dict) -> None:
    with SessionLocal() as session:
        category = Category
        category = session.execute(
            select(Category).where(
                Category.name == data["category"], Category.type == data["type"]
            )
        ).scalar_one_or_none()

        if not category:
            category = Category(name=data["category"], type=data["type"])
            session.add(category)
            session.flush()

        tx = Transaction(
            date=data["date"],
            amount=data["amount"],
            type=data["type"],
            category_id=category.id,
            payment_method=data.get("payment_method", ""),
            tags=data.get("tags", ""),
            note=data.get("note", ""),
        )
        session.add(tx)
        session.commit()


def list_transactions() -> List[Dict]:
    with SessionLocal() as session:
        stmt = (
            select(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        rows = session.execute(stmt).all()

        return [
            {
                "id": tx.id,
                "date": tx.date,
                "amount": tx.amount,
                "type": tx.type,
                "category": cat.name if cat else "",
                "payment_method": tx.payment_method or "",
                "tags": tx.tags or "",
                "note": tx.note or "",
            }
            for tx, cat in rows
        ]


def filter_transactions(date_from=None, date_to=None, category=None, type_=None) -> List[Dict]:
    with SessionLocal() as session:
        stmt = (
            select(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
        )

        if date_from:
            stmt = stmt.where(Transaction.date >= date_from)
        if date_to:
            stmt = stmt.where(Transaction.date <= date_to)
        if category and category.lower() != "all":
            stmt = stmt.where(Category.name == category)
        if type_ and type_.lower() != "all":
            stmt = stmt.where(Transaction.type == type_.lower())

        rows = session.execute(stmt).all()
        return [
            {
                "id": tx.id,
                "date": tx.date,
                "amount": tx.amount,
                "type": tx.type,
                "category": cat.name if cat else "",
                "payment_method": tx.payment_method or "",
                "tags": tx.tags or "",
                "note": tx.note or "",
            }
            for tx, cat in rows
        ]


def get_totals() -> Tuple[float, float, float]:
    with SessionLocal() as session:
        income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.type == "income"
        )
        income = session.execute(income_stmt).scalar_one() or 0.0

        expense_stmt = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.type == "expense"
        )
        expense = session.execute(expense_stmt).scalar_one() or 0.0

        balance = income - expense
        return float(income), float(expense), float(balance)


# ========== REPORTS ==========

def get_expense_by_category_summary() -> Dict[str, float]:
    with SessionLocal() as session:
        stmt = (
            select(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .where(Transaction.type == "expense")
        )
        rows = session.execute(stmt).all()
        totals: Dict[str, float] = defaultdict(float)

        for tx, cat in rows:
            name = cat.name if cat else "Uncategorized"
            totals[name] += tx.amount

        return dict(totals)


def get_monthly_income_expense_summary() -> List[Dict[str, float]]:
    with SessionLocal() as session:
        txs = session.execute(select(Transaction)).scalars().all()
        income_map = defaultdict(float)
        expense_map = defaultdict(float)

        for tx in txs:
            if not tx.date:
                continue
            month = tx.date[:7]
            if tx.type == "income":
                income_map[month] += tx.amount
            elif tx.type == "expense":
                expense_map[month] += tx.amount

        months = sorted(set(list(income_map.keys()) + list(expense_map.keys())))
        return [
            {
                "month": m,
                "income": float(income_map.get(m, 0.0)),
                "expense": float(expense_map.get(m, 0.0)),
            }
            for m in months
        ]


def get_balance_timeseries() -> List[Dict[str, float]]:
    with SessionLocal() as session:
        txs = session.execute(
            select(Transaction).order_by(Transaction.date.asc(), Transaction.id.asc())
        ).scalars().all()

        balance = 0.0
        points = []

        for tx in txs:
            balance = balance + tx.amount if tx.type == "income" else balance - tx.amount
            points.append({"date": tx.date, "balance": float(balance)})

        compressed = {}
        for p in points:
            compressed[p["date"]] = p["balance"]

        return [{"date": d, "balance": compressed[d]} for d in sorted(compressed.keys())]


# ========== BUDGETS (CORRECTED) ==========

def _get_cycle_window(cycle_day: int, ref_date: Optional[date] = None) -> Tuple[str, str]:
    if ref_date is None:
        ref_date = date.today()

    d = min(max(int(cycle_day), 1), 28)
    y, m = ref_date.year, ref_date.month

    if ref_date.day >= d:
        start = date(y, m, d)
        end = date(y + 1, 1, d) if m == 12 else date(y, m + 1, d)
    else:
        start = date(y - 1, 12, d) if m == 1 else date(y, m - 1, d)
        end = date(y, m, d)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def get_budgets() -> List[Dict]:
    with SessionLocal() as session:
        stmt = (
            select(Budget, Category)
            .join(Category, Budget.category_id == Category.id)
            .order_by(Category.type.asc(), Category.name.asc())
        )

        rows = session.execute(stmt).all()
        return [
            {
                "id": b.id,
                "category_id": b.category_id,
                "category_name": c.name,
                "type": c.type,
                "amount": float(b.amount),
                "cycle_day": int(b.cycle_day),
            }
            for b, c in rows
        ]


def create_budget(category_id: int, amount: float, cycle_day: int) -> bool:
    if amount <= 0:
        return False
    with SessionLocal() as session:
        exists = session.execute(
            select(Budget).where(Budget.category_id == category_id)
        ).scalar_one_or_none()
        if exists:
            return False

        b = Budget(category_id=category_id, amount=amount, cycle_day=cycle_day)
        session.add(b)
        session.commit()
        return True


def update_budget(budget_id: int, category_id: int, amount: float, cycle_day: int) -> bool:
    with SessionLocal() as session:
        b = session.get(Budget, budget_id)
        if not b:
            return False

        b.category_id = category_id
        b.amount = amount
        b.cycle_day = cycle_day
        session.commit()
        return True


def delete_budget(budget_id: int) -> bool:
    with SessionLocal() as session:
        b = session.get(Budget, budget_id)
        if not b:
            return False
        session.delete(b)
        session.commit()
        return True


def get_budgets_with_status(ref_date: Optional[date] = None) -> List[Dict]:
    if ref_date is None:
        ref_date = date.today()

    with SessionLocal() as session:
        stmt = select(Budget, Category).join(Category, Budget.category_id == Category.id)
        rows = session.execute(stmt).all()

        result: List[Dict] = []
        for b, cat in rows:
            start_str, end_str = _get_cycle_window(b.cycle_day, ref_date)

            spent = (
                session.execute(
                    select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                        Transaction.type == "expense",
                        Transaction.category_id == b.category_id,
                        Transaction.date >= start_str,
                        Transaction.date < end_str,
                    )
                ).scalar_one()
                or 0.0
            )

            remaining = float(b.amount) - float(spent)
            percent = float(spent) / float(b.amount) * 100.0 if b.amount else 0.0

            result.append(
                {
                    "id": b.id,
                    "category_id": b.category_id,
                    "category_name": cat.name,
                    "type": cat.type,
                    "amount": float(b.amount),
                    "cycle_day": int(b.cycle_day),
                    "spent": float(spent),
                    "remaining": float(remaining),
                    "percent": float(percent),
                    "overspent": remaining < 0,
                }
            )

        return result


def any_budget_overspent(ref_date: Optional[date] = None) -> bool:
    return any(b["overspent"] for b in get_budgets_with_status(ref_date))


# ========== TRANSACTION EDIT / DELETE ==========

def get_transaction(tx_id: int) -> Optional[Dict]:
    with SessionLocal() as session:
        tx = session.get(Transaction, tx_id)
        if not tx:
            return None
        cat = session.get(Category, tx.category_id) if tx.category_id else None
        return {
            "id": tx.id,
            "date": tx.date,
            "amount": tx.amount,
            "type": tx.type,
            "category": cat.name if cat else "",
            "payment_method": tx.payment_method or "",
            "tags": tx.tags or "",
            "note": tx.note or "",
            "recurring_id": tx.recurring_id,
        }


def update_transaction(tx_id: int, data: Dict) -> bool:
    with SessionLocal() as session:
        tx = session.get(Transaction, tx_id)
        if not tx:
            return False

        tx.date = data.get("date", tx.date)
        tx.amount = data.get("amount", tx.amount)
        tx.type = data.get("type", tx.type)

        # ensure category exists or set to None
        category_name = data.get("category")
        if category_name:
            cat = session.execute(
                select(Category).where(Category.name == category_name)
            ).scalar_one_or_none()
            if not cat:
                cat = Category(name=category_name, type=data.get("type", tx.type))
                session.add(cat)
                session.flush()
            tx.category_id = cat.id

        tx.payment_method = data.get("payment_method", tx.payment_method)
        tx.tags = data.get("tags", tx.tags)
        tx.note = data.get("note", tx.note)
        session.commit()
        return True


def delete_transaction(tx_id: int) -> bool:
    with SessionLocal() as session:
        tx = session.get(Transaction, tx_id)
        if not tx:
            return False
        session.delete(tx)
        session.commit()
        return True


# ========== IMPORT / EXPORT / BACKUP ==========

def export_transactions_csv(path: str) -> None:
    rows = list_transactions()
    fieldnames = ["id", "date", "amount", "type", "category", "payment_method", "tags", "note"]
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})


def import_transactions_csv(path: str) -> int:
    added = 0
    with open(path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data = {
                    "date": row.get("date") or datetime.today().strftime("%Y-%m-%d"),
                    "amount": float(row.get("amount", 0)),
                    "type": row.get("type", "expense"),
                    "category": row.get("category", ""),
                    "payment_method": row.get("payment_method", ""),
                    "tags": row.get("tags", ""),
                    "note": row.get("note", ""),
                }
                add_transaction(data)
                added += 1
            except Exception:
                continue
    return added


def export_transactions_json(path: str) -> None:
    rows = list_transactions()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def import_transactions_json(path: str) -> int:
    added = 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        for row in data:
            try:
                add_transaction(row)
                added += 1
            except Exception:
                continue
    return added


def backup_db(backup_path: str) -> bool:
    try:
        src = os.path.abspath("spent.db")
        shutil.copy2(src, backup_path)
        return True
    except Exception:
        return False


def restore_db(backup_path: str) -> bool:
    try:
        dst = os.path.abspath("spent.db")
        shutil.copy2(backup_path, dst)
        return True
    except Exception:
        return False


# ========== SETTINGS ==========

def set_setting(key: str, value: str) -> None:
    with SessionLocal() as session:
        s = session.get(Setting, key)
        if not s:
            s = Setting(key=key, value=value)
            session.add(s)
        else:
            s.value = value
        session.commit()


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with SessionLocal() as session:
        s = session.get(Setting, key)
        return s.value if s else default


# ========== RECURRING RULES ==========

def create_recurring_rule(data: Dict) -> int:
    """Create a recurring rule and return its id."""
    with SessionLocal() as session:
        # resolve category
        cat = None
        if data.get("category"):
            cat = session.execute(
                select(Category).where(Category.name == data["category"])
            ).scalar_one_or_none()
        if not cat and data.get("category"):
            cat = Category(name=data["category"], type=data.get("type", "expense"))
            session.add(cat)
            session.flush()

        rr = RecurringRule(
            transaction_type=data.get("type", "expense"),
            amount=data.get("amount", 0.0),
            category_id=cat.id if cat else None,
            payment_method=data.get("payment_method"),
            tags=data.get("tags"),
            note=data.get("note"),
            every=data.get("every", "monthly"),
            interval=int(data.get("interval", 1)),
            next_date=data.get("next_date", datetime.today().strftime("%Y-%m-%d")),
        )
        session.add(rr)
        session.commit()
        return rr.id


def list_recurring_rules() -> List[Dict]:
    with SessionLocal() as session:
        rows = session.execute(select(RecurringRule)).scalars().all()
        result = []
        for r in rows:
            cat = session.get(Category, r.category_id) if r.category_id else None
            result.append(
                {
                    "id": r.id,
                    "type": r.transaction_type,
                    "amount": float(r.amount),
                    "category": cat.name if cat else "",
                    "payment_method": r.payment_method,
                    "tags": r.tags,
                    "note": r.note,
                    "every": r.every,
                    "interval": int(r.interval),
                    "next_date": r.next_date,
                }
            )
        return result


def delete_recurring_rule(rule_id: int) -> bool:
    with SessionLocal() as session:
        r = session.get(RecurringRule, rule_id)
        if not r:
            return False
        session.delete(r)
        session.commit()
        return True


def _advance_next_date(current: str, every: str, interval: int) -> str:
    try:
        d = datetime.strptime(current, "%Y-%m-%d").date()
    except Exception:
        d = date.today()

    if every in ("weekly", "week"):
        nd = d + timedelta(weeks=interval)
    elif every in ("yearly", "year"):
        # naive year add
        nd = date(d.year + interval, d.month, min(d.day, 28))
    else:
        # default monthly
        month = d.month - 1 + interval
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, 28)
        nd = date(year, month, day)

    return nd.strftime("%Y-%m-%d")


def apply_recurring_rules(up_to_date: Optional[str] = None) -> int:
    """Generate due transactions for recurring rules up to `up_to_date` (YYYY-MM-DD).
    Returns number of transactions created."""
    created = 0
    if up_to_date is None:
        up_to_date = datetime.today().strftime("%Y-%m-%d")

    with SessionLocal() as session:
        rules = session.execute(select(RecurringRule)).scalars().all()
        for r in rules:
            # generate while next_date <= up_to_date
            while r.next_date <= up_to_date:
                # create transaction
                tx = Transaction(
                    date=r.next_date,
                    amount=r.amount,
                    type=r.transaction_type,
                    category_id=r.category_id,
                    payment_method=r.payment_method or "",
                    tags=r.tags or "",
                    note=r.note or "",
                    recurring_id=r.id,
                )
                session.add(tx)
                created += 1

                # advance rule
                r.next_date = _advance_next_date(r.next_date, r.every, int(r.interval or 1))

        session.commit()

    return created


# ========== WIPE DATA ==========

def wipe_all_data() -> bool:
    """Delete all transactions, budgets, and recurring rules. Keep default categories."""
    try:
        from sqlalchemy import delete
        with SessionLocal() as session:
            # delete all transactions
            session.execute(delete(Transaction))
            # delete all budgets
            session.execute(delete(Budget))
            # delete all recurring rules
            session.execute(delete(RecurringRule))
            session.commit()
        return True
    except Exception as e:
        return False
