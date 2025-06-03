import pytest
import pygame
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import snake module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snake import Coconut, Snake, Game, GameConfig, Color

class TestCoconut:
    def setup_method(self):
        """Setup test fixtures before each test method."""
        pygame.init()
        self.config = GameConfig()
        
    def test_coconut_initialization(self):
        """Test that coconut initializes correctly."""
        coconut = Coconut(self.config)
        
        assert coconut.config == self.config
        assert isinstance(coconut.pos, pygame.Vector2)
        assert 0 <= coconut.pos.x < self.config.cell_number_x
        assert 0 <= coconut.pos.y < self.config.cell_number_y
    
    def test_coconut_randomize(self):
        """Test that coconut randomizes position correctly."""
        coconut = Coconut(self.config)
        
        # Randomize multiple times to check bounds
        for _ in range(10):
            coconut.randomize()
            assert 0 <= coconut.pos.x < self.config.cell_number_x
            assert 0 <= coconut.pos.y < self.config.cell_number_y
    
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('pygame.draw.circle')
    def test_coconut_draw(self, mock_circle, mock_line, mock_ellipse):
        """Test that coconut drawing calls pygame functions correctly."""
        coconut = Coconut(self.config)
        mock_screen = Mock()
        
        coconut.draw_coconut(mock_screen)
        
        # Check that drawing functions were called
        assert mock_ellipse.called
        assert mock_line.called
        assert mock_circle.called
        
        # Check ellipse call (coconut body)
        ellipse_call = mock_ellipse.call_args
        assert ellipse_call[0][1] == Color.COCONUT_BROWN
        
        # Check circle calls (coconut eyes - should be called 3 times)
        assert mock_circle.call_count == 3
        for call in mock_circle.call_args_list:
            assert call[0][1] == Color.BLACK


class TestSnakeCoconutInteraction:
    def setup_method(self):
        """Setup test fixtures before each test method."""
        pygame.init()
        self.config = GameConfig()
        self.snake = Snake(self.config)
    
    def test_snake_remove_block(self):
        """Test that snake can remove a block."""
        initial_length = len(self.snake.body)
        
        # Add a block first
        self.snake.add_block()
        self.snake.move_snake()
        assert len(self.snake.body) == initial_length + 1
        
        # Now remove a block (coconut removes 1 segment)
        self.snake.remove_block()
        self.snake.move_snake()
        # After removing, we should be back to original length (since we remove 1 segment)
        assert len(self.snake.body) == initial_length
    
    def test_snake_remove_block_minimum_length(self):
        """Test that snake doesn't go below minimum length."""
        # Create snake with minimum length
        self.snake.body = [pygame.Vector2(5, 5)]
        
        self.snake.remove_block()
        self.snake.move_snake()
        
        # Snake should still have at least 1 segment
        assert len(self.snake.body) >= 1


class TestGameCoconutFeature:
    def setup_method(self):
        """Setup test fixtures before each test method."""
        pygame.init()
        self.config = GameConfig()
        self.game = Game(self.config)
    
    def test_game_coconut_initialization(self):
        """Test that game initializes without coconut."""
        assert self.game.coconut is None
        assert self.game.current_speed == self.config.snake_speed
    
    @patch('random.random')
    def test_coconut_spawning(self, mock_random):
        """Test coconut spawning when eating apple."""
        # Mock random to trigger coconut spawn
        mock_random.return_value = 0.1  # Less than coconut_spawn_chance
        
        # Position snake head at food position
        self.game.snake.body[0] = self.game.food.pos.copy()
        
        # Check collision
        self.game.check_collision()
        
        # Coconut should have spawned
        assert self.game.coconut is not None
        assert isinstance(self.game.coconut, Coconut)
    
    @patch('random.random')
    def test_coconut_not_spawning(self, mock_random):
        """Test coconut not spawning when probability is low."""
        # Mock random to prevent coconut spawn
        mock_random.return_value = 0.9  # Greater than coconut_spawn_chance
        
        # Position snake head at food position
        self.game.snake.body[0] = self.game.food.pos.copy()
        
        # Check collision
        self.game.check_collision()
        
        # Coconut should not have spawned
        assert self.game.coconut is None
    
    def test_coconut_collision_effects(self):
        """Test effects of eating coconut."""
        # Create and position coconut
        self.game.coconut = Coconut(self.config)
        self.game.snake.body[0] = self.game.coconut.pos.copy()
        
        initial_speed = self.game.current_speed
        initial_score = self.game.score
        
        # Check collision
        self.game.check_collision()
        
        # Verify effects
        assert self.game.coconut is None  # Coconut should be consumed
        assert self.game.current_speed < initial_speed  # Speed should increase
        assert self.game.score == initial_score + 2  # Score should increase by 2
    
    def test_speed_increase_mechanism(self):
        """Test that speed increase works correctly."""
        initial_speed = self.game.current_speed
        
        self.game.increase_speed()
        
        expected_speed = max(self.config.min_snake_speed, 
                           initial_speed - self.config.speed_increase)
        assert self.game.current_speed == expected_speed
    
    def test_speed_minimum_limit(self):
        """Test that speed doesn't go below minimum."""
        # Set speed near minimum
        self.game.current_speed = self.config.min_snake_speed + 5
        
        # Try to increase speed multiple times
        for _ in range(10):
            self.game.increase_speed()
        
        # Speed should not go below minimum
        assert self.game.current_speed >= self.config.min_snake_speed
    
    def test_restart_game_resets_coconut_state(self):
        """Test that restarting game resets coconut-related state."""
        # Modify game state
        self.game.coconut = Coconut(self.config)
        self.game.current_speed = 100
        
        # Restart game
        self.game.restart_game()
        
        # Verify reset
        assert self.game.coconut is None
        assert self.game.current_speed == self.config.snake_speed
    
    def test_ensure_coconut_not_on_snake(self):
        """Test that coconut doesn't spawn on snake body."""
        # Create coconut at snake position
        self.game.coconut = Coconut(self.config)
        self.game.coconut.pos = self.game.snake.body[0].copy()
        
        # Ensure it moves away from snake
        self.game.ensure_coconut_not_on_snake()
        
        # Coconut should not be on any snake segment
        for segment in self.game.snake.body:
            assert self.game.coconut.pos != segment


if __name__ == "__main__":
    pytest.main([__file__])