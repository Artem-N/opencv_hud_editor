"""
Менеджер для управління групами фігур
"""


class ShapeGroup:
    """Клас для представлення групи фігур"""
    
    def __init__(self, name, shape_indices=None, color=None):
        """
        Args:
            name: назва групи
            shape_indices: список індексів фігур в групі
            color: колір для відображення групи (опціонально)
        """
        self.name = name
        self.shape_indices = set(shape_indices) if shape_indices else set()
        self.color = color or (100, 150, 255)  # За замовчуванням синій
    
    def add_shape(self, idx):
        """Додати фігуру до групи"""
        self.shape_indices.add(idx)
    
    def remove_shape(self, idx):
        """Видалити фігуру з групи"""
        self.shape_indices.discard(idx)
    
    def has_shape(self, idx):
        """Чи містить група цю фігуру"""
        return idx in self.shape_indices
    
    def clear(self):
        """Очистити групу"""
        self.shape_indices.clear()
    
    def is_empty(self):
        """Чи пуста група"""
        return len(self.shape_indices) == 0


class GroupManager:
    """Менеджер для управління групами фігур"""
    
    def __init__(self):
        self.groups = []  # Список груп
    
    def create_group(self, name, shape_indices=None):
        """
        Створити нову групу
        
        Args:
            name: назва групи
            shape_indices: список індексів фігур
        
        Returns:
            ShapeGroup: створена група
        """
        # Перевіряємо чи не існує група з такою назвою
        if self.get_group_by_name(name):
            # Додаємо номер до назви
            i = 1
            base_name = name
            while self.get_group_by_name(f"{base_name}_{i}"):
                i += 1
            name = f"{base_name}_{i}"
        
        group = ShapeGroup(name, shape_indices)
        self.groups.append(group)
        return group
    
    def delete_group(self, group_name):
        """Видалити групу за назвою"""
        self.groups = [g for g in self.groups if g.name != group_name]
    
    def get_group_by_name(self, name):
        """Отримати групу за назвою"""
        for group in self.groups:
            if group.name == name:
                return group
        return None
    
    def get_groups_for_shape(self, shape_idx):
        """Отримати всі групи, які містять цю фігуру"""
        result = []
        for group in self.groups:
            if group.has_shape(shape_idx):
                result.append(group)
        return result
    
    def add_shapes_to_group(self, group_name, shape_indices):
        """Додати фігури до групи"""
        group = self.get_group_by_name(group_name)
        if group:
            for idx in shape_indices:
                group.add_shape(idx)
    
    def remove_shapes_from_group(self, group_name, shape_indices):
        """Видалити фігури з групи"""
        group = self.get_group_by_name(group_name)
        if group:
            for idx in shape_indices:
                group.remove_shape(idx)
    
    def remove_shape_from_all_groups(self, shape_idx):
        """Видалити фігуру з усіх груп"""
        for group in self.groups:
            group.remove_shape(shape_idx)
    
    def update_indices_after_deletion(self, deleted_idx):
        """
        Оновити індекси після видалення фігури
        
        Args:
            deleted_idx: індекс видаленої фігури
        """
        for group in self.groups:
            # Видаляємо видалену фігуру
            group.remove_shape(deleted_idx)
            
            # Зменшуємо індекси фігур що були після видаленої
            new_indices = set()
            for idx in group.shape_indices:
                if idx > deleted_idx:
                    new_indices.add(idx - 1)
                else:
                    new_indices.add(idx)
            group.shape_indices = new_indices
    
    def get_all_group_names(self):
        """Отримати список всіх назв груп"""
        return [g.name for g in self.groups]
    
    def get_ungrouped_shapes(self, total_shapes):
        """
        Отримати індекси фігур, які не в жодній групі
        
        Args:
            total_shapes: загальна кількість фігур
        
        Returns:
            set: індекси фігур без груп
        """
        grouped = set()
        for group in self.groups:
            grouped.update(group.shape_indices)
        
        all_shapes = set(range(total_shapes))
        return all_shapes - grouped
    
    def rename_group(self, old_name, new_name):
        """Перейменувати групу"""
        group = self.get_group_by_name(old_name)
        if group and not self.get_group_by_name(new_name):
            group.name = new_name
            return True
        return False
    
    def clear_all(self):
        """Очистити всі групи"""
        self.groups.clear()
    
    def to_dict(self):
        """Конвертувати в словник для збереження"""
        return {
            'groups': [
                {
                    'name': g.name,
                    'shape_indices': list(g.shape_indices),
                    'color': g.color
                }
                for g in self.groups
            ]
        }
    
    def from_dict(self, data):
        """Завантажити з словника"""
        self.groups.clear()
        for g_data in data.get('groups', []):
            group = ShapeGroup(
                g_data['name'],
                g_data.get('shape_indices', []),
                tuple(g_data.get('color', (100, 150, 255)))
            )
            self.groups.append(group)

