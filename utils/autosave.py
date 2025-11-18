"""
Автозбереження сесії
"""
import os
import json
from datetime import datetime
from PyQt5 import QtCore


class AutoSaveManager(QtCore.QObject):
    """Менеджер для автоматичного збереження сесії"""
    
    def __init__(self, canvas_widget, parent=None):
        super().__init__(parent)
        self.canvas = canvas_widget
        self.autosave_enabled = True
        self.autosave_interval = 60000  # 60 секунд
        self.autosave_file = self._get_autosave_path()
        
        # Таймер для автозбереження
        self.autosave_timer = QtCore.QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        
        if self.autosave_enabled:
            self.autosave_timer.start(self.autosave_interval)
    
    def _get_autosave_path(self):
        """Отримати шлях до файлу автозбереження"""
        # Зберігаємо в temp директорії
        temp_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.TempLocation)
        return os.path.join(temp_dir, 'opencv_hud_editor_autosave.json')
    
    def autosave(self):
        """Автоматично зберегти поточну сесію"""
        if not self.autosave_enabled:
            return
        
        try:
            # Використовуємо ProjectIO для збереження
            from export.project_io import ProjectIO
            
            # Зберігаємо з міткою часу
            ProjectIO.save_project(
                self.canvas.shape_manager.shapes,
                self.autosave_file,
                self.canvas.group_manager
            )
            
            print(f"[AutoSave] Session saved at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"[AutoSave] Error: {e}")
    
    def has_autosave(self):
        """Чи є файл автозбереження"""
        return os.path.exists(self.autosave_file)
    
    def load_autosave(self):
        """Завантажити автозбереження"""
        if not self.has_autosave():
            return False
        
        try:
            from export.project_io import ProjectIO
            
            shapes, groups_data = ProjectIO.load_project(self.autosave_file)
            self.canvas.shape_manager.shapes = shapes
            self.canvas.selection_manager.clear_selection()
            
            if groups_data:
                self.canvas.group_manager.from_dict(groups_data)
            else:
                self.canvas.group_manager.clear_all()
            
            self.canvas.update()
            print(f"[AutoSave] Session restored")
            return True
        except Exception as e:
            print(f"[AutoSave] Error loading: {e}")
            return False
    
    def clear_autosave(self):
        """Видалити файл автозбереження"""
        if self.has_autosave():
            try:
                os.remove(self.autosave_file)
                print("[AutoSave] Autosave file cleared")
            except Exception as e:
                print(f"[AutoSave] Error clearing: {e}")
    
    def get_autosave_info(self):
        """Отримати інформацію про автозбереження"""
        if not self.has_autosave():
            return None
        
        try:
            stat = os.stat(self.autosave_file)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Читаємо кількість фігур
            with open(self.autosave_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                num_shapes = len(data.get('shapes', []))
                num_groups = len(data.get('groups', {}).get('groups', []))
            
            return {
                'file': self.autosave_file,
                'modified': modified_time,
                'shapes': num_shapes,
                'groups': num_groups
            }
        except Exception as e:
            print(f"[AutoSave] Error getting info: {e}")
            return None
    
    def set_enabled(self, enabled):
        """Увімкнути/вимкнути автозбереження"""
        self.autosave_enabled = enabled
        if enabled:
            self.autosave_timer.start(self.autosave_interval)
        else:
            self.autosave_timer.stop()
    
    def set_interval(self, seconds):
        """Встановити інтервал автозбереження"""
        self.autosave_interval = seconds * 1000
        if self.autosave_enabled:
            self.autosave_timer.stop()
            self.autosave_timer.start(self.autosave_interval)

