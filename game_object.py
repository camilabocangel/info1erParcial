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

    def update(self, delta_time):
        """
        Update the position of the bird sprite based on the physics body position
        """
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle

    def use_special_ability(self, space):
        pass  #Implementar la habilidad especial del pajaro si es necesario
class RedBird(Bird):
    """Pájaro rojo básico - sin habilidad especial"""
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/red-bird3.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=5,
            radius=12,
            scale=1
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
            scale=0.4
        )
class ChuckBird(Bird):
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/chuck.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=3,  # Ligero
            radius=11,
            power_multiplier=60,  # Más rápido por defecto
            scale=0.08
        )
class BombBird(Bird):
    def __init__(self, impulse_vector: ImpulseVector, x: float, y: float, space: pymunk.Space):
        super().__init__(
            image_path="assets/img/bomb.png",
            impulse_vector=impulse_vector,
            x=x,
            y=y,
            space=space,
            mass=8,  # Más pesado
            radius=14,
            power_multiplier=40,  
            scale=0.08
        )
        self.has_special_ability = True
        self.explosion_radius = 150  # Radio de explosión
        
    def use_special_ability(self, space):
        if not self.ability_used:
            self.ability_used = True
            # Crear explosión (esto es simplificado)
            explosion_point = pymunk.Vec2d(self.center_x, self.center_y)
            
            # Aplicar fuerza explosiva a objetos cercanos
            for body in space.bodies:
                if body.body_type == pymunk.Body.DYNAMIC:
                    distance = (body.position - explosion_point).length
                    if distance < self.explosion_radius:
                        # Fuerza inversamente proporcional a la distancia
                        force = (self.explosion_radius - distance) * 500
                        direction = (body.position - explosion_point).normalized()
                        body.apply_impulse_at_world_point(direction * force, body.position)
        
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

