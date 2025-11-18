"""
Віджет для малювання фігур - тонкий клей між модулями
"""
import math
from PyQt5 import QtWidgets, QtGui, QtCore

# Імпортуємо всі наші модулі
from core.shape_manager import ShapeManager
from core.selection_manager import SelectionManager
from core.group_manager import GroupManager
from tools.zoom_pan_manager import ZoomPanManager
from tools.mouse_handler import MouseHandler
from rendering.shape_renderer import ShapeRenderer
from rendering.grid_renderer import GridRenderer
from export.code_generator import CodeGenerator
from export.project_io import ProjectIO
from utils.autosave import AutoSaveManager


class CanvasWidget(QtWidgets.QWidget):
    """Основний віджет canvas - координує роботу всіх модулів"""
    
    mode_changed = QtCore.pyqtSignal(str)
    mouse_moved = QtCore.pyqtSignal(int, int)
    shape_info_changed = QtCore.pyqtSignal(str)
    zoom_changed = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        
        # Ініціалізуємо менеджери
        self.shape_manager = ShapeManager()
        self.selection_manager = SelectionManager()
        self.group_manager = GroupManager()
        self.zoom_pan_manager = ZoomPanManager()
        self.mouse_handler = MouseHandler(self)
        self.shape_renderer = ShapeRenderer()
        self.grid_renderer = GridRenderer()
        self.autosave_manager = AutoSaveManager(self)
        
        # Поточний режим
        self.current_mode = 'pan'
        
        # Поточні налаштування малювання
        self.current_color_bgr = (0, 255, 0)
        self.current_thickness = 2
        self.current_style = 'default'
        self.current_font_scale = 1.0
        self.current_line_style = 'solid'
        self.current_filled = False
        self.current_dash_length = 10
        self.current_dot_length = 5
        
        # Інше
        self.snap_to_grid = False
        self.grid_step = 20
        self.mouse_pos = None
    
    # --- Методи режимів малювання ---

    def set_mode_pan(self):
        """Режим панування"""
        self.current_mode = 'pan'
        self._clear_temp_state()
        self.mode_changed.emit('pan')
        self.update()

    def set_mode_select(self):
        """Режим виділення"""
        self.current_mode = 'select'
        self._clear_temp_state()
        self.mode_changed.emit('select')
        self.update()

    def set_mode_line(self):
        """Режим малювання ліній"""
        self.current_mode = 'line'
        self._clear_temp_state()
        self.mode_changed.emit('line')
        self.update()

    def set_mode_circle(self):
        """Режим малювання кіл"""
        self.current_mode = 'circle'
        self._clear_temp_state()
        self.mode_changed.emit('circle')
        self.update()

    def set_mode_text(self):
        """Режим додавання тексту"""
        self.current_mode = 'text'
        self._clear_temp_state()
        self.mode_changed.emit('text')
        self.update()
    
    def set_mode_point(self):
        """Режим додавання точок"""
        self.current_mode = 'point'
        self._clear_temp_state()
        self.mode_changed.emit('point')
        self.update()
    
    def set_mode_rectangle(self):
        """Режим малювання прямокутників"""
        self.current_mode = 'rectangle'
        self._clear_temp_state()
        self.mode_changed.emit('rectangle')
        self.update()
    
    def set_mode_arrow(self):
        """Режим малювання стрілок"""
        self.current_mode = 'arrow'
        self._clear_temp_state()
        self.mode_changed.emit('arrow')
        self.update()
    
    def set_mode_polygon(self):
        """Режим малювання полігонів"""
        self.current_mode = 'polygon'
        self._clear_temp_state()
        self.mode_changed.emit('polygon')
        self.update()
    
    def set_mode_ellipse(self):
        """Режим малювання еліпсів"""
        self.current_mode = 'ellipse'
        self._clear_temp_state()
        self.mode_changed.emit('ellipse')
        self.update()

    def _clear_temp_state(self):
        """Очистити тимчасовий стан"""
        self.mouse_handler.temp_point = None
        self.mouse_handler.polygon_points = []
        self.selection_manager.stop_dragging()
        self.selection_manager.stop_curve_editing()
        self.shape_info_changed.emit("")
    
    # --- Обробка подій миші ---

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """Обробка натискання миші"""
        if self.parent():
            self.parent().setFocus()
        
        result = self.mouse_handler.handle_press(
            event, self.current_mode, 
            self.zoom_pan_manager, 
            self.selection_manager,
            self.shape_manager
        )
        
        if result.get('redraw'):
                                self.update()
        if result.get('change_mode'):
                self.set_mode_pan()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """Обробка руху миші"""
        result = self.mouse_handler.handle_move(
            event, self.current_mode,
            self.zoom_pan_manager,
            self.selection_manager,
            self.shape_manager
        )
        
        world_x = result.get('world_x')
        world_y = result.get('world_y')
        
        if world_x is not None and world_y is not None:
            self.mouse_pos = (world_x, world_y)
            self.mouse_moved.emit(int(world_x), int(world_y))
            
            # Інфо про фігуру
            info = self.mouse_handler.get_shape_info(world_x, world_y)
            self.shape_info_changed.emit(info)
        
        if result.get('redraw'):
            self.update()
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """Обробка відпускання миші"""
        result = self.mouse_handler.handle_release(
            event, self.current_mode,
            self.zoom_pan_manager,
            self.selection_manager,
            self.shape_manager
        )
        
        if result.get('clear_shape_info'):
                self.shape_info_changed.emit("")
        
        if result.get('redraw'):
                self.update()
    
    def wheelEvent(self, event: QtGui.QWheelEvent):
        """Обробка колеса миші (зум)"""
        result = self.mouse_handler.handle_wheel(event, self.zoom_pan_manager)
        
        if result.get('zoom') is not None:
            self.zoom_changed.emit(result['zoom'])
        
        if result.get('redraw'):
            self.update()

    # --- Малювання (paintEvent) ---

    def paintEvent(self, event):
        """Малювання всього canvas"""
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0))

        # Застосовуємо трансформацію (zoom + pan)
        transform = QtGui.QTransform()
        transform.translate(self.zoom_pan_manager.pan_x, self.zoom_pan_manager.pan_y)
        transform.scale(self.zoom_pan_manager.zoom_factor, self.zoom_pan_manager.zoom_factor)
        painter.setTransform(transform)

        # Малюємо сітку та осі
        self.grid_renderer.draw_grid(painter, self.rect(), self.zoom_pan_manager)
        self.grid_renderer.draw_center_axes(painter, self.rect(), self.zoom_pan_manager)

        # Малюємо фігури
        self.shape_renderer.draw_shapes(
            painter, 
            self.shape_manager.shapes, 
            self.selection_manager.selected_shapes,
            self.zoom_pan_manager.zoom_factor,
            self.selection_manager.show_control_points
        )
        
        # Малюємо рамку виділення
        if self.current_mode == 'select':
            self.shape_renderer.draw_selection_rect(
                painter, 
                self.mouse_handler.temp_point,
                self.mouse_pos
            )
        
        # Прев'ю незавершеної фігури
        if self.current_mode in ['line', 'circle', 'rectangle', 'arrow', 'ellipse']:
            self.shape_renderer.draw_shape_preview(
                painter,
                self.current_mode,
                self.mouse_handler.temp_point,
                self.mouse_pos,
                self.current_color_bgr,
                self.current_thickness,
                self.current_filled,
                self.zoom_pan_manager.zoom_factor
            )
        
        # Прев'ю полігону
        if self.current_mode == 'polygon':
            self.shape_renderer.draw_polygon_preview(
                painter,
                self.mouse_handler.polygon_points,
                self.mouse_pos,
                self.current_color_bgr,
                self.current_thickness,
                self.zoom_pan_manager.zoom_factor
            )
    
    # --- Методи для зміни налаштувань ---
    
    def set_color(self, color_bgr):
        """Встановити колір"""
        self.current_color_bgr = color_bgr
        self.update()
    
    def set_thickness(self, thickness):
        """Встановити товщину"""
        self.current_thickness = thickness
        self.update()
    
    def set_style(self, style):
        """Встановити стиль"""
        self.current_style = style
        self.update()
    
    def set_line_style(self, line_style):
        """Встановити стиль лінії"""
        self.current_line_style = line_style
        self.update()
    
    def set_filled(self, filled):
        """Встановити заповнення"""
        self.current_filled = filled
        self.update()
    
    def set_font_scale(self, font_scale):
        """Встановити розмір шрифту"""
        self.current_font_scale = font_scale
        self.update()
    
    def set_dash_length(self, dash_length):
        """Встановити довжину пунктира"""
        self.current_dash_length = dash_length
        self.update()
    
    def set_dot_length(self, dot_length):
        """Встановити відстань між точками"""
        self.current_dot_length = dot_length
        self.update()
    
    def set_snap_to_grid(self, enabled: bool):
        """Встановити прив'язку до сітки"""
        self.snap_to_grid = enabled
        self.update()
    
    # --- Редагування фігур ---
    
    def undo(self):
        """Скасувати останню дію"""
        self.shape_manager.undo()
        self.autosave_manager.autosave()  # Зберігаємо після зміни
        self.update()
    
    def clear_all(self):
        """Очистити всі фігури"""
        self.shape_manager.clear_all()
        self.selection_manager.clear_selection()
        self.autosave_manager.autosave()  # Зберігаємо після зміни
        self.update()
    
    def copy_selected(self):
        """Копіювати вибрані фігури"""
        self.shape_manager.copy_shapes(self.selection_manager.selected_shapes)
    
    def paste(self):
        """Вставити фігури"""
        new_indices = self.shape_manager.paste_shapes()
        if new_indices:
            self.selection_manager.selected_shapes = set(new_indices)
            self.update()
    
    def flip_horizontal(self):
        """Відзеркалити по горизонталі"""
        new_indices = self.shape_manager.flip_shapes_horizontal(
            self.selection_manager.selected_shapes
        )
        if new_indices:
            self.selection_manager.selected_shapes = set(new_indices)
            self.update()
    
    def flip_vertical(self):
        """Відзеркалити по вертикалі"""
        new_indices = self.shape_manager.flip_shapes_vertical(
            self.selection_manager.selected_shapes
        )
        if new_indices:
            self.selection_manager.selected_shapes = set(new_indices)
        self.update()
    
    # --- Zoom та Pan ---
    
    def reset_zoom(self):
        """Скинути zoom та pan"""
        self.zoom_pan_manager.reset()
        self.zoom_changed.emit(self.zoom_pan_manager.zoom_factor)
        self.update()
    
    # --- Експорт та збереження ---
    
    def generate_opencv_code(self, origin_mode='editor', canvas_width=None, canvas_height=None):
        """Генерувати OpenCV код"""
        # Передаємо групи якщо вони є
        groups = self.group_manager.groups if len(self.group_manager.groups) > 0 else None
        return CodeGenerator.generate_opencv_code(
            self.shape_manager.shapes,
            origin_mode,
            canvas_width,
            canvas_height,
            groups
        )
    
    def save_project(self, filename: str):
        """Зберегти проект"""
        ProjectIO.save_project(self.shape_manager.shapes, filename, self.group_manager)
    
    def load_project(self, filename: str):
        """Завантажити проект"""
        shapes, groups_data = ProjectIO.load_project(filename)
        self.shape_manager.shapes = shapes
        self.selection_manager.clear_selection()
        
        # Завантажуємо групи
        if groups_data:
            self.group_manager.from_dict(groups_data)
        else:
            self.group_manager.clear_all()
        
        self.update()
    
    # --- Властивості для сумісності ---
    
    @property
    def shapes(self):
        """Доступ до списку фігур (для сумісності з main_window)"""
        return self.shape_manager.shapes
    
    @property
    def selected_shapes(self):
        """Доступ до вибраних фігур (для сумісності)"""
        return self.selection_manager.selected_shapes
