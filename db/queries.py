from datetime import datetime
from sqlalchemy import extract
from sqlalchemy.orm import query, joinedload
from sqlalchemy.sql import func
from db.engine import get_db
from db.models import User, Category, Expense, UserCategory, Income

session = get_db()


def get_user(user_id: int) -> None:
    return session.query(User).where(User.id == user_id).first()


def create_user(user_id: int, first_name: str, username: str) -> None:
    new_user = User(id=user_id, first_name=first_name, username=username)
    session.add(new_user)
    session.commit()


def get_expenses(user_id: int, month: int, date: datetime) -> query:
    return session.query(Expense).options(joinedload("category")) \
        .filter(Expense.user_id == user_id,
                extract('month', Expense.date) == month,
                extract('year', Expense.date) == date.year,
                extract('day', Expense.date) <= date.day) \
        .order_by(Expense.id.desc()).all()


def del_last_expense(user_id: int) -> Expense:
    last_expense = session.query(Expense).options(joinedload("category")) \
        .filter(Expense.user_id == user_id) \
        .order_by(Expense.id.desc()) \
        .limit(1).scalar()
    session.delete(last_expense)
    session.commit()
    return last_expense


def create_expense(cost: int, name: str, user_id: int, date: datetime, category_id: int, comment: str = None) -> None:
    new_expense = Expense(cost=cost, name=name, user_id=user_id, date=date, comment=comment, category_id=category_id)
    session.add(new_expense)
    session.commit()


def update_expense(*args, **kwargs) -> None:
    expense = session.query(Expense) \
        .where(Expense.user_id == kwargs['user_id'],
               Expense.name == kwargs['name'],
               Expense.category_id == kwargs['category_id'],
               extract('month', Expense.date) == kwargs['date'].month,
               extract('year', Expense.date) == kwargs['date'].year,
               extract('day', Expense.date) == kwargs['date'].day).order_by('id').first()
    expense.cost = kwargs['cost']
    expense.name = kwargs['name']
    expense.comment = kwargs['comment']
    expense.date = kwargs['date']
    session.commit()


def delete_future_expenses(user_id: int, category_id: int, _date: datetime):
    session.query(Expense).filter(Expense.user_id == user_id,
                                  Expense.category_id == category_id, Expense.date > _date).delete()
    session.commit()


def bulk_create_expenses(objects: list) -> None:
    session.bulk_save_objects(objects)
    session.commit()


def get_category(title: str) -> Category:
    return session.query(Category).where(Category.title == title).first()


def delete_user_category(user_id: int, category_id: int) -> None:
    session.query(UserCategory).where(UserCategory.user_id == user_id, UserCategory.category_id == category_id).delete()
    session.commit()


def create_category(title: str) -> Category:
    new_category = Category(title=title)
    session.add(new_category)
    session.flush()
    return new_category


def get_user_category(user_id: int, category_id: int) -> UserCategory:
    return session.query(UserCategory) \
        .where(UserCategory.user_id == user_id, UserCategory.category_id == category_id).first()


def get_user_categories(user_id: int) -> query:
    return session.query(UserCategory.costs, UserCategory.status, UserCategory.is_auto, Category.title, Category.id) \
        .where(Category.id == UserCategory.category_id, UserCategory.user_id == user_id).all()


def create_user_category(user_id: int, category_id: int, costs: list, status: str, is_auto: bool) -> None:
    new_user_category = UserCategory(user_id=user_id, category_id=category_id,
                                     costs=costs, status=status, is_auto=is_auto)
    session.add(new_user_category)
    session.commit()


def update_user_category(user_id: int, category_id: int, costs: list, status: str, is_auto: bool) -> None:
    user_category = session.query(UserCategory) \
        .where(UserCategory.user_id == user_id, UserCategory.category_id == category_id).first()
    user_category.costs = costs
    user_category.status = status
    user_category.is_auto = is_auto
    session.commit()


def add_income(user_id: int, date: datetime, name: str, value: int) -> None:
    new_income = Income(user_id=user_id, date=date, name=name, value=value)
    session.add(new_income)
    session.commit()


def get_income_sum(user_id: int, date: datetime) -> int:
    return session.query(func.sum(Income.value)).filter(Income.user_id == user_id,
                                                        extract('month', Income.date) == date.month,
                                                        extract('year', Income.date) == date.year).scalar()


def get_income(user_id: int, date: datetime) -> query:
    return session.query(Income).filter(Income.user_id == user_id,
                                        extract('month', Income.date) == date.month,
                                        extract('year', Income.date) == date.year).all()
