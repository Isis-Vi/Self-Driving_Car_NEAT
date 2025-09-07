import pygame
import os
import math
import sys
import neat

pygame.init()

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
STAT_FONT = pygame.font.SysFont("timesnewroman", 50)
FIT_FONT = pygame.font.SysFont("timesnewroman", 20)

gen = 0

# Set sprites
## Collision map sprite
collision_map = pygame.image.load(os.path.join("Driving_Ai_Car_NEAT", "imgs", "street_race1.png"))
collision_map = pygame.transform.scale(collision_map, (WIN_WIDTH, WIN_HEIGHT))

## Visual map sprite
visual_map = pygame.image.load(os.path.join("Driving_Ai_Car_NEAT", "imgs", "pretty_track1.png"))
visual_map = pygame.transform.scale(visual_map, (WIN_WIDTH, WIN_HEIGHT))

## Car sprite
car_img = pygame.image.load(os.path.join("Driving_Ai_Car_NEAT", "imgs", "car.png"))

# Collision mask for the bicolored track
collision_mask = pygame.mask.from_threshold(collision_map, (0, 0, 0), (1, 1, 1))  # black_out

# Class for all car objects.
class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = car_img
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(300, 610))
        self.vel = pygame.math.Vector2(0.5, 0)
        self.angle = 0
        self.rotation_vel = 2
        self.direction = 0
        self.radars = []
        self.alive = True

    def drive(self):
        self.rect.center += self.vel * 6

    def rotate(self):
        if self.direction == 1:
            self.angle -= self.rotation_vel
            self.vel.rotate_ip(self.rotation_vel)
        if self.direction == -1:
            self.angle += self.rotation_vel
            self.vel.rotate_ip(-self.rotation_vel)

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1) #To rotate the sprite
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        self.radars.clear()
        self.drive()
        self.rotate()
        for radar_angle in (-60, -30, 0, 30, 60):
            self.radar(radar_angle)
        self.collision()
        self.data() # Call the NEAT data function
    
    def radar(self, radar_angle):
        """
        ----------
        Parametros
        ----------
            - radar_angle: float
        """
        length = 0
        x = int(self.rect.centerx)
        y = int(self.rect.centery)

        while True:
            x = int(self.rect.centerx + math.cos(math.radians(self.angle + radar_angle)) * length)
            y = int(self.rect.centery - math.sin(math.radians(self.angle + radar_angle)) * length)

            # Manage going out of the map
            if x < 0 or y < 0 or x >= collision_map.get_width() or y >= collision_map.get_height():
                break

            # Check track borders
            if collision_map.get_at((x, y))[:3] == (0, 0, 0):  # Touched a border
                break

            length += 1
            if length > 200:  #Max lenght of the radar
                break

        # Draw Radar
        pygame.draw.line(WIN, (GREEN), self.rect.center, (x, y), 1)
        pygame.draw.circle(WIN, (GREEN), (x, y), 3)

        dist = int(math.sqrt(math.pow(self.rect.center[0] - x, 2)
                            + math.pow(self.rect.center[1] - y, 2)))
        
        self.radars.append([radar_angle, dist])

        

    
    def collision(self):
        # Car mask for collisions
        car_mask = pygame.mask.from_surface(self.image)
        offset = (self.rect.left, self.rect.top)

        hit = collision_mask.overlap(car_mask, offset)  # Check if crash (none if not)

        if hit:
            self.alive = False

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

    def data(self):
        input = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            input[i] = int(radar[1])
        return input
    
# To delete dead cars
def remove(index):
    cars.pop(index)
    ge.pop(index)
    nets.pop(index)

# Main Function to evaluate genomes(cars)
def eval_genomes(genomes, config):
    global cars, ge, nets, gen

    # Set the empty list to manage NEAT
    gen += 1
    cars = []
    ge = []
    nets = []

    # To access each new genome(car)
    for genome_id, genome in genomes:
        cars.append(pygame.sprite.GroupSingle(Car())) # Add a new car sprite
        ge.append(genome) # Assign a genome to the car sprite
        net = neat.nn.FeedForwardNetwork.create(genome, config) # Creating the neural network to feed
        nets.append(net) # Add new net to each genome
        genome.fitness = 0 # Set the initial fitness func to 0

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Show track
        WIN.blit(visual_map, (0,0))

        # Show scores
        if gen == 0:
            gen = 1

        ## generations
        gens_label = STAT_FONT.render("Gens: " + str(gen),1,(WHITE))
        WIN.blit(gens_label, (10, 10))

        ## alive
        alive_label = STAT_FONT.render("Alive: " + str(len(cars)),1,(WHITE))
        WIN.blit(alive_label, (10, 50))

        # If there is no remaining genomes(car), end sim
        if len(cars) == 0:
            break

        # Increase the fitness func the more time each genome is alive
        for i, car in enumerate(cars):
            ge[i].fitness += 1
            if not car.sprite.alive:
                print(ge[i].fitness)
                remove(i)

        # Movement input
        for i, car in enumerate(cars):
            output = nets[i].activate(car.sprite.data())
            if output[0] > 0.7:
                car.sprite.direction = 1
            if output[1] > 0.7:
                car.sprite.direction = -1
            if output[0] <= 0.7 and output[1] <= 0.7:
                car.sprite.direction = 0

        # Update
        for car in cars:
            car.update()
            car.draw(WIN)
        pygame.display.update()

# Setup NEAT Neural Network
def run(config_path):
    global pop
    config = neat.config.Config( # Get each section of the config file
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    # Assign population num from the config file
    pop = neat.Population(config)

    # Show stats in the terminal
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    # Initialize the sim
    pop.run(eval_genomes, 50)


    # show final stats
    print('\nBest genome:\n{!s}'.format(pop))

# Get the config file path
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)


