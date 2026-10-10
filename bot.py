# ========= =ИМПОРТ ==========
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage



# ========== НАСТРОЙКИ ==========

BOT_TOKEN = "8848107773:AAGsJKewcrmP9CVh_QJ6xncKWCu9fADXtNw"
ADMIN_IDS = {8552544963}
DB_NAME = "recipes.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())



# ========== СОСТОЯНИЯ ==========

class RecipeForm(StatesGroup):
    title = State()
    category = State()
    ingredients = State()
    steps = State()


class SearchForm(StatesGroup):
    ingredients = State()


class AdminEditForm(StatesGroup):
    recipe_id = State()
    field = State()
    value = State()


class AdminDeleteForm(StatesGroup):
    recipe_id = State()



# ========== БАЗА ДАННЫХ ==========

def db_connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                steps TEXT NOT NULL,
                author_id INTEGER
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                UNIQUE(user_id, recipe_id)
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM recipes"
        ).fetchone()[0]

        if count == 0:
            recipes = [
                (
                    "Яичница с сыром", "Завтраки",
                    "2 яйца, 30 г сыра, соль, масло",
                    "1. Разогрейте сковороду с маслом. "
                    "2. Разбейте яйца. "
                    "3. Добавьте тёртый сыр и готовьте 3–5 минут.",
                    None
                ),
                (
                    "Сырники", "Завтраки",
                    "200 г творога, 1 яйцо, 2 ст. л. муки, сахар",
                    "1. Смешайте творог, яйцо, муку и сахар. "
                    "2. Сформируйте сырники. "
                    "3. Обжарьте с двух сторон до золотистой корочки.",
                    None
                ),
                (
                    "Омлет", "Завтраки",
                    "3 яйца, 50 мл молока, соль, масло",
                    "1. Взбейте яйца с молоком и солью. "
                    "2. Вылейте на разогретую сковороду. "
                    "3. Готовьте под крышкой 5–7 минут.",
                    None
                ),
                (
                    "Макароны с сыром", "Обеды",
                    "200 г макарон, 70 г сыра, соль",
                    "1. Отварите макароны в подсоленной воде. "
                    "2. Слейте воду. "
                    "3. Добавьте натёртый сыр и перемешайте.",
                    None
                ),
                (
                    "Курица с рисом", "Обеды",
                    "200 г куриного филе, 150 г риса, соль, специи",
                    "1. Отварите рис. "
                    "2. Нарежьте курицу и обжарьте до готовности. "
                    "3. Добавьте специи и подавайте с рисом.",
                    None
                ),
                (
                    "Картофельное пюре", "Обеды",
                    "500 г картофеля, 50 мл молока, 20 г сливочного масла",
                    "1. Очистите и отварите картофель. "
                    "2. Слейте воду. "
                    "3. Добавьте молоко и масло, разомните.",
                    None
                ),
                (
                    "Паста с курицей", "Ужины",
                    "200 г макарон, 200 г курицы, 100 мл сливок, соль",
                    "1. Отварите макароны. "
                    "2. Обжарьте кусочки курицы. "
                    "3. Добавьте сливки и готовьте 5 минут. "
                    "4. Смешайте с макаронами.",
                    None
                ),
                (
                    "Жареный картофель", "Ужины",
                    "500 г картофеля, масло, соль",
                    "1. Нарежьте картофель. "
                    "2. Разогрейте масло на сковороде. "
                    "3. Жарьте до золотистой корочки, периодически помешивая.",
                    None
                ),
                (
                    "Блины", "Десерты",
                    "250 мл молока, 1 яйцо, 150 г муки, сахар",
                    "1. Смешайте молоко, яйцо, муку и сахар. "
                    "2. Разогрейте сковороду. "
                    "3. Выпекайте тонкие блины с двух сторон.",
                    None
                ),
                (
                    "Банановый десерт", "Десерты",
                    "2 банана, 150 г йогурта, шоколад по желанию",
                    "1. Нарежьте бананы. "
                    "2. Добавьте йогурт. "
                    "3. По желанию посыпьте тёртым шоколадом.",
                    None
                ),
            ]

            conn.executemany("""
                INSERT INTO recipes
                (title, category, ingredients, steps, author_id)
                VALUES (?, ?, ?, ?, ?)
            """, recipes)


        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                UNIQUE(user_id, recipe_id)
            )
        """)


def get_recipes(category=None):
    with db_connect() as conn:
        if category:
            return conn.execute(
                "SELECT id, title FROM recipes WHERE category = ? ORDER BY title",
                (category,)
            ).fetchall()

        return conn.execute(
            "SELECT id, title FROM recipes ORDER BY title"
        ).fetchall()


def get_recipe(recipe_id):
    with db_connect() as conn:
        return conn.execute(
            """SELECT id, title, category, ingredients, steps, author_id
               FROM recipes WHERE id = ?""",
            (recipe_id,)
        ).fetchone()


def is_admin(user_id):
    return user_id in ADMIN_IDS



# ========== КЛАВИАТУРЫ ==========

def main_menu(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🍽 Все рецепты", callback_data="recipes")
    builder.button(text="📂 Категории", callback_data="categories")
    builder.button(text="🔎 Поиск по ингредиентам", callback_data="search")
    builder.button(text="⭐ Избранное", callback_data="favorites")
    builder.button(text="➕ Добавить рецепт", callback_data="add_recipe")

    if is_admin(user_id):
        builder.button(text="⚙️ Панель администратора", callback_data="admin")

    builder.adjust(2)
    return builder.as_markup()


def recipes_keyboard(recipes):
    builder = InlineKeyboardBuilder()

    for recipe_id, title in recipes:
        builder.button(
            text=title,
            callback_data=f"recipe:{recipe_id}"
        )

    builder.button(text="⬅️ Главное меню", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()


def is_favorite(user_id, recipe_id):
    with db_connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (user_id, recipe_id)
        ).fetchone()
    return row is not None


def recipe_keyboard(recipe_id, user_id):
    builder = InlineKeyboardBuilder()

    if is_favorite(user_id, recipe_id):
        builder.button(
            text="❌ Убрать из избранного",
            callback_data=f"unfav:{recipe_id}"
        )
    else:
        builder.button(
            text="⭐ В избранное",
            callback_data=f"fav:{recipe_id}"
        )

    builder.button(text="⬅️ Главное меню", callback_data="home")
    builder.adjust(1)
    return builder.as_markup()



# ========== СТАРТ И МЕНЮ ==========

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в бот рецептов.\n"
        "Здесь ты можешь находить рецепты, искать блюда "
        "по ингредиентам и сохранять их в избранное.\n\n"
        "Выбери нужный раздел в меню ниже:"
        ,
        reply_markup=main_menu(message.from_user.id)
    )



@dp.message(Command("recipes"))
async def recipes_command(message: Message):
    recipes = get_recipes()

    if not recipes:
        await message.answer("Рецептов пока нет.")
        return

    await message.answer(
        "Все рецепты:",
        reply_markup=recipes_keyboard(recipes)
    )


@dp.callback_query(F.data == "home")
async def home_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()



# ========== КАТЕГОРИИ ==========

@dp.callback_query(F.data == "categories")
async def categories_callback(callback: CallbackQuery):
    with db_connect() as conn:
        categories = conn.execute(
            "SELECT DISTINCT category FROM recipes ORDER BY category"
        ).fetchall()

    if not categories:
        await callback.message.answer("Категорий пока нет.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()

    for (category,) in categories:
        builder.button(
            text=category,
            callback_data=f"category:{category}"
        )

    builder.button(text="⬅️ Главное меню", callback_data="home")
    builder.adjust(1)

    await callback.message.answer(
        "Выберите категорию:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("category:"))
async def category_callback(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    recipes = get_recipes(category)

    if not recipes:
        await callback.message.answer("В этой категории пока нет рецептов.")
    else:
        await callback.message.answer(
            f"Категория: {category}",
            reply_markup=recipes_keyboard(recipes)
        )

    await callback.answer()



# ========== ПРОСМОТР РЕЦЕПТА ==========

@dp.callback_query(F.data.startswith("recipe:"))
async def recipe_callback(callback: CallbackQuery):
    recipe_id = int(callback.data.split(":")[1])
    recipe = get_recipe(recipe_id)

    if not recipe:
        await callback.answer("Рецепт не найден.", show_alert=True)
        return

    _, title, category, ingredients, steps, _ = recipe

    text = (
        f"🍽 {title}\n\n"
        f"📂 Категория: {category}\n\n"
        f"🧾 Ингредиенты:\n{ingredients}\n\n"
        f"👨‍🍳 Приготовление:\n{steps}"
    )

    await callback.message.answer(
        text,
        reply_markup=recipe_keyboard(recipe_id, callback.from_user.id)
    )
    await callback.answer()



# ========== ИЗБРАННОЕ ==========

@dp.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    with db_connect() as conn:
        recipes = conn.execute("""
            SELECT recipes.id, recipes.title
            FROM recipes
            JOIN favorites ON recipes.id = favorites.recipe_id
            WHERE favorites.user_id = ?
            ORDER BY recipes.title
        """, (callback.from_user.id,)).fetchall()

    if not recipes:
        await callback.message.answer("В избранном пока нет рецептов.")
    else:
        await callback.message.answer(
            "Ваши избранные рецепты:",
            reply_markup=recipes_keyboard(recipes)
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("fav:"))
async def favorite_callback(callback: CallbackQuery):
    recipe_id = int(callback.data.split(":")[1])

    with db_connect() as conn:
        recipe = conn.execute(
            "SELECT id FROM recipes WHERE id = ?",
            (recipe_id,)
        ).fetchone()

        if not recipe:
            await callback.answer("Рецепт не найден.", show_alert=True)
            return

        conn.execute(
            "INSERT OR IGNORE INTO favorites (user_id, recipe_id) VALUES (?, ?)",
            (callback.from_user.id, recipe_id)
        )

    await callback.message.edit_reply_markup(
        reply_markup=recipe_keyboard(recipe_id, callback.from_user.id)
    )
    await callback.answer("Добавлено в избранное.")


@dp.callback_query(F.data.startswith("unfav:"))
async def unfavorite_callback(callback: CallbackQuery):
    recipe_id = int(callback.data.split(":")[1])

    with db_connect() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
            (callback.from_user.id, recipe_id)
        )

    await callback.message.edit_reply_markup(
        reply_markup=recipe_keyboard(recipe_id, callback.from_user.id)
    )
    await callback.answer("Убрано из избранного.")



# ========== ПОИСК ПО ИНГРЕДИЕНТАМ ==========

@dp.callback_query(F.data == "search")
async def search_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchForm.ingredients)
    await callback.message.answer(
        "Введите ингредиенты для поиска через запятую.\n"
        "Например: курица, сыр, помидоры"
    )
    await callback.answer()


@dp.message(Command("search"))
async def search_command(message: Message, state: FSMContext):
    await state.set_state(SearchForm.ingredients)
    await message.answer("Введите ингредиенты для поиска через запятую.")


@dp.message(SearchForm.ingredients)
async def search_recipes(message: Message, state: FSMContext):
    ingredients = [
        item.strip().lower()
        for item in message.text.split(",")
        if item.strip()
    ]

    with db_connect() as conn:
        recipes = conn.execute(
            "SELECT id, title, ingredients FROM recipes ORDER BY title"
        ).fetchall()

    found = []

    for recipe_id, title, recipe_ingredients in recipes:
        text = recipe_ingredients.lower()

        if any(item in text for item in ingredients):
            found.append((recipe_id, title))

    await state.clear()

    if not found:
        await message.answer("Рецепты с такими ингредиентами не найдены.")
        return

    await message.answer(
        "Найденные рецепты:",
        reply_markup=recipes_keyboard(found)
    )



# ========== ДОБАВЛЕНИЕ РЕЦЕПТА ==========

@dp.callback_query(F.data == "add_recipe")
async def add_recipe_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(RecipeForm.title)
    await callback.message.answer("Введите название рецепта:")
    await callback.answer()


@dp.message(RecipeForm.title)
async def recipe_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(RecipeForm.category)
    await message.answer(
        "Введите категорию рецепта.\n"
        "Например: Завтраки, Обеды, Ужины, Десерты"
    )


@dp.message(RecipeForm.category)
async def recipe_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(RecipeForm.ingredients)
    await message.answer("Введите ингредиенты и их количество:")


@dp.message(RecipeForm.ingredients)
async def recipe_ingredients(message: Message, state: FSMContext):
    await state.update_data(ingredients=message.text.strip())
    await state.set_state(RecipeForm.steps)
    await message.answer("Опишите шаги приготовления:")


@dp.message(RecipeForm.steps)
async def recipe_steps(message: Message, state: FSMContext):
    data = await state.get_data()

    with db_connect() as conn:
        conn.execute("""
            INSERT INTO recipes
            (title, category, ingredients, steps, author_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["title"],
            data["category"],
            data["ingredients"],
            message.text.strip(),
            message.from_user.id
        ))

    await state.clear()
    await message.answer(
        "Рецепт успешно добавлен.",
        reply_markup=main_menu(message.from_user.id)
    )



# ========== ПАНЕЛЬ АДМИНИСТРАТОРА ==========

@dp.callback_query(F.data == "admin")
async def admin_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить рецепт", callback_data="add_recipe")
    builder.button(text="✏️ Изменить рецепт", callback_data="admin_edit")
    builder.button(text="🗑 Удалить рецепт", callback_data="admin_delete")
    builder.button(text="📋 Все рецепты", callback_data="recipes")
    builder.button(text="⬅️ Главное меню", callback_data="home")
    builder.adjust(1)

    await callback.message.answer(
        "Панель администратора:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()



# ========== РЕДАКТИРОВАНИЕ РЕЦЕПТА ==========

@dp.callback_query(F.data == "admin_edit")
async def admin_edit_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminEditForm.recipe_id)
    await callback.message.answer(
        "Введите ID рецепта, который нужно изменить.\n"
        "ID можно посмотреть в базе данных recipes.db."
    )
    await callback.answer()


@dp.message(AdminEditForm.recipe_id)
async def admin_edit_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        recipe_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом. Введите ID ещё раз:")
        return

    recipe = get_recipe(recipe_id)

    if not recipe:
        await message.answer("Рецепт с таким ID не найден. Введите другой ID:")
        return

    await state.update_data(recipe_id=recipe_id)
    await state.set_state(AdminEditForm.field)

    builder = InlineKeyboardBuilder()
    builder.button(text="Название", callback_data="editfield:title")
    builder.button(text="Категория", callback_data="editfield:category")
    builder.button(text="Ингредиенты", callback_data="editfield:ingredients")
    builder.button(text="Приготовление", callback_data="editfield:steps")
    builder.adjust(1)

    await message.answer(
        "Что нужно изменить?",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(
    AdminEditForm.field,
    F.data.startswith("editfield:")
)
async def admin_edit_field(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    field = callback.data.split(":", 1)[1]
    allowed_fields = {"title", "category", "ingredients", "steps"}

    if field not in allowed_fields:
        await callback.answer("Неизвестное поле.", show_alert=True)
        return

    await state.update_data(field=field)
    await state.set_state(AdminEditForm.value)

    prompts = {
        "title": "Введите новое название рецепта:",
        "category": "Введите новую категорию:",
        "ingredients": "Введите новый список ингредиентов:",
        "steps": "Введите новое описание приготовления:"
    }

    await callback.message.answer(prompts[field])
    await callback.answer()


@dp.message(AdminEditForm.value)
async def admin_edit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    field = data["field"]
    recipe_id = data["recipe_id"]
    value = message.text.strip()

    allowed_fields = {"title", "category", "ingredients", "steps"}

    if field not in allowed_fields:
        await state.clear()
        await message.answer("Ошибка: неизвестное поле.")
        return

    with db_connect() as conn:
        conn.execute(
            f"UPDATE recipes SET {field} = ? WHERE id = ?",
            (value, recipe_id)
        )

    await state.clear()
    await message.answer(
        "Рецепт успешно изменён.",
        reply_markup=main_menu(message.from_user.id)
    )



# ========== УДАЛЕНИЕ РЕЦЕПТА ==========

@dp.callback_query(F.data == "admin_delete")
async def admin_delete_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminDeleteForm.recipe_id)
    await callback.message.answer(
        "Введите ID рецепта, который нужно удалить:"
    )
    await callback.answer()


@dp.message(AdminDeleteForm.recipe_id)
async def admin_delete_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        recipe_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом. Введите ID ещё раз:")
        return

    with db_connect() as conn:
        recipe = conn.execute(
            "SELECT id FROM recipes WHERE id = ?",
            (recipe_id,)
        ).fetchone()

        if not recipe:
            await message.answer("Рецепт не найден. Введите другой ID:")
            return

        conn.execute(
            "DELETE FROM favorites WHERE recipe_id = ?",
            (recipe_id,)
        )
        conn.execute(
            "DELETE FROM recipes WHERE id = ?",
            (recipe_id,)
        )

    await state.clear()
    await message.answer(
        "Рецепт удалён.",
        reply_markup=main_menu(message.from_user.id)
    )



# ========== ЗАПУСК ==========

@dp.callback_query(F.data == "recipes")
async def recipes_callback(callback: CallbackQuery):
    recipes = get_recipes()

    if not recipes:
        await callback.message.answer("Рецептов пока нет.")
    else:
        await callback.message.answer(
            "Все рецепты:",
            reply_markup=recipes_keyboard(recipes)
        )

    await callback.answer()

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())