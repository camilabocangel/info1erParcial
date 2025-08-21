import math
import arcade
from dataclasses import dataclass
from logging import getLogger

logger = getLogger(__name__) #imprime informacion de depuración


@dataclass
class ImpulseVector: #vector de impulso
    angle: float
    impulse: float


@dataclass
class Point2D:  #punto en 2D
    x: float = 0
    y: float = 0


def get_angle_radians(point_a: Point2D, point_b: Point2D) -> float:
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y
    return math.atan2(dy, dx)


def get_distance(point_a: Point2D, point_b: Point2D) -> float:
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y
    return math.sqrt(dx**2 + dy**2)


def get_impulse_vector(start_point: Point2D, end_point: Point2D) -> ImpulseVector:
    distance = get_distance(start_point, end_point)
    angle = get_angle_radians(start_point, end_point)
    
    angle += math.pi  
    
    max_drag_distance = 200
    normalized_distance = min(distance, max_drag_distance) / max_drag_distance
    
    impulse = normalized_distance * 100  
    
    return ImpulseVector(angle, impulse)
