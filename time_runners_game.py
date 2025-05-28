import pygame
import sys
import random
import os
from collections import deque

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 1
JUMP_STRENGTH = -15
SCROLL_SPEED = 5
OBSTACLE_SPEED = 5
TIMELINE_HEIGHT = SCREEN_HEIGHT // 2
DELAY_FRAMES = 2 * FPS  # 2 seconds delay at 60 FPS
SLOW_MO_DISTANCE = 150  # Distance to trigger slow motion
SLOW_MO_FACTOR = 0.5    # Slow motion speed factor

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GRAY = (200, 200, 200)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Time Runners: Paradox Shift")
clock = pygame.time.Clock()

# Load fonts
font = pygame.font.SysFont("Arial", 24)
large_font = pygame.font.SysFont("Arial", 48)
small_font = pygame.font.SysFont("Arial", 18)

# Create directory for music and sound effects if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"), exist_ok=True)

# Music and sound effects
try:
    # We'll create placeholder music files - in a real game you'd replace these with actual files
    pygame.mixer.music.load(os.path.join("assets", "background_music.mp3"))
    jump_sound = pygame.mixer.Sound(os.path.join("assets", "jump.wav"))
    slow_mo_sound = pygame.mixer.Sound(os.path.join("assets", "slow_mo.wav"))
    game_over_sound = pygame.mixer.Sound(os.path.join("assets", "game_over.wav"))
except:
    print("Music files not found. Game will run without sound.")
    # Create dummy sound objects to avoid errors
    class DummySound:
        def play(self): pass
        def stop(self): pass
    jump_sound = DummySound()
    slow_mo_sound = DummySound()
    game_over_sound = DummySound()

class Runner:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 40
        self.color = color
        self.vel_y = 0
        self.is_jumping = False
        self.is_alive = True
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.trail_positions = []  # Store previous positions for trail effect
        
    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_STRENGTH
            self.is_jumping = True
            jump_sound.play()
    
    def update(self, ground_y, time_factor=1.0):
        # Store current position for trail effect (only during slow-mo)
        if time_factor < 1.0 and pygame.time.get_ticks() % 5 == 0:
            self.trail_positions.append((self.x, self.y))
            # Keep only the last 10 positions
            if len(self.trail_positions) > 10:
                self.trail_positions.pop(0)
                
        # Apply gravity with time factor
        self.vel_y += GRAVITY * time_factor
        self.y += self.vel_y * time_factor
        
        # Check ground collision
        if self.y + self.height > ground_y:
            self.y = ground_y - self.height
            self.vel_y = 0
            self.is_jumping = False
        
        # Update animation frame
        self.animation_frame += self.animation_speed * time_factor
        if self.animation_frame >= 4:
            self.animation_frame = 0
    
    def draw(self, surface, time_distortion=0):
        # Draw trail effect during slow-mo
        if time_distortion > 0 and self.trail_positions:
            for i, (trail_x, trail_y) in enumerate(self.trail_positions):
                alpha = int(100 * (i / len(self.trail_positions)) * time_distortion)
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                # Draw a simplified stick figure silhouette
                pygame.draw.circle(s, (*self.color, alpha), (self.width // 2, 10), 8)
                pygame.draw.line(s, (*self.color, alpha), (self.width // 2, 20), (self.width // 2, 30), 2)
                surface.blit(s, (trail_x, trail_y))
        
        # Draw stick figure with animation
        frame = int(self.animation_frame)
        
        # Apply time distortion effect (glowing/flickering when in slow-mo)
        color = self.color
        if time_distortion > 0:
            # Make the character glow/flicker in slow motion
            brightness = 150 + int(100 * abs(math.sin(pygame.time.get_ticks() * 0.01)))
            color = (min(255, self.color[0] + brightness // 3), 
                     min(255, self.color[1] + brightness // 3), 
                     min(255, self.color[2] + brightness // 3))
        
        # Head
        pygame.draw.circle(surface, color, (self.x + self.width // 2, self.y + 10), 10)
        
        # Body
        pygame.draw.line(surface, color, 
                        (self.x + self.width // 2, self.y + 20), 
                        (self.x + self.width // 2, self.y + 30), 2)
        
        # Arms - animate based on running/jumping
        arm_angle = math.sin(self.animation_frame * 2) * 0.5 if not self.is_jumping else -0.2
        pygame.draw.line(surface, color, 
                        (self.x + self.width // 2, self.y + 25), 
                        (self.x + self.width // 2 - 10 * math.cos(arm_angle), 
                         self.y + 20 - 5 * math.sin(arm_angle)), 2)
        pygame.draw.line(surface, color, 
                        (self.x + self.width // 2, self.y + 25), 
                        (self.x + self.width // 2 + 10 * math.cos(arm_angle), 
                         self.y + 20 - 5 * math.sin(arm_angle)), 2)
        
        # Legs - animate based on running/jumping
        if self.is_jumping:
            # Tucked position for jumping
            pygame.draw.line(surface, color, 
                            (self.x + self.width // 2, self.y + 30), 
                            (self.x + self.width // 2 - 8, self.y + 35), 2)
            pygame.draw.line(surface, color, 
                            (self.x + self.width // 2, self.y + 30), 
                            (self.x + self.width // 2 + 8, self.y + 35), 2)
        else:
            # Running animation
            leg_angle = math.sin(self.animation_frame * 2)
            pygame.draw.line(surface, color, 
                            (self.x + self.width // 2, self.y + 30), 
                            (self.x + self.width // 2 - 10 * math.cos(leg_angle), 
                             self.y + 40 - 5 * math.sin(leg_angle)), 2)
            pygame.draw.line(surface, color, 
                            (self.x + self.width // 2, self.y + 30), 
                            (self.x + self.width // 2 + 10 * math.cos(-leg_angle), 
                             self.y + 40 - 5 * math.sin(-leg_angle)), 2)
        
        # Draw time distortion effect
        if time_distortion > 0:
            # Draw echo/trail effect
            alpha = int(100 * time_distortion)
            s = pygame.Surface((self.width * 2, self.height * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (self.width, 10), 12)
            surface.blit(s, (self.x - self.width // 2, self.y))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Obstacle:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.pulse = 0
    
    def update(self, speed_factor=1.0):
        self.x -= OBSTACLE_SPEED * speed_factor
        self.pulse = (self.pulse + 0.05 * speed_factor) % (2 * math.pi)
    
    def draw(self, surface, time_distortion=0):
        # Base obstacle
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw spikes on top with pulsing effect in slow motion
        pulse_intensity = 0
        if time_distortion > 0:
            pulse_intensity = math.sin(self.pulse) * 3 * time_distortion
        
        for i in range(self.width // 10):
            pygame.draw.polygon(surface, self.color, [
                (self.x + i * 10, self.y),
                (self.x + i * 10 + 5, self.y - 10 - pulse_intensity),
                (self.x + i * 10 + 10, self.y)
            ])
            
        # Draw time distortion effect
        if time_distortion > 0:
            # Draw glowing outline
            glow_color = (255, 255, 0, int(100 * time_distortion))
            s = pygame.Surface((self.width + 10, self.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(s, glow_color, (0, 10, self.width + 10, self.height))
            surface.blit(s, (self.x - 5, self.y - 10))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y - 10, self.width, self.height + 10)

class Particle:
    def __init__(self, x, y, color, timeline="present"):
        self.x = x
        self.y = y
        self.color = color
        self.timeline = timeline
        self.size = random.randint(2, 5)
        self.speed_x = random.uniform(-1, 1)
        self.speed_y = random.uniform(-2, 0)
        self.lifetime = random.randint(20, 40)
        self.pulse = random.random() * math.pi * 2  # Random starting phase
    
    def update(self, time_factor=1.0):
        self.x += self.speed_x * time_factor
        self.y += self.speed_y * time_factor
        self.lifetime -= time_factor
        self.size = max(0, self.size - 0.05 * time_factor)
        self.pulse = (self.pulse + 0.1 * time_factor) % (math.pi * 2)
    
    def draw(self, surface):
        if self.lifetime > 0 and self.size > 0:
            # Add pulsing effect
            pulse_factor = (math.sin(self.pulse) + 1) / 2  # Value between 0 and 1
            size_with_pulse = self.size * (0.8 + 0.4 * pulse_factor)
            
            alpha = int(255 * (self.lifetime / 40))
            s = pygame.Surface((int(size_with_pulse * 2), int(size_with_pulse * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(size_with_pulse), int(size_with_pulse)), int(size_with_pulse))
            surface.blit(s, (int(self.x - size_with_pulse), int(self.y - size_with_pulse)))

class Game:
    def __init__(self):
        self.reset()
        self.show_intro = True
        self.intro_page = 0
        self.story_text = [
            # Page 1
            [
                "THE YEAR IS 2157.",
                "DR. ELARA CHEN, A BRILLIANT QUANTUM PHYSICIST,",
                "HAS DISCOVERED A WAY TO MANIPULATE THE FABRIC OF TIME.",
                "",
                "A CATASTROPHIC EVENT IS ABOUT TO DESTROY HUMANITY."
            ],
            # Page 2
            [
                "USING HER EXPERIMENTAL TECHNOLOGY,",
                "DR. CHEN CREATES A TEMPORAL PARADOX.",
                "",
                "BY RUNNING THROUGH BOTH TIMELINES SIMULTANEOUSLY -",
                "ONE IN THE PRESENT AND ONE 2 SECONDS IN THE PAST -",
                "SHE HOPES TO FIND THE EXACT MOMENT TO PREVENT THE DISASTER."
            ],
            # Page 3
            [
                "BUT THE UNIVERSE DOESN'T LIKE PARADOXES...",
                "REALITY ITSELF IS FIGHTING BACK WITH TEMPORAL ANOMALIES.",
                "",
                "CAN YOU HELP DR. CHEN NAVIGATE BOTH TIMELINES",
                "LONG ENOUGH TO SAVE HUMANITY FROM EXTINCTION?"
            ]
        ]
        
        # Try to start background music
        try:
            pygame.mixer.music.play(-1)  # Loop indefinitely
            pygame.mixer.music.set_volume(0.5)
        except:
            pass
    
    def reset(self):
        # Create runners
        self.present_runner = Runner(100, TIMELINE_HEIGHT - 100, BLUE)
        self.past_runner = Runner(100, SCREEN_HEIGHT - 100, RED)
        
        # Game state
        self.score = 0
        self.game_over = False
        self.slow_mo_active = False
        self.time_factor = 1.0
        
        # Obstacles
        self.present_obstacles = []
        self.past_obstacles = []
        
        # Store past actions for delayed replay
        self.action_history = deque(maxlen=DELAY_FRAMES + 1)
        for _ in range(DELAY_FRAMES + 1):
            self.action_history.append(False)  # No jump initially
        
        # Background elements
        self.present_bg_elements = []
        self.past_bg_elements = []
        
        # Initialize obstacle spawn timer
        self.obstacle_timer = 0
        self.obstacle_spawn_delay = 60  # frames
        
        # Particles
        self.particles = []
        
        # Milestone messages
        self.milestone_messages = {
            100: "TEMPORAL STABILITY AT 10%",
            500: "TIMELINE CONVERGENCE BEGINNING",
            1000: "QUANTUM FLUCTUATIONS DETECTED",
            2000: "TIMELINE STABILIZING",
            3000: "PARADOX RESOLUTION IMMINENT",
            5000: "HUMANITY'S FUTURE SECURED!"
        }
        self.current_milestone = None
        self.milestone_timer = 0
        
        # Reset slow-mo sound
        try:
            slow_mo_sound.stop()
        except:
            pass
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if self.show_intro:
                    self.intro_page += 1
                    if self.intro_page >= 3:  # 3 pages of story
                        self.show_intro = False
                elif event.key == pygame.K_SPACE and self.game_over:
                    self.reset()
        
        if self.show_intro:
            return
        
        # Record jump action for present runner
        keys = pygame.key.get_pressed()
        jump_pressed = keys[pygame.K_UP]
        
        if jump_pressed and not self.present_runner.is_jumping:
            self.present_runner.jump()
            
            # Create jump particles
            for _ in range(10):
                self.particles.append(Particle(
                    self.present_runner.x + self.present_runner.width // 2,
                    self.present_runner.y + self.present_runner.height,
                    BLUE,
                    "present"
                ))
        
        # Store the current action
        self.action_history.append(jump_pressed)
        
        # Get the delayed action for past runner
        past_action = self.action_history[0]
        if past_action and not self.past_runner.is_jumping:
            self.past_runner.jump()
            
            # Create jump particles
            for _ in range(10):
                self.particles.append(Particle(
                    self.past_runner.x + self.past_runner.width // 2,
                    self.past_runner.y + self.past_runner.height,
                    RED,
                    "past"
                ))
    
    def check_slow_motion(self):
        """Check if slow motion should be activated based on proximity to obstacles"""
        self.slow_mo_active = False
        min_distance = float('inf')
        
        # Check distance to obstacles in present timeline
        for obstacle in self.present_obstacles:
            if obstacle.x > self.present_runner.x:  # Only obstacles ahead
                distance = obstacle.x - (self.present_runner.x + self.present_runner.width)
                min_distance = min(min_distance, distance)
        
        # Check distance to obstacles in past timeline
        for obstacle in self.past_obstacles:
            if obstacle.x > self.past_runner.x:  # Only obstacles ahead
                distance = obstacle.x - (self.past_runner.x + self.past_runner.width)
                min_distance = min(min_distance, distance)
        
        # Activate slow motion if close to an obstacle
        if min_distance < SLOW_MO_DISTANCE:
            self.slow_mo_active = True
            # Calculate time factor based on distance (closer = slower)
            self.time_factor = SLOW_MO_FACTOR + (1.0 - SLOW_MO_FACTOR) * (min_distance / SLOW_MO_DISTANCE)
            
            # Play slow-mo sound if not already playing
            try:
                slow_mo_sound.play(-1)  # Loop
            except:
                pass
                
            # Create time distortion particles
            if random.random() < 0.2:
                for _ in range(3):
                    timeline = random.choice(["present", "past"])
                    if timeline == "present":
                        x = random.randint(0, SCREEN_WIDTH)
                        y = random.randint(0, TIMELINE_HEIGHT)
                        color = (100, 100, 255)  # Light blue
                    else:
                        x = random.randint(0, SCREEN_WIDTH)
                        y = random.randint(TIMELINE_HEIGHT, SCREEN_HEIGHT)
                        color = (255, 100, 100)  # Light red
                    self.particles.append(Particle(x, y, color, timeline))
        else:
            self.time_factor = 1.0
            try:
                slow_mo_sound.stop()
            except:
                pass
    
    def update(self):
        if self.show_intro or self.game_over:
            return
        
        # Check for slow motion
        self.check_slow_motion()
        
        # Update runners with time factor
        self.present_runner.update(TIMELINE_HEIGHT - 60, self.time_factor)
        self.past_runner.update(SCREEN_HEIGHT - 60, self.time_factor)
        
        # Spawn obstacles
        self.obstacle_timer += self.time_factor
        if self.obstacle_timer >= self.obstacle_spawn_delay:
            self.obstacle_timer = 0
            self.obstacle_spawn_delay = random.randint(45, 90)  # Random spawn delay
            
            # Create obstacles with same pattern in both timelines
            obstacle_width = random.randint(30, 80)
            
            present_obstacle = Obstacle(
                SCREEN_WIDTH, 
                TIMELINE_HEIGHT - 60, 
                obstacle_width, 
                20, 
                RED
            )
            
            past_obstacle = Obstacle(
                SCREEN_WIDTH, 
                SCREEN_HEIGHT - 60, 
                obstacle_width, 
                20, 
                RED
            )
            
            self.present_obstacles.append(present_obstacle)
            self.past_obstacles.append(past_obstacle)
        
        # Update obstacles with time factor
        for obstacle in self.present_obstacles[:]:
            obstacle.update(self.time_factor)
            if obstacle.x + obstacle.width < 0:
                self.present_obstacles.remove(obstacle)
        
        for obstacle in self.past_obstacles[:]:
            obstacle.update(self.time_factor)
            if obstacle.x + obstacle.width < 0:
                self.past_obstacles.remove(obstacle)
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(self.time_factor)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Check collisions
        for obstacle in self.present_obstacles:
            if self.present_runner.get_rect().colliderect(obstacle.get_rect()):
                self.game_over = True
                try:
                    game_over_sound.play()
                    pygame.mixer.music.stop()
                except:
                    pass
                
                # Create explosion particles
                for _ in range(30):
                    self.particles.append(Particle(
                        self.present_runner.x + self.present_runner.width // 2,
                        self.present_runner.y + self.present_runner.height // 2,
                        YELLOW,
                        "present"
                    ))
        
        for obstacle in self.past_obstacles:
            if self.past_runner.get_rect().colliderect(obstacle.get_rect()):
                self.game_over = True
                try:
                    game_over_sound.play()
                    pygame.mixer.music.stop()
                except:
                    pass
                
                # Create explosion particles
                for _ in range(30):
                    self.particles.append(Particle(
                        self.past_runner.x + self.past_runner.width // 2,
                        self.past_runner.y + self.past_runner.height // 2,
                        YELLOW,
                        "past"
                    ))
        
        # Update score
        if not self.game_over:
            self.score += self.time_factor  # Score increases slower during slow-mo
            
            # Check for milestones
            for milestone in sorted(self.milestone_messages.keys()):
                if int(self.score) >= milestone and (self.current_milestone is None or milestone > self.current_milestone):
                    self.current_milestone = milestone
                    self.milestone_timer = 180  # Show for 3 seconds at 60 FPS
                    break
        
        # Update milestone timer
        if self.milestone_timer > 0:
            self.milestone_timer -= self.time_factor
    
    def draw_intro(self):
        screen.fill(BLACK)
        
        # Create a stylish background with time-themed elements
        # Draw some particle effects for aesthetics
        for i in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            alpha = random.randint(50, 200)
            color = random.choice([BLUE, RED, PURPLE])
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (size, size), size)
            screen.blit(s, (x, y))
        
        # Draw decorative time lines
        for i in range(5):
            y = random.randint(0, SCREEN_HEIGHT)
            width = random.randint(50, 200)
            alpha = random.randint(20, 80)
            s = pygame.Surface((width, 1), pygame.SRCALPHA)
            s.fill((255, 255, 255, alpha))
            screen.blit(s, (random.randint(0, SCREEN_WIDTH - width), y))
        
        # Add a semi-transparent overlay for better text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Title with glow effect
        title_shadow = large_font.render("TIME RUNNERS: PARADOX SHIFT", True, PURPLE)
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_shadow.get_width() // 2 + 2, 52))
        title_text = large_font.render("TIME RUNNERS: PARADOX SHIFT", True, YELLOW)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        
        # Draw a decorative line under the title
        pygame.draw.line(screen, YELLOW, 
                        (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100),
                        (SCREEN_WIDTH // 2 + title_text.get_width() // 2, 100), 2)
        
        # Story text - now using the nested list structure
        story_lines = self.story_text[self.intro_page]
        
        # Create a stylish text box
        text_box_width = 600
        text_box_height = 300
        text_box_x = (SCREEN_WIDTH - text_box_width) // 2
        text_box_y = 150
        
        # Draw text box background
        s = pygame.Surface((text_box_width, text_box_height), pygame.SRCALPHA)
        s.fill((0, 0, 50, 150))
        pygame.draw.rect(s, (100, 100, 255, 100), (0, 0, text_box_width, text_box_height), 2)
        screen.blit(s, (text_box_x, text_box_y))
        
        # Draw story text
        y_pos = text_box_y + 40
        for line in story_lines:
            if line:  # Skip empty lines
                text = font.render(line, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_pos))
            y_pos += 35
        
        # Page indicator
        page_text = small_font.render(f"PAGE {self.intro_page + 1}/3", True, LIGHT_GRAY)
        screen.blit(page_text, (SCREEN_WIDTH - page_text.get_width() - 20, SCREEN_HEIGHT - 40))
        
        # Continue prompt with pulsing effect
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2  # Value between 0 and 1
        continue_color = (255, 255, 0, int(155 + 100 * pulse))
        s = pygame.Surface((400, 40), pygame.SRCALPHA)
        continue_text = font.render("PRESS ANY KEY TO CONTINUE", True, continue_color)
        s.blit(continue_text, (200 - continue_text.get_width() // 2, 20 - continue_text.get_height() // 2))
        screen.blit(s, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 100))
        
        pygame.display.flip()
    
    def draw(self):
        if self.show_intro:
            self.draw_intro()
            return
            
        # Clear screen
        screen.fill(BLACK)
        
        # Draw stylish background elements
        # Stars/particles in the background
        for i in range(10):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, TIMELINE_HEIGHT - 60)
            size = random.randint(1, 2)
            pygame.draw.circle(screen, WHITE, (x, y), size)
            
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(TIMELINE_HEIGHT, SCREEN_HEIGHT - 60)
            size = random.randint(1, 2)
            pygame.draw.circle(screen, WHITE, (x, y), size)
        
        # Draw dividing line with glow effect
        if self.slow_mo_active:
            # Glowing divider during slow-mo
            glow_surf = pygame.Surface((SCREEN_WIDTH, 10), pygame.SRCALPHA)
            glow_color = (200, 200, 255, 150)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, SCREEN_WIDTH, 10))
            screen.blit(glow_surf, (0, TIMELINE_HEIGHT - 5))
        
        pygame.draw.line(screen, WHITE, (0, TIMELINE_HEIGHT), (SCREEN_WIDTH, TIMELINE_HEIGHT), 2)
        
        # Draw present timeline (top half) with gradient effect
        present_bg = pygame.Surface((SCREEN_WIDTH, TIMELINE_HEIGHT))
        for y in range(TIMELINE_HEIGHT - 60):
            # Create a subtle gradient from dark blue to light blue
            color_value = 20 + int(80 * (y / (TIMELINE_HEIGHT - 60)))
            pygame.draw.line(present_bg, (0, 0, color_value), (0, y), (SCREEN_WIDTH, y))
        screen.blit(present_bg, (0, 0))
        
        # Ground for present timeline
        pygame.draw.rect(screen, GREEN, (0, TIMELINE_HEIGHT - 60, SCREEN_WIDTH, 60))
        # Add texture to ground
        for i in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = TIMELINE_HEIGHT - 60 + random.randint(5, 55)
            width = random.randint(5, 20)
            height = random.randint(2, 5)
            pygame.draw.rect(screen, (0, 100, 0), (x, y, width, height))
        
        # Draw past timeline (bottom half) with gradient effect
        past_bg = pygame.Surface((SCREEN_WIDTH, TIMELINE_HEIGHT))
        for y in range(TIMELINE_HEIGHT):
            # Create a subtle gradient from dark gray to light gray
            color_value = 20 + int(60 * (y / TIMELINE_HEIGHT))
            pygame.draw.line(past_bg, (color_value, color_value, color_value), (0, y), (SCREEN_WIDTH, y))
        screen.blit(past_bg, (0, TIMELINE_HEIGHT))
        
        # Ground for past timeline
        pygame.draw.rect(screen, GRAY, (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))
        # Add texture to ground
        for i in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT - 60 + random.randint(5, 55)
            width = random.randint(5, 20)
            height = random.randint(2, 5)
            pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height))
        
        # Draw timeline labels with stylish backgrounds
        present_label = pygame.Surface((120, 30), pygame.SRCALPHA)
        present_label.fill((0, 0, 100, 150))
        pygame.draw.rect(present_label, BLUE, (0, 0, 120, 30), 1)
        screen.blit(present_label, (10, 10))
        present_text = font.render("PRESENT", True, WHITE)
        screen.blit(present_text, (20, 15))
        
        past_label = pygame.Surface((120, 30), pygame.SRCALPHA)
        past_label.fill((100, 0, 0, 150))
        pygame.draw.rect(past_label, RED, (0, 0, 120, 30), 1)
        screen.blit(past_label, (10, TIMELINE_HEIGHT + 10))
        past_text = font.render("PAST (-2s)", True, WHITE)
        screen.blit(past_text, (20, TIMELINE_HEIGHT + 15))
        
        # Draw slow-mo indicator with pulsing effect
        if self.slow_mo_active:
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2  # Value between 0 and 1
            slow_mo_bg = pygame.Surface((350, 30), pygame.SRCALPHA)
            slow_mo_bg.fill((128, 0, 128, int(100 + 50 * pulse)))
            pygame.draw.rect(slow_mo_bg, PURPLE, (0, 0, 350, 30), 1)
            screen.blit(slow_mo_bg, (SCREEN_WIDTH // 2 - 175, 10))
            slow_mo_text = font.render("TEMPORAL DISTORTION ACTIVE", True, WHITE)
            screen.blit(slow_mo_text, (SCREEN_WIDTH // 2 - slow_mo_text.get_width() // 2, 15))
        
        # Draw particles
        for particle in self.particles:
            particle.draw(screen)
        
        # Draw obstacles with time distortion effect if in slow-mo
        for obstacle in self.present_obstacles:
            time_distortion = 1.0 - self.time_factor if self.slow_mo_active else 0
            obstacle.draw(screen, time_distortion)
        
        for obstacle in self.past_obstacles:
            time_distortion = 1.0 - self.time_factor if self.slow_mo_active else 0
            obstacle.draw(screen, time_distortion)
        
        # Draw runners with time distortion effect if in slow-mo
        time_distortion = 1.0 - self.time_factor if self.slow_mo_active else 0
        self.present_runner.draw(screen, time_distortion)
        self.past_runner.draw(screen, time_distortion)
        
        # Draw score with stylish background
        score_bg = pygame.Surface((150, 30), pygame.SRCALPHA)
        score_bg.fill((0, 0, 0, 150))
        pygame.draw.rect(score_bg, WHITE, (0, 0, 150, 30), 1)
        screen.blit(score_bg, (SCREEN_WIDTH - 160, 10))
        score_text = font.render(f"SCORE: {int(self.score)}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - 150, 15))
        
        # Draw milestone message with stylish background
        if self.milestone_timer > 0:
            milestone_bg = pygame.Surface((500, 40), pygame.SRCALPHA)
            alpha = int(min(255, self.milestone_timer * 2))
            milestone_bg.fill((50, 50, 0, alpha))
            pygame.draw.rect(milestone_bg, YELLOW, (0, 0, 500, 40), 1)
            screen.blit(milestone_bg, (SCREEN_WIDTH // 2 - 250, TIMELINE_HEIGHT // 2 - 20))
            milestone_text = font.render(self.milestone_messages[self.current_milestone], True, YELLOW)
            screen.blit(milestone_text, (SCREEN_WIDTH // 2 - milestone_text.get_width() // 2, TIMELINE_HEIGHT // 2 - 10))
        
        # Draw game over message with stylish overlay
        if self.game_over:
            # Create a pulsing overlay
            pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 4 + 0.5  # Value between 0.5 and 1
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, int(150 * pulse)))
            screen.blit(overlay, (0, 0))
            
            # Create a stylish game over box
            game_over_box = pygame.Surface((500, 250), pygame.SRCALPHA)
            game_over_box.fill((0, 0, 0, 200))
            pygame.draw.rect(game_over_box, RED, (0, 0, 500, 250), 2)
            screen.blit(game_over_box, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 125))
            
            # Draw fracture lines to represent timeline collapse
            for i in range(10):
                start_x = SCREEN_WIDTH // 2 - 250 + random.randint(0, 500)
                start_y = SCREEN_HEIGHT // 2 - 125 + random.randint(0, 250)
                length = random.randint(20, 100)
                angle = random.uniform(0, 2 * math.pi)
                end_x = start_x + length * math.cos(angle)
                end_y = start_y + length * math.sin(angle)
                pygame.draw.line(screen, (255, 0, 0, 150), (start_x, start_y), (end_x, end_y), 1)
            
            game_over_text = large_font.render("TEMPORAL COLLAPSE", True, RED)
            score_final_text = font.render(f"TIMELINE STABILITY: {int(self.score)}", True, WHITE)
            restart_text = font.render("PRESS SPACE TO RESTART EXPERIMENT", True, YELLOW)
            
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            screen.blit(score_final_text, (SCREEN_WIDTH // 2 - score_final_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        
        # Update display
        pygame.display.flip()

# Add missing math module
import math

# Create game instance
game = Game()

# Main game loop
while True:
    game.handle_events()
    game.update()
    game.draw()
    clock.tick(FPS)
