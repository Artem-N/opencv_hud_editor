"""
Рендер фігур на Qt canvas
"""
import math
from PyQt5 import QtGui, QtCore


class ShapeRenderer:
    """Клас для малювання фігур на Qt canvas"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def draw_shapes(painter, shapes, selected_shapes, zoom_factor, show_control_points=True):
        """Намалювати всі фігури"""
        for idx, shape in enumerate(shapes):
            is_selected = idx in selected_shapes
            ShapeRenderer.draw_shape(painter, shape, is_selected, zoom_factor, show_control_points)
    
    @staticmethod
    def draw_shape(painter, shape, is_selected, zoom_factor, show_control_points=True):
        """Намалювати одну фігуру"""
        r, g, b = shape.color_bgr[2], shape.color_bgr[1], shape.color_bgr[0]
        color = QtGui.QColor(r, g, b)
        pen = QtGui.QPen(color)
        pen.setWidth(max(1, int(shape.thickness / zoom_factor)))
        
        line_style = getattr(shape, 'line_style', 'solid')
        dash_length = getattr(shape, 'dash_length', 10)
        dot_length = getattr(shape, 'dot_length', 5)
        
        if is_selected:
            pen.setWidth(max(2, int((shape.thickness + 2) / zoom_factor)))
            pen.setStyle(QtCore.Qt.DashLine)
        else:
            pen.setStyle(QtCore.Qt.SolidLine)
        
        filled = getattr(shape, 'filled', False)
        
        painter.setPen(pen)
        if filled and shape.kind in ['circle', 'rectangle', 'ellipse', 'polygon']:
            brush = QtGui.QBrush(color)
            painter.setBrush(brush)
        else:
            painter.setBrush(QtCore.Qt.NoBrush)
        
        if shape.kind == 'line':
            ShapeRenderer._draw_line(painter, shape, is_selected, line_style, dash_length, dot_length, pen, color, zoom_factor)
        elif shape.kind == 'arrow':
            ShapeRenderer._draw_arrow(painter, shape, is_selected, line_style, dash_length, dot_length, pen, color, zoom_factor)
        elif shape.kind == 'curve':
            ShapeRenderer._draw_curve(painter, shape, is_selected, show_control_points, zoom_factor, pen, color)
        elif shape.kind == 'circle':
            ShapeRenderer._draw_circle(painter, shape)
        elif shape.kind == 'ellipse':
            ShapeRenderer._draw_ellipse(painter, shape)
        elif shape.kind == 'rectangle':
            ShapeRenderer._draw_rectangle(painter, shape)
        elif shape.kind == 'polygon':
            ShapeRenderer._draw_polygon(painter, shape)
        elif shape.kind == 'point':
            ShapeRenderer._draw_point(painter, shape, color)
        elif shape.kind == 'text':
            ShapeRenderer._draw_text(painter, shape)
        
        painter.setBrush(QtCore.Qt.NoBrush)
    
    @staticmethod
    def _draw_line(painter, shape, is_selected, line_style, dash_length, dot_length, pen, color, zoom_factor):
        """Малювання лінії"""
        c = shape.coords
        if not is_selected:
            if line_style == 'dashed':
                ShapeRenderer._draw_dashed_line_qt(painter, c['x1'], c['y1'], c['x2'], c['y2'], pen, dash_length)
            elif line_style == 'dotted':
                ShapeRenderer._draw_dotted_line_qt(painter, c['x1'], c['y1'], c['x2'], c['y2'], pen, dot_length)
            else:
                painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['x2'], c['y2']))
        else:
            painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['x2'], c['y2']))
            
            # Малюємо маркери на кінцях для вказівки можливості створення кубічної кривої
            endpoint_size = 8 / zoom_factor
            painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 200, 255)))  # Блакитний
            painter.setPen(QtGui.QPen(QtGui.QColor(50, 150, 255), 2))
            painter.drawEllipse(QtCore.QPointF(c['x1'], c['y1']), endpoint_size, endpoint_size)
            painter.drawEllipse(QtCore.QPointF(c['x2'], c['y2']), endpoint_size, endpoint_size)
    
    @staticmethod
    def _draw_arrow(painter, shape, is_selected, line_style, dash_length, dot_length, pen, color, zoom_factor):
        """Малювання стрілки"""
        c = shape.coords
        # Малюємо лінію
        if not is_selected:
            if line_style == 'dashed':
                ShapeRenderer._draw_dashed_line_qt(painter, c['x1'], c['y1'], c['x2'], c['y2'], pen, dash_length)
            elif line_style == 'dotted':
                ShapeRenderer._draw_dotted_line_qt(painter, c['x1'], c['y1'], c['x2'], c['y2'], pen, dot_length)
            else:
                painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['x2'], c['y2']))
        else:
            painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['x2'], c['y2']))
        
        # Малюємо стрілку (трикутник)
        dx = c['x2'] - c['x1']
        dy = c['y2'] - c['y1']
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
            arrow_size = min(20, length / 3)
            ax, ay = c['x2'], c['y2']
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
        
        # Малюємо маркери на кінцях коли виділено
        if is_selected:
            endpoint_size = 8 / zoom_factor
            painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 200, 255)))  # Блакитний
            painter.setPen(QtGui.QPen(QtGui.QColor(50, 150, 255), 2))
            painter.drawEllipse(QtCore.QPointF(c['x1'], c['y1']), endpoint_size, endpoint_size)
            painter.drawEllipse(QtCore.QPointF(c['x2'], c['y2']), endpoint_size, endpoint_size)
    
    @staticmethod
    def _draw_curve(painter, shape, is_selected, show_control_points, zoom_factor, pen, color):
        """Малювання кривої Безьє (квадратичної або кубічної)"""
        c = shape.coords
        
        # Перевіряємо стилі лінії
        line_style = getattr(shape, 'line_style', 'solid')
        dash_length = getattr(shape, 'dash_length', 10)
        dot_length = getattr(shape, 'dot_length', 5)
        
        path = QtGui.QPainterPath()
        path.moveTo(c['x1'], c['y1'])
        
        # Перевіряємо тип кривої
        if 'cx1' in c and 'cy1' in c and 'cx2' in c and 'cy2' in c:
            # Кубічна крива Безьє з двома контрольними точками
            path.cubicTo(c['cx1'], c['cy1'], c['cx2'], c['cy2'], c['x2'], c['y2'])
        else:
            # Квадратична крива Безьє з однією контрольною точкою
            path.quadTo(c['cx'], c['cy'], c['x2'], c['y2'])
        
        # Застосовуємо стилі для кривої через QPen (правильні пунктири)
        if line_style == 'dashed':
            # Створюємо pen з пунктирним стилем
            dashed_pen = QtGui.QPen(pen)
            # Встановлюємо pattern для пунктиру
            dash_pattern = [dash_length, dash_length]  # [довжина_пунктира, проміжок]
            dashed_pen.setDashPattern(dash_pattern)
            dashed_pen.setCapStyle(QtCore.Qt.FlatCap)
            painter.setPen(dashed_pen)
            painter.drawPath(path)
        elif line_style == 'dotted':
            # Створюємо pen з точковим стилем
            dotted_pen = QtGui.QPen(pen)
            # Встановлюємо pattern для точок
            dot_pattern = [dot_length, dot_length * 2]  # [довжина_точки, проміжок]
            dotted_pen.setDashPattern(dot_pattern)
            dotted_pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(dotted_pen)
            painter.drawPath(path)
        else:
            # Суцільна лінія - малюємо звичайним path
            painter.drawPath(path)
        
        # Контрольні точки
        if is_selected and show_control_points:
            pen_helper = QtGui.QPen(QtGui.QColor(100, 100, 100))
            pen_helper.setStyle(QtCore.Qt.DotLine)
            pen_helper.setWidth(1)
            painter.setPen(pen_helper)
            
            ctrl_point_size = 6 / zoom_factor
            end_point_size = 4 / zoom_factor
            
            if 'cx1' in c and 'cy1' in c and 'cx2' in c and 'cy2' in c:
                # Кубічна крива - малюємо дві контрольні точки
                # Лінії до контрольних точок
                painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['cx1'], c['cy1']))
                painter.drawLine(QtCore.QPointF(c['x2'], c['y2']), QtCore.QPointF(c['cx2'], c['cy2']))
                
                # Перша контрольна точка (жовта)
                painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 200, 0)))
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
                painter.drawEllipse(QtCore.QPointF(c['cx1'], c['cy1']), ctrl_point_size, ctrl_point_size)
                
                # Друга контрольна точка (помаранчева)
                painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 150, 0)))
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 100, 0)))
                painter.drawEllipse(QtCore.QPointF(c['cx2'], c['cy2']), ctrl_point_size, ctrl_point_size)
            else:
                # Квадратична крива - одна контрольна точка
                painter.drawLine(QtCore.QPointF(c['x1'], c['y1']), QtCore.QPointF(c['cx'], c['cy']))
                painter.drawLine(QtCore.QPointF(c['x2'], c['y2']), QtCore.QPointF(c['cx'], c['cy']))
                
                # Контрольна точка (жовта)
                painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 200, 0)))
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
                painter.drawEllipse(QtCore.QPointF(c['cx'], c['cy']), ctrl_point_size, ctrl_point_size)
            
            # Кінцеві точки
            painter.setBrush(QtGui.QBrush(color))
            painter.setPen(pen)
            painter.drawEllipse(QtCore.QPointF(c['x1'], c['y1']), end_point_size, end_point_size)
            painter.drawEllipse(QtCore.QPointF(c['x2'], c['y2']), end_point_size, end_point_size)
    
    @staticmethod
    def _draw_circle(painter, shape):
        """Малювання кола"""
        c = shape.coords
        painter.drawEllipse(QtCore.QPointF(c['cx'], c['cy']), c['r'], c['r'])
    
    @staticmethod
    def _draw_ellipse(painter, shape):
        """Малювання еліпса"""
        c = shape.coords
        cx, cy = c['cx'], c['cy']
        rx, ry = c['rx'], c['ry']
        painter.drawEllipse(QtCore.QRectF(cx - rx, cy - ry, 2 * rx, 2 * ry))
    
    @staticmethod
    def _draw_rectangle(painter, shape):
        """Малювання прямокутника"""
        c = shape.coords
        x1, y1 = min(c['x1'], c['x2']), min(c['y1'], c['y2'])
        x2, y2 = max(c['x1'], c['x2']), max(c['y1'], c['y2'])
        painter.drawRect(QtCore.QRectF(x1, y1, x2 - x1, y2 - y1))
    
    @staticmethod
    def _draw_polygon(painter, shape):
        """Малювання полігону"""
        c = shape.coords
        if 'points' in c and len(c['points']) >= 3:
            poly = QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in c['points']])
            painter.drawPolygon(poly)
    
    @staticmethod
    def _draw_point(painter, shape, color):
        """Малювання точки"""
        c = shape.coords
        point_size = max(3, shape.thickness * 2)
        painter.setBrush(QtGui.QBrush(color))
        painter.drawEllipse(QtCore.QPointF(c['x'], c['y']), point_size, point_size)
    
    @staticmethod
    def _draw_text(painter, shape):
        """Малювання тексту"""
        c = shape.coords
        font_scale = getattr(shape, 'font_scale', 1.0)
        text = getattr(shape, 'text', '')
        font = QtGui.QFont("Arial", int(16 * font_scale))
        painter.setFont(font)
        painter.drawText(QtCore.QPointF(c['x'], c['y']), text)
    
    @staticmethod
    def _draw_dashed_line_qt(painter, x1, y1, x2, y2, pen, dash_length):
        """Малювання пунктирної лінії"""
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 1:
            return
        
        dashes = int(dist / dash_length)
        if dashes < 1:
            painter.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
            return
        
        for i in range(dashes):
            if i % 2 == 0:
                start_t = i / dashes
                end_t = (i + 0.5) / dashes
                start_x = x1 + (x2 - x1) * start_t
                start_y = y1 + (y2 - y1) * start_t
                end_x = x1 + (x2 - x1) * end_t
                end_y = y1 + (y2 - y1) * end_t
                painter.drawLine(QtCore.QPointF(start_x, start_y), QtCore.QPointF(end_x, end_y))
    
    @staticmethod
    def _draw_dotted_line_qt(painter, x1, y1, x2, y2, pen, dot_length):
        """Малювання точкової лінії"""
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 1:
            return
        
        dots = int(dist / dot_length)
        if dots < 1:
            painter.drawEllipse(QtCore.QPointF(x1, y1), pen.width(), pen.width())
            return
        
        for i in range(dots):
            if i % 2 == 0:
                t = i / dots
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                painter.drawEllipse(QtCore.QPointF(px, py), max(1, pen.width()), max(1, pen.width()))
    
    @staticmethod
    def draw_selection_rect(painter, temp_point, mouse_pos):
        """Намалювати рамку виділення"""
        if temp_point is None or mouse_pos is None:
            return
        
        x0, y0 = temp_point
        x1, y1 = mouse_pos
        pen = QtGui.QPen(QtGui.QColor(100, 150, 255))
        pen.setStyle(QtCore.Qt.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(QtCore.QRectF(
            QtCore.QPointF(min(x0, x1), min(y0, y1)),
            QtCore.QPointF(max(x0, x1), max(y0, y1))
        ))
    
    @staticmethod
    def draw_shape_preview(painter, mode, temp_point, mouse_pos, current_color_bgr, 
                          current_thickness, current_filled, zoom_factor):
        """Намалювати прев'ю незавершеної фігури"""
        if temp_point is None or mouse_pos is None:
            return
        
        if mode not in ['line', 'circle', 'rectangle', 'arrow', 'ellipse']:
            return
        
        x0, y0 = temp_point
        x1, y1 = mouse_pos
        r, g, b = current_color_bgr[2], current_color_bgr[1], current_color_bgr[0]
        color = QtGui.QColor(r, g, b)
        pen = QtGui.QPen(color)
        pen.setStyle(QtCore.Qt.DotLine)
        pen.setWidth(max(1, int(current_thickness / zoom_factor)))
        painter.setPen(pen)
        
        if current_filled:
            brush = QtGui.QBrush(color)
            painter.setBrush(brush)
        else:
            painter.setBrush(QtCore.Qt.NoBrush)
        
        if mode == 'line':
            painter.drawLine(QtCore.QPointF(x0, y0), QtCore.QPointF(x1, y1))
        elif mode == 'arrow':
            painter.drawLine(QtCore.QPointF(x0, y0), QtCore.QPointF(x1, y1))
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
        elif mode == 'circle':
            r = int(round(math.hypot(x1 - x0, y1 - y0)))
            painter.drawEllipse(QtCore.QPointF(x0, y0), r, r)
        elif mode == 'rectangle':
            rect_x1, rect_y1 = min(x0, x1), min(y0, y1)
            rect_x2, rect_y2 = max(x0, x1), max(y0, y1)
            painter.drawRect(QtCore.QRectF(rect_x1, rect_y1, rect_x2 - rect_x1, rect_y2 - rect_y1))
        elif mode == 'ellipse':
            rx = abs(x1 - x0)
            ry = abs(y1 - y0)
            painter.drawEllipse(QtCore.QRectF(x0 - rx, y0 - ry, 2 * rx, 2 * ry))
    
    @staticmethod
    def draw_polygon_preview(painter, polygon_points, mouse_pos, current_color_bgr, current_thickness, zoom_factor):
        """Намалювати прев'ю полігону"""
        if len(polygon_points) == 0:
            return
        
        r, g, b = current_color_bgr[2], current_color_bgr[1], current_color_bgr[0]
        color = QtGui.QColor(r, g, b)
        pen = QtGui.QPen(color)
        pen.setWidth(max(1, int(current_thickness / zoom_factor)))
        painter.setPen(pen)
        
        # Малюємо точки
        for px, py in polygon_points:
            point_size = 4
            painter.setBrush(QtGui.QBrush(color))
            painter.drawEllipse(QtCore.QPointF(px, py), point_size, point_size)
        
        # Малюємо лінії
        painter.setBrush(QtCore.Qt.NoBrush)
        pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(pen)
        for i in range(len(polygon_points) - 1):
            p1 = polygon_points[i]
            p2 = polygon_points[i + 1]
            painter.drawLine(QtCore.QPointF(p1[0], p1[1]), QtCore.QPointF(p2[0], p2[1]))
        
        # Лінія від останньої точки до курсору
        if mouse_pos is not None and len(polygon_points) > 0:
            last_point = polygon_points[-1]
            pen.setStyle(QtCore.Qt.DotLine)
            painter.setPen(pen)
            painter.drawLine(
                QtCore.QPointF(last_point[0], last_point[1]),
                QtCore.QPointF(mouse_pos[0], mouse_pos[1])
            )
        
        # Лінія замикання
        if len(polygon_points) >= 3:
            first_point = polygon_points[0]
            last_point = polygon_points[-1]
            pen.setStyle(QtCore.Qt.DotLine)
            painter.setPen(pen)
            painter.drawLine(
                QtCore.QPointF(last_point[0], last_point[1]),
                QtCore.QPointF(first_point[0], first_point[1])
            )

