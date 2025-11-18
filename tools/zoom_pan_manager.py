"""
Менеджер для керування zoom та pan (переміщення полотна)
"""
from PyQt5 import QtCore


class ZoomPanManager:
    """Клас для управління зумом та панування"""
    
    def __init__(self):
        # Zoom параметри
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.1
        
        # Pan параметри
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_start = None  # Початкова позиція при панування (screen coords)
    
    def screen_to_world(self, screen_x, screen_y):
        """Конвертувати screen координати в world координати"""
        world_x = (screen_x - self.pan_x) / self.zoom_factor
        world_y = (screen_y - self.pan_y) / self.zoom_factor
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y):
        """Конвертувати world координати в screen координати"""
        screen_x = world_x * self.zoom_factor + self.pan_x
        screen_y = world_y * self.zoom_factor + self.pan_y
        return screen_x, screen_y
    
    def start_pan(self, screen_x, screen_y):
        """Почати панування"""
        self.pan_start = (screen_x, screen_y)
    
    def update_pan(self, screen_x, screen_y):
        """Оновити pan позицію при переміщенні миші"""
        if self.pan_start is None:
            return False
        
        dx = screen_x - self.pan_start[0]
        dy = screen_y - self.pan_start[1]
        self.pan_x += dx
        self.pan_y += dy
        self.pan_start = (screen_x, screen_y)
        return True
    
    def stop_pan(self):
        """Закінчити панування"""
        self.pan_start = None
    
    def is_panning(self):
        """Чи відбувається панування зараз"""
        return self.pan_start is not None
    
    def zoom_in(self, mouse_world_x, mouse_world_y):
        """Збільшити зум"""
        new_zoom = min(self.zoom_factor + self.zoom_step, self.max_zoom)
        self._apply_zoom(new_zoom, mouse_world_x, mouse_world_y)
        return self.zoom_factor
    
    def zoom_out(self, mouse_world_x, mouse_world_y):
        """Зменшити зум"""
        new_zoom = max(self.zoom_factor - self.zoom_step, self.min_zoom)
        self._apply_zoom(new_zoom, mouse_world_x, mouse_world_y)
        return self.zoom_factor
    
    def handle_wheel(self, delta, mouse_world_x, mouse_world_y):
        """Обробити колесо миші для зуму"""
        if delta > 0:
            return self.zoom_in(mouse_world_x, mouse_world_y)
        else:
            return self.zoom_out(mouse_world_x, mouse_world_y)
    
    def _apply_zoom(self, new_zoom, mouse_world_x, mouse_world_y):
        """Застосувати новий зум зі збереженням позиції курсору"""
        if new_zoom != self.zoom_factor:
            zoom_ratio = new_zoom / self.zoom_factor
            # Зберігаємо позицію курсору при зумі
            self.pan_x = mouse_world_x - (mouse_world_x - self.pan_x) * zoom_ratio
            self.pan_y = mouse_world_y - (mouse_world_y - self.pan_y) * zoom_ratio
            self.zoom_factor = new_zoom
    
    def reset(self):
        """Скинути zoom та pan до дефолтних значень"""
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_start = None

