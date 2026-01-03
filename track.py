import pygame
import math
import numpy as np

class Track:
    def __init__(self):
        self.width = 800
        self.height = 600

        # Colors
        self.bg_color = (10, 10, 20)
        self.track_color = (40, 40, 60)
        self.border_color = (0, 255, 255)
        self.finish_color = (255, 255, 255)

        # Geometry Config (Stadium Shape)
        self.center_left = (200, 300)
        self.center_right = (600, 300)
        self.outer_radius = 200
        self.inner_radius = 100
        self.track_width = self.outer_radius - self.inner_radius # 100

        # Start/Finish Line (Top Center)
        self.finish_x = 400
        self.finish_y = 150 # Top straight center
        self.finish_height = 100 # Track width
        
        # Barrier removed so cars can loop. 
        # We rely on the AI to learn direction from rewards.

        # Create mask surface
        self.track_surf = pygame.Surface((self.width, self.height))
        self.track_surf.fill((0, 0, 0))
        self._draw_track_shape(self.track_surf, (255, 255, 255)) 

    def _draw_track_shape(self, surface, color):
        """Helper to draw the defined stadium shape."""
        # 1. Left Turn (Outer)
        pygame.draw.circle(surface, color, self.center_left, self.outer_radius)
        # 2. Right Turn (Outer)
        pygame.draw.circle(surface, color, self.center_right, self.outer_radius)
        # 3. Connector (Outer)
        pygame.draw.rect(surface, color, (self.center_left[0], 300 - self.outer_radius, 
                                          self.center_right[0] - self.center_left[0], self.outer_radius * 2))

        # 4. Punch Hole (Inner - Black for mask)
        hole_color = (0, 0, 0)
        
        pygame.draw.circle(surface, hole_color, self.center_left, self.inner_radius)
        pygame.draw.circle(surface, hole_color, self.center_right, self.inner_radius)
        pygame.draw.rect(surface, hole_color, (self.center_left[0], 300 - self.inner_radius, 
                                               self.center_right[0] - self.center_left[0], self.inner_radius * 2))

    def on_track(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        try:
            return self.track_surf.get_at((int(x), int(y)))[0] > 128
        except:
            return False

    def get_radar(self, x, y, angle):
        length = 0
        max_len = 200
        step = 5
        dx = math.cos(angle) * step
        dy = math.sin(angle) * step
        curr_x, curr_y = x, y

        while length < max_len:
            curr_x += dx
            curr_y += dy
            length += step
            if not self.on_track(curr_x, curr_y):
                return length
        return max_len

    def hit_barrier(self, x, y):
        # No barrier
        return False

    def crossed_finish(self, prev_x, x, y):
        # Moving Right on Top Straight
        # Barrier is at X+20, so Finish is at X=400.
        # Check Y to be within top track section
        # Top center Y = 150. Width 100. Range: 100-200.
        if not (100 < y < 200):
            return False
            
        return (prev_x < self.finish_x <= x)

    def get_offset_from_center(self, x, y):
        """Returns distance from the ideal center line of the track."""
        # 1. Top Straight
        if 200 <= x <= 600 and y < 300:
            return abs(y - 150)
            
        # 2. Bottom Straight
        elif 200 <= x <= 600 and y >= 300:
            return abs(y - 450)
            
        # 3. Left Turn
        elif x < 200:
            dist = math.hypot(x - 200, y - 300)
            return abs(dist - 150)
            
        # 4. Right Turn
        elif x > 600:
            dist = math.hypot(x - 600, y - 300)
            return abs(dist - 150)
            
        return 0 # Should not happen if on track

    def draw(self, screen):
        screen.fill(self.bg_color)
        
        # 1. Main Track Body
        self._draw_track_shape(screen, self.track_color)
        
        # 2. Borders (Draw explicit outlines for neon look)
        # Outer Border
        self._draw_borders(screen)

        # 3. Checkered Finish Line
        self._draw_finish_line(screen)
        
        # 4. Barrier (Hidden or debug)
        # pygame.draw.rect(screen, (255, 0, 0), self.barrier_rect)

    def _draw_borders(self, screen):
        # Outer Arcs
        rect_left_out = (self.center_left[0]-self.outer_radius, self.center_left[1]-self.outer_radius, self.outer_radius*2, self.outer_radius*2)
        rect_right_out = (self.center_right[0]-self.outer_radius, self.center_right[1]-self.outer_radius, self.outer_radius*2, self.outer_radius*2)
        
        pygame.draw.arc(screen, self.border_color, rect_left_out, math.pi/2, 3*math.pi/2, 3)
        pygame.draw.arc(screen, self.border_color, rect_right_out, -math.pi/2, math.pi/2, 3)
        
        # Inner Arcs
        rect_left_in = (self.center_left[0]-self.inner_radius, self.center_left[1]-self.inner_radius, self.inner_radius*2, self.inner_radius*2)
        rect_right_in = (self.center_right[0]-self.inner_radius, self.center_right[1]-self.inner_radius, self.inner_radius*2, self.inner_radius*2)
        
        pygame.draw.arc(screen, self.border_color, rect_left_in, math.pi/2, 3*math.pi/2, 3)
        pygame.draw.arc(screen, self.border_color, rect_right_in, -math.pi/2, math.pi/2, 3)

        # Straight Lines
        # Top Outer
        pygame.draw.line(screen, self.border_color, (self.center_left[0], 300-self.outer_radius), (self.center_right[0], 300-self.outer_radius), 3)
        # Bottom Outer
        pygame.draw.line(screen, self.border_color, (self.center_left[0], 300+self.outer_radius), (self.center_right[0], 300+self.outer_radius), 3)
        # Top Inner
        pygame.draw.line(screen, self.border_color, (self.center_left[0], 300-self.inner_radius), (self.center_right[0], 300-self.inner_radius), 3)
        # Bottom Inner
        pygame.draw.line(screen, self.border_color, (self.center_left[0], 300+self.inner_radius), (self.center_right[0], 300+self.inner_radius), 3)

    def _draw_finish_line(self, screen):
        # Draw checkered pattern
        rows = 4
        cols = 2
        tile_w = 10
        tile_h = self.finish_height / rows
        
        x_base = self.finish_x - tile_w
        y_base = self.finish_y - self.finish_height // 2
        
        for c in range(cols):
            for r in range(rows):
                color = (255, 255, 255) if (c + r) % 2 == 0 else (20, 20, 20)
                pygame.draw.rect(screen, color, (x_base + c*tile_w, y_base + r*tile_h, tile_w, tile_h))
