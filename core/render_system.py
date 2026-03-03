"""
Optimized rendering system with culling and batching
"""

import pygame
from .render_layers import RenderLayer


class RenderSystem:
    """Optimized rendering system with spatial culling and object batching"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.render_batches = {}  # Organize objects by render layer
        self.font_cache = {}
        self.dirty_rects = []
        self.use_dirty_rects = False
        
    def clear_batches(self):
        """Clear all render batches"""
        self.render_batches.clear()
        self.dirty_rects.clear()
    
    def add_object(self, obj, layer=RenderLayer.ENTITIES):
        """Add an object to the appropriate render batch"""
        if layer not in self.render_batches:
            self.render_batches[layer] = []
        self.render_batches[layer].append(obj)
    
    def add_dirty_rect(self, rect):
        """Add a dirty rectangle for partial screen updates"""
        if self.use_dirty_rects:
            self.dirty_rects.append(rect)
    
    def is_on_screen(self, obj):
        """Check if object is visible on screen"""
        if hasattr(obj, 'get_rect'):
            rect = obj.get_rect()
        elif hasattr(obj, 'rect'):
            rect = obj.rect
        else:
            return True  # Assume visible if no rect
        
        # Check if object intersects with screen bounds
        return not (rect.right < 0 or rect.left > self.width or
                   rect.bottom < 0 or rect.top > self.height)
    
    def render(self, screen, background_color=(0, 0, 0), background_draw=None):
        """Render all objects in proper order with culling"""
        # Clear screen or draw background
        if background_draw is not None:
            background_draw(screen)
        elif self.use_dirty_rects and self.dirty_rects:
            # Only clear dirty areas
            for rect in self.dirty_rects:
                pygame.draw.rect(screen, background_color, rect)
        else:
            screen.fill(background_color)
        
        # Render in layer order
        for layer in sorted(RenderLayer):
            if layer in self.render_batches:
                self._render_layer(screen, self.render_batches[layer])
        
        # Display update is intentionally owned by the main game loop.
    
    def _render_layer(self, screen, objects):
        """Render all objects in a specific layer"""
        for obj in objects:
            # Skip off-screen objects
            if not self.is_on_screen(obj):
                continue
            
            # Render object
            if hasattr(obj, 'draw'):
                obj.draw(screen)
            elif hasattr(obj, 'render'):
                obj.render(screen)
    
    def get_font(self, size, font_name=None):
        """Get cached font or create new one"""
        key = (font_name, size)
        if key not in self.font_cache:
            if font_name:
                self.font_cache[key] = pygame.font.Font(font_name, size)
            else:
                self.font_cache[key] = pygame.font.Font(None, size)
        return self.font_cache[key]
    
    def enable_dirty_rects(self, enabled=True):
        """Enable or disable dirty rectangle optimization"""
        self.use_dirty_rects = enabled


class ScreenShakeEffect:
    """Optimized screen shake effect"""
    
    def __init__(self):
        self.duration = 0
        self.intensity = 0
        self.offset_x = 0
        self.offset_y = 0
    
    def start(self, intensity, duration):
        """Start screen shake effect"""
        self.intensity = intensity
        self.duration = duration
    
    def update(self):
        """Update screen shake"""
        if self.duration > 0:
            self.duration -= 1
            import random
            self.offset_x = random.randint(-self.intensity, self.intensity)
            self.offset_y = random.randint(-self.intensity, self.intensity)
            return True
        else:
            self.offset_x = 0
            self.offset_y = 0
            return False
    
    def apply_offset(self, screen):
        """Apply screen shake offset"""
        if self.duration > 0:
            # Create temporary surface with shake
            temp_surface = screen.copy()
            screen.fill((0, 0, 0))
            screen.blit(temp_surface, (self.offset_x, self.offset_y))
