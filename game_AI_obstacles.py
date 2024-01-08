import pygame, random
from spaceship import *
from obstacle import Obstacle
from obstacle import grid
from alien import *
from laser import Laser

pygame.init()

class SpaceInvadersGameAI:
    def __init__(self,screen_width,screen_height, offset, TICK):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.tick = TICK
        self.spaceship_group = pygame.sprite.GroupSingle()
        self.spaceship_group.add(Spaceship(self.screen_width,self.screen_height, self.offset,self.tick))
        self.obstacles = self.create_obstacles()
        self.alien_group = pygame.sprite.Group()
        self.create_aliens()
        self.aliens_direction = 1
        self.alien_lasers_group = pygame.sprite.Group()
        self.mystery_ship_group = pygame.sprite.GroupSingle()
        self.lives = 3
        self.level = 1
        self.reward = 0
        self.run = True
        self.score = 0
        self.highscore = 0
        self.border = 100
        self.sideborder = 40
        self.load_highscore()
        self.explosion_sound = pygame.mixer.Sound("sounds/explosion.ogg")
        self.scale = 1
        self.shoot_alien_reward = 5 * self.scale
        self.crash_into_alien_reward = -20 * self.scale
        self.shoot_target_reward = 5 * self.scale
        self.shoot_mystery_reward = 10 * self.scale
        self.shoot_obstacle_reward = -3 * self.scale
        self.passive_laser_miss_reward = 0 * self.scale
        self.obstacle_ahead_reward = -10
        self.get_hit_reward = -2 * self.scale
        self.x_reward_multiplier = 1.5 * self.scale
        self.y_reward_multiplier = 333 * self.scale
        self.laser_collision_reward_multiplier = 1 * self.scale
        self.avoid_laser_reward_multiple = 3
        self.avoid_laser_reward_multiple_top = 100
        self.reset_frames = 0
        self.time = 0
        self.exists = False
        self.time_reward = 1
        self.old_x = 0
        self.old_y = 0
        
        
        # pygame.mixer.music.load("sounds/music.ogg")
        # pygame.mixer.music.play(-1)
        
    def create_obstacles(self):
        num_obstacles = 4
        obstacle_width = len(grid[0]) * 3
        gap = (self.screen_width + self.offset - (num_obstacles * obstacle_width)) / 5    
        obstacles = []
        for i in range(num_obstacles):
            offset_x = (i + 1) * gap + i * obstacle_width
            obstacle = Obstacle(offset_x,self.screen_height - 100)
            obstacles.append(obstacle)
        return obstacles
    
    def create_aliens(self):
        multiple = 55
        num_rows = 5
        num_cols = 11
        
        for row in range(num_rows):
            for column in range(num_cols):
                x = 75+ column * multiple
                y = 110 + row * multiple
                
                if row == 0:
                    alien_type = 3
                elif row in (1,2):
                    alien_type = 2
                else:
                    alien_type = 1    
                    
                alien = Alien(alien_type, x + self.offset/2, y)
                self.alien_group.add(alien)
                
    def move_aliens(self):
        self.alien_group.update(self.aliens_direction)
        
        alien_sprites = self.alien_group.sprites()
        for alien in alien_sprites:
            if alien.rect.right >= self.screen_width + self.offset/2:
                self.aliens_direction = -1
                self.alien_move_down(2)
            elif alien.rect.left <= self.offset/2:
                self.aliens_direction = 1
                self.alien_move_down(2)
                
    def alien_move_down(self, distance):
        if self.alien_group:
            for alien in self.alien_group.sprites():
                alien.rect.y += distance
    
    def alien_shoot_laser(self):
        if self.alien_group.sprites():
            random_alien = random.choice(self.alien_group.sprites())
            laser_sprite = Laser(random_alien.rect.center, -6, self.screen_height)
            self.alien_lasers_group.add(laser_sprite)
            
    def create_mystery_ship(self):
        self.mystery_ship_group.add(MysteryShip(self.screen_width,self.offset)) 
        
    def check_for_collisions(self):
        laser_hit = False
        self.time +=1
        targetx = self.target_depth_first()[0]
        #Check for worst case: alien collision with ship
        if self.alien_group:
            for alien in self.alien_group:
                for obstacle in self.obstacles:
                    pygame.sprite.spritecollide(alien,obstacle.blocks_group,True)            
                if pygame.sprite.spritecollide(alien,self.spaceship_group,False):
                    self.reward = self.crash_into_alien_reward                           #Play around with self.reward values
                    self.game_over()
                      
        #Spaceship
        if self.spaceship_group.sprite.laser_group:
            for laser_sprite in self.spaceship_group.sprite.laser_group:
                
                aliens_hit = pygame.sprite.spritecollide(laser_sprite, self.alien_group, True)
                
                if aliens_hit:
                    for alien in aliens_hit:
                        alienx = alien.rect.centerx
                        self.reward += self.shoot_alien_reward                       #Play around with self.reward values
                        self.score += alien.type * 100
                        self.check_for_highscore()
                        # self.explosion_sound.play()
                        if alienx == targetx:
                            self.reward += self.shoot_target_reward
                        laser_sprite.kill()
                        laser_hit = True
                        self.time = 0
                        
                if pygame.sprite.spritecollide(laser_sprite, self.mystery_ship_group, True):
                    self.reward += self.shoot_mystery_reward                            #Play around with reward values
                    self.score += 500
                    self.check_for_highscore()
                    # self.explosion_sound.play()
                    laser_sprite.kill()
                    laser_hit = True
                    
                for obstacle in self.obstacles:
                    if pygame.sprite.spritecollide(laser_sprite,obstacle.blocks_group,True):
                        laser_sprite.kill()
                        self.reward = self.shoot_obstacle_reward
                        
        if laser_hit == False:
            self.reward -= self.passive_laser_miss_reward
        #Alien lasers
        if self.alien_lasers_group:
            for laser_sprite in self.alien_lasers_group:
                if pygame.sprite.spritecollide(laser_sprite, self.spaceship_group, False):
                    self.reward += self.get_hit_reward                           #Play around with reward values
                    laser_sprite.kill()
                    self.lives -= 1
                    if self.lives == 0:
                        self.game_over()

                    
                for obstacle in self.obstacles:
                    if pygame.sprite.spritecollide(laser_sprite,obstacle.blocks_group,True):
                        laser_sprite.kill()          
                    
    def game_over(self):
        self.run = False
    
    def reset(self):
        self.run = True
        self.lives = 3
        self.time = 0
        self.spaceship_group.sprite.reset()
        self.alien_group.empty()
        self.alien_lasers_group.empty()
        self.mystery_ship_group.empty()
        self.score = 0
        self.reset_frames = 0
        self.create_aliens()
        self.obstacles = self.create_obstacles()

    def check_for_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            
            with open("highscore.txt", "w") as file:
                file.write(str(self.highscore))
                
    def load_highscore(self):
        try:
            with open("highscore.txt", "r") as file:
                self.highscore = int(file.read())
        except FileNotFoundError:
            self.highscore = 0
        
    def left_danger(self, border):
        if self.alien_lasers_group:
            for laser_sprite in self.alien_lasers_group:
                if laser_sprite.rect.right > self.spaceship_group.sprite.rect.left - border \
                    and laser_sprite.rect.right < self.spaceship_group.sprite.rect.centerx \
                    and laser_sprite.rect.bottom > self.spaceship_group.sprite.rect.top - border \
                    and laser_sprite.rect.top < self.spaceship_group.sprite.rect.bottom:
                    distance = abs(laser_sprite.rect.right - (self.spaceship_group.sprite.rect.left - (border / 2)))
                    self.reward += (-distance + (border/2)) / self.avoid_laser_reward_multiple
                    return distance
        return 0
                    
    def right_danger(self, border):
        if self.alien_lasers_group:
            for laser_sprite in self.alien_lasers_group:
                if laser_sprite.rect.left > self.spaceship_group.sprite.rect.centerx \
                    and laser_sprite.rect.left < self.spaceship_group.sprite.rect.right + border \
                    and laser_sprite.rect.bottom > self.spaceship_group.sprite.rect.top - border \
                    and laser_sprite.rect.top < self.spaceship_group.sprite.rect.bottom:
                    distance = abs(laser_sprite.rect.left - (self.spaceship_group.sprite.rect.right + (border / 2)))
                    self.reward += (-distance + (border/2)) / self.avoid_laser_reward_multiple                    
                    return distance
        return 0    
    
    def top_danger(self,border):
        if self.alien_lasers_group:
            for laser_sprite in self.alien_lasers_group:
                if laser_sprite.rect.left > self.spaceship_group.sprite.rect.left \
                    and laser_sprite.rect.right < self.spaceship_group.sprite.rect.right \
                    and laser_sprite.rect.bottom > self.spaceship_group.sprite.rect.top - border \
                    and laser_sprite.rect.top < self.spaceship_group.sprite.rect.bottom:
                    distance = abs(laser_sprite.rect.bottom - self.spaceship_group.sprite.rect.top)
                    self.reward += self.avoid_laser_reward_multiple_top /(-distance - border)  
                    return distance
        return 0
                
    def alien_direction(self):
        if self.aliens_direction == 1:
            return 1
        if self.aliens_direction == -1:
            return 0
        else:
            return 0.5 
        
    def target_lowest(self):
        target_x = 0
        target_y = 0
        closest_distance = self.screen_width * 2
        closest_y = 0

        if self.alien_group:
            for alien in self.alien_group:
                x_distance = abs(self.spaceship_group.sprite.rect.centerx - alien.rect.centerx)
                if alien.rect.centery > closest_y or (alien.rect.centery == closest_y and x_distance < closest_distance):
                    closest_y = alien.rect.centery
                    closest_distance = x_distance
                    target_x = alien.rect.centerx
                    target_y = alien.rect.centery
                    
        return target_x, target_y
    
    def target_depth_first(self):
        target_x = 0
        target_y = 0

        closest_distance = self.screen_width * 2
        farthest_y = self.screen_height
        closest_y = 0

        if self.alien_group:
            for alien in self.alien_group:
                x_distance = abs(self.spaceship_group.sprite.rect.centerx - alien.rect.centerx)
                if alien.rect.centery < farthest_y or (alien.rect.centery == farthest_y and x_distance < closest_distance):
                    farthest_y = alien.rect.centery
                    closest_distance = x_distance
                    target_x = alien.rect.centerx
                    target_y = alien.rect.centery
                if alien.rect.centery > closest_y:
                    closest_y = alien.rect.centery
                    
        return target_x, target_y, closest_y    
    
    def target_same_column(self):
        if self.exists == False:
            if self.alien_group:
                for alien in self.alien_group:
                    x_distance = abs(self.spaceship_group.sprite.rect.centerx - alien.rect.centerx)
                    if alien.rect.centery < farthest_y or (alien.rect.centery == farthest_y and x_distance < closest_distance):
                        farthest_y = alien.rect.centery
                        closest_distance = x_distance
                        target_x = alien.rect.centerx
                        target_y = alien.rect.centery
                    if alien.rect.centery > closest_y:
                        closest_y = alien.rect.centery
        self.exists = True
                        
        
                        
        
    def line_of_fire(self,border):
        if self.alien_group:    
            for alien in self.alien_group:
                if self.spaceship_group.sprite.rect.centerx < alien.rect.right + border \
                and self.spaceship_group.sprite.rect.centerx > alien.rect.left - border:        
                    self.reward += 1
                    return 1            #return 1 for true, 0 for false
        self.reward -= 1
        return 0
    
    def obstacle_ahead(self):
        if self.obstacles:
            for obstacle in self.obstacles:
                if obstacle.rect.left < self.spaceship_group.sprite.rect.centerx   \
                    and obstacle.rect.right > self.spaceship_group.sprite.rect.centerx \
                    and  obstacle.rect.top < self.spaceship_group.sprite.rect.bottom:
                    self.reward += self.obstacle_ahead_reward
                    return 1 

        return 0        
          
    def mystery_exists(self):
        if self.mystery_ship_group:     #return 1 for true, 0 for false
            return 1, self.mystery_ship_group.sprite.rect.centerx, self.mystery_ship_group.sprite.rect.centery
        return 0, 0, 0
                 
    def retrieve_state(self):
        target = self.target_depth_first()
        left_danger = self.left_danger(self.sideborder)
        right_danger = self.right_danger(self.sideborder)
        top_danger = self.top_danger(self.border)
        alien_direction = self.alien_direction()
        lof = self.line_of_fire(self.border)
        recharge = self.spaceship_group.sprite.laser_ready
        mysteryship_exists, mystery_position_x, mystery_position_y = self.mystery_exists() 
        obs_ahead = self.obstacle_ahead()
        obs_ahead = 1
        return left_danger, right_danger, top_danger, alien_direction, lof, recharge, target, obs_ahead, self.time, mysteryship_exists, mystery_position_x, mystery_position_y, self.spaceship_group.sprite.rect.center

    def level_up(self):
        if self.alien_group:
            return 0    
        self.level +=1
        self.create_aliens()
        # if self.run == False:
        #     self.reset()
        # else:
        #     self.run = False
        
    def train_movement(self):
        target_x, target_y, closest_y = self.target_depth_first()
        ship_x, ship_y = self.spaceship_group.sprite.rect.center
        
        relative_x = abs(ship_x - target_x)
        relative_y = abs(ship_y - closest_y)
        
        window = 200
        
        self.reward += ((-relative_x + 15) / 10) * self.x_reward_multiplier
        if relative_y < window:
            self.reward += self.y_reward_multiplier/(-relative_y) 
                   
    def timer(self):
        if self.time > 100:
            self.reward -= self.time*self.time/10000
    
    def check_reset(self):
        self.reset_frames += 1
        if self.alien_group:
            for alien in self.alien_group:
                if self.spaceship_group.sprite.rect.centerx == alien.rect.centerx:
                    self.reset_frames = 0
                    
        if self.reset_frames == 1000:
            self.reset()
            self.reward = -500
            self.run = False
            
    def move_incentive(self):
        if self.old_x != self.spaceship_group.sprite.rect.centerx:
            self.reward+= 1
        if self.old_y != self.spaceship_group.sprite.rect.centery:
            self.reward+= 0.1
            
        self.old_x = self.spaceship_group.sprite.rect.centerx
        self.old_y = self.spaceship_group.sprite.rect.centery
            
    def play_step_AI(self, final_move):
        if self.spaceship_group.sprite.laser_ready == False:
            self.reward += 10
        self.spaceship_group.sprite.update_AI(final_move)
        self.move_aliens()
        self.left_danger(self.sideborder) 
        self.right_danger(self.sideborder)
        self.top_danger(self.border)         
        self.train_movement()
        self.check_for_collisions()
        self.timer()
        self.alien_lasers_group.update()
        self.mystery_ship_group.update()
        self.level_up()
        self.check_reset()        
        
    def play_step(self):
        if self.spaceship_group.sprite.laser_ready == False:
            self.reward += 1
        self.spaceship_group.sprite.update()
        self.move_aliens()
        self.left_danger(self.sideborder) 
        self.right_danger(self.sideborder)
        self.top_danger(self.border)         
        self.train_movement()
        self.check_for_collisions()
        self.timer()
        self.alien_lasers_group.update()
        self.mystery_ship_group.update()
        self.level_up()
        self.check_reset()
        
        
        
        