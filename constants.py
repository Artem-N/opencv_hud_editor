"""
Константи для редактора OpenCV HUD
"""

# Пресети кольорів BGR
COLOR_PRESETS = {
    'Green': (0, 255, 0),
    'Red': (0, 0, 255),
    'Blue': (255, 0, 0),
    'Cyan': (255, 255, 0),
    'Yellow': (0, 255, 255),
    'Magenta': (255, 0, 255),
    'White': (255, 255, 255),
    'Black': (0, 0, 0),
    'Orange': (0, 165, 255),
    'Purple': (128, 0, 128),
}

# Пресети стилів
STYLE_PRESETS = ['default', 'horizontal', 'vertical', 'accent']

# Маппінг BGR кольорів на назви для експорту
COLOR_MAP = {
    (0, 255, 0): 'green',
    (0, 0, 255): 'red',
    (255, 0, 0): 'blue',
    (255, 255, 0): 'cyan',
    (0, 255, 255): 'yellow',
    (255, 0, 255): 'magenta',
    (255, 255, 255): 'white',
    (0, 0, 0): 'black',
    (0, 165, 255): 'orange',
    (128, 0, 128): 'purple',
}

