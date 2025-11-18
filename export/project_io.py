"""
Збереження та завантаження проектів (JSON)
"""
import json
from shape import Shape


class ProjectIO:
    """Клас для збереження та завантаження проектів"""
    
    @staticmethod
    def save_project(shapes, filename, groups=None, canvas_limits=None):
        """Зберегти проект у JSON файл
        
        Args:
            shapes: список фігур
            filename: назва файлу
            groups: GroupManager або None
            canvas_limits: dict з налаштуваннями меж полотна
        """
        project_data = {
            'version': '2.3',  # Оновлюємо версію для підтримки canvas_limits
            'shapes': []
        }
        
        for shape in shapes:
            shape_data = {
                'kind': shape.kind,
                'color_bgr': shape.color_bgr,
                'thickness': shape.thickness,
                'style': shape.style,
                'line_style': getattr(shape, 'line_style', 'solid'),
                'filled': getattr(shape, 'filled', False),
                'dash_length': getattr(shape, 'dash_length', 10),
                'dot_length': getattr(shape, 'dot_length', 5),
                'coords': dict(shape.coords)
            }
            
            # Додаткові параметри для тексту
            if shape.kind == 'text':
                shape_data['text'] = getattr(shape, 'text', '')
                shape_data['font_scale'] = getattr(shape, 'font_scale', 1.0)
            
            project_data['shapes'].append(shape_data)
        
        # Додаємо інформацію про групи
        if groups:
            project_data['groups'] = groups.to_dict()
        
        # Додаємо налаштування меж полотна
        if canvas_limits:
            project_data['canvas_limits'] = canvas_limits
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_project(filename):
        """Завантажити проект з JSON файлу
        
        Returns:
            tuple: (shapes, groups_data, canvas_limits) - список фігур, дані груп та налаштування полотна
        """
        with open(filename, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        shapes = []
        
        for shape_data in project_data.get('shapes', []):
            shape = Shape(
                kind=shape_data['kind'],
                color_bgr=tuple(shape_data['color_bgr']),
                thickness=shape_data['thickness'],
                style=shape_data.get('style', 'default'),
                line_style=shape_data.get('line_style', 'solid'),
                filled=shape_data.get('filled', False),
                dash_length=shape_data.get('dash_length', 10),
                dot_length=shape_data.get('dot_length', 5),
                text=shape_data.get('text', ''),
                font_scale=shape_data.get('font_scale', 1.0),
                **shape_data['coords']
            )
            shapes.append(shape)
        
        # Завантажуємо інформацію про групи (якщо є)
        groups_data = project_data.get('groups', None)
        
        # Завантажуємо налаштування меж полотна (якщо є)
        canvas_limits = project_data.get('canvas_limits', None)
        
        return shapes, groups_data, canvas_limits

