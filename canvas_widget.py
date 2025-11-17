"""
Віджет для малювання фігур
"""
import math
import json
from PyQt5 import QtWidgets, QtGui, QtCore

from shape import Shape
from constants import COLOR_MAP


class CanvasWidget(QtWidgets.QWidget):
    mode_changed = QtCore.pyqtSignal(str)
    mouse_moved = QtCore.pyqtSignal(int, int)
    shape_info_changed = QtCore.pyqtSignal(str)
    zoom_changed = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        # Не перехоплюємо фокус клавіатури - дозволяємо MainWindow обробляти
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.shapes = []
        self.current_mode = 'pan'  # За замовчуванням режим панування (переміщення полотна)
        self.temp_point = None
        self.mouse_pos = None
        
        # поточні налаштування малювання
        self.current_color_bgr = (0, 255, 0)
        self.current_thickness = 2
        self.current_style = 'default'
        self.current_font_scale = 1.0  # розмір шрифту для тексту
        self.current_line_style = 'solid'  # стиль лінії (solid, dashed, dotted)
        self.current_filled = False  # чи заповнена фігура
        
        # для малювання полігонів
        self.polygon_points = []  # точки поточного полігону
        
        # вибрані фігури та буфер обміну
        self.selected_shapes = set()  # індекси вибраних фігур
        self.clipboard = []  # буфер обміну для копіювання/вставки
        self.selection_rect = None  # рамка виділення (для вибору області)
        
        # переміщення фігур
        self.dragging_shapes = False  # чи відбувається перетягування
        self.drag_start = None  # початкова позиція курсору при перетягуванні
        self.original_coords = {}  # оригінальні координати фігур
        
        # редагування кривих
        self.editing_curve = False  # чи редагуємо криву
        self.curve_shape_idx = None  # індекс фігури що редагується
        self.dragging_control_point = False  # чи тягнемо контрольну точку
        self.show_control_points = True  # показувати контрольні точки
        
        # малювання фігур (drag to draw)
        self.drawing_shape = False  # чи малюємо фігуру зараз
        
        # налаштування сітки
        self.grid_step = 20
        self.grid_bold_step = 5
        self.snap_to_grid = False
        
        # налаштування зуму та панування
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.1
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_start = None

    # --- режим малювання ---

    def set_mode_pan(self):
        self.current_mode = 'pan'
        self.temp_point = None
        self.selection_rect = None
        self.dragging_shapes = False
        self.drawing_shape = False
        self.drag_start = None
        self.original_coords = {}
        self.shape_info_changed.emit("")
        self.mode_changed.emit('pan')
        self.update()

    def set_mode_select(self):
        self.current_mode = 'select'
        self.temp_point = None
        self.selection_rect = None
        self.dragging_shapes = False
        self.drawing_shape = False
        self.drag_start = None
        self.original_coords = {}
        self.shape_info_changed.emit("")
        self.mode_changed.emit('select')
        self.update()

    def set_mode_line(self):
        self.current_mode = 'line'
        self.temp_point = None
        self.drawing_shape = False
        self.shape_info_changed.emit("")
        self.mode_changed.emit('line')
        self.update()

    def set_mode_circle(self):
        self.current_mode = 'circle'
        self.temp_point = None
        self.drawing_shape = False
        self.shape_info_changed.emit("")
        self.mode_changed.emit('circle')
        self.update()

    def set_mode_text(self):
        self.current_mode = 'text'
        self.temp_point = None
        self.drawing_shape = False
        self.polygon_points = []
        self.shape_info_changed.emit("")
        self.mode_changed.emit('text')
        self.update()
    
    def set_mode_point(self):
        self.current_mode = 'point'
        self.temp_point = None
        self.drawing_shape = False
        self.polygon_points = []
        self.shape_info_changed.emit("")
        self.mode_changed.emit('point')
        self.update()
    
    def set_mode_rectangle(self):
        self.current_mode = 'rectangle'
        self.temp_point = None
        self.drawing_shape = False
        self.polygon_points = []
        self.shape_info_changed.emit("")
        self.mode_changed.emit('rectangle')
        self.update()
    
    def set_mode_arrow(self):
        self.current_mode = 'arrow'
        self.temp_point = None
        self.drawing_shape = False
        self.polygon_points = []
        self.shape_info_changed.emit("")
        self.mode_changed.emit('arrow')
        self.update()
    
    def set_mode_polygon(self):
        self.current_mode = 'polygon'
        self.temp_point = None
        self.drawing_shape = False
        self.polygon_points = []
        self.shape_info_changed.emit("")
        self.mode_changed.emit('polygon')
        self.update()
    
    def set_mode_ellipse(self):
        self.current_mode = 'ellipse'
        self.temp_point = None
        self.drawing_shape = False
        self.polygon_points = []
        self.shape_info_changed.emit("")
        self.mode_changed.emit('ellipse')
        self.update()

    # --- мишка ---

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # Передаємо фокус назад на MainWindow для обробки клавіатури
        if self.parent():
            self.parent().setFocus()
        
        screen_x, screen_y = event.x(), event.y()
        world_x, world_y = self._screen_to_world(screen_x, screen_y)
        
        if event.button() == QtCore.Qt.LeftButton:
            # У режимі pan - рухаємо полотно
            if self.current_mode == 'pan':
                self.pan_start = (screen_x, screen_y)
            elif self.current_mode == 'text':
                # Текст - просто клік без drag
                x, y = world_x, world_y
                if self.snap_to_grid:
                    x, y = self._snap_to_grid(x, y)
                self._handle_text_click(x, y)
            elif self.current_mode == 'point':
                # Крапка - просто клік без drag
                x, y = world_x, world_y
                if self.snap_to_grid:
                    x, y = self._snap_to_grid(x, y)
                self._handle_point_click(x, y)
            elif self.current_mode == 'polygon':
                # Полігон - додаємо точку при кожному кліку
                x, y = world_x, world_y
                if self.snap_to_grid:
                    x, y = self._snap_to_grid(x, y)
                self._handle_polygon_click(x, y)
            else:
                x, y = world_x, world_y
                
                if self.snap_to_grid and self.current_mode != 'select':
                    x, y = self._snap_to_grid(x, y)
                
                # Починаємо малювання/вибір
                self.temp_point = (x, y)
                
                if self.current_mode == 'select':
                    clicked_shape_idx = self._find_shape_at_point(x, y)
                    if clicked_shape_idx is not None:
                        shape = self.shapes[clicked_shape_idx]
                        
                        # Спеціальна логіка для ліній/стрілок - перевірка чи клікнули на середину
                        if shape.kind in ['line', 'arrow']:
                            c = shape.coords
                            is_middle, t = self._is_point_near_line_middle(
                                x, y, c['x1'], c['y1'], c['x2'], c['y2'], 
                                15 / self.zoom_factor
                            )
                            if is_middle:
                                # Перетворюємо лінію в криву
                                self.editing_curve = True
                                self.curve_shape_idx = clicked_shape_idx
                                self.drag_start = (x, y)
                                self.temp_point = None
                                self.update()
                                return
                        
                        # Перевірка чи клікнули на контрольну точку кривої
                        if shape.kind == 'curve':
                            c = shape.coords
                            ctrl_dist = math.hypot(x - c['cx'], y - c['cy'])
                            if ctrl_dist < 10 / self.zoom_factor:
                                # Клікнули на контрольну точку
                                self.dragging_control_point = True
                                self.curve_shape_idx = clicked_shape_idx
                                self.selected_shapes = {clicked_shape_idx}
                                self.temp_point = None
                                self.update()
                                return
                        
                        # Клікнули на фігуру
                        modifiers = QtWidgets.QApplication.keyboardModifiers()
                        ctrl_pressed = modifiers & QtCore.Qt.ControlModifier
                        
                        # Змінюємо виділення тільки якщо Ctrl натиснуто або клікнули на невибрану фігуру
                        if ctrl_pressed:
                            if clicked_shape_idx in self.selected_shapes:
                                self.selected_shapes.remove(clicked_shape_idx)
                            else:
                                self.selected_shapes.add(clicked_shape_idx)
                        else:
                            if clicked_shape_idx not in self.selected_shapes:
                                self.selected_shapes = {clicked_shape_idx}
                        
                        # Готуємося до переміщення тільки якщо є вибрані фігури
                        if self.selected_shapes and clicked_shape_idx in self.selected_shapes:
                            self.dragging_shapes = True
                            self.drag_start = (x, y)
                            self.original_coords = {}
                            for idx in self.selected_shapes:
                                shape = self.shapes[idx]
                                self.original_coords[idx] = dict(shape.coords)
                        
                        self.update()
                        # Не встановлюємо temp_point, щоб не почати рамку виділення
                        self.temp_point = None
                    # else: починаємо рамку виділення (temp_point вже встановлено)
                elif self.current_mode in ['line', 'circle', 'rectangle', 'arrow', 'ellipse']:
                    # Починаємо малювання фігури
                    self.drawing_shape = True
        elif event.button() == QtCore.Qt.RightButton:
            # Для полігонів - завершуємо малювання
            if self.current_mode == 'polygon' and len(self.polygon_points) >= 3:
                self._finish_polygon()
            # Скасування всіх дій або повернення до режиму pan
            elif self.current_mode != 'pan':
                self.set_mode_pan()
            else:
                self.temp_point = None
                self.selection_rect = None
                self.dragging_shapes = False
                self.drawing_shape = False
                self.drag_start = None
                self.original_coords = {}
                self.shape_info_changed.emit("")
                self.update()
        elif event.button() == QtCore.Qt.MidButton:
            self.pan_start = (screen_x, screen_y)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        screen_x, screen_y = event.x(), event.y()
        
        if self.pan_start is not None:
            dx = screen_x - self.pan_start[0]
            dy = screen_y - self.pan_start[1]
            self.pan_x += dx
            self.pan_y += dy
            self.pan_start = (screen_x, screen_y)
            self.update()
            return
        
        world_x, world_y = self._screen_to_world(screen_x, screen_y)
        
        # Редагування кривої (перетворення лінії в криву)
        if self.editing_curve and self.curve_shape_idx is not None:
            shape = self.shapes[self.curve_shape_idx]
            if shape.kind in ['line', 'arrow']:
                # Перетворюємо лінію в криву
                c = shape.coords
                shape.kind = 'curve'
                shape.coords = {
                    'x1': c['x1'],
                    'y1': c['y1'],
                    'x2': c['x2'],
                    'y2': c['y2'],
                    'cx': world_x,
                    'cy': world_y
                }
                self.editing_curve = False
                self.dragging_control_point = True
                # Додаємо фігуру до вибраних
                self.selected_shapes = {self.curve_shape_idx}
            self.mouse_pos = (world_x, world_y)
            self.mouse_moved.emit(int(world_x), int(world_y))
            self.update()
            return
        
        # Переміщення контрольної точки кривої
        if self.dragging_control_point and self.curve_shape_idx is not None:
            shape = self.shapes[self.curve_shape_idx]
            if shape.kind == 'curve':
                shape.coords['cx'] = world_x
                shape.coords['cy'] = world_y
            self.mouse_pos = (world_x, world_y)
            self.mouse_moved.emit(int(world_x), int(world_y))
            self.update()
            return
        
        # Перетягування вибраних фігур
        if self.dragging_shapes and self.drag_start is not None:
            dx = world_x - self.drag_start[0]
            dy = world_y - self.drag_start[1]
            
            # Оновлюємо позиції всіх вибраних фігур
            for idx in self.selected_shapes:
                if idx not in self.original_coords:
                    continue
                
                shape = self.shapes[idx]
                orig = self.original_coords[idx]
                
                if shape.kind in ['line', 'arrow']:
                    shape.coords['x1'] = orig['x1'] + dx
                    shape.coords['y1'] = orig['y1'] + dy
                    shape.coords['x2'] = orig['x2'] + dx
                    shape.coords['y2'] = orig['y2'] + dy
                elif shape.kind == 'curve':
                    shape.coords['x1'] = orig['x1'] + dx
                    shape.coords['y1'] = orig['y1'] + dy
                    shape.coords['x2'] = orig['x2'] + dx
                    shape.coords['y2'] = orig['y2'] + dy
                    shape.coords['cx'] = orig['cx'] + dx
                    shape.coords['cy'] = orig['cy'] + dy
                elif shape.kind in ['circle', 'ellipse']:
                    shape.coords['cx'] = orig['cx'] + dx
                    shape.coords['cy'] = orig['cy'] + dy
                elif shape.kind in ['text', 'point']:
                    shape.coords['x'] = orig['x'] + dx
                    shape.coords['y'] = orig['y'] + dy
                elif shape.kind == 'rectangle':
                    shape.coords['x1'] = orig['x1'] + dx
                    shape.coords['y1'] = orig['y1'] + dy
                    shape.coords['x2'] = orig['x2'] + dx
                    shape.coords['y2'] = orig['y2'] + dy
                elif shape.kind == 'polygon':
                    if 'points' in orig:
                        shape.coords['points'] = [(x + dx, y + dy) for x, y in orig['points']]
            
            self.mouse_pos = (world_x, world_y)
            self.mouse_moved.emit(int(world_x), int(world_y))
            self.update()
            return
        
        if self.snap_to_grid and self.current_mode != 'select':
            world_x, world_y = self._snap_to_grid(world_x, world_y)
        
        if self.temp_point is not None:
            if self.current_mode == 'line':
                modifiers = QtWidgets.QApplication.keyboardModifiers()
                if modifiers & QtCore.Qt.ShiftModifier:
                    world_x, world_y = self._constrain_line(world_x, world_y)
            elif self.current_mode == 'select' and self.selection_rect is not None:
                # Оновлюємо рамку виділення
                pass
        
        self.mouse_pos = (world_x, world_y)
        self.mouse_moved.emit(int(world_x), int(world_y))
        
        if self.temp_point is not None:
            info = self._get_shape_info(world_x, world_y)
            self.shape_info_changed.emit(info)
        else:
            self.shape_info_changed.emit("")
        
        self.update()
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MidButton:
            self.pan_start = None
        elif event.button() == QtCore.Qt.LeftButton:
            # Завершуємо панування
            if self.pan_start is not None:
                self.pan_start = None
            
            # Завершуємо редагування кривої
            if self.editing_curve or self.dragging_control_point:
                self.editing_curve = False
                self.dragging_control_point = False
                self.curve_shape_idx = None
                self.update()
            
            # Завершуємо перетягування фігур
            if self.dragging_shapes:
                self.dragging_shapes = False
                self.drag_start = None
                self.original_coords = {}
            
            # Завершуємо малювання фігури
            if self.drawing_shape and self.temp_point is not None:
                screen_x, screen_y = event.x(), event.y()
                world_x, world_y = self._screen_to_world(screen_x, screen_y)
                
                if self.snap_to_grid:
                    world_x, world_y = self._snap_to_grid(world_x, world_y)
                
                x0, y0 = self.temp_point
                x1, y1 = world_x, world_y
                
                # Перевіряємо чи є мінімальна довжина (щоб не було точкових фігур)
                if abs(x1 - x0) > 2 or abs(y1 - y0) > 2:
                    if self.current_mode == 'line':
                        self.shapes.append(
                            Shape(
                                'line',
                                color_bgr=self.current_color_bgr,
                                thickness=self.current_thickness,
                                style=self.current_style,
                                line_style=self.current_line_style,
                                x1=int(x0), y1=int(y0),
                                x2=int(x1), y2=int(y1),
                            )
                        )
                    elif self.current_mode == 'circle':
                        dx = x1 - x0
                        dy = y1 - y0
                        r = int(round(math.hypot(dx, dy)))
                        if r > 2:  # Мінімальний радіус
                            self.shapes.append(
                                Shape(
                                    'circle',
                                    color_bgr=self.current_color_bgr,
                                    thickness=self.current_thickness,
                                    style=self.current_style,
                                    line_style=self.current_line_style,
                                    filled=self.current_filled,
                                    cx=int(x0), cy=int(y0), r=r,
                                )
                            )
                    elif self.current_mode == 'rectangle':
                        self.shapes.append(
                            Shape(
                                'rectangle',
                                color_bgr=self.current_color_bgr,
                                thickness=self.current_thickness,
                                style=self.current_style,
                                line_style=self.current_line_style,
                                filled=self.current_filled,
                                x1=int(x0), y1=int(y0),
                                x2=int(x1), y2=int(y1),
                            )
                        )
                    elif self.current_mode == 'arrow':
                        self.shapes.append(
                            Shape(
                                'arrow',
                                color_bgr=self.current_color_bgr,
                                thickness=self.current_thickness,
                                style=self.current_style,
                                line_style=self.current_line_style,
                                x1=int(x0), y1=int(y0),
                                x2=int(x1), y2=int(y1),
                            )
                        )
                    elif self.current_mode == 'ellipse':
                        rx = int(abs(x1 - x0))
                        ry = int(abs(y1 - y0))
                        if rx > 2 and ry > 2:  # Мінімальний розмір
                            self.shapes.append(
                                Shape(
                                    'ellipse',
                                    color_bgr=self.current_color_bgr,
                                    thickness=self.current_thickness,
                                    style=self.current_style,
                                    line_style=self.current_line_style,
                                    filled=self.current_filled,
                                    cx=int(x0), cy=int(y0), rx=rx, ry=ry, angle=0,
                                )
                            )
                
                self.drawing_shape = False
                self.temp_point = None
                self.shape_info_changed.emit("")
                self.update()
            
            # Завершуємо вибір рамкою (select mode)
            elif self.current_mode == 'select' and self.temp_point is not None:
                screen_x, screen_y = event.x(), event.y()
                world_x, world_y = self._screen_to_world(screen_x, screen_y)
                x1, y1 = self.temp_point
                x2, y2 = world_x, world_y
                
                # Перевіряємо чи це була рамка (мінімальний рух)
                if abs(x2 - x1) > 3 or abs(y2 - y1) > 3:
                    # Знаходимо всі фігури в рамці
                    shapes_in_rect = self._find_shapes_in_rect(
                        min(x1, x2), min(y1, y2),
                        max(x1, x2), max(y1, y2)
                    )
                    
                    modifiers = QtWidgets.QApplication.keyboardModifiers()
                    ctrl_pressed = modifiers & QtCore.Qt.ControlModifier
                    
                    if ctrl_pressed:
                        self.selected_shapes.update(shapes_in_rect)
                    else:
                        self.selected_shapes = set(shapes_in_rect)
                else:
                    # Це був просто клік на пусте місце - скидаємо виділення
                    modifiers = QtWidgets.QApplication.keyboardModifiers()
                    ctrl_pressed = modifiers & QtCore.Qt.ControlModifier
                    if not ctrl_pressed:
                        self.selected_shapes.clear()
                
                self.temp_point = None
                self.update()
    
    def wheelEvent(self, event: QtGui.QWheelEvent):
        screen_x = event.x()
        screen_y = event.y()
        world_x, world_y = self._screen_to_world(screen_x, screen_y)
        
        delta = event.angleDelta().y()
        if delta > 0:
            new_zoom = min(self.zoom_factor + self.zoom_step, self.max_zoom)
        else:
            new_zoom = max(self.zoom_factor - self.zoom_step, self.min_zoom)
        
        if new_zoom != self.zoom_factor:
            zoom_ratio = new_zoom / self.zoom_factor
            self.pan_x = world_x - (world_x - self.pan_x) * zoom_ratio
            self.pan_y = world_y - (world_y - self.pan_y) * zoom_ratio
            
            self.zoom_factor = new_zoom
            self.zoom_changed.emit(self.zoom_factor)
            self.update()


    def _handle_text_click(self, x, y):
        """Обробка кліку для додавання тексту"""
        # Викликаємо сигнал для отримання тексту від MainWindow
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
        
        if ok and text:
            self.shapes.append(
                Shape(
                    'text',
                    color_bgr=self.current_color_bgr,
                    thickness=self.current_thickness,
                    style=self.current_style,
                    text=text,
                    font_scale=self.current_font_scale,
                    x=int(x), y=int(y),
                )
            )
        self.update()
    
    def _handle_point_click(self, x, y):
        """Обробка кліку для додавання крапки"""
        self.shapes.append(
            Shape(
                'point',
                color_bgr=self.current_color_bgr,
                thickness=self.current_thickness,
                style=self.current_style,
                x=int(x), y=int(y),
            )
        )
        self.update()
    
    def _handle_polygon_click(self, x, y):
        """Обробка кліку для додавання точки до полігону"""
        self.polygon_points.append((int(x), int(y)))
        self.update()
    
    def _finish_polygon(self):
        """Завершити малювання полігону"""
        if len(self.polygon_points) >= 3:
            self.shapes.append(
                Shape(
                    'polygon',
                    color_bgr=self.current_color_bgr,
                    thickness=self.current_thickness,
                    style=self.current_style,
                    line_style=self.current_line_style,
                    filled=self.current_filled,
                    points=list(self.polygon_points),
                )
            )
            self.polygon_points = []
            self.update()


    # --- вибір фігур ---
    
    def _find_shape_at_point(self, x, y, tolerance=10):
        """Знайти фігуру під курсором"""
        # Шукаємо з кінця списку (верхні фігури)
        for idx in range(len(self.shapes) - 1, -1, -1):
            shape = self.shapes[idx]
            if shape.kind in ['line', 'arrow']:
                c = shape.coords
                if self._point_near_line(x, y, c['x1'], c['y1'], c['x2'], c['y2'], tolerance / self.zoom_factor):
                    return idx
            elif shape.kind == 'curve':
                c = shape.coords
                # Перевіряємо близькість до кривої Безьє
                if self._point_near_curve(x, y, c['x1'], c['y1'], c['x2'], c['y2'], c['cx'], c['cy'], tolerance / self.zoom_factor):
                    return idx
            elif shape.kind == 'circle':
                c = shape.coords
                dist = math.hypot(x - c['cx'], y - c['cy'])
                if abs(dist - c['r']) < tolerance / self.zoom_factor:
                    return idx
            elif shape.kind == 'ellipse':
                c = shape.coords
                # Приблизна перевірка для еліпса
                dx = (x - c['cx']) / c['rx'] if c['rx'] > 0 else 0
                dy = (y - c['cy']) / c['ry'] if c['ry'] > 0 else 0
                dist = math.hypot(dx, dy)
                if abs(dist - 1.0) < tolerance / self.zoom_factor / max(c['rx'], c['ry']):
                    return idx
            elif shape.kind == 'rectangle':
                c = shape.coords
                x1, y1, x2, y2 = min(c['x1'], c['x2']), min(c['y1'], c['y2']), max(c['x1'], c['x2']), max(c['y1'], c['y2'])
                tol = tolerance / self.zoom_factor
                # Перевіряємо близькість до країв прямокутника
                if ((abs(x - x1) < tol or abs(x - x2) < tol) and y1 <= y <= y2) or \
                   ((abs(y - y1) < tol or abs(y - y2) < tol) and x1 <= x <= x2):
                    return idx
            elif shape.kind == 'polygon':
                c = shape.coords
                if 'points' in c and len(c['points']) >= 3:
                    # Перевіряємо близькість до кожної лінії полігону
                    points = c['points']
                    for i in range(len(points)):
                        p1 = points[i]
                        p2 = points[(i + 1) % len(points)]
                        if self._point_near_line(x, y, p1[0], p1[1], p2[0], p2[1], tolerance / self.zoom_factor):
                            return idx
            elif shape.kind == 'text':
                c = shape.coords
                # Приблизна область тексту (можна покращити)
                text = getattr(shape, 'text', '')
                font_scale = getattr(shape, 'font_scale', 1.0)
                text_width = len(text) * 10 * font_scale
                text_height = 20 * font_scale
                if (c['x'] <= x <= c['x'] + text_width and
                    c['y'] - text_height <= y <= c['y']):
                    return idx
            elif shape.kind == 'point':
                c = shape.coords
                dist = math.hypot(x - c['x'], y - c['y'])
                if dist < tolerance / self.zoom_factor:
                    return idx
        return None
    
    def _point_near_line(self, px, py, x1, y1, x2, y2, tolerance):
        """Перевірити чи точка близько до лінії"""
        # Відстань від точки до лінії
        line_len = math.hypot(x2 - x1, y2 - y1)
        if line_len < 0.001:
            return math.hypot(px - x1, py - y1) < tolerance
        
        # Проекція точки на лінію
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len * line_len)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        dist = math.hypot(px - proj_x, py - proj_y)
        return dist < tolerance
    
    def _point_near_curve(self, px, py, x1, y1, x2, y2, cx, cy, tolerance):
        """Перевірити чи точка близько до кривої Безьє"""
        # Апроксимуємо криву точками і перевіряємо відстань
        min_dist = float('inf')
        steps = 20
        for i in range(steps + 1):
            t = i / steps
            # Квадратична крива Безьє: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
            bx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
            by = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
            dist = math.hypot(px - bx, py - by)
            min_dist = min(min_dist, dist)
        return min_dist < tolerance
    
    def _is_point_near_line_middle(self, px, py, x1, y1, x2, y2, tolerance):
        """Перевірити чи точка близько до середини лінії"""
        # Середина лінії
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        
        # Перевіряємо чи точка близько до середини
        dist_to_middle = math.hypot(px - mx, py - my)
        if dist_to_middle > tolerance * 2:
            return False, None
        
        # Перевіряємо чи точка на лінії
        line_len = math.hypot(x2 - x1, y2 - y1)
        if line_len < 0.001:
            return False, None
        
        # Проекція точки на лінію
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len * line_len)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        dist = math.hypot(px - proj_x, py - proj_y)
        # Якщо близько до лінії і близько до середини
        if dist < tolerance and abs(t - 0.5) < 0.3:
            return True, t
        return False, None
    
    def _find_shapes_in_rect(self, x1, y1, x2, y2):
        """Знайти всі фігури в прямокутнику"""
        shapes_in_rect = []
        for idx, shape in enumerate(self.shapes):
            if shape.kind in ['line', 'arrow', 'curve']:
                c = shape.coords
                # Перевіряємо чи обидві точки лінії/кривої в прямокутнику
                if (x1 <= c['x1'] <= x2 and y1 <= c['y1'] <= y2 and
                    x1 <= c['x2'] <= x2 and y1 <= c['y2'] <= y2):
                    shapes_in_rect.append(idx)
            elif shape.kind in ['circle', 'ellipse']:
                c = shape.coords
                # Перевіряємо чи центр кола/еліпса в прямокутнику
                if x1 <= c['cx'] <= x2 and y1 <= c['cy'] <= y2:
                    shapes_in_rect.append(idx)
            elif shape.kind == 'rectangle':
                c = shape.coords
                # Перевіряємо чи центр прямокутника в прямокутнику виділення
                cx = (c['x1'] + c['x2']) / 2
                cy = (c['y1'] + c['y2']) / 2
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    shapes_in_rect.append(idx)
            elif shape.kind == 'polygon':
                c = shape.coords
                if 'points' in c and len(c['points']) > 0:
                    # Перевіряємо чи всі точки полігону в прямокутнику
                    all_inside = all(x1 <= px <= x2 and y1 <= py <= y2 for px, py in c['points'])
                    if all_inside:
                        shapes_in_rect.append(idx)
            elif shape.kind in ['text', 'point']:
                c = shape.coords
                # Перевіряємо чи позиція тексту/крапки в прямокутнику
                if x1 <= c['x'] <= x2 and y1 <= c['y'] <= y2:
                    shapes_in_rect.append(idx)
        return shapes_in_rect
    
    # --- копіювання/вставка ---
    
    def copy_selected(self):
        """Копіювати вибрані фігури в буфер обміну"""
        self.clipboard = [self.shapes[idx] for idx in sorted(self.selected_shapes)]
    
    def paste(self):
        """Вставити фігури з буфера обміну"""
        if not self.clipboard:
            return
        
        # Вставляємо зі зсувом (достатньо великим, щоб було видно)
        offset_x = 30
        offset_y = 30
        new_shapes_indices = []
        
        for shape in self.clipboard:
            new_shape = Shape(
                shape.kind,
                color_bgr=shape.color_bgr,
                thickness=shape.thickness,
                style=shape.style,
                line_style=getattr(shape, 'line_style', 'solid'),
                text=getattr(shape, 'text', ''),
                font_scale=getattr(shape, 'font_scale', 1.0),
                filled=getattr(shape, 'filled', False)
            )
            
            if shape.kind in ['line', 'arrow']:
                c = shape.coords
                new_shape.coords = {
                    'x1': c['x1'] + offset_x,
                    'y1': c['y1'] + offset_y,
                    'x2': c['x2'] + offset_x,
                    'y2': c['y2'] + offset_y,
                }
            elif shape.kind == 'curve':
                c = shape.coords
                new_shape.coords = {
                    'x1': c['x1'] + offset_x,
                    'y1': c['y1'] + offset_y,
                    'x2': c['x2'] + offset_x,
                    'y2': c['y2'] + offset_y,
                    'cx': c['cx'] + offset_x,
                    'cy': c['cy'] + offset_y,
                }
            elif shape.kind == 'circle':
                c = shape.coords
                new_shape.coords = {
                    'cx': c['cx'] + offset_x,
                    'cy': c['cy'] + offset_y,
                    'r': c['r'],
                }
            elif shape.kind == 'ellipse':
                c = shape.coords
                new_shape.coords = {
                    'cx': c['cx'] + offset_x,
                    'cy': c['cy'] + offset_y,
                    'rx': c['rx'],
                    'ry': c['ry'],
                    'angle': c.get('angle', 0),
                }
            elif shape.kind == 'rectangle':
                c = shape.coords
                new_shape.coords = {
                    'x1': c['x1'] + offset_x,
                    'y1': c['y1'] + offset_y,
                    'x2': c['x2'] + offset_x,
                    'y2': c['y2'] + offset_y,
                }
            elif shape.kind == 'polygon':
                c = shape.coords
                new_shape.coords = {
                    'points': [(x + offset_x, y + offset_y) for x, y in c['points']]
                }
            elif shape.kind in ['text', 'point']:
                c = shape.coords
                new_shape.coords = {
                    'x': c['x'] + offset_x,
                    'y': c['y'] + offset_y,
                }
            
            self.shapes.append(new_shape)
            new_shapes_indices.append(len(self.shapes) - 1)
        
        # Вибираємо вставлені фігури
        self.selected_shapes = set(new_shapes_indices)
        self.update()
    
    # --- дзеркалення ---
    
    def flip_horizontal(self):
        """Створити відзеркалені копії вибраних фігур по горизонталі"""
        if not self.selected_shapes:
            return
        
        # Знаходимо bounding box виділених фігур
        bbox = self._get_selection_bbox()
        if bbox is None:
            return
        
        min_x, min_y, max_x, max_y = bbox
        
        # Відзеркалюємо відносно правого краю з невеликим зазором
        gap = 20  # зазор між оригіналом і копією
        mirror_axis = max_x + gap
        
        new_shapes_indices = []
        
        # Створюємо відзеркалені копії
        for idx in sorted(self.selected_shapes):
            shape = self.shapes[idx]
            
            # Створюємо нову фігуру
            new_shape = Shape(
                shape.kind,
                color_bgr=shape.color_bgr,
                thickness=shape.thickness,
                style=shape.style,
                line_style=getattr(shape, 'line_style', 'solid'),
                text=getattr(shape, 'text', ''),
                font_scale=getattr(shape, 'font_scale', 1.0),
                filled=getattr(shape, 'filled', False)
            )
            
            if shape.kind in ['line', 'arrow']:
                c = shape.coords
                # Відстань від осі дзеркалення
                new_x1 = mirror_axis + (mirror_axis - c['x1'])
                new_x2 = mirror_axis + (mirror_axis - c['x2'])
                new_shape.coords = {
                    'x1': new_x1,
                    'y1': c['y1'],
                    'x2': new_x2,
                    'y2': c['y2'],
                }
            elif shape.kind == 'curve':
                c = shape.coords
                new_x1 = mirror_axis + (mirror_axis - c['x1'])
                new_x2 = mirror_axis + (mirror_axis - c['x2'])
                new_cx = mirror_axis + (mirror_axis - c['cx'])
                new_shape.coords = {
                    'x1': new_x1,
                    'y1': c['y1'],
                    'x2': new_x2,
                    'y2': c['y2'],
                    'cx': new_cx,
                    'cy': c['cy'],
                }
            elif shape.kind == 'circle':
                c = shape.coords
                new_cx = mirror_axis + (mirror_axis - c['cx'])
                new_shape.coords = {
                    'cx': new_cx,
                    'cy': c['cy'],
                    'r': c['r'],
                }
            elif shape.kind == 'ellipse':
                c = shape.coords
                new_cx = mirror_axis + (mirror_axis - c['cx'])
                new_shape.coords = {
                    'cx': new_cx,
                    'cy': c['cy'],
                    'rx': c['rx'],
                    'ry': c['ry'],
                    'angle': c.get('angle', 0),
                }
            elif shape.kind == 'rectangle':
                c = shape.coords
                new_x1 = mirror_axis + (mirror_axis - c['x1'])
                new_x2 = mirror_axis + (mirror_axis - c['x2'])
                new_shape.coords = {
                    'x1': new_x1,
                    'y1': c['y1'],
                    'x2': new_x2,
                    'y2': c['y2'],
                }
            elif shape.kind == 'polygon':
                c = shape.coords
                new_points = [(mirror_axis + (mirror_axis - x), y) for x, y in c['points']]
                new_shape.coords = {
                    'points': new_points,
                }
            elif shape.kind in ['text', 'point']:
                c = shape.coords
                new_x = mirror_axis + (mirror_axis - c['x'])
                new_shape.coords = {
                    'x': int(new_x),
                    'y': c['y'],
                }
            
            self.shapes.append(new_shape)
            new_shapes_indices.append(len(self.shapes) - 1)
        
        # Вибираємо нові відзеркалені фігури
        self.selected_shapes = set(new_shapes_indices)
        self.update()
    
    def flip_vertical(self):
        """Створити відзеркалені копії вибраних фігур по вертикалі"""
        if not self.selected_shapes:
            return
        
        # Знаходимо bounding box виділених фігур
        bbox = self._get_selection_bbox()
        if bbox is None:
            return
        
        min_x, min_y, max_x, max_y = bbox
        
        # Відзеркалюємо відносно нижнього краю з невеликим зазором
        gap = 20  # зазор між оригіналом і копією
        mirror_axis = max_y + gap
        
        new_shapes_indices = []
        
        # Створюємо відзеркалені копії
        for idx in sorted(self.selected_shapes):
            shape = self.shapes[idx]
            
            # Створюємо нову фігуру
            new_shape = Shape(
                shape.kind,
                color_bgr=shape.color_bgr,
                thickness=shape.thickness,
                style=shape.style,
                line_style=getattr(shape, 'line_style', 'solid'),
                text=getattr(shape, 'text', ''),
                font_scale=getattr(shape, 'font_scale', 1.0),
                filled=getattr(shape, 'filled', False)
            )
            
            if shape.kind in ['line', 'arrow']:
                c = shape.coords
                # Відстань від осі дзеркалення
                new_y1 = mirror_axis + (mirror_axis - c['y1'])
                new_y2 = mirror_axis + (mirror_axis - c['y2'])
                new_shape.coords = {
                    'x1': c['x1'],
                    'y1': new_y1,
                    'x2': c['x2'],
                    'y2': new_y2,
                }
            elif shape.kind == 'curve':
                c = shape.coords
                new_y1 = mirror_axis + (mirror_axis - c['y1'])
                new_y2 = mirror_axis + (mirror_axis - c['y2'])
                new_cy = mirror_axis + (mirror_axis - c['cy'])
                new_shape.coords = {
                    'x1': c['x1'],
                    'y1': new_y1,
                    'x2': c['x2'],
                    'y2': new_y2,
                    'cx': c['cx'],
                    'cy': new_cy,
                }
            elif shape.kind == 'circle':
                c = shape.coords
                new_cy = mirror_axis + (mirror_axis - c['cy'])
                new_shape.coords = {
                    'cx': c['cx'],
                    'cy': new_cy,
                    'r': c['r'],
                }
            elif shape.kind == 'ellipse':
                c = shape.coords
                new_cy = mirror_axis + (mirror_axis - c['cy'])
                new_shape.coords = {
                    'cx': c['cx'],
                    'cy': new_cy,
                    'rx': c['rx'],
                    'ry': c['ry'],
                    'angle': c.get('angle', 0),
                }
            elif shape.kind == 'rectangle':
                c = shape.coords
                new_y1 = mirror_axis + (mirror_axis - c['y1'])
                new_y2 = mirror_axis + (mirror_axis - c['y2'])
                new_shape.coords = {
                    'x1': c['x1'],
                    'y1': new_y1,
                    'x2': c['x2'],
                    'y2': new_y2,
                }
            elif shape.kind == 'polygon':
                c = shape.coords
                new_points = [(x, mirror_axis + (mirror_axis - y)) for x, y in c['points']]
                new_shape.coords = {
                    'points': new_points,
                }
            elif shape.kind in ['text', 'point']:
                c = shape.coords
                new_y = mirror_axis + (mirror_axis - c['y'])
                new_shape.coords = {
                    'x': c['x'],
                    'y': int(new_y),
                }
            
            self.shapes.append(new_shape)
            new_shapes_indices.append(len(self.shapes) - 1)
        
        # Вибираємо нові відзеркалені фігури
        self.selected_shapes = set(new_shapes_indices)
        self.update()
    
    def _get_selection_bbox(self):
        """Отримати bounding box (мінімальний прямокутник) виділених фігур"""
        if not self.selected_shapes:
            return None
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for idx in self.selected_shapes:
            shape = self.shapes[idx]
            if shape.kind in ['line', 'arrow', 'curve']:
                c = shape.coords
                min_x = min(min_x, c['x1'], c['x2'])
                max_x = max(max_x, c['x1'], c['x2'])
                min_y = min(min_y, c['y1'], c['y2'])
                max_y = max(max_y, c['y1'], c['y2'])
                # Для кривих також враховуємо контрольну точку
                if shape.kind == 'curve':
                    min_x = min(min_x, c['cx'])
                    max_x = max(max_x, c['cx'])
                    min_y = min(min_y, c['cy'])
                    max_y = max(max_y, c['cy'])
            elif shape.kind == 'circle':
                c = shape.coords
                min_x = min(min_x, c['cx'] - c['r'])
                max_x = max(max_x, c['cx'] + c['r'])
                min_y = min(min_y, c['cy'] - c['r'])
                max_y = max(max_y, c['cy'] + c['r'])
            elif shape.kind == 'ellipse':
                c = shape.coords
                min_x = min(min_x, c['cx'] - c['rx'])
                max_x = max(max_x, c['cx'] + c['rx'])
                min_y = min(min_y, c['cy'] - c['ry'])
                max_y = max(max_y, c['cy'] + c['ry'])
            elif shape.kind == 'rectangle':
                c = shape.coords
                min_x = min(min_x, c['x1'], c['x2'])
                max_x = max(max_x, c['x1'], c['x2'])
                min_y = min(min_y, c['y1'], c['y2'])
                max_y = max(max_y, c['y1'], c['y2'])
            elif shape.kind == 'polygon':
                c = shape.coords
                if 'points' in c:
                    for px, py in c['points']:
                        min_x = min(min_x, px)
                        max_x = max(max_x, px)
                        min_y = min(min_y, py)
                        max_y = max(max_y, py)
            elif shape.kind == 'text':
                c = shape.coords
                text = getattr(shape, 'text', '')
                font_scale = getattr(shape, 'font_scale', 1.0)
                text_width = len(text) * 10 * font_scale
                text_height = 20 * font_scale
                min_x = min(min_x, c['x'])
                max_x = max(max_x, c['x'] + text_width)
                min_y = min(min_y, c['y'] - text_height)
                max_y = max(max_y, c['y'])
            elif shape.kind == 'point':
                c = shape.coords
                min_x = min(min_x, c['x'])
                max_x = max(max_x, c['x'])
                min_y = min(min_y, c['y'])
                max_y = max(max_y, c['y'])
        
        if min_x == float('inf'):
            return None
        
        return (min_x, min_y, max_x, max_y)
    
    def _get_selection_center_x(self):
        """Отримати центр X виділених фігур"""
        bbox = self._get_selection_bbox()
        if bbox is None:
            return 0
        min_x, min_y, max_x, max_y = bbox
        return (min_x + max_x) / 2
    
    def _get_selection_center_y(self):
        """Отримати центр Y виділених фігур"""
        bbox = self._get_selection_bbox()
        if bbox is None:
            return 0
        min_x, min_y, max_x, max_y = bbox
        return (min_y + max_y) / 2

    # --- рендер ---

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0))

        transform = QtGui.QTransform()
        transform.translate(self.pan_x, self.pan_y)
        transform.scale(self.zoom_factor, self.zoom_factor)
        painter.setTransform(transform)

        self._draw_grid(painter)
        self._draw_center_axes(painter)

        for idx, shape in enumerate(self.shapes):
            r, g, b = shape.color_bgr[2], shape.color_bgr[1], shape.color_bgr[0]
            color = QtGui.QColor(r, g, b)
            pen = QtGui.QPen(color)
            pen.setWidth(max(1, int(shape.thickness / self.zoom_factor)))
            
            # Стиль лінії (dashed, dotted, solid)
            line_style = getattr(shape, 'line_style', 'solid')
            if line_style == 'dashed':
                pen.setStyle(QtCore.Qt.DashLine)
            elif line_style == 'dotted':
                pen.setStyle(QtCore.Qt.DotLine)
            else:
                pen.setStyle(QtCore.Qt.SolidLine)
            
            # Якщо фігура вибрана, малюємо її яскравіше
            if idx in self.selected_shapes:
                pen.setWidth(max(2, int((shape.thickness + 2) / self.zoom_factor)))
                if line_style == 'solid':
                    pen.setStyle(QtCore.Qt.DashLine)
            
            # Чи заповнена фігура
            filled = getattr(shape, 'filled', False)
            
            painter.setPen(pen)
            if filled and shape.kind in ['circle', 'rectangle', 'ellipse', 'polygon']:
                brush = QtGui.QBrush(color)
                painter.setBrush(brush)
            else:
                painter.setBrush(QtCore.Qt.NoBrush)
            
            if shape.kind == 'line':
                c = shape.coords
                painter.drawLine(
                    QtCore.QPointF(c['x1'], c['y1']),
                    QtCore.QPointF(c['x2'], c['y2'])
                )
            elif shape.kind == 'arrow':
                c = shape.coords
                # Малюємо лінію
                painter.drawLine(
                    QtCore.QPointF(c['x1'], c['y1']),
                    QtCore.QPointF(c['x2'], c['y2'])
                )
                # Малюємо стрілку (трикутник на кінці)
                dx = c['x2'] - c['x1']
                dy = c['y2'] - c['y1']
                length = math.hypot(dx, dy)
                if length > 0:
                    # Нормалізуємо вектор
                    dx /= length
                    dy /= length
                    # Розмір стрілки
                    arrow_size = min(20, length / 3)
                    # Точка кінця стрілки
                    ax, ay = c['x2'], c['y2']
                    # Дві точки основи стрілки
                    b1x = ax - arrow_size * dx + arrow_size * 0.3 * dy
                    b1y = ay - arrow_size * dy - arrow_size * 0.3 * dx
                    b2x = ax - arrow_size * dx - arrow_size * 0.3 * dy
                    b2y = ay - arrow_size * dy + arrow_size * 0.3 * dx
                    # Малюємо трикутник
                    arrow_poly = QtGui.QPolygonF([
                        QtCore.QPointF(ax, ay),
                        QtCore.QPointF(b1x, b1y),
                        QtCore.QPointF(b2x, b2y)
                    ])
                    painter.setBrush(QtGui.QBrush(color))
                    painter.drawPolygon(arrow_poly)
            elif shape.kind == 'curve':
                c = shape.coords
                # Малюємо квадратичну криву Безьє
                path = QtGui.QPainterPath()
                path.moveTo(c['x1'], c['y1'])
                path.quadTo(c['cx'], c['cy'], c['x2'], c['y2'])
                painter.drawPath(path)
                
                # Якщо фігура вибрана - показуємо контрольну точку
                if idx in self.selected_shapes and self.show_control_points:
                    # Лінії до контрольної точки
                    pen_helper = QtGui.QPen(QtGui.QColor(100, 100, 100))
                    pen_helper.setStyle(QtCore.Qt.DotLine)
                    pen_helper.setWidth(1)
                    painter.setPen(pen_helper)
                    painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['cx'], c['cy']))
                    painter.drawLine(QtCore.QPointF(c['x2'], c['y2']), QtCore.QPointF(c['cx'], c['cy']))
                    
                    # Контрольна точка
                    ctrl_point_size = 6 / self.zoom_factor
                    painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 200, 0)))
                    painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
                    painter.drawEllipse(QtCore.QPointF(c['cx'], c['cy']), ctrl_point_size, ctrl_point_size)
                    
                    # Кінцеві точки
                    end_point_size = 4 / self.zoom_factor
                    painter.setBrush(QtGui.QBrush(color))
                    painter.setPen(pen)
                    painter.drawEllipse(QtCore.QPointF(c['x1'], c['y1']), end_point_size, end_point_size)
                    painter.drawEllipse(QtCore.QPointF(c['x2'], c['y2']), end_point_size, end_point_size)
            elif shape.kind == 'circle':
                c = shape.coords
                painter.drawEllipse(QtCore.QPointF(c['cx'], c['cy']), c['r'], c['r'])
            elif shape.kind == 'ellipse':
                c = shape.coords
                cx, cy = c['cx'], c['cy']
                rx, ry = c['rx'], c['ry']
                painter.drawEllipse(QtCore.QRectF(cx - rx, cy - ry, 2 * rx, 2 * ry))
            elif shape.kind == 'rectangle':
                c = shape.coords
                x1, y1 = min(c['x1'], c['x2']), min(c['y1'], c['y2'])
                x2, y2 = max(c['x1'], c['x2']), max(c['y1'], c['y2'])
                painter.drawRect(QtCore.QRectF(x1, y1, x2 - x1, y2 - y1))
            elif shape.kind == 'polygon':
                c = shape.coords
                if 'points' in c and len(c['points']) >= 3:
                    poly = QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in c['points']])
                    painter.drawPolygon(poly)
            elif shape.kind == 'point':
                c = shape.coords
                # Малюємо крапку як маленьке коло
                point_size = max(3, shape.thickness * 2)
                painter.setBrush(QtGui.QBrush(color))
                painter.drawEllipse(QtCore.QPointF(c['x'], c['y']), point_size, point_size)
            elif shape.kind == 'text':
                c = shape.coords
                # Перевіряємо наявність атрибутів (для сумісності зі старими фігурами)
                font_scale = getattr(shape, 'font_scale', 1.0)
                text = getattr(shape, 'text', '')
                font = QtGui.QFont("Arial", int(16 * font_scale))
                painter.setFont(font)
                painter.drawText(QtCore.QPointF(c['x'], c['y']), text)
            
            painter.setBrush(QtCore.Qt.NoBrush)
        
        # Малюємо рамку виділення
        if self.current_mode == 'select' and self.temp_point is not None and self.mouse_pos is not None:
            x0, y0 = self.temp_point
            x1, y1 = self.mouse_pos
            pen = QtGui.QPen(QtGui.QColor(100, 150, 255))
            pen.setStyle(QtCore.Qt.DashLine)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(QtCore.QRectF(
                QtCore.QPointF(min(x0, x1), min(y0, y1)),
                QtCore.QPointF(max(x0, x1), max(y0, y1))
            ))

        # прев'ю незавершеної фігури
        if self.current_mode in ['line', 'circle', 'rectangle', 'arrow', 'ellipse'] and self.temp_point is not None and self.mouse_pos is not None:
            x0, y0 = self.temp_point
            x1, y1 = self.mouse_pos
            r, g, b = self.current_color_bgr[2], self.current_color_bgr[1], self.current_color_bgr[0]
            color = QtGui.QColor(r, g, b)
            pen = QtGui.QPen(color)
            pen.setStyle(QtCore.Qt.DotLine)
            pen.setWidth(max(1, int(self.current_thickness / self.zoom_factor)))
            painter.setPen(pen)
            
            if self.current_filled:
                brush = QtGui.QBrush(color)
                painter.setBrush(brush)
            else:
                painter.setBrush(QtCore.Qt.NoBrush)
            
            if self.current_mode == 'line':
                painter.drawLine(
                    QtCore.QPointF(x0, y0),
                    QtCore.QPointF(x1, y1)
                )
            elif self.current_mode == 'arrow':
                painter.drawLine(
                    QtCore.QPointF(x0, y0),
                    QtCore.QPointF(x1, y1)
                )
                # Прев'ю стрілки
                dx = x1 - x0
                dy = y1 - y0
                length = math.hypot(dx, dy)
                if length > 0:
                    dx /= length
                    dy /= length
                    arrow_size = min(20, length / 3)
                    ax, ay = x1, y1
                    b1x = ax - arrow_size * dx + arrow_size * 0.3 * dy
                    b1y = ay - arrow_size * dy - arrow_size * 0.3 * dx
                    b2x = ax - arrow_size * dx - arrow_size * 0.3 * dy
                    b2y = ay - arrow_size * dy + arrow_size * 0.3 * dx
                    arrow_poly = QtGui.QPolygonF([
                        QtCore.QPointF(ax, ay),
                        QtCore.QPointF(b1x, b1y),
                        QtCore.QPointF(b2x, b2y)
                    ])
                    painter.setBrush(QtGui.QBrush(color))
                    painter.drawPolygon(arrow_poly)
            elif self.current_mode == 'circle':
                r = int(round(math.hypot(x1 - x0, y1 - y0)))
                painter.drawEllipse(QtCore.QPointF(x0, y0), r, r)
            elif self.current_mode == 'rectangle':
                rect_x1, rect_y1 = min(x0, x1), min(y0, y1)
                rect_x2, rect_y2 = max(x0, x1), max(y0, y1)
                painter.drawRect(QtCore.QRectF(rect_x1, rect_y1, rect_x2 - rect_x1, rect_y2 - rect_y1))
            elif self.current_mode == 'ellipse':
                rx = abs(x1 - x0)
                ry = abs(y1 - y0)
                painter.drawEllipse(QtCore.QRectF(x0 - rx, y0 - ry, 2 * rx, 2 * ry))
        
        # Малюємо поточний полігон в процесі малювання
        if self.current_mode == 'polygon' and len(self.polygon_points) > 0:
            r, g, b = self.current_color_bgr[2], self.current_color_bgr[1], self.current_color_bgr[0]
            color = QtGui.QColor(r, g, b)
            pen = QtGui.QPen(color)
            pen.setWidth(max(1, int(self.current_thickness / self.zoom_factor)))
            painter.setPen(pen)
            
            # Малюємо точки полігону
            for px, py in self.polygon_points:
                point_size = 4
                painter.setBrush(QtGui.QBrush(color))
                painter.drawEllipse(QtCore.QPointF(px, py), point_size, point_size)
            
            # Малюємо лінії між точками
            painter.setBrush(QtCore.Qt.NoBrush)
            pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(pen)
            for i in range(len(self.polygon_points) - 1):
                p1 = self.polygon_points[i]
                p2 = self.polygon_points[i + 1]
                painter.drawLine(QtCore.QPointF(p1[0], p1[1]), QtCore.QPointF(p2[0], p2[1]))
            
            # Лінія від останньої точки до курсору
            if self.mouse_pos is not None and len(self.polygon_points) > 0:
                last_point = self.polygon_points[-1]
                pen.setStyle(QtCore.Qt.DotLine)
                painter.setPen(pen)
                painter.drawLine(
                    QtCore.QPointF(last_point[0], last_point[1]),
                    QtCore.QPointF(self.mouse_pos[0], self.mouse_pos[1])
                )
            
            # Лінія замикання полігону (від останньої до першої точки)
            if len(self.polygon_points) >= 3:
                first_point = self.polygon_points[0]
                last_point = self.polygon_points[-1]
                pen.setStyle(QtCore.Qt.DotLine)
                painter.setPen(pen)
                painter.drawLine(
                    QtCore.QPointF(last_point[0], last_point[1]),
                    QtCore.QPointF(first_point[0], first_point[1])
                )
    
    def _screen_to_world(self, screen_x, screen_y):
        world_x = (screen_x - self.pan_x) / self.zoom_factor
        world_y = (screen_y - self.pan_y) / self.zoom_factor
        return world_x, world_y
    
    def _world_to_screen(self, world_x, world_y):
        screen_x = world_x * self.zoom_factor + self.pan_x
        screen_y = world_y * self.zoom_factor + self.pan_y
        return screen_x, screen_y

    # --- редагування списку фігур ---

    def undo(self):
        if self.shapes:
            self.shapes.pop()
            self.update()

    def clear_all(self):
        self.shapes.clear()
        self.temp_point = None
        self.update()

    # --- генерація коду OpenCV ---

    def generate_opencv_code_simple(self, origin_mode='editor', canvas_width=None, canvas_height=None) -> str:
        """Старий метод генерації простого коду (залишено для сумісності)"""
        lines = []
        lines.append("import cv2")
        lines.append("import numpy as np")
        lines.append("import math")
        lines.append("")
        lines.append("")
        lines.append("class DrawingOverlay:")
        lines.append("    \"\"\"")
        lines.append("    OpenCV Drawing Overlay - Auto-generated by OpenCV HUD Editor")
        lines.append("    \"\"\"")
        lines.append("    ")
        lines.append("    def __init__(self):")
        lines.append("        # Кольори (BGR формат)")
        
        unique_colors = {}
        color_name_map = {}
        color_counter = {}
        
        for shape in self.shapes:
            color_bgr = shape.color_bgr
            style = shape.style
            key = (color_bgr, style)
            
            if key not in color_name_map:
                color_name = self._get_color_name(color_bgr, style, color_counter)
                color_name_map[key] = color_name
                unique_colors[key] = color_bgr
        
        if unique_colors:
            lines.append("    # Кольори")
            lines.append("    colors = {")
            for key, color_bgr in unique_colors.items():
                color_name = color_name_map[key]
                b, g, r = color_bgr
                lines.append(f"        '{color_name}': ({b}, {g}, {r}),")
            lines.append("    }")
            lines.append("")
        
        if origin_mode == 'center' and canvas_width is not None and canvas_height is not None:
            offset_x = canvas_width // 2
            offset_y = canvas_height // 2
            lines.append(f"    # Система координат: відносно центру")
            lines.append(f"    # Зсув: ({offset_x}, {offset_y})")
            lines.append("")
        else:
            offset_x = 0
            offset_y = 0
            lines.append("    # Система координат: як у редакторі (0,0 в лівому верхньому куті)")
            lines.append("")

        for shape in self.shapes:
            color_bgr = shape.color_bgr
            style = shape.style
            key = (color_bgr, style)
            color_name = color_name_map[key]
            t = shape.thickness
            style_comment = f"  # style: {shape.style}" if shape.style != 'default' else ""
            
            # Перевірка на заповнену фігуру
            filled = getattr(shape, 'filled', False)
            thickness_param = -1 if filled else t
            
            if shape.kind == 'line':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                lines.append(
                    f"    cv2.line(frame, "
                    f"({x1}, {y1}), "
                    f"({x2}, {y2}), "
                    f"colors['{color_name}'], {t}, cv2.LINE_AA){style_comment}"
                )
            elif shape.kind == 'arrow':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                lines.append(
                    f"    cv2.arrowedLine(frame, "
                    f"({x1}, {y1}), "
                    f"({x2}, {y2}), "
                    f"colors['{color_name}'], {t}, cv2.LINE_AA, tipLength=0.3){style_comment}"
                )
            elif shape.kind == 'circle':
                c = shape.coords
                cx = int(c['cx']) - offset_x
                cy = int(c['cy']) - offset_y
                r = int(c['r'])
                lines.append(
                    f"    cv2.circle(frame, "
                    f"({cx}, {cy}), "
                    f"{r}, "
                    f"colors['{color_name}'], {thickness_param}, cv2.LINE_AA){style_comment}"
                )
            elif shape.kind == 'ellipse':
                c = shape.coords
                cx = int(c['cx']) - offset_x
                cy = int(c['cy']) - offset_y
                rx = int(c['rx'])
                ry = int(c['ry'])
                angle = int(c.get('angle', 0))
                lines.append(
                    f"    cv2.ellipse(frame, "
                    f"({cx}, {cy}), "
                    f"({rx}, {ry}), "
                    f"{angle}, 0, 360, "
                    f"colors['{color_name}'], {thickness_param}, cv2.LINE_AA){style_comment}"
                )
            elif shape.kind == 'rectangle':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                lines.append(
                    f"    cv2.rectangle(frame, "
                    f"({x1}, {y1}), "
                    f"({x2}, {y2}), "
                    f"colors['{color_name}'], {thickness_param}, cv2.LINE_AA){style_comment}"
                )
            elif shape.kind == 'polygon':
                c = shape.coords
                if 'points' in c:
                    pts = [(int(x) - offset_x, int(y) - offset_y) for x, y in c['points']]
                    pts_str = ', '.join([f"[{x}, {y}]" for x, y in pts])
                    lines.append(f"    pts = np.array([[{pts_str}]], dtype=np.int32)")
                    if filled:
                        lines.append(
                            f"    cv2.fillPoly(frame, pts, colors['{color_name}'], cv2.LINE_AA){style_comment}"
                        )
                    else:
                        lines.append(
                            f"    cv2.polylines(frame, pts, True, colors['{color_name}'], {t}, cv2.LINE_AA){style_comment}"
                        )
            elif shape.kind == 'point':
                c = shape.coords
                x = int(c['x']) - offset_x
                y = int(c['y']) - offset_y
                point_size = max(3, t * 2)
                lines.append(
                    f"    cv2.circle(frame, "
                    f"({x}, {y}), "
                    f"{point_size}, "
                    f"colors['{color_name}'], -1, cv2.LINE_AA){style_comment}"
                )
            elif shape.kind == 'text':
                c = shape.coords
                x = int(c['x']) - offset_x
                y = int(c['y']) - offset_y
                text = getattr(shape, 'text', '')
                font_scale = getattr(shape, 'font_scale', 1.0)
                lines.append(
                    f"    cv2.putText(frame, "
                    f"'{text}', "
                    f"({x}, {y}), "
                    f"cv2.FONT_HERSHEY_SIMPLEX, {font_scale}, "
                    f"colors['{color_name}'], {t}, cv2.LINE_AA){style_comment}"
                )

        lines.append("")
        lines.append("    return frame")
        return "\n".join(lines)
    
    def generate_opencv_code(self, origin_mode='editor', canvas_width=None, canvas_height=None) -> str:
        """Генерація структурованого OpenCV коду у вигляді класу"""
        lines = []
        
        # Імпорти
        lines.append("\"\"\"")
        lines.append("OpenCV Drawing Overlay - Auto-generated by OpenCV HUD Editor")
        lines.append("\"\"\"")
        lines.append("import cv2")
        lines.append("import numpy as np")
        
        # Перевіряємо чи потрібен math (для пунктирних/точкових ліній, стрілок або кривих)
        needs_math = False
        has_dashed = False
        has_dotted = False
        has_curves = False
        
        for shape in self.shapes:
            line_style = getattr(shape, 'line_style', 'solid')
            if line_style == 'dashed':
                has_dashed = True
                needs_math = True
            elif line_style == 'dotted':
                has_dotted = True
                needs_math = True
            if shape.kind == 'arrow' and line_style != 'solid':
                needs_math = True
            if shape.kind == 'curve':
                has_curves = True
                needs_math = True
        
        if needs_math:
            lines.append("import math")
        
        lines.append("")
        lines.append("")
        
        # Збираємо унікальні кольори
        unique_colors = {}
        color_name_map = {}
        color_counter = {}
        
        for shape in self.shapes:
            color_bgr = shape.color_bgr
            style = shape.style
            key = (color_bgr, style)
            
            if key not in color_name_map:
                color_name = self._get_color_name(color_bgr, style, color_counter)
                color_name_map[key] = color_name
                unique_colors[key] = color_bgr
        
        # Визначаємо offset
        if origin_mode == 'center' and canvas_width is not None and canvas_height is not None:
            offset_x = canvas_width // 2
            offset_y = canvas_height // 2
        else:
            offset_x = 0
            offset_y = 0
        
        # Початок класу
        lines.append("class DrawingOverlay:")
        lines.append("    \"\"\"")
        lines.append("    Клас для малювання overlay графіки на кадрі")
        lines.append("    ")
        if origin_mode == 'center':
            lines.append(f"    Система координат: відносно центру (offset: {offset_x}, {offset_y})")
        else:
            lines.append("    Система координат: як у редакторі (0,0 в лівому верхньому куті)")
        lines.append("    ")
        # Інформація про використані стилі
        styles_info = []
        if has_dashed:
            styles_info.append("dashed lines")
        if has_dotted:
            styles_info.append("dotted lines")
        if has_curves:
            styles_info.append("bezier curves")
        if styles_info:
            lines.append(f"    Використані стилі: {', '.join(styles_info)}")
        lines.append(f"    Кількість фігур: {len(self.shapes)}")
        lines.append("    \"\"\"")
        lines.append("    ")
        lines.append("    def __init__(self):")
        lines.append("        \"\"\"Ініціалізація кольорів та констант\"\"\"")
        
        # Кольори
        if unique_colors:
            lines.append("        # Кольори (BGR формат)")
            lines.append("        self.colors = {")
            for key, color_bgr in unique_colors.items():
                color_name = color_name_map[key]
                b, g, r = color_bgr
                lines.append(f"            '{color_name}': ({b}, {g}, {r}),")
            lines.append("        }")
        
        lines.append("    ")
        
        # Допоміжний метод для пунктирних ліній (ТІЛЬКИ якщо використовується)
        if has_dashed:
            lines.append("    @staticmethod")
            lines.append("    def draw_dashed_line(frame, pt1, pt2, color, thickness=1, dash_length=10):")
            lines.append("        \"\"\"Малювання пунктирної лінії\"\"\"")
            lines.append("        dist = math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])")
            lines.append("        if dist < 1:")
            lines.append("            return")
            lines.append("        dashes = int(dist / dash_length)")
            lines.append("        for i in range(dashes):")
            lines.append("            if i % 2 == 0:")
            lines.append("                start = (")
            lines.append("                    int(pt1[0] + (pt2[0] - pt1[0]) * i / dashes),")
            lines.append("                    int(pt1[1] + (pt2[1] - pt1[1]) * i / dashes)")
            lines.append("                )")
            lines.append("                end = (")
            lines.append("                    int(pt1[0] + (pt2[0] - pt1[0]) * (i + 0.5) / dashes),")
            lines.append("                    int(pt1[1] + (pt2[1] - pt1[1]) * (i + 0.5) / dashes)")
            lines.append("                )")
            lines.append("                cv2.line(frame, start, end, color, thickness, cv2.LINE_AA)")
            lines.append("    ")
        
        # Допоміжний метод для точкових ліній (ТІЛЬКИ якщо використовується)
        if has_dotted:
            lines.append("    @staticmethod")
            lines.append("    def draw_dotted_line(frame, pt1, pt2, color, thickness=1, dot_length=5):")
            lines.append("        \"\"\"Малювання точкової лінії\"\"\"")
            lines.append("        dist = math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])")
            lines.append("        if dist < 1:")
            lines.append("            return")
            lines.append("        dots = int(dist / dot_length)")
            lines.append("        for i in range(dots):")
            lines.append("            if i % 2 == 0:")
            lines.append("                pt = (")
            lines.append("                    int(pt1[0] + (pt2[0] - pt1[0]) * i / dots),")
            lines.append("                    int(pt1[1] + (pt2[1] - pt1[1]) * i / dots)")
            lines.append("                )")
            lines.append("                cv2.circle(frame, pt, max(1, thickness), color, -1, cv2.LINE_AA)")
            lines.append("    ")
        
        # Допоміжний метод для кривих Безьє (ТІЛЬКИ якщо використовується)
        if has_curves:
            lines.append("    @staticmethod")
            lines.append("    def draw_bezier_curve(frame, x1, y1, x2, y2, cx, cy, color, thickness=1, steps=20):")
            lines.append("        \"\"\"Малювання квадратичної кривої Безьє\"\"\"")
            lines.append("        points = []")
            lines.append("        for i in range(steps + 1):")
            lines.append("            t = i / steps")
            lines.append("            # Квадратична крива Безьє: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2")
            lines.append("            bx = int((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2)")
            lines.append("            by = int((1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2)")
            lines.append("            points.append([bx, by])")
            lines.append("        # Малюємо криву як polyline")
            lines.append("        pts = np.array([points], dtype=np.int32)")
            lines.append("        cv2.polylines(frame, pts, False, color, thickness, cv2.LINE_AA)")
            lines.append("    ")
        
        # Основний метод малювання
        lines.append("    def draw(self, frame):")
        lines.append("        \"\"\"")
        lines.append("        Намалювати всі фігури на кадрі")
        lines.append("        ")
        lines.append("        Args:")
        lines.append("            frame: np.ndarray (H, W, 3) BGR")
        lines.append("        ")
        lines.append("        Returns:")
        lines.append("            frame: np.ndarray з намальованими фігурами")
        lines.append("        \"\"\"")
        
        # Генеруємо код для кожної фігури
        for shape in self.shapes:
            color_bgr = shape.color_bgr
            style = shape.style
            key = (color_bgr, style)
            color_name = color_name_map[key]
            t = shape.thickness
            line_style = getattr(shape, 'line_style', 'solid')
            filled = getattr(shape, 'filled', False)
            thickness_param = -1 if filled else t
            
            # Формуємо коментар з інформацією про стилі
            comments = []
            if shape.style != 'default':
                comments.append(f"style: {shape.style}")
            if line_style != 'solid':
                comments.append(f"line: {line_style}")
            if filled:
                comments.append("filled")
            comment = f"  # {', '.join(comments)}" if comments else ""
            
            if shape.kind == 'line':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                
                if line_style == 'dashed':
                    lines.append(f"        self.draw_dashed_line(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {t}){comment}")
                elif line_style == 'dotted':
                    lines.append(f"        self.draw_dotted_line(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {t}){comment}")
                else:
                    lines.append(f"        cv2.line(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {t}, cv2.LINE_AA){comment}")
                    
            elif shape.kind == 'arrow':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                
                if line_style == 'solid':
                    lines.append(f"        cv2.arrowedLine(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {t}, cv2.LINE_AA, tipLength=0.3){comment}")
                else:
                    # Для пунктирних стрілок малюємо лінію + трикутник
                    if line_style == 'dashed':
                        lines.append(f"        self.draw_dashed_line(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {t}){comment}")
                    else:
                        lines.append(f"        self.draw_dotted_line(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {t}){comment}")
                    # Малюємо наконечник стрілки
                    lines.append(f"        dx, dy = {x2} - {x1}, {y2} - {y1}")
                    lines.append(f"        length = math.hypot(dx, dy)")
                    lines.append(f"        if length > 0:")
                    lines.append(f"            dx, dy = dx / length, dy / length")
                    lines.append(f"            arrow_size = min(20, length / 3)")
                    lines.append(f"            pts = np.array([[")
                    lines.append(f"                [{x2}, {y2}],")
                    lines.append(f"                [int({x2} - arrow_size * dx + arrow_size * 0.3 * dy), int({y2} - arrow_size * dy - arrow_size * 0.3 * dx)],")
                    lines.append(f"                [int({x2} - arrow_size * dx - arrow_size * 0.3 * dy), int({y2} - arrow_size * dy + arrow_size * 0.3 * dx)]")
                    lines.append(f"            ]], dtype=np.int32)")
                    lines.append(f"            cv2.fillPoly(frame, pts, self.colors['{color_name}'], cv2.LINE_AA)")
            
            elif shape.kind == 'curve':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                cx = int(c['cx']) - offset_x
                cy = int(c['cy']) - offset_y
                lines.append(f"        self.draw_bezier_curve(frame, {x1}, {y1}, {x2}, {y2}, {cx}, {cy}, self.colors['{color_name}'], {t}){comment}")
                    
            elif shape.kind == 'circle':
                c = shape.coords
                cx = int(c['cx']) - offset_x
                cy = int(c['cy']) - offset_y
                r = int(c['r'])
                lines.append(f"        cv2.circle(frame, ({cx}, {cy}), {r}, self.colors['{color_name}'], {thickness_param}, cv2.LINE_AA){comment}")
                
            elif shape.kind == 'ellipse':
                c = shape.coords
                cx = int(c['cx']) - offset_x
                cy = int(c['cy']) - offset_y
                rx = int(c['rx'])
                ry = int(c['ry'])
                angle = int(c.get('angle', 0))
                lines.append(f"        cv2.ellipse(frame, ({cx}, {cy}), ({rx}, {ry}), {angle}, 0, 360, self.colors['{color_name}'], {thickness_param}, cv2.LINE_AA){comment}")
                
            elif shape.kind == 'rectangle':
                c = shape.coords
                x1 = int(c['x1']) - offset_x
                y1 = int(c['y1']) - offset_y
                x2 = int(c['x2']) - offset_x
                y2 = int(c['y2']) - offset_y
                lines.append(f"        cv2.rectangle(frame, ({x1}, {y1}), ({x2}, {y2}), self.colors['{color_name}'], {thickness_param}, cv2.LINE_AA){comment}")
                
            elif shape.kind == 'polygon':
                c = shape.coords
                if 'points' in c:
                    pts = [(int(x) - offset_x, int(y) - offset_y) for x, y in c['points']]
                    pts_str = ', '.join([f"[{x}, {y}]" for x, y in pts])
                    lines.append(f"        pts = np.array([[{pts_str}]], dtype=np.int32)")
                    if filled:
                        lines.append(f"        cv2.fillPoly(frame, pts, self.colors['{color_name}'], cv2.LINE_AA){comment}")
                    else:
                        lines.append(f"        cv2.polylines(frame, pts, True, self.colors['{color_name}'], {t}, cv2.LINE_AA){comment}")
                        
            elif shape.kind == 'point':
                c = shape.coords
                x = int(c['x']) - offset_x
                y = int(c['y']) - offset_y
                point_size = max(3, t * 2)
                lines.append(f"        cv2.circle(frame, ({x}, {y}), {point_size}, self.colors['{color_name}'], -1, cv2.LINE_AA){comment}")
                
            elif shape.kind == 'text':
                c = shape.coords
                x = int(c['x']) - offset_x
                y = int(c['y']) - offset_y
                text = getattr(shape, 'text', '')
                font_scale = getattr(shape, 'font_scale', 1.0)
                lines.append(f"        cv2.putText(frame, '{text}', ({x}, {y}), cv2.FONT_HERSHEY_SIMPLEX, {font_scale}, self.colors['{color_name}'], {t}, cv2.LINE_AA){comment}")
        
        lines.append("        ")
        lines.append("        return frame")
        lines.append("")
        lines.append("")
        
        # Приклад використання
        lines.append("# Приклад використання:")
        lines.append("if __name__ == '__main__':")
        lines.append("    # Створюємо overlay")
        lines.append("    overlay = DrawingOverlay()")
        lines.append("    ")
        lines.append("    # Читаємо або створюємо кадр")
        lines.append("    frame = np.zeros((720, 1280, 3), dtype=np.uint8)  # Чорний кадр")
        lines.append("    # або завантажте з відео/камери:")
        lines.append("    # cap = cv2.VideoCapture(0)")
        lines.append("    # ret, frame = cap.read()")
        lines.append("    ")
        lines.append("    # Малюємо overlay")
        lines.append("    frame = overlay.draw(frame)")
        lines.append("    ")
        lines.append("    # Показуємо результат")
        lines.append("    cv2.imshow('Overlay', frame)")
        lines.append("    cv2.waitKey(0)")
        lines.append("    cv2.destroyAllWindows()")
        
        return "\n".join(lines)
    
    def _get_color_name(self, color_bgr, style, color_counter):
        if color_bgr in COLOR_MAP:
            base_name = COLOR_MAP[color_bgr]
        else:
            b, g, r = color_bgr
            base_name = f"color_{r}_{g}_{b}"
        
        if style != 'default':
            color_name = f"{base_name}_{style}"
        else:
            color_name = base_name
        
        if color_name in color_counter:
            color_counter[color_name] += 1
            color_name = f"{color_name}_{color_counter[color_name]}"
        else:
            color_counter[color_name] = 0
        
        return color_name
    
    # --- методи для зміни налаштувань ---
    
    def set_color(self, color_bgr):
        self.current_color_bgr = color_bgr
        self.update()
    
    def set_thickness(self, thickness):
        self.current_thickness = thickness
        self.update()
    
    def set_style(self, style):
        self.current_style = style
        self.update()
    
    def set_line_style(self, line_style):
        """Встановити стиль лінії (solid, dashed, dotted)"""
        self.current_line_style = line_style
        self.update()
    
    def set_filled(self, filled):
        """Встановити чи фігура заповнена"""
        self.current_filled = filled
        self.update()
    
    # --- сітка та інформація ---
    
    def _draw_grid(self, painter):
        rect = self.rect()
        screen_width = rect.width()
        screen_height = rect.height()
        
        world_x_min, world_y_min = self._screen_to_world(0, 0)
        world_x_max, world_y_max = self._screen_to_world(screen_width, screen_height)
        
        world_x_min = int(world_x_min // self.grid_step) * self.grid_step - self.grid_step
        world_y_min = int(world_y_min // self.grid_step) * self.grid_step - self.grid_step
        world_x_max = int(world_x_max // self.grid_step) * self.grid_step + self.grid_step
        world_y_max = int(world_y_max // self.grid_step) * self.grid_step + self.grid_step
        
        pen_thin = QtGui.QPen(QtGui.QColor(40, 40, 40))
        pen_thin.setWidth(1)
        
        pen_bold = QtGui.QPen(QtGui.QColor(60, 60, 60))
        pen_bold.setWidth(1)
        
        x = float(world_x_min)
        while x <= world_x_max:
            if int(x) % (self.grid_step * self.grid_bold_step) == 0:
                painter.setPen(pen_bold)
            else:
                painter.setPen(pen_thin)
            painter.drawLine(
                QtCore.QPointF(x, world_y_min),
                QtCore.QPointF(x, world_y_max)
            )
            x += self.grid_step
        
        y = float(world_y_min)
        while y <= world_y_max:
            if int(y) % (self.grid_step * self.grid_bold_step) == 0:
                painter.setPen(pen_bold)
            else:
                painter.setPen(pen_thin)
            painter.drawLine(
                QtCore.QPointF(world_x_min, y),
                QtCore.QPointF(world_x_max, y)
            )
            y += self.grid_step
    
    def _get_shape_info(self, x, y):
        if self.temp_point is None:
            if self.current_mode == 'polygon' and len(self.polygon_points) > 0:
                return f"Polygon: {len(self.polygon_points)} points (Right-click to finish)"
            return ""
        
        x0, y0 = self.temp_point
        
        if self.current_mode in ['line', 'arrow']:
            length = int(round(math.hypot(x - x0, y - y0)))
            return f"Length: {length} px"
        elif self.current_mode == 'circle':
            radius = int(round(math.hypot(x - x0, y - y0)))
            return f"Radius: {radius} px"
        elif self.current_mode == 'ellipse':
            rx = int(abs(x - x0))
            ry = int(abs(y - y0))
            return f"Ellipse: {rx}x{ry} px"
        elif self.current_mode == 'rectangle':
            width = int(abs(x - x0))
            height = int(abs(y - y0))
            return f"Rectangle: {width}x{height} px"
        
        return ""
    
    def _snap_to_grid(self, x, y):
        snapped_x = round(x / self.grid_step) * self.grid_step
        snapped_y = round(y / self.grid_step) * self.grid_step
        return int(snapped_x), int(snapped_y)
    
    def _constrain_line(self, x, y):
        if self.temp_point is None:
            return x, y
        
        x0, y0 = self.temp_point
        dx = abs(x - x0)
        dy = abs(y - y0)
        
        if dx > dy:
            return x, y0
        else:
            return x0, y
    
    def _draw_center_axes(self, painter):
        rect = self.rect()
        screen_center_x = rect.width() / 2
        screen_center_y = rect.height() / 2
        world_center_x, world_center_y = self._screen_to_world(screen_center_x, screen_center_y)
        
        world_x_min, world_y_min = self._screen_to_world(0, 0)
        world_x_max, world_y_max = self._screen_to_world(rect.width(), rect.height())
        
        pen = QtGui.QPen(QtGui.QColor(100, 100, 100))
        pen.setWidth(1)
        pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(pen)
        
        painter.drawLine(
            QtCore.QPointF(world_center_x, world_y_min),
            QtCore.QPointF(world_center_x, world_y_max)
        )
        
        painter.drawLine(
            QtCore.QPointF(world_x_min, world_center_y),
            QtCore.QPointF(world_x_max, world_center_y)
        )
    
    def set_snap_to_grid(self, enabled: bool):
        self.snap_to_grid = enabled
        self.update()
    
    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom_changed.emit(self.zoom_factor)
        self.update()
    
    # --- збереження/завантаження проекту ---
    
    def save_project(self, filename: str):
        """Зберегти проект у JSON файл"""
        project_data = {
            'version': '2.0',
            'shapes': []
        }
        
        for shape in self.shapes:
            shape_data = {
                'kind': shape.kind,
                'color_bgr': shape.color_bgr,
                'thickness': shape.thickness,
                'style': shape.style,
                'line_style': getattr(shape, 'line_style', 'solid'),
                'filled': getattr(shape, 'filled', False),
                'coords': dict(shape.coords)
            }
            
            # Додаткові параметри для тексту
            if shape.kind == 'text':
                shape_data['text'] = getattr(shape, 'text', '')
                shape_data['font_scale'] = getattr(shape, 'font_scale', 1.0)
            
            project_data['shapes'].append(shape_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
    
    def load_project(self, filename: str):
        """Завантажити проект з JSON файлу"""
        with open(filename, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        self.shapes.clear()
        self.selected_shapes.clear()
        
        for shape_data in project_data.get('shapes', []):
            shape = Shape(
                kind=shape_data['kind'],
                color_bgr=tuple(shape_data['color_bgr']),
                thickness=shape_data['thickness'],
                style=shape_data.get('style', 'default'),
                line_style=shape_data.get('line_style', 'solid'),
                filled=shape_data.get('filled', False),
                text=shape_data.get('text', ''),
                font_scale=shape_data.get('font_scale', 1.0),
                **shape_data['coords']
            )
            self.shapes.append(shape)
        
        self.update()

