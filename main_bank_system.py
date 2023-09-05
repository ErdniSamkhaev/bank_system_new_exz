import database
import Client
import hashlib
from database import connect_to_db, close_db_connection


def get_sender_recipient_info(account_id):
    """Функция для получения информации об отправителе и получателе"""
    conn, cursor = connect_to_db()  # Открытие соединения

    # Получаем информацию о счете
    cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
    account_info = cursor.fetchone()

    if account_info is None:
        close_db_connection(conn)  # Закрытие соединения
        return None, None, None

    sender_id = account_info[0]
    sender_balance = account_info[5]

    # Получение информации о клиенте
    cursor.execute('SELECT type FROM clients WHERE id = ?', (sender_id,))
    sender_type = cursor.fetchone()[0]  # Тип клиента

    close_db_connection(conn)  # Закрытие соединения
    return sender_id, sender_balance, sender_type


def deposit_money(client_id, amount):
    """Функция пополнения счета"""
    conn, cursor = connect_to_db()  # Открытие соединения

    # Выводим данные
    cursor.execute('SELECT * FROM accounts WHERE id = ?', (client_id,))
    account_info = cursor.fetchone()

    if account_info is None:
        conn.close()
        return "Клиент не найден"

    column_names = [desc[0] for desc in cursor.description]  # Извлечение названий из запроса
    account_dict = dict(zip(column_names, account_info))  # Словарь с информацией о счете

    balance = account_dict['balance']  # Получение текущего баланса
    new_balance = balance + amount  # Вычисление нового баланса
    owner_name = account_dict['owner_name']

    # Обновление баланса в БД
    cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_balance, client_id))
    conn.commit()
    close_db_connection(conn)  # Закрытие соединения

    return f"Счет успешно пополнен для {owner_name}. Новый баланс: {new_balance}"


def update_account_balance(cursor, account_id, new_balance):
    """Обновляет баланс для указанного счета"""
    cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_balance, account_id))


def pay_salary(sender_id, recipient_id, salary_amount):
    """Функция выплаты зарплаты"""
    conn, cursor = connect_to_db()  # Открытие соединения

    # Получаем информацию об отправителе и получателе
    sender_id, sender_balance, sender_type = get_sender_recipient_info(sender_id)
    recipient_id, recipient_balance, recipient_type = get_sender_recipient_info(recipient_id)

    if sender_id is None or recipient_id is None:
        close_db_connection(conn)  # Закрытие соединения
        return "Клиент не найден"

    sender_client_type = sender_type
    recipient_client_type = recipient_type

    if sender_client_type == 'Физическое лицо' and recipient_client_type == 'Физическое лицо':
        close_db_connection(conn)  # Закрытие соединения
        return "Перевод зарплаты запрещен"

    if sender_client_type == 'Физическое лицо' and recipient_client_type == 'Юридическое лицо':
        close_db_connection(conn)  # Закрытие соединения
        return "Перевод зарплаты запрещен"

    if sender_client_type == 'Юридическое лицо' and recipient_client_type == 'Юридическое лицо':
        close_db_connection(conn)  # Закрытие соединения
        return "Перевод зарплаты запрещен"

    elif sender_client_type == 'Юридическое лицо':
        transfer_fee = salary_amount * 0.42  # Налог 42% на сумму перевода
        total_amount = salary_amount + transfer_fee
        if sender_balance >= total_amount:
            new_sender_balance = sender_balance - total_amount
            new_recipient_balance = recipient_balance + salary_amount

            # Проверяем наличие достаточных средств для перевода с учетом комиссии
            if sender_balance < salary_amount:
                close_db_connection(conn)  # Закрытие соединения
                return "Недостаточно средств для перевода с учетом комиссии"

            # Зачисляем налог на счет банка
            bank_account_id = 2
            cursor.execute('SELECT balance FROM accounts WHERE id = ?', (bank_account_id,))
            bank_balance = cursor.fetchone()[0]
            new_bank_balance = bank_balance + transfer_fee
            cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_bank_balance, bank_account_id))

            # Обновляем балансы
            update_account_balance(cursor, sender_id, new_sender_balance)
            update_account_balance(cursor, recipient_id, new_recipient_balance)

            # Записываем транзакцию
            cursor.execute(
                'INSERT INTO transactions (sender_id, recipient_id, amount, transfer_fee) VALUES (?, ?, ?, ?)',
                (sender_id, recipient_id, salary_amount, transfer_fee))
            conn.commit()
            close_db_connection(conn)  # Закрытие соединения
            return "Перевод успешно выполнен"
        else:
            close_db_connection(conn)  # Закрытие соединения
            return "Недостаточно средств для перевода с учетом налога"


def make_transfer(sender_id, recipient_id, amount):
    """
    Функция для осуществления денежных переводов между клиентами.

    Parameters:
        sender_id (int): Идентификатор отправителя.
        recipient_id (int): Идентификатор получателя.
        amount (float): Сумма перевода.

    Returns:
        str: Сообщение о результате операции.

    Description:
        Эта функция позволяет осуществлять переводы между клиентами. В зависимости от типов клиентов (физическое или
        юридическое лицо) и суммы перевода, применяется комиссия или налог.

        - Если отправитель и получатель являются физическими лицами, то для суммы перевода более 100 000 рублей
          применяется комиссия 1% от суммы. Проверяется наличие достаточных средств для перевода с учетом комиссии.
          Если средств недостаточно, операция отклоняется.

        - Если отправитель и получатель являются юридическими лицами или если отправитель физическое лицо, а получатель
          юридическое лицо, то применяется налог 20% на сумму перевода. Проверяется наличие достаточных средств для
          перевода с учетом налога. Если средств недостаточно, операция отклоняется.

        - Если отправитель юридическое лицо, а получатель физическое лицо, то операция отклоняется.

        В случае успешного перевода, балансы отправителя и получателя обновляются, а также записывается соответствующая
        транзакция. Комиссия или налог зачисляются на счет банка.

        В случае ошибок (например, недостаточно средств или другие ошибки во время операции), функция вернет
        соответствующее сообщение об ошибке.

    """
    conn, cursor = connect_to_db()  # Открытие соединения

    # Получаем информацию об отправителе и получателе
    sender_id, sender_balance, sender_type = get_sender_recipient_info(sender_id)
    recipient_id, recipient_balance, recipient_type = get_sender_recipient_info(recipient_id)

    # Проверка если нет ID в БД
    if sender_id is None or recipient_id is None:
        return "Клиент не найден"

    # Проверка, кто отправитель и получатель
    cursor.execute('SELECT type FROM clients WHERE id = ?', (sender_id,))
    sender_client_type = cursor.fetchone()[0]
    cursor.execute('SELECT type FROM clients WHERE id = ?', (recipient_id,))
    recipient_client_type = cursor.fetchone()[0]

    if sender_client_type == 'Юридическое лицо' and recipient_client_type == 'Физическое лицо':
        close_db_connection(conn)  # Закрытие соединения
        return "Перевод запрещен. Нельзя переводить с расчетного счета физическим лицам."

    if sender_client_type == 'Физическое лицо' and recipient_client_type == 'Физическое лицо':

        # Проверка чтобы нельзя было переводить самому себе на тот же счет.
        if sender_id == recipient_id:
            close_db_connection(conn)
            return "Нельзя переводить самому себе."

        transfer_fee = 0
        if amount > 100000:
            transfer_fee = amount * 0.01

        # Вычисляем общую сумму, которая будет списана со счета отправителя
        total_amount = amount + transfer_fee

        # Проверяем наличие достаточных средств для перевода с учетом комиссии
        if sender_balance < amount:
            close_db_connection(conn)  # Закрытие соединения
            return "Недостаточно средств для перевода с учетом комиссии"

        # Обновляем балансы
        new_sender_balance = sender_balance - total_amount
        new_recipient_balance = recipient_balance + amount

        cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_sender_balance, sender_id))
        cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_recipient_balance, recipient_id))
        cursor.execute('INSERT INTO transactions (sender_id, recipient_id, amount, transfer_fee) VALUES (?, ?, ?, ?)',
                       (sender_id, recipient_id, amount, transfer_fee))

        # Зачисляем комиссию на счет банка
        bank_account_id = 2
        cursor.execute('SELECT balance FROM accounts WHERE id = ?', (bank_account_id,))
        bank_balance = cursor.fetchone()[0]
        new_bank_balance = bank_balance + transfer_fee
        cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_bank_balance, bank_account_id))

        conn.commit()
        close_db_connection(conn)  # Закрытие соединения
        return "Перевод успешно выполнен"

    if (sender_client_type == 'Юридическое лицо' and recipient_client_type == 'Юридическое лицо' or
            sender_client_type == 'Физическое лицо' and recipient_client_type == 'Юридическое лицо'):

        # Проверка чтобы нельзя было переводить самому себе.
        if sender_id == recipient_id:
            close_db_connection(conn)
            return "Нельзя переводить самому себе."

        transfer_fee = amount * 0.2  # Налог 20% на сумму перевода
        total_amount = amount + transfer_fee

        # Проверяем наличие достаточных средств для перевода с учетом налога
        if sender_balance >= total_amount:
            new_sender_balance = sender_balance - total_amount
            new_recipient_balance = recipient_balance + amount

            # Обновляем балансы
            cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_sender_balance, sender_id))
            cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_recipient_balance, recipient_id))

            # Зачисляем налог на счет банка
            bank_account_id = 2
            cursor.execute('SELECT balance FROM accounts WHERE id = ?', (bank_account_id,))
            bank_balance = cursor.fetchone()[0]
            new_bank_balance = bank_balance + transfer_fee
            cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (new_bank_balance, bank_account_id))

            # Записываем транзакцию
            cursor.execute(
                'INSERT INTO transactions (sender_id, recipient_id, amount, transfer_fee) VALUES (?, ?, ?, ?)',
                (sender_id, recipient_id, amount, transfer_fee))

            conn.commit()  # Записываем
            close_db_connection(conn)  # Закрытие соединения
            return "Перевод успешно выполнен"
        else:
            close_db_connection(conn)  # Закрытие соединения
            return "Недостаточно средств для перевода с учетом налога"


def view_balance(account_id):
    """Просмотр баланса"""
    conn, cursor = connect_to_db()  # Открытие соединения

    # Выводим информацию из БД
    cursor.execute('SELECT balance FROM accounts WHERE id = ?', (account_id,))
    balance = cursor.fetchone()[0]

    close_db_connection(conn)  # Закрытие соединения
    return balance


def perform_transfer(sender_id):
    """Функция перевода средств"""
    recipient_id = int(input("Введите ID получателя: "))
    transfer_amount = float(input("Введите сумму перевода: "))

    transfer_result = make_transfer(sender_id, recipient_id, transfer_amount)
    print(transfer_result)


def money_cash(account_id):
    """Функция снятия денег"""
    conn, cursor = connect_to_db()  # Открытие соединения

    # Получение информации у кого снимаем деньги
    cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
    account_info = cursor.fetchone()

    if account_info is None:
        close_db_connection(conn)  # Закрытие соединения
        return "Клиент не найден"

    account_type = account_info[2]  # Тип счета
    client_id = account_info[1]  # ID клиента

    print("Тип счета:", account_type)
    if account_type == 'Расчетный':
        close_db_connection(conn)  # Закрытие соединения
        return 'Нельзя снимать деньги с расчетного счета.'

    balance = account_info[5]  # Текущий баланс

    # Получение информации о клиенте
    cursor.execute('SELECT type FROM clients WHERE id = ?', (client_id,))
    client_type = cursor.fetchone()[0]  # Тип клиента

    print("Тип клиента:", client_type)

    try:
        amount_to_withdraw = float(input("Введите сумму для снятия."))
    except ValueError:
        close_db_connection(conn)  # Закрытие соединения
        return 'Некорректная сумма'

    if amount_to_withdraw <= 0:
        close_db_connection(conn)  # Закрытие соединения
        return 'Некорректная сумма'

    if client_type == 'Физическое лицо' and amount_to_withdraw > 1000000:
        close_db_connection(conn)  # Закрытие соединения
        return 'Физическим лицам запрещено снимать более 1 миллиона. Вам нужно явиться в банк.'

    if balance >= amount_to_withdraw:
        new_balance = balance - amount_to_withdraw

        # Обновляем баланс
        cursor.execute('UPDATE accounts SET balance = ? WHERE client_id = ?', (new_balance, account_id))
        conn.commit()
        close_db_connection(conn)  # Закрытие соединения
        return f"Сумма {amount_to_withdraw} успешно снята. Новый баланс: {new_balance}"
    else:
        close_db_connection(conn)  # Закрытие соединения
        return 'Недостаточно средств на счете.'


def login():
    """Функция для входа в личный кабинет"""
    while True:
        email_or_phone = input("Введите почту или телефон: ")

        conn, cursor = connect_to_db()  # Открытие соединения

        cursor.execute('SELECT id, type, full_name, password FROM clients WHERE (email = ? OR phone = ?)'
                       , (email_or_phone, email_or_phone))

        user_data = cursor.fetchone()  # Записываем

        if user_data is None:
            close_db_connection(conn)  # Закрытие соединения
            print('Пользователь с такой почтой или телефоном не найден.')
            continue  # Пользователь не найден, продолжаем цикл.

        user_id, user_type, user_full_name, stored_password = user_data

        # Теперь кода почта или телефон найдены, запрашиваем пароль.
        password = input("Введите пароль: ")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Проверка введенного пароля
        if hashed_password != stored_password:
            close_db_connection(conn)
            print("Не правильный пароль. Попробуйте снова.")
            continue  # Не правильный пароль, продолжаем цикл

        close_db_connection(conn)
        return user_id, user_type, user_full_name


def main():
    database.create_tables()
    while True:
        print("1. Регистрация физического лица.")
        print("2. Регистрация юридического лица.")
        print("3. Пополнить счет.")  # Пока просто для проверок функций
        print("4. Вход в личный кабинет.")
        print("0. Выйти из программы.")
        choice = input("Выберите пункт: ")

        if choice == '1':
            Client.Client.register_client('individual')
        elif choice == '2':
            Client.Client.register_client('company')
        elif choice == '3':
            client_id = int(input("Введите ID клиента: "))
            deposit_amount = float(input("Введите сумму для пополнения: "))
            result = deposit_money(client_id, deposit_amount)
            print(result)
        elif choice == '4':
            user_id = login()
            if user_id is not None:
                user_id, user_type, user_full_name = user_id
                print("Вход выполнен. Здравствуйте, дорогой: ", user_full_name)
                if user_type == 'Физическое лицо':
                    print("1. Создать счёт.")
                    print("2. Просмотр баланса.")
                    print("3. Перевод между счетами.")
                    print("4. Изменить данные.")
                    print("5. Снять деньги со счета.")
                    print("0. Выйти из личного кабинета.")
                    user_choice = input("Выберите пункт: ")
                    if user_choice == '1':
                        result = Client.Client.create_account_for_client(user_id, user_type)
                        print(result)
                    elif user_choice == '2':
                        user_balance = view_balance(user_id)
                        print(f"Баланс вашего счета: {user_balance}")
                    elif user_choice == '3':
                        perform_transfer(user_id)
                        continue
                    elif user_choice == '4':
                        new_name = input('Введите новое имя: ')
                        new_phone = input("Введите новый номер телефона: ")
                        new_email = input("Введите новый адрес эл.почты: ")
                        new_password = input("Введите новый пароль: ")
                        result = Client.Client.update_client_info_individual(user_id, new_name, new_phone, new_email,
                                                                             new_password)
                        print(result)
                    elif user_choice == '5':
                        account_id = int(input('Введите ID клиента:'))
                        result = money_cash(account_id)
                        print(result)
                    elif user_choice == '0':
                        print("Выход из личного кабинета.")
                        break
                    else:
                        print("Некорректный выбор.")
                elif user_type == 'Юридическое лицо':
                    while True:
                        print("1. Создать счёт.")
                        print("2. Просмотр баланса.")
                        print("3. Выплатить ЗП сотрудникам.")
                        print("4. Изменить данные.")
                        print("5. Переводы между счетами.")
                        print("0. Выйти из личного_кабинета.")
                        user_choice = input("Выберите пункт : ")
                        if user_choice == '1':
                            result = Client.Client.create_account_for_client(user_id, user_type)
                            print(result)
                        elif user_choice == '2':
                            company_balance = view_balance(user_id)
                            print(f"Баланс компании: {company_balance}")
                        elif user_choice == '3':
                            sender = input('Введите ID отправителя: ')
                            recipient = input('Введите ID получателя: ')
                            salary = int(input('Введите сумму зарплаты: '))
                            result = pay_salary(sender, recipient, salary)
                            print(result)
                        elif user_choice == '4':
                            new_name = input('Введите новое название компании: ')
                            new_director_name = input("Введите новое имя директора: ")
                            new_phone = input("Введите новый номер телефона: ")
                            new_email = input("Введите новый адрес эл.почты: ")
                            new_password = input("Введите новый пароль: ")
                            result = Client.Client.update_client_info_company(user_id, new_name, new_director_name,
                                                                              new_phone, new_email, new_password)
                            print(result)
                        elif user_choice == '5':
                            perform_transfer(user_id)
                        elif user_choice == '0':
                            print("Выход из личного кабинета.")
                            break
                        else:
                            print("Некорректный выбор.")
            else:
                print("Ошибка входа. Проверьте почту/телефон и пароль.")
        elif choice == '0':
            print("Программа завершена.")
            break
        else:
            print("Некорректный выбор")


if __name__ == "__main__":
    main()
