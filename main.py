import math
import logging
import arcade
import pymunk
import random

from game_object import RedBird, BlueBird, ChuckBird, BombBird, Column, Pig
from game_logic import get_impulse_vector, Point2D, get_distance, ImpulseVector

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900
POINTS_PER_PIG = 500
MAX_ATTEMPTS = 5
HUD_COLOR = arcade.color.BLACK


class App(arcade.View):  # pantalla principal del juego
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")

        # crear espacio de pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)

        # agregar piso
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()
        self.add_columns()
        self.add_pigs()

        # agregar un collision handler
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler



        self.score = 0
        self.attempts_left = MAX_ATTEMPTS
        self.font_size = 24
        self.score_text = arcade.Text(
            text=f"Score: {self.score}", x=20, y=HEIGHT - 40,
            color=HUD_COLOR, font_size=self.font_size, font_name="Arial"
        )
        self.attempts_text = arcade.Text(
            text=f"Attempts: {self.attempts_left}", x=20, y=HEIGHT - 80,
            color=HUD_COLOR, font_size=self.font_size, font_name="Arial"
        )

        self.bird_queue = []  # Cola de pájaros disponibles
        self.current_bird_index = 0
        self.init_bird_queue()
        self.active_bird = None
        self.preview_bird = None

        self.slingshot_pos = Point2D(300, 80)  #izq
        self.preview_pos = Point2D(230, 140)  #pajaro previo
        self.start_point = self.slingshot_pos  
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False
        self.slingshot_texture = arcade.load_texture("assets/img/sling-3.png")
        self.update_preview_bird()

        self.birds_to_remove = {}

        self.game_over = False
        self.won = False
        self.result_text = None
        self.result_sprite = None

    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        if impulse_norm > 800:
            for obj in list(self.world):
                if obj.shape in arbiter.shapes:
                    if isinstance(obj, Pig):
                        self.score += POINTS_PER_PIG
                        self.score_text.text = f"Score: {self.score}"
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)
        return True

    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig_positions = [
            (WIDTH / 2, 100),
            (WIDTH / 2 + 200, 100),
            (WIDTH / 2 + 400, 100),
            (WIDTH / 2 + 300, 200),
        ]
        for x, y in pig_positions:
            pig = Pig(x, y, self.space)
            self.sprites.append(pig)
            self.world.append(pig)

    def on_update(self, delta_time: float):
        if self.game_over:
            return
        self.space.step(1 / 60.0)
        self.update_collisions()
        self.sprites.update(delta_time)
        self._check_end_conditions()
    
        for sprite in self.sprites:
            if hasattr(sprite, 'body'):
                sprite.center_x = sprite.body.position.x
                sprite.center_y = sprite.body.position.y
                if hasattr(sprite, 'shape') and hasattr(sprite.shape, 'body'):
                    sprite.angle = math.degrees(sprite.body.angle)
    
        for bird in self.birds:
        # Verificar si el pájaro está muy abajo (tocó el piso)
            if hasattr(bird, 'body') and bird.body.position.y <= 30:
                if bird not in self.birds_to_remove:
                    logger.debug(f"Bird touched ground, will remove in 2 seconds: {bird.body.position}")
                    self.birds_to_remove[bird] = 0.0
                else:
                    # Actualizar el tiempo acumulado para este pájaro
                    self.birds_to_remove[bird] += delta_time

        # Lista temporal para pájaros que deben ser eliminados (ya pasaron 2 segundos)
        birds_to_remove_now = []

        for bird, elapsed_time in list(self.birds_to_remove.items()):
            if elapsed_time >= 2.0:  # 2 segundos han pasado
                birds_to_remove_now.append(bird)
                # Remover del diccionario de seguimiento
                del self.birds_to_remove[bird]

    # Eliminar pájaros que tocaron el piso
        for bird in birds_to_remove_now:
            logger.debug(f"Removing bird at position: {bird.body.position if hasattr(bird, 'body') else 'No body'}")
        
        # Remover de las listas de sprites
            if bird in self.sprites:
                self.sprites.remove(bird)
        
        # Remover de la lista de pájaros
            if bird in self.birds:
                self.birds.remove(bird)
        
        # Remover del espacio de física si tiene body y shape
            if hasattr(bird, 'body') and hasattr(bird, 'shape'):
                self.space.remove(bird.shape, bird.body)
        
        # Si era el pájaro activo, actualizar la vista previa
            if bird == self.active_bird:
                self.active_bird = None
                self.update_preview_bird()


    def update_collisions(self):
        pass

    def _remaining_pigs(self):
        return [obj for obj in self.world if isinstance(obj, Pig)]

    def _check_end_conditions(self):
        pigs = self._remaining_pigs()
        if len(pigs) == 0:
            self._finish_game(won=True)
            return
        if self.attempts_left == 0 and len(self.birds) == 0 and len(pigs) > 0:
            self._finish_game(won=False)
    def _finish_game(self, won: bool):
        self.game_over = True
        self.won = won

    # Cargar la imagen correspondiente usando la ruta del archivo
        if won:
            texture_path = "assets/img/ganaste.png"
        else:
            texture_path = "assets/img/perdiste.png"

    # Escala ajustable
        scale = 0.5

        self.result_sprite = arcade.Sprite(
            texture_path,  # Pasar la ruta directamente
            scale=scale
        )
        
        self.result_sprite.center_x = (WIDTH / 2) - 150
        self.result_sprite.center_y = HEIGHT / 2


    def init_bird_queue(self):
        #pajaros aleatorios
        bird_types = [RedBird, BlueBird, ChuckBird, BombBird]
        self.bird_queue = random.choices(bird_types, k=5)  

    def get_next_bird(self):
        if self.current_bird_index >= len(self.bird_queue):
            self.init_bird_queue()  
            self.current_bird_index = 0

        bird_class = self.bird_queue[self.current_bird_index]
        self.current_bird_index += 1
        return bird_class
    def update_preview_bird(self):
        if self.preview_bird:
            self.preview_bird.remove_from_sprite_lists()
            self.preview_bird = None
            
        if self.current_bird_index < len(self.bird_queue):
            BirdClass = self.bird_queue[self.current_bird_index]
            self.preview_bird = BirdClass(
                ImpulseVector(0, 0), 
                self.slingshot_pos.x - 70,
                self.slingshot_pos.y + 100, 
                self.space
            )
            if hasattr(self.preview_bird, "body") and hasattr(self.preview_bird, "shape"):
                self.space.remove(self.preview_bird.shape, self.preview_bird.body)
            self.sprites.append(self.preview_bird)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_over or self.attempts_left <= 0:
            return
        if button == arcade.MOUSE_BUTTON_LEFT and self.preview_bird:
        
            
            self.active_bird = self.preview_bird
            self.preview_bird = None
            self.birds.append(self.active_bird)
            self.draw_line = True


    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if self.game_over:
            return
        if buttons == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.active_bird:
        # solo actualiza el punto final
            self.end_point = Point2D(x, y)


    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.game_over:
            return
        if button == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.active_bird:
            self.draw_line = False
            
            impulse_vector = get_impulse_vector(self.slingshot_pos, self.end_point)
            if hasattr(self.active_bird, "body") and hasattr(self.active_bird, "shape"):
                self.space.add(self.active_bird.body, self.active_bird.shape)
            # apply impulse
                self.active_bird.body.apply_impulse_at_local_point(
                    (impulse_vector.impulse * math.cos(impulse_vector.angle) * 50,
                    impulse_vector.impulse * math.sin(impulse_vector.angle) * 50)
                )
            self.active_bird = None
            self.update_preview_bird()
            self.attempts_left = max(0, self.attempts_left - 1)
            self.attempts_text.text = f"Attempts: {self.attempts_left}"
    def on_mouse_motion(self, x, y, dx, dy):
        if self.active_bird and self.draw_line:
        # Clamp dragging distance (optional, so bird can't go too far)
            max_pull = 120
            dx = x - self.slingshot_pos.x
            dy = y - (self.slingshot_pos.y + 150)  # use same anchor height
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist > max_pull:
                scale = max_pull / dist
                dx *= scale
                dy *= scale

        # update bird position while dragging
            self.active_bird.center_x = self.slingshot_pos.x + dx
            self.active_bird.center_y = (self.slingshot_pos.y + 150) + dy


    def on_key_press(self, key, modifiers):
        if self.game_over:
            return
        if key == arcade.key.SPACE:
            for bird in self.birds:
                if bird.has_special_ability and not bird.ability_used:
                    bird.use_special_ability(self.space, self.sprites)

    def draw_trajectory(self, start_point, impulse_vector):
        if self.active_bird:
            start_x = self.active_bird.center_x
            start_y = self.active_bird.center_y
        else:
            start_x = self.preview_bird.center_x if self.preview_bird else start_point.x
            start_y = self.preview_bird.center_y if self.preview_bird else start_point.y

        power_multiplier = 50 
        velocity = impulse_vector.impulse * power_multiplier

        v_x = math.cos(impulse_vector.angle) * velocity / 5
        v_y = math.sin(impulse_vector.angle) * velocity / 5

        g = GRAVITY
        num_points = 50
        time_step = 0.1

        for i in range(num_points):
            t = i * time_step
            x = start_x + v_x * t
            y = start_y + v_y * t + 0.5 * g * (t ** 2) * (1 / 60)
            arcade.draw_circle_filled(x, y, 3, arcade.color.GRAY)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, WIDTH, HEIGHT),
        )
        # resorte
        scale = 1.8
        arcade.draw_texture_rect(
            self.slingshot_texture,
            arcade.XYWH(
                self.slingshot_pos.x,
                self.slingshot_pos.y,
                self.slingshot_texture.width * scale,
                self.slingshot_texture.height * scale,
            ),
        )

        # Sprites del mundo
        self.sprites.draw()
        self.score_text.draw()
        self.attempts_text.draw()

        # Línea de apuntado + punto final y trayectoria
        if self.draw_line:
            left_band = (self.slingshot_pos.x - 15, self.slingshot_pos.y + 150)
            right_band = (self.slingshot_pos.x -150, self.slingshot_pos.y + 150)

            arcade.draw_line(
                left_band[0], left_band[1],
                self.end_point.x, self.end_point.y,
                arcade.color.DARK_BROWN, 6
            )
            arcade.draw_line(
                right_band[0], right_band[1],
                self.end_point.x, self.end_point.y,
                arcade.color.DARK_BROWN, 6
            )
             # Punto final

            arcade.draw_circle_filled(
                self.end_point.x, self.end_point.y,
                8, arcade.color.RED
            )
            impulse_vector = get_impulse_vector(self.slingshot_pos, self.end_point)
            self.draw_trajectory(self.slingshot_pos, impulse_vector)
        if self.game_over and self.result_sprite:
            arcade.draw_sprite(self.result_sprite)



def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()

