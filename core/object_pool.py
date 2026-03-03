"""
Object pooling system for performance optimization
"""

import pygame
from typing import List, TypeVar, Generic, Callable, Optional

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """Generic object pool for reusing objects instead of creating/destroying"""
    
    def __init__(self, create_func: Callable[[], T], reset_func: Optional[Callable[[T], None]] = None, initial_size: int = 10):
        self.create_func = create_func
        self.reset_func = reset_func or (lambda obj: None)
        self.available: List[T] = []
        self.in_use: List[T] = []
        
        # Pre-populate pool
        for _ in range(initial_size):
            obj = create_func()
            self.available.append(obj)
    
    def acquire(self) -> T:
        """Get an object from the pool"""
        if self.available:
            obj = self.available.pop()
        else:
            obj = self.create_func()
        
        self.in_use.append(obj)
        return obj
    
    def release(self, obj: T) -> None:
        """Return an object to the pool"""
        if obj in self.in_use:
            self.in_use.remove(obj)
            self.reset_func(obj)
            self.available.append(obj)
    
    def release_all(self) -> None:
        """Release all currently used objects"""
        for obj in self.in_use[:]:
            self.release(obj)
    
    def clear(self) -> None:
        """Clear the entire pool"""
        self.available.clear()
        self.in_use.clear()


class ProjectilePool(ObjectPool):
    """Specialized pool for projectiles"""
    
    def __init__(self, initial_size: int = 50):
        super().__init__(
            create_func=lambda: self._create_projectile(),
            reset_func=self._reset_projectile,
            initial_size=initial_size
        )
    
    def _create_projectile(self):
        """Create a new projectile"""
        from .projectile import Projectile
        return Projectile(0, 0, 0, 0, 10, (255, 255, 0))
    
    def _reset_projectile(self, projectile):
        """Reset projectile to default state"""
        projectile.x = 0
        projectile.y = 0
        projectile.dx = 0
        projectile.dy = 0
        projectile.damage = 10
        projectile.color = (255, 255, 0)
        projectile.active = True
        
        # Clear any custom attributes
        for attr in dir(projectile):
            if attr.startswith('_') or attr in ['x', 'y', 'dx', 'dy', 'damage', 'color', 'active']:
                continue
            try:
                delattr(projectile, attr)
            except AttributeError:
                pass
    
    def get_projectile(self, x, y, dx, dy, damage, color):
        """Get a pre-configured projectile"""
        projectile = self.acquire()
        projectile.x = x
        projectile.y = y
        projectile.dx = dx
        projectile.dy = dy
        projectile.damage = damage
        projectile.color = color
        projectile.active = True
        return projectile


class EffectPool(ObjectPool):
    """Specialized pool for effects"""
    
    def __init__(self, initial_size: int = 20):
        super().__init__(
            create_func=lambda: self._create_effect(),
            reset_func=self._reset_effect,
            initial_size=initial_size
        )
    
    def _create_effect(self):
        """Create a new effect"""
        from .effect import Telegraph
        return Telegraph(0, 0, 50, 30, (255, 0, 0), 10)
    
    def _reset_effect(self, effect):
        """Reset effect to default state"""
        effect.x = 0
        effect.y = 0
        effect.radius = 50
        effect.duration = 30
        effect.color = (255, 0, 0)
        effect.damage = 10
        effect.active_start = 15
        effect.active_end = 25
        effect.active = False


class PoolManager:
    """Manages multiple object pools"""
    
    def __init__(self):
        self.projectile_pool = ProjectilePool()
        self.effect_pool = EffectPool()
        self.pools = {
            'projectile': self.projectile_pool,
            'effect': self.effect_pool
        }
    
    def get_pool(self, pool_type: str) -> ObjectPool:
        """Get a specific pool by type"""
        return self.pools.get(pool_type)
    
    def release_all(self, pool_type: str = None):
        """Release all objects from a specific pool or all pools"""
        if pool_type:
            pool = self.pools.get(pool_type)
            if pool:
                pool.release_all()
        else:
            for pool in self.pools.values():
                pool.release_all()
    
    def clear_all(self):
        """Clear all pools"""
        for pool in self.pools.values():
            pool.clear()
