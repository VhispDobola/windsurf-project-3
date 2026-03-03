"""
Spatial partitioning system for efficient collision detection
"""

import math


class SpatialGrid:
    """Grid-based spatial partitioning for efficient collision detection"""
    
    def __init__(self, width, height, cell_size=64):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        self.grid = {}
    
    def clear(self):
        """Clear all objects from the grid"""
        self.grid.clear()
    
    def add_object(self, obj, rect=None):
        """Add an object to the grid"""
        if rect is None:
            rect = obj.get_rect() if hasattr(obj, 'get_rect') else obj.rect
        
        cells = self._get_cells_for_rect(rect)
        for cell in cells:
            if cell not in self.grid:
                self.grid[cell] = []
            self.grid[cell].append(obj)
    
    def get_nearby_objects(self, obj, rect=None):
        """Get all objects in cells that overlap with the given object"""
        if rect is None:
            rect = obj.get_rect() if hasattr(obj, 'get_rect') else obj.rect
        
        cells = self._get_cells_for_rect(rect)
        nearby = set()
        
        for cell in cells:
            if cell in self.grid:
                for other in self.grid[cell]:
                    if other != obj:
                        nearby.add(other)
        
        return list(nearby)
    
    def _get_cells_for_rect(self, rect):
        """Get all grid cells that overlap with the given rectangle"""
        start_col = max(0, rect.left // self.cell_size)
        end_col = min(self.cols - 1, rect.right // self.cell_size)
        start_row = max(0, rect.top // self.cell_size)
        end_row = min(self.rows - 1, rect.bottom // self.cell_size)
        
        cells = []
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cells.append((col, row))
        
        return cells


class QuadTree:
    """Quadtree spatial partitioning for dynamic objects"""
    
    def __init__(self, boundary, capacity=10, max_depth=5):
        self.boundary = boundary  # (x, y, width, height)
        self.capacity = capacity
        self.max_depth = max_depth
        self.objects = []
        self.divided = False
        self.children = None
    
    def clear(self):
        """Clear all objects from the quadtree"""
        self.objects.clear()
        if self.divided:
            for child in self.children:
                child.clear()
            self.divided = False
            self.children = None
    
    def insert(self, obj, rect=None):
        """Insert an object into the quadtree"""
        if rect is None:
            rect = obj.get_rect() if hasattr(obj, 'get_rect') else obj.rect
        
        if not self._intersects(rect, self.boundary):
            return False
        
        if len(self.objects) < self.capacity or self.max_depth <= 0:
            self.objects.append(obj)
            return True
        
        if not self.divided:
            self._subdivide()
        
        return (self.children[0].insert(obj, rect) or
                self.children[1].insert(obj, rect) or
                self.children[2].insert(obj, rect) or
                self.children[3].insert(obj, rect))
    
    def query(self, rect, found=None):
        """Query for objects that intersect with the given rectangle"""
        if found is None:
            found = []
        
        if not self._intersects(rect, self.boundary):
            return found
        
        for obj in self.objects:
            obj_rect = obj.get_rect() if hasattr(obj, 'get_rect') else obj.rect
            if self._intersects(rect, obj_rect):
                found.append(obj)
        
        if self.divided:
            self.children[0].query(rect, found)
            self.children[1].query(rect, found)
            self.children[2].query(rect, found)
            self.children[3].query(rect, found)
        
        return found
    
    def _subdivide(self):
        """Subdivide the quadtree into four children"""
        x, y, w, h = self.boundary
        half_w = w / 2
        half_h = h / 2
        
        self.children = [
            QuadTree((x, y, half_w, half_h), self.capacity, self.max_depth - 1),
            QuadTree((x + half_w, y, half_w, half_h), self.capacity, self.max_depth - 1),
            QuadTree((x, y + half_h, half_w, half_h), self.capacity, self.max_depth - 1),
            QuadTree((x + half_w, y + half_h, half_w, half_h), self.capacity, self.max_depth - 1)
        ]
        self.divided = True
    
    def _intersects(self, rect1, rect2):
        """Check if two rectangles intersect"""
        return not (rect1.right <= rect2.left or
                  rect1.left >= rect2.right or
                  rect1.bottom <= rect2.top or
                  rect1.top >= rect2.bottom)
