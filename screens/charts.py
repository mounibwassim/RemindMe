from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, SmoothLine, Quad, Mesh
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ListProperty, StringProperty, NumericProperty
from kivy.metrics import dp
from math import cos, sin, pi

class ModernLineChart(Widget):
    data_sets = ListProperty([]) # List of dicts: {'color': (r,g,b,a), 'values': [y1, y2, ...], 'label': 'Name'}
    labels = ListProperty([]) # X-axis labels
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, data_sets=self.update_canvas)
        
    def update_canvas(self, *args):
        try:
            self.canvas.clear()
            self.canvas.after.clear()
            
            if not self.data_sets:
                return
                
            # Dimensions
            x, y = self.pos
            w, h = self.size
            padding = dp(30)
            chart_w = w - 2 * padding
            chart_h = h - 2 * padding
            chart_x = x + padding
            chart_y = y + padding
            
            # Find max value for scaling
            all_values = [v for ds in self.data_sets for v in ds['values']]
            max_val = max(all_values) if all_values else 10
            if max_val == 0: max_val = 10 # Prevent division by zero
            # Round up to nice number
            max_val = ((int(max_val) // 5) + 1) * 5
            
            # Draw Grid
            with self.canvas:
                Color(1, 1, 1, 0.1)
                # Horizontal lines
                steps = 5
                for i in range(steps + 1):
                    ly = chart_y + (chart_h / steps) * i
                    Line(points=[chart_x, ly, chart_x + chart_w, ly], width=1)
                    
            # Draw Lines
            num_points = len(self.labels)
            if num_points < 2: return
            
            step_x = chart_w / (num_points - 1)
            
            with self.canvas:
                for ds in self.data_sets:
                    color = ds.get('color', (1, 1, 1, 1))
                    values = ds['values']
                    
                    points = []
                    for i, val in enumerate(values):
                        px = chart_x + i * step_x
                        py = chart_y + (val / max_val) * chart_h
                        points.extend([px, py])
                        
                        # Draw dot
                        Color(*color)
                        Ellipse(pos=(px - dp(3), py - dp(3)), size=(dp(6), dp(6)))
                        
                    # Draw smooth line
                    Color(*color)
                    Line(points=points, width=2)
        except Exception as e:
            print(f"Error drawing ModernLineChart: {e}")

class DonutChart(Widget):
    slices = ListProperty([]) # [{'value': 10, 'color': (1,0,0,1), 'label': 'A'}, ...]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, slices=self.update_canvas)
        
    def update_canvas(self, *args):
        try:
            self.canvas.clear()
            
            if not self.slices:
                return
                
            total = sum([s['value'] for s in self.slices])
            if total == 0: return # Prevent division by zero
            
            angle_start = 0
            center_x, center_y = self.center
            radius = min(self.size) / 2
            thickness = dp(15)
            
            with self.canvas:
                for s in self.slices:
                    val = s['value']
                    angle_sweep = (val / total) * 360
                    angle_end = angle_start + angle_sweep
                    
                    Color(*s['color'])
                    # Simple Arc using Line
                    Line(circle=(center_x, center_y, radius - thickness/2, angle_start, angle_end), width=thickness, cap='none')
                    
                    angle_start = angle_end
        except Exception as e:
            print(f"Error drawing DonutChart: {e}")
