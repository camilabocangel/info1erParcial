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

        self.bird_queue = []  # Cola de pájaros disponibles
        self.current_bird_index = 0
        self.init_bird_queue()

        self.active_bird = None
        self.preview_bird = None
        self.slingshot_pos = Point2D(300, 80)  # Posición fija a la izquierda
        self.preview_pos = Point2D(230, 140)  # Vista previa al lado de la resortera
        self.start_point = self.slingshot_pos  # El inicio siempre será el slingshot
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False
        self.slingshot_texture = arcade.load_texture("assets/img/sling-3.png")

        self.update_preview_bird()

        self.birds_to_remove = {}



    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        logger.debug(impulse_norm)
        if impulse_norm > 1200:
            for obj in self.world:
                if obj.shape in arbiter.shapes:
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)
        return True

    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig1 = Pig(WIDTH / 2, 100, self.space)
        self.sprites.append(pig1)
        self.world.append(pig1)

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.update_collisions()
    
    # Actualizar posiciones de sprites según Pymunk
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

    def init_bird_queue(self):
        """Inicializa la cola de pájaros de manera aleatoria"""
        bird_types = [RedBird, BlueBird, ChuckBird, BombBird]
        self.bird_queue = random.choices(bird_types, k=5)  # 5 pájaros aleatorios

    def get_next_bird(self):
        """Obtiene el siguiente pájaro de la cola"""
        if self.current_bird_index >= len(self.bird_queue):
            self.init_bird_queue()  # Recargar cola si se acaban
            self.current_bird_index = 0

        bird_class = self.bird_queue[self.current_bird_index]
        self.current_bird_index += 1
        return bird_class
    def update_preview_bird(self):
        """Actualiza el pájaro de vista previa con el siguiente de la cola"""
        if self.preview_bird:
            self.preview_bird.remove_from_sprite_lists()
            
        if self.current_bird_index < len(self.bird_queue):
            BirdClass = self.bird_queue[self.current_bird_index]
            # Crear un pájaro de vista previa (sin física)
            self.preview_bird = BirdClass(
                ImpulseVector(0, 0), 
                self.preview_pos.x,
                self.preview_pos.y, 
                self.space
            )
            # No queremos que el pájaro de vista previa tenga física
            if hasattr(self.preview_bird, "body") and hasattr(self.preview_bird, "shape"):
                self.space.remove(self.preview_bird.shape, self.preview_bird.body)
            self.sprites.append(self.preview_bird)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            scale = 1.8
            width = self.slingshot_texture.width * scale
            height = self.slingshot_texture.height * scale
            left = self.slingshot_pos.x - width / 2
            right = self.slingshot_pos.x + width / 2
            bottom = self.slingshot_pos.y - height / 2
            top = self.slingshot_pos.y + height / 2
            if left <= x <= right and bottom <= y <= top:
                self.end_point = Point2D(x, y)
                self.draw_line = True
                logger.debug("Start dragging from slingshot (click inside texture)")

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT and self.draw_line:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT and self.draw_line:
            logger.debug(f"Releasing from: {self.end_point}")
            self.draw_line = False

            impulse_vector = get_impulse_vector(self.slingshot_pos, self.end_point)
            BirdClass = self.get_next_bird()
            bird = BirdClass(impulse_vector, self.slingshot_pos.x, self.slingshot_pos.y, self.space)
            self.sprites.append(bird)
            self.birds.append(bird)
            self.active_bird = bird  # Establecer como pájaro activo
            
            # Actualizar la vista previa para el siguiente pájaro
            self.update_preview_bird()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            for bird in self.birds:
                if bird.has_special_ability and not bird.ability_used:
                    bird.use_special_ability(self.space, self.sprites)

    def draw_trajectory(self, start_point, impulse_vector):
        power_multiplier = 50  # mismo factor que usas al crear el pájaro
        velocity = impulse_vector.impulse * power_multiplier

        v_x = math.cos(impulse_vector.angle) * velocity / 5
        v_y = math.sin(impulse_vector.angle) * velocity / 5

        g = GRAVITY
        num_points = 30
        time_step = 0.1

        for i in range(num_points):
            t = i * time_step
            x = start_point.x + v_x * t
            y = start_point.y + v_y * t + 0.5 * g * (t ** 2) * (1 / 60)
            arcade.draw_circle_filled(x, y, 3, arcade.color.GRAY)

    def on_draw(self):
        self.clear()
        # 3.3.2: usar draw_texture_rect + LBWH
        arcade.draw_texture_rect(
            self.background,
            arcade.LBWH(0, 0, WIDTH, HEIGHT),
        )

        # === Resortera ===
        # 3.3.2: usar draw_texture_rect + XYWH (centrado en slingshot_pos)
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

        # Línea de apuntado + punto final y trayectoria
        if self.draw_line:
            arcade.draw_line(
                self.slingshot_pos.x, self.slingshot_pos.y,
                self.end_point.x, self.end_point.y,
                arcade.color.BLACK, 3
            )
            arcade.draw_circle_filled(
                self.end_point.x, self.end_point.y,
                8, arcade.color.RED
            )
            impulse_vector = get_impulse_vector(self.slingshot_pos, self.end_point)
            self.draw_trajectory(self.slingshot_pos, impulse_vector)


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()
