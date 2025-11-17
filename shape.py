"""
Клас для зберігання даних про фігури
"""


class Shape:
    def __init__(self, kind, color_bgr=(0, 255, 0), thickness=2, style='default', 
                 line_style='solid', text='', font_scale=1.0, filled=False, **coords):
        """
        Клас для представлення фігури
        
        Args:
            kind: тип фігури ('line', 'circle', 'text', 'point', 'polygon', 'rectangle', 'arrow', 'ellipse', 'curve')
            color_bgr: колір у форматі BGR (tuple)
            thickness: товщина лінії
            style: стиль фігури ('default', 'horizontal', 'vertical', 'accent')
            line_style: стиль лінії ('solid', 'dashed', 'dotted')
            text: текст для kind='text'
            font_scale: розмір шрифту для тексту
            filled: чи заповнена фігура (для кіл, прямокутників, полігонів)
            **coords: координати фігури:
                - line: x1,y1,x2,y2
                - circle: cx,cy,r
                - text: x,y
                - point: x,y
                - polygon: points (list of tuples)
                - rectangle: x1,y1,x2,y2
                - arrow: x1,y1,x2,y2
                - ellipse: cx,cy,rx,ry,angle
                - curve: x1,y1,x2,y2,cx,cy (квадратична крива Безьє)
        """
        self.kind = kind
        self.color_bgr = color_bgr
        self.thickness = thickness
        self.style = style
        self.line_style = line_style
        self.text = text
        self.font_scale = font_scale
        self.filled = filled
        self.coords = coords

