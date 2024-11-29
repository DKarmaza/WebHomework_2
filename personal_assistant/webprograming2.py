from collections import UserDict
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
import re
import pickle

class View(ABC):
    @abstractmethod
    def display_contact(self, record):
        pass

    @abstractmethod
    def display_all_contacts(self, address_book):
        pass

    @abstractmethod
    def display_message(self, massage):
        pass

class ConsoleView(View):
    def display_contact(self, record):
        print(record)

    def display_all_contacts(self, address_book):
        print(address_book)

    def display_message(self, massage):
        print(massage)

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field): # клас ім'я
    def __init__(self, value):
        if not value:
            raise ValueError("Neme required.")
        super().__init__(value)

class Phone(Field): # клас телефон
    def __init__(self, value):
        if not self.is_valid_phone(value):
            raise ValueError("Number may contain 10 digits.")
        super().__init__(value)

    @staticmethod # валідація введенного телефону
    def is_valid_phone(value):
        return bool(re.match(r'^\d{10}$', value))

class Birthday(Field):
    def __init__(self, value):
        if not self.is_valid_birthday(value):
            raise ValueError("Wrong date, date may be like: DD.MM.YYYY")
        super().__init__(value)

    @staticmethod
    def is_valid_birthday(value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            return True
        except ValueError:
            return False

    def to_date(self):
        return datetime.strptime(self.value, "%d.%m.%Y").date()

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
    
    def add_phone(self, phone_number): # додавання телефону
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number): # видалення телефону
        phone_to_remove = None
        for phone in self.phones:
            if phone.value == phone_number:
                phone_to_remove = phone
                break
        
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError("Number not found.")

    def edit_phone(self, old_number, new_number): # зміна телефону
        if not self.find_phone(old_number):
            raise ValueError("Old number not found.")
        if not Phone.is_valid_phone(new_number): # Перевірка на правильність нового номера
            raise ValueError("New number may contain 10 digits.")
        self.remove_phone(old_number)
        self.add_phone(new_number)

    def find_phone(self, phone_number): # знайти телефон
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday_date):  # додавання дати народження
        self.birthday = Birthday(birthday_date)

    def __str__(self):
        phones_str = '; '.join(str(phone) for phone in self.phones)
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"

class AddressBook(UserDict): # клас сама книжка
    def add_record(self, record): # додавання телефону у книзі
        self.data[record.name.value] = record

    def find(self, name): # знаходження телефону у книзі
        return self.data.get(name)

    def delete(self, name): # видалення телефону у книзі
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError("Record not found.")

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())
    
    def get_upcoming_birthdays(self, days=7): #прорахунок дати дня народження
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.to_date().replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                adjusted_birthday = self.adjust_for_weekend(birthday_this_year)
                if 0 <= (adjusted_birthday - today).days <= days:
                    congratulation_date_str = adjusted_birthday.strftime("%d.%m.%Y")
                    upcoming_birthdays.append({"name": record.name.value, "congratulation_date": congratulation_date_str})

        return upcoming_birthdays

    def adjust_for_weekend(self, birthday):  # Корекція днів народження
        if birthday.weekday() == 5:  # Якщо субота
            birthday += timedelta(days=2)  # Переносимо на понеділок
        elif birthday.weekday() == 6:  # Якщо неділя
            birthday += timedelta(days=1)  # Переносимо на понеділок
        return birthday

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено
      
def input_error(func): # Обробка помилок

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            if func.__name__ == "add_contact":
                return "Give me name and phone please."
            elif func.__name__ == "change_contact":
                return "Give me name, old phone and new phone please."
            elif func.__name__ == "add_birthday":
                return "Give me name and date(DD.MM.YYYY) please."
        except IndexError:
            return "Give me name please."

    return inner

def parse_input(user_input): # Введення команд юзера
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book): # Додавання контакту
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book): #зміна контакту
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Contact updated."
    else:
        return "Contact not found."

@input_error
def show_phone(args, book): #показ номеру за іменем
    name = args[0]
    record = book.find(name)
    if record:
        return ', '.join([phone.value for phone in record.phones])
    else:
        return "Contact not found."
    
@input_error
def add_birthday(args, book): #додати дату дня народження
    name, birthday_date = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday_date)
        return "Birthday added."
    else:
        return "Contact not found."

@input_error
def show_birthday(args, book): #показати день народження за іменем
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is {record.birthday}"
    else:
        return "Contact not found."

@input_error
def birthdays(args, book): # показати всі дні народження
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays."
    result = "\n".join([f"{entry['name']}: {entry['congratulation_date']}" for entry in upcoming_birthdays])
    return result

def main():
    book = load_data()
    view = ConsoleView()
    view.display_message("Welcome to the assistant bot! Type command 'help' to get a list of available commands") # Вітання

    while True:
        user_input = input("Enter a command: ") # Введення команд
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]: # Закриття програми
            view.display_message("Good bye!")
            save_data(book)  # Збереження стану адресної книги
            break
        
        elif command in ["hello", "hi"]: # Початок роботи
            view.display_message("How can I help you?")
        
        elif command == "add": # Додати контакт
            view.display_message(add_contact(args, book))
        
        elif command == "change": # Змінити контакт
            view.display_message(change_contact(args, book))

        elif command == "phone": # Знайти за ім'ям 
            view.display_message(show_phone(args, book))

        elif command == "all": # Всі контакти 
            view.display_message(book)
        
        elif command == "add-birthday": #додати день народження
            view.display_message(add_birthday(args, book))

        elif command == "show-birthday": #показати день народження за іменем
            view.display_message(show_birthday(args, book)) 

        elif command == "birthdays": #показати всі дні народження
            view.display_message(birthdays(args, book))

        elif command == "help":
            view.display_message("""Available list of commands:
[hello, hi] - start of program, 
[close, exit] - close program and save the contact book, 
[add name number(10 digits)] - add contact, 
[change name old phone new phone] - change contact, 
[phone name] - find phone using name, 
[all] - full list of contacts, 
[add-birthday name date(DD.MM.YYYY)] - add birthday to contact, 
[show-birthday name] - find birthday using name, 
[birthdays] - full list of birthdays

Version: beta 0.0.7""")

        else:
            view.display_message("Invalid command.")

if __name__ == "__main__":
    main()
