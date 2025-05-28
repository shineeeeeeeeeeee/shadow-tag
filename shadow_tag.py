import pygame
import sys
import random
import math
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 200)
BLUE = (50, 50, 255)
GRAY = (50, 50, 50)

# Game settings
PLAYER_SPEED = 5
SHADOW_SPEED = 2
INITIAL_LIGHT_RADIUS = 150
LIGHT_SHRINK_RATE = 0.05  # How much the light radius shrinks per second
MIN_LIGHT_RADIUS = 30
SHADOW_COUNT = 5
SHADOW_SIZE = 15
PLAYER_SIZE = 10

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shadow Tag")
clock = pygame.time.Clock()

# Load fonts
font = pygame.font.SysFont("Arial", 24)
large_font = pygame.font.SysFont("Arial", 48)
small_font = pygame.font.SysFont("Arial", 16)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_SIZE
        self.light_radius = INITIAL_LIGHT_RADIUS
        self.speed = PLAYER_SPEED
        self.base_color = YELLOW
        self.color = self.base_color
        self.move_sound_timer = 0
        self.last_pos = (x, y)
    
    def update(self, keys):
        # Store previous position to detect movement
        self.last_pos = (self.x, self.y)
        
        # Handle movement
        if keys[pygame.K_LEFT] and self.x - self.radius > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x + self.radius < SCREEN_WIDTH:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y - self.radius > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y + self.radius < SCREEN_HEIGHT:
            self.y += self.speed
        
        # Shrink light radius over time
        self.light_radius = max(MIN_LIGHT_RADIUS, self.light_radius - LIGHT_SHRINK_RATE)
        
        # Update light color based on remaining light
        light_percent = (self.light_radius - MIN_LIGHT_RADIUS) / (INITIAL_LIGHT_RADIUS - MIN_LIGHT_RADIUS) * 100
        if light_percent > 60:
            self.color = YELLOW  # Full yellow when light is strong
        elif light_percent > 30:
            # Transition from yellow to orange
            orange_factor = (60 - light_percent) / 30  # 0 to 1
            self.color = (
                255,  # Red stays at 255
                255 - int(90 * orange_factor),  # Green decreases
                200 - int(150 * orange_factor)  # Blue decreases
            )
        else:
            # Transition from orange to red
            red_factor = (30 - light_percent) / 30  # 0 to 1
            self.color = (
                255,  # Red stays at 255
                165 - int(165 * red_factor),  # Green decreases to 0
                50 - int(50 * red_factor)  # Blue decreases to 0
            )
            
            # Make light pulse when critically low
            if light_percent < 15 and pygame.time.get_ticks() % 1000 < 500:
                pulse_factor = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.01)
                self.color = (
                    min(255, int(self.color[0] * pulse_factor)),
                    min(255, int(self.color[1] * pulse_factor)),
                    min(255, int(self.color[2] * pulse_factor))
                )
        
        # Play movement sound occasionally if player is moving
        if (self.x, self.y) != self.last_pos:
            self.move_sound_timer += 1
            if self.move_sound_timer >= 20:  # Play sound every 20 frames of movement
                self.move_sound_timer = 0
                try:
                    # Try to play the movement sound if it exists
                    if hasattr(pygame.mixer, 'Channel'):
                        channel = pygame.mixer.Channel(1)  # Use channel 1 for movement sounds
                        channel.set_volume(0.2)  # Lower volume for movement
                        channel.play(pygame.mixer.Sound(os.path.join("assets", "move.wav")))
                except:
                    pass  # Silently fail if sound doesn't exist
    
    def draw(self, surface):
        # Draw light radius (semi-transparent)
        light_surface = pygame.Surface((self.light_radius * 2, self.light_radius * 2), pygame.SRCALPHA)
        
        # Create gradient light effect with current color
        for r in range(int(self.light_radius), 0, -1):
            # Calculate alpha and color for this ring of the gradient
            alpha = max(0, min(150 - r // 2, 150))  # Fade out towards the edge
            
            # Get base color components
            r_val, g_val, b_val = self.color
            
            # Create gradient that fades to white at center
            if r < self.light_radius * 0.3:  # Inner 30% transitions to white
                white_factor = 1 - (r / (self.light_radius * 0.3))
                r_val = min(255, int(r_val + (255 - r_val) * white_factor))
                g_val = min(255, int(g_val + (255 - g_val) * white_factor))
                b_val = min(255, int(b_val + (255 - b_val) * white_factor))
            
            pygame.draw.circle(light_surface, (r_val, g_val, b_val, alpha), 
                              (self.light_radius, self.light_radius), r)
        
        surface.blit(light_surface, (self.x - self.light_radius, self.y - self.light_radius))
        
        # Draw player orb with current color
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
        
        # Add a small white center for visual interest
        pygame.draw.circle(surface, WHITE, (self.x, self.y), self.radius // 2)
        
        # Add a subtle glow effect
        glow_surface = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        for r in range(self.radius * 2, 0, -1):
            alpha = max(0, min(100 - r * 5, 100))
            pygame.draw.circle(glow_surface, (*self.color, alpha // 4), 
                              (self.radius * 2, self.radius * 2), r)
        surface.blit(glow_surface, (self.x - self.radius * 2, self.y - self.radius * 2))
    
    def collides_with(self, shadow):
        # Check if player touches shadow
        distance = math.sqrt((self.x - shadow.x) ** 2 + (self.y - shadow.y) ** 2)
        return distance < self.radius + shadow.radius

class Shadow:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = SHADOW_SIZE
        self.speed = SHADOW_SPEED
        self.color = GRAY
        self.direction = random.uniform(0, 2 * math.pi)
        self.change_direction_counter = 0
        self.tagged = False
        self.fade_out = 255  # For fade out animation when tagged
    
    def update(self, player):
        if self.tagged:
            # Fade out animation when tagged
            self.fade_out -= 15
            if self.fade_out <= 0:
                self.fade_out = 0
            return
        
        # Calculate distance to player
        distance = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
        
        # Change direction occasionally
        self.change_direction_counter += 1
        if self.change_direction_counter > random.randint(30, 90):
            self.direction = random.uniform(0, 2 * math.pi)
            self.change_direction_counter = 0
        
        # Move away from player if within light radius
        if distance < player.light_radius:
            # Calculate angle to player
            angle_to_player = math.atan2(player.y - self.y, player.x - self.x)
            
            # Move in opposite direction (away from player)
            self.direction = angle_to_player + math.pi
            
            # Slow down when in light
            light_factor = distance / player.light_radius  # 0 when at player, 1 when at edge of light
            current_speed = self.speed * max(0.2, light_factor)  # At least 20% of normal speed
        else:
            current_speed = self.speed
        
        # Move in current direction
        self.x += math.cos(self.direction) * current_speed
        self.y += math.sin(self.direction) * current_speed
        
        # Bounce off walls
        if self.x - self.radius < 0:
            self.x = self.radius
            self.direction = math.pi - self.direction
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.direction = math.pi - self.direction
            
        if self.y - self.radius < 0:
            self.y = self.radius
            self.direction = -self.direction
        elif self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.direction = -self.direction
    
    def draw(self, surface):
        if self.tagged and self.fade_out <= 0:
            return
        
        # Draw shadow with fade effect if tagged
        if self.tagged:
            alpha = self.fade_out
            shadow_color = (self.color[0], self.color[1], self.color[2], alpha)
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, shadow_color, (self.radius, self.radius), self.radius)
            surface.blit(s, (self.x - self.radius, self.y - self.radius))
        else:
            pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
            # Add some texture to shadows
            for i in range(3):
                offset_x = random.randint(-self.radius//2, self.radius//2)
                offset_y = random.randint(-self.radius//2, self.radius//2)
                size = random.randint(2, 4)
                pygame.draw.circle(surface, BLACK, 
                                  (int(self.x + offset_x), int(self.y + offset_y)), size)

class Game:
    def __init__(self):
        # Create assets directory if it doesn't exist
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"), exist_ok=True)
        
        # Load sounds (with error handling in case files don't exist)
        try:
            self.tag_sound = pygame.mixer.Sound(os.path.join("assets", "tag.wav"))
            self.light_low_sound = pygame.mixer.Sound(os.path.join("assets", "light_low.wav"))
            self.level_complete_sound = pygame.mixer.Sound(os.path.join("assets", "level_complete.wav"))
            self.game_over_sound = pygame.mixer.Sound(os.path.join("assets", "game_over.wav"))
            pygame.mixer.music.load(os.path.join("assets", "ambient.mp3"))
            self.sound_enabled = True
        except:
            print("Sound files not found. Game will run without sound.")
            # Create dummy sound objects to avoid errors
            class DummySound:
                def play(self): pass
                def stop(self): pass
            self.tag_sound = DummySound()
            self.light_low_sound = DummySound()
            self.level_complete_sound = DummySound()
            self.game_over_sound = DummySound()
            self.sound_enabled = False
        
        self.reset()
        
        # Start ambient music if available
        if self.sound_enabled:
            try:
                pygame.mixer.music.play(-1)  # Loop indefinitely
                pygame.mixer.music.set_volume(0.5)
            except:
                pass
        
        # Sound state tracking
        self.light_warning_played = False
    
    def reset(self):
        # Create player in center of screen
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Create shadows at random positions
        self.shadows = []
        for _ in range(SHADOW_COUNT):
            # Make sure shadows don't spawn too close to player
            while True:
                x = random.randint(SHADOW_SIZE, SCREEN_WIDTH - SHADOW_SIZE)
                y = random.randint(SHADOW_SIZE, SCREEN_HEIGHT - SHADOW_SIZE)
                distance = math.sqrt((x - self.player.x) ** 2 + (y - self.player.y) ** 2)
                if distance > self.player.light_radius:
                    break
            
            self.shadows.append(Shadow(x, y))
        
        # Game state
        self.game_over = False
        self.win = False
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.score = 0
        if not hasattr(self, 'level'):
            self.level = 1
        
        # Reset sound state tracking
        self.light_warning_played = False
        
        # Restart ambient music if it was stopped
        if self.sound_enabled and not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.5)
            except:
                pass
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and (self.game_over or self.win):
                    if self.win:
                        # Next level
                        self.level += 1
                        global SHADOW_COUNT, LIGHT_SHRINK_RATE
                        SHADOW_COUNT += 2  # More shadows each level
                        LIGHT_SHRINK_RATE += 0.01  # Light shrinks faster each level
                    self.reset()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_m:  # Toggle music
                    if self.sound_enabled:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()
                elif event.key == pygame.K_s:  # Toggle sound effects
                    self.sound_enabled = not self.sound_enabled
    
    def update(self):
        if self.game_over or self.win:
            return
        
        # Update timer
        self.elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000
        
        # Get keyboard input
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        
        # Update shadows
        active_shadows = 0
        for shadow in self.shadows:
            shadow.update(self.player)
            
            # Check for collision with player
            if not shadow.tagged and self.player.collides_with(shadow):
                shadow.tagged = True
                self.score += 100
                self.tag_sound.play()  # Play tag sound
            
            if not shadow.tagged:
                active_shadows += 1
        
        # Check win condition
        if active_shadows == 0:
            self.win = True
            self.level_complete_sound.play()  # Play level complete sound
        
        # Check if light is too small
        if self.player.light_radius <= MIN_LIGHT_RADIUS:
            self.game_over = True
            self.game_over_sound.play()  # Play game over sound
            pygame.mixer.music.stop()  # Stop ambient music
        
        # Play warning sound when light is getting low
        light_percent = (self.player.light_radius - MIN_LIGHT_RADIUS) / (INITIAL_LIGHT_RADIUS - MIN_LIGHT_RADIUS) * 100
        if light_percent < 25 and not self.light_warning_played:
            self.light_low_sound.play()
            self.light_warning_played = True
        elif light_percent >= 25:
            self.light_warning_played = False
    
    def draw(self):
        # Draw background
        screen.fill(BLACK)
        
        # Draw some subtle background elements
        for i in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 2)
            brightness = random.randint(5, 20)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
        
        # Draw shadows
        for shadow in self.shadows:
            shadow.draw(screen)
        
        # Draw player
        self.player.draw(screen)
        
        # Draw UI
        # Light meter
        light_percent = (self.player.light_radius - MIN_LIGHT_RADIUS) / (INITIAL_LIGHT_RADIUS - MIN_LIGHT_RADIUS) * 100
        meter_width = 200
        meter_height = 20
        pygame.draw.rect(screen, GRAY, (20, 20, meter_width, meter_height))
        
        # Make light meter color match the player's light color
        meter_color = self.player.color
            
        pygame.draw.rect(screen, meter_color, (20, 20, meter_width * light_percent / 100, meter_height))
        light_text = font.render("Light", True, WHITE)
        screen.blit(light_text, (20, 45))
        
        # Timer and score
        time_text = font.render(f"Time: {self.elapsed_time}s", True, WHITE)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        shadows_text = font.render(f"Shadows: {sum(1 for s in self.shadows if not s.tagged)}/{len(self.shadows)}", True, WHITE)
        
        screen.blit(time_text, (SCREEN_WIDTH - time_text.get_width() - 20, 20))
        screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 20, 50))
        screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 20, 80))
        screen.blit(shadows_text, (SCREEN_WIDTH - shadows_text.get_width() - 20, 110))
        
        # Sound controls info
        if pygame.time.get_ticks() % 10000 < 3000:  # Show periodically
            sound_text = small_font.render("Press M to toggle music, S to toggle sound effects", True, (150, 150, 150))
            screen.blit(sound_text, (20, SCREEN_HEIGHT - 30))
        
        # Game over / win message
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            game_over_text = large_font.render("DARKNESS CONSUMES YOU", True, WHITE)
            score_final_text = font.render(f"Final Score: {self.score}", True, WHITE)
            restart_text = font.render("Press SPACE to restart", True, YELLOW)
            
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            screen.blit(score_final_text, (SCREEN_WIDTH // 2 - score_final_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        
        elif self.win:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            win_text = large_font.render("LEVEL COMPLETE!", True, YELLOW)
            score_text = font.render(f"Score: {self.score}", True, WHITE)
            time_text = font.render(f"Time: {self.elapsed_time} seconds", True, WHITE)
            next_text = font.render("Press SPACE for next level", True, YELLOW)
            
            screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
            screen.blit(next_text, (SCREEN_WIDTH // 2 - next_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
        
        # Update display
        pygame.display.flip()

# Create game instance
game = Game()

# Main game loop
while True:
    game.handle_events()
    game.update()
    game.draw()
    clock.tick(FPS)
