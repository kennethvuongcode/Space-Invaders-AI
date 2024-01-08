import torch
import random
import numpy as np
import pygame, sys, random
from game_AI_obstacles import SpaceInvadersGameAI
from collections import deque
from model import Linear_QNet, QTrainer
from helper import plot
import time
import os

################################################   AGENT PARAMETERS   #################################################

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 #randomness
        self.gamma = 0   #discount rate
        self.memory = deque(maxlen=MAX_MEMORY) 
        self.model = Linear_QNet(11,256,256,256,5) #TODO: implement neural net
        self.trainer = QTrainer(self.model,lr=LR,gamma=self.gamma) #TODO: implement trainer
        pass
    
    def scale_predictions(self,predictions, new_min=0, new_max=1):
        """ Scale the predictions to a new range [new_min, new_max]. """
        min_pred = torch.min(predictions)
        max_pred = torch.max(predictions)
        scaled_pred = (new_max - new_min) * (predictions - min_pred) / (max_pred - min_pred) + new_min
        return scaled_pred

    def apply_threshold(self,scaled_predictions, threshold=0.5):
        """ Apply a threshold to the scaled predictions to decide on actions. """
        actions = (scaled_predictions >= threshold).int()
        return actions

    def get_state(self,game):
        ld, rd, td, ad, lof, recharge, target, obs_ahead,time,mys_exists,mys_x,mys_y,ship = game.retrieve_state() 

        
        target_x, closest_y = target[0], target[2] 
        ship_x, ship_y = ship[0], ship[1]
        
        relative_x = ship_x - target_x
        relative_y = ship_y - closest_y
        
        state = [
            ld,
            rd,
            td,
            ad,
            # lof,
            recharge,
            relative_x,
            relative_y,
            obs_ahead,
            time, 
            # mys_exists,
            # mys_x,
            # mys_y,
            ship_x,
            ship_y,                     
        ]
        
        # print(state)
        
        return np.array(state,dtype=int)
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        # Convert actions to the correct format here
        actions = [action[0] for action in actions]  # Assuming action is a single integer per sample
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    
    def train_short_memory(self,state,action,reward,next_state,done):
        self.trainer.train_step(state,action,reward,next_state,done)
    
    def get_action(self,state):
        #random moves to explore and balance with exploiting spammable moves
        self.epsilon = 60 - (self.n_games / 1) #hardcoded value
        final_move = [0,0,0,0,0] #Choose moves to use
        if random.randint(0,60) < self.epsilon:
            for i in range(len(final_move)):
                final_move[i] = random.randint(0,1)
        else:
            state0 = torch.tensor(state,dtype=torch.float)
            prediction = self.model(state0)
            scaled_pred = self.scale_predictions(prediction)
            final_move = self.apply_threshold(scaled_pred, threshold=0.5)
            if final_move == [0,0,0,0,0]:
                move = torch.argmax(prediction).item()
                final_move[move] = 1                        
            
        return final_move
    
    def save_model(self, file_name='model.pth'):
        """Saves the state dict of the model to a file."""
        torch.save(self.model.state_dict(), file_name)

    def load_model(self, file_name='model.pth'):
        """Loads the state dict into the model from a file."""
        self.model.load_state_dict(torch.load(file_name))
        self.model.eval()  # Set the model to evaluation mode
        
##############################################   DRAW PARAMETERS   #####################################################
SCREEN_WIDTH = 750
SCREEN_HEIGHT = 700
OFFSET = 50

GREY = (29,29,27)
GREEN = (100,253,134)

TICK =  10000 #120 standard

def draw(screen, game, clock, target):
 #Drawing         


    font = pygame.font.Font("Fonts/monogram.ttf", 40)
    level = "LEVEL " + str(game.level).zfill(3)
    level_surface = font.render(level, False, GREEN)
    game_over_surface = font.render("GAME OVER", False, GREEN)
    score_text_surface = font.render("SCORE", False, GREEN)
    highscore_text_surface = font.render("HIGHSCORE", False, GREEN)    
    
    screen.fill(GREY)                       #background
    pygame.draw.rect(screen, GREEN, (10,10, 780,780), 2, 0, 60, 60, 60, 60) 
    pygame.draw.line(screen, GREEN, (25,730), (775,730), 3)
    
    if game.run:
        screen.blit(level_surface, (570, 740, 50, 50))
    else:
        screen.blit(game_over_surface, (570, 740, 50, 50))

        
    x = 50
    for life in range(game.lives):
        screen.blit(game.spaceship_group.sprite.image,(x,740))
        x += 50
        
    screen.blit(score_text_surface,(50,15,50,50))
    formatted_score = str(game.score).zfill(8)
    score_surface = font.render(formatted_score,False,GREEN)
    screen.blit(score_surface,(50,40,50,50))
    screen.blit(highscore_text_surface, (550, 15, 50, 50))
    formatted_highscore = str(game.highscore).zfill(8)
    highscore_surface = font.render(formatted_highscore, False, GREEN)
    screen.blit(highscore_surface,(550,40,50,50))

    pygame.draw.rect(screen, (255,0,0), (target[0]-25,target[1]-25, 50,50))         
    
    game.spaceship_group.draw(screen)
    game.spaceship_group.sprite.laser_group.draw(screen)
    for obstacle in game.obstacles:
        obstacle.blocks_group.draw(screen)
    game.alien_group.draw(screen)
    game.alien_lasers_group.draw(screen)
    game.mystery_ship_group.draw(screen)
    
    pygame.display.update()
    clock.tick(TICK)                          #While loop will run 60 times a second, tick is a wait of 1/60th of a second

def save(self, file_name='model.pth'):
    model_folder_path = './model'
    if not os.path.exists(model_folder_path):
        os.makedirs(model_folder_path)
    
    file_name = os.path.join(model_folder_path, file_name)
    torch.save(self.state_dict(), file_name)
    
##############################################   TRAIN   ################################################

def train(draws):
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = SpaceInvadersGameAI(SCREEN_WIDTH,SCREEN_HEIGHT, OFFSET, TICK)

    if draws == True:
        screen = pygame.display.set_mode((SCREEN_WIDTH + OFFSET, SCREEN_HEIGHT + 2*OFFSET))
        pygame.display.set_caption("Space Invaders AI")
        clock = pygame.time.Clock()
    
    alien_counter = 0
    alien_timer = 20
    mystery_counter = 0
    mystery_timer = 1000

    # previous_time = time.time()  # Initialize the time before the loop starts

    while True:
        # current_time = time.time()
        # time_elapsed = current_time - previous_time
        # print(f"Time elapsed since last iteration: {time_elapsed} seconds")         
        
        #Updating
        alien_counter += 1
        mystery_counter += 1

        if alien_counter >= alien_timer and game.run:  
                game.alien_shoot_laser()
                alien_counter = 0
        if mystery_counter >= mystery_timer and game.run:
            game.create_mystery_ship()
            mystery_counter = random.randint(0,mystery_timer/4) #change to set mystery spawn rate
        

        # get old state
        state_old = agent.get_state(game)
        
        # get move 
        final_move = agent.get_action(state_old)         
            
        done = False
        if game.run:
            game.play_step_AI(final_move)
            target =  game.target_depth_first() 
            reward = game.reward
            game.reward = 0
            print(reward)
            state_new = agent.get_state(game)

        if game.run == False:
            done = True
            
        if draws == True:
            draw(screen,game,clock, target)
        
        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)
        
        if done:
            alien_counter = 0
            mystery_counter = 0
            
            agent.n_games += 1            
            

            plot_scores.append(game.score)
            total_score += game.score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)
            
            if game.score > record:
                record = game.score
                agent.model.save()            
            
            game.reset()
            agent.train_long_memory()
        
        for event in pygame.event.get():        #While loop checks for events thrown by pygame, if exit button pressed then quit the game
            if event.type == pygame.QUIT:
                # Save the model before exiting
                agent.save_model('path_to_save_model.pth')
                pygame.quit()
                sys.exit()
                
        # previous_time = current_time  # Update the previous_time for the next iteration
                
        


if __name__ == '__main__':
    train(False)
    