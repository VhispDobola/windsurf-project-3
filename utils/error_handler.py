"""
Error handling and logging utilities
"""

import logging
import traceback
import os
from datetime import datetime


class GameErrorHandler:
    """Centralized error handling for the game"""
    
    def __init__(self, log_file=None):
        self.setup_logging(log_file)
    
    def setup_logging(self, log_file=None):
        """Setup logging configuration"""
        if log_file is None:
            log_file = f"game_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_pygame_error(self, operation, error):
        """Handle pygame-specific errors"""
        self.logger.error(f"Pygame error during {operation}: {error}")
        return None
    
    def handle_file_error(self, filename, operation, error):
        """Handle file I/O errors"""
        self.logger.error(f"File error during {operation} on {filename}: {error}")
        return None
    
    def safe_file_operation(self, operation, filename, default_return=None):
        """Safely execute file operations with error handling"""
        try:
            return operation(filename)
        except (IOError, OSError, PermissionError) as e:
            self.handle_file_error(filename, "file operation", e)
            return default_return
        except Exception as e:
            self.logger.error(f"Unexpected error during file operation on {filename}: {e}")
            self.logger.debug(traceback.format_exc())
            return default_return
    
    def safe_pygame_operation(self, operation, default_return=None):
        """Safely execute pygame operations with error handling"""
        try:
            return operation()
        except Exception as e:
            self.handle_pygame_error("pygame operation", e)
            return default_return
    
    def validate_input(self, value, input_type, min_val=None, max_val=None):
        """Validate user input"""
        try:
            if input_type == "int":
                validated = int(value)
            elif input_type == "float":
                validated = float(value)
            elif input_type == "str":
                validated = str(value)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
            
            if min_val is not None and validated < min_val:
                raise ValueError(f"Value {validated} is below minimum {min_val}")
            
            if max_val is not None and validated > max_val:
                raise ValueError(f"Value {validated} is above maximum {max_val}")
            
            return validated
        
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Input validation failed: {e}")
            return None


def validate_game_config():
    """Validate game configuration values"""
    errors = []
    
    # Validate screen dimensions
    from config.constants import WIDTH, HEIGHT, FPS
    
    if WIDTH <= 0 or HEIGHT <= 0:
        errors.append("Screen dimensions must be positive")
    
    if FPS <= 0:
        errors.append("FPS must be positive")
    
    # Validate color constants
    colors = ["WHITE", "BLACK", "RED", "BLUE", "GREEN", "YELLOW"]
    from config.constants import WHITE, BLACK, RED, BLUE, GREEN, YELLOW
    
    for color_name, color_value in zip(colors, [WHITE, BLACK, RED, BLUE, GREEN, YELLOW]):
        if not isinstance(color_value, tuple) or len(color_value) != 3:
            errors.append(f"Color {color_name} must be a 3-tuple")
        elif not all(0 <= c <= 255 for c in color_value):
            errors.append(f"Color {color_name} values must be 0-255")
    
    return errors


def safe_resource_load(resource_path, resource_type="file"):
    """Safely load game resources"""
    if not os.path.exists(resource_path):
        raise FileNotFoundError(f"Resource not found: {resource_path}")
    
    if not os.access(resource_path, os.R_OK):
        raise PermissionError(f"Cannot read resource: {resource_path}")
    
    return resource_path
