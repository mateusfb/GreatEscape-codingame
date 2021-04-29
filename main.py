import sys
import math
from queue import PriorityQueue
from copy import deepcopy

class GridCell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.neighbours = {}
        self.has_wall = False
    def __repr__(self):
        return '(' + str(self.x) + ',' + str(self.y) + ')' 

class Wall:
    def __init__(self, x, y, orientation):
        self.x = x
        self.y = y
        self.orientation = orientation

class Dragon:
    def __init__(self, player_id, x, y, walls_left, goal):
        self.player_id = player_id
        self.x = x
        self.y = y
        self.walls_left = walls_left
        self.goal = goal

#Verifica se uma nova parede cruza uma parede existente
def wall_cross(x, y, orientation, wall):
    if(wall.x == x and wall.y == y and wall.orientation == orientation):
        return True
    if(orientation == "H"):
        if((wall.x == x+1 and wall.y == y-1) or (wall.orientation == "H" and  wall.y == y and (wall.x == x-1 or wall.x == x+1))):
            return True
    else:
        if((wall.x == x-1 and wall.y == y+1) or (wall.orientation == "V" and  wall.x == x and (wall.y == y-1 or wall.y == y+1))):
            return True
    return False

#Verifica se uma nova parede pode ser posicionada
def validate_wall(x, y, orientation, walls):
    if((orientation == "H" and x >= 8 or x < 0) or (orientation == "V" and y >= 8 or y < 0)):
        return False
    for wall in walls:
        if(wall_cross(x, y, orientation, wall)):
            return False
    return True

#Checa qual o objetivo do jogador de acordo com o id
def what_is_my_goal(id):
    my_goal = None
    if(id == 0):
        my_goal = "RIGHT"
    elif(id == 1):
        my_goal = "LEFT"
    else:
        my_goal = "DOWN"
    return my_goal

#Retorna os vizinhos de uma determinada celula no grid
def get_neighbours(x, y, grid):
    neighbours = {}
    if x > 0:
        neighbours["LEFT"] = grid[x-1][y]
    if x < 8:
        neighbours["RIGHT"] = grid[x+1][y]
    if y > 0:
        neighbours["TOP"] = grid[x][y-1]
    if y < 8:
        neighbours["DOWN"] = grid[x][y+1]
    return neighbours

def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

#Pathfinding com A*
def find_shortest_path(start, goal, grid, debug=False):
    frontier = PriorityQueue()
    frontier.put((0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    while(not frontier.empty()):
        curr = frontier.get()[1]
        if(curr == goal):
            break
        for neighbour in grid[curr[0]][curr[1]].neighbours.values():
            neighbour_pos = (neighbour.x, neighbour.y)
            new_cost = cost_so_far[curr] + 1
            if((neighbour_pos not in cost_so_far) or (new_cost < cost_so_far[neighbour_pos])):
                cost_so_far[neighbour_pos] = new_cost
                priority = new_cost + manhattan_distance(neighbour_pos, goal)
                frontier.put((priority, neighbour_pos))
                came_from[neighbour_pos] = curr

    if(goal not in came_from):
        return 10000000, ''

    steps = 1
    first_step = goal
    parent = came_from[goal]
    while(parent != None):
        if(came_from[parent] != None):
            first_step = parent
        parent = came_from[parent]
        steps += 1
    command = ''
    if(first_step[0] > start[0]):
        command = 'RIGHT'
    elif(first_step[0] < start[0]):
        command = 'LEFT'
    elif(first_step[1] > start[1]):
        command = 'DOWN'
    elif(first_step[1] < start[1]):
        command = 'UP'
    return steps, command

#Encontra a celula de objetivo mais proxima do jogador
def find_closest_objective_position_on_grid(dragon, grid, debug=False):
    dragon_pos = (dragon.x, dragon.y)
    closest_objective = None
    closest_objective_distance = 90000000
    next_step = None
    x = 0
    if(dragon.goal == "DOWN"):
        for i in range(9):
            distance, temp = find_shortest_path(dragon_pos, (i, 8), grid, debug=debug)
            if(distance < closest_objective_distance):
                closest_objective_distance = distance
                closest_objective = (i, 8)
                next_step = temp
        return closest_objective, closest_objective_distance, next_step
    if(dragon.goal == "RIGHT"):
        x = 8
    for i in range(9):
        distance, temp = find_shortest_path(dragon_pos, (x, i), grid, debug=debug)
        if(distance < closest_objective_distance):
            closest_objective_distance = distance
            closest_objective = (x, i)
            next_step = temp
    return closest_objective, closest_objective_distance, next_step

#Encontra qual o inimigo mais proximo do objetivo
def find_enemy_closest_to_objective(enemies, grid, debug=False):
    enemy_closest_to_obtective = None
    shortest_distance = 90000000
    for enemy in enemies:
        closest_objective, distance, temp = find_closest_objective_position_on_grid(enemy, grid, debug=debug)
        if(distance < shortest_distance):
            shortest_distance = distance
            enemy_closest_to_obtective = enemy
            next_step = temp
    return enemy_closest_to_obtective, shortest_distance, next_step

#Define a posicao para colocar uma parede capaz de bloquear o inimigo
def block(enemy_pos_x, enemy_pos_y, enemy_next_step, walls):
    wall_placing_pos_x = enemy_pos_x
    wall_placing_pos_y = enemy_pos_y
    
    if(enemy_next_step == "RIGHT"):
        wall_placing_pos_x += 1
        wall_orientation = "V"
    elif(enemy_next_step == "LEFT"):
        wall_orientation = "V"
    elif(enemy_next_step == "UP"):
        wall_orientation = "H"
    else:
        wall_placing_pos_y += 1
        wall_orientation = "H"

    if(validate_wall(wall_placing_pos_x, wall_placing_pos_y, wall_orientation, walls)):
        return (wall_placing_pos_x, wall_placing_pos_y), wall_orientation
    elif(((enemy_next_step == "RIGHT" or enemy_next_step == "LEFT") and enemy_pos_y - 1 < 0) or ((enemy_next_step == "UP" or enemy_next_step == "DOWN") and enemy_pos_x - 1 < 0)):
        return None, None
    else:
        if(enemy_next_step == "RIGHT" or enemy_next_step == "LEFT"):
            return block(enemy_pos_x, enemy_pos_y - 1, enemy_next_step, walls)
        if(enemy_next_step == "UP" or enemy_next_step == "DOWN"):
            return block(enemy_pos_x - 1, enemy_pos_y, enemy_next_step, walls)

#Checa se uma parede bloqueia todas as saidas de um jogador       
def block_all_exits(enemy, block_position, orientation, grid):
    wall_x = block_position[0]
    wall_y = block_position[1]
    grid_copy = deepcopy(grid)
    
    if(orientation == 'V'):
        grid_copy[wall_x][wall_y].neighbours.pop("LEFT")
        if(wall_y+1 <= 8):
            grid_copy[wall_x][wall_y+1].neighbours.pop("LEFT")

        if(wall_x-1 >= 0):
            grid_copy[wall_x-1][wall_y].neighbours.pop("RIGHT")
            if(wall_y+1 <= 8):
                grid_copy[wall_x-1][wall_y+1].neighbours.pop("RIGHT")

    else:
        grid_copy[wall_x][wall_y].neighbours.pop("TOP")
        if(wall_x+1 <= 8):
            grid_copy[wall_x+1][wall_y].neighbours.pop("TOP")

        if(wall_y-1 >= 0):
            grid_copy[wall_x][wall_y-1].neighbours.pop("DOWN")
            if(wall_x+1 <= 8):
                grid_copy[wall_x+1][wall_y-1].neighbours.pop("DOWN")

    closest_objective, closest_objective_distance, next_step = find_closest_objective_position_on_grid(enemy, grid_copy)

    if(next_step == ''):
        return True

    return False

#Checa se uma parede bloqueia as saidas de todos os inimigos
def block_exits_for_everyone(enemies, block_position, orientation, grid):
    for enemy in enemies:
        if(block_all_exits(enemy, block_position, orientation, grid)):
            return True
        
    return False


# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

# w: width of the board
# h: height of the board
# player_count: number of players (2 or 3)
# my_id: id of my player (0 = 1st player, 1 = 2nd player, ...)
w, h, player_count, my_id = [int(i) for i in input().split()]

#Instanciando meu dragao
my_dragon = Dragon(my_id,0,0,0,None)

#Instanciando array que representa a grid do jogo
grid = []

#Populando grid com GridCells
for x in range(9):
    grid.append([])
    for y in range(9):
        grid[x].append(GridCell(x, y))

#for y in range(9):
#    print(grid[y], file=sys.stderr, flush=True)

gameturn = 0

# game loop
while True:
    walls = []

    #Setando os vizinhos de cada celula do grid
    for x in range(9):
        for y in range(9):
            grid[x][y].neighbours = get_neighbours(x, y, grid)
    
    #Instanciando array dos dragões inimigos
    enemy_dragons = []

    for i in range(player_count):
        # x: x-coordinate of the player
        # y: y-coordinate of the player
        # walls_left: number of walls available for the player
        x, y, walls_left = [int(j) for j in input().split()]

        #Populando objetos dragao com os dados do input
        if(i == my_id): #Se e meu dragao seta os atributos
            my_dragon.x = x
            my_dragon.y = y
            my_dragon.walls_left = walls_left
            my_dragon.goal = what_is_my_goal(i)
        else: #Se e inimigo, cria e adiciona no array de inimigos
            enemy_dragons.append(Dragon(i,x,y,walls_left,what_is_my_goal(i)))

    wall_count = int(input())  # number of walls on the board
    for i in range(wall_count):
        inputs = input().split()
        wall_x = int(inputs[0])  # x-coordinate of the wall
        wall_y = int(inputs[1])  # y-coordinate of the wall
        wall_orientation = inputs[2]  # wall orientation ('H' or 'V')

        walls.append(Wall(wall_x, wall_y, wall_orientation))
        
        #Checando orientacao da parede para remover vizinhanças
        if(wall_orientation == 'V'):
            #Removendo vizinhança das celulas a direita da parede
            grid[wall_x][wall_y].neighbours.pop("LEFT")
            grid[wall_x][wall_y+1].neighbours.pop("LEFT")

            #Removendo vizinhança das celulas a esquerda da parede
            grid[wall_x-1][wall_y].neighbours.pop("RIGHT")
            grid[wall_x-1][wall_y+1].neighbours.pop("RIGHT")

        else:
            grid[wall_x][wall_y].neighbours.pop("TOP")
            grid[wall_x+1][wall_y].neighbours.pop("TOP")

            grid[wall_x][wall_y-1].neighbours.pop("DOWN")
            grid[wall_x+1][wall_y-1].neighbours.pop("DOWN")
            
    enemy_closest_to_objective, enemy_closest_to_objective_distance, enemy_next_step = find_enemy_closest_to_objective(enemy_dragons, grid)
    closest_objective_pos, distance_to_objective, next_step = find_closest_objective_position_on_grid(my_dragon, grid)    

    distance_difference = enemy_closest_to_objective_distance - distance_to_objective

    #Definindo um intervalo pra começar a colocar as paredes
    if(gameturn < 5):
        print(next_step)
    else:
        #Se meu dragao tem id maior que o inimigo mais proximo do objetivo e ambos chegarem ao mesmo tempo, ele ganha
        if(my_dragon.player_id > enemy_closest_to_objective.player_id): 
            if(distance_difference <= 0 and enemy_closest_to_objective_distance > 0 and my_dragon.walls_left > 0): #devo me manter a frente
                block_position, orientation = block(enemy_closest_to_objective.x, enemy_closest_to_objective.y, enemy_next_step, walls)
                if(block_position != None and not block_exits_for_everyone(enemy_dragons, block_position, orientation, grid) and not block_all_exits(my_dragon, block_position, orientation, grid)):
                    print(block_position[0], block_position[1], orientation)
                else:
                    print(enemy_closest_to_objective.x, enemy_closest_to_objective.y, file=sys.stderr, flush=True)
                    print("mov", file=sys.stderr, flush=True)
                    print(next_step)
            else:
                print(next_step)
        #Se meu dragao tem id menor que o inimigo mais proximo do objetivo e ambos chegarem ao mesmo tempo, eu ganho
        else:
            if(distance_difference < 0 and enemy_closest_to_objective_distance > 0 and my_dragon.walls_left > 0): #nao posso ficar atras
                block_position, orientation = block(enemy_closest_to_objective.x, enemy_closest_to_objective.y, enemy_next_step, walls)
                if(block_position != None and not block_exits_for_everyone(enemy_dragons, block_position, orientation, grid) and not block_all_exits(my_dragon, block_position, orientation, grid)):
                    print(block_position[0], block_position[1], orientation)
                else:
                    print(enemy_closest_to_objective.x, enemy_closest_to_objective.y, file=sys.stderr, flush=True)
                    print("mov", file=sys.stderr, flush=True)
                    print(next_step)
            else:
                print(next_step)

    gameturn +=1

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)


    # action: LEFT, RIGHT, UP, DOWN or "putX putY putOrientation" to place a wall
   
