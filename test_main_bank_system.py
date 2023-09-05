import unittest
from unittest.mock import patch
from main_bank_system import get_sender_recipient_info
from database import connect_to_db, close_db_connection


class TestGetSenderRecipientInfo(unittest.TestCase):
    @patch('database.connect_to_db')
    def test_get_sender_recipient_info(self, mock_connect_db):
        # Мокируем connect_to_db
        mock_conn, mock_cursor = mock_connect_db.return_value
        mock_cursor.fetchone.return_value = (1, 'Sender Name', 'Sender Type')

        # Вызываем функцию get_sender_recipient_info
        sender_id, sender_balance, sender_type = get_sender_recipient_info(1)

        # Проверяем, что функция правильно вызывает connect_to_db
        mock_connect_db.assert_called_once()

        # Проверяем, что функция возвращает ожидаемые значения
        self.assertEqual(sender_id, 1)
        self.assertEqual(sender_balance, 'Sender Name')
        self.assertEqual(sender_type, 'Sender Type')


if __name__ == '__main__':
    unittest.main()
