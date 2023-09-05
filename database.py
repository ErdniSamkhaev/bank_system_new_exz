import sqlite3


def connect_to_db():
    """Функция открытия соединения с БД"""
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    return conn, cursor


def close_db_connection(conn):
    """Функция закрытия соединения с БД"""
    conn.commit()
    conn.close()


def create_tables():
    """
        Создает таблицы в базе данных для управления клиентами, счетами и транзакциями в банковской системе.

        - clients: Таблица для хранения информации о клиентах.
            - id: Уникальный идентификатор клиента.
            - type: Тип клиента (Физическое лицо или Юридическое лицо).
            - full_name: Полное имя клиента (ФИО или название компании).
            - director_name: Имя директора (только для юридических лиц).
            - email: Адрес электронной почты клиента.
            - phone: Номер телефона клиента.
            - password: Хэшированный пароль клиента.
            - is_legal_entity: Флаг, указывающий, является ли клиент юридическим лицом.
            - withdrawal_limit: Лимит на снятие средств с аккаунта.
            - transfer_fee_rate: Процентная ставка для комиссии за переводы.
            - transfer_limit: Лимит на сумму перевода.

        - accounts: Таблица для хранения информации о счетах клиентов.
            - id: Уникальный идентификатор счета.
            - client_id: Идентификатор клиента, которому принадлежит счет.
            - account_type: Тип счета (Лицевой или Расчетный).
            - owner_name: Имя владельца счета (ФИО или название компании).
            - is_legal_entity: Флаг, указывающий, является ли владелец юридическим лицом.
            - balance: Текущий баланс счета.

        - transactions: Таблица для хранения информации о транзакциях между счетами.
            - id: Уникальный идентификатор транзакции.
            - sender_id: Идентификатор счета отправителя.
            - recipient_id: Идентификатор счета получателя.
            - amount: Сумма транзакции.
            - transfer_fee: Комиссия за транзакцию.
            - timestamp: Метка времени создания транзакции.
        """
    # Создаем подключение к базе данных
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()

    # Создаем таблицу клиентов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            type TEXT,
            full_name TEXT,
            director_name TEXT,
            email TEXT,
            phone TEXT,
            password TEXT,
            is_legal_entity BOOLEAN,
            withdrawal_limit REAL,
            transfer_fee_rate REAL,
            transfer_limit REAL
        )
    ''')

    # Создаем таблицу счетов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            client_id INTEGER,
            account_type TEXT,
            owner_name TEXT,
            is_legal_entity BOOLEAN,
            balance REAL,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')

    # Создаем таблицу транзакций
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                sender_id INTEGER,
                recipient_id INTEGER,
                amount REAL,
                transfer_fee REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES accounts (id),
                FOREIGN KEY (recipient_id) REFERENCES accounts (id)
            )
        ''')
    # Сохраняем изменения
    conn.commit()
    # Закрываем соединение
    conn.close()
