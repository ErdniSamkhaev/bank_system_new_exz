import sqlite3


# commit

def create_tables():
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
