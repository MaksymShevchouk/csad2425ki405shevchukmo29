import unittest
import serial
import json
import time
import argparse
import sys


class TicTacToeArduinoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ser = serial.Serial(cls.SERIAL_PORT, cls.BAUD_RATE, timeout=1)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.ser.close()

    def send_command(self, command_dict):
        """Send a JSON command to the Arduino via serial."""
        self.ser.write((json.dumps(command_dict) + '\n').encode())
        time.sleep(0.5)

    def receive_response(self):
        """Receive a JSON response from the Arduino."""
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode().strip()
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return None
        return None

    def test_initialize_board(self):
        """Test if the board initializes correctly after reset."""
        self.send_command({"command": "RESET"})
        response1 = self.receive_response()
        response2 = self.receive_response()
        self.assertIsNotNone(response2)
        if response2["type"] == "game_status":
            self.assertEqual(response2["message"], "Game reset.")
            response2 = self.receive_response()
        self.assertEqual(response2["type"], "board")
        board_state = response2.get("board", [])
        for row in board_state:
            for cell in row:
                self.assertEqual(cell, " ")

    def test_make_valid_move(self):
        """Test if a valid move updates the board correctly."""
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        self.send_command({"command": "MOVE", "row": 0, "col": 0})
        response = self.receive_response()
        self.assertEqual(response["type"], "board")
        board_state = response.get("board", [])
        self.assertEqual(board_state[0][0], "X")

    def test_make_invalid_move(self):
        """Test if an invalid move is correctly handled."""
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        self.send_command({"command": "MOVE", "row": 0, "col": 0})
        self.receive_response()

        self.send_command({"command": "MOVE", "row": 0, "col": 0})
        response = self.receive_response()
        self.assertIsNotNone(response)
        if response["type"] == "error":
            self.assertEqual(response["message"], "Invalid move.")
        else:
            self.assertEqual(response["type"], "board")

    def test_check_win(self):
        """Test if the game detects a win correctly."""
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        moves = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)]
        for row, col in moves:
            self.send_command({"command": "MOVE", "row": row, "col": col})
            self.receive_response()

        response = self.receive_response()
        self.assertEqual(response["type"], "win_status")
        self.assertEqual(response["message"], "Player X wins!")

    def test_draw(self):
        """Test if the game correctly detects a draw."""
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        moves = [
            (0, 0), (0, 1), (0, 2),
            (1, 1), (1, 0), (1, 2),
            (2, 1), (2, 0), (2, 2)
        ]
        for row, col in moves:
            self.send_command({"command": "MOVE", "row": row, "col": col})
            self.receive_response()

        response = self.receive_response()
        self.assertEqual(response["type"], "win_status")
        self.assertEqual(response["message"], "It's a draw!")

    def test_game_mode_switch(self):
        """Test switching between different game modes."""
        self.send_command({"command": "MODE", "mode": 1})
        responses = {"game_mode": False, "game_status": False, "board": False}
        for _ in range(5):
            response = self.receive_response()
            if response:
                response_type = response["type"]
                if response_type == "game_mode":
                    responses["game_mode"] = True
                    self.assertIn("Game mode set to 1", response["message"])
                elif response_type == "game_status":
                    responses["game_status"] = True
                    self.assertEqual(response["message"], "Game reset.")

                if all(responses.values()):
                    break

        self.send_command({"command": "MODE", "mode": 2})
        responses = {"game_mode": False, "game_status": False, "board": False}

        for _ in range(5):
            response = self.receive_response()
            if response:
                response_type = response["type"]
                if response_type == "game_mode":
                    responses["game_mode"] = True
                    self.assertIn("Game mode set to 2", response["message"])
                elif response_type == "game_status":
                    responses["game_status"] = True
                    self.assertEqual(response["message"], "Game reset.")
                elif response_type == "board":
                    responses["board"] = True
                    board_state = response["board"]
                    for row in board_state:
                        for cell in row:
                            self.assertEqual(cell, " ")
                if all(responses.values()):
                    break

    def test_handle_ai_vs_ai(self):
        """Test handling AI vs AI gameplay."""
        self.send_command({"command": "MODE", "mode": 2})
        self.receive_response()
        self.receive_response()

        max_iterations = 100
        for _ in range(max_iterations):
            response = self.receive_response()
            if response and response["type"] == "win_status":
                self.assertIn(response["message"], ["Player X wins!", "Player O wins!", "It's a draw!"])
                break
        else:
            self.fail("AI vs AI test did not conclude within the iteration limit.")


if __name__ == '__main__':
    # Parse custom arguments
    parser = argparse.ArgumentParser(description="Run TicTacToe hardware tests.")
    parser.add_argument('--port', required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument('--baudrate', type=int, default=9600, help="Baud rate for serial communication")
    args, remaining_args = parser.parse_known_args()

    # Pass arguments to the test class
    TicTacToeArduinoTests.SERIAL_PORT = args.port
    TicTacToeArduinoTests.BAUD_RATE = args.baudrate

    # Remove custom arguments from sys.argv to avoid unittest conflicts
    sys.argv = [sys.argv[0]] + remaining_args

    # Run tests
    unittest.main()
