import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.utils import executor

from app.config import TOKEN
from db.queries import get_category, create_category, create_user_category, update_user_category, get_user_category, \
    get_user_categories, get_expenses, create_expense, add_income, update_expense, delete_future_expenses, \
    delete_user_category, get_income_sum, del_last_expense, get_income
from app.forms import CategoryForm, DeleteCategoryForm, AddExpenseForm
from utils import convert_categories_list, parse_expense, define_category, aggregate_expenses, \
    convert_aggregate_expenses, parse_income, update_auto_expenses, convert_income

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

MONTH_DICT = {'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6,
              'июль': 7, 'август': 8, 'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12}


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply('Привет! Как тебя зовут?')


@dp.message_handler(commands=['manage_categories'])
async def cmd_manage_categories(message: types.Message):
    await CategoryForm.title.set()
    await message.reply('Название категории:')


@dp.message_handler(state=CategoryForm.title)
async def process_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text

    await CategoryForm.next()
    await message.reply('Предполагаемые названия трат по этой категории через запятую:')


@dp.message_handler(lambda message: types.Message, state=CategoryForm.costs)
async def process_costs(message: types.Message, state: FSMContext):
    await CategoryForm.next()
    await state.update_data(costs=message.text)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('По будням', 'Ежедневно', 'Ежемесячно', 'Еженедельно')

    await message.reply('Укажите период для траты', reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ('По будням', 'Ежедневно', 'Ежемесячно', 'Еженедельно'),
                    state=CategoryForm.costs)
async def process_gender_invalid(message: types.Message):
    return await message.reply('Неправильный период\nВыберите из предложенных.')


@dp.message_handler(lambda message: types.Message, state=CategoryForm.period)
async def process_budget(message: types.Message, state: FSMContext):
    await CategoryForm.next()
    await state.update_data(period=message.text)

    await message.reply('Какой бюджет закладывается на месяц по данной категории?\nМожно отправить 0.',
                        reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: not message.text.isdigit(), state=CategoryForm.costs)
async def process_gender_invalid(message: types.Message):
    return await message.reply('Введите цифру.')


@dp.message_handler(lambda message: types.Message, state=CategoryForm.budget)
async def process_period(message: types.Message, state: FSMContext):
    await CategoryForm.next()
    await state.update_data(budget=message.text)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('Да', 'Нет')

    await message.reply('Автоматически считать расход?', reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ('Да', 'Нет'), state=CategoryForm.is_auto)
async def process_is_auto_invalid(message: types.Message):
    return await message.reply('Да/Нет?')


@dp.message_handler(lambda message: types.Message, state=CategoryForm.is_auto)
async def process_period(message: types.Message, state: FSMContext):
    await CategoryForm.next()
    await state.update_data(is_auto=message.text)

    await message.reply('Если трата автоматическая, введите её стоимость\nЕсли нет, то отправьте 0.',
                        reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: not message.text.isdigit(), state=CategoryForm.price)
async def process_gender_invalid(message: types.Message):
    return await message.reply('Введите цифру.')


@dp.message_handler(state=CategoryForm.price)
async def process_category(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
        markup = types.ReplyKeyboardRemove()

        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Категория:', md.bold(data['title'])),
                md.text('Траты:', md.code(data['costs'])),
                md.text('Период:', data['period']),
                md.text('Бюджет', data['budget']),
                md.text('Авто:', data['is_auto']),
                md.text('Стоимость', data['price']),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
    category = get_category(title=data['title'])
    if not category:
        category = create_category(title=data['title'])
    is_auto_filters = {
        'Да': True, 'Нет': False,
        'Ежедневно': 'daily', 'Еженедельно': 'weekly', 'Ежемесячно': 'monthly', 'По будням': 'weekdays'
    }
    if get_user_category(user_id=message.from_user.id, category_id=category.id):
        update_user_category(user_id=message.from_user.id, category_id=category.id, costs=data['costs'].split(','),
                             status=is_auto_filters[data['period']], is_auto=is_auto_filters[data['is_auto']])
    else:
        create_user_category(user_id=message.from_user.id, category_id=category.id,
                             costs=[el.strip() for el in data['costs'].split(',')],
                             status=is_auto_filters[data['period']], is_auto=is_auto_filters[data['is_auto']])
    if is_auto_filters[data['period']] in ('weekdays', 'daily') and is_auto_filters[data['is_auto']]:
        update_auto_expenses(cost=data['price'], name=data['costs'], user_id=message.from_user.id,
                             category_id=category.id, period=is_auto_filters[data['period']],
                             start_day=message.date.day, year=message.date.year,
                             month=message.date.month)
    await state.finish()


@dp.message_handler(commands=['get_categories'])
async def cmd_get_categories(message: types.Message):
    user_categories = get_user_categories(user_id=message.from_user.id)
    categories_list = convert_categories_list(user_categories)
    await message.answer(categories_list)


@dp.message_handler(commands=['del_category'])
async def cmd_del_category(message: types.Message):
    await DeleteCategoryForm.category_id.set()
    user_categories = get_user_categories(user_id=message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(*[category.title for category in user_categories])
    await message.answer('Выбери категорию для удаления.', reply_markup=markup)


@dp.message_handler(state=DeleteCategoryForm.category_id)
async def process_del_category(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['category_id'] = get_category(message.text).id
        delete_future_expenses(user_id=message.from_user.id, category_id=data['category_id'], _date=message.date)
        delete_user_category(user_id=message.from_user.id, category_id=data['category_id'])
    await message.answer('Категория удалена.', reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(commands=['get_expenses'])
async def get_expenses_command(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(*MONTH_DICT)
    await message.answer('Выберите месяц', reply_markup=markup)


@dp.message_handler(lambda message: message.text.lower() in MONTH_DICT)
async def get_month_expenses(message: types.Message):
    markup = types.ReplyKeyboardRemove()
    expenses = get_expenses(user_id=message.from_user.id, month=MONTH_DICT[message.text.lower()],
                            date=message.date)
    aggregated_expenses = aggregate_expenses(expenses)
    result = convert_aggregate_expenses(aggregated_expenses)
    if not result:
        return await message.answer('За этот месяц трат нет', reply_markup=markup)
    income = get_income_sum(user_id=message.from_user.id, date=message.date)
    if not income:
        income = 0
    left = income - sum({v for k, v in aggregated_expenses.items()})
    await message.answer(result, reply_markup=markup)
    await message.answer(f'Доход: {income}')
    await message.answer(f'Осталось: {left}')


@dp.message_handler(commands=['add_income'])
async def add_income_help(message: types.Message):
    await message.answer('Чтобы добавить доход за текущий месяц,\nотправьте сообщение такого вида: +10000 зарплата')


@dp.message_handler(lambda message: message.text[0] == '+')
async def add_income_command(message: types.Message):
    income = parse_income(message.text)
    add_income(user_id=message.from_user.id, date=message.date, **income)
    await message.answer('Доход добавлен')


@dp.message_handler(lambda message: len(message.text.split()) > 1)
async def add_expense(message: types.Message, state: FSMContext):
    await AddExpenseForm.expense.set()
    expense_attrs = parse_expense(message.text)
    if not expense_attrs:
        return await message.answer('Некорректный ввод')
    title, category_id, is_auto = define_category(user_id=message.from_user.id, title=expense_attrs.get('name'))
    expense = {'user_id': message.from_user.id, 'date': message.date, 'category_id': category_id, **expense_attrs}
    if is_auto:
        await state.update_data(expense=expense, title=title)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add('Изменить', 'Добавить новый')
        await message.answer('Эта категория автоматическая, изменить сегодняшнюю трату?', reply_markup=markup)
    else:
        create_expense(**expense)
        await message.answer(f'Добавлено в категорию: {title}', reply_markup=types.ReplyKeyboardRemove())
        await state.finish()


@dp.message_handler(lambda message: message.text not in ('Изменить', 'Добавить новый'), state=AddExpenseForm.expense)
async def process_expense_invalid(message: types.Message):
    return await message.reply('Выберите вариант на клавиатуре.')


@dp.message_handler(state=AddExpenseForm.expense)
async def process_expense(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        markup = types.ReplyKeyboardRemove()
        if message.text == 'Изменить':
            update_expense(**data['expense'])
            await message.answer('Автоматическая трата изменена.', reply_markup=markup)
        if message.text == 'Добавить новый':
            create_expense(**data['expense'])
            title = data['title']
            await message.answer(f'Добавлено в категорию: {title}', reply_markup=markup)

    return await state.finish()


@dp.message_handler(commands=['del'])
async def add_income_help(message: types.Message):
    try:
        expense = del_last_expense(user_id=message.from_user.id)
    except:
        return await message.answer('Не удалось удалить последнюю трату.')
    await message.answer(f'Последняя трата удалена: {expense.name, expense.cost}')


@dp.message_handler(commands=['get_income'])
async def get_income_cmd(message: types.Message):
    incomes = get_income(user_id=message.from_user.id, date=message.date)
    result = convert_income(incomes)
    await message.answer(f'Доходы в этом месяце:\n{result}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
