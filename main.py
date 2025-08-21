import math
import logging
import arcade
import pymunk

from game_object import Bird, Column, Pig
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

POINTS_PER_PIG = 500
MAX_ATTEMPTS = 5
HUD_COLOR = arcade.color.BLACK
WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900
MIN_DRAG = 0  

class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")

        # ---- Física
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()   # Columns + Pigs para colisiones

        self.add_columns()
        self.add_pigs()

        # ---- Lanzamiento
        self.start_point = Point2D()
        self.end_point = Point2D()
        self.draw_line = False

        # ---- Colisiones
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler

        # ---- HUD
        self.score = 0
        self.attempts_left = MAX_ATTEMPTS
        self.font_size = 24
        self.score_text = arcade.Text(
            text=f"Score: {self.score}",
            x=20, y=HEIGHT - 40,
            color=HUD_COLOR,
            font_size=self.font_size,
            font_name="Arial",
        )
        self.attempts_text = arcade.Text(
            text=f"Attempts: {self.attempts_left}",
            x=20, y=HEIGHT - 80,
            color=HUD_COLOR,
            font_size=self.font_size,
            font_name="Arial",
        )

    # ---- Colisiones fuertes: eliminar objetos; sumar puntos si era Pig
    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True  # ignora rozes leves

        logger.debug(f"Impulse: {impulse_norm}")

        if impulse_norm > 800:  # umbral moderado para pruebas
            removed_any = False
            for obj in list(self.world):  # iterar copia; vamos a eliminar
                if obj.shape in arbiter.shapes:
                    if isinstance(obj, Pig):
                        self.score += POINTS_PER_PIG
                        self.score_text.text = f"Score: {self.score}"
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)
                    removed_any = True
            return True

        return True

    # ---- Construcción del mundo
    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig1 = Pig(WIDTH / 2, 100, self.space)
        self.sprites.append(pig1)
        self.world.append(pig1)

    # ---- Loop
    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.sprites.update(delta_time)

    # ---- Input
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.start_point = Point2D(x, y)
            self.end_point = Point2D(x, y)
            self.draw_line = True
            logger.debug(f"Start Point: {self.start_point}")

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        logger.debug(f"Releasing from: {self.end_point}")
        self.draw_line = False

        # sin intentos -> no lanza
        if self.attempts_left <= 0:
            return

        # permite clic sin arrastrar; si quisieras exigir arrastre, sube MIN_DRAG
        if get_distance(self.start_point, self.end_point) < MIN_DRAG:
            # Opcional: podrías lanzar con un impulso mínimo
            # pass
            return

        impulse_vector = get_impulse_vector(self.start_point, self.end_point)
        bird = Bird("assets/img/red-bird3.png", impulse_vector, x, y, self.space)
        self.sprites.append(bird)
        self.birds.append(bird)
        logger.debug("Bird spawned!")

        # bajar intento y refrescar HUD
        self.attempts_left = max(0, self.attempts_left - 1)
        self.attempts_text.text = f"Attempts: {self.attempts_left}"

    # ---- Render
    def on_draw(self):
        self.clear()
        # Fondo en Arcade 2.6.x: draw_texture_rect(texture, LRBT)
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))

        # Mundo y pájaros
        self.sprites.draw()

        # HUD
        self.score_text.draw()
        self.attempts_text.draw()

        # Línea de lanzamiento
        if self.draw_line:
            arcade.draw_line(self.start_point.x, self.start_point.y,
                             self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()