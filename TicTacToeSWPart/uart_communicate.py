import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, scrolledtext


class UARTCommunication:
    def __init__(self):
        self.ser = None
        self.baud_rate = 9600
        self.access_denied_shown = False
        self.stop_auto_receive = False

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port):
        if self.ser and self.ser.is_open:
            self.ser.close()

        try:
            self.ser = serial.Serial(port, self.baud_rate, timeout=1)
            self.access_denied_shown = False
            self.stop_auto_receive = False
            return f"Connected to {port} at {self.baud_rate} baud"
        except serial.SerialException as e:
            self.ser = None
            if not self.access_denied_shown:
                self.access_denied_shown = True
                return f"Error: Could not open port {port} - {e}"
            return ""
        except PermissionError as e:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = None
            if not self.access_denied_shown:
                self.access_denied_shown = True
                self.stop_auto_receive = True
                return f"Error: Access denied to port {port} - {e}"
            return ""

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser.baudrate = baud_rate
            self.ser.open()

    def send_message(self, message):
        if self.ser and self.ser.is_open:
            self.ser.write((message + "\n").encode())
            return f"Sent: {message}"
        return "Port not opened"

    def receive_message(self):
        if self.ser and self.ser.is_open:
            try:
                response = self.ser.readline().decode("utf-8", errors="replace").strip()
                if response:
                    return response
            except Exception as e:
                self.stop_auto_receive = True
                return f"Error: {e}"
        return "Port not opened"


def auto_receive(uart, output_text, status_label, root):
    if uart.stop_auto_receive:
        return

    response = uart.receive_message()
    if response and response != "Port not opened":
        output_text.insert(tk.END, f"Received: {response}\n")
        output_text.see(tk.END)
    root.after(100, lambda: auto_receive(uart, output_text, status_label, root))


def start_gui():
    uart = UARTCommunication()
    root = tk.Tk()
    root.title("UART Communication Interface")
    root.configure(bg="#FFF3E0")  # Soft peach background color

    # Header Section
    header_frame = tk.Frame(root, bg="#FF7043", pady=15)
    header_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
    header_label = tk.Label(header_frame, text="UART Communication Interface", font=("Arial", 18, "bold"), fg="white",
                            bg="#FF7043")
    header_label.pack()

    # Port Selection
    port_label = tk.Label(root, text="Select Port:", font=("Arial", 12), bg="#FFF3E0")
    port_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly", width=25,
                                 font=("Arial", 12))
    port_combobox.grid(row=1, column=1, padx=10, pady=10)

    # Baud Rate Selection
    baud_label = tk.Label(root, text="Baud Rate:", font=("Arial", 12), bg="#FFF3E0")
    baud_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

    baud_var = tk.StringVar(value="9600")
    baud_combobox = ttk.Combobox(root, textvariable=baud_var, values=["4800", "9600", "19200", "57600", "115200"],
                                 state="readonly", width=25, font=("Arial", 12))
    baud_combobox.grid(row=2, column=1, padx=10, pady=10)

    def update_baud_rate():
        try:
            baud_rate = int(baud_var.get())
            uart.set_baud_rate(baud_rate)
            status_label.config(text=f"Baud rate set to {baud_rate}", fg="#43A047")  # Dark green
        except ValueError:
            status_label.config(text="Invalid baud rate selected", fg="#D32F2F")  # Red

    baud_combobox.bind("<<ComboboxSelected>>", lambda _: update_baud_rate())

    # Open Port Button (Soft Orange)
    open_button = tk.Button(root, text="Open Port", command=lambda: open_port_callback(), bg="#FFB74D", fg="white",
                            font=("Arial", 12, "bold"), relief="flat", width=15, height=2, borderwidth=3)
    open_button.grid(row=1, column=2, padx=20, pady=10)

    # Send Message Section
    message_label = tk.Label(root, text="Message:", font=("Arial", 12), bg="#FFF3E0")
    message_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")

    message_entry = tk.Entry(root, width=25, font=("Arial", 12))  # No border
    message_entry.grid(row=3, column=1, padx=10, pady=10)

    def send_message_callback():
        status = uart.send_message(message_entry.get())
        status_label.config(text=status, fg="#388E3C" if "Sent" in status else "#D32F2F")  # Green for success, red for error

    # Send Button (Soft Orange)
    send_button = tk.Button(root, text="Send", command=send_message_callback, bg="#FFB74D", fg="white",
                            font=("Arial", 12, "bold"), relief="flat", width=15, height=2, borderwidth=3)
    send_button.grid(row=3, column=2, padx=20, pady=10)

    # Output Text Area (White background)
    output_text = scrolledtext.ScrolledText(root, width=70, height=15, wrap=tk.WORD, font=("Arial", 12), bd=2,
                                            relief="solid", bg="white")
    output_text.grid(row=4, column=0, columnspan=3, padx=20, pady=10)

    # Status Label
    status_label = tk.Label(root, text="Status: Not connected", fg="#FB8C00", font=("Arial", 12), bg="#FFF3E0")  # Orange for initial status
    status_label.grid(row=5, column=0, columnspan=3, padx=20, pady=10)

    # Open Port Callback
    def open_port_callback():
        status = uart.open_port(port_var.get())
        if status:
            status_label.config(text=status, fg="#43A047" if "Connected" in status else "#D32F2F")  # Green for success, red for error
        if "Connected" in status:
            auto_receive(uart, output_text, status_label, root)

    # Run the GUI
    root.mainloop()


if __name__ == "__main__":
    start_gui()
