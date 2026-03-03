# Boss Rush Game - Setup and Development Guide

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Pygame 2.5.2 or higher
- Git (for version control)

### Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd windsurf-project-3
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
python main.py
```

## Development Setup

### Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### IDE Configuration
- Use VS Code with Python extension
- Configure Python interpreter to use virtual environment
- Install Python docstring extension for better documentation

## Project Structure

```
windsurf-project-3/
├── main.py                    # Game entry point
├── requirements.txt            # Dependencies
├── .gitignore                # Git ignore rules
├── CODING_STANDARDS.md      # Development guidelines
├── README_IMPROVEMENTS.md    # Improvement documentation
├── SETUP_GUIDE.md           # This file
├── config/                   # Configuration
│   ├── __init__.py
│   └── constants.py         # Game constants
├── core/                     # Core game systems
│   ├── __init__.py
│   ├── entity.py            # Base entity class
│   ├── boss.py             # Boss base class
│   ├── player.py           # Player class
│   ├── projectile.py       # Projectile system
│   ├── effect.py           # Visual effects
│   ├── collision_system.py # Optimized collisions
│   ├── render_system.py    # Optimized rendering
│   ├── spatial_partition.py # Spatial indexing
│   ├── object_pool.py      # Memory management
│   ├── input_manager.py    # Input handling
│   ├── audio_manager.py    # Sound system
│   ├── game_state.py      # State management
│   ├── upgrade_system.py   # Player progression
│   └── boss_patterns.py   # Reusable patterns
├── bosses/                  # Boss implementations
│   ├── __init__.py
│   ├── boss_base.py       # Boss base class
│   ├── eternal_guardian.py
│   ├── duelist.py
│   └── ... (other bosses)
├── ui/                      # User interface
│   ├── __init__.py
│   ├── ui_manager.py       # UI management
│   └── boss_title_animator.py
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── performance_logger.py
│   ├── boss_scaling.py
│   └── error_handler.py    # Error handling
└── data/                    # Game data
    └── boss_performance_log.json
```

## Development Guidelines

### Code Standards
Follow `CODING_STANDARDS.md` for:
- Naming conventions
- Code organization
- Documentation standards
- Best practices

### Testing
```bash
# Run basic game test
python main.py

# Check configuration
python -c "from config.constants import *; print('Config OK')"

# Test imports
python -c "from core import *; from bosses import *; print('Imports OK')"
```

### Debugging
- Enable debug logging in `utils/error_handler.py`
- Use performance logger to monitor FPS
- Check `data/boss_performance_log.json` for boss statistics

## Configuration

### Game Balance
Edit `config/constants.py`:
```python
# Player settings
PLAYER_BASE_SPEED = 4
PLAYER_BASE_HEALTH = 100
PLAYER_DASH_SPEED = 12

# Boss settings
BOSS_INTRO_DURATION = 120
BOSS_WEAKENED_HEALTH_MULTIPLIER = 0.65

# UI settings
UPGRADE_COUNT = 4
HEALTH_BAR_WIDTH = 250
```

### Input Controls
Default controls are in `core/input_manager.py`:
- WASD/Arrows: Move
- Shift: Dash
- Space: Shoot/Confirm
- Escape: Cancel/Menu
- F11: Fullscreen
- R: Restart (when game over)

## Adding New Content

### New Boss
1. Create file in `bosses/` directory
2. Inherit from `BaseBoss`
3. Use `BossAttackPattern` for attacks
4. Add to `bosses/__init__.py`
5. Add to `core/boss_manager.py`

### New Attack Pattern
1. Add method to `core/boss_patterns.py`
2. Follow existing pattern structure
3. Use parameters for customization

### New Upgrade
1. Add to `core/upgrade_system.py`
2. Implement apply method
3. Add to upgrade list

## Performance Optimization

### Monitoring
- Use built-in performance logger
- Monitor FPS in game window title
- Check collision detection performance

### Optimization Tips
- Use object pools for frequent allocations
- Leverage spatial partitioning for collisions
- Implement viewport culling for rendering
- Cache frequently used resources

## Troubleshooting

### Common Issues

**Game won't start:**
- Check Python version (3.8+)
- Verify pygame installation
- Check for missing assets

**Performance issues:**
- Lower screen resolution in constants
- Disable visual effects
- Check for memory leaks

**Audio not working:**
- Verify audio files exist
- Check pygame mixer initialization
- Test with different audio drivers

### Error Logs
- Check console output for errors
- Review `game_errors_*.log` files
- Use debug mode for detailed logging

## Contributing

### Pull Request Process
1. Fork repository
2. Create feature branch
3. Follow coding standards
4. Test thoroughly
5. Submit pull request

### Code Review Checklist
- [ ] Follows coding standards
- [ ] No hardcoded values
- [ ] Proper error handling
- [ ] Documentation updated
- [ ] Performance tested
- [ ] No memory leaks

## Deployment

### Creating Executable
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### Web Version
Consider using Pygbol or similar for web deployment.

## Support

### Documentation
- `CODING_STANDARDS.md` - Development guidelines
- `README_IMPROVEMENTS.md` - Technical improvements
- Code comments and docstrings

### Community
- Report issues on GitHub
- Join Discord for development discussion
- Check Wiki for tutorials

## License

This project is open source. See LICENSE file for details.

---

**Happy Game Development!** 🎮
