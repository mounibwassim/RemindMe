from kivymd.uix.card import MDCard
from kivy.metrics import dp

class ClickableCard(MDCard):
    """
    A stable alternative to (ButtonBehavior, MDCard) which causes MRO errors.
    Uses manual touch handling to dispatch 'on_release'.
    """
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        super().__init__(**kwargs)
        self.ripple_behavior = True

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Check if any child button/widget consumes the touch FIRST
            if super().on_touch_down(touch):
                return True
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.collide_point(*touch.pos):
                self.dispatch('on_release')
            return True
        return super().on_touch_up(touch)

    def on_release(self, *args):
        pass
