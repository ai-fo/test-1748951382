from __future__ import annotations

import pygame
import random
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
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
                with open(self.config.high_score_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return [0]
    
    def save_scores(self) -> None:
        try:
            with open(self.config.high_score_file, 'w') as f:
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
            pygame.Vector2(3, 10)
        ]
        self.direction: pygame.Vector2 = Direction.RIGHT.value
        self.new_block: bool = False
        
    def draw_snake(self, screen: pygame.Surface) -> None:
        for i, block in enumerate(self.body):
            x_pos = int(block.x * self.config.cell_size)
            y_pos = int(block.y * self.config.cell_size)
            block_rect = pygame.Rect(x_pos, y_pos, self.config.cell_size, self.config.cell_size)
            
            if i == 0:  # Head
                pygame.draw.rect(screen, Color.YELLOW, block_rect)
            else:  # Body
                pygame.draw.rect(screen, Color.DARK_GREEN, block_rect)
            
            pygame.draw.rect(screen, Color.WHITE, block_rect, 1)
    
    def move_snake(self) -> None:
        if self.new_block:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]
            self.new_block = False
        else:
            body_copy = self.body[:-1]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy[:]
    
    def add_block(self) -> None:
        self.new_block = True
    
    def check_collision(self) -> bool:
        head = self.body[0]
        if not (0 <= head.x < self.config.cell_number_x and 0 <= head.y < self.config.cell_number_y):
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
            Direction.RIGHT: Direction.LEFT
        }
        
        current_direction = None
        for direction in Direction:
            if direction.value == self.direction:
                current_direction = direction
                break
        
        if current_direction and opposite_directions.get(current_direction) != new_direction:
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
            (center_x + 4, y_pos + 5)
        ]
        pygame.draw.polygon(screen, Color.GREEN, leaf_points)
    
    def randomize(self) -> None:
        x = random.randint(0, self.config.cell_number_x - 1)
        y = random.randint(0, self.config.cell_number_y - 1)
        self.pos = pygame.Vector2(x, y)

class Game:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.snake = Snake(config)
        self.food = Food(config)
        self.score = 0
        self.state = GameState.MENU
        self.high_score_manager = HighScoreManager(config)
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 72)
        
    def update(self) -> None:
        if self.state == GameState.PLAYING:
            self.snake.move_snake()
            self.check_collision()
            self.check_fail()
    
    def draw_elements(self, screen: pygame.Surface) -> None:
        if self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            self.food.draw_food(screen)
            self.snake.draw_snake(screen)
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
        controls_rect = controls_text.get_rect(center=(self.config.window_width // 2, 350))
        screen.blit(controls_text, controls_rect)
        
        high_score_text = self.font.render(f"High Score: {self.high_score_manager.get_high_score()}", True, Color.YELLOW)
        high_score_rect = high_score_text.get_rect(center=(self.config.window_width // 2, 400))
        screen.blit(high_score_text, high_score_rect)
    
    def draw_pause_screen(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((self.config.window_width, self.config.window_height))
        overlay.set_alpha(128)
        overlay.fill(Color.BLACK)
        screen.blit(overlay, (0, 0))
        
        pause_text = self.large_font.render("PAUSED", True, Color.WHITE)
        pause_rect = pause_text.get_rect(center=(self.config.window_width // 2, self.config.window_height // 2))
        screen.blit(pause_text, pause_rect)
    
    def draw_game_over(self, screen: pygame.Surface) -> None:
        game_over_text = self.large_font.render("GAME OVER", True, Color.RED)
        game_over_rect = game_over_text.get_rect(center=(self.config.window_width // 2, 200))
        screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font.render(f"Final Score: {self.score}", True, Color.WHITE)
        score_rect = score_text.get_rect(center=(self.config.window_width // 2, 280))
        screen.blit(score_text, score_rect)
        
        high_score_text = self.font.render(f"High Score: {self.high_score_manager.get_high_score()}", True, Color.YELLOW)
        high_score_rect = high_score_text.get_rect(center=(self.config.window_width // 2, 320))
        screen.blit(high_score_text, high_score_rect)
        
        restart_text = self.font.render("Press R to restart or ESC to menu", True, Color.WHITE)
        restart_rect = restart_text.get_rect(center=(self.config.window_width // 2, 380))
        screen.blit(restart_text, restart_rect)
    
    def check_collision(self) -> None:
        if self.food.pos == self.snake.body[0]:
            self.food.randomize()
            self.snake.add_block()
            self.score += 1
            
            # Ensure food doesn't spawn on snake
            for block in self.snake.body[1:]:
                if block == self.food.pos:
                    self.food.randomize()
    
    def check_fail(self) -> None:
        if self.snake.check_collision():
            self.game_over()
    
    def game_over(self) -> None:
        self.high_score_manager.add_score(self.score)
        self.state = GameState.GAME_OVER
    
    def restart_game(self) -> None:
        self.snake = Snake(self.config)
        self.food = Food(self.config)
        self.score = 0
        self.state = GameState.PLAYING
    
    def draw_score(self, screen: pygame.Surface) -> None:
        score_text = self.font.render(f"Score: {self.score}", True, Color.WHITE)
        screen.blit(score_text, (10, 10))
        
        high_score_text = self.font.render(f"High: {self.high_score_manager.get_high_score()}", True, Color.YELLOW)
        screen.blit(high_score_text, (10, 50))

def main() -> None:
    config = GameConfig()
    screen = pygame.display.set_mode((config.window_width, config.window_height))
    pygame.display.set_caption("Modern Snake Game")
    clock = pygame.time.Clock()
    
    game = Game(config)
    
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, config.snake_speed)
    
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
        
        screen.fill(Color.BLACK)
        game.draw_elements(screen)
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()