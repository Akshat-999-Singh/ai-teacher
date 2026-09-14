from manim import *

class TestScene(Scene):
    def construct(self):
        self.play(Write(MathTex(r"a^2 + b^2 = c^2")))
        self.wait()