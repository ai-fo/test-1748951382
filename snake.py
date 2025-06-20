from __future__ import annotations

import pygame
import random
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import json
import os

pygame.init()


class Color:
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    GRAY = (128, 128, 128)
    DARK_GREEN = (100, 200, 100)
    YELLOW = (255, 255, 0)
    GRASS_GREEN = (34, 139, 34)
    BROWN = (139, 69, 19)
    FLOWER_RED = (220, 20, 60)
    FLOWER_PINK = (255, 182, 193)
    PURPLE = (128, 0, 128)
    COCONUT_BROWN = (101, 67, 33)
    COCONUT_FIBER = (160, 130, 98)

    # Rainbow colors for the snake
    RAINBOW_COLORS = [
        (255, 0, 0),  # Red
        (255, 127, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),  # Green
        (0, 0, 255),  # Blue
        (75, 0, 130),  # Indigo
        (148, 0, 211),  # Violet
    ]


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class Direction(Enum):
    UP = pygame.Vector2(0, -1)
    DOWN = pygame.Vector2(0, 1)
    LEFT = pygame.Vector2(-1, 0)
    RIGHT = pygame.Vector2(1, 0)


@dataclass
class GameConfig:
    window_width: int = 800
    window_height: int = 600
    cell_size: int = 20
    snake_speed: int = 150
    min_snake_speed: int = 80
    max_snake_speed: int = 300
    speed_increase: int = 20
    coconut_spawn_chance: float = 0.15
    high_score_file: str = "high_scores.json"

    @property
    def cell_number_x(self) -> int:
        return self.window_width // self.cell_size

    @property
    def cell_number_y(self) -> int:
        return self.window_height // self.cell_size


class HighScoreManager:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.scores: List[int] = self.load_scores()

    def load_scores(self) -> List[int]:
        try:
            if os.path.exists(self.config.high_score_file):
                with open(self.config.high_score_file, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return [0]

    def save_scores(self) -> None:
        try:
            with open(self.config.high_score_file, "w") as f:
                json.dump(self.scores, f)
        except IOError:
            pass

    def add_score(self, score: int) -> bool:
        self.scores.append(score)
        self.scores.sort(reverse=True)
        self.scores = self.scores[:10]  # Keep top 10
        self.save_scores()
        return score == self.scores[0]  # Return True if new high score

    def get_high_score(self) -> int:
        return max(self.scores) if self.scores else 0


class Snake:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.body: List[pygame.Vector2] = [
            pygame.Vector2(5, 10),
            pygame.Vector2(4, 10),
            pygame.Vector2(3, 10),
        ]
        self.direction: pygame.Vector2 = Direction.RIGHT.value
        self.new_block: bool = False
        self.should_remove_block: bool = False

    def draw_snake(self, screen: pygame.Surface) -> None:
        for i, block in enumerate(self.body):
            x_pos = int(block.x * self.config.cell_size)
            y_pos = int(block.y * self.config.cell_size)
            block_rect = pygame.Rect(
                x_pos, y_pos, self.config.cell_size, self.config.cell_size
            )

            if i == 0:  # Head
                pygame.draw.rect(screen, Color.YELLOW, block_rect)
            else:  # Body - rainbow effect
                color_index = (i - 1) % len(Color.RAINBOW_COLORS)
                rainbow_color = Color.RAINBOW_COLORS[color_index]
                pygame.draw.rect(screen, rainbow_color, block_rect)

            pygame.draw.rect(screen, Color.WHITE, block_rect, 1)

    def move_snake(self) -> None:
        if self.new_block:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]
            self.new_block = False
        elif self.should_remove_block and len(self.body) > 1:
            # Remove one segment but ensure we don't go below 1 segment
            if len(self.body) > 2:
                body_copy = self.body[:-2]  # Remove 2 segments (tail + one more)
            else:
                body_copy = []  # Will become 1 segment after adding new head
            body_copy.insert(0, self.body[0] + self.direction)
            self.body = body_copy[:]
            self.should_remove_block = False
        else:
            if len(self.body) > 1:
                body_copy = self.body[:-1]
                body_copy.insert(0, body_copy[0] + self.direction)
                self.body = body_copy[:]
            else:
                # Single segment case
                self.body = [self.body[0] + self.direction]

    def add_block(self) -> None:
        self.new_block = True

    def remove_block(self) -> None:
        if len(self.body) > 1:
            self.should_remove_block = True

    def check_collision(self) -> bool:
        head = self.body[0]
        if not (
            0 <= head.x < self.config.cell_number_x
            and 0 <= head.y < self.config.cell_number_y
        ):
            return True

        for block in self.body[1:]:
            if block == head:
                return True

        return False

    def set_direction(self, new_direction: Direction) -> None:
        opposite_directions = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        current_direction = None
        for direction in Direction:
            if direction.value == self.direction:
                current_direction = direction
                break

        if (
            current_direction
            and opposite_directions.get(current_direction) != new_direction
        ):
            self.direction = new_direction.value


class Food:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.randomize()

    def draw_food(self, screen: pygame.Surface) -> None:
        x_pos = int(self.pos.x * self.config.cell_size)
        y_pos = int(self.pos.y * self.config.cell_size)
        center_x = x_pos + self.config.cell_size // 2
        center_y = y_pos + self.config.cell_size // 2
        radius = self.config.cell_size // 3

        # Draw apple body
        pygame.draw.circle(screen, Color.RED, (center_x, center_y), radius)

        # Draw apple stem
        stem_rect = pygame.Rect(center_x - 1, y_pos + 2, 2, 4)
        pygame.draw.rect(screen, (139, 69, 19), stem_rect)

        # Draw apple leaf
        leaf_points = [
            (center_x + 2, y_pos + 3),
            (center_x + 5, y_pos + 1),
            (center_x + 4, y_pos + 5),
        ]
        pygame.draw.polygon(screen, Color.GREEN, leaf_points)

    def randomize(self) -> None:
        x = random.randint(0, self.config.cell_number_x - 1)
        y = random.randint(0, self.config.cell_number_y - 1)
        self.pos = pygame.Vector2(x, y)


class Coconut:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.randomize()

    def draw_coconut(self, screen: pygame.Surface) -> None:
        x_pos = int(self.pos.x * self.config.cell_size)
        y_pos = int(self.pos.y * self.config.cell_size)
        center_x = x_pos + self.config.cell_size // 2
        center_y = y_pos + self.config.cell_size // 2

        # Draw coconut body (brown oval)
        coconut_rect = pygame.Rect(
            x_pos + 2, y_pos + 1, self.config.cell_size - 4, self.config.cell_size - 2
        )
        pygame.draw.ellipse(screen, Color.COCONUT_BROWN, coconut_rect)

        # Draw coconut fiber texture (lighter brown lines)
        for i in range(3):
            line_y = y_pos + 4 + i * 4
            pygame.draw.line(
                screen,
                Color.COCONUT_FIBER,
                (x_pos + 3, line_y),
                (x_pos + self.config.cell_size - 3, line_y),
                1,
            )

        # Draw coconut eyes (3 dark spots)
        eye_radius = 2
        pygame.draw.circle(
            screen, Color.BLACK, (center_x - 4, center_y - 2), eye_radius
        )
        pygame.draw.circle(
            screen, Color.BLACK, (center_x + 4, center_y - 2), eye_radius
        )
        pygame.draw.circle(screen, Color.BLACK, (center_x, center_y + 3), eye_radius)

    def randomize(self) -> None:
        x = random.randint(0, self.config.cell_number_x - 1)
        y = random.randint(0, self.config.cell_number_y - 1)
        self.pos = pygame.Vector2(x, y)


class GardenBackground:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.flowers = []
        self.generate_flowers()

    def generate_flowers(self) -> None:
        for _ in range(15):
            x = random.randint(0, self.config.cell_number_x - 1)
            y = random.randint(0, self.config.cell_number_y - 1)
            flower_type = random.choice(["red", "pink"])
            self.flowers.append({"pos": pygame.Vector2(x, y), "type": flower_type})

    def draw_background(self, screen: pygame.Surface) -> None:
        screen.fill(Color.GRASS_GREEN)

        for x in range(0, self.config.window_width, self.config.cell_size * 4):
            for y in range(0, self.config.window_height, self.config.cell_size * 4):
                if random.random() < 0.3:
                    grass_rect = pygame.Rect(
                        x, y, self.config.cell_size // 2, self.config.cell_size // 2
                    )
                    pygame.draw.rect(screen, Color.DARK_GREEN, grass_rect)

        for flower in self.flowers:
            x_pos = int(flower["pos"].x * self.config.cell_size)
            y_pos = int(flower["pos"].y * self.config.cell_size)

            flower_color = (
                Color.FLOWER_RED if flower["type"] == "red" else Color.FLOWER_PINK
            )
            center = (
                x_pos + self.config.cell_size // 2,
                y_pos + self.config.cell_size // 2,
            )
            pygame.draw.circle(screen, flower_color, center, self.config.cell_size // 4)
            pygame.draw.circle(screen, Color.YELLOW, center, self.config.cell_size // 8)


class Enemy:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.direction: pygame.Vector2 = pygame.Vector2(0, 0)
        self.speed = 0.5
        self.randomize_position()
        self.randomize_direction()
        self.move_timer = 0
        self.move_interval = 60

    def randomize_position(self) -> None:
        x = random.randint(0, self.config.cell_number_x - 1)
        y = random.randint(0, self.config.cell_number_y - 1)
        self.pos = pygame.Vector2(x, y)

    def randomize_direction(self) -> None:
        directions = [
            pygame.Vector2(0, -1),  # UP
            pygame.Vector2(0, 1),  # DOWN
            pygame.Vector2(-1, 0),  # LEFT
            pygame.Vector2(1, 0),  # RIGHT
        ]
        self.direction = random.choice(directions)

    def update(self) -> None:
        self.move_timer += 1
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            new_pos = self.pos + self.direction

            if (
                0 <= new_pos.x < self.config.cell_number_x
                and 0 <= new_pos.y < self.config.cell_number_y
            ):
                self.pos = new_pos
            else:
                self.randomize_direction()

            if random.random() < 0.3:
                self.randomize_direction()

    def draw(self, screen: pygame.Surface) -> None:
        x_pos = int(self.pos.x * self.config.cell_size)
        y_pos = int(self.pos.y * self.config.cell_size)
        enemy_rect = pygame.Rect(
            x_pos, y_pos, self.config.cell_size, self.config.cell_size
        )
        pygame.draw.rect(screen, Color.PURPLE, enemy_rect)
        pygame.draw.rect(screen, Color.WHITE, enemy_rect, 2)

        center = (
            x_pos + self.config.cell_size // 2,
            y_pos + self.config.cell_size // 2,
        )
        pygame.draw.circle(screen, Color.RED, (center[0] - 3, center[1] - 3), 2)
        pygame.draw.circle(screen, Color.RED, (center[0] + 3, center[1] - 3), 2)


class Game:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.snake = Snake(config)
        self.food = Food(config)
        self.coconut: Optional[Coconut] = None
        self.garden = GardenBackground(config)
        self.enemies = [Enemy(config) for _ in range(3)]
        self.score = 0
        self.state = GameState.MENU
        self.high_score_manager = HighScoreManager(config)
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 72)
        self.current_speed = config.snake_speed

    def update(self) -> None:
        if self.state == GameState.PLAYING:
            self.snake.move_snake()
            for enemy in self.enemies:
                enemy.update()
            self.check_collision()
            self.check_enemy_collision()
            self.check_fail()

    def draw_elements(self, screen: pygame.Surface) -> None:
        if self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            self.garden.draw_background(screen)
            self.food.draw_food(screen)
            if self.coconut:
                self.coconut.draw_coconut(screen)
            self.snake.draw_snake(screen)
            for enemy in self.enemies:
                enemy.draw(screen)
            self.draw_score(screen)

            if self.state == GameState.PAUSED:
                self.draw_pause_screen(screen)
        elif self.state == GameState.MENU:
            self.draw_menu(screen)
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over(screen)

    def draw_menu(self, screen: pygame.Surface) -> None:
        title_text = self.large_font.render("SNAKE GAME", True, Color.WHITE)
        title_rect = title_text.get_rect(center=(self.config.window_width // 2, 200))
        screen.blit(title_text, title_rect)

        start_text = self.font.render("Press SPACE to start", True, Color.WHITE)
        start_rect = start_text.get_rect(center=(self.config.window_width // 2, 300))
        screen.blit(start_text, start_rect)

        controls_text = self.font.render("Use arrow keys to move", True, Color.GRAY)
        controls_rect = controls_text.get_rect(
            center=(self.config.window_width // 2, 350)
        )
        screen.blit(controls_text, controls_rect)

        high_score_text = self.font.render(
            f"High Score: {self.high_score_manager.get_high_score()}",
            True,
            Color.YELLOW,
        )
        high_score_rect = high_score_text.get_rect(
            center=(self.config.window_width // 2, 400)
        )
        screen.blit(high_score_text, high_score_rect)

    def draw_pause_screen(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((self.config.window_width, self.config.window_height))
        overlay.set_alpha(128)
        overlay.fill(Color.BLACK)
        screen.blit(overlay, (0, 0))

        pause_text = self.large_font.render("PAUSED", True, Color.WHITE)
        pause_rect = pause_text.get_rect(
            center=(self.config.window_width // 2, self.config.window_height // 2)
        )
        screen.blit(pause_text, pause_rect)

    def draw_game_over(self, screen: pygame.Surface) -> None:
        game_over_text = self.large_font.render("GAME OVER", True, Color.RED)
        game_over_rect = game_over_text.get_rect(
            center=(self.config.window_width // 2, 200)
        )
        screen.blit(game_over_text, game_over_rect)

        score_text = self.font.render(f"Final Score: {self.score}", True, Color.WHITE)
        score_rect = score_text.get_rect(center=(self.config.window_width // 2, 280))
        screen.blit(score_text, score_rect)

        high_score_text = self.font.render(
            f"High Score: {self.high_score_manager.get_high_score()}",
            True,
            Color.YELLOW,
        )
        high_score_rect = high_score_text.get_rect(
            center=(self.config.window_width // 2, 320)
        )
        screen.blit(high_score_text, high_score_rect)

        restart_text = self.font.render(
            "Press R to restart or ESC to menu", True, Color.WHITE
        )
        restart_rect = restart_text.get_rect(
            center=(self.config.window_width // 2, 380)
        )
        screen.blit(restart_text, restart_rect)

    def check_collision(self) -> None:
        # Ensure positions are integers for accurate collision detection
        snake_head = pygame.Vector2(
            int(self.snake.body[0].x), int(self.snake.body[0].y)
        )
        food_pos = pygame.Vector2(int(self.food.pos.x), int(self.food.pos.y))

        # Check apple collision
        if food_pos == snake_head:
            self.food.randomize()
            self.snake.add_block()
            self.score += 1

            # Spawn coconut occasionally
            if random.random() < self.config.coconut_spawn_chance and not self.coconut:
                self.coconut = Coconut(self.config)
                self.ensure_coconut_not_on_snake()
                self.ensure_food_not_on_coconut()

            # Ensure food doesn't spawn on snake or coconut
            self.ensure_food_not_on_snake()

        # Check coconut collision
        if self.coconut:
            coconut_pos = pygame.Vector2(
                int(self.coconut.pos.x), int(self.coconut.pos.y)
            )
            if coconut_pos == snake_head:
                # Remove snake segment and increase speed
                self.snake.remove_block()
                self.increase_speed()
                self.coconut = None
                self.score += 2  # Bonus points for coconut

    def check_enemy_collision(self) -> None:
        for enemy in self.enemies:
            if enemy.pos == self.snake.body[0]:
                self.game_over()

    def check_fail(self) -> None:
        if self.snake.check_collision():
            self.game_over()

    def game_over(self) -> None:
        self.high_score_manager.add_score(self.score)
        self.state = GameState.GAME_OVER

    def restart_game(self) -> None:
        self.snake = Snake(self.config)
        self.food = Food(self.config)
        self.coconut = None
        self.garden = GardenBackground(self.config)
        self.enemies = [Enemy(self.config) for _ in range(3)]
        self.score = 0
        self.current_speed = self.config.snake_speed
        self.state = GameState.PLAYING

    def draw_score(self, screen: pygame.Surface) -> None:
        score_text = self.font.render(f"Score: {self.score}", True, Color.WHITE)
        screen.blit(score_text, (10, 10))

        high_score_text = self.font.render(
            f"High: {self.high_score_manager.get_high_score()}", True, Color.YELLOW
        )
        screen.blit(high_score_text, (10, 50))

        # Show current speed
        speed_text = self.font.render(f"Speed: {self.current_speed}", True, Color.BLUE)
        screen.blit(speed_text, (10, 90))

        # Show coconut indicator
        if self.coconut:
            coconut_text = self.font.render(
                "🥥 Coconut Available!", True, Color.COCONUT_BROWN
            )
            screen.blit(coconut_text, (10, 130))

    def increase_speed(self) -> None:
        self.current_speed = max(
            self.config.min_snake_speed, self.current_speed - self.config.speed_increase
        )
        # Update the game timer with new speed
        pygame.time.set_timer(pygame.USEREVENT, self.current_speed)

    def ensure_coconut_not_on_snake(self) -> None:
        if not self.coconut:
            return

        while any(block == self.coconut.pos for block in self.snake.body):
            self.coconut.randomize()

    def ensure_food_not_on_snake(self) -> None:
        collision_found = True
        attempts = 0
        while collision_found and attempts < 100:  # Prevent infinite loop
            collision_found = False
            for block in self.snake.body:
                if pygame.Vector2(int(block.x), int(block.y)) == pygame.Vector2(
                    int(self.food.pos.x), int(self.food.pos.y)
                ):
                    self.food.randomize()
                    collision_found = True
                    break
            attempts += 1

    def ensure_food_not_on_coconut(self) -> None:
        if not self.coconut:
            return

        attempts = 0
        while (
            pygame.Vector2(int(self.food.pos.x), int(self.food.pos.y))
            == pygame.Vector2(int(self.coconut.pos.x), int(self.coconut.pos.y))
        ) and attempts < 100:
            self.food.randomize()
            attempts += 1


def main() -> None:
    config = GameConfig()
    screen = pygame.display.set_mode((config.window_width, config.window_height))
    pygame.display.set_caption("Modern Snake Game")
    clock = pygame.time.Clock()

    game = Game(config)

    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, game.current_speed)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == SCREEN_UPDATE and game.state == GameState.PLAYING:
                game.update()

            if event.type == pygame.KEYDOWN:
                if game.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        game.restart_game()

                elif game.state == GameState.PLAYING:
                    if event.key == pygame.K_UP:
                        game.snake.set_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        game.snake.set_direction(Direction.DOWN)
                    elif event.key == pygame.K_RIGHT:
                        game.snake.set_direction(Direction.RIGHT)
                    elif event.key == pygame.K_LEFT:
                        game.snake.set_direction(Direction.LEFT)
                    elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                        game.state = GameState.PAUSED

                elif game.state == GameState.PAUSED:
                    if event.key == pygame.K_p or event.key == pygame.K_SPACE:
                        game.state = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        game.state = GameState.MENU

                elif game.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        game.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        game.state = GameState.MENU

        if game.state == GameState.MENU or game.state == GameState.GAME_OVER:
            screen.fill(Color.BLACK)
        game.draw_elements(screen)
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
