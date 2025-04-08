
from datetime import datetime, timedelta, date
from collections import UserDict
from tabulate import tabulate
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# === Декоратор обробки помилок ===
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError:
            return "Give me correct name and phone."
        except IndexError:
            return "Enter all required fields."
        except Exception as e:
            return f"Error: {str(e)}"
    return inner

# === Класи ===
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        self.email = None
        self.address = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return True
        return False

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        return f"{self.name.value}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        start_period = today + timedelta(days=(7 - today.weekday()))
        end_period = start_period + timedelta(days=6)
        upcoming = {}

        for record in self.data.values():
            if record.birthday:
                bday_this_year = record.birthday.value.replace(year=today.year)
                if start_period <= bday_this_year <= end_period:
                    day = bday_this_year.weekday()
                    congrats_day = start_period if day >= 5 else bday_this_year
                    weekday_str = congrats_day.strftime("%A")
                    if weekday_str not in upcoming:
                        upcoming[weekday_str] = []
                    upcoming[weekday_str].append(record.name.value)

        if not upcoming:
            return "No birthdays next week."

        result = []
        for day in sorted(upcoming):
            names = ", ".join(upcoming[day])
            result.append(f"{day}: {names}")
        return "\n".join(result)

# === Відображення та логіка ===
def show_edit_menu():
    table = [
        ["1", "Edit name"],
        ["2", "Edit phones"],
        ["3", "Edit email"],
        ["4", "Edit birthday"],
        ["5", "Edit address"]
    ]
    print(tabulate(table, headers=["Option", "Description"], tablefmt="grid"))

def print_contact_info(record):
    table = Table.grid(padding=1)
    table.add_column(justify="right", style="cyan", no_wrap=True)
    table.add_column(style="white")
    table.add_row("Name:", record.name.value)
    phones = ', '.join(p.value for p in record.phones) if record.phones else "-"
    table.add_row("Phones:", phones)
    emails = record.email if record.email else "-"
    table.add_row("Email:", emails)
    address = record.address if record.address else "-"
    table.add_row("Address:", address)
    birthday = record.birthday.value.strftime("%Y-%m-%d") if record.birthday else "-"
    table.add_row("Birthday:", birthday)

    if record.birthday:
        days_to_bday = (record.birthday.value.replace(year=date.today().year) - date.today()).days
        if days_to_bday < 0:
            days_to_bday += 365
        table.add_row("Days to birthday:", str(days_to_bday))

    panel = Panel(table, title=f"Contact: {record.name.value}", expand=False, border_style="blue")
    console.print(panel)

# === Функції ===
def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return None, []
    return parts[0].lower(), parts[1:]

@input_error
def add_contact(book, name, phone):
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return f"Contact '{name}' added or updated with phone."

@input_error
def edit_contact(book, name):
    record = book.find(name)
    if not record:
        return "Contact not found."
    show_edit_menu()
    option = input("Choose what to edit (1–5): ").strip()
    if option == "1":
        new_name = input("Enter new name: ").strip()
        book.delete(record.name.value)
        record.name = Name(new_name)
        book.add_record(record)
        return f"Name updated to '{new_name}'."
    elif option == "2":
        old = input("Enter old phone: ")
        new = input("Enter new phone: ")
        if record.edit_phone(old, new):
            return "Phone updated!"
        return "Phone not found."
    elif option == "3":
        record.email = input("Enter new email: ")
        return "Email updated!"
    elif option == "4":
        record.add_birthday(input("Enter birthday (DD.MM.YYYY): "))
        return "Birthday updated!"
    elif option == "5":
        record.address = input("Enter new address: ")
        return "Address updated!"
    return "Invalid option."

@input_error
def show_phone(book, name):
    record = book.find(name)
    if not record:
        return "Contact not found."
    return ', '.join(p.value for p in record.phones)

def show_all(book):
    if not book.data:
        return "No contacts found."
    for record in book.data.values():
        print_contact_info(record)
    return ""

# === Основний цикл ===
def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ("exit", "close"):
            print("Good bye!")
            break
        elif command == "add":
            if len(args) < 2:
                print("Please provide name and phone.")
                continue
            print(add_contact(book, args[0], args[1]))
        elif command == "edit":
            if not args:
                print("Please provide a name.")
                continue
            print(edit_contact(book, args[0]))
        elif command == "phone":
            if not args:
                print("Please provide a name.")
                continue
            print(show_phone(book, args[0]))
        elif command == "all":
            print(show_all(book))
        elif command == "birthdays":
            print(book.get_upcoming_birthdays())
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
