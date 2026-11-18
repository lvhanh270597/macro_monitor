import unittest
from unittest.mock import patch

import macro_monitor


class MacroMonitorTests(unittest.TestCase):
    @patch("macro_monitor.send_telegram_alert")
    @patch("macro_monitor.get_us30y_yield", return_value=4.25)
    @patch("macro_monitor.get_tga_data", return_value=(None, None, None))
    def test_main_handles_missing_tga_data(
        self,
        mock_get_tga_data,
        mock_get_us30y_yield,
        mock_send_telegram_alert,
    ):
        macro_monitor.main()

        mock_send_telegram_alert.assert_called_once()
        message = mock_send_telegram_alert.call_args.args[0]
        self.assertIn("Số dư TGA", message)
        self.assertIn("Không có dữ liệu", message)


if __name__ == "__main__":
    unittest.main()
