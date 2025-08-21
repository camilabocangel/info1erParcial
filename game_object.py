import math
import arcade
import pymunk
from game_logic import ImpulseVector


class Bird(arcade.Sprite): #pajaro rojo 
    """
    Bird class. This represents an angry bird. All the physics is handled by Pymunk,
    the init method only set some initial properties
    """
    def __init__( #inicializa el pajaro
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 12,
        max_impulse: float = 100,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
        scale: float = 1.0,
    ):
        super().__init__(image_path, scale) #cuerpo fisico en pymunk
        # body
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        impulse_pymunk = impulse * pymunk.Vec2d(1, 0)
        # apply impulse
        body.apply_impulse_at_local_point(impulse_pymunk.rotated(impulse_vector.angle))
        # shape - define la forma fisica del pajaro (circulo)
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer

        space.add(body, shape)

        self.body = body
        self.shape = shape
        self.has_special_ability = False
        self.ability_used = False
    def use_special_ability(self, space, sprites_list):
        pass
    def update(self, delta_time):
        """
        Update the position of the bird sprite based on the physics body position
        """
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle

class RedBird(Bird):
    
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/red-bird3.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=5,
            radius=12,
            scale=1.5
        )
class BlueBird(Bird):
    """Pájaro azul - se divide en 3 pájaros más pequeños"""
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/blue.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=4,  # Más ligero
            radius=10,
            scale=0.3
        )
        self.has_special_ability = True
    def use_special_ability(self, space, sprites_list):
        if not self.ability_used:
            self.ability_used = True
            current_pos = pymunk.Vec2d(self.center_x, self.center_y)
            current_velocity = self.body.velocity
            
            # Crear 3 pájaros azules más pequeños
            for i in range(3):
                angle = math.pi/4 * (i - 1)  # -45°, 0°, 45°
                new_velocity = current_velocity.rotated(angle) * 1.2
                
                # Crear nuevo pájaro
                new_bird = BlueBirdSplit(
                    ImpulseVector(0, 0),
                    current_pos.x,
                    current_pos.y,
                    space
                )
                
                # Aplicar velocidad
                new_bird.body.velocity = new_velocity
                
                sprites_list.append(new_bird)


class BlueBirdSplit(Bird):
    """Versión más pequeña del pájaro azul para la habilidad especial"""
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/blue.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=2,  # Más ligero
            radius=6,  # Más pequeño
            scale=0.2
        )
class ChuckBird(Bird):
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/chuck.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=4,  # Ligero
            radius=11,
            power_multiplier=60,  # Más rápido por defecto
            scale=0.08
        )
        self.has_special_ability = True
        self.speed_boost_applied = False
    def use_special_ability(self, space, sprites_list):
        if not self.ability_used and not self.speed_boost_applied:
            self.ability_used = True
            self.speed_boost_applied = True
            
            # Aumentar velocidad significativamente
            speed_boost = 1.5  # Multiplicador de velocidad
            current_velocity = self.body.velocity
            self.body.velocity = current_velocity * speed_boost
            
            # Cambiar apariencia para indicar el boost
            self.texture = arcade.load_texture("assets/img/chuck.png")
class BombBird(Bird):
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/bomb.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=5,  
            radius=14,
            power_multiplier=40,  
            scale=0.08
        )
        self.has_special_ability = True
        self.explosion_radius = 150  # Radio de explosión
    def use_special_ability(self, space, sprites_list):
        if not self.ability_used:
            self.ability_used = True
            explosion_point = pymunk.Vec2d(self.center_x, self.center_y)
            explosion = Explosion(self.center_x, self.center_y)
            sprites_list.append(explosion)
            for body in space.bodies:
                if body.body_type == pymunk.Body.DYNAMIC:
                    distance = (body.position - explosion_point).length
                    if distance < self.explosion_radius:
                        force = (self.explosion_radius - distance) * 800
                        direction = (body.position - explosion_point).normalized()
                        body.apply_impulse_at_world_point(direction * force, body.position)
            self.remove_from_sprite_lists()
            space.remove(self.shape, self.body)

            print("¡BOOM! Explosión del pájaro bomba")
        
        
class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = 0,
    ):
        super().__init__("assets/img/pig_failed.png", 0.1)
        moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle
class Explosion(arcade.Sprite):
    def __init__(self, x: float, y: float):
        super().__init__("assets/img/explosion.png", 0.3)  # escala ajustable
        self.center_x = x
        self.center_y = y
        self.duration = 0.5  # medio segundo visible
        self.timer = 0

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.duration:
            self.remove_from_sprite_lists()


class PassiveObject(arcade.Sprite):
    """
    Passive object that can interact with other objects.
    """
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)

        moment = pymunk.moment_for_box(mass, (self.width, self.height))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space)


class StaticObject(arcade.Sprite):
    def __init__(
            self,
            image_path: str,
            x: float,
            y: float,
            space: pymunk.Space,
            mass: float = 2,
            elasticity: float = 0.8,
            friction: float = 1,
            collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)

