from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # "income" or "expense"

    transactions = relationship("Transaction", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name} ({self.type})>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    amount = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)  # "income" or "expense"
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    payment_method = Column(String(50), nullable=True)
    tags = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    recurring_id = Column(Integer, nullable=True)  # for future recurring support

    category = relationship("Category", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.date} {self.amount} {self.type}>"


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Float, nullable=False)          # monthly budget amount
    cycle_day = Column(Integer, nullable=False)     # 1–28 (budget reset day)
    created_at = Column(String(10), nullable=True)  # "YYYY-MM-DD" (optional / future use)

    category = relationship("Category")

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)

class RecurringRule(Base):
    __tablename__ = "recurring_rules"

    id = Column(Integer, primary_key=True)
    transaction_type = Column(String, nullable=False)   # income or expense
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    payment_method = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    note = Column(String, nullable=True)

    every = Column(String, nullable=False)              # daily / weekly / monthly / custom-days
    interval = Column(Integer, default=1)               # 1 = every month, 2 = every 2 months
    next_date = Column(String, nullable=False) 