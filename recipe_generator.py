import json


class RecipeHandler:
    def __init__(self, filename):
        self.recipes = self.load_recipes(filename)
        self.replacements_graph = self.build_replacements_graph()

    def load_recipes(self, filename):
        """Загрузка рецептов из JSON-файла"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def build_replacements_graph(self):
        """Построение графа замен ингредиентов"""
        graph = {}
        for recipe in self.recipes:
            for ingredient, substitutes in recipe.get('replacements', {}).items():
                ingredient_lower = ingredient.lower()
                graph.setdefault(ingredient_lower, [])
                for sub in substitutes:
                    graph[ingredient_lower].append(sub.lower())
        return graph

    def find_possible_replacements(self, ingredient, user_ingredients):
        """Поиск возможных замен для ингредиента"""
        ingredient_lower = ingredient.lower()
        user_ingredients_lower = {ing.lower() for ing in user_ingredients}
        return [sub for sub in self.replacements_graph.get(ingredient_lower, [])
                if sub in user_ingredients_lower]

    def get_all_replacements(self, ingredient):
        """Получение всех возможных замен из графа"""
        return self.replacements_graph.get(ingredient.lower(), [])

    def calculate_match_percentage(self, recipe, user_ingredients):
        """Расчет процента совпадения с учетом всех возможных замен"""
        required = [ingredient.lower() for ingredient in recipe['ingredients']]
        user_ingredients_lower = {ing.lower() for ing in user_ingredients}

        matches = 0
        missing = []
        used_replacements = {}
        all_replacements = {}

        for ingredient in required:
            if ingredient in user_ingredients_lower:
                matches += 1
            else:
                # Все возможные замены из графа
                possible_subs = self.get_all_replacements(ingredient)
                # Доступные замены у пользователя
                available_subs = [sub for sub in possible_subs if sub in user_ingredients_lower]

                all_replacements[ingredient] = possible_subs
                if available_subs:
                    matches += 1
                    used_replacements[ingredient] = available_subs
                else:
                    missing.append(ingredient)

        total = len(required)
        percentage = (matches / total * 100) if total > 0 else 0
        return percentage, missing, used_replacements, all_replacements

    def find_matching_recipes(self, user_ingredients, complexity_filter=None):
        """Поиск рецептов с информацией о заменах"""
        # поиск с частичным совпадением и поддержкой замен
        matched = []
        for recipe in self.recipes:
            if complexity_filter and recipe['complexity'] != complexity_filter:
                continue
            percentage, missing, used_replacements, all_replacements = self.calculate_match_percentage(recipe,
                                                                                                       user_ingredients)
            if percentage > 0:
                # Формируем строку с заменами
                replacements_str = self.format_replacements(used_replacements)

                matched.append({
                    'name': recipe['name'],
                    'percentage': percentage,
                    'time': recipe['time'],
                    'complexity': recipe['complexity'],
                    'replacements_info': replacements_str,  # Новая информация
                    'missing': missing,
                    'used_replacements': used_replacements,
                    'all_replacements': all_replacements
                })
        return matched

    def format_replacements(self, replacements):
        """Форматирование замен в читаемую строку"""
        if not replacements:
            return ""
        return ", ".join([f"{orig}→{', '.join(subs)}" for orig, subs in replacements.items()])

    def quick_sort(self, arr):
        """Быстрая сортировка (Хоара) по времени (по возрастанию)"""
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]['time']
        less = [x for x in arr if x['time'] < pivot]
        equal = [x for x in arr if x['time'] == pivot]
        greater = [x for x in arr if x['time'] > pivot]
        return self.quick_sort(less) + equal + self.quick_sort(greater)

    def shell_sort(self, arr):
        """Сортировка Шелла по сложности (лёгкие → сложные)"""
        complexity_order = {'лёгкая': 1, 'средняя': 2, 'сложная': 3}
        n = len(arr)
        gap = n // 2

        while gap > 0:
            for i in range(gap, n):
                temp = arr[i]
                j = i
                while j >= gap and complexity_order[arr[j - gap]['complexity']] > complexity_order[temp['complexity']]:
                    arr[j] = arr[j - gap]
                    j -= gap
                arr[j] = temp
            gap //= 2
        return arr

    def merge_sort(self, arr):
        """Сортировка слиянием по проценту совпадения (по убыванию)"""
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = self.merge_sort(arr[:mid])
        right = self.merge_sort(arr[mid:])
        return self.merge(left, right)

    def merge(self, left, right):
        # слияние отсортированных списков
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i]['percentage'] >= right[j]['percentage']:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    def sort_recipes(self, recipes, sort_key):
        """Применение выбранного алгоритма сортировки"""
        if sort_key == 'time':
            return self.quick_sort(recipes.copy())
        elif sort_key == 'complexity':
            return self.shell_sort(recipes.copy())
        else:  # default to merge sort for match percentage
            return self.merge_sort(recipes.copy())

