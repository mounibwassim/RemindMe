from kivy.graphics import Rectangle, Color, Ellipse
from kivy.graphics.texture import Texture
from kivymd.uix.screen import MDScreen
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.metrics import dp

from utils.ui_components import ClickableCard

class WelcomeScreen(MDScreen):
    # ... (rest of class)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
        
    def build_ui(self):
        # 1. Background Gradient & Orbs (The "Blue Atmosphere")
        self.bg_layout = MDFloatLayout()
        with self.bg_layout.canvas.before:
            # Gradient Canvas
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.bg_layout.size, pos=self.bg_layout.pos)
            
            # Orbs (Soft decoration)
            Color(1, 1, 1, 0.1) # Soft White
            self.orb1 = Ellipse(size=(dp(250), dp(250)), pos=(400, 600))
            
            Color(1, 1, 1, 0.05)
            self.orb2 = Ellipse(size=(dp(350), dp(350)), pos=(-100, -100))
            
        self.bg_layout.bind(size=self._update_bg, pos=self._update_bg)
        self._create_gradient()
        self.add_widget(self.bg_layout)
        
        # 2. Main Glass Card (The "Container")
        glass_card = MDCard(
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            radius=[40],
            md_bg_color=(1, 1, 1, 0.08), 
            line_color=(1, 1, 1, 0.5),   
            line_width=dp(1.2),
            elevation=0,
            padding=dp(24),
            orientation='vertical'
        )
        
        # Main content container for professional vertical hierarchy
        content_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10), # Tighter spacing for text
            size_hint=(1, 1) # Ensure it fills the card
        )

        # 1. TITLE (Centered, Top)
        title = MDLabel(
            text="RemindMe",
            halign="center",
            font_style="H3", # Larger Title
            bold=True,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(60) 
        )
        content_box.add_widget(title)
        
        # 2. SUBTITLE
        subtitle = MDLabel(
            text="Secure & Smart Task Management",
            halign="center",
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=(0.9, 0.9, 0.9, 1), 
            size_hint_y=None,
            height=dp(30)
        )
        content_box.add_widget(subtitle)
        
        # 3. HERO IMAGE CONTAINER (Dominant Section)
        # Using 70% of available space for the illustration
        image_container = MDBoxLayout(
            size_hint=(1, 0.7),
            padding=0, # No padding to maximize size
            pos_hint={"center_x": 0.5}
        )
        
        design_image = Image(
            source="assets/hero_robot.png",
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
            pos_hint={"center_x": 0.5}
        )
        image_container.add_widget(design_image)
        content_box.add_widget(image_container)

        # 4. ACTION BUTTON (Get Started)
        btn_wrapper = MDBoxLayout(
            size_hint=(1, None),
            height=dp(80),
            pos_hint={"center_x": 0.5}
        )
        
        btn = ClickableCard(
            size_hint=(None, None),
            size=(dp(260), dp(56)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            radius=[28], 
            elevation=0, 
            md_bg_color=(0.53, 0.81, 0.92, 1), 
            on_release=self.go_to_login,
        )
        
        btn_label = MDLabel(
            text="GET STARTED",
            halign="center",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            bold=True,
            font_style="H6"
        )
        btn.add_widget(btn_label)
        btn_wrapper.add_widget(btn)
        
        content_box.add_widget(btn_wrapper)
        
        # Extra safety bottom spacer
        content_box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        
        # VERSION BADGE
        version_label = MDLabel(
            text="v1.0.2",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.5),
            size_hint_y=None,
            height=dp(20)
        )
        content_box.add_widget(version_label)
        
        glass_card.add_widget(content_box)
        self.add_widget(glass_card)

    def _update_bg(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        # Responsive Orbs
        self.orb1.pos = (instance.width * 0.75, instance.height * 0.75)
        self.orb2.pos = (-instance.width * 0.1, -instance.width * 0.1)

    def _create_gradient(self):
        # Vertical Gradient: Sky Blue -> Dodger Blue
        texture = Texture.create(size=(1, 2), colorfmt='rgba')
        c1 = [135, 206, 235, 255] # Sky
        c2 = [30, 144, 255, 255]  # Deep
        buf = bytes(c2 + c1)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        self.rect.texture = texture
        
    def go_to_login(self, instance):
        from kivy.app import App
        App.get_running_app().switch_screen('login')

    def on_enter(self):
        pass
