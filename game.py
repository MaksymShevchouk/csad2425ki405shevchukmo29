"""
@file
@brief Python GUI and serial communication interface for a Tic-Tac-Toe game.
"""

import threading
import serial
import serial.tools.list_ports
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox

class UARTCommunication:
    """
    @class UARTCommunication
    @brief Handles UART communication with the Tic-Tac-Toe game running on an Arduino.
    """
    def __init__(self):
        """
        @brief Constructor initializes the serial connection as None.
        """
        self.ser = None

    def list_ports(self):
        """
        @brief Lists all available serial ports.

        @return A list of available port names.
        """
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port, baud_rate=9600):
        """
        @brief Opens a serial port connection.

        @param port The port name to open.
        @param baud_rate The baud rate for the connection (default: 9600).
        @return A message indicating success or error.
        """
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            return f"Connected to {port}"
        except Exception as e:
            self.ser = None
            return f"Error: {e}"

    def send_message(self, message):
        """
        @brief Sends a JSON-encoded message over the serial connection.

        @param message A dictionary containing the message data.
        @return A message indicating success or error.
        """
        if self.ser and self.ser.is_open:
            try:
                json_message = json.dumps(message)
                self.ser.write((json_message + "\n").encode())
                return f"Sent: {json_message}"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

    def receive_message(self):
        """
        @brief Receives a JSON-encoded message from the serial connection.

        @return A dictionary with the received data, or an error message.
        """
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode().strip()
                    if response:
                        json_response = json.loads(response)
                        return json_response
            except json.JSONDecodeError:
                return "Error: Invalid JSON received"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

def update_game_board(board, buttons):
    """
    @brief Updates the GUI buttons to reflect the current state of the Tic-Tac-Toe board.

    @param board A 2D list representing the board state.
    @param buttons A 2D list of tkinter buttons.
    """
    for i in range(3):
        for j in range(3):
            buttons[i][j].config(text=board[i][j], font=("Arial", 14))

def send_move(uart, row, col):
    """
    @brief Sends a MOVE command to the game.

    @param uart The UARTCommunication instance.
    @param row The row index of the move (0-based).
    @param col The column index of the move (0-based).
    """
    message = {"command": "MOVE", "row": row, "col": col}
    uart.send_message(message)

def set_mode(uart, mode):
    """
    @brief Sends a MODE command to set the game mode.

    @param uart The UARTCommunication instance.
    @param mode The mode to set (0: User vs User, 1: User vs AI, 2: AI vs AI).
    """
    message = {"command": "MODE", "mode": mode}
    uart.send_message(message)

def reset_game(uart):
    """
    @brief Sends a RESET command to restart the game.

    @param uart The UARTCommunication instance.
    """
    message = {"command": "RESET"}
    uart.send_message(message)

def auto_receive(uart, buttons, output_text, root):
    """
    @brief Automatically checks for incoming messages and updates the GUI.

    @param uart The UARTCommunication instance.
    @param buttons A 2D list of tkinter buttons.
    @param output_text The tkinter scrolled text widget for displaying messages.
    @param root The main tkinter window.
    """
    try:
        if uart.ser and uart.ser.is_open:
            response = uart.receive_message()
            if response and response != "Port not opened":
                if isinstance(response, dict):
                    if "board" in response:
                        update_game_board(response["board"], buttons)
                    else:
                        output_text.insert(tk.END, f"Game status: {response['message']}\n")

                    if response.get("type") == "win_status":
                        thread = threading.Thread(target=messagebox.showinfo, args=("Win Status", response.get("message")))
                        thread.start()
                else:
                    output_text.insert(tk.END, f"Received: {response}\n")
                output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
    root.after(100, lambda: auto_receive(uart, buttons, output_text, root))

def start_gui():
    """
    @brief Initializes and runs the GUI for the Tic-Tac-Toe game interface.
    """
    uart = UARTCommunication()

    root = tk.Tk()
    root.title("TicTacToe Game Interface")
    root.config(bg="#f0f0f0")

    # Port selection
    port_label = tk.Label(root, text="Select Port:", font=("Arial", 10), bg="#f0f0f0")
    port_label.grid(row=0, column=0, padx=10, pady=5)
    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly", font=("Arial", 10))
    port_combobox.grid(row=0, column=1, padx=10, pady=5)

    def open_port_callback():
        """
        @brief Callback function for opening the selected port.
        """
        status = uart.open_port(port_var.get())
        status_label.config(text=status)
        if "Connected" in status:
            auto_receive(uart, buttons, output_text, root)
        else:
            output_text.insert(tk.END, f"Failed to connect: {status}\n")

    open_button = tk.Button(root, text="Open Port", command=open_port_callback, font=("Arial", 10), relief="solid", width=10, height=1)
    open_button.grid(row=0, column=2, padx=10, pady=5)

    # Game board buttons
    buttons = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            button = tk.Button(root, text=" ", width=8, height=2, font=("Arial", 14), relief="solid",
                               command=lambda row=i, col=j: send_move(uart, row, col), bg="#e0e0e0")
            button.grid(row=i + 1, column=j, padx=5, pady=5)
            buttons[i][j] = button

    # Mode selection
    mode_label = tk.Label(root, text="Select Game Mode:", font=("Arial", 10), bg="#f0f0f0")
    mode_label.grid(row=4, column=0, padx=10, pady=5)
    mode_var = tk.StringVar(value="User vs User")
    mode_combobox = ttk.Combobox(root, textvariable=mode_var, values=["User vs User", "User vs AI", "AI vs AI"], state="readonly", font=("Arial", 10))
    mode_combobox.grid(row=4, column=1, padx=10, pady=5)

    def set_mode_callback():
        """
        @brief Callback function for setting the game mode.
        """
        mode_index = mode_combobox.current()
        set_mode(uart, mode_index)
        status_label.config(text=f"Game mode set to {mode_combobox.get()}")

    mode_button = tk.Button(root, text="Set Mode", command=set_mode_callback, font=("Arial", 10), relief="solid", width=10, height=1)
    mode_button.grid(row=4, column=2, padx=10, pady=5)

    # Reset button
    reset_button = tk.Button(root, text="Reset", command=lambda: reset_game(uart), font=("Arial", 10), relief="solid", width=10, height=1)
    reset_button.grid(row=5, column=1, padx=10, pady=5)

    # Output text area
    output_text = scrolledtext.ScrolledText(root, width=40, height=8, wrap=tk.WORD, font=("Arial", 10))
    output_text.grid(row=6, column=0, columnspan=3, padx=10, pady=5)

    # Status label
    status_label = tk.Label(root, text="Status: Not connected", fg="blue", font=("Arial", 10), bg="#f0f0f0")
    status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
