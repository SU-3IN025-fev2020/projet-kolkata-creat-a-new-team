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
    game.fps = 50  # frames per second
    game.mainiteration()
    game.mask.allow_overlaping_players = True
    #player = game.player
    
######################################################################################
class Client():
    def __init__(self, i, strat, nbR):
        self.nbR = nbR # nombre de restaurants
        self.resto = random.randint(0,nbR-1) # resto cible
        self.strat = strat # strat choisie
        self.score = 0
        self.nbplay = 1 # Nombre d'itération de la stratégie
        self.id = i
        
    def update_choix(self, frequentation): 
        """
        Prend la liste de fréquentation des restaurant et applique la stratégie
        de l'agent:
        'aleatoire', 'tetu', 'moins_freq'
        """
        self.nbplay += 1
        if self.strat == 'aleatoire':
            self.resto = random.randint(0,self.nbR-1)
        
        elif self.strat == 'moins_freq':
            """
            choisi un restaurant au hasard parmis les restaurants les moins
            fréquenté
            """
            tmp = np.where(frequentation == np.min(frequentation))[0]
            self.resto = random.choice(tmp)
            
        elif self.strat == 'plus_freq':
            """
            choisi un restaurant au hasard parmis les restaurants les plus
            fréquentés
            Contre stratégie à moins_freq
            """
            tmp = np.where(not frequentation == np.min(frequentation))[0]
            self.resto = random.choice(tmp)
            
        elif self.strat == 'moins_freq_alea':
            """
            choisi un restaurant au hasard avec une probabilité pour chaque restaurant 
            correspondante à l'inverse du pourcentage de fréquentation
            """
            a = 10 - np.array(frequentation)
            a = a/sum(a)
            self.resto = np.where(np.random.multinomial(1,a))[0][0]
            
        elif self.strat == 'plus_freq_alea':
            """
            choisi un restaurant au hasard avec une probabilité pour chaque restaurant 
            correspondante au pourcentage de fréquentation
            """
            a = np.array(frequentation)/sum(frequentation)
            self.resto = np.where(np.random.multinomial(1,a))[0][0]
            
    def toString(self):
        return "Client :{} strat : {}\n\tmean score : {:07.3f} score : {}\n".format(self.id,self.strat,(self.score/self.nbplay),self.score)


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
                    
    def play(self, player, restaurant):
        """
        player : numéro du joueur
        restaurant : numéro du restaurant
        Etabli la liste des cases qu'un joueur doit empreinter pour atteindre son 
        restaurant, utilise l'algorithme A*
        """
        
        row, col = self.players[player].get_rowcol()
        r = self.restau[restaurant]
        
        frontier = PriorityQueue()
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
                #On explore la position si c'est celle d'une case valide
                # et si elle n'a pas déjà été rajoutée aux positions à explorer
                if (x,y) not in l and self.move_possible(x,y):
                    m = self.manhattan_dst(r, x, y)
                    #On rajoute la case dans la liste "à explorer"
                    frontier.put((m +dst+1, x, y, dst+1))
                    l[(x,y)] = (row, col)# On indique que (row, col) est le pére de (x,y) 
        
        # La case de départ possède un père (-1,-1)
        # On remonte la liste des père des cases explorés du restaurant
        # jusqu'à la case de (-1,-1)
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
    # chaque joueur choisit un restaurant et une stratégie
    #-------------------------------
    
    d = ["aleatoire", "tetu"]
    #d = ["aleatoire", "tetu", "moins_freq"]
    #d = ["plus_freq", "moins_freq"]
    #d = ["plus_freq_alea", "moins_freq_alea"]
    clients=[Client(o, d[(o+1)%len(d)], nbRestaus) for o in range(nbPlayers)]
    

    #-------------------------------
    # Boucle principale de déplacements 
    #-------------------------------
    A = Aetoile(game)
    for i in range(20):
    
        resto = [[] for _ in range(nbRestaus)] # Liste des joueurs dans les restaurants
        
        for j in range(nbPlayers): 
            # On établit la liste des cases de la position du joueur à son restaurant
            l = A.play(j, clients[j].resto)
            
            for i in l: # On fait avancer le joueur
                players[j].set_rowcol(i[0], i[1])
                game.mainiteration()
                #o = players[j].ramasse(game.layers)
                #goalStates.remove((row,col)) # on enlève ce goalState de la liste
            
            resto[clients[j].resto] += [clients[j].id]
            
        frequentation = [len(j) for j in resto]
        
        for j in resto: # on compte les points
            if len(j) > 0:
                clients[random.choice(j)].score += 1
                
        # On update les clients
        for j in clients :
            j.update_choix(frequentation)
    
    for i in clients:
        print(i.toString())
                
        
    pygame.quit()
if __name__ == '__main__':
    main()
    


