"""
Обробка подій миші
"""
import math
from PyQt5 import QtWidgets, QtCore
from shape import Shape
from utils.geometry import is_point_near_line_middle, is_point_near_line_endpoint, snap_to_grid, constrain_line


class MouseHandler:
    """Клас для обробки подій миші"""
    
    def __init__(self, canvas_widget):
        self.canvas = canvas_widget
        self.temp_point = None  # Для малювання фігур
        self.polygon_points = []  # Для малювання полігонів
    
    def handle_press(self, event, current_mode, zoom_pan, selection_mgr, shape_mgr):
        """Обробити натискання миші"""
        screen_x, screen_y = event.x(), event.y()
        world_x, world_y = zoom_pan.screen_to_world(screen_x, screen_y)
        
        if event.button() == QtCore.Qt.LeftButton:
            return self._handle_left_press(
                screen_x, screen_y, world_x, world_y, 
                current_mode, zoom_pan, selection_mgr, shape_mgr
            )
        elif event.button() == QtCore.Qt.RightButton:
            return self._handle_right_press(current_mode)
        elif event.button() == QtCore.Qt.MidButton:
            zoom_pan.start_pan(screen_x, screen_y)
            return {'redraw': True}
        
        return {'redraw': False}
    
    def _handle_left_press(self, screen_x, screen_y, world_x, world_y, 
                          current_mode, zoom_pan, selection_mgr, shape_mgr):
        """Обробити ліву кнопку миші"""
        # Pan mode
        if current_mode == 'pan':
            zoom_pan.start_pan(screen_x, screen_y)
            return {'redraw': True}
        
        # Text mode - клік для додавання тексту
        if current_mode == 'text':
            x, y = world_x, world_y
            if self.canvas.snap_to_grid:
                x, y = snap_to_grid(x, y, self.canvas.grid_step)
            self._handle_text_click(x, y, shape_mgr)
            return {'redraw': True}
        
        # Point mode
        if current_mode == 'point':
            x, y = world_x, world_y
            if self.canvas.snap_to_grid:
                x, y = snap_to_grid(x, y, self.canvas.grid_step)
            self._handle_point_click(x, y, shape_mgr)
            return {'redraw': True}
        
        # Polygon mode
        if current_mode == 'polygon':
            x, y = world_x, world_y
            if self.canvas.snap_to_grid:
                x, y = snap_to_grid(x, y, self.canvas.grid_step)
            self._handle_polygon_click(x, y)
            return {'redraw': True}
        
        # Інші режими
        x, y = world_x, world_y
        
        if self.canvas.snap_to_grid and current_mode != 'select':
            x, y = snap_to_grid(x, y, self.canvas.grid_step)
        
        self.temp_point = (x, y)
        
        # Select mode
        if current_mode == 'select':
            return self._handle_select_press(x, y, selection_mgr, shape_mgr, zoom_pan)
        elif current_mode in ['line', 'circle', 'rectangle', 'arrow', 'ellipse']:
            # Починаємо малювання
            return {'redraw': True, 'drawing': True}
        
        return {'redraw': True}
    
    def _handle_select_press(self, x, y, selection_mgr, shape_mgr, zoom_pan):
        """Обробити клік в режимі select"""
        clicked_shape_idx = selection_mgr.find_shape_at_point(
            shape_mgr.shapes, x, y, zoom_pan.zoom_factor
        )
        
        if clicked_shape_idx is not None:
            shape = shape_mgr.shapes[clicked_shape_idx]
            
            # Перевірка на кінці лінії/стрілки (для перетворення в кубічну криву)
            if shape.kind in ['line', 'arrow']:
                c = shape.coords
                # Збільшений tolerance для легшого захоплення кінців
                tolerance = max(25, 10 * zoom_pan.zoom_factor)  # Адаптивний tolerance
                endpoint, point_coords = is_point_near_line_endpoint(
                    x, y, c['x1'], c['y1'], c['x2'], c['y2'], 
                    tolerance
                )
                if endpoint:
                    # Створюємо кубічну криву з редагуванням кінця
                    selection_mgr.start_cubic_curve_editing(clicked_shape_idx, x, y, endpoint, shape_mgr.shapes)
                    self.temp_point = None
                    return {'redraw': True}
                
                # Якщо не кінець, перевіряємо середину (для квадратичної кривої)
                is_middle, t = is_point_near_line_middle(
                    x, y, c['x1'], c['y1'], c['x2'], c['y2'], 
                    15 / zoom_pan.zoom_factor
                )
                if is_middle:
                    selection_mgr.start_curve_editing(clicked_shape_idx, x, y)
                    self.temp_point = None
                    return {'redraw': True}
            
            # Перевірка на контрольну точку кривої
            if shape.kind == 'curve':
                if selection_mgr.is_near_control_point(
                    shape_mgr.shapes, clicked_shape_idx, x, y, zoom_pan.zoom_factor
                ):
                    selection_mgr.start_control_point_dragging(clicked_shape_idx)
                    self.temp_point = None
                    return {'redraw': True}
            
            # Звичайне виділення
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            ctrl_pressed = modifiers & QtCore.Qt.ControlModifier
            
            if ctrl_pressed:
                selection_mgr.toggle_shape(clicked_shape_idx)
            else:
                if not selection_mgr.is_selected(clicked_shape_idx):
                    selection_mgr.clear_selection()
                    selection_mgr.select_shape(clicked_shape_idx)
            
            # Готуємося до переміщення
            if selection_mgr.is_selected(clicked_shape_idx):
                selection_mgr.start_dragging(shape_mgr.shapes, x, y)
            
            self.temp_point = None
            return {'redraw': True}
        
        # Клікнули на пусте місце
        return {'redraw': True}
    
    def _handle_right_press(self, current_mode):
        """Обробити праву кнопку миші"""
        # Для полігонів - завершуємо малювання
        if current_mode == 'polygon' and len(self.polygon_points) >= 3:
            self._finish_polygon()
            return {'redraw': True, 'change_mode': None}
        
        # Скасування або повернення до pan
        if current_mode != 'pan':
            return {'redraw': True, 'change_mode': 'pan'}
        
        # Вже в pan - просто очищаємо все
        self.temp_point = None
        return {'redraw': True, 'clear_all_temp': True}
    
    def handle_move(self, event, current_mode, zoom_pan, selection_mgr, shape_mgr):
        """Обробити рух миші"""
        screen_x, screen_y = event.x(), event.y()
        
        # Панування
        if zoom_pan.is_panning():
            zoom_pan.update_pan(screen_x, screen_y)
            return {'redraw': True, 'world_x': None, 'world_y': None}
        
        world_x, world_y = zoom_pan.screen_to_world(screen_x, screen_y)
        
        # Редагування кривої
        if selection_mgr.editing_curve or selection_mgr.dragging_control_point:
            selection_mgr.update_curve_editing(shape_mgr.shapes, world_x, world_y)
            return {'redraw': True, 'world_x': world_x, 'world_y': world_y}
        
        # Перетягування фігур
        if selection_mgr.is_dragging():
            selection_mgr.update_dragging(shape_mgr.shapes, world_x, world_y)
            return {'redraw': True, 'world_x': world_x, 'world_y': world_y}
        
        # Snap to grid
        if self.canvas.snap_to_grid and current_mode != 'select':
            world_x, world_y = snap_to_grid(world_x, world_y, self.canvas.grid_step)
        
        # Constrain для ліній (Shift)
        if self.temp_point is not None and current_mode == 'line':
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers & QtCore.Qt.ShiftModifier:
                world_x, world_y = constrain_line(world_x, world_y, self.temp_point[0], self.temp_point[1])
        
        return {'redraw': True, 'world_x': world_x, 'world_y': world_y}
    
    def handle_release(self, event, current_mode, zoom_pan, selection_mgr, shape_mgr):
        """Обробити відпускання миші"""
        if event.button() == QtCore.Qt.MidButton:
            zoom_pan.stop_pan()
            return {'redraw': True}
        
        if event.button() == QtCore.Qt.LeftButton:
            # Завершуємо панування
            if zoom_pan.is_panning():
                zoom_pan.stop_pan()
                return {'redraw': True}
            
            # Завершуємо редагування кривої
            if selection_mgr.editing_curve or selection_mgr.dragging_control_point:
                selection_mgr.stop_curve_editing()
                return {'redraw': True}
            
            # Завершуємо перетягування
            if selection_mgr.is_dragging():
                selection_mgr.stop_dragging()
                return {'redraw': True}
            
            # Завершуємо малювання фігури
            if self.temp_point is not None and current_mode in ['line', 'circle', 'rectangle', 'arrow', 'ellipse']:
                screen_x, screen_y = event.x(), event.y()
                world_x, world_y = zoom_pan.screen_to_world(screen_x, screen_y)
                
                if self.canvas.snap_to_grid:
                    world_x, world_y = snap_to_grid(world_x, world_y, self.canvas.grid_step)
                
                x0, y0 = self.temp_point
                x1, y1 = world_x, world_y
                
                # Мінімальна довжина
                if abs(x1 - x0) > 2 or abs(y1 - y0) > 2:
                    self._create_shape(current_mode, x0, y0, x1, y1, shape_mgr)
                    # Автозбереження після додавання фігури
                    if hasattr(self.canvas, 'autosave_manager'):
                        self.canvas.autosave_manager.autosave()
                
                self.temp_point = None
                return {'redraw': True, 'clear_shape_info': True}
            
            # Завершуємо вибір рамкою
            if current_mode == 'select' and self.temp_point is not None:
                screen_x, screen_y = event.x(), event.y()
                world_x, world_y = zoom_pan.screen_to_world(screen_x, screen_y)
                x1, y1 = self.temp_point
                x2, y2 = world_x, world_y
                
                if abs(x2 - x1) > 3 or abs(y2 - y1) > 3:
                    # Рамка виділення
                    shapes_in_rect = selection_mgr.find_shapes_in_rect(
                        shape_mgr.shapes,
                        min(x1, x2), min(y1, y2),
                        max(x1, x2), max(y1, y2)
                    )
                    
                    modifiers = QtWidgets.QApplication.keyboardModifiers()
                    ctrl_pressed = modifiers & QtCore.Qt.ControlModifier
                    
                    if ctrl_pressed:
                        for idx in shapes_in_rect:
                            selection_mgr.select_shape(idx)
                    else:
                        selection_mgr.clear_selection()
                        for idx in shapes_in_rect:
                            selection_mgr.select_shape(idx)
                else:
                    # Просто клік - скидаємо виділення
                    modifiers = QtWidgets.QApplication.keyboardModifiers()
                    ctrl_pressed = modifiers & QtCore.Qt.ControlModifier
                    if not ctrl_pressed:
                        selection_mgr.clear_selection()
                
                self.temp_point = None
                return {'redraw': True}
        
        return {'redraw': False}
    
    def handle_wheel(self, event, zoom_pan):
        """Обробити колесо миші (зум)"""
        screen_x = event.x()
        screen_y = event.y()
        world_x, world_y = zoom_pan.screen_to_world(screen_x, screen_y)
        
        delta = event.angleDelta().y()
        new_zoom = zoom_pan.handle_wheel(delta, world_x, world_y)
        
        return {'redraw': True, 'zoom': new_zoom}
    
    def _handle_text_click(self, x, y, shape_mgr):
        """Додати текст"""
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self.canvas, "Add Text", "Enter text:")
        
        if ok and text:
            shape_mgr.add_shape(
                Shape(
                    'text',
                    color_bgr=self.canvas.current_color_bgr,
                    thickness=self.canvas.current_thickness,
                    style=self.canvas.current_style,
                    text=text,
                    font_scale=self.canvas.current_font_scale,
                    dash_length=self.canvas.current_dash_length,
                    dot_length=self.canvas.current_dot_length,
                    x=int(x), y=int(y),
                )
            )
            # Автозбереження після додавання фігури
            if hasattr(self.canvas, 'autosave_manager'):
                self.canvas.autosave_manager.autosave()
    
    def _handle_point_click(self, x, y, shape_mgr):
        """Додати точку"""
        shape_mgr.add_shape(
            Shape(
                'point',
                color_bgr=self.canvas.current_color_bgr,
                thickness=self.canvas.current_thickness,
                style=self.canvas.current_style,
                dash_length=self.canvas.current_dash_length,
                dot_length=self.canvas.current_dot_length,
                x=int(x), y=int(y),
            )
        )
        # Автозбереження після додавання фігури
        if hasattr(self.canvas, 'autosave_manager'):
            self.canvas.autosave_manager.autosave()
    
    def _handle_polygon_click(self, x, y):
        """Додати точку до полігону"""
        self.polygon_points.append((int(x), int(y)))
    
    def _finish_polygon(self):
        """Завершити малювання полігону"""
        if len(self.polygon_points) >= 3:
            shape_mgr = self.canvas.shape_manager
            shape_mgr.add_shape(
                Shape(
                    'polygon',
                    color_bgr=self.canvas.current_color_bgr,
                    thickness=self.canvas.current_thickness,
                    style=self.canvas.current_style,
                    line_style=self.canvas.current_line_style,
                    filled=self.canvas.current_filled,
                    dash_length=self.canvas.current_dash_length,
                    dot_length=self.canvas.current_dot_length,
                    points=list(self.polygon_points),
                )
            )
            self.polygon_points = []
            # Автозбереження після додавання фігури
            if hasattr(self.canvas, 'autosave_manager'):
                self.canvas.autosave_manager.autosave()
    
    def _create_shape(self, mode, x0, y0, x1, y1, shape_mgr):
        """Створити фігуру після завершення малювання"""
        if mode == 'line':
            shape_mgr.add_shape(
                Shape(
                    'line',
                    color_bgr=self.canvas.current_color_bgr,
                    thickness=self.canvas.current_thickness,
                    style=self.canvas.current_style,
                    line_style=self.canvas.current_line_style,
                    dash_length=self.canvas.current_dash_length,
                    dot_length=self.canvas.current_dot_length,
                    x1=int(x0), y1=int(y0),
                    x2=int(x1), y2=int(y1),
                )
            )
        elif mode == 'circle':
            dx = x1 - x0
            dy = y1 - y0
            r = int(round(math.hypot(dx, dy)))
            if r > 2:
                shape_mgr.add_shape(
                    Shape(
                        'circle',
                        color_bgr=self.canvas.current_color_bgr,
                        thickness=self.canvas.current_thickness,
                        style=self.canvas.current_style,
                        line_style=self.canvas.current_line_style,
                        filled=self.canvas.current_filled,
                        dash_length=self.canvas.current_dash_length,
                        dot_length=self.canvas.current_dot_length,
                        cx=int(x0), cy=int(y0), r=r,
                    )
                )
        elif mode == 'rectangle':
            shape_mgr.add_shape(
                Shape(
                    'rectangle',
                    color_bgr=self.canvas.current_color_bgr,
                    thickness=self.canvas.current_thickness,
                    style=self.canvas.current_style,
                    line_style=self.canvas.current_line_style,
                    filled=self.canvas.current_filled,
                    dash_length=self.canvas.current_dash_length,
                    dot_length=self.canvas.current_dot_length,
                    x1=int(x0), y1=int(y0),
                    x2=int(x1), y2=int(y1),
                )
            )
        elif mode == 'arrow':
            shape_mgr.add_shape(
                Shape(
                    'arrow',
                    color_bgr=self.canvas.current_color_bgr,
                    thickness=self.canvas.current_thickness,
                    style=self.canvas.current_style,
                    line_style=self.canvas.current_line_style,
                    dash_length=self.canvas.current_dash_length,
                    dot_length=self.canvas.current_dot_length,
                    x1=int(x0), y1=int(y0),
                    x2=int(x1), y2=int(y1),
                )
            )
        elif mode == 'ellipse':
            rx = int(abs(x1 - x0))
            ry = int(abs(y1 - y0))
            if rx > 2 and ry > 2:
                shape_mgr.add_shape(
                    Shape(
                        'ellipse',
                        color_bgr=self.canvas.current_color_bgr,
                        thickness=self.canvas.current_thickness,
                        style=self.canvas.current_style,
                        line_style=self.canvas.current_line_style,
                        filled=self.canvas.current_filled,
                        dash_length=self.canvas.current_dash_length,
                        dot_length=self.canvas.current_dot_length,
                        cx=int(x0), cy=int(y0), rx=rx, ry=ry, angle=0,
                    )
                )
    
    def get_shape_info(self, world_x, world_y):
        """Отримати інформацію про фігуру що малюється"""
        if self.temp_point is None:
            if len(self.polygon_points) > 0:
                return f"Polygon: {len(self.polygon_points)} points (Right-click to finish)"
            return ""
        
        x0, y0 = self.temp_point
        mode = self.canvas.current_mode
        
        if mode in ['line', 'arrow']:
            length = int(round(math.hypot(world_x - x0, world_y - y0)))
            return f"Length: {length} px"
        elif mode == 'circle':
            radius = int(round(math.hypot(world_x - x0, world_y - y0)))
            return f"Radius: {radius} px"
        elif mode == 'ellipse':
            rx = int(abs(world_x - x0))
            ry = int(abs(world_y - y0))
            return f"Ellipse: {rx}x{ry} px"
        elif mode == 'rectangle':
            width = int(abs(world_x - x0))
            height = int(abs(world_y - y0))
            return f"Rectangle: {width}x{height} px"
        
        return ""

