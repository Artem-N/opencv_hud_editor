"""
Головне вікно додатку
"""
import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore

from canvas_widget import CanvasWidget
from constants import COLOR_PRESETS, STYLE_PRESETS


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV HUD Editor")
        self.resize(800, 600)
        
        # Встановлюємо політику фокусу для прийому клавіатурних подій
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.canvas = CanvasWidget()
        self.setCentralWidget(self.canvas)

        self._build_ui()

    def _build_ui(self):
        toolbar = QtWidgets.QToolBar()
        toolbar.setFocusPolicy(QtCore.Qt.NoFocus)  # Toolbar не має перехоплювати фокус
        self.addToolBar(toolbar)

        btn_pan = QtWidgets.QAction("Pan (P)", self)
        btn_pan.setToolTip("Pan mode - move canvas with left mouse button")
        btn_pan.triggered.connect(self.canvas.set_mode_pan)
        toolbar.addAction(btn_pan)

        btn_select = QtWidgets.QAction("Select (S)", self)
        btn_select.triggered.connect(self.canvas.set_mode_select)
        toolbar.addAction(btn_select)

        btn_line = QtWidgets.QAction("Line (L)", self)
        btn_line.triggered.connect(self.canvas.set_mode_line)
        toolbar.addAction(btn_line)

        btn_circle = QtWidgets.QAction("Circle (C)", self)
        btn_circle.triggered.connect(self.canvas.set_mode_circle)
        toolbar.addAction(btn_circle)

        btn_text = QtWidgets.QAction("Text (T)", self)
        btn_text.triggered.connect(self.canvas.set_mode_text)
        toolbar.addAction(btn_text)
        
        btn_point = QtWidgets.QAction("Point", self)
        btn_point.setToolTip("Point - single click")
        btn_point.triggered.connect(self.canvas.set_mode_point)
        toolbar.addAction(btn_point)
        
        btn_rectangle = QtWidgets.QAction("Rectangle (R)", self)
        btn_rectangle.setToolTip("Rectangle - drag to draw")
        btn_rectangle.triggered.connect(self.canvas.set_mode_rectangle)
        toolbar.addAction(btn_rectangle)
        
        btn_arrow = QtWidgets.QAction("Arrow (A)", self)
        btn_arrow.setToolTip("Arrow - drag to draw")
        btn_arrow.triggered.connect(self.canvas.set_mode_arrow)
        toolbar.addAction(btn_arrow)
        
        btn_polygon = QtWidgets.QAction("Polygon", self)
        btn_polygon.setToolTip("Polygon - click to add points, right-click to finish")
        btn_polygon.triggered.connect(self.canvas.set_mode_polygon)
        toolbar.addAction(btn_polygon)
        
        btn_ellipse = QtWidgets.QAction("Ellipse (E)", self)
        btn_ellipse.setToolTip("Ellipse - drag to draw")
        btn_ellipse.triggered.connect(self.canvas.set_mode_ellipse)
        toolbar.addAction(btn_ellipse)

        toolbar.addSeparator()

        # Вибір кольору
        toolbar.addWidget(QtWidgets.QLabel("Color:"))
        self.color_combo = QtWidgets.QComboBox()
        self.color_combo.addItems(list(COLOR_PRESETS.keys()))
        self.color_combo.setCurrentText('Green')
        self.color_combo.currentTextChanged.connect(self.on_color_preset_changed)
        toolbar.addWidget(self.color_combo)
        
        btn_color_dialog = QtWidgets.QAction("Custom...", self)
        btn_color_dialog.setToolTip("Choose custom color")
        btn_color_dialog.triggered.connect(self.show_color_dialog)
        toolbar.addAction(btn_color_dialog)
        
        self.color_preview = QtWidgets.QWidget()
        self.color_preview.setFixedSize(20, 20)
        self.color_preview.setStyleSheet("background-color: rgb(0, 255, 0); border: 1px solid gray;")
        toolbar.addWidget(self.color_preview)

        toolbar.addSeparator()

        # Товщина лінії
        toolbar.addWidget(QtWidgets.QLabel("Thickness:"))
        self.thickness_spin = QtWidgets.QSpinBox()
        self.thickness_spin.setMinimum(1)
        self.thickness_spin.setMaximum(20)
        self.thickness_spin.setValue(2)
        self.thickness_spin.valueChanged.connect(self.on_thickness_changed)
        toolbar.addWidget(self.thickness_spin)

        toolbar.addSeparator()

        # Стиль
        toolbar.addWidget(QtWidgets.QLabel("Style:"))
        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItems(STYLE_PRESETS)
        self.style_combo.setCurrentText('default')
        self.style_combo.currentTextChanged.connect(self.on_style_changed)
        toolbar.addWidget(self.style_combo)

        toolbar.addSeparator()
        
        # Стиль лінії
        toolbar.addWidget(QtWidgets.QLabel("Line:"))
        self.line_style_combo = QtWidgets.QComboBox()
        self.line_style_combo.addItems(['solid', 'dashed', 'dotted'])
        self.line_style_combo.setCurrentText('solid')
        self.line_style_combo.setToolTip("Line style")
        self.line_style_combo.currentTextChanged.connect(self.on_line_style_changed)
        toolbar.addWidget(self.line_style_combo)
        
        # Заповнення
        self.filled_checkbox = QtWidgets.QCheckBox("Filled")
        self.filled_checkbox.setToolTip("Fill shapes (circles, rectangles, polygons)")
        self.filled_checkbox.toggled.connect(self.on_filled_toggled)
        toolbar.addWidget(self.filled_checkbox)

        toolbar.addSeparator()

        # Розмір шрифту для тексту
        toolbar.addWidget(QtWidgets.QLabel("Font:"))
        self.font_scale_spin = QtWidgets.QDoubleSpinBox()
        self.font_scale_spin.setRange(0.5, 5.0)
        self.font_scale_spin.setSingleStep(0.5)
        self.font_scale_spin.setValue(1.0)
        self.font_scale_spin.setToolTip("Font scale for text")
        self.font_scale_spin.valueChanged.connect(self.on_font_scale_changed)
        toolbar.addWidget(self.font_scale_spin)

        toolbar.addSeparator()

        # Снап до сітки
        self.snap_checkbox = QtWidgets.QCheckBox("Snap to Grid")
        self.snap_checkbox.setToolTip("Snap points to grid (G)")
        self.snap_checkbox.toggled.connect(self.on_snap_toggled)
        toolbar.addWidget(self.snap_checkbox)

        toolbar.addSeparator()

        btn_copy = QtWidgets.QAction("Copy (Ctrl+C)", self)
        btn_copy.setToolTip("Copy selected shapes")
        btn_copy.triggered.connect(self.canvas.copy_selected)
        toolbar.addAction(btn_copy)

        btn_paste = QtWidgets.QAction("Paste (Ctrl+V)", self)
        btn_paste.setToolTip("Paste shapes from clipboard")
        btn_paste.triggered.connect(self.canvas.paste)
        toolbar.addAction(btn_paste)

        toolbar.addSeparator()

        btn_flip_h = QtWidgets.QAction("Flip H", self)
        btn_flip_h.setToolTip("Create mirrored copies horizontally")
        btn_flip_h.triggered.connect(self.canvas.flip_horizontal)
        toolbar.addAction(btn_flip_h)

        btn_flip_v = QtWidgets.QAction("Flip V", self)
        btn_flip_v.setToolTip("Create mirrored copies vertically")
        btn_flip_v.triggered.connect(self.canvas.flip_vertical)
        toolbar.addAction(btn_flip_v)

        toolbar.addSeparator()

        btn_undo = QtWidgets.QAction("Undo (Z)", self)
        btn_undo.triggered.connect(self.canvas.undo)
        toolbar.addAction(btn_undo)

        btn_clear = QtWidgets.QAction("Clear", self)
        btn_clear.triggered.connect(self.canvas.clear_all)
        toolbar.addAction(btn_clear)

        toolbar.addSeparator()

        btn_reset_zoom = QtWidgets.QAction("Reset Zoom (R)", self)
        btn_reset_zoom.setToolTip("Reset zoom and pan to default")
        btn_reset_zoom.triggered.connect(self.canvas.reset_zoom)
        toolbar.addAction(btn_reset_zoom)

        toolbar.addSeparator()
        
        btn_save_project = QtWidgets.QAction("Save Project", self)
        btn_save_project.setToolTip("Save project to JSON file (Ctrl+S)")
        btn_save_project.triggered.connect(self.save_project)
        toolbar.addAction(btn_save_project)
        
        btn_load_project = QtWidgets.QAction("Load Project", self)
        btn_load_project.setToolTip("Load project from JSON file (Ctrl+O)")
        btn_load_project.triggered.connect(self.load_project)
        toolbar.addAction(btn_load_project)

        toolbar.addSeparator()

        btn_export = QtWidgets.QAction("Export code (Ctrl+E)", self)
        btn_export.triggered.connect(self.export_code)
        toolbar.addAction(btn_export)

        # статусна строка
        self.status = QtWidgets.QLabel("Mode: pan | Left click & drag to move canvas | Right click to return to Pan | Wheel – zoom")
        self.statusBar().addWidget(self.status)
        
        self.coords_label = QtWidgets.QLabel("")
        self.shape_info_label = QtWidgets.QLabel("")
        self.zoom_label = QtWidgets.QLabel("Zoom: 100%")
        self.statusBar().addPermanentWidget(self.coords_label)
        self.statusBar().addPermanentWidget(self.shape_info_label)
        self.statusBar().addPermanentWidget(self.zoom_label)
        
        # Підключення сигналів
        self.canvas.mode_changed.connect(self.on_mode_changed)
        self.canvas.mouse_moved.connect(self.on_mouse_moved)
        self.canvas.shape_info_changed.connect(self.on_shape_info_changed)
        self.canvas.zoom_changed.connect(self.on_zoom_changed)
        
        # Ініціалізація початкових значень
        self.on_color_preset_changed('Green')
        self.on_thickness_changed(2)
        self.on_style_changed('default')

    def on_mode_changed(self, mode: str):
        if mode == 'pan':
            self.status.setText(f"Mode: {mode} | Left click & drag to move canvas | Right click to return to Pan | Wheel – zoom")
        elif mode == 'select':
            self.status.setText(f"Mode: {mode} | Click to select | Drag selected to move | Ctrl+Click – add | Right click – back to Pan")
        elif mode in ['line', 'circle', 'rectangle', 'arrow', 'ellipse']:
            self.status.setText(f"Mode: {mode} | Left click & drag to draw | Right click – back to Pan | Shift – constrain | Wheel – zoom")
        elif mode == 'polygon':
            self.status.setText(f"Mode: {mode} | Click to add points | Right click to finish polygon (min 3 points) | Esc – back to Pan")
        elif mode == 'point':
            self.status.setText(f"Mode: {mode} | Click to place point | Right click – back to Pan")
        elif mode == 'text':
            self.status.setText(f"Mode: {mode} | Click where you want to add text | Right click – back to Pan")
    
    def on_snap_toggled(self, checked: bool):
        self.canvas.set_snap_to_grid(checked)
    
    def on_mouse_moved(self, x: int, y: int):
        self.coords_label.setText(f"Cursor: ({x}, {y})")
    
    def on_shape_info_changed(self, info: str):
        if info:
            self.shape_info_label.setText(f" | {info}")
        else:
            self.shape_info_label.setText("")
    
    def on_zoom_changed(self, zoom_factor: float):
        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")
    
    def on_color_preset_changed(self, preset_name: str):
        if preset_name in COLOR_PRESETS:
            color_bgr = COLOR_PRESETS[preset_name]
            self.canvas.set_color(color_bgr)
            self._update_color_preview(color_bgr)
            # Якщо є вибрані фігури - змінюємо їх колір
            self._apply_to_selected_shapes('color', color_bgr)
    
    def show_color_dialog(self):
        current_b, current_g, current_r = self.canvas.current_color_bgr
        current_color = QtGui.QColor(current_r, current_g, current_b)
        color = QtWidgets.QColorDialog.getColor(current_color, self, "Choose Color")
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            color_bgr = (b, g, r)
            self.canvas.set_color(color_bgr)
            self._update_color_preview(color_bgr)
            # Якщо є вибрані фігури - змінюємо їх колір
            self._apply_to_selected_shapes('color', color_bgr)
    
    def _update_color_preview(self, color_bgr):
        b, g, r = color_bgr
        self.color_preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 1px solid gray;")
    
    def on_thickness_changed(self, value: int):
        self.canvas.set_thickness(value)
        # Якщо є вибрані фігури - змінюємо їх товщину
        self._apply_to_selected_shapes('thickness', value)
    
    def on_style_changed(self, style: str):
        self.canvas.set_style(style)
        # Якщо є вибрані фігури - змінюємо їх стиль
        self._apply_to_selected_shapes('style', style)
    
    def on_font_scale_changed(self, value: float):
        self.canvas.set_font_scale(value)
        # Якщо є вибрані фігури тексту - змінюємо їх розмір
        self._apply_to_selected_shapes('font_scale', value)
    
    def on_line_style_changed(self, line_style: str):
        """Обробник зміни стилю лінії"""
        self.canvas.set_line_style(line_style)
        # Якщо є вибрані фігури - змінюємо їх стиль лінії
        self._apply_to_selected_shapes('line_style', line_style)
    
    def on_filled_toggled(self, checked: bool):
        """Обробник зміни заповнення фігур"""
        self.canvas.set_filled(checked)
        # Якщо є вибрані фігури - змінюємо їх заповнення
        self._apply_to_selected_shapes('filled', checked)
    
    def _apply_to_selected_shapes(self, property_name: str, value):
        """Застосувати зміни до вибраних фігур"""
        if not self.canvas.selected_shapes:
            return
        
        changed = False
        for idx in self.canvas.selected_shapes:
            if 0 <= idx < len(self.canvas.shapes):
                shape = self.canvas.shapes[idx]
                
                if property_name == 'color':
                    shape.color_bgr = value
                    changed = True
                elif property_name == 'thickness':
                    shape.thickness = value
                    changed = True
                elif property_name == 'style':
                    shape.style = value
                    changed = True
                elif property_name == 'font_scale':
                    # Тільки для тексту
                    if shape.kind == 'text':
                        shape.font_scale = value
                        changed = True
                elif property_name == 'line_style':
                    shape.line_style = value
                    changed = True
                elif property_name == 'filled':
                    # Тільки для фігур, які можуть бути заповненими
                    if shape.kind in ['circle', 'rectangle', 'ellipse', 'polygon']:
                        shape.filled = value
                        changed = True
        
        if changed:
            self.canvas.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        text = event.text().upper()  # Отримуємо текст клавіші в верхньому регістрі
        
        # Дебаг: виводимо в консоль що отримали
        # print(f"Key pressed: key={key}, text='{text}', modifiers={modifiers}")
        
        # Спеціальні клавіші
        if key == QtCore.Qt.Key_Escape:
            self.canvas.set_mode_pan()
            return
        elif key == QtCore.Qt.Key_Delete:
            self.delete_selected()
            return
        
        # Перевіряємо Ctrl модифікатор
        ctrl_pressed = bool(modifiers & QtCore.Qt.ControlModifier)
        
        # Ctrl+C / Ctrl+V
        if ctrl_pressed:
            if key == QtCore.Qt.Key_C or text in ['C', 'С']:
                self.canvas.copy_selected()
                return
            elif key == QtCore.Qt.Key_V or text in ['V', 'М']:
                self.canvas.paste()
                return
        
        # Звичайні клавіші (без Ctrl)
        if not ctrl_pressed:
            # Перевіряємо по коду клавіші або по тексту
            if key == QtCore.Qt.Key_P or text in ['P', 'З']:
                self.canvas.set_mode_pan()
            elif key == QtCore.Qt.Key_S or text in ['S', 'І', 'Ы']:
                self.canvas.set_mode_select()
            elif key == QtCore.Qt.Key_L or text in ['L', 'Д']:
                self.canvas.set_mode_line()
            elif key == QtCore.Qt.Key_T or text in ['T', 'Е']:
                self.canvas.set_mode_text()
            elif key == QtCore.Qt.Key_C or text in ['C', 'С']:
                self.canvas.set_mode_circle()
            elif key == QtCore.Qt.Key_A or text in ['A', 'Ф']:
                self.canvas.set_mode_arrow()
            elif key == QtCore.Qt.Key_R or text in ['R', 'К']:
                # R тепер для Rectangle (раніше був reset zoom, тепер reset на клавіші 0)
                self.canvas.set_mode_rectangle()
            elif key == QtCore.Qt.Key_E or text in ['E', 'У']:
                # E тепер для Ellipse (раніше був export, тепер export на Ctrl+E)
                self.canvas.set_mode_ellipse()
            elif key == QtCore.Qt.Key_Y or text in ['Y', 'Н']:
                self.canvas.set_mode_polygon()
            elif key == QtCore.Qt.Key_D or text in ['D', 'В']:
                self.canvas.set_mode_point()
            elif key == QtCore.Qt.Key_G or text in ['G', 'П', 'Р']:
                self.snap_checkbox.toggle()
            elif key == QtCore.Qt.Key_0 or key == QtCore.Qt.Key_Home:
                self.canvas.reset_zoom()
            elif key == QtCore.Qt.Key_Z or text in ['Z', 'Я']:
                self.canvas.undo()
            elif key == QtCore.Qt.Key_F5:
                self.export_code()
            else:
                super().keyPressEvent(event)
        else:
            # Ctrl+E для експорту коду
            if key == QtCore.Qt.Key_E or text in ['E', 'У']:
                self.export_code()
            # Ctrl+S для збереження проекту
            elif key == QtCore.Qt.Key_S or text in ['S', 'І', 'Ы']:
                self.save_project()
            # Ctrl+O для завантаження проекту
            elif key == QtCore.Qt.Key_O or text in ['O', 'Щ']:
                self.load_project()
            else:
                super().keyPressEvent(event)
    
    def delete_selected(self):
        """Видалити вибрані фігури"""
        if not self.canvas.selected_shapes:
            return
        
        # Видаляємо фігури (від кінця до початку, щоб індекси не зміщувалися)
        for idx in sorted(self.canvas.selected_shapes, reverse=True):
            if 0 <= idx < len(self.canvas.shapes):
                del self.canvas.shapes[idx]
        
        self.canvas.selected_shapes.clear()
        self.canvas.update()

    def export_code(self):
        canvas_rect = self.canvas.rect()
        canvas_width = canvas_rect.width()
        canvas_height = canvas_rect.height()
        
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Export OpenCV code")
        layout = QtWidgets.QVBoxLayout(dlg)
        
        options_group = QtWidgets.QGroupBox("Export Options")
        options_layout = QtWidgets.QVBoxLayout()
        
        origin_label = QtWidgets.QLabel("Coordinate system:")
        options_layout.addWidget(origin_label)
        
        self.origin_combo = QtWidgets.QComboBox()
        self.origin_combo.addItem("Editor coordinates (0,0 at top-left)", 'editor')
        self.origin_combo.addItem("Center-based coordinates (0,0 at center)", 'center')
        self.origin_combo.setCurrentIndex(0)
        options_layout.addWidget(self.origin_combo)
        
        info_label = QtWidgets.QLabel(f"Canvas size: {canvas_width} x {canvas_height} px")
        info_label.setStyleSheet("color: gray;")
        options_layout.addWidget(info_label)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        buttons_layout = QtWidgets.QHBoxLayout()
        
        btn_generate = QtWidgets.QPushButton("Generate Code")
        btn_generate.clicked.connect(lambda: self._generate_and_show_code(dlg, canvas_width, canvas_height))
        buttons_layout.addWidget(btn_generate)
        
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(dlg.reject)
        buttons_layout.addWidget(btn_close)
        
        layout.addLayout(buttons_layout)
        
        dlg.resize(700, 500)
        dlg.exec_()
    
    def _generate_and_show_code(self, parent_dlg, canvas_width, canvas_height):
        origin_mode = self.origin_combo.currentData()
        
        code = self.canvas.generate_opencv_code(
            origin_mode=origin_mode,
            canvas_width=canvas_width,
            canvas_height=canvas_height
        )
        
        parent_dlg.accept()
        
        code_dlg = QtWidgets.QDialog(self)
        code_dlg.setWindowTitle("Generated OpenCV code")
        code_layout = QtWidgets.QVBoxLayout(code_dlg)
        
        text = QtWidgets.QPlainTextEdit()
        text.setPlainText(code)
        text.setReadOnly(True)
        text.setFont(QtGui.QFont("Consolas", 9))
        code_layout.addWidget(text)
        
        buttons_layout = QtWidgets.QHBoxLayout()
        
        btn_save = QtWidgets.QPushButton("Save as...")
        btn_save.clicked.connect(lambda: self._save_code_to_file(code))
        buttons_layout.addWidget(btn_save)
        
        btn_copy = QtWidgets.QPushButton("Copy to Clipboard")
        btn_copy.clicked.connect(lambda: self._copy_to_clipboard(code))
        buttons_layout.addWidget(btn_copy)
        
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(code_dlg.accept)
        buttons_layout.addWidget(btn_close)
        
        code_layout.addLayout(buttons_layout)
        
        code_dlg.resize(700, 500)
        code_dlg.exec_()
    
    def _copy_to_clipboard(self, text):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text)
        QtWidgets.QMessageBox.information(self, "Copied", "Code copied to clipboard!")
    
    def _save_code_to_file(self, code):
        if hasattr(sys, 'frozen'):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        default_filename = os.path.join(script_dir, "overlay_generated.py")
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Python file",
            default_filename,
            "Python files (*.py);;All files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(code)
                QtWidgets.QMessageBox.information(
                    self,
                    "Saved",
                    f"Code saved to:\n{filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save file:\n{str(e)}"
                )
    
    def save_project(self):
        """Зберегти проект у JSON файл"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                self.canvas.save_project(filename)
                QtWidgets.QMessageBox.information(
                    self,
                    "Saved",
                    f"Project saved to:\n{filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save project:\n{str(e)}"
                )
    
    def load_project(self):
        """Завантажити проект з JSON файлу"""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Project",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                self.canvas.load_project(filename)
                QtWidgets.QMessageBox.information(
                    self,
                    "Loaded",
                    f"Project loaded from:\n{filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load project:\n{str(e)}"
                )

