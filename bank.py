import json
import hashlib
import hmac
import secrets
import string
from pathlib import Path
from datetime import datetime

class Bank:
    """Educational banking application with JSON-based storage."""

    DATABASE = Path(__file__).with_name("data.json")

    def __init__(self):
        self.data = self.load_data()

    def load_data(self):
        try:
            if not self.DATABASE.exists():
                return []
            with self.DATABASE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Database must contain a list of accounts.")
            return data
        except (json.JSONDecodeError, OSError, ValueError) as error:
            raise RuntimeError(f"Could not load the database: {error}") from error

    def save_data(self):
        """Write to a temporary file first, then replace the database."""
        temporary_file = self.DATABASE.with_suffix(".tmp")
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)
        temporary_file.replace(self.DATABASE)

    @staticmethod
    def hash_pin(pin, salt=None):
        salt = salt or secrets.token_hex(16)
        pin_hash = hashlib.pbkdf2_hmac(
            "sha256", pin.encode("utf-8"), salt.encode("utf-8"), 200_000
        ).hex()
        return salt, pin_hash

    @staticmethod
    def verify_pin(pin, account):
        salt, expected_hash = account["pin_salt"], account["pin_hash"]
        _, actual_hash = Bank.hash_pin(pin, salt)
        return hmac.compare_digest(actual_hash, expected_hash)

    def generate_account_number(self):
        existing = {account["account_number"] for account in self.data}
        while True:
            number = "ABC" + "".join(secrets.choice(string.digits) for _ in range(8))
            if number not in existing:
                return number

    def find_account(self, account_number, pin):
        for account in self.data:
            if account["account_number"] == account_number:
                if self.verify_pin(pin, account):
                    return account
                return None
        return None

    def create_account(self, name, age, email, pin):
        name, email = name.strip(), email.strip().lower()
        if not name:
            raise ValueError("Name cannot be empty.")
        if age < 18:
            raise ValueError("You must be at least 18 years old.")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Enter a valid email address.")
        if len(pin) != 4 or not pin.isdigit():
            raise ValueError("PIN must contain exactly four digits.")

        salt, pin_hash = self.hash_pin(pin)
        account = {
            "name": name,
            "age": age,
            "email": email,
            "pin_salt": salt,
            "pin_hash": pin_hash,
            "account_number": self.generate_account_number(),
            "balance": 0.0,
            "transactions": [{
                "type": "Account opened",
                "amount": 0.0,
                "date": datetime.now().isoformat(timespec="seconds")
            }]
        }
        self.data.append(account)
        self.save_data()
        return account["account_number"]

    def deposit(self, account_number, pin, amount):
        account = self.find_account(account_number, pin)
        if account is None:
            raise ValueError("Account number or PIN is incorrect.")
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")
        account["balance"] = round(account["balance"] + amount, 2)
        self.add_transaction(account, "Deposit", amount)
        self.save_data()
        return account["balance"]

    def withdraw(self, account_number, pin, amount):
        account = self.find_account(account_number, pin)
        if account is None:
            raise ValueError("Account number or PIN is incorrect.")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > account["balance"]:
            raise ValueError("Insufficient balance.")
        account["balance"] = round(account["balance"] - amount, 2)
        self.add_transaction(account, "Withdrawal", amount)
        self.save_data()
        return account["balance"]

    @staticmethod
    def add_transaction(account, transaction_type, amount):
        account["transactions"].append({
            "type": transaction_type,
            "amount": round(amount, 2),
            "date": datetime.now().isoformat(timespec="seconds")
        })

    def get_account_details(self, account_number, pin):
        account = self.find_account(account_number, pin)
        if account is None:
            raise ValueError("Account number or PIN is incorrect.")
        # Never return the PIN hash or salt to the user interface.
        return {
            key: value for key, value in account.items()
            if key not in ("pin_salt", "pin_hash")
        }

    def update_account(self, account_number, pin, name=None, age=None, email=None, new_pin=None):
        account = self.find_account(account_number, pin)
        if account is None:
            raise ValueError("Account number or PIN is incorrect.")

        if name is not None:
            if not name.strip():
                raise ValueError("Name cannot be empty.")
            account["name"] = name.strip()
        if age is not None:
            if age < 18:
                raise ValueError("Account holder must be at least 18.")
            account["age"] = age
        if email is not None:
            email = email.strip().lower()
            if "@" not in email or "." not in email.split("@")[-1]:
                raise ValueError("Enter a valid email address.")
            account["email"] = email
        if new_pin:
            if len(new_pin) != 4 or not new_pin.isdigit():
                raise ValueError("New PIN must contain exactly four digits.")
            salt, pin_hash = self.hash_pin(new_pin)
            account["pin_salt"] = salt
            account["pin_hash"] = pin_hash

        self.save_data()

    def delete_account(self, account_number, pin):
        account = self.find_account(account_number, pin)
        if account is None:
            raise ValueError("Account number or PIN is incorrect.")
        if account["balance"] != 0:
            raise ValueError("Withdraw the remaining balance before deleting the account.")
        self.data.remove(account)
        self.save_data()
