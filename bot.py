from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types
manager = DB_Manager(DATABASE)

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"

def cansel(message):
    bot.send_message(
        message.chat.id,
        "❌ Действие отменено\n\nℹ️ Чтобы посмотреть команды, используй /info",
        reply_markup=hideBoard
    )
  
def no_projects(message):
    bot.send_message(
        message.chat.id,
        "📂 У тебя пока нет проектов!\n\n➕ Можешь добавить первый с помощью команды /new_project"
    )

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(f"📌 {row}", callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {
    'Имя проекта': ["✏️ Введите новое имя проекта", "project_name"],
    'Описание': ["📝 Введите новое описание проекта", "description"],
    'Ссылка': ["🔗 Введите новую ссылку на проект", "url"],
    'Статус': ["📊 Выберите новый статус проекта", "status_id"]
}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = '— навыки пока не добавлены —'

    bot.send_message(
    message.chat.id,
    f"""
╔══════════════════════╗
📁 <b>{info[0]}</b>
╚══════════════════════╝

📝 <b>Описание:</b>
{info[1]}

🔗 <b>Ссылка:</b>
{info[2]}

📊 <b>Статус:</b> {info[3]}

🛠 <b>Навыки:</b>
{skills}

━━━━━━━━━━━━━━━━━━
🚀 Продолжай развивать проект!
""",
    parse_mode="HTML"
)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        """👋 Привет!

Я — 🤖 <b>бот-менеджер проектов</b>
Помогаю хранить твои проекты, навыки и ссылки в одном месте 💼✨
""",
        parse_mode="HTML"
    )
    info(message)
    
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(
        message.chat.id,
        """ℹ️ <b>Доступные команды:</b>

➕ /new_project — добавить новый проект  
🛠 /skills — добавить навыки к проекту  
📂/projects — список всех проектов  
🗑 /delete — удалить проект  
✏️ /update_projects — изменить данные проекта  
""",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "📌 Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "📝 Введите описание проекта:")
    bot.register_next_step_handler(message, description_project, data=data)

def description_project(message, data):
    data.append(message.text)
    bot.send_message(message.chat.id, "🔗 Введите ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(
        message.chat.id,
        "📊 Выберите текущий статус проекта:",
        reply_markup=gen_markup(statuses)
    )
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(
            message.chat.id,
            "⚠️ Пожалуйста, выбери статус из списка 👇",
            reply_markup=gen_markup(statuses)
        )
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    bot.send_message(
    message.chat.id,
    "🎉 <b>Проект успешно сохранён!</b>\n\n✨ Теперь можешь добавить навыки.",
    parse_mode="HTML"
)

@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(
            message.chat.id,
            "🛠 Выбери проект, для которого хочешь добавить навык:",
            reply_markup=gen_markup(projects)
        )
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)

def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(
            message.chat.id,
            "⚠️ Такого проекта нет. Попробуй выбрать ещё раз:",
            reply_markup=gen_markup(projects)
        )
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(
            message.chat.id,
            "🧠 Выбери навык:",
            reply_markup=gen_markup(skills)
        )
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(
            message.chat.id,
            "⚠️ Выбери навык из списка:",
            reply_markup=gen_markup(skills)
        )
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(
        message.chat.id,
        f"✅ Навык <b>{skill}</b> добавлен к проекту <b>{project_name}</b>",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)

    if not projects:
        no_projects(message)
        return

    text = ""
    for p in projects:
        # p — кортеж с полями из таблицы projects
        # предположим, что:
        # p[2] — имя проекта
        # p[3] — описание
        # p[4] — ссылка
        # p[5] — status_id, но нам нужен статус по имени, нужно запросить

        status_name = manager.get_status_name_by_id(p[5]) if p[5] else 'Не указан'

        text += (
            f"╔══════════════════════╗\n"
            f"       📁 <b>{p[2]}</b>\n"
            f"╚══════════════════════╝\n\n"
            f"📝 <b>Описание:</b>\n{p[3] if p[3] else '— нет описания —'}\n\n"
            f"🔗 <b>Ссылка:</b> {p[4] if p[4] else '— нет ссылки —'}\n\n"
            f"📊 <b>Статус:</b> {status_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=hideBoard
    )


if __name__ == "__main__":
    bot.infinity_polling()
