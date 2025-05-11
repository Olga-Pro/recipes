import tkinter as tk
from tkinter import ttk, filedialog
from recipe_generator import RecipeHandler


class RecipeApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Генератор рецептов")
        self.master.geometry("800x600")  # Увеличиваем размер окна
        self.handler = RecipeHandler('recipes.json')
        self.matched_recipes = []

        # Настройка веса столбцов для растягивания
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(3, weight=1)

        self.create_widgets()
        self.create_sorting_controls()

    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Ввод ингредиентов
        ttk.Label(self.master, text="Ингредиенты (через запятую):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.ingredients_entry = ttk.Entry(self.master, width=60)
        self.ingredients_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2, sticky='ew')

        # Кнопки
        ttk.Button(self.master, text="Загрузить из файла", command=self.load_file).grid(row=0, column=3, padx=5, pady=5,
                                                                                        sticky='e')
        ttk.Button(self.master, text="Поиск рецептов", command=self.search_recipes).grid(row=2, column=3, padx=5,
                                                                                         pady=5, sticky='e')

        # Фильтр сложности
        ttk.Label(self.master, text="Сложность:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.complexity = ttk.Combobox(self.master, values=["Любая", "лёгкая", "средняя", "сложная"], width=15)
        self.complexity.current(0)
        self.complexity.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Таблица результатов
        self.tree = ttk.Treeview(self.master,
                                 columns=('name', 'match', 'time', 'complexity', 'replacements'),
                                 show='headings')

        # Настройка колонок
        self.tree.heading('name', text='Название')
        self.tree.heading('match', text='Совпадение (%)')
        self.tree.heading('time', text='Время')
        self.tree.heading('complexity', text='Сложность')
        self.tree.heading('replacements', text='Использованные замены')

        self.tree.column('name', width=180)
        self.tree.column('match', width=90, anchor='center')
        self.tree.column('time', width=70, anchor='center')
        self.tree.column('complexity', width=90, anchor='center')
        self.tree.column('replacements', width=200)
        self.tree.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky='nsew')

        # Детали рецепта
        self.details = tk.Text(self.master, height=15, width=60, state='disabled')
        self.details.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky='ew')
        self.tree.bind('<<TreeviewSelect>>', self.show_details)

    def create_sorting_controls(self):
        """Элементы управления сортировкой"""
        ttk.Label(self.master, text="Сортировать по:").grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.sort_key = ttk.Combobox(self.master, values=["Совпадение", "Время", "Сложность"], width=15)
        self.sort_key.current(0)
        self.sort_key.grid(row=1, column=3, padx=5, pady=5, sticky='w')

    def load_file(self):
        """Загрузка ингредиентов из файла"""
        filepath = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                ingredients = [line.strip() for line in f if line.strip()]
                self.ingredients_entry.delete(0, tk.END)
                self.ingredients_entry.insert(0, ', '.join(ingredients))

    def search_recipes(self):
        """Поиск и сортировка рецептов"""
        # Получаем введенные данные
        ingredients = [x.strip() for x in self.ingredients_entry.get().split(',') if x.strip()]
        complexity_filter = self.complexity.get()
        complexity_filter = None if complexity_filter == "Любая" else complexity_filter

        # Выполняем поиск
        matched = self.handler.find_matching_recipes(ingredients, complexity_filter)

        # Сортируем результаты
        sort_option = self.sort_key.get()
        sort_mapping = {
            "Совпадение": "percentage",
            "Время": "time",
            "Сложность": "complexity"
        }
        self.matched_recipes = self.handler.sort_recipes(matched, sort_mapping[sort_option])

        # Обновляем таблицу
        self.update_results_view()

    def update_results_view(self):
        """Обновление таблицы с новой колонкой"""
        self.tree.delete(*self.tree.get_children())
        for recipe in self.matched_recipes:
            self.tree.insert('', 'end', values=(
                recipe['name'],
                f"{recipe['percentage']:.1f}%",
                recipe['time'],
                recipe['complexity'],
                recipe['replacements_info']  # Новая колонка
            ))

    def show_details(self, event):
        """Отображение деталей с разделением на доступные и возможные замены"""
        self.details.config(state='normal')
        self.details.delete(1.0, tk.END)

        selected = self.tree.selection()
        if not selected:
            return

        recipe_name = self.tree.item(selected[0])['values'][0]
        recipe = next((r for r in self.matched_recipes if r['name'] == recipe_name), None)
        if not recipe:
            return

        info = [
            f"Рецепт: {recipe['name']}",
            f"Совпадение: {recipe['percentage']:.1f}%",
            f"Время: {recipe['time']} мин",
            f"Сложность: {recipe['complexity']}"
        ]

        if recipe['missing']:
            info.append("\nНедостающие ингредиенты:")
            for ing in recipe['missing']:
                line = f"• {ing}"
                if ing in recipe['all_replacements']:
                    subs = recipe['all_replacements'][ing]
                    used_subs = recipe['used_replacements'].get(ing, [])
                    if subs:
                        available = [s for s in subs if s in used_subs]
                        other = [s for s in subs if s not in used_subs]
                        parts = []
                        if available:
                            parts.append(f"Доступные замены: {', '.join(available)}")
                        if other:
                            parts.append(f"Другие варианты: {', '.join(other)}")
                        line += " - " + "; ".join(parts)
                    else:
                        line += " - замены не найдены"
                info.append(line)
        else:
            info.append("\nВсе ингредиенты в наличии!")

        self.details.insert(tk.END, '\n'.join(info))
        self.details.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = RecipeApp(root)
    root.mainloop()