import pygame
from laser import Laser

class Spaceship(pygame.sprite.Sprite):
    def __init__(self,screen_width,screen_height, offset, ticks):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.image = pygame.image.load("graphics/spaceship.png")
        self.rect = self.image.get_rect(midbottom = ((self.screen_width + self.offset)/2,self.screen_height))
        self.speed = 6 #change to achieve diff move distances
        self.laser_group = pygame.sprite.Group()
        self.laser_ready = True
        self.laser_time = 0
        self.laser_counter =  0          #change to set firing rate
        self.laser_sound = pygame.mixer.Sound("sounds/laser.ogg")
        
    def get_user_input(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        if keys[pygame.K_SPACE] and self.laser_ready:
            self.laser_ready = False
            laser = Laser(self.rect.midtop,10,self.screen_height)
            self.laser_group.add(laser)
            self.laser_time = pygame.time.get_ticks()
            # self.laser_sound.play()
            
    def get_ai_user_input(self, action):
        if action[0] == 1:               #RIGHT
            self.rect.x += self.speed    
        if action[1] == 1:               #LEFT
            self.rect.x -= self.speed    
        if action[2] == 1:               #UP
            self.rect.y -= self.speed    
        if action[3] == 1:               #DOWN
            self.rect.y += self.speed    
        if action[4] == 1 and self.laser_ready:               #SHOOT
            self.laser_ready = False
            self.laser_counter = 0
            laser = Laser(self.rect.midtop,10,self.screen_height)
            self.laser_group.add(laser)
            self.laser_time = pygame.time.get_ticks()
            # self.laser_sound.play() 
            
            
    
    def constrain_movement(self):
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
        if self.rect.left < self.offset:
            self.rect.left = self.offset
        if self.rect.bottom > self.screen_height:
            self.rect.bottom = self.screen_height
        if self.rect.top < 3*self.screen_height/4:
            self.rect.top = 3*self.screen_height/4            
        
    def recharge_laser(self):
        threshold = 30
        
        if self.laser_ready is False:   #charge if we need to recharge
            self.laser_counter += 1
            if self.laser_counter >= threshold:
                self.laser_ready = True
                self.laser_counter = 0
                
    def update(self):
        self.get_user_input()
        self.constrain_movement()
        self.laser_group.update()
        self.recharge_laser()
    
    def update_AI(self, move):
        self.get_ai_user_input(move)
        self.constrain_movement()
        self.laser_group.update()
        self.recharge_laser()
                
    def reset(self):
        self.rect = self.image.get_rect(midbottom = ((self.screen_width + self.offset)/2, self.screen_height))
        self.laser_group.empty()