"""
UI панель для управління групами фігур
"""
from PyQt5 import QtWidgets, QtCore, QtGui


class GroupPanel(QtWidgets.QDockWidget):
    """Панель для управління групами фігур"""
    
    group_changed = QtCore.pyqtSignal()  # Сигнал коли змінюється щось в групах
    
    def __init__(self, canvas_widget, parent=None):
        super().__init__("Groups", parent)
        self.canvas = canvas_widget
        
        # Основний widget
        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(main_widget)
        
        # Кнопка створення нової групи
        btn_new_group = QtWidgets.QPushButton("➕ Create New Group")
        btn_new_group.clicked.connect(self.create_new_group)
        layout.addWidget(btn_new_group)
        
        # Список груп
        self.group_list = QtWidgets.QListWidget()
        self.group_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.group_list.itemSelectionChanged.connect(self.on_group_selection_changed)
        layout.addWidget(self.group_list)
        
        # Кнопки управління
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.btn_add_to_group = QtWidgets.QPushButton("Add Selected")
        self.btn_add_to_group.setToolTip("Add selected shapes to this group")
        self.btn_add_to_group.clicked.connect(self.add_selected_to_group)
        btn_layout.addWidget(self.btn_add_to_group)
        
        self.btn_remove_from_group = QtWidgets.QPushButton("Remove")
        self.btn_remove_from_group.setToolTip("Remove selected shapes from this group")
        self.btn_remove_from_group.clicked.connect(self.remove_selected_from_group)
        btn_layout.addWidget(self.btn_remove_from_group)
        
        layout.addLayout(btn_layout)
        
        # Кнопки видалення та перейменування
        btn_layout2 = QtWidgets.QHBoxLayout()
        
        self.btn_rename = QtWidgets.QPushButton("Rename")
        self.btn_rename.clicked.connect(self.rename_group)
        btn_layout2.addWidget(self.btn_rename)
        
        self.btn_delete = QtWidgets.QPushButton("Delete Group")
        self.btn_delete.clicked.connect(self.delete_group)
        btn_layout2.addWidget(self.btn_delete)
        
        layout.addLayout(btn_layout2)
        
        # Інфо про групу
        self.info_label = QtWidgets.QLabel("No group selected")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.info_label)
        
        self.setWidget(main_widget)
        self.refresh_groups()
    
    def refresh_groups(self):
        """Оновити список груп"""
        self.group_list.clear()
        
        group_manager = self.canvas.group_manager
        for group in group_manager.groups:
            item = QtWidgets.QListWidgetItem(f"📁 {group.name} ({len(group.shape_indices)} shapes)")
            item.setData(QtCore.Qt.UserRole, group.name)
            self.group_list.addItem(item)
        
        # Оновлюємо інфо
        self.update_info()
    
    def create_new_group(self):
        """Створити нову групу"""
        # Запитуємо назву
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Create New Group",
            "Group name:",
            QtWidgets.QLineEdit.Normal,
            "Group"
        )
        
        if ok and name:
            # Створюємо групу з вибраними фігурами
            selected_indices = self.canvas.selection_manager.selected_shapes
            group = self.canvas.group_manager.create_group(name, selected_indices)
            
            self.refresh_groups()
            self.group_changed.emit()
            self.canvas.update()
            
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Group '{group.name}' created with {len(selected_indices)} shapes"
            )
    
    def on_group_selection_changed(self):
        """Обробити зміну виділення групи"""
        self.update_info()
    
    def get_selected_group_name(self):
        """Отримати назву вибраної групи"""
        selected_items = self.group_list.selectedItems()
        if selected_items:
            return selected_items[0].data(QtCore.Qt.UserRole)
        return None
    
    def add_selected_to_group(self):
        """Додати вибрані фігури до групи"""
        group_name = self.get_selected_group_name()
        if not group_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a group first")
            return
        
        selected_indices = self.canvas.selection_manager.selected_shapes
        if not selected_indices:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select shapes first")
            return
        
        self.canvas.group_manager.add_shapes_to_group(group_name, selected_indices)
        
        self.refresh_groups()
        self.group_changed.emit()
        self.canvas.update()
    
    def remove_selected_from_group(self):
        """Видалити вибрані фігури з групи"""
        group_name = self.get_selected_group_name()
        if not group_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a group first")
            return
        
        selected_indices = self.canvas.selection_manager.selected_shapes
        if not selected_indices:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select shapes first")
            return
        
        self.canvas.group_manager.remove_shapes_from_group(group_name, selected_indices)
        
        self.refresh_groups()
        self.group_changed.emit()
        self.canvas.update()
    
    def rename_group(self):
        """Перейменувати групу"""
        group_name = self.get_selected_group_name()
        if not group_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a group first")
            return
        
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Rename Group",
            "New name:",
            QtWidgets.QLineEdit.Normal,
            group_name
        )
        
        if ok and new_name and new_name != group_name:
            if self.canvas.group_manager.rename_group(group_name, new_name):
                self.refresh_groups()
                self.group_changed.emit()
                self.canvas.update()
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Error",
                    f"Cannot rename group: name '{new_name}' already exists"
                )
    
    def delete_group(self):
        """Видалити групу"""
        group_name = self.get_selected_group_name()
        if not group_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a group first")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete group '{group_name}'?\n(Shapes will not be deleted, only ungrouped)",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.canvas.group_manager.delete_group(group_name)
            self.refresh_groups()
            self.group_changed.emit()
            self.canvas.update()
    
    def update_info(self):
        """Оновити інформацію про вибрану групу"""
        group_name = self.get_selected_group_name()
        
        if not group_name:
            self.info_label.setText("No group selected")
            return
        
        group = self.canvas.group_manager.get_group_by_name(group_name)
        if group:
            info = f"<b>{group.name}</b><br>"
            info += f"Shapes: {len(group.shape_indices)}<br>"
            
            if group.shape_indices:
                info += f"Shape indices: {sorted(list(group.shape_indices))[:10]}"
                if len(group.shape_indices) > 10:
                    info += "..."
            
            self.info_label.setText(info)
        else:
            self.info_label.setText("Group not found")

