"""
Рендер сітки та центральних осей
"""
from PyQt5 import QtGui, QtCore


class GridRenderer:
    """Клас для малювання сітки та центральних осей"""
    
    def __init__(self, grid_step=5, grid_bold_step=20):
        self.grid_step = grid_step
        self.grid_bold_step = grid_bold_step  # Кожна 20-та лінія жирна (кожні 100px при grid_step=5)
    
    def draw_grid(self, painter, rect, zoom_pan_manager, canvas_limits=None):
        """Намалювати сітку
        
        Args:
            painter: QPainter для малювання
            rect: прямокутник екрану
            zoom_pan_manager: менеджер зуму та панування
            canvas_limits: dict з налаштуваннями меж полотна (опціонально)
        """
        screen_width = rect.width()
        screen_height = rect.height()
        
        world_x_min, world_y_min = zoom_pan_manager.screen_to_world(0, 0)
        world_x_max, world_y_max = zoom_pan_manager.screen_to_world(screen_width, screen_height)
        
        pen_thin = QtGui.QPen(QtGui.QColor(40, 40, 40))
        pen_thin.setWidth(1)
        
        pen_bold = QtGui.QPen(QtGui.QColor(60, 60, 60))
        pen_bold.setWidth(1)
        
        # Якщо є обмеження полотна - малюємо сітку вирівняну по центру полотна
        if canvas_limits and canvas_limits.get('enabled'):
            canvas_width = canvas_limits['width']
            canvas_height = canvas_limits['height']
            
            # Центр полотна
            center_x = canvas_width / 2.0
            center_y = canvas_height / 2.0
            
            # Малюємо вертикальні лінії від центру в обидві сторони
            # Спочатку центральна лінія
            x = center_x
            while x >= world_x_min:
                distance_from_center = abs(x - center_x)
                if int(distance_from_center) % (self.grid_step * self.grid_bold_step) == 0:
                    painter.setPen(pen_bold)
                else:
                    painter.setPen(pen_thin)
                painter.drawLine(
                    QtCore.QPointF(x, world_y_min),
                    QtCore.QPointF(x, world_y_max)
                )
                x -= self.grid_step
            
            # Праворуч від центру
            x = center_x + self.grid_step
            while x <= world_x_max:
                distance_from_center = abs(x - center_x)
                if int(distance_from_center) % (self.grid_step * self.grid_bold_step) == 0:
                    painter.setPen(pen_bold)
                else:
                    painter.setPen(pen_thin)
                painter.drawLine(
                    QtCore.QPointF(x, world_y_min),
                    QtCore.QPointF(x, world_y_max)
                )
                x += self.grid_step
            
            # Малюємо горизонтальні лінії від центру в обидві сторони
            # Спочатку центральна лінія
            y = center_y
            while y >= world_y_min:
                distance_from_center = abs(y - center_y)
                if int(distance_from_center) % (self.grid_step * self.grid_bold_step) == 0:
                    painter.setPen(pen_bold)
                else:
                    painter.setPen(pen_thin)
                painter.drawLine(
                    QtCore.QPointF(world_x_min, y),
                    QtCore.QPointF(world_x_max, y)
                )
                y -= self.grid_step
            
            # Вниз від центру
            y = center_y + self.grid_step
            while y <= world_y_max:
                distance_from_center = abs(y - center_y)
                if int(distance_from_center) % (self.grid_step * self.grid_bold_step) == 0:
                    painter.setPen(pen_bold)
                else:
                    painter.setPen(pen_thin)
                painter.drawLine(
                    QtCore.QPointF(world_x_min, y),
                    QtCore.QPointF(world_x_max, y)
                )
                y += self.grid_step
            
        else:
            # Стандартна сітка без вирівнювання
            world_x_min_grid = int(world_x_min // self.grid_step) * self.grid_step - self.grid_step
            world_y_min_grid = int(world_y_min // self.grid_step) * self.grid_step - self.grid_step
            world_x_max_grid = int(world_x_max // self.grid_step) * self.grid_step + self.grid_step
            world_y_max_grid = int(world_y_max // self.grid_step) * self.grid_step + self.grid_step
            
            # Вертикальні лінії
            x = float(world_x_min_grid)
            while x <= world_x_max_grid:
                if int(x) % (self.grid_step * self.grid_bold_step) == 0:
                    painter.setPen(pen_bold)
                else:
                    painter.setPen(pen_thin)
                painter.drawLine(
                    QtCore.QPointF(x, world_y_min),
                    QtCore.QPointF(x, world_y_max)
                )
                x += self.grid_step
            
            # Горизонтальні лінії
            y = float(world_y_min_grid)
            while y <= world_y_max_grid:
                if int(y) % (self.grid_step * self.grid_bold_step) == 0:
                    painter.setPen(pen_bold)
                else:
                    painter.setPen(pen_thin)
                painter.drawLine(
                    QtCore.QPointF(world_x_min, y),
                    QtCore.QPointF(world_x_max, y)
                )
                y += self.grid_step
    
    def draw_center_axes(self, painter, rect, zoom_pan_manager, canvas_limits=None):
        """Намалювати центральні осі
        
        Якщо є межі полотна - малює осі через центр полотна,
        інакше - через центр екрану (0,0)
        """
        world_x_min, world_y_min = zoom_pan_manager.screen_to_world(0, 0)
        world_x_max, world_y_max = zoom_pan_manager.screen_to_world(rect.width(), rect.height())
        
        pen = QtGui.QPen(QtGui.QColor(100, 100, 100))
        pen.setWidth(1)
        pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(pen)
        
        # Якщо є обмеження полотна - малюємо осі через центр полотна
        if canvas_limits and canvas_limits.get('enabled'):
            canvas_width = canvas_limits['width']
            canvas_height = canvas_limits['height']
            
            center_x = canvas_width / 2.0
            center_y = canvas_height / 2.0
        else:
            # Інакше через центр екрану
            screen_center_x = rect.width() / 2
            screen_center_y = rect.height() / 2
            center_x, center_y = zoom_pan_manager.screen_to_world(screen_center_x, screen_center_y)
        
        # Вертикальна вісь (X = center)
        painter.drawLine(
            QtCore.QPointF(center_x, world_y_min),
            QtCore.QPointF(center_x, world_y_max)
        )
        
        # Горизонтальна вісь (Y = center)
        painter.drawLine(
            QtCore.QPointF(world_x_min, center_y),
            QtCore.QPointF(world_x_max, center_y)
        )
        
        # Малюємо маркер центру полотна (якщо є обмеження)
        if canvas_limits and canvas_limits.get('enabled'):
            pen_center = QtGui.QPen(QtGui.QColor(150, 150, 150))
            pen_center.setWidth(2)
            painter.setPen(pen_center)
            
            # Малюємо хрестик в центрі
            cross_size = 10
            painter.drawLine(
                QtCore.QPointF(center_x - cross_size, center_y),
                QtCore.QPointF(center_x + cross_size, center_y)
            )
            painter.drawLine(
                QtCore.QPointF(center_x, center_y - cross_size),
                QtCore.QPointF(center_x, center_y + cross_size)
            )
    
    def draw_canvas_limits(self, painter, width, height):
        """Намалювати межі полотна (якщо увімкнено обмеження)"""
        # Малюємо прямокутник від (0, 0) до (width, height)
        pen = QtGui.QPen(QtGui.QColor(255, 100, 0))  # Помаранчевий колір
        pen.setWidth(2)
        pen.setStyle(QtCore.Qt.SolidLine)
        painter.setPen(pen)
        
        # Малюємо рамку
        painter.drawRect(QtCore.QRectF(0, 0, width, height))
        
        # Додаємо напівпрозорий фон з текстом в кутах
        font = QtGui.QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(255, 150, 0))
        
        # Текст в верхньому лівому куті
        painter.drawText(QtCore.QPointF(5, 15), f"Canvas: {width}x{height}")
        
        # Текст в верхньому правому куті
        painter.drawText(QtCore.QPointF(width - 80, 15), f"({width}, 0)")
        
        # Текст в нижньому лівому куті
        painter.drawText(QtCore.QPointF(5, height - 5), f"(0, {height})")

