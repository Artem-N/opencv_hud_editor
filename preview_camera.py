"""
Попередній перегляд HUD на відео з камери
"""
import cv2
import numpy as np
import math
from PyQt5 import QtWidgets, QtCore, QtGui


class CameraPreviewWindow(QtWidgets.QDialog):
    """Вікно для попереднього перегляду HUD на відео з камери"""
    
    def __init__(self, canvas_widget, parent=None):
        super().__init__(parent)
        self.canvas_widget = canvas_widget
        self.setWindowTitle("Camera Preview - HUD Overlay Test")
        
        # Налаштування вікна
        self.setModal(False)
        self.resize(1280, 720)
        
        # Змінні для камери
        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_running = False
        
        # Отримуємо налаштування полотна
        self.canvas_limits = canvas_widget.get_canvas_limits()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Налаштування інтерфейсу"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Інформаційна панель
        info_layout = QtWidgets.QHBoxLayout()
        
        self.info_label = QtWidgets.QLabel()
        self.info_label.setStyleSheet("color: white; background-color: #333; padding: 5px;")
        info_layout.addWidget(self.info_label)
        
        self.fps_label = QtWidgets.QLabel("FPS: 0")
        self.fps_label.setStyleSheet("color: lime; background-color: #333; padding: 5px;")
        info_layout.addWidget(self.fps_label)
        
        layout.addLayout(info_layout)
        
        # Віджет для відображення відео
        self.video_label = QtWidgets.QLabel()
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setMinimumSize(640, 480)
        layout.addWidget(self.video_label)
        
        # Панель керування
        control_layout = QtWidgets.QHBoxLayout()
        
        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2"])
        control_layout.addWidget(QtWidgets.QLabel("Camera:"))
        control_layout.addWidget(self.camera_combo)
        
        control_layout.addStretch()
        
        self.start_btn = QtWidgets.QPushButton("Start Preview")
        self.start_btn.clicked.connect(self.start_preview)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_preview)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        control_layout.addWidget(self.close_btn)
        
        layout.addLayout(control_layout)
        
        # Початкова інформація
        if self.canvas_limits['enabled']:
            self.info_label.setText(
                f"Canvas size: {self.canvas_limits['width']}x{self.canvas_limits['height']} | "
                f"Video will be scaled to match canvas size"
            )
        else:
            self.info_label.setText("No canvas limits set. Video will be used as-is.")
    
    def start_preview(self):
        """Запустити попередній перегляд"""
        camera_index = self.camera_combo.currentIndex()
        
        # Спробувати відкрити камеру
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            QtWidgets.QMessageBox.warning(
                self,
                "Camera Error",
                f"Cannot open camera {camera_index}. Please check if camera is available."
            )
            return
        
        # Отримуємо параметри камери
        cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cam_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.info_label.setText(
            f"Camera: {cam_width}x{cam_height} @ {cam_fps}fps | "
            f"Canvas: {self.canvas_limits['width']}x{self.canvas_limits['height'] if self.canvas_limits['enabled'] else 'unlimited'}"
        )
        
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.camera_combo.setEnabled(False)
        
        # Запустити таймер (30 FPS)
        self.timer.start(33)
    
    def stop_preview(self):
        """Зупинити попередній перегляд"""
        self.is_running = False
        self.timer.stop()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.video_label.clear()
        self.video_label.setText("Preview stopped")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.camera_combo.setEnabled(True)
    
    def update_frame(self):
        """Оновити кадр"""
        if not self.is_running or not self.cap:
            return
        
        ret, frame = self.cap.read()
        
        if not ret:
            self.stop_preview()
            QtWidgets.QMessageBox.warning(
                self,
                "Camera Error",
                "Failed to read frame from camera."
            )
            return
        
        # Масштабуємо відео під розмір полотна (якщо потрібно)
        if self.canvas_limits['enabled']:
            target_width = self.canvas_limits['width']
            target_height = self.canvas_limits['height']
            
            # Масштабуємо відео
            frame = cv2.resize(frame, (target_width, target_height))
        
        # Накладаємо HUD
        frame = self._draw_hud_on_frame(frame)
        
        # Конвертуємо для відображення в Qt
        self._display_frame(frame)
        
        # Оновлюємо FPS
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps_label.setText(f"FPS: {int(fps)}")
    
    def _draw_hud_on_frame(self, frame):
        """Намалювати HUD на кадрі"""
        from rendering.shape_renderer import ShapeRenderer
        
        # Імпортуємо фігури з canvas
        shapes = self.canvas_widget.shape_manager.shapes
        
        if not shapes:
            return frame
        
        # Малюємо всі фігури на кадрі
        for shape in shapes:
            self._draw_shape(frame, shape)
        
        return frame
    
    def _draw_shape(self, frame, shape):
        """Намалювати одну фігуру на кадрі"""
        color = shape.color_bgr
        thickness = shape.thickness
        
        # Безпечно отримуємо стиль лінії
        line_style = getattr(shape, 'line_style', 'solid')
        dash_length = getattr(shape, 'dash_length', 10)
        dot_length = getattr(shape, 'dot_length', 5)
        
        if shape.kind == 'line':
            x1, y1 = int(shape.coords['x1']), int(shape.coords['y1'])
            x2, y2 = int(shape.coords['x2']), int(shape.coords['y2'])
            
            if line_style == 'solid':
                cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)
            elif line_style == 'dashed':
                self._draw_dashed_line(frame, (x1, y1), (x2, y2), color, thickness, dash_length)
            elif line_style == 'dotted':
                self._draw_dotted_line(frame, (x1, y1), (x2, y2), color, thickness, dot_length)
            else:
                # За замовчуванням суцільна лінія
                cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)
        
        elif shape.kind == 'circle':
            cx, cy = int(shape.coords['cx']), int(shape.coords['cy'])
            radius = int(shape.coords['radius'])
            fill = -1 if shape.filled else thickness
            cv2.circle(frame, (cx, cy), radius, color, fill, cv2.LINE_AA)
        
        elif shape.kind == 'rectangle':
            x1, y1 = int(shape.coords['x1']), int(shape.coords['y1'])
            x2, y2 = int(shape.coords['x2']), int(shape.coords['y2'])
            fill = -1 if shape.filled else thickness
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, fill, cv2.LINE_AA)
        
        elif shape.kind == 'arrow':
            x1, y1 = int(shape.coords['x1']), int(shape.coords['y1'])
            x2, y2 = int(shape.coords['x2']), int(shape.coords['y2'])
            
            if line_style == 'solid':
                cv2.arrowedLine(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA, tipLength=0.3)
            elif line_style == 'dashed':
                # Для пунктирних стрілок малюємо пунктирну лінію
                self._draw_dashed_line(frame, (x1, y1), (x2, y2), color, thickness, dash_length)
            elif line_style == 'dotted':
                # Для точкових стрілок малюємо точкову лінію
                self._draw_dotted_line(frame, (x1, y1), (x2, y2), color, thickness, dot_length)
            else:
                # За замовчуванням суцільна стрілка
                cv2.arrowedLine(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA, tipLength=0.3)
        
        elif shape.kind == 'ellipse':
            cx, cy = int(shape.coords['cx']), int(shape.coords['cy'])
            rx, ry = int(shape.coords['rx']), int(shape.coords['ry'])
            fill = -1 if shape.filled else thickness
            cv2.ellipse(frame, (cx, cy), (rx, ry), 0, 0, 360, color, fill, cv2.LINE_AA)
        
        elif shape.kind == 'point':
            x, y = int(shape.coords['x']), int(shape.coords['y'])
            cv2.circle(frame, (x, y), thickness, color, -1, cv2.LINE_AA)
        
        elif shape.kind == 'polygon':
            points = shape.coords['points']
            pts = np.array([[int(p[0]), int(p[1])] for p in points], np.int32)
            pts = pts.reshape((-1, 1, 2))
            fill = shape.filled
            if fill:
                cv2.fillPoly(frame, [pts], color, cv2.LINE_AA)
            else:
                cv2.polylines(frame, [pts], True, color, thickness, cv2.LINE_AA)
        
        elif shape.kind == 'text':
            x, y = int(shape.coords['x']), int(shape.coords['y'])
            text = shape.text
            font_scale = shape.font_scale
            cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, color, thickness, cv2.LINE_AA)
        
        elif shape.kind == 'curve':
            # Малюємо криву Безьє (квадратичну або кубічну)
            c = shape.coords
            
            is_cubic = 'cx1' in c and 'cy1' in c and 'cx2' in c and 'cy2' in c
            steps = self._estimate_curve_steps(c, is_cubic)
            
            # Перевіряємо тип кривої
            if is_cubic:
                # Кубічна крива
                points = self._calculate_cubic_bezier_curve(
                    (c['x1'], c['y1']), (c['cx1'], c['cy1']), 
                    (c['cx2'], c['cy2']), (c['x2'], c['y2']), steps
                )
            else:
                # Квадратична крива
                points = self._calculate_bezier_curve(
                    (c['x1'], c['y1']), (c['cx'], c['cy']), (c['x2'], c['y2']), steps
                )
            
            # Малюємо зі стилем
            if line_style == 'solid':
                pts = np.array([[int(p[0]), int(p[1])] for p in points], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], False, color, thickness, cv2.LINE_AA)
            elif line_style == 'dashed':
                # Малюємо пунктирну криву, враховуючи безперервність
                self._draw_dashed_polyline(frame, points, color, thickness, dash_length)
            elif line_style == 'dotted':
                # Малюємо точкову криву, враховуючи безперервність
                self._draw_dotted_polyline(frame, points, color, thickness, dot_length)
            else:
                # За замовчуванням суцільна крива
                pts = np.array([[int(p[0]), int(p[1])] for p in points], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], False, color, thickness, cv2.LINE_AA)
    
    def _draw_dashed_line(self, frame, pt1, pt2, color, thickness, dash_length):
        """Намалювати пунктирну лінію"""
        
        x1, y1 = pt1
        x2, y2 = pt2
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        dx /= length
        dy /= length
        
        current_length = 0
        draw = True
        
        while current_length < length:
            start_x = int(x1 + dx * current_length)
            start_y = int(y1 + dy * current_length)
            
            current_length += dash_length
            if current_length > length:
                current_length = length
            
            end_x = int(x1 + dx * current_length)
            end_y = int(y1 + dy * current_length)
            
            if draw:
                cv2.line(frame, (start_x, start_y), (end_x, end_y), color, thickness, cv2.LINE_AA)
            
            draw = not draw
    
    def _draw_dotted_line(self, frame, pt1, pt2, color, thickness, dot_spacing):
        """Намалювати точкову лінію"""
        
        x1, y1 = pt1
        x2, y2 = pt2
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        dx /= length
        dy /= length
        
        num_dots = int(length / dot_spacing)
        
        for i in range(num_dots + 1):
            x = int(x1 + dx * dot_spacing * i)
            y = int(y1 + dy * dot_spacing * i)
            cv2.circle(frame, (x, y), thickness, color, -1, cv2.LINE_AA)
    
    def _draw_dashed_polyline(self, frame, points, color, thickness, dash_length):
        """Намалювати пунктир вздовж polyline (кожен штрих — рівна пряма)"""
        if len(points) < 2 or dash_length <= 0:
            return
        
        total_length = self._polyline_length(points)
        if total_length <= 0:
            return
        
        current = 0.0
        draw_segment = True
        
        while current < total_length:
            next_dist = min(current + dash_length, total_length)
            if draw_segment:
                start_pt = self._point_on_polyline(points, current)
                end_pt = self._point_on_polyline(points, next_dist)
                if start_pt and end_pt:
                    x1, y1 = (int(round(start_pt[0])), int(round(start_pt[1])))
                    x2, y2 = (int(round(end_pt[0])), int(round(end_pt[1])))
                    if x1 != x2 or y1 != y2:
                        cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)
                    else:
                        cv2.circle(frame, (x1, y1), max(1, thickness), color, -1, cv2.LINE_AA)
            current = next_dist
            draw_segment = not draw_segment
    
    def _draw_dotted_polyline(self, frame, points, color, thickness, dot_spacing):
        """Намалювати точкову polyline з рівномірним кроком"""
        if len(points) < 2 or dot_spacing <= 0:
            return
        
        total_length = self._polyline_length(points)
        if total_length <= 0:
            return
        
        dist = 0.0
        while dist <= total_length:
            pt = self._point_on_polyline(points, dist)
            if pt:
                x, y = int(round(pt[0])), int(round(pt[1]))
                cv2.circle(frame, (x, y), max(1, thickness), color, -1, cv2.LINE_AA)
            dist += dot_spacing
        
        # Обов'язково додаємо останню точку
        pt_end = self._point_on_polyline(points, total_length)
        if pt_end:
            x, y = int(round(pt_end[0])), int(round(pt_end[1]))
            cv2.circle(frame, (x, y), max(1, thickness), color, -1, cv2.LINE_AA)
    
    def _polyline_length(self, points):
        """Повернути довжину polyline"""
        total = 0.0
        for i in range(len(points) - 1):
            total += math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        return total
    
    def _point_on_polyline(self, points, target_dist):
        """Отримати координату на polyline на заданій довжині"""
        if not points:
            return None
        
        if target_dist <= 0:
            return points[0]
        
        travelled = 0.0
        for i in range(len(points) - 1):
            pt1 = points[i]
            pt2 = points[i + 1]
            segment = math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])
            if segment == 0:
                continue
            if travelled + segment >= target_dist:
                t = (target_dist - travelled) / segment
                x = pt1[0] + (pt2[0] - pt1[0]) * t
                y = pt1[1] + (pt2[1] - pt1[1]) * t
                return (x, y)
            travelled += segment
        return points[-1]
    
    def _estimate_curve_steps(self, coords, is_cubic):
        """Оцінити кількість сегментів для кривої, щоб уникнути ламаних пунктирів"""
        def dist(pt_a, pt_b):
            return math.hypot(pt_a[0] - pt_b[0], pt_a[1] - pt_b[1])
        
        if is_cubic:
            p0 = (coords['x1'], coords['y1'])
            p1 = (coords['cx1'], coords['cy1'])
            p2 = (coords['cx2'], coords['cy2'])
            p3 = (coords['x2'], coords['y2'])
            approx_len = dist(p0, p1) + dist(p1, p2) + dist(p2, p3)
        else:
            p0 = (coords['x1'], coords['y1'])
            p1 = (coords['cx'], coords['cy'])
            p2 = (coords['x2'], coords['y2'])
            approx_len = dist(p0, p1) + dist(p1, p2)
        
        # Додаємо базову довжину між кінцями для надійності
        approx_len += dist((coords['x1'], coords['y1']), (coords['x2'], coords['y2']))
        
        steps = int(max(60, min(400, approx_len / 3)))
        return steps
    
    def _calculate_bezier_curve(self, p0, p1, p2, num_points):
        """Розрахувати точки квадратичної кривої Безьє"""
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
            points.append((x, y))
        return points
    
    def _calculate_cubic_bezier_curve(self, p0, p1, p2, p3, num_points):
        """Розрахувати точки кубічної кривої Безьє"""
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            t_inv = 1 - t
            # Кубічна крива Безьє: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            x = t_inv ** 3 * p0[0] + 3 * t_inv ** 2 * t * p1[0] + 3 * t_inv * t ** 2 * p2[0] + t ** 3 * p3[0]
            y = t_inv ** 3 * p0[1] + 3 * t_inv ** 2 * t * p1[1] + 3 * t_inv * t ** 2 * p2[1] + t ** 3 * p3[1]
            points.append((x, y))
        return points
    
    def _display_frame(self, frame):
        """Відобразити кадр у Qt віджеті"""
        # Конвертуємо BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Створюємо QImage
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(frame_rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        
        # Масштабуємо під розмір віджету
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
    
    def closeEvent(self, event):
        """Обробка закриття вікна"""
        self.stop_preview()
        event.accept()

