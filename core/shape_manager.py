"""
Менеджер для управління фігурами (додавання, видалення, копіювання)
"""
import math
from shape import Shape


class ShapeManager:
    """Клас для управління колекцією фігур"""
    
    def __init__(self):
        self.shapes = []
        self.clipboard = []  # Буфер обміну
    
    def add_shape(self, shape):
        """Додати фігуру"""
        self.shapes.append(shape)
    
    def remove_shape(self, idx):
        """Видалити фігуру за індексом"""
        if 0 <= idx < len(self.shapes):
            del self.shapes[idx]
    
    def undo(self):
        """Скасувати останню дію (видалити останню фігуру)"""
        if self.shapes:
            self.shapes.pop()
    
    def clear_all(self):
        """Очистити всі фігури"""
        self.shapes.clear()
    
    def copy_shapes(self, indices):
        """Копіювати фігури за індексами в буфер обміну"""
        self.clipboard = [self.shapes[idx] for idx in sorted(indices) if 0 <= idx < len(self.shapes)]
    
    def paste_shapes(self, offset_x=30, offset_y=30):
        """Вставити фігури з буфера обміну зі зсувом"""
        if not self.clipboard:
            return []
        
        new_shapes_indices = []
        
        for shape in self.clipboard:
            new_shape = self._create_shape_copy(shape, offset_x, offset_y)
            self.shapes.append(new_shape)
            new_shapes_indices.append(len(self.shapes) - 1)
        
        return new_shapes_indices
    
    def flip_shapes_horizontal(self, selected_indices, gap=20):
        """Створити відзеркалені копії фігур по горизонталі"""
        from utils.geometry import get_selection_bbox
        
        if not selected_indices:
            return []
        
        bbox = get_selection_bbox(self.shapes, selected_indices)
        if bbox is None:
            return []
        
        min_x, min_y, max_x, max_y = bbox
        mirror_axis = max_x + gap
        
        new_shapes_indices = []
        
        for idx in sorted(selected_indices):
            shape = self.shapes[idx]
            new_shape = self._create_flipped_shape_horizontal(shape, mirror_axis)
            self.shapes.append(new_shape)
            new_shapes_indices.append(len(self.shapes) - 1)
        
        return new_shapes_indices
    
    def flip_shapes_vertical(self, selected_indices, gap=20):
        """Створити відзеркалені копії фігур по вертикалі"""
        from utils.geometry import get_selection_bbox
        
        if not selected_indices:
            return []
        
        bbox = get_selection_bbox(self.shapes, selected_indices)
        if bbox is None:
            return []
        
        min_x, min_y, max_x, max_y = bbox
        mirror_axis = max_y + gap
        
        new_shapes_indices = []
        
        for idx in sorted(selected_indices):
            shape = self.shapes[idx]
            new_shape = self._create_flipped_shape_vertical(shape, mirror_axis)
            self.shapes.append(new_shape)
            new_shapes_indices.append(len(self.shapes) - 1)
        
        return new_shapes_indices
    
    def _create_shape_copy(self, shape, offset_x, offset_y):
        """Створити копію фігури зі зсувом"""
        new_shape = Shape(
            shape.kind,
            color_bgr=shape.color_bgr,
            thickness=shape.thickness,
            style=shape.style,
            line_style=getattr(shape, 'line_style', 'solid'),
            text=getattr(shape, 'text', ''),
            font_scale=getattr(shape, 'font_scale', 1.0),
            filled=getattr(shape, 'filled', False),
            dash_length=getattr(shape, 'dash_length', 10),
            dot_length=getattr(shape, 'dot_length', 5)
        )
        
        # Копіюємо координати зі зсувом
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
        
        return new_shape
    
    def _create_flipped_shape_horizontal(self, shape, mirror_axis):
        """Створити відзеркалену копію фігури по горизонталі"""
        new_shape = Shape(
            shape.kind,
            color_bgr=shape.color_bgr,
            thickness=shape.thickness,
            style=shape.style,
            line_style=getattr(shape, 'line_style', 'solid'),
            text=getattr(shape, 'text', ''),
            font_scale=getattr(shape, 'font_scale', 1.0),
            filled=getattr(shape, 'filled', False),
            dash_length=getattr(shape, 'dash_length', 10),
            dot_length=getattr(shape, 'dot_length', 5)
        )
        
        if shape.kind in ['line', 'arrow']:
            c = shape.coords
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
        
        return new_shape
    
    def _create_flipped_shape_vertical(self, shape, mirror_axis):
        """Створити відзеркалену копію фігури по вертикалі"""
        new_shape = Shape(
            shape.kind,
            color_bgr=shape.color_bgr,
            thickness=shape.thickness,
            style=shape.style,
            line_style=getattr(shape, 'line_style', 'solid'),
            text=getattr(shape, 'text', ''),
            font_scale=getattr(shape, 'font_scale', 1.0),
            filled=getattr(shape, 'filled', False),
            dash_length=getattr(shape, 'dash_length', 10),
            dot_length=getattr(shape, 'dot_length', 5)
        )
        
        if shape.kind in ['line', 'arrow']:
            c = shape.coords
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
        
        return new_shape

