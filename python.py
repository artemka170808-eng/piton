import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# Константы
FAVORITES_FILE = "favorites.json"
GITHUB_API_URL = "https://api.github.com/search/users"


class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # Загрузка избранного
        self.favorites = self.load_favorites()

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Рамка поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Поиск пользователя:").pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_users())

        self.search_button = ttk.Button(search_frame, text="Найти", command=self.search_users)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Рамка результатов поиска
        result_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Таблица (Treeview) для результатов
        columns = ("login", "avatar")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=8)
        self.tree.heading("login", text="Логин")
        self.tree.heading("avatar", text="URL аватара")
        self.tree.column("login", width=200)
        self.tree.column("avatar", width=350)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки действий с результатом
        action_frame = ttk.Frame(self.root, padding="5")
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.add_fav_button = ttk.Button(action_frame, text="Добавить в избранное",
                                         command=self.add_to_favorites, state=tk.DISABLED)
        self.add_fav_button.pack(side=tk.LEFT, padx=5)

        self.show_fav_button = ttk.Button(action_frame, text="Показать избранное",
                                          command=self.show_favorites)
        self.show_fav_button.pack(side=tk.LEFT, padx=5)

        # Статусная строка
        self.status_var = tk.StringVar(value="Готов")
        status_label = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Обработка выбора в таблице
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def load_favorites(self):
        """Загружает избранных пользователей из JSON-файла."""
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_favorites(self):
        """Сохраняет избранных пользователей в JSON-файл."""
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, indent=4, ensure_ascii=False)

    def search_users(self):
        """Выполняет поиск пользователей GitHub по введённому запросу."""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Пустой запрос", "Поле поиска не должно быть пустым.")
            return

        self.status_var.set("Поиск...")
        self.root.update()

        try:
            response = requests.get(GITHUB_API_URL, params={"q": query, "per_page": 30})
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])

            # Очистка таблицы
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Заполнение таблицы
            for user in items:
                self.tree.insert("", tk.END, values=(user["login"], user["avatar_url"]))

            count = len(items)
            self.status_var.set(f"Найдено пользователей: {count}")
            self.add_fav_button.config(state=tk.DISABLED)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Не удалось выполнить запрос:\n{e}")
            self.status_var.set("Ошибка запроса")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка:\n{e}")
            self.status_var.set("Ошибка")

    def on_tree_select(self, event):
        """Активирует кнопку добавления в избранное при выборе строки."""
        selected = self.tree.selection()
        self.add_fav_button.config(state=tk.NORMAL if selected else tk.DISABLED)

    def add_to_favorites(self):
        """Добавляет выбранного пользователя в избранное."""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        login = item["values"][0]
        avatar_url = item["values"][1]

        # Проверка на дубликат
        if any(fav["login"] == login for fav in self.favorites):
            messagebox.showinfo("Уже в избранном", f"Пользователь '{login}' уже в избранном.")
            return

        self.favorites.append({"login": login, "avatar_url": avatar_url})
        self.save_favorites()
        messagebox.showinfo("Добавлено", f"Пользователь '{login}' добавлен в избранное.")
        self.status_var.set(f"'{login}' добавлен в избранное")

    def show_favorites(self):
        """Отображает окно со списком избранных пользователей."""
        fav_window = tk.Toplevel(self.root)
        fav_window.title("Избранные пользователи")
        fav_window.geometry("500x300")
        fav_window.resizable(True, True)

        frame = ttk.Frame(fav_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Список избранных пользователей", font=("Arial", 12)).pack(pady=5)

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Courier", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for fav in self.favorites:
            listbox.insert(tk.END, f"{fav['login']} - {fav['avatar_url']}")

        if not self.favorites:
            listbox.insert(tk.END, "Нет избранных пользователей.")

        # Кнопка удаления
        def delete_selected():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(self.favorites):
                    removed = self.favorites.pop(index)
                    self.save_favorites()
                    listbox.delete(index)
                    self.status_var.set(f"'{removed['login']}' удалён из избранного")
                    messagebox.showinfo("Удалено", f"Пользователь '{removed['login']}' удалён.")

        btn_delete = ttk.Button(frame, text="Удалить выбранного", command=delete_selected)
        btn_delete.pack(pady=5)


def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()


if __name__ == "__main__":
    main()