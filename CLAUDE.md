# Project: Snake Game

## Description
A modernized Snake game built with Python and Pygame featuring:
- Rainbow-colored snake with yellow head
- Garden background with grass and flowers
- Realistic apple food with stem and leaf
- Purple enemies that move randomly
- Game states: menu, playing, paused, game over
- High score persistence
- Modern Python structure with type hints, dataclasses, and enums

## Commands

### Development Workflow (Always follow this order)
1. **Run tests first**: `uv run pytest tests/ -v`
2. **Check code quality**: `uv run ruff check . && uv run ruff format .`
3. **Run the game**: `uv run python snake.py`

### Test Commands
```bash
# Run all tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest --cov=snake tests/

# Run specific test file
uv run pytest tests/test_snake.py -v
```

### Install dependencies
```bash
uv sync
```

### Quality Checks
```bash
# Check and format code
uv run ruff check .
uv run ruff format .

# Type checking (if mypy added)
uv run mypy snake.py
```

### Project structure
- `snake.py` - Main game file with all classes and logic
- `main.py` - Simple Flask hello world (separate from game)
- `pyproject.toml` - Project configuration and dependencies
- `high_scores.json` - Persistent high score storage (auto-generated)

## Controls
- **SPACE**: Start game from menu, pause/unpause during game
- **Arrow keys**: Control snake direction
- **P**: Pause/unpause
- **R**: Restart after game over
- **ESC**: Return to menu from pause or game over

## Development Guidelines
- **Always create unit tests** for new functions in `tests/` directory
- **Test-Driven Development**: Tests must pass before considering code complete
- **Auto-commit workflow**: If all tests pass + code quality checks pass → auto git commit & push
- Use pytest for testing framework
- Aim for high test coverage (>80%)
- Test both happy path and edge cases
- Mock external dependencies (pygame display, file I/O, etc.)

## Auto-Validation Criteria
Code is considered 100% functional when:
1. ✅ All unit tests pass
2. ✅ Code quality checks pass (ruff)
3. ✅ No type errors (if using mypy)
4. ✅ Game launches without crashes
5. ✅ All game states work correctly (menu → play → pause → game over)

If all criteria met → Auto commit with descriptive message & push to main

## Features
- Type-safe code with comprehensive type hints
- Configurable game settings via GameConfig dataclass
- High score management with JSON persistence
- Multiple game states with proper state management
- Enhanced graphics with colored snake segments
- Garden theme with decorative background elements
- Enemy AI with random movement patterns