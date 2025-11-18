"""
Менеджер для вибору та переміщення фігур
"""
import math
from utils.geometry import point_near_line, point_near_curve, point_near_cubic_curve


class SelectionManager:
    """Клас для управління виділенням та переміщенням фігур"""
    
    def __init__(self):
        self.selected_shapes = set()  # Індекси вибраних фігур
        
        # Для переміщення фігур
        self.dragging_shapes = False
        self.drag_start = None  # Початкова позиція курсору (world coords)
        self.original_coords = {}  # Оригінальні координати фігур перед переміщенням
        
        # Для редагування кривих
        self.editing_curve = False
        self.curve_shape_idx = None
        self.dragging_control_point = False
        self.editing_cubic_curve = False  # Для кубічних кривих
        self.cubic_curve_endpoint = None  # 'start' або 'end' - який кінець редагуємо
        self.dragging_which_control = None  # 'cx' або 'cx1'/'cx2' для кубічних
        self.show_control_points = True
    
    def clear_selection(self):
        """Очистити виділення"""
        self.selected_shapes.clear()
    
    def select_shape(self, idx):
        """Вибрати фігуру"""
        self.selected_shapes.add(idx)
    
    def deselect_shape(self, idx):
        """Скасувати виділення фігури"""
        self.selected_shapes.discard(idx)
    
    def toggle_shape(self, idx):
        """Перемкнути виділення фігури"""
        if idx in self.selected_shapes:
            self.selected_shapes.remove(idx)
        else:
            self.selected_shapes.add(idx)
    
    def is_selected(self, idx):
        """Чи вибрана фігура"""
        return idx in self.selected_shapes
    
    def find_shape_at_point(self, shapes, x, y, zoom_factor, tolerance=10):
        """Знайти фігуру під курсором"""
        tolerance = tolerance / zoom_factor
        
        # Шукаємо з кінця списку (верхні фігури)
        for idx in range(len(shapes) - 1, -1, -1):
            shape = shapes[idx]
            if self._is_point_on_shape(shape, x, y, tolerance):
                return idx
        return None
    
    def find_shapes_in_rect(self, shapes, x1, y1, x2, y2):
        """Знайти всі фігури в прямокутнику"""
        shapes_in_rect = []
        for idx, shape in enumerate(shapes):
            if self._is_shape_in_rect(shape, x1, y1, x2, y2):
                shapes_in_rect.append(idx)
        return shapes_in_rect
    
    def start_dragging(self, shapes, world_x, world_y):
        """Почати перетягування вибраних фігур"""
        if not self.selected_shapes:
            return False
        
        self.dragging_shapes = True
        self.drag_start = (world_x, world_y)
        self.original_coords = {}
        
        for idx in self.selected_shapes:
            if 0 <= idx < len(shapes):
                shape = shapes[idx]
                self.original_coords[idx] = dict(shape.coords)
        
        return True
    
    def update_dragging(self, shapes, world_x, world_y):
        """Оновити позиції фігур під час перетягування"""
        if not self.dragging_shapes or self.drag_start is None:
            return False
        
        dx = world_x - self.drag_start[0]
        dy = world_y - self.drag_start[1]
        
        for idx in self.selected_shapes:
            if idx not in self.original_coords:
                continue
            
            if idx >= len(shapes):
                continue
            
            shape = shapes[idx]
            orig = self.original_coords[idx]
            
            self._update_shape_position(shape, orig, dx, dy)
        
        return True
    
    def stop_dragging(self):
        """Закінчити перетягування"""
        self.dragging_shapes = False
        self.drag_start = None
        self.original_coords = {}
    
    def is_dragging(self):
        """Чи відбувається перетягування"""
        return self.dragging_shapes
    
    def start_curve_editing(self, idx, world_x, world_y):
        """Почати редагування кривої (перетворення лінії в криву)"""
        self.editing_curve = True
        self.curve_shape_idx = idx
        self.drag_start = (world_x, world_y)
    
    def start_cubic_curve_editing(self, idx, world_x, world_y, endpoint, shapes):
        """Почати редагування кубічної кривої (перетворення лінії в криву з 2 контрольними точками)
        
        Args:
            idx: індекс фігури
            world_x, world_y: координати кліку
            endpoint: 'start' або 'end' - який кінець лінії тягнемо
            shapes: список фігур
        """
        if idx >= len(shapes):
            return
        
        shape = shapes[idx]
        if shape.kind not in ['line', 'arrow']:
            return
        
        c = shape.coords
        
        # Зберігаємо старий kind (для стрілок)
        old_kind = shape.kind
        
        # Одразу перетворюємо лінію в кубічну криву
        # Початкові контрольні точки розміщуємо на 1/3 та 2/3 лінії
        cx1_initial = c['x1'] + (c['x2'] - c['x1']) / 3
        cy1_initial = c['y1'] + (c['y2'] - c['y1']) / 3
        cx2_initial = c['x1'] + 2 * (c['x2'] - c['x1']) / 3
        cy2_initial = c['y1'] + 2 * (c['y2'] - c['y1']) / 3
        
        # Зберігаємо всі атрибути стилю
        line_style = getattr(shape, 'line_style', 'solid')
        dash_length = getattr(shape, 'dash_length', 10)
        dot_length = getattr(shape, 'dot_length', 5)
        
        shape.kind = 'curve'
        shape.coords = {
            'x1': c['x1'],
            'y1': c['y1'],
            'x2': c['x2'],
            'y2': c['y2'],
            'cx1': cx1_initial,
            'cy1': cy1_initial,
            'cx2': cx2_initial,
            'cy2': cy2_initial
        }
        
        # Копіюємо стилі лінії
        shape.line_style = line_style
        shape.dash_length = dash_length
        shape.dot_length = dot_length
        
        # Встановлюємо режим перетягування відповідної контрольної точки
        self.dragging_control_point = True
        self.curve_shape_idx = idx
        self.cubic_curve_endpoint = endpoint
        # Визначаємо яку контрольну точку будемо тягнути
        self.dragging_which_control = 'cx1' if endpoint == 'start' else 'cx2'
        self.selected_shapes = {idx}
        self.drag_start = (world_x, world_y)
    
    def start_control_point_dragging(self, idx, which_control='cx'):
        """Почати перетягування контрольної точки кривої
        
        Args:
            idx: індекс фігури
            which_control: 'cx' для квадратичної, 'cx1' або 'cx2' для кубічної
        """
        self.dragging_control_point = True
        self.dragging_which_control = which_control
        self.curve_shape_idx = idx
        self.selected_shapes = {idx}
    
    def update_curve_editing(self, shapes, world_x, world_y):
        """Оновити редагування кривої"""
        if self.curve_shape_idx is None or self.curve_shape_idx >= len(shapes):
            return False
        
        shape = shapes[self.curve_shape_idx]
        
        # Перетворення лінії в квадратичну криву (клік по середині)
        if self.editing_curve and shape.kind in ['line', 'arrow']:
            c = shape.coords
            
            # Зберігаємо всі атрибути стилю
            line_style = getattr(shape, 'line_style', 'solid')
            dash_length = getattr(shape, 'dash_length', 10)
            dot_length = getattr(shape, 'dot_length', 5)
            
            shape.kind = 'curve'
            shape.coords = {
                'x1': c['x1'],
                'y1': c['y1'],
                'x2': c['x2'],
                'y2': c['y2'],
                'cx': world_x,
                'cy': world_y
            }
            
            # Копіюємо стилі лінії
            shape.line_style = line_style
            shape.dash_length = dash_length
            shape.dot_length = dot_length
            
            self.editing_curve = False
            self.dragging_control_point = True
            self.dragging_which_control = 'cx'
            self.selected_shapes = {self.curve_shape_idx}
            return True
        
        # Кубічна крива вже була створена в start_cubic_curve_editing, тут не потрібно робити перетворення
        
        # Оновлення контрольної точки існуючої кривої
        if self.dragging_control_point and shape.kind == 'curve':
            c = shape.coords
            # Перевіряємо чи це кубічна крива (має cx1, cy1, cx2, cy2)
            if 'cx1' in c and 'cy1' in c and 'cx2' in c and 'cy2' in c:
                # Кубічна крива - оновлюємо відповідну контрольну точку
                if self.dragging_which_control == 'cx1':
                    shape.coords['cx1'] = world_x
                    shape.coords['cy1'] = world_y
                elif self.dragging_which_control == 'cx2':
                    shape.coords['cx2'] = world_x
                    shape.coords['cy2'] = world_y
            else:
                # Квадратична крива - оновлюємо єдину контрольну точку
                shape.coords['cx'] = world_x
                shape.coords['cy'] = world_y
            return True
        
        return False
    
    def stop_curve_editing(self):
        """Закінчити редагування кривої"""
        self.editing_curve = False
        self.editing_cubic_curve = False
        self.dragging_control_point = False
        self.curve_shape_idx = None
        self.cubic_curve_endpoint = None
        self.dragging_which_control = None
    
    def is_near_control_point(self, shapes, shape_idx, x, y, zoom_factor):
        """Перевірити чи курсор близько до контрольної точки кривої
        
        Повертає True якщо близько до будь-якої контрольної точки.
        Оновлює self.dragging_which_control для визначення якої саме.
        """
        if shape_idx >= len(shapes):
            return False
        
        shape = shapes[shape_idx]
        if shape.kind != 'curve':
            return False
        
        c = shape.coords
        tolerance = 10 / zoom_factor
        
        # Перевіряємо кубічну криву (з двома контрольними точками)
        if 'cx1' in c and 'cy1' in c and 'cx2' in c and 'cy2' in c:
            dist1 = math.hypot(x - c['cx1'], y - c['cy1'])
            dist2 = math.hypot(x - c['cx2'], y - c['cy2'])
            
            if dist1 < tolerance:
                self.dragging_which_control = 'cx1'
                return True
            if dist2 < tolerance:
                self.dragging_which_control = 'cx2'
                return True
            return False
        
        # Квадратична крива (з однією контрольною точкою)
        if 'cx' in c and 'cy' in c:
            ctrl_dist = math.hypot(x - c['cx'], y - c['cy'])
            if ctrl_dist < tolerance:
                self.dragging_which_control = 'cx'
                return True
        
        return False
    
    def _is_point_on_shape(self, shape, x, y, tolerance):
        """Перевірити чи точка на фігурі"""
        if shape.kind in ['line', 'arrow']:
            c = shape.coords
            return point_near_line(x, y, c['x1'], c['y1'], c['x2'], c['y2'], tolerance)
        elif shape.kind == 'curve':
            c = shape.coords
            # Перевіряємо чи це кубічна крива
            if 'cx1' in c and 'cy1' in c and 'cx2' in c and 'cy2' in c:
                return point_near_cubic_curve(x, y, c['x1'], c['y1'], c['x2'], c['y2'], 
                                             c['cx1'], c['cy1'], c['cx2'], c['cy2'], tolerance)
            else:
                # Квадратична крива
                return point_near_curve(x, y, c['x1'], c['y1'], c['x2'], c['y2'], c['cx'], c['cy'], tolerance)
        elif shape.kind == 'circle':
            c = shape.coords
            dist = math.hypot(x - c['cx'], y - c['cy'])
            return abs(dist - c['r']) < tolerance
        elif shape.kind == 'ellipse':
            c = shape.coords
            dx = (x - c['cx']) / c['rx'] if c['rx'] > 0 else 0
            dy = (y - c['cy']) / c['ry'] if c['ry'] > 0 else 0
            dist = math.hypot(dx, dy)
            return abs(dist - 1.0) < tolerance / max(c['rx'], c['ry'])
        elif shape.kind == 'rectangle':
            c = shape.coords
            x1, y1, x2, y2 = min(c['x1'], c['x2']), min(c['y1'], c['y2']), max(c['x1'], c['x2']), max(c['y1'], c['y2'])
            # Перевіряємо близькість до країв прямокутника
            return ((abs(x - x1) < tolerance or abs(x - x2) < tolerance) and y1 <= y <= y2) or \
                   ((abs(y - y1) < tolerance or abs(y - y2) < tolerance) and x1 <= x <= x2)
        elif shape.kind == 'polygon':
            c = shape.coords
            if 'points' in c and len(c['points']) >= 3:
                points = c['points']
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]
                    if point_near_line(x, y, p1[0], p1[1], p2[0], p2[1], tolerance):
                        return True
            return False
        elif shape.kind == 'text':
            c = shape.coords
            text = getattr(shape, 'text', '')
            font_scale = getattr(shape, 'font_scale', 1.0)
            text_width = len(text) * 10 * font_scale
            text_height = 20 * font_scale
            return (c['x'] <= x <= c['x'] + text_width and
                    c['y'] - text_height <= y <= c['y'])
        elif shape.kind == 'point':
            c = shape.coords
            dist = math.hypot(x - c['x'], y - c['y'])
            return dist < tolerance
        
        return False
    
    def _is_shape_in_rect(self, shape, x1, y1, x2, y2):
        """Перевірити чи фігура в прямокутнику"""
        if shape.kind in ['line', 'arrow', 'curve']:
            c = shape.coords
            return (x1 <= c['x1'] <= x2 and y1 <= c['y1'] <= y2 and
                    x1 <= c['x2'] <= x2 and y1 <= c['y2'] <= y2)
        elif shape.kind in ['circle', 'ellipse']:
            c = shape.coords
            return x1 <= c['cx'] <= x2 and y1 <= c['cy'] <= y2
        elif shape.kind == 'rectangle':
            c = shape.coords
            cx = (c['x1'] + c['x2']) / 2
            cy = (c['y1'] + c['y2']) / 2
            return x1 <= cx <= x2 and y1 <= cy <= y2
        elif shape.kind == 'polygon':
            c = shape.coords
            if 'points' in c and len(c['points']) > 0:
                return all(x1 <= px <= x2 and y1 <= py <= y2 for px, py in c['points'])
        elif shape.kind in ['text', 'point']:
            c = shape.coords
            return x1 <= c['x'] <= x2 and y1 <= c['y'] <= y2
        
        return False
    
    def _update_shape_position(self, shape, orig_coords, dx, dy):
        """Оновити позицію фігури"""
        if shape.kind in ['line', 'arrow']:
            shape.coords['x1'] = orig_coords['x1'] + dx
            shape.coords['y1'] = orig_coords['y1'] + dy
            shape.coords['x2'] = orig_coords['x2'] + dx
            shape.coords['y2'] = orig_coords['y2'] + dy
        elif shape.kind == 'curve':
            shape.coords['x1'] = orig_coords['x1'] + dx
            shape.coords['y1'] = orig_coords['y1'] + dy
            shape.coords['x2'] = orig_coords['x2'] + dx
            shape.coords['y2'] = orig_coords['y2'] + dy
            # Підтримка квадратичних та кубічних кривих
            if 'cx' in orig_coords and 'cy' in orig_coords:
                shape.coords['cx'] = orig_coords['cx'] + dx
                shape.coords['cy'] = orig_coords['cy'] + dy
            if 'cx1' in orig_coords and 'cy1' in orig_coords:
                shape.coords['cx1'] = orig_coords['cx1'] + dx
                shape.coords['cy1'] = orig_coords['cy1'] + dy
            if 'cx2' in orig_coords and 'cy2' in orig_coords:
                shape.coords['cx2'] = orig_coords['cx2'] + dx
                shape.coords['cy2'] = orig_coords['cy2'] + dy
        elif shape.kind in ['circle', 'ellipse']:
            shape.coords['cx'] = orig_coords['cx'] + dx
            shape.coords['cy'] = orig_coords['cy'] + dy
        elif shape.kind in ['text', 'point']:
            shape.coords['x'] = orig_coords['x'] + dx
            shape.coords['y'] = orig_coords['y'] + dy
        elif shape.kind == 'rectangle':
            shape.coords['x1'] = orig_coords['x1'] + dx
            shape.coords['y1'] = orig_coords['y1'] + dy
            shape.coords['x2'] = orig_coords['x2'] + dx
            shape.coords['y2'] = orig_coords['y2'] + dy
        elif shape.kind == 'polygon':
            if 'points' in orig_coords:
                shape.coords['points'] = [(x + dx, y + dy) for x, y in orig_coords['points']]

