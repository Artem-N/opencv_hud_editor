"""
Геометричні утиліти та обчислення
"""
import math


def snap_to_grid(x, y, grid_step):
    """Прив'язка координат до сітки"""
    snapped_x = round(x / grid_step) * grid_step
    snapped_y = round(y / grid_step) * grid_step
    return int(snapped_x), int(snapped_y)


def point_near_line(px, py, x1, y1, x2, y2, tolerance):
    """Перевірити чи точка близько до лінії"""
    line_len = math.hypot(x2 - x1, y2 - y1)
    if line_len < 0.001:
        return math.hypot(px - x1, py - y1) < tolerance
    
    # Проекція точки на лінію
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len * line_len)))
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    
    dist = math.hypot(px - proj_x, py - proj_y)
    return dist < tolerance


def point_near_curve(px, py, x1, y1, x2, y2, cx, cy, tolerance):
    """Перевірити чи точка близько до кривої Безьє"""
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


def is_point_near_line_middle(px, py, x1, y1, x2, y2, tolerance):
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


def is_point_near_line_endpoint(px, py, x1, y1, x2, y2, tolerance):
    """Перевірити чи точка близько до початку чи кінця лінії
    
    Returns:
        (is_near, endpoint): (True/'start'/'end', None) або (False, None)
    """
    # Перевіряємо відстань до початку лінії
    dist_to_start = math.hypot(px - x1, py - y1)
    if dist_to_start < tolerance:
        return 'start', (x1, y1)
    
    # Перевіряємо відстань до кінця лінії
    dist_to_end = math.hypot(px - x2, py - y2)
    if dist_to_end < tolerance:
        return 'end', (x2, y2)
    
    return None, None


def point_near_cubic_curve(px, py, x1, y1, x2, y2, cx1, cy1, cx2, cy2, tolerance):
    """Перевірити чи точка близько до кубічної кривої Безьє"""
    min_dist = float('inf')
    steps = 30
    for i in range(steps + 1):
        t = i / steps
        # Кубічна крива Безьє: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
        t_inv = 1 - t
        bx = (t_inv ** 3 * x1 + 
              3 * t_inv ** 2 * t * cx1 + 
              3 * t_inv * t ** 2 * cx2 + 
              t ** 3 * x2)
        by = (t_inv ** 3 * y1 + 
              3 * t_inv ** 2 * t * cy1 + 
              3 * t_inv * t ** 2 * cy2 + 
              t ** 3 * y2)
        dist = math.hypot(px - bx, py - by)
        min_dist = min(min_dist, dist)
    return min_dist < tolerance


def constrain_line(x, y, x0, y0):
    """Обмежити лінію до горизонталі або вертикалі (при Shift)"""
    dx = abs(x - x0)
    dy = abs(y - y0)
    
    if dx > dy:
        return x, y0
    else:
        return x0, y


def get_selection_bbox(shapes, selected_shapes):
    """Отримати bounding box (мінімальний прямокутник) виділених фігур"""
    if not selected_shapes:
        return None
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for idx in selected_shapes:
        shape = shapes[idx]
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

