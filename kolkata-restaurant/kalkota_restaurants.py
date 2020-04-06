# -*- coding: utf-8 -*-

# Nicolas, 2020-03-20

from __future__ import absolute_import, print_function, unicode_literals
from gameclass import Game,check_init_game_done
from spritebuilder import SpriteBuilder
from players import Player
from sprite import MovingSprite
from ontology import Ontology
from itertools import chain
import pygame
import glo
from queue import PriorityQueue
import random 
import numpy as np
import sys



    
# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()

def init(_boardname=None):
    global player,game
    # pathfindingWorld_MultiPlayer4
    name = _boardname if _boardname is not None else 'kolkata_6_10'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 100  # frames per second
    game.mainiteration()
    game.mask.allow_overlaping_players = True
    #player = game.player
    
######################################################################################
class Client():
    def __init__(self, i, strat, nbR):
        self.nbR = nbR
        self.resto = random.randint(0,nbR-1)
        self.strat = strat
        self.score = 0
        self.id = i
        self.dictio_strat = {0 : "aléatoire",1 : "tétu"}
        
    def update_choix(self):
        if self.strat == 0:
            self.resto = random.randint(0,self.nbR-1)
        
    def toString(self):
        return 'Client '+str(self.id)+' strat ' + self.dictio_strat.get(self.strat, "tétu")+" score : "+str(self.score)


class Aetoile():
    def __init__(self, game):
        self.game = game
        
        self.nbL = game.spriteBuilder.rowsize
        self.nbC = game.spriteBuilder.colsize
        
        self.players = [o for o in game.layers['joueur']]
        
        self.wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
        self.restau = [o.get_rowcol() for o in game.layers['ramassable']]
        #self.posPlayers = [o.get_rowcol() for o in game.layers['joueur']]
        
    def manhattan_dst(self, r, a, b):
        return abs(a-r[0]) + abs(b-r[1])
        
    def move_possible(self, x, y):
        if ((x,y) not in self.wallStates) and \
                x>=0 and x<self.nbL and \
                y>=0 and y<self.nbC:
            return True
        return False
                    
    def strat(self, p, r):
        """
        Etabli la liste des cases qu'un joueur p doit empreinter pour atteindre le 
        restaurant r utilisant l'algorithme de A*
        """
        
        r = self.restau[r]
        
        frontier = PriorityQueue()
        row, col = self.players[p].get_rowcol()
        l = {(row, col) : (-1, -1)} # Dictionnaire des péres
        
        #Liste des positions à parcourir
        dst = 0
        m = self.manhattan_dst(r, row, col)
        frontier.put((m, row, col, dst))
        while(True):
            m, row, col, dst = frontier.get() #Prend le + petit
            if (row,col) == r: break # On a atteint le restaurant
            for i in [(0,1),(0,-1),(1,0),(-1,0)]: #On regarde les 4 directions
                x = row + i[0]
                y = col + i[1]
                #On explore la position si : elle correspond à une case valide,
                #si elle n'a pas déjà été rajoutée aux positions a explorer
                if (x,y) not in l and self.move_possible(x,y):
                    m = self.manhattan_dst(r, x, y)
                    #On rajoute la case dans la liste à explorer
                    frontier.put((m +dst+1, x, y, dst+1))
                    l[(x,y)] = (row, col)# On indique que (row, col) est le pére de (x,y) 
        
        def roll_back(posi):
            if posi == (-1, -1):
                return []
            return  roll_back(l[posi]) + [posi]
        return roll_back(r)
        
            
####################################################################################""
    
def main():

    #for arg in sys.argv:
    iterations = 20 # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print ("Iterations: ")
    print (iterations)

    init()
    #-------------------------------
    # Initialisation
    #-------------------------------
    nbLignes = game.spriteBuilder.rowsize
    nbColonnes = game.spriteBuilder.colsize
    print("lignes", nbLignes)
    print("colonnes", nbColonnes)
    players = [o for o in game.layers['joueur']]
    nbPlayers = len(game.layers['joueur'])
    # on localise tous les états initiaux (loc du joueur)
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)
    # on localise tous les objets  ramassables (les restaurants)
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)
    nbRestaus = len(goalStates)
    # on localise tous les murs
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    #print ("Wall states:", wallStates)
    # on liste toutes les positions permises
    allowedStates = [(x,y) for x in range(nbLignes) for y in range(nbColonnes)\
                     if (x,y) not in wallStates or  goalStates] 
    #-------------------------------
    # Placement aleatoire des joueurs, en évitant les obstacles
    #-------------------------------
    posPlayers = initStates
    for j in range(nbPlayers):
        x,y = random.choice(allowedStates)
        players[j].set_rowcol(x,y)
        game.mainiteration()
        posPlayers[j]=(x,y)
    #-------------------------------
    # chaque joueur choisit un restaurant
    #-------------------------------
    clients=[Client(o, (o+1)%2, nbRestaus) for o in range(nbPlayers)]
    

    #-------------------------------
    # Boucle principale de déplacements 
    #-------------------------------
    A = Aetoile(game)
    for i in range(20):
        for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
            l = A.strat(j, clients[j].resto)
            for i in l:
                players[j].set_rowcol(i[0], i[1])
                game.mainiteration()
                #o = players[j].ramasse(game.layers)
                #goalStates.remove((row,col)) # on enlève ce goalState de la liste
        resto = [[] for _ in range(nbRestaus)]
        
        for j in clients:
            j.update_choix()
            resto[j.resto] += [j.id]
        
        for j in resto:
            if len(j) > 0:
                clients[random.choice(j)].score += 1
    
    for i in clients:
        print(i.toString())
                
        
    pygame.quit()
if __name__ == '__main__':
    main()
    


