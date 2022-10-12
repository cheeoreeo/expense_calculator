import calendar
from datetime import datetime

from sqlalchemy.orm import query

from db.models import Expense
from db.queries import get_user_categories, bulk_create_expenses


def define_category(user_id: int, title: str) -> tuple:
    categories = get_user_categories(user_id=user_id)
    for category in categories:
        if title in category.costs:
            return category.title, category.id, category.is_auto
    return 'Разное', 0, False


def parse_expense(text: str) -> dict:
    expense = text.strip().split()
    try:
        result = {
            'cost': int(expense[0]),
            'name': expense[1],
            'comment': ' '.join(expense[2:])
        }
    except:
        return {}
    return result


def convert_categories_list(categories: list) -> str:
    result = ''
    status_filters = {'daily': 'Ежедневно', "weekly": "Еженедельно", "monthly": "Ежемесячно", "weekdays": "По будням"}
    for category in categories:
        costs = ','.join(category[0])
        status = status_filters[category[1]]
        is_auto = category[2]
        title = category[3]
        result += f'{title}\nТраты: {costs}\nСтатус: {status}\nАвто: {is_auto}\n\n'
    return result


def aggregate_expenses(expenses: query) -> dict:
    result = {}
    for expense in expenses:
        cost, category = expense.cost, expense.category.title
        if category in result:
            result[category] += cost
        else:
            result[category] = cost
    return result


def get_last_expenses(expenses: query) -> str:
    result = ''
    count = 0
    for expense in expenses:
        count += 1
        cost, category, name = expense.cost, expense.category.title, expense.name
        result += f'/del{count}: {cost,name,category}\n'
    return result


def convert_aggregate_expenses(expenses: dict) -> str:
    result = ''
    for k, v in expenses.items():
        result += f'{k}: {v}\n'
    return result


def parse_income(text: str) -> dict:
    result = {'name': 'Undefined', 'value': 0}
    if text[0] == '+':
        splitted_text = text.split()
        result['value'] = splitted_text[0][1:]
        result['name'] = ' '.join(splitted_text[1:])
    return result


def get_weekdays(start_day, last_day: int, year: int, month: int) -> list:
    result = []
    excluded_days = ('Saturday', 'Sunday')
    for day_number in range(start_day, last_day + 1):
        day = datetime(year, month, day_number)
        weekday = calendar.day_name[day.weekday()]
        if weekday not in excluded_days:
            result.append(day)
    return result


def get_days(start_day, last_day: int, year: int, month: int) -> list:
    result = []
    for day_number in range(start_day, last_day + 1):
        result.append(datetime(year, month, day_number))
    return result


def get_month_lastday(month: int, year: int) -> int:
    return calendar.monthrange(year, month)[1]


def update_auto_expenses(cost: int, name: str, user_id: int, category_id: int,
                         period: str, start_day: int, year: int, month: int) -> None:
    last_day = get_month_lastday(month, year)
    period_filters = {
        'daily': get_days(start_day, last_day, year, month),
        'weekdays': get_weekdays(start_day, last_day, year, month)
    }
    days = period_filters[period]
    expenses = [Expense(cost=cost, name=name, user_id=user_id, category_id=category_id, date=day) for
                day in days]
    bulk_create_expenses(expenses)


def convert_income(incomes: query) -> str:
    result = ''
    for income in incomes:
        result += f'{income.name if income.name else "Безымянный"}: {income.value}\n'
    return result
