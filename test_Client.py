import unittest
from Client import is_valid_name, is_valid_phone
import Client
from unittest.mock import patch, MagicMock
import hashlib


class TestIsValidName(unittest.TestCase):
    def test_valid_names(self):
        valid_names = ["Иванов Иван", "Анна-Мария", "Петр Алексеевич", "Егор"]
        for name in valid_names:
            with self.subTest(name=name):
                self.assertTrue(is_valid_name(name), f"Ожидалось, что {name} является допустимым именем.")

    def test_invalid_names(self):
        invalid_names = ["12345", "John Smith", "Иван@Петрович"]
        for name in invalid_names:
            with self.subTest(name=name):
                self.assertFalse(is_valid_name(name), f"Ожидалось, что {name} не является допустимым именем.")

    def test_empty_name(self):
        empty_name = " "
        self.assertTrue(is_valid_name(empty_name), f"Ожидалось, что {empty_name} является допустимым именем.")


class TestIsValidPhone(unittest.TestCase):
    @patch('builtins.input', side_effect=['123 456 78 90'])
    def test_valid_phone_format(self, mock_input):
        with unittest.mock.patch('builtins.print') as mock_print:
            result = is_valid_phone()
            mock_print.assert_not_called()
            self.assertEqual(result, '123 456 78 90')

    @patch('builtins.input', side_effect=['1234', '123 45 67', '123 456 78 901', '123 456 78 90'])
    def test_invalid_phone_format(self, mock_input):
        with unittest.mock.patch('builtins.print') as mock_print:
            result = is_valid_phone()
            mock_print.assert_called_with("Некорректный формат телефона. Пожалуйста, введите еще раз.")
            self.assertEqual(result, '123 456 78 90')


class TestUpdateClientInfoCompany(unittest.TestCase):
    @patch('your_module.connect_to_db')
    def test_update_client_info_company(self, mock_connect):
        # Создаем мок-объекты для connect_to_db
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = (mock_conn, mock_cursor)

        # Параметры для теста
        client_id = 1
        new_name = 'New Company'
        new_director_name = 'New Director'
        new_phone = '123 456 78 90'
        new_email = 'new_email@example.com'
        new_password = 'new_password'

        # Вызываем функцию
        result = Client.Client.update_client_info_company(client_id, new_name, new_director_name, new_phone, new_email, new_password)

        # Проверяем, что функция вернула ожидаемое сообщение
        self.assertEqual(result, 'Данные успешно обновлены.')

        # Проверяем, что были вызваны ожидаемые SQL-запросы
        expected_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        mock_cursor.execute.assert_called_once_with('UPDATE clients SET full_name = ?, director_name = ?, phone = ?,'
                                                    ' email = ?, password = ? WHERE id = ?',
                                                    (new_name, new_director_name, new_phone, new_email,
                                                     expected_password_hash, client_id))
        mock_cursor.execute.assert_called_once_with('UPDATE accounts SET owner_name = ? WHERE client_id = ?',
                                                    (new_name, client_id))

        # Проверяем, что соединение было закрыто
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
