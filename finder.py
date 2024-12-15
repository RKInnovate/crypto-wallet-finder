"""
Cryptocurrency Wallet Seed Finder

This module implements a parallel processing system to find cryptocurrency wallet seeds
by generating and testing permutations of seed phrases. It includes both the core
processing logic and a GUI interface for user interaction.

Key Features:
    - Parallel processing of seed phrase permutations
    - GUI interface for monitoring progress and results
    - Automatic progress saving and resumption
    - CSV export of found wallet addresses

The system uses Python's multiprocessing to efficiently process large numbers of
permutations while maintaining a responsive GUI interface.

Note:
    This tool requires significant CPU resources and may take considerable time
    to process all possible permutations.
"""

import os
import csv
import json
import types
import platform
import itertools
import multiprocessing
from pathlib import Path
from functools import partial
from logging.handlers import RotatingFileHandler

import re
import uuid
import logging
import threading
import tkinter as tk
from tkinter import Tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog, messagebox
import sys

import requests
from more_itertools import chunked

from crypto_wallet import CryptoWallet

app_data_dir = Path.home() / '.wallet_finder'

Path.mkdir(app_data_dir, exist_ok=True)
csv_file= app_data_dir / "found_wallets.csv"
config_file = app_data_dir / "config.json"
download_dir = Path.home() / 'Downloads'
config: dict = None
logger: logging.Logger = None

class WalletFinder:
    """
    Core wallet finding implementation using parallel processing.

    This class handles the generation and testing of wallet seed phrases using
    multiprocessing for optimal performance. It processes permutations of seed
    phrases in parallel, checking each generated wallet address against a set
    of target addresses.

    The class is designed to:
        - Utilize all available CPU cores efficiently
        - Process seed phrases in optimized chunks
        - Save progress periodically
        - Report results through callback functions

    Note:
        All methods in this class are static as it serves as a utility class
        rather than maintaining instance state.
    """
    @staticmethod
    def process(seeds: list[str], target_address: set) -> tuple[bool, list]:
        """
        Generate a wallet address from the given seed phrase and check if it matches the target address.

        Args:
            seeds (list[str]): List of words forming the seed phrase
            target_address (set): Set of target wallet addresses to match against

        Returns:
            tuple[bool, list]: A tuple containing:
                - bool: True if the generated address matches any target address, False otherwise
                - list: [seed_phrase, address] if match found, [None, None] otherwise
        """
        seeds = " ".join(map(lambda x: x.lower().strip(), seeds))
        try:
            wallet = CryptoWallet(seeds)
            address = wallet.get_trx_address()
            if str(address) in target_address:
                return True, [seeds, address]
            
        except Exception as e:
            # Don't need to log the exception if exception is value error
            if not isinstance(e, ValueError):
                print(e)

        return False, [None, None]

    @staticmethod
    def start(update_status_func: types.FunctionType, update_list_func: types.FunctionType, resume: bool = False) -> None:
        """
        Start the wallet finding process using multiprocessing.

        This function:
        1. Generates permutations of the wordlist
        2. Processes chunks of permutations in parallel
        3. Updates GUI with progress and found wallets
        4. Saves progress and found wallets to disk

        Args:
            update_status_func (types.FunctionType): Callback to update status in GUI
            update_list_func (types.FunctionType): Callback to update found wallets list in GUI
            resume (bool, optional): If True, resumes from last saved progress. Defaults to False.

        Note:
            - Uses multiprocessing for parallel processing
            - Saves progress every 10 chunks
            - Writes found wallets to CSV file immediately
        """
        num_processes = multiprocessing.cpu_count()

        combinations = itertools.permutations(wordlist, 12)
        start_from = config["progress"] if resume else 0

        logger.info('Starting Process...')
        update_status_func('Starting Process...')


        # Parallel processing
        with multiprocessing.Pool(processes=num_processes) as pool:
            chunk_size = num_processes * 10000  # Adjust as per system resources

            # Create a partial function for static arguments
            process_partial = partial(
                WalletFinder.process,
                target_address=target_address
            )

            # Process in chunks
            for index, chunk in enumerate(chunked(itertools.islice(combinations, start_from, None), chunk_size), start=int(start_from / chunk_size) - 1):
                process_count = (index + 1) * chunk_size
                update_status_func(f'Checking Wallet: {"{:,}".format(process_count)}\t({num_processes} cores)')
                result = pool.map(process_partial, chunk)

                for success, [seeds, address] in result:
                    if not success:
                        continue

                    logger.info(f"Found address: {address} with seed: {seeds}")
                    with open(csv_file, mode="a", newline="", encoding='utf-8') as file:
                        csv_writer = csv.writer(file)
                        csv_writer.writerow([seeds, address])
                    update_list_func(seeds, address)

                # Update config progress value
                if index % 10 == 0:
                    config["progress"] = (index + 1) * chunk_size
                    save_config()

class WalletFinderGUI:
    """
    Graphical user interface for the wallet finder application.

    This class provides a Tkinter-based GUI that allows users to:
        - Input target wallet addresses
        - Select wordlist files
        - Monitor processing progress
        - View found wallet addresses in real-time
        - Save and resume progress

    The GUI is designed to remain responsive during intensive processing by
    using separate threads for UI updates and background processing.

    Attributes:
        root (Tk): The main Tkinter window
        addresses (set): Set of target wallet addresses to search for
        result_list (list): List to store found wallet results
    """
    def __init__(self, tk_root: Tk) -> None:
        """
        Initializes the WalletFinderGUI with the given Tkinter root and config.

        Args:
            root (Tk): The Tkinter root window.
        """
        global target_address, wordlist

        logger.info('TKInter Version: %s', tk.TkVersion)

        self.root = tk_root
        self.root.title("Wallet Finder")
        self.root.geometry("1000x500")

        # Set window icon
        try:
            # For packaged app
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, 'icon.png')
            if os.path.exists(icon_path):
                icon_img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon_img)
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")

        self.result_list = []  # List to store results (seed, address)
        
        self.addresses = set(config.get("addresses", []))
        target_address = set(self.addresses)

        wordlist = load_wordlist(config.get("wordlist_file")) if config.get("wordlist_file") else []
        self.create_widgets()

    def create_widgets(self):
        """
        Creates the UI widgets for the application, including buttons for adding
        addresses, selecting the wordlist file, displaying the listbox for results,
        and status bar.
        """

        # Add Address Button
        self.add_address_button = tk.Button(self.root, text="Edit Addresses" if len(self.addresses) > 0 else "Add Addresses", command=self.add_addresses)
        self.add_address_button.pack(pady=10)

        wordlist_file = config.get("wordlist_file")

        # Select Wordlist File Button
        self.select_wordlist_button = tk.Button(self.root, text="Select Wordlist File" if not wordlist_file else "Change Wordlist File", command=self.select_wordlist_file)
        self.select_wordlist_button.pack(pady=10)

        # Status Bar
        self.status_label = tk.Label(self.root, text="Status: Idle", anchor="w", relief="sunken", bd=1)
        self.status_label.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        # Listbox to display results (seed, address)
        self.result_listbox = ttk.Treeview(self.root, columns=("Seed", "Address"), show="headings")
        self.result_listbox.heading("Seed", text="Seed Phrase")
        self.result_listbox.heading("Address", text="TRX Address")
        self.result_listbox.pack(pady=(0, 20), padx=10, fill=tk.BOTH, expand=True)
        
        # Start and Stop Buttons
        self.start_button = tk.Button(self.root, text="Start", command=self.start_process)
        self.start_button.pack(side=tk.LEFT, padx=20, pady=10)

        self.stop_button = tk.Button(self.root, text="Quit", command=self.quit)
        self.stop_button.pack(side=tk.RIGHT, padx=20, pady=10)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def add_addresses(self):
        """
        Opens a new window where the user can input wallet addresses manually.
        These addresses are converted into a list and displayed in the main window.
        """
        # Create a new window to input addresses
        address_window = tk.Toplevel(self.root)
        address_window.title("Enter TRX Addresses")
        address_window.geometry("300x400")

        # Create a scrolled text box for addresses input
        address_textbox = scrolledtext.ScrolledText(address_window, wrap=tk.WORD, width=35, height=25)
        address_textbox.pack(pady=10)

        if self.addresses:
            address_textbox.insert(tk.INSERT, "\n".join(self.addresses))

        # Create a button to convert addresses to list
        def convert_addresses():
            """
            Converts the addresses entered in the textbox into a list and
            updates the main window's result listbox.
            """
            global target_address

            addresses_str = address_textbox.get("1.0", tk.END).strip()
            
            if ',' in addresses_str:
                addresses = addresses_str.split(',')
            else:
                addresses = addresses_str.splitlines()

            addresses = [re.sub(r'[,"\'\s]', '', address) for address in addresses if address.strip()]  # Clean and split
            self.addresses.update(addresses)
            config["addresses"] = list(self.addresses)
            save_config()
            target_address = set(self.addresses)
            self.add_address_button.config(text="Edit Addresses")
            address_window.destroy()

        convert_button = tk.Button(address_window, text="Add", command=convert_addresses)
        convert_button.pack(pady=10)

    def safe_update_listbox(self, seed, address):
        """
        Safely updates the listbox in the main thread using the `after` method.
        This ensures thread-safety when updating the GUI from a background thread.

        Args:
            seed (str): The seed phrase corresponding to the address.
            address (str): The wallet address to be displayed.
        """
        self.root.after(0, self._update_listbox, seed, address)

    def _update_listbox(self, seed, address):
        """
        Updates the listbox widget with a new seed phrase and address.

        Args:
            seed (str): The seed phrase to be inserted into the listbox.
            address (str): The wallet address to be inserted into the listbox.
        """
        self.result_listbox.insert("", "end", values=(seed, address))

    def select_wordlist_file(self):
        """
        Opens a file dialog to allow the user to select a wordlist file for wallet recovery.
        The selected file path is stored in the config instance.

        Raises:
            messagebox: Displays an informational message if a file is selected, or a warning if no file is selected.
        """
        global wordlist
        # Open a file dialog to select the wordlist file
        file_path = filedialog.askopenfilename(title="Select Wordlist File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))

        if file_path:
            wordlist = load_wordlist(file_path)
            config["wordlist_file"] = file_path
            save_config()
        else:
            messagebox.showwarning("No File", "No file was selected!")

    def start_process(self):
        """
        Starts the wallet recovery process in a new thread. This simulates a long-running process
        and updates the status bar and result listbox as new addresses are found.

        This method creates a new thread to run the `run_process` method, allowing the GUI to remain responsive.
        """
        self.update_status("Processing...")
        thread = threading.Thread(target=self.run_process, daemon=True)
        thread.start()

    def run_process(self):
        """
        Simulates a long-running process (e.g., wallet recovery). This is a placeholder method
        and should be replaced with actual wallet recovery logic.

        The method runs in a separate thread to avoid freezing the UI, and updates the status
        and result listbox during the process.
        """
        global wordlist, target_address
        resume = False

        try:
            # Validate the device with the API key
            success, status, status_code = validate_device()
            if not success or status_code != 200:
                messagebox.showerror("Device Validation Failed", f"Device validation failed with status: {status}")
                self.update_status(f"Device validation failed with status: {status}")
                return
        
        except Exception as e:
            messagebox.showerror("Device Validation Error", f"Device validation failed: {e}")
            self.update_status(f"Device validation failed: {e}")
            return

        if not wordlist and config.get("wordlist_file"):
            wordlist = load_wordlist(config.get("wordlist_file"))

        if not wordlist:
            messagebox.showerror("No Wordlist", "No wordlist file selected!")
            self.update_status("No wordlist file selected!")
            return

        if not target_address:
            messagebox.showwarning("No Address", "No TRX address added! Please add an address.")
            self.update_status("No TRX address added! Please add an address.")
            return
        
        if config["progress"] > 0:
            resume = messagebox.askyesno("Progress", "Do you want to continue from the last progress?")

        # Initialize the WalletFinder instance
        finder = WalletFinder()

        finder.start(self.update_status, self.safe_update_listbox, resume)

    def quit(self):
        """
        Exits the application gracefully by destroying the root window and quitting the main loop.
        """

        # copy the found wallets to the main csv file in download folder
        try:
            copy_found_wallets()
            messagebox.showinfo("Success", "Found wallets file has been saved to the download folder.")
        except ValueError:
            pass

        self.root.destroy()
        self.root.quit()
        exit(0)

    def update_status(self, status):
        """
        Updates the status bar with the provided status text. This method is thread-safe
        and ensures the GUI remains responsive during background processes.

        Args:
            status (str): The status message to be displayed on the status bar.
        """
        self.root.after(0, self._update_status, status)

    def _update_status(self, status):
        """
        Helper method that updates the status label widget with the given status text.

        Args:
            status (str): The status message to be displayed on the status label.
        """
        self.status_label.config(text=f"Status: {status}")

def logger_config() -> None:
    """
    Set up the logger for the application. The logger writes log messages to a rotating log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    global logger

    # Set up the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    max_log_size = 25 * 1024 * 1024  # 25 MB
    backup_count = 5  # Keep last 5 log files

    # Log message format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File Handler for persistent logging
    file_handler = RotatingFileHandler(app_data_dir / 'execution.log', maxBytes=max_log_size, backupCount=backup_count)
    file_handler.setLevel(logger.level)
    file_handler.setFormatter(formatter)

    # Console Handler for displaying log messages in the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info("Logging initialized")
    logger.info("Running on %s %s", platform.system(), platform.release())

def load_wordlist(filename='bip39_wordlist.txt') -> list[str]:
    """
    Load a wordlist from a specified file.

    Args:
        filename (str): The file name containing the wordlist (default is 'bip39_wordlist.txt').

    Returns:
        list: A list of seed words loaded from the file.
    """
    with open(filename, 'r', encoding="utf-8") as f:
        return f.read().splitlines()

def get_config() -> None:
    """
    Retrieve configuration data from the config.json file.

    If the configuration file does not exist, it creates a new one with default settings.

    Returns:
        dict: The loaded or default configuration data.
    """
    global config
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        # Save default configuration to the file
        config = {
            "device_id": str(uuid.uuid4()),
            "device_mac": hex(uuid.getnode()),
            "device_name": platform.node(),
            "progress": 0,
            "wordlist_file": ""
        }
        save_config()

def save_config() -> None:
    """
    Save the current configuration data to the config.json file.

    This function updates the configuration file with the current settings.
    """
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def copy_found_wallets():
    """
    Copy the found wallets to the main CSV file in the download folder.

    This function copies the found wallets from the application data directory to the download directory.
    """
    # Check for the empty file. If it is empty, do not copy. and raise an error to prevent the message box from showing
    if os.stat(csv_file).st_size <= 25:
        raise ValueError("No wallets found to copy.")

    os.system(f'cp {csv_file} {download_dir / "found_wallets.csv"}')
    logger.info("Found wallets copied to the download directory.")

def validate_device() -> bool:
    """
    Validate the device with the API key.

    This function sends a POST request to the API to validate the device with the provided API key.


    Returns:
        bool: True if the device is validated; False otherwise.

    Raises:
        Exception: If the request fails or an error occurs during the validation process
    """
    request_data = {
        "device_id": config.get("device_id"),
        "device_mac": config.get("device_mac"),
        "device_name": config.get("device_name")
    }

    if config.get("api_key"):
        request_data["api_key"] = config.get("api_key")

    try:
        response = requests.post("https://us-central1-crypto-wallet-recovery.cloudfunctions.net/gcp-wallet-finder-validate-device", json=request_data, timeout=120)
    except requests.exceptions.RequestException as e:
        logger.error("Device validation failed: %s", e)
        raise Exception("Device validation failed. Please check your internet connection.")
    
    response_data = response.json()
    logger.info("Device validation response: %s", json.dumps(response_data, indent=4))

    if response.status_code == 201:
        config["api_key"] = response_data.get("api_key")
        save_config()

    return response_data.get("success", False), response_data.get("message", "Unknown Error"), response.status_code

if __name__ == "__main__":
    # Fix for PyInstaller + multiprocessing on macOS
    multiprocessing.freeze_support()
    
    # Set multiprocessing start method to 'spawn' for macOS
    if platform.system().lower() == 'darwin':
        multiprocessing.set_start_method('spawn')
    
    system = platform.system().lower()

    if not os.path.exists(csv_file):
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Seed Phrase", "TRX Address"])

    get_config()
    logger_config()
    logger.info("Application started")
    logger.info("Configuration loaded: %s", json.dumps(config, indent=4))

    root = Tk()
    app = WalletFinderGUI(root)
    root.mainloop()
