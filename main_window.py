"""
Головне вікно додатку
"""
import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore

from canvas_widget import CanvasWidget
from constants import COLOR_PRESETS, STYLE_PRESETS
from ui_group_panel import GroupPanel


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV HUD Editor")
        self.resize(800, 600)
        
        # Встановлюємо політику фокусу для прийому клавіатурних подій
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.canvas = CanvasWidget()
        self.setCentralWidget(self.canvas)

        # Створюємо панель груп
        self.group_panel = GroupPanel(self.canvas, self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.group_panel)
        self.group_panel.group_changed.connect(self.on_group_changed)

        self._build_ui()
        
        # Перевіряємо чи є автозбереження
        self._check_autosave()
    
    def _create_menu(self):
        """Створити меню"""
        menubar = self.menuBar()
        
        # Меню File
        file_menu = menubar.addMenu("&File")
        
        save_action = QtWidgets.QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save project to JSON file")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        load_action = QtWidgets.QAction("&Open Project", self)
        load_action.setShortcut("Ctrl+O")
        load_action.setStatusTip("Load project from JSON file")
        load_action.triggered.connect(self.load_project)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        export_action = QtWidgets.QAction("&Export Code...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export to OpenCV Python code")
        export_action.triggered.connect(self.export_code)
        file_menu.addAction(export_action)
        
        preview_action = QtWidgets.QAction("&Test on Camera...", self)
        preview_action.setShortcut("Ctrl+T")
        preview_action.setStatusTip("Test HUD overlay on camera video")
        preview_action.triggered.connect(self.show_camera_preview)
        file_menu.addAction(preview_action)
        
        file_menu.addSeparator()
        
        exit_action = QtWidgets.QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Edit
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QtWidgets.QAction("&Undo", self)
        undo_action.setShortcut("Z")
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self.canvas.undo)
        edit_menu.addAction(undo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QtWidgets.QAction("&Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setStatusTip("Copy selected shapes")
        copy_action.triggered.connect(self.canvas.copy_selected)
        edit_menu.addAction(copy_action)
        
        paste_action = QtWidgets.QAction("&Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setStatusTip("Paste shapes from clipboard")
        paste_action.triggered.connect(self.canvas.paste)
        edit_menu.addAction(paste_action)
        
        delete_action = QtWidgets.QAction("&Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.setStatusTip("Delete selected shapes")
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        flip_h_action = QtWidgets.QAction("Flip &Horizontal", self)
        flip_h_action.setStatusTip("Create mirrored copies horizontally (with gap)")
        flip_h_action.triggered.connect(self.canvas.flip_horizontal)
        edit_menu.addAction(flip_h_action)
        
        flip_v_action = QtWidgets.QAction("Flip &Vertical", self)
        flip_v_action.setStatusTip("Create mirrored copies vertically (with gap)")
        flip_v_action.triggered.connect(self.canvas.flip_vertical)
        edit_menu.addAction(flip_v_action)
        
        edit_menu.addSeparator()
        
        mirror_h_action = QtWidgets.QAction("Mirror Across &Vertical Axis", self)
        mirror_h_action.setShortcut("Shift+H")
        mirror_h_action.setStatusTip("Mirror shapes across vertical axis (canvas center)")
        mirror_h_action.triggered.connect(self.canvas.mirror_across_center_horizontal)
        edit_menu.addAction(mirror_h_action)
        
        mirror_v_action = QtWidgets.QAction("Mirror Across Hori&zontal Axis", self)
        mirror_v_action.setShortcut("Shift+V")
        mirror_v_action.setStatusTip("Mirror shapes across horizontal axis (canvas center)")
        mirror_v_action.triggered.connect(self.canvas.mirror_across_center_vertical)
        edit_menu.addAction(mirror_v_action)
        
        edit_menu.addSeparator()
        
        clear_action = QtWidgets.QAction("C&lear All", self)
        clear_action.setStatusTip("Clear all shapes")
        clear_action.triggered.connect(self.canvas.clear_all)
        edit_menu.addAction(clear_action)
        
        edit_menu.addSeparator()
        
        # Автозбереження
        autosave_action = QtWidgets.QAction("&AutoSave Settings...", self)
        autosave_action.setStatusTip("Configure autosave")
        autosave_action.triggered.connect(self.show_autosave_settings)
        edit_menu.addAction(autosave_action)
        
        # Меню View
        view_menu = menubar.addMenu("&View")
        
        reset_zoom_action = QtWidgets.QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("0")
        reset_zoom_action.setStatusTip("Reset zoom and pan to default")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        self.snap_action = QtWidgets.QAction("&Snap to Grid", self)
        self.snap_action.setShortcut("G")
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(False)
        self.snap_action.setStatusTip("Snap points to grid")
        self.snap_action.toggled.connect(self.on_snap_toggled)
        view_menu.addAction(self.snap_action)
        
        grid_size_action = QtWidgets.QAction("Grid &Size...", self)
        grid_size_action.setStatusTip("Change grid size")
        grid_size_action.triggered.connect(self.show_grid_size_dialog)
        view_menu.addAction(grid_size_action)
        
        view_menu.addSeparator()
        
        canvas_limits_action = QtWidgets.QAction("Canvas &Limits...", self)
        canvas_limits_action.setStatusTip("Set canvas size limits")
        canvas_limits_action.triggered.connect(self.show_canvas_limits_dialog)
        view_menu.addAction(canvas_limits_action)
        
        view_menu.addSeparator()
        
        show_groups_action = QtWidgets.QAction("Show &Groups Panel", self)
        show_groups_action.setCheckable(True)
        show_groups_action.setChecked(True)
        show_groups_action.toggled.connect(self.toggle_groups_panel)
        view_menu.addAction(show_groups_action)

    def _build_ui(self):
        # Створюємо меню
        self._create_menu()
        
        # Створюємо тулбар для основних інструментів
        toolbar = QtWidgets.QToolBar("Tools")
        toolbar.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addToolBar(toolbar)

        # Інструменти навігації та виділення
        btn_pan = QtWidgets.QAction("Pan (P)", self)
        btn_pan.setToolTip("Pan mode - move canvas with left mouse button")
        btn_pan.triggered.connect(self.canvas.set_mode_pan)
        toolbar.addAction(btn_pan)

        btn_select = QtWidgets.QAction("Select (S)", self)
        btn_select.setToolTip("Select and move shapes")
        btn_select.triggered.connect(self.canvas.set_mode_select)
        toolbar.addAction(btn_select)

        toolbar.addSeparator()

        # Інструменти малювання
        btn_line = QtWidgets.QAction("Line (L)", self)
        btn_line.setToolTip("Draw line")
        btn_line.triggered.connect(self.canvas.set_mode_line)
        toolbar.addAction(btn_line)

        btn_arrow = QtWidgets.QAction("Arrow (A)", self)
        btn_arrow.setToolTip("Draw arrow")
        btn_arrow.triggered.connect(self.canvas.set_mode_arrow)
        toolbar.addAction(btn_arrow)
        
        btn_rectangle = QtWidgets.QAction("Rectangle (R)", self)
        btn_rectangle.setToolTip("Draw rectangle")
        btn_rectangle.triggered.connect(self.canvas.set_mode_rectangle)
        toolbar.addAction(btn_rectangle)

        btn_circle = QtWidgets.QAction("Circle (C)", self)
        btn_circle.setToolTip("Draw circle")
        btn_circle.triggered.connect(self.canvas.set_mode_circle)
        toolbar.addAction(btn_circle)
        
        btn_ellipse = QtWidgets.QAction("Ellipse (E)", self)
        btn_ellipse.setToolTip("Draw ellipse")
        btn_ellipse.triggered.connect(self.canvas.set_mode_ellipse)
        toolbar.addAction(btn_ellipse)
        
        btn_polygon = QtWidgets.QAction("Polygon", self)
        btn_polygon.setToolTip("Draw polygon - click points, right-click to finish")
        btn_polygon.triggered.connect(self.canvas.set_mode_polygon)
        toolbar.addAction(btn_polygon)
        
        btn_point = QtWidgets.QAction("Point", self)
        btn_point.setToolTip("Place point")
        btn_point.triggered.connect(self.canvas.set_mode_point)
        toolbar.addAction(btn_point)

        btn_text = QtWidgets.QAction("Text (T)", self)
        btn_text.setToolTip("Add text")
        btn_text.triggered.connect(self.canvas.set_mode_text)
        toolbar.addAction(btn_text)

        toolbar.addSeparator()

        # Налаштування малювання
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
        
        # Довжина пунктира
        toolbar.addWidget(QtWidgets.QLabel("Dash:"))
        self.dash_length_spin = QtWidgets.QSpinBox()
        self.dash_length_spin.setMinimum(2)
        self.dash_length_spin.setMaximum(50)
        self.dash_length_spin.setValue(10)
        self.dash_length_spin.setToolTip("Dash length for dashed lines (in pixels)")
        self.dash_length_spin.valueChanged.connect(self.on_dash_length_changed)
        toolbar.addWidget(self.dash_length_spin)
        
        # Відстань між точками
        toolbar.addWidget(QtWidgets.QLabel("Dot:"))
        self.dot_length_spin = QtWidgets.QSpinBox()
        self.dot_length_spin.setMinimum(2)
        self.dot_length_spin.setMaximum(30)
        self.dot_length_spin.setValue(5)
        self.dot_length_spin.setToolTip("Dot spacing for dotted lines (in pixels)")
        self.dot_length_spin.valueChanged.connect(self.on_dot_length_changed)
        toolbar.addWidget(self.dot_length_spin)
        
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
    
    def toggle_groups_panel(self, checked: bool):
        """Показати/сховати панель груп"""
        if checked:
            self.group_panel.show()
        else:
            self.group_panel.hide()
    
    def on_group_changed(self):
        """Обробити зміни в групах"""
        # Можна додати додаткову логіку якщо потрібно
        pass
    
    def _check_autosave(self):
        """Перевірити наявність автозбереження"""
        autosave = self.canvas.autosave_manager
        
        if autosave.has_autosave():
            info = autosave.get_autosave_info()
            
            if info:
                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Question)
                msg.setWindowTitle("Restore Session")
                msg.setText("Found autosaved session!")
                msg.setInformativeText(
                    f"Last saved: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Shapes: {info['shapes']}\n"
                    f"Groups: {info['groups']}\n\n"
                    f"Do you want to restore it?"
                )
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
                
                reply = msg.exec_()
                
                if reply == QtWidgets.QMessageBox.Yes:
                    if autosave.load_autosave():
                        # Оновлюємо панель груп
                        if hasattr(self, 'group_panel'):
                            self.group_panel.refresh_groups()
                        
                        self.statusBar().showMessage("Session restored!", 3000)
                else:
                    # Якщо не відновлюємо, видаляємо автозбереження
                    autosave.clear_autosave()
    
    def show_autosave_settings(self):
        """Показати налаштування автозбереження"""
        autosave = self.canvas.autosave_manager
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("AutoSave Settings")
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Чекбокс для увімкнення/вимкнення
        enabled_checkbox = QtWidgets.QCheckBox("Enable AutoSave")
        enabled_checkbox.setChecked(autosave.autosave_enabled)
        layout.addWidget(enabled_checkbox)
        
        # Інтервал
        interval_layout = QtWidgets.QHBoxLayout()
        interval_layout.addWidget(QtWidgets.QLabel("Interval (seconds):"))
        interval_spin = QtWidgets.QSpinBox()
        interval_spin.setRange(10, 600)
        interval_spin.setValue(autosave.autosave_interval // 1000)
        interval_layout.addWidget(interval_spin)
        layout.addLayout(interval_layout)
        
        # Інфо про поточне автозбереження
        info_label = QtWidgets.QLabel()
        if autosave.has_autosave():
            info = autosave.get_autosave_info()
            if info:
                info_label.setText(
                    f"Current autosave:\n"
                    f"Location: {info['file']}\n"
                    f"Last saved: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Shapes: {info['shapes']}, Groups: {info['groups']}"
                )
        else:
            info_label.setText("No autosave file found")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Кнопки
        button_layout = QtWidgets.QHBoxLayout()
        
        btn_clear = QtWidgets.QPushButton("Clear AutoSave")
        btn_clear.clicked.connect(lambda: self._clear_autosave_and_update(autosave, info_label))
        button_layout.addWidget(btn_clear)
        
        btn_save = QtWidgets.QPushButton("Save Now")
        btn_save.clicked.connect(lambda: self._save_now_and_update(autosave, info_label))
        button_layout.addWidget(btn_save)
        
        layout.addLayout(button_layout)
        
        # OK/Cancel
        ok_cancel_layout = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        ok_cancel_layout.addWidget(btn_ok)
        ok_cancel_layout.addWidget(btn_cancel)
        layout.addLayout(ok_cancel_layout)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            autosave.set_enabled(enabled_checkbox.isChecked())
            autosave.set_interval(interval_spin.value())
            self.statusBar().showMessage("AutoSave settings updated", 2000)
    
    def _clear_autosave_and_update(self, autosave, label):
        """Очистити автозбереження та оновити label"""
        autosave.clear_autosave()
        label.setText("No autosave file found")
    
    def _save_now_and_update(self, autosave, label):
        """Зберегти зараз та оновити label"""
        autosave.autosave()
        if autosave.has_autosave():
            info = autosave.get_autosave_info()
            if info:
                label.setText(
                    f"Current autosave:\n"
                    f"Location: {info['file']}\n"
                    f"Last saved: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Shapes: {info['shapes']}, Groups: {info['groups']}"
                )
        self.statusBar().showMessage("Saved!", 2000)
    
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
    
    def on_dash_length_changed(self, value: int):
        """Обробник зміни довжини пунктира"""
        self.canvas.set_dash_length(value)
        # Якщо є вибрані фігури - змінюємо їх довжину пунктира
        self._apply_to_selected_shapes('dash_length', value)
    
    def on_dot_length_changed(self, value: int):
        """Обробник зміни відстані між точками"""
        self.canvas.set_dot_length(value)
        # Якщо є вибрані фігури - змінюємо їх відстань між точками
        self._apply_to_selected_shapes('dot_length', value)
    
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
                elif property_name == 'dash_length':
                    shape.dash_length = value
                    changed = True
                elif property_name == 'dot_length':
                    shape.dot_length = value
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
            # Ctrl+T для тестування на камері
            elif key == QtCore.Qt.Key_T or text in ['T', 'Е']:
                self.show_camera_preview()
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
        
        # Перевіряємо чи встановлені межі полотна
        limits = self.canvas.get_canvas_limits()
        
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
        
        # Показуємо інформацію про розмір
        if limits['enabled']:
            info_label = QtWidgets.QLabel(
                f"Canvas size limits: {limits['width']} x {limits['height']} px (enabled)\n"
                f"Export will use these dimensions."
            )
            info_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            info_label = QtWidgets.QLabel(
                f"Canvas size: {canvas_width} x {canvas_height} px\n"
                f"No size limits set. You can set them in View → Canvas Limits."
            )
            info_label.setStyleSheet("color: gray;")
        info_label.setWordWrap(True)
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
    
    def show_canvas_limits_dialog(self):
        """Показати діалог налаштувань розміру полотна"""
        limits = self.canvas.get_canvas_limits()
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Canvas Size Limits")
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Інформація
        info_label = QtWidgets.QLabel(
            "Встановіть обмеження розміру полотна для малювання.\n"
            "Це корисно, коли ви малюєте HUD для відео певної роздільності."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Чекбокс для увімкнення/вимкнення
        enabled_checkbox = QtWidgets.QCheckBox("Увімкнути обмеження розміру полотна")
        enabled_checkbox.setChecked(limits['enabled'])
        layout.addWidget(enabled_checkbox)
        
        layout.addSpacing(10)
        
        # Швидкий вибір роздільності
        preset_group = QtWidgets.QGroupBox("Стандартні роздільності")
        preset_layout = QtWidgets.QVBoxLayout()
        
        presets = [
            ("1920 x 1080 (Full HD)", 1920, 1080),
            ("1280 x 720 (HD)", 1280, 720),
            ("1600 x 900", 1600, 900),
            ("2560 x 1440 (2K)", 2560, 1440),
            ("3840 x 2160 (4K)", 3840, 2160),
        ]
        
        for label, w, h in presets:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda checked, width=w, height=h: self._set_preset_size(width, height, width_spin, height_spin))
            preset_layout.addWidget(btn)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        layout.addSpacing(10)
        
        # Власні розміри
        custom_group = QtWidgets.QGroupBox("Власна роздільність")
        custom_layout = QtWidgets.QFormLayout()
        
        width_spin = QtWidgets.QSpinBox()
        width_spin.setRange(100, 10000)
        width_spin.setValue(limits['width'])
        custom_layout.addRow("Ширина:", width_spin)
        
        height_spin = QtWidgets.QSpinBox()
        height_spin.setRange(100, 10000)
        height_spin.setValue(limits['height'])
        custom_layout.addRow("Висота:", height_spin)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        layout.addSpacing(10)
        
        # Кнопки OK/Cancel
        button_layout = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        button_layout.addWidget(btn_ok)
        button_layout.addWidget(btn_cancel)
        layout.addLayout(button_layout)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.canvas.set_canvas_limits(
                enabled_checkbox.isChecked(),
                width_spin.value(),
                height_spin.value()
            )
            self.statusBar().showMessage(
                f"Canvas limits: {'enabled' if enabled_checkbox.isChecked() else 'disabled'} "
                f"({width_spin.value()}x{height_spin.value()})", 
                3000
            )
    
    def _set_preset_size(self, width, height, width_spin, height_spin):
        """Встановити розмір з пресету"""
        width_spin.setValue(width)
        height_spin.setValue(height)
    
    def show_grid_size_dialog(self):
        """Показати діалог налаштування розміру сітки"""
        current_size = self.canvas.get_grid_size()
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Grid Size Settings")
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Інформація
        info_label = QtWidgets.QLabel(
            "Оберіть розмір сітки для малювання.\n"
            "Менший розмір = точніше малювання, але більше ліній.\n"
            "Більший розмір = швидше, але менш точно."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Пресети розміру сітки
        presets_group = QtWidgets.QGroupBox("Швидкий вибір")
        presets_layout = QtWidgets.QVBoxLayout()
        
        grid_presets = [
            ("5 пікселів (дуже точно)", 5),
            ("10 пікселів (точно) - рекомендовано", 10),
            ("20 пікселів (стандарт)", 20),
            ("50 пікселів (грубо)", 50),
        ]
        
        for label, size in grid_presets:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda checked, s=size: self._apply_grid_size(s, dialog))
            if size == current_size:
                btn.setStyleSheet("background-color: #4CAF50; color: white;")
            presets_layout.addWidget(btn)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        layout.addSpacing(10)
        
        # Поточний розмір
        current_label = QtWidgets.QLabel(f"Поточний розмір: {current_size} пікселів")
        current_label.setStyleSheet("color: gray;")
        layout.addWidget(current_label)
        
        # Кнопка Close
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec_()
    
    def _apply_grid_size(self, size, dialog):
        """Застосувати розмір сітки"""
        self.canvas.set_grid_size(size)
        self.statusBar().showMessage(f"Grid size set to {size}px", 2000)
        dialog.accept()
    
    def show_camera_preview(self):
        """Показати попередній перегляд на камері"""
        # Перевіряємо чи є фігури для відображення
        if not self.canvas.shapes:
            QtWidgets.QMessageBox.information(
                self,
                "No Shapes",
                "Please draw some shapes before testing on camera."
            )
            return
        
        # Імпортуємо модуль перегляду
        from preview_camera import CameraPreviewWindow
        
        # Створюємо і показуємо вікно
        preview_window = CameraPreviewWindow(self.canvas, self)
        preview_window.exec_()

