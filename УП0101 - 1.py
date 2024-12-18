import sqlite3
from datetime import datetime
from tkinter import Tk, Frame, Label, Entry, Button, Listbox, Toplevel, StringVar, OptionMenu, messagebox


# --- Функции для работы с базой данных ---
def setup_database():
    conn = sqlite3.connect('repair_requests.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_added TEXT,
            equipment TEXT,
            issue_type TEXT,
            description TEXT,
            client TEXT,
            status TEXT,
            date_completed TEXT,
            responsible TEXT,
            comments TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Добавляем пользователя по умолчанию
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password)
        VALUES ('admin', 'admin123')
    ''')
    conn.commit()
    conn.close()


def list_requests():
    conn = sqlite3.connect('repair_requests.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests")
    results = cursor.fetchall()
    conn.close()
    return results


def get_request_by_id(request_id):
    conn = sqlite3.connect('repair_requests.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    request = cursor.fetchone()
    conn.close()
    return request


def update_request(request_id, equipment, issue_type, description, client, responsible, status):
    conn = sqlite3.connect('repair_requests.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE requests
        SET equipment = ?, issue_type = ?, description = ?, client = ?, responsible = ?, status = ?
        WHERE id = ?
    ''', (equipment, issue_type, description, client, responsible, status, request_id))
    conn.commit()
    conn.close()


def count_requests_by_status():
    conn = sqlite3.connect('repair_requests.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT status, COUNT(*) FROM requests GROUP BY status
    ''')
    stats = cursor.fetchall()
    conn.close()
    return stats


def verify_user(username, password):
    conn = sqlite3.connect('repair_requests.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user


# --- Страницы приложения ---
class LoginPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        Label(self, text="Авторизация", font=("Arial", 16)).pack(pady=10)

        Label(self, text="Логин").pack(pady=5)
        self.username_entry = Entry(self)
        self.username_entry.pack(pady=5)

        Label(self, text="Пароль").pack(pady=5)
        self.password_entry = Entry(self, show="*")
        self.password_entry.pack(pady=5)

        Button(self, text="Войти", command=self.login, width=20).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if verify_user(username, password):
            self.controller.show_frame("MainPage")
        else:
            messagebox.showerror("Ошибка", "Неправильный логин или пароль!")


class MainPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        Label(self, text="Главная страница", font=("Arial", 16)).pack(pady=10)
        Button(self, text="Добавить заявку", command=lambda: controller.show_frame("AddRequestPage"), width=25).pack(pady=5)
        Button(self, text="Просмотр заявок", command=lambda: controller.show_frame("ViewRequestsPage"), width=25).pack(pady=5)
        Button(self, text="Статистика", command=lambda: controller.show_frame("StatisticsPage"), width=25).pack(pady=5)
        Button(self, text="Выход", command=self.controller.quit, width=25).pack(pady=5)


class AddRequestPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        Label(self, text="Добавить заявку", font=("Arial", 16)).pack(pady=10)
        self.fields = {}
        labels = ["Оборудование", "Тип неисправности", "Описание", "Клиент", "Ответственный"]
        for label_text in labels:
            Label(self, text=label_text).pack()
            entry = Entry(self)
            entry.pack(pady=5)
            self.fields[label_text] = entry

        Button(self, text="Добавить", command=self.add_request, width=20).pack(pady=5)
        Button(self, text="Назад", command=lambda: controller.show_frame("MainPage"), width=20).pack(pady=5)

    def add_request(self):
        data = {key: entry.get() for key, entry in self.fields.items()}
        if any(not value for value in data.values()):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
            return

        conn = sqlite3.connect('repair_requests.db')
        cursor = conn.cursor()
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO requests (date_added, equipment, issue_type, description, client, status, date_completed, responsible, comments)
            VALUES (?, ?, ?, ?, ?, "Принята", NULL, ?, NULL)
        ''', (date_added, data["Оборудование"], data["Тип неисправности"], data["Описание"], data["Клиент"], data["Ответственный"]))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успех", "Заявка успешно добавлена!")
        self.controller.show_frame("MainPage")


class ViewRequestsPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        Label(self, text="Просмотр заявок", font=("Arial", 16)).pack(pady=10)
        self.listbox = Listbox(self, width=120, height=15)
        self.listbox.pack(pady=10)

        Label(self, text="Поиск по ID").pack(pady=5)
        self.search_entry = Entry(self)
        self.search_entry.pack(pady=5)
        Button(self, text="Найти", command=self.search_request, width=20).pack(pady=5)

        Button(self, text="Редактировать", command=self.edit_request, width=20).pack(pady=5)
        Button(self, text="Обновить", command=self.load_requests, width=20).pack(pady=5)
        Button(self, text="Назад", command=lambda: controller.show_frame("MainPage"), width=20).pack(pady=5)

    def load_requests(self):
        self.listbox.delete(0, 'end')
        requests = list_requests()
        for request in requests:
            self.listbox.insert('end', f"ID {request[0]} | Дата: {request[1]} | Оборудование: {request[2]} | Тип: {request[3]} | "
                                       f"Описание: {request[4]} | Клиент: {request[5]} | Статус: {request[6]} | "
                                       f"Ответственный: {request[8]}")

    def search_request(self):
        request_id = self.search_entry.get()
        if not request_id.isdigit():
            messagebox.showerror("Ошибка", "Введите корректный ID!")
            return

        request = get_request_by_id(int(request_id))
        if not request:
            messagebox.showerror("Ошибка", "Заявка не найдена!")
            return

        self.listbox.delete(0, 'end')
        self.listbox.insert('end', f"ID {request[0]} | Дата: {request[1]} | Оборудование: {request[2]} | Тип: {request[3]} | "
                                   f"Описание: {request[4]} | Клиент: {request[5]} | Статус: {request[6]} | "
                                   f"Ответственный: {request[8]}")

    def edit_request(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите заявку для редактирования!")
            return

        request_id = int(self.listbox.get(selected[0]).split()[1])
        EditRequestWindow(self, request_id)

class EditRequestWindow(Toplevel):
    def __init__(self, parent, request_id):
        super().__init__(parent)
        self.request_id = request_id
        self.title("Редактировать заявку")
        self.geometry("400x500")

        self.fields = {}
        labels = ["Оборудование", "Тип неисправности", "Описание", "Клиент", "Ответственный"]
        conn = sqlite3.connect('repair_requests.db')
        cursor = conn.cursor()
        cursor.execute("SELECT equipment, issue_type, description, client, responsible, status FROM requests WHERE id = ?", (request_id,))
        data = cursor.fetchone()
        conn.close()

        for i, label_text in enumerate(labels):
            Label(self, text=label_text).pack()
            entry = Entry(self)
            entry.insert(0, data[i])
            entry.pack(pady=5)
            self.fields[label_text] = entry

        # Поле для редактирования статуса
        Label(self, text="Статус").pack()
        self.status_var = StringVar(value=data[5])  # Статус из базы данных
        statuses = ["Принята", "В работе", "Завершена"]
        OptionMenu(self, self.status_var, *statuses).pack(pady=5)

        Button(self, text="Сохранить", command=self.save_changes, width=20).pack(pady=10)
        Button(self, text="Отмена", command=self.destroy, width=20).pack(pady=10)

    def save_changes(self):
        data = {key: entry.get() for key, entry in self.fields.items()}
        if any(not value for value in data.values()):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
            return

        # Обновление данных заявки в базе данных
        update_request(
            self.request_id,
            data["Оборудование"],
            data["Тип неисправности"],
            data["Описание"],
            data["Клиент"],
            data["Ответственный"],
            self.status_var.get()  # Новый статус
        )
        messagebox.showinfo("Успех", "Изменения сохранены!")
        self.destroy()
        
class StatisticsPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        Label(self, text="Статистика заявок", font=("Arial", 16)).pack(pady=10)
        self.stats_label = Label(self, text="", font=("Arial", 12), justify="left")
        self.stats_label.pack(pady=10)

        Button(self, text="Обновить статистику", command=self.load_statistics, width=25).pack(pady=10)
        Button(self, text="Назад", command=lambda: controller.show_frame("MainPage"), width=25).pack(pady=10)

    def load_statistics(self):
        stats = count_requests_by_status()
        stats_text = "\n".join([f"{status}: {count} заявок" for status, count in stats])
        self.stats_label.config(text=stats_text)


# --- Контроллер приложения ---
class Application(Tk):
    def __init__(self):
        super().__init__()
        self.title("Учет заявок")
        self.geometry("900x600")
        self.frames = {}

        for F in (LoginPage, MainPage, AddRequestPage, ViewRequestsPage, StatisticsPage):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


if __name__ == "__main__":
    setup_database()
    app = Application()
    app.mainloop()
