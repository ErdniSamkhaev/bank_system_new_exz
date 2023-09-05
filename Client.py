import hashlib
import re
from database import connect_to_db, close_db_connection


def is_valid_name(name):
    """Функция для проверки переданной строки."""
    return bool(re.match(r'^[А-Яа-я\s]*$', name))


def is_valid_phone():
    """Функция для проверки формата телефона"""
    while True:
        phone = input("Введите телефон в формате '999 999 99 99' с пробелами: ")
        if re.match(r'^\d{3} \d{3} \d{2} \d{2}$', phone):
            return phone
        else:
            print("Некорректный формат телефона. Пожалуйста, введите еще раз.")


def is_valid_email():
    """Функция для проверки формата почты"""
    while True:
        email = input("Введите почту в формате 'info@rambler.ru': ")
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return email
        else:
            print("Некорректный формат почты. Пожалуйста, введите еще раз.")


class Client:
    @staticmethod
    def update_client_info_company(client_id, new_name, new_director_name, new_phone, new_email, new_password):
        """
        Обновляет информацию о юридическом лице в базе данных.

        Параметры:
        client_id (int): Идентификатор клиента, информацию о котором нужно обновить.
        new_name (str): Новое полное имя юридического лица.
        new_director_name (str): Новое имя директора юридического лица.
        new_phone (str): Новый номер телефона клиента.
        new_email (str): Новый адрес электронной почты клиента.
        new_password (str): Новый пароль клиента (будет хеширован перед обновлением).

        Возвращает:
        str: Сообщение об успешном обновлении данных клиента.
        """
        conn, cursor = connect_to_db()  # Открытие соединения

        # Хеширование нового пароля
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        # Обновление данных клиента в таблицах clients и accounts
        cursor.execute('UPDATE clients SET full_name = ?, director_name = ?, phone = ?, email = ?, password = ? '
                       'WHERE id = ?', (new_name, new_director_name, new_phone, new_email, hashed_password, client_id))
        cursor.execute('UPDATE accounts SET owner_name = ? WHERE client_id = ?',
                       (new_name, client_id))

        conn.commit()  # Сохраняем
        close_db_connection(conn)  # Закрытие соединения
        return 'Данные успешно обновлены.'

    @staticmethod
    def update_client_info_individual(client_id, new_name, new_phone, new_email, new_password):
        """
        Обновляет информацию о физическом лице в базе данных.

        Args:
            client_id (int): Идентификатор клиента, которого нужно обновить.
            new_name (str): Новое имя клиента.
            new_phone (str): Новый номер телефона клиента.
            new_email (str): Новый адрес электронной почты клиента.
            new_password (str): Новый пароль клиента (будет хэширован перед обновлением).
        Returns:
            str: Сообщение об успешном обновлении данных.

        """
        conn, cursor = connect_to_db()  # Открытие соединения

        # Хеширование нового пароля
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        # ООбновление данных клиента в таблицах clients и accounts
        cursor.execute('UPDATE clients SET full_name = ?, phone = ?, email = ?, password = ? '
                       'WHERE id = ?', (new_name, new_phone, new_email, hashed_password, client_id))
        cursor.execute('UPDATE accounts SET owner_name = ? WHERE client_id = ?',
                       (new_name, client_id))

        conn.commit()  # Сохраняем
        close_db_connection(conn)  # Закрытие соединения
        return 'Данные успешно обновлены.'

    @staticmethod
    def create_account_for_client(client_id, user_type):
        """
    Создает счет для указанного клиента.

    Args:
        client_id (int): Идентификатор клиента, для которого создается счет.
        user_type (str): Тип клиента ('Физическое лицо' или 'Юридическое лицо').

    Returns:
        str: Сообщение об успешном создании счета или ошибка, если счет уже существует или указан некорректный тип клиента.
    """
        conn, cursor = connect_to_db()  # Открытие соединения

        # Проверка наличия счета "Расчетный" для данного юридического лица
        cursor.execute('SELECT COUNT(*) FROM accounts WHERE client_id = ? AND account_type = "Расчетный"', (client_id,))
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            close_db_connection(conn)  # Закрытие соединения
            return "Для данного юридического лица уже существует счет."

        # Запрос на получение типа клиента
        cursor.execute('SELECT type, full_name, director_name FROM clients WHERE id = ?', (client_id,))
        client_type = cursor.fetchone()

        if client_type is None:
            close_db_connection(conn)  # Закрытие соединения
            return "Такого клиента нет."

        if user_type == 'Физическое лицо':
            account_type = 'Лицевой'
        elif user_type == 'Юридическое лицо':
            account_type = 'Расчетный'
        else:
            return "Некорректный тип клиента"

        owner_name = client_type[1] if user_type == 'Физическое лицо' else client_type[2]

        # Вставляем новую запись счета в таблицу
        cursor.execute('''
            INSERT INTO accounts (client_id, owner_name, account_type, is_legal_entity, balance)
            VALUES (?, ?, ?, ?, ?)
        ''', (client_id, owner_name, account_type, client_type[0] == 'Юридическое лицо', 0.0))

        conn.commit()  # Записываем
        close_db_connection(conn)  # Закрытие соединения
        return f"Счет успешно создан для владельца для владельца: {owner_name}"

    @staticmethod
    def get_password():
        """Функция для ввода и хеширования пароля"""
        while True:
            password = input("Пароль должен содержать минимум 8 символов, хотя бы одну цифру, одну маленькую и одну \n"
                             "большую латинскую букву. Введите пароль для регистрации : ")

            if len(password) < 8:
                print("Ошибка: Пароль должен содержать как минимум 8 символов.")
                continue

            if not re.search(r'\d', password):
                print("Ошибка: Пароль должен содержать хотя бы одну цифру.")
                continue

            if not re.search(r'[a-z]', password):
                print("Ошибка: Пароль должен содержать хотя бы одну маленькую латинскую букву.")
                continue

            if not re.search(r'[A-Z]', password):
                print("Ошибка: Пароль должен содержать хотя бы одну большую латинскую букву.")
                continue

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            return hashed_password

    @staticmethod
    def register_client(client_type, user_type=None):
        """Регистрация клиента.

        Функция позволяет зарегистрировать клиента, как физическое или юридическое лицо, собирая необходимую информацию,
        такую как ФИО (для физического лица) или название компании и ФИО директора (для юридического лица), а также
        электронную почту, телефон и пароль. При этом, функция выполняет следующие действия:

        - Функция проверяет валидность ФИО и формат электронной почты.
        - Пароль клиента хэшируется с использованием функции `get_password` из этого класса.
        - Регистрация клиента в базе данных выполняется через SQL-запросы.
        - После успешной регистрации создается аккаунт для клиента.

        Функция `create_account_for_client` позволяет создать счет после регистрации.

        Параметры:
        client_type (str): Тип клиента, может быть 'individual' (физическое лицо) или 'company' (юридическое лицо).

        Возвращает:
        str: Сообщение об успешной регистрации клиента.
        """
        full_name = ""
        company_name = ""
        director_name = ""

        if client_type == 'individual':
            while True:
                full_name = input("Введите ФИО в формате 'Иванов Иван Иванович': ")
                if len(full_name) > 75:
                    print("Ошибка: ФИО не может превышать 75 символов.")
                elif not is_valid_name(full_name):
                    print('Ошибка. ФИО не должно содержать цифры или специальные символы.')
                else:
                    break
        else:
            while True:
                company_name = input("Введите название компании в формате 'ООО Ромашка': ")
                if len(company_name) > 40:
                    print("Ошибка: Название компании не должно превышать 40 символов.")
                else:
                    break
            while True:
                director_name = input("Введите ФИО директора в формате 'Иванов Иван Иванович': ")
                if len(director_name) > 75:
                    print("Ошибка: ФИО директора не должно превышать 75 символов.")
                elif not is_valid_name(director_name):
                    print('Ошибка. ФИО не должно содержать цифры или специальные символы.')
                else:
                    break

        hashed_password = Client.get_password()

        email = is_valid_email()
        phone = is_valid_phone()

        # Сохранение информации в базу данных
        conn, cursor = connect_to_db()  # Открытие соединения

        if client_type == 'individual':
            cursor.execute('''
                INSERT INTO clients (type, full_name, email, phone, password, is_legal_entity, withdrawal_limit,
                 transfer_fee_rate, transfer_limit )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('Физическое лицо', full_name, email, phone, hashed_password, False, None, None, None))
        else:
            cursor.execute('''
                INSERT INTO clients (type, full_name, director_name, email, phone, password, is_legal_entity, 
                withdrawal_limit, transfer_fee_rate, transfer_limit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('Юридическое лицо', company_name, director_name, email, phone, hashed_password, True, 0.0, 0.0, 0.0))

        owner_id = cursor.lastrowid  # Возвращаем ID последней записи
        Client.create_account_for_client(owner_id, user_type)  # Создаем счет для определенного клиента

        conn.commit()  # Записываем в БД
        close_db_connection(conn)  # Закрытие соединения

        print("Регистрация успешно завершена!")
