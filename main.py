import pygame
import os
import math
import sys
import neat

# Set colores for upcoming use
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 128, 0) 
BLUE = (0, 0, 255)

# Window settings
WIN_WIDTH = 800
WIN_HEIGHT = 700
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

# Set sprites
collision_map = pygame.image.load(os.path.join("Driving_Ai_Car_NEAT", "imgs", "street_race.png"))
collision_map = pygame.transform.scale(collision_map, (WIN_WIDTH, WIN_HEIGHT))
car_img = pygame.image.load(os.path.join("Driving_Ai_Car_NEAT", "imgs", "car.png"))

# Collision mask for the bicolored track
collision_mask = pygame.mask.from_threshold(collision_map, (0, 0, 0), (1, 1, 1))  # negro = fuera

#Class for all car objects.
class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = car_img
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(300, 565))
        self.drive_state = 0
        self.vel = pygame.math.Vector2(0.5, 0)
        self.angle = 0
        self.rotation_vel = 2
        self.direction = 0
        self.radars = []
        self.alive = True

    def drive(self):
        if self.drive_state != 0:
            self.rect.center += self.vel * (6 * self.drive_state)

    def rotate(self):
        if self.direction == 1:
            self.angle -= self.rotation_vel
            self.vel.rotate_ip(self.rotation_vel)
        if self.direction == -1:
            self.angle += self.rotation_vel
            self.vel.rotate_ip(-self.rotation_vel)

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        self.drive()
        self.rotate()
        for radar_angle in (-180,-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150, 180):
            self.radar(radar_angle)
        self.collision()
    
    def radar(self, radar_angle):
        length = 0
        x = int(self.rect.centerx)
        y = int(self.rect.centery)

        while True:
            x = int(self.rect.centerx + math.cos(math.radians(self.angle + radar_angle)) * length)
            y = int(self.rect.centery - math.sin(math.radians(self.angle + radar_angle)) * length)

            # Manage goign out of the map
            if x < 0 or y < 0 or x >= collision_map.get_width() or y >= collision_map.get_height():
                break

            # Check track borders
            if collision_map.get_at((x, y))[:3] == (0, 0, 0):  # llegó al borde
                break

            length += 1
            if length > 200:  #Max lenght of the radar
                break

        # Draw radars
        pygame.draw.line(WIN, (255, 255, 255), self.rect.center, (x, y), 1)
        pygame.draw.circle(WIN, (0, 255, 0), (x, y), 3)

        # Draw Radar
        pygame.draw.line(WIN, (GREEN), self.rect.center, (x, y), 1)
        pygame.draw.circle(WIN, (GREEN), (x, y), 3)
    
    def collision(self):
        # Car mask for collisions
        car_mask = pygame.mask.from_surface(self.image)
        offset = (self.rect.left, self.rect.top)

        hit = collision_mask.overlap(car_mask, offset)  # Check if crash (none if not)

        if hit:
            self.alive = False
            print("car is dead")

        # Visual debug
        length = 40
        collision_point_right = [
            int(self.rect.center[0] + math.cos(math.radians(self.angle + 18)) * length),
            int(self.rect.center[1] - math.sin(math.radians(self.angle + 18)) * length)
        ]
        collision_point_left = [
            int(self.rect.center[0] + math.cos(math.radians(self.angle - 18)) * length),
            int(self.rect.center[1] - math.sin(math.radians(self.angle - 18)) * length)
        ]

        # Visual debug coloring and rendering
        point_color = (RED) if hit else (BLUE)

        pygame.draw.circle(WIN, point_color, collision_point_right, 4)
        pygame.draw.circle(WIN, point_color, collision_point_left, 4)

car = pygame.sprite.GroupSingle(Car())

def eval_genomes():
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        WIN.blit(collision_map, (0,0))

        # User input
        user_input = pygame.key.get_pressed()

        # If there is no input, stay put
        if sum(user_input) == 0:
            car.sprite.drive_state = 0
            car.sprite.direction = 0

        # Drive: Exclusive movement (W priority)
        if user_input[pygame.K_w]:
            car.sprite.drive_state = 1   # forward
        elif user_input[pygame.K_s]:
            car.sprite.drive_state = -1  # backwards
        else:
            car.sprite.drive_state = 0   # still

        # Steer (independant from driving)
        if user_input[pygame.K_d]:
            car.sprite.direction = 1
        elif user_input[pygame.K_a]:
            car.sprite.direction = -1
        else:
            car.sprite.direction = 0

        # Update
        car.update()
        car.draw(WIN)
        pygame.display.update()

eval_genomes()

