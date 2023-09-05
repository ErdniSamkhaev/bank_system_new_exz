import unittest
from unittest.mock import patch, MagicMock
from main_bank_system import money_cash


class TestMoneyCash(unittest.TestCase):
    @patch('main_bank_system.connect_to_db')
    def test_successful_money_cash(self, mock_connect):
        # Создаем мок-объекты для connect_to_db
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = (mock_conn, mock_cursor)

        # Устанавливаем ожидаемые значения из базы данных
        account_info = (1, 1, 'Сберегательный', 1, 1, 1000.0)  # Пример данных счета
        mock_cursor.fetchone.return_value = account_info

        # Вызываем функцию
        result = money_cash(1)

        # Проверяем, что функция вернула ожидаемый результат
        self.assertEqual(result, "Сумма 100.0 успешно снята. Новый баланс: 900.0")


if __name__ == '__main__':
    unittest.main()
