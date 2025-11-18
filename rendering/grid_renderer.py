"""
Рендер сітки та центральних осей
"""
from PyQt5 import QtGui, QtCore


class GridRenderer:
    """Клас для малювання сітки та центральних осей"""
    
    def __init__(self, grid_step=20, grid_bold_step=5):
        self.grid_step = grid_step
        self.grid_bold_step = grid_bold_step
    
    def draw_grid(self, painter, rect, zoom_pan_manager):
        """Намалювати сітку"""
        screen_width = rect.width()
        screen_height = rect.height()
        
        world_x_min, world_y_min = zoom_pan_manager.screen_to_world(0, 0)
        world_x_max, world_y_max = zoom_pan_manager.screen_to_world(screen_width, screen_height)
        
        world_x_min = int(world_x_min // self.grid_step) * self.grid_step - self.grid_step
        world_y_min = int(world_y_min // self.grid_step) * self.grid_step - self.grid_step
        world_x_max = int(world_x_max // self.grid_step) * self.grid_step + self.grid_step
        world_y_max = int(world_y_max // self.grid_step) * self.grid_step + self.grid_step
        
        pen_thin = QtGui.QPen(QtGui.QColor(40, 40, 40))
        pen_thin.setWidth(1)
        
        pen_bold = QtGui.QPen(QtGui.QColor(60, 60, 60))
        pen_bold.setWidth(1)
        
        # Вертикальні лінії
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
        
        # Горизонтальні лінії
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
    
    def draw_center_axes(self, painter, rect, zoom_pan_manager):
        """Намалювати центральні осі (координати 0,0)"""
        screen_center_x = rect.width() / 2
        screen_center_y = rect.height() / 2
        world_center_x, world_center_y = zoom_pan_manager.screen_to_world(screen_center_x, screen_center_y)
        
        world_x_min, world_y_min = zoom_pan_manager.screen_to_world(0, 0)
        world_x_max, world_y_max = zoom_pan_manager.screen_to_world(rect.width(), rect.height())
        
        pen = QtGui.QPen(QtGui.QColor(100, 100, 100))
        pen.setWidth(1)
        pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(pen)
        
        # Вертикальна вісь (X = center)
        painter.drawLine(
            QtCore.QPointF(world_center_x, world_y_min),
            QtCore.QPointF(world_center_x, world_y_max)
        )
        
        # Горизонтальна вісь (Y = center)
        painter.drawLine(
            QtCore.QPointF(world_x_min, world_center_y),
            QtCore.QPointF(world_x_max, world_center_y)
        )

