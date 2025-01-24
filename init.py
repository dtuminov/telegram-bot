import sqlite3
from telegram import Update, ReplyKeyboardMarkup

commands = [
    ("/start", "Запустить бота"),
    ("/help", "Показать доступные команды"),
    ("/register", "Зарегистрироваться"),
    ("/profile", "Посмотреть свой профиль"),
    ("/edit_profile", "Редактировать профиль"),
    ("/find_match", "Найти совпадения")
]

courses = [ "Механико-математический факультет 🧮",
            "Факультет вычислительной математики и кибернетики 💻",
            "Физический факультет 🔩",
            "Химический факультет 🧪",
            "Биологический факультет 🧫",
            "Факультет наук о материалах 🧱",
            "Факультет почвоведения 🌱",
            "Геологический факультет 🪨",
            "Географический факультет 🌍",
            "Факультет биоинженерии и биоинформатики 🧬",
            "Факультет фундаментальной медицины 💊",
            "Факультет фундаментальной физико-химической инженерии 🔬",
            "Биотехнологический факультет 🦠",
            "Факультет космических исследований 🚀",
            "Исторический факультет 🏺",
            "Филологический факультет 📚",
            "Философский факультет 🗿",
            "Экономический факультет 💸",
            "Юридический факультет ⚖️",
            "Социологический факультет🗣️",
            "Факультет журналистики 📝",
            "Факультет психологии 🌈",
            "Институт стран Азии и Африки 🎎",
            "Факультет политологии 🇷🇺",
            "Факультет иностранных языков и регионоведения 🏛️",
            "Факультет государственного управления 🏦",
            "Факультет мировой политики 🇺🇳",
            "Факультет глобальных процессов 🖥️",
            "Факультет искусств 💃",
            "Высшая школа бизнеса 💳",
            "Московская школа экономики 📈",
            "Высшая школа перевода 🇬🇧",
            "Высшая школа государственного администрирования 🔖",
            "Высшая школа государственного аудита🎙️",
            "Высшая школа управления и инноваций⚗️",
            "Высшая школа инновационного бизнеса 💰",
            "Высшая школа телевидения 🎥",
            "Высшая школа современных социальных наук 📲",
            "Высшая школа культурной политики и управления в гуманитарной сфере 🏢",
            "Факультет педагогического образования 🧑‍🏫",
            "Университетская гимназия 🏫",
            "Первый университетский лицей имени Н.И.Лобачевского 📄",
            "Специализированный учебно–научный центр 🧑‍️",]


def create_menu_keyboard():
    # Создаем клавиатуру на основе команд, организовав их по двум строкам
    options = []
    for i in range(0, len(commands), 2):  # Разбиваем команды на строки, по 2 в каждой
        options.append([command[0] for command in commands[i:i + 2]])
    return ReplyKeyboardMarkup(options, one_time_keyboard=True, resize_keyboard=True)


# Создаем и подключаемся к базе данных
conn = sqlite3.connect('users.db')  # бля вот это вообще пиздец
cursor = conn.cursor()
