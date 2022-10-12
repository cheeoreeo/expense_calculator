from aiogram.dispatcher.filters.state import State, StatesGroup


class CategoryForm(StatesGroup):
    title = State()
    costs = State()
    period = State()
    budget = State()
    is_auto = State()
    price = State()


class DeleteCategoryForm(StatesGroup):
    category_id = State()


class AddExpenseForm(StatesGroup):
    expense = State()
    title = State()
