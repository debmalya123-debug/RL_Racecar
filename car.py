import numpy as np
import pygame
import math

class Car:
    def __init__(self, color):
        self.color = color
        self.radars = [] # List of (length, angle_offset)
        self.trail = []  # List of (x, y)
        self.reset()
        
        # Car Sprite (Simple Triangle)
        self.width = 10
        self.length = 20

    def reset(self):
        self.x = 450 # Well ahead of finish line
        self.y = 150 # On the top straight
        self.angle = 0 # Facing Right (Clockwise)
        self.speed = 0
        self.alive = True
        self.distance = 0
        self.trail = []
        self.radars = []

    def step(self, steering, throttle):
        self.angle += steering * 0.1
        self.speed = max(0, min(6, self.speed + throttle * 0.25))

        dx = self.speed * np.cos(self.angle)
        dy = self.speed * np.sin(self.angle)

        self.x += dx
        self.y += dy
        self.distance += abs(self.speed)
        
        # Update trail
        if len(self.trail) == 0 or math.hypot(self.trail[-1][0] - self.x, self.trail[-1][1] - self.y) > 5:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 40:
                self.trail.pop(0)

    def draw(self, screen):
        # 1. Draw Sensors (Solid Triangle/Fan Look)
        if self.radars:
            # Create a transparent surface for the field of view
            # calculate bounding box to avoid creating full screen surface?
            # For simplicity, let's just make it screen size (sim is small enough).
            radar_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            
            # Construct polygon points: Center -> Ray 1 -> Ray 2 ... -> Ray N
            poly_points = [(self.x, self.y)]
            
            for r_len, r_angle in self.radars:
                end_x = self.x + math.cos(self.angle + r_angle) * r_len
                end_y = self.y + math.sin(self.angle + r_angle) * r_len
                poly_points.append((end_x, end_y))
            
            # Draw the filled fan
            # Use car color with low alpha
            poly_color = (*self.color, 60) # integer alpha 0-255
            if len(poly_points) > 2:
                pygame.draw.polygon(radar_surf, poly_color, poly_points)
            
            screen.blit(radar_surf, (0, 0))

            # Draw the distinct rays (borders) for clarity
            for r_len, r_angle in self.radars:
                end_x = int(self.x + math.cos(self.angle + r_angle) * r_len)
                end_y = int(self.y + math.sin(self.angle + r_angle) * r_len)
                
                # Dynamic dot color (Red = Close, Green = Far)
                dist_ratio = r_len / 200 # max range approximately
                dot_color = (
                    int(255 * (1 - dist_ratio)), 
                    int(255 * dist_ratio), 
                    0
                )
                
                # Slight line glow
                pygame.draw.line(screen, (*self.color, 100), (self.x, self.y), (end_x, end_y), 1)
                pygame.draw.circle(screen, dot_color, (end_x, end_y), 3)

        # 2. Draw Trail
        if len(self.trail) > 1:
            pygame.draw.lines(screen, self.color, False, self.trail, 2)

        # 3. Draw Car (Triangle)
        # Calculate vertices
        tip_x = self.x + math.cos(self.angle) * 10
        tip_y = self.y + math.sin(self.angle) * 10
        
        left_x = self.x + math.cos(self.angle + 2.5) * 8
        left_y = self.y + math.sin(self.angle + 2.5) * 8
        
        right_x = self.x + math.cos(self.angle - 2.5) * 8
        right_y = self.y + math.sin(self.angle - 2.5) * 8
        
        pygame.draw.polygon(screen, self.color, [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)])
