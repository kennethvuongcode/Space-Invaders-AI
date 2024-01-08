import pygame

class Block(pygame.sprite.Sprite):                          #creating a block to build obstacles
    def __init__(self,x,y):
        super().__init__()
        self.image = pygame.Surface((3,3))
        self.image.fill((243,216,63))
        self.rect = self.image.get_rect(topleft = (x,y))
        
grid = [
[0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
[0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
[0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
[0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1],
[1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1]]

class Obstacle():
    def __init__(self,x,y):
        self.blocks_group = pygame.sprite.Group()
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = 0, 0
        for row in range(len(grid)):
            for column in range(len(grid[0])):
                if grid[row][column] == 1:
                    pos_x = column * 3 + x
                    pos_y = row * 3 + y
                    block = Block(pos_x,pos_y)
                    self.blocks_group.add(block)
                    min_x = min(min_x, pos_x)
                    min_y = min(min_y, pos_y)
                    max_x = max(max_x, pos_x)
                    max_y = max(max_y, pos_y)

        # Create a rect that encompasses all blocks
        self.rect = pygame.Rect(min_x, min_y, max_x - min_x + 3, max_y - min_y + 3)
