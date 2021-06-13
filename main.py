from subprocess import call

call(["python", "-m", "pip", "install", "-r", "requirements.txt"])

import random
import copy
import math
from tkinter import *
from PIL import Image, ImageTk
from os import listdir
from time import sleep

fenetre = Tk()
fenetre.title('Rogue : The Spiral Of The Abyss')
croix = Image.open('data/croix.png')
croix = croix.resize((32, 32), resample=Image.NEAREST)
base_textures = [ImageTk.PhotoImage(croix)]

width = fenetre.winfo_screenwidth()
height = fenetre.winfo_screenheight()

list_input = [
    '&', 'eacute', 'quotedbl', "'", 'parenleft', 'minus', 'egrave',
    'underscore', 'ccedilla', 'agrave'
]


class Element(object):
    """Class qui définit les intéractions et informations de bases que partage tous les éléments du jeu."""

    def __init__(self, name, abbrv=None, textures=None):
        """Constructeur de la class Element"""
        if abbrv is None:
            abbrv = name[0]
        self.name = name
        self.abbrv = abbrv
        self.animation_tick = 0
        if textures is None:
            self.textures = base_textures
        else:
            self.textures = textures
        self.current_texture = self.textures[0]

    def __repr__(self):
        """Définition de la représentation d'un élément de la class Element"""
        return self.abbrv

    def description(self):
        """Méthode description d'un élément de la class Element"""
        return "<" + self.name + ">"

    def meet(self, hero):
        """Méthode qui gère la rencontre entre un objet et le héro en l'ajoutant dans l'inventaire et en retournant True"""
        raise NotImplementedError("Not implemented yet")

    def update(self, dt):
        """Méthode qui permet de passer d'une texture à la suivante pour créer des animations"""
        self.animation_tick += 1 * dt
        if self.animation_tick >= len(self.textures):
            self.animation_tick = 0
        self.current_texture = self.textures[int(self.animation_tick)]


class Stairs(Element):
    """classe pour implémenter des escaliers et par la même occasion des étages"""

    def __init__(self, name='stairs', abbrv="L"):
        Element.__init__(self, name, abbrv)

    def meet(self, hero):
        """Méthode pour gérer le changement d'étage"""
        theGame().level += 1
        theGame().buildFloor()
        if theGame().level % 2 == 0:
            for key, item in theGame().floor._elem.items():
                if isinstance(key, Creature) and not isinstance(key, Hero):
                    key.hpmax += theGame().level // 2
                    key.hp = key.hpmax
                    key.strength += (theGame().level - 1) // 2
        else:
            for key, item in theGame().floor._elem.items():
                if isinstance(key, Creature) and not isinstance(key, Hero):
                    key.hpmax += (theGame().level - 1) // 2
                    key.hp = key.hpmax
                    key.strength += theGame().level // 2

    def textureAttribution(self):
        """Méthode qui attribut des texture aux objets"""
        for i in theGame().interface.data[self.name]:
            self.textures.append(i)
        self.current_texture = self.textures[0]


class Equipment(Element):
    """Class qui hérite de Element qui gère les informations et intéractions que partage tous les équipements du jeu."""

    def __init__(self, name, abbrv=None, usage=None):
        """Constructeur de la class Equipment"""
        Element.__init__(self, name, abbrv)
        self.usage = usage
        self.textures = []

    def meet(self, hero):
        """Méthode qui gère la rencontre entre un objet et le héro en l'ajoutant dans l'inventaire et en retournant True"""
        if self.name == 'gold' or len(hero._inventory) < 10:
            theGame().addMessage("You pick up a " + self.name)
            Hero.take(hero, self)
            return True
        return False

    def use(self, creature):
        """Méthode qui gère l'utilisation d'un consommable"""
        if self.usage != None:
            theGame().addMessage("The " + str(creature.name) + " uses the " + str(self.name))
            return self.usage(self, creature)
        theGame().addMessage("The " + str(self.name) + " is not usable")
        return False

    def textureAttribution(self):
        """Méthode qui attribut des texture aux objets"""
        for key, item in theGame().interface.data[self.name].items():
            self.textures.append(item)
        self.current_texture = self.textures[0]


class Armure(Equipment):
    """Classe qui hérite de Equipment pour gérer les armures"""

    def __init__(self, name, abbrv=None, defense=0, durability=None):
        Equipment.__init__(self, name, abbrv, usage=None)
        self.defense = defense
        self.durability = durability
        self.maxdurability = durability

    def use(self, hero):
        """Méthode qui gère l'action d'équiper une armure"""
        theGame().hero.changeEquipment(self)

    def breakArmure(self, hero):
        if self.durability is not None:
            self.durability -= 1
            if self.durability <= 0:
                hero._armure = None
                theGame().addMessage(f"Flûte alors {self.name} s'est brisé")


class Arme(Equipment):
    """Classe qui hérite de Equipment pour gérer les armes"""

    def __init__(self, name, abbrv=None, attaque=0, durability=None):
        Equipment.__init__(self, name, abbrv, usage=None)
        self.attaque = attaque
        self.durability = durability
        self.maxdurability = durability

    def use(self, hero):
        """Méthode qui gère l'action d'équiper une arme"""
        theGame().hero.changeEquipment(self)

    def breakArme(self, hero):
        if self.durability is not None:
            self.durability -= 1
            if self.durability <= 0:
                hero._arme = None
                theGame().addMessage(f"Flûte alors {self.name} s'est brisé")


class Creature(Element):
    """Class qui hérite des attributs de Element"""

    def __init__(self, name, hp, abbrv=None, strength=1, xp=0, invisible=False, poisonous=False, faster=False):
        """Constructeur de la class Creature"""
        Element.__init__(self, name, abbrv)
        self.hp = hp
        self.hpmax = hp
        self.strength = strength
        self.textures = []
        self.xp = xp
        self.invisible = invisible
        self.poisonous = poisonous
        self.faster = faster
        self.makeInvisible()

    def makeInvisible(self):
        if self.invisible:
            self.abbrv = Map.ground

    def removeInvisibility(self):
        self.invisible = False
        self.abbrv = self.name[0]

    def description(self):
        """Méthode description d'un élément de la class Creature"""
        return Element.description(self) + "(" + str(self.hp) + ")"

    def meet(self, other):
        """Méthode pour gérer les combats entre créature et héro"""
        if isinstance(other, Hero):
            other.removeInvisibility()
            self.removeInvisibility()
            other.hit(self)
            theGame().addMessage(f"The {other.name} hits the {self.name + '(' + str(self.hp) + ')'}")
            if self.hp <= 0:
                # Gain xp et passage niveau
                other.xp += self.xp
                other.gainLevel()
                return True
            return False
        else:
            other.removeInvisibility()
            self.encaisser(other)
            theGame().addMessage(f"The {other.name} hits the {self.name + '(' + str(self.hp) + ')'}")
            if other.poisonous:
                self.poison += 2
                self.poison_delay += 1

    def textureAttribution(self):
        """Méthode qui attribut des texture aux créatures et au Héro par la même occasion"""
        if isinstance(self, Hero):
            for key, item in theGame().interface.data['Hero'].items():
                self.textures.append(item)
        else:
            for key, item in theGame().interface.data[self.name].items():
                self.textures.append(item)
        self.current_texture = self.textures[0]


class Hero(Creature):
    """Class qui hérite des attrubuts de Creature"""

    def __init__(self, name="Hero", hp=10, abbrv="@", strength=2, gold=0, xp=0, mana=10):
        """Constructeur de la class Hero"""
        Creature.__init__(self, name, hp, abbrv, strength, xp)
        self._inventory = []
        self.gold = gold
        self.level = 1
        self.mana = mana
        self.manamax = mana
        self._arme = None
        self._armure = None
        self.poison = 0
        self.poison_delay = 0
        self.invisibility = 0

    def invisibilityDecrease(self):
        if self.invisibility>0:
            self.invisibility-=1

    def removeInvisibility(self):
        if self.invisibility>0:
            self.invisibility=0

    def magicInvisibility(self):
        if self.mana >= 3:
            self.invisibility += 4
            self.mana-=3
            theGame().addMessage("Be quiet ! Now you're hidden !")
        else :
            theGame().addMessage("Invisibility cannot be activated !")

    def magicHeal(self):
        if self.mana >= 2 and self.hp < self.hpmax:
            heal(self, self.hpmax * 3 // 10)
            self.mana -= 2
            theGame().addMessage(f"{self.name} used the spell Heal !")
        else:
            theGame().addMessage("Heal cannot be activated !")

    def magicTeleportation(self):
        if self.mana >= 1:
            teleport(self, True)
            self.mana -= 1
            theGame().addMessage(f"{self.name} used the spell Teleportation !")
        else:
            theGame().addMessage("Teleportation cannot be activated !")

    def poisonRecovery(self):
        if self.poison > 0:
            if self.poison_delay == 0:
                self.poison -= 1
                self.hp -= 1
                self.poison_delay = 1
            else:
                self.poison_delay -= 1

    def changeEquipment(self, equipment):
        if isinstance(equipment, Arme):
            if self._arme is None:
                self._arme = equipment
                self._inventory.remove(equipment)
                theGame().addMessage(f'{self.name} equip the {equipment.name}')
            else:
                theGame().addMessage(
                    f'{self.name} put the {self._arme.name} in his inventory' + '\n' + f'and take the {equipment.name}')
                self._inventory.append(self._arme)
                self._arme = equipment
                self._inventory.remove(equipment)
        else:
            if self._armure is None:
                self._armure = equipment
                self._inventory.remove(equipment)
                theGame().addMessage(f'{self.name} equip the {equipment.name}')
            else:
                theGame().addMessage(
                    f'{self.name} put the {self._armure.name} in his inventory' + '\n' + f'and equip the {equipment.name}')
                self._inventory.append(self._armure)
                self._armure = equipment
                self._inventory.remove(equipment)

    def hit(self, monster):
        """Partie pour gérer une attaque du héro avec ou sans arme"""
        if self._arme is not None:
            monster.hp -= self.strength + self._arme.attaque
            self._arme.breakArme(self)
        else:
            monster.hp -= self.strength

    def encaisser(self, monster):
        """Partie défense du héro avec ou sans armure"""
        if self._armure is not None:
            if self._armure.defense < monster.strength:
                self.hp -= monster.strength - self._armure.defense
            self._armure.breakArmure(self)
        else:
            self.hp -= monster.strength

    def gainLevel(self):
        """Méthode qui gère le passage au niveau supérieur"""
        if self.xp >= self.level * 10:
            self.xp -= self.level * 10
            self.level += 1
            self.hpmax += 2
            self.hp = self.hpmax
            self.strength += 1
            theGame().addMessage(f'Well done, you are now at level {self.level} !')
            if self.poison > 0:
                self.poison = 0
                self.poison_delay = 0
                theGame().addMessage(f'Eureka, by passing a level :' + '\n' + 'the poison has been removed !')

    def take(self, elem):
        """Méthode qui ajoute l'élément elem à l'inventaire"""
        if isinstance(elem, Equipment):
            if elem.name == 'gold':
                self.gold += 1
            else:
                self._inventory.append(elem)
        else:
            raise TypeError

    def description(self):
        """Méthode description d'un élément de la class Hero"""
        return Creature.description(self) + str(self._inventory)

    def fullDescription(self):
        """Méthode qui génère une description détaillé des attributs du héros, pv restant, force,
        contenu inventaire... """
        res = ''
        for key, item in self.__dict__.items():
            if '_' not in key and key != 'textures':
                res += f'> {key} : {item}\n'
        res += f'> INVENTORY : {[x.name for x in self._inventory]}'
        return res

    def use(self, item):
        """Méthode qui est appelé quand on veut utiliser un item afin de vérifier que l'item existe et qu'il est dans
        l'inventaire pour ensuite appelé la méthode de la classe Equipment """
        if not isinstance(item, Equipment):
            raise TypeError
        elif item not in self._inventory:
            raise ValueError
        else:
            if item.use(self):
                self._inventory.remove(item)


class Coord(object):
    """Class qui permet de gérer le système de coordonnées du jeu ainsi que leurs différente propriétés et
    utilisation """

    def __init__(self, x, y):
        "Constructeur de l'objet"
        self.x = x
        self.y = y

    def __repr__(self):
        "définition d'une représentation des éléments de Coord pour les print"
        return "<" + str(self.x) + "," + str(self.y) + ">"

    def __eq__(self, other):
        "définition de l'égalité de 2 éléments de la classe Coord"
        if self.x == other.x and self.y == other.y:
            return True
        return False

    def __add__(self, other):
        "définition de l'addition de 2 éléments de Coord"
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        "définition de la soustraction de 2 éléments de Coord"
        return Coord(self.x - other.x, self.y - other.y)

    def distance(self, other):
        "Calcule la distance entre 2 éléments de Coord"
        return math.sqrt(math.pow((other.x - self.x), 2) + math.pow((other.y - self.y), 2))

    def direction(self, other):
        """Calcule l'angle entre 2 objet, utile pour calculer dans quel direction doit se déplacer un monstre
        afin de rejoindre le joueur """
        cos = (self - other).x / math.sqrt(math.pow((self - other).x, 2) + math.pow((self - other).y, 2))
        if cos > 1 / math.sqrt(2):
            return Coord(-1, 0)
        elif cos < -1 / math.sqrt(2):
            return Coord(1, 0)
        elif self.__sub__(other).y > 0:
            return Coord(0, -1)
        else:
            return Coord(0, 1)


class Map(object):
    "définition de la matrice de placement des éléments du jeu ainsi que leur représentation"
    ground = "."
    empty = " "
    dir = {"z": Coord(0, -1), "s": Coord(0, 1), "d": Coord(1, 0), "q": Coord(-1, 0)}

    def __init__(self, size=20, nbrooms=7, hero=None):
        "Constructeur de Map"
        self.size = size
        if hero == None:
            hero = Hero()
        self.hero = hero
        res = []
        for i in range(0, size):
            res2 = []
            for i in range(0, size):
                res2.append(Map.empty)
            res.append(res2)
        self._mat = res
        self._elem = {}
        self._roomsToReach = []
        self._rooms = []
        self.generateRooms(nbrooms)
        self.reachAllRooms()
        self.put(self._rooms[0].center(), hero)
        for i in self._rooms:
            i.decorate(self)
        self.stairsPlacement()

    def __repr__(self):
        "définition de la représentation d'un élément de Map"
        res = ''
        for y in range(0, self.size):
            for i in range(0, self.size):
                res += str(self._mat[y][i])
            res += '\n'
        return res

    def __len__(self):
        """Méthode protégé qui renvoie la taille de la map quand on fait len d'un élément de map"""
        return self.size

    def __contains__(self, item):
        """Méthode protégé qui renvoie True si l'élement est une coord appartenant à la map ou un item qui est présent sur la map"""
        if isinstance(item, Coord):
            if item.x >= 0 and item.x < self.size and item.y >= 0 and item.y < self.size:
                return True
        else:
            for i in self._mat:
                if item in i:
                    return True
        return False

    def get(self, c):
        "Donne l'élement qui est placé aux coordonnées c"
        self.checkCoord(c)
        return self._mat[c.y][c.x]

    def pos(self, e):
        "Donne la position d'un élément e unique sur la map"
        self.checkElement(e)
        for i in range(len(self._mat)):
            for y in range(len(self._mat)):
                if self._mat[i][y] == e:
                    return Coord(y, i)

    def put(self, c, e):
        "Remplace un item par un autre appelé e aux coordonnées c"
        self.checkCoord(c)
        if self.pos(e) is not None:
            raise KeyError
        if self._mat[c.y][c.x] != Map.ground:
            raise ValueError

        self._mat[c.y][c.x] = e
        self._elem[e] = Coord(c.x, c.y)

    def rm(self, c):
        "Remplace l'item placé aux coordonnées c par le ground"
        self.checkCoord(c)
        del self._elem[self._mat[c.y][c.x]]
        self._mat[c.y][c.x] = Map.ground

    def move(self, e, way):
        """Moves the element e in the direction way."""
        orig = self.pos(e)
        dest = orig + way
        if dest in self:
            if self.get(dest) == Map.ground:
                self._mat[orig.y][orig.x] = Map.ground
                self._mat[dest.y][dest.x] = e
                self._elem[e] = dest
            elif e == self.hero and self.get(dest) != Map.empty and self.get(dest).meet(e) and self.get(
                    dest) != self.hero:
                self.rm(dest)
            elif isinstance(e, Creature) and not isinstance(e, Hero) and isinstance(self.get(dest), Hero):
                self.get(dest).meet(e)
            if isinstance(e, Hero):
                if not isinstance(self.get(dest), Stairs):
                    self.moveAllMonsters()
                e.poisonRecovery()
                e.invisibilityDecrease()
                print()
                print(theGame().floor)
                print(theGame().hero.description())
                theGame().interface.partieHud()

    def addRoom(self, room):
        """Méthode permettant de créer une nouvelle salle"""
        self._roomsToReach.append(room)
        for y in range(room.c1.y, room.c2.y + 1):
            for x in range(room.c1.x, room.c2.x + 1):
                self._mat[y][x] = Map.ground

    def findRoom(self, coord):
        """Methode permettant de choisir une salle au hasard dans les salles encore non reliées par les couloirs"""
        for i in self._roomsToReach:
            if coord in i:
                return i
        return False

    def intersectNone(self, room):
        """Méthode qui vérifie que la salle en question n'est relié a aucune autre."""
        for i in self._roomsToReach:
            if room.intersect(i):
                return False
        return True

    def dig(self, coord):
        """Méthode qui permet de transformer du vide en sol"""
        self._mat[coord.y][coord.x] = Map.ground
        if self.findRoom(coord):
            self._rooms.append(self.findRoom(coord))
            self._roomsToReach.remove(self.findRoom(coord))

    def corridor(self, start, end):
        """Méthode qui permet de relier 2 salles à l'aide de la méthode dig"""
        self.dig(start)
        if start.y > end.y:
            while start.y != end.y:
                start += Coord(0, -1)
                self.dig(start)
        else:
            while start.y != end.y:
                start += Coord(0, 1)
                self.dig(start)
        if start.x > end.x:
            while start.x != end.x:
                start += Coord(-1, 0)
                self.dig(start)
        else:
            while start.x != end.x:
                start += Coord(1, 0)
                self.dig(start)

    def reach(self):
        """Méthode qui choisit 2 salles et qui les relie via la méthode corridor"""
        a = self._rooms[random.randint(0, len(self._rooms) - 1)]
        b = self._roomsToReach[random.randint(0, len(self._roomsToReach) - 1)]
        self.corridor(a.center(), b.center())

    def reachAllRooms(self):
        """Méthode appelant en boucle la méthode reach pour relier toutes les salles entre elles"""
        self._rooms.append(self._roomsToReach[0])
        del self._roomsToReach[0]
        while len(self._roomsToReach) != 0:
            self.reach()

    def randRoom(self):
        """Méthode qui permet de créer une salle aléatoire"""
        x1 = random.randint(0, len(self) - 3)
        y1 = random.randint(0, len(self) - 3)
        return Room(Coord(x1, y1),
                    Coord(min(len(self) - 1, x1 + random.randint(3, 8)), min(len(self) - 1, y1 + random.randint(3, 8))))

    def generateRooms(self, n):
        """Méthode qui crée un nombre n de salle non collé sur la map"""
        while n != 0:
            x = self.randRoom()
            if self.intersectNone(x):
                self.addRoom(x)
            n -= 1

    def checkCoord(self, c):
        """Méthode qui permet de tester si c est une coord et si elle appartient à la map"""
        if not isinstance(c, Coord):
            raise TypeError
        elif c not in self:
            raise IndexError

    def checkElement(self, e):
        """Méthode qui permet de tester si e est un objet de la class Element"""
        if not isinstance(e, Element):
            raise TypeError

    def moveAllMonsters(self):
        """Méthode qui permet de déplacer simultanément tout les monstres situés à moins de 6 cases du héros"""
        for i in self._elem:
            if isinstance(i, Creature) and not isinstance(i, Hero) and Coord.distance(self.pos(i),
                                                                                      self.pos(self.hero)) <= 6 and theGame().hero.invisibility==0:
                self.move(i, Coord.direction(self.pos(i), self.pos(self.hero)))
                if i.faster:
                    self.move(i, Coord.direction(self.pos(i), self.pos(self.hero)))

    def update(self):
        for key, element in self._elem.items():
            if not isinstance(key, Stairs):
                key.update()

    def stairsPlacement(self):
        try:
            self.put(random.choice(self._rooms[1:]).center(), Stairs(name='stairs'))
        except ValueError:
            self.put(random.choice(self._rooms[1:]).center(), Stairs(name='stairs'))


class Room(object):
    """Class qui permet de gérer les salles de chaque map"""

    def __init__(self, c1, c2):
        """Constructeur de la class Room"""
        self.c1 = c1
        self.c2 = c2

    def __repr__(self):
        """Méthode protégée qui sert lorsque l'on print un élément de Room"""
        return "[" + str(self.c1) + ", " + str(self.c2) + "]"

    def __contains__(self, test):
        """Méthode qui permet de savoir si un élément de Coord appartient à la salle que l'on teste"""
        if test.x <= self.c2.x and test.x >= self.c1.x and test.y <= self.c2.y and test.y >= self.c1.y:
            return True

    def center(self):
        """Méthode qui retourne la coordonnée du centre de la map"""
        return Coord((self.c1.x + self.c2.x) // 2, (self.c1.y + self.c2.y) // 2)

    def intersect(self, other):
        """Méthode qui vérifie si une salle empiète sur l'autre et inversement, renvoie true si c'est le cas et false sinon"""
        if self.c1 in other or self.c2 in other or Coord(self.c1.x, self.c2.y) in other or Coord(self.c2.x,
                                                                                                 self.c1.y) in other or other.c1 in self or other.c2 in self or Coord(
            other.c1.x, other.c2.y) in self or Coord(other.c2.x, other.c1.y) in self:
            return True
        else:
            return False

    def randCoord(self):
        """Méthode qui choisit une coordonnée aléatoire dans la salle"""
        return Coord(random.randint(self.c1.x, self.c2.x), random.randint(self.c1.y, self.c2.y))

    def randEmptyCoord(self, map):
        """Méthode qui appelle randCoord pour avoir une coordonnée aléatoire dans la salle et vérifie si elle est
        libre, si c'est le cas on la retourne, sinon on recommence """
        while True:
            b = self.randCoord()
            if b != self.center() and map.get(b) == Map.ground:
                return b

    def decorate(self, map):
        """Méthode qui ajoute des équipements et monstre aléatoire dans des endroits aléatoire de la salle"""
        map.put(self.randEmptyCoord(map), theGame().randEquipment())
        map.put(self.randEmptyCoord(map), theGame().randMonster())


class Game(object):
    """Class qui définit les éléments de base du jeu, touches, liste monstres,objet, la messagerie,..."""
    equipments = {0: [Equipment("heal_potion", "!", usage=lambda equip, user: heal(user, 3)), Equipment("gold", "o")],
                  1: [Arme("sword", attaque=1, durability=20),
                      Equipment("teleport_potion", "%", usage=lambda equip, user: teleport(user, True)),
                      Equipment("antidote", '+', usage=lambda equip, user: curePoison(user))],
                  2: [Armure("chainmail", defense=1, durability=20),
                      Equipment("Mana_potion", 'm', usage=lambda equip, user: ManaRecovery(user, 3))],
                  3: [Equipment("portoloin", "w", usage=lambda equip, user: teleport(user, False))]}
    monsters = {0: [Creature("Gobelin", 4, xp=3), Creature("Squelette", 2, "W", xp=2),
                    Creature('Ghost', 3, xp=5, invisible=True)],
                1: [Creature("Ork", 6, strength=2, xp=5), Creature("Blob", 10, xp=4)],
                2: [Creature('Muddy', 5, xp=7, poisonous=True)],
                3: [Creature('Diablotin', 4, strength=1, xp=9, faster=True)],
                5: [Creature("Dragon", 20, strength=3, xp=10)]}
    _actions = {'z': lambda hero: theGame().floor.move(hero, Coord(0, -1)),
                's': lambda hero: theGame().floor.move(hero, Coord(0, 1)),
                'q': lambda hero: theGame().floor.move(hero, Coord(-1, 0)),
                'd': lambda hero: theGame().floor.move(hero, Coord(1, 0)),
                'i': lambda hero: theGame().afficheFullDescription(),
                'k': lambda hero: theGame().suicide(),
                'r': lambda hero: theGame().rest(),
                ' ': lambda hero: None,
                ',': lambda hero: hero.magicHeal(),
                ';': lambda hero: hero.magicTeleportation(),
                ':': lambda hero: hero.magicInvisibility()}

    def __init__(self, interface, hero=None, level=1):
        """Constructeur de la class Game"""
        if hero == None:
            hero = Hero()
        self.hero = hero
        self.level = level
        self.floor = None
        self._message = []
        self.interface = interface
        self.sieste = None

    def rest(self):
        if self.sieste == 0 and self.hero.hp < self.hero.hpmax:
            self.sieste += 1
            if self.hero.hp + 5 > self.hero.hpmax:
                self.hero.hp = self.hero.hpmax
            else:
                self.hero.hp += 5
            for i in range(5):
                theGame().floor.moveAllMonsters()
            theGame().addMessage("Wake up ! Wake up !" + '\n' + "Time to slay some monster there !")
            theGame().hero.poisonRecovery()
            print()
            print(theGame().floor)
            print(theGame().hero.description())
            theGame().interface.partieHud()
        else:
            theGame().addMessage("You can't rest for the moment," + '\n' + "try later :P")
            theGame().interface.partieHud()

    def suicide(self):
        self.hero.__setattr__('hp', 0)
        self.interface.fenetre.destroy()

    def buildFloor(self):
        """Méthode qui crée une map aléatoire avec notre héros"""
        self.floor = Map(hero=self.hero)
        self.sieste = 0
        for key, item in self.floor._elem.items():
            key.textureAttribution()
        self.interface.generateBackground()
        self.interface.partieJeu()
        self.interface.partieHud()

    def addMessage(self, msg):
        """Méthode qui ajoute un message à la liste des messages à lire"""
        self._message.append(msg)

    def readMessages(self):
        """Méthode qui montre les messages à lire puis les supprime"""
        result = ""
        for i in self._message:
            result += str(i)
            if str(i)[-1] not in ['.', ';', ':', '!', '?']:
                result += ". "
            result += '\n'
        self._message.clear()
        return result

    def afficheFullDescription(self):
        """Méthode qui permet d'afficher dans l'interface graphique la description complète du héros lorsque l'on appuie sur 'i'."""
        self.addMessage(self.hero.fullDescription())
        self.interface.partieHud()

    def randElement(self, collection):
        """Méthode qui choisit un élément aléatoire dans une liste en fonction de l'étage de la map"""
        X = random.expovariate(1 / self.level)
        a = max(b for b in collection if b <= X)
        return random.choice(collection[a])

    def randEquipment(self):
        """Méthode qui retourne un équipement aléatoire parmi les équipements du jeu en fonction de l'étage de la map"""
        return copy.copy(self.randElement(Game.equipments))

    def randMonster(self):
        """Méthode qui retourne un monstre aléatoire parmi les monstres du jeu en fonction de l'étage de la map"""
        return copy.copy(self.randElement(Game.monsters))

    def select(self):
        """Méthode pour me faire les bind de touches relatif à l'utilisation d'objet"""
        for idx, item in enumerate(list_input):
            fenetre.bind(f"<KeyRelease-{item}>",
                         lambda e, n=idx: self.useItem(n))

    def remove(self):
        """Méthode pour me faire les bind de touches relatif à la suppression d'objet"""
        for idx, item in enumerate(list_input):
            fenetre.bind(f"<Control-KeyRelease-{item}>",
                         lambda e, n=idx: self.deleteItem(n))

    def useItem(self, idx):
        """Méthode qui est appelée lorsque l'une des touches qui sert à utiliser un item dans l'inventaire est pressée"""
        if idx < len(self.hero._inventory):
            self.hero.use(self.hero._inventory[idx])
            theGame().hero.poisonRecovery()
            print()
            print(theGame().floor)
            print(theGame().hero.description())
            self.floor.moveAllMonsters()
            self.interface.partieHud()

    def deleteItem(self, index):
        """Méthode qui est appelée lorsque l'une des touches qui sert à supprimer un item dans l'inventaire est pressée"""
        if index < len(self.hero._inventory):
            theGame().addMessage(f'You destroy a {self.hero._inventory[index].name}')
            self.hero._inventory.pop(index)
            print()
            print(theGame().floor)
            print(theGame().hero.description())
            self.interface.partieHud()

    def play(self):
        """Main game loop"""
        self.buildFloor()
        print("--- Welcome Hero! ---")
        print()
        print(self.floor)
        print(self.hero.description())
        print(self.readMessages())
        fenetre.bind('<KeyRelease>', onKeyRelease)
        self.select()
        self.remove()
        while self.hero.hp > 0:
            self.interface.partieJeu()
            fenetre.update()
            sleep(0.06025)
        self.interface.fenetre.quit()
        print("--- Game Over ---")


"""Partie interface graphique"""


class InterfaceJeu(object):
    """Class permettant de générer une interface graphique"""

    def __init__(self, width, height, fenetre):
        """initialisation des variables d'instance de mon interface"""
        self.data = {'floors': [],
                     'walls': [],
                     'stairs': [],
                     'heal_potion': {},
                     'gold': {},
                     'sword': {},
                     'teleport_potion': {},
                     'antidote': {},
                     'Mana_potion': {},
                     'chainmail': {},
                     'portoloin': {},
                     'Gobelin': {},
                     'Squelette': {},
                     'Ork': {},
                     'Blob': {},
                     'Dragon': {},
                     'Ghost': {},
                     'Muddy': {},
                     'Diablotin': {},
                     'Hero': {},
                     'hud': {}}
        self.width = width
        self.height = height
        self.fenetre = fenetre
        self.jeu = Canvas(self.fenetre, width=self.width, height=int((32 / 1920) * self.width) * 20)
        self.load()
        self.background = []
        self.hud = Canvas(self.fenetre, width=self.width, height=self.height - int((32 / 1920) * self.width) * 20,
                          bg='light grey')

    def load(self):
        """Import de l'ensemble des images de mon jeu"""
        taille_element_jeu = int((32 / 1920) * self.width)
        # floor
        for file in listdir('data/floor'):
            for angle_multiplier in range(4):
                floor = Image.open('data/floor/' + file)
                floor = floor.resize((taille_element_jeu, taille_element_jeu),
                                     resample=Image.NEAREST)
                self.data['floors'].append(ImageTk.PhotoImage(floor.rotate(angle_multiplier * 90)))

        # wall
        for file in listdir('data/wall'):
            walls = Image.open('data/wall/' + file)
            walls = walls.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['walls'].append(ImageTk.PhotoImage(walls))

        # stairs
        for file in listdir('data/stairs'):
            stairs = Image.open('data/stairs/' + file)
            stairs = stairs.resize((taille_element_jeu, taille_element_jeu),
                                   resample=Image.NEAREST)
            self.data['stairs'].append(ImageTk.PhotoImage(stairs))

        # heal_potion
        for file in listdir('data/heal_potion/idle'):
            potion = Image.open('data/heal_potion/idle/' + file)
            potion = potion.resize((taille_element_jeu, taille_element_jeu),
                                   resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['heal_potion']['heal_potion_idle_' + y[0]] = ImageTk.PhotoImage(potion)

        # gold
        for file in listdir('data/gold/idle'):
            gold = Image.open('data/gold/idle/' + file)
            gold = gold.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['gold']['gold_idle_' + y[0]] = ImageTk.PhotoImage(gold)

        # sword
        for file in listdir('data/sword/idle'):
            sword = Image.open('data/sword/idle/' + file)
            sword = sword.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['sword']['sword_idle_' + y[0]] = ImageTk.PhotoImage(sword)

        # teleport_potion
        for file in listdir('data/teleport_potion/idle'):
            teleport_potion = Image.open('data/teleport_potion/idle/' + file)
            teleport_potion = teleport_potion.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['teleport_potion']['teleport_potion_idle_' + y[0]] = ImageTk.PhotoImage(teleport_potion)

        # antidote
        for file in listdir('data/antidote/idle'):
            antidote = Image.open('data/antidote/idle/' + file)
            antidote = antidote.resize((taille_element_jeu, taille_element_jeu),
                                       resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['antidote']['antidote_idle_' + y[0]] = ImageTk.PhotoImage(antidote)

        # Mana_potion
        for file in listdir('data/Mana/idle'):
            Mana = Image.open('data/Mana/idle/' + file)
            Mana = Mana.resize((taille_element_jeu, taille_element_jeu),
                               resample=Image.NEAREST)
            x = file.split('_')
            y = x[3].split('.')
            self.data['Mana_potion']['Mana_potion_idle_' + y[0]] = ImageTk.PhotoImage(Mana)

        # chainmail
        for file in listdir('data/chainmail/idle'):
            chainmail = Image.open('data/chainmail/idle/' + file)
            chainmail = chainmail.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['chainmail']['chainmail_idle_' + y[0]] = ImageTk.PhotoImage(chainmail)

        # portoloin
        for file in listdir('data/portoloin/idle'):
            portoloin = Image.open('data/portoloin/idle/' + file)
            portoloin = portoloin.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
            x = file.split('_')
            y = x[2].split('.')
            self.data['portoloin']['portoloin_idle_' + y[0]] = ImageTk.PhotoImage(portoloin)

        # Gobelin
        for file in listdir('data/Gobelin/idle'):
            if file != 'desktop.ini':
                Gobelin = Image.open('data/Gobelin/idle/' + file)
                Gobelin = Gobelin.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Gobelin']['Gobelin_idle_' + y[0]] = ImageTk.PhotoImage(Gobelin)
        # Diablotin
        for file in listdir('data/Diablotin/idle'):
            if file != 'desktop.ini':
                Diablotin = Image.open('data/Diablotin/idle/' + file)
                Diablotin = Diablotin.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Diablotin']['Diablotin_idle_' + y[0]] = ImageTk.PhotoImage(Diablotin)
        # Squelette
        for file in listdir('data/Squelette/idle'):
            if file != 'desktop.ini':
                Squelette = Image.open('data/Squelette/idle/' + file)
                Squelette = Squelette.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Squelette']['Squelette_idle_' + y[0]] = ImageTk.PhotoImage(Squelette)

        # Ork
        for file in listdir('data/Ork/idle'):
            if file != 'desktop.ini':
                Ork = Image.open('data/Ork/idle/' + file)
                Ork = Ork.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Ork']['Ork_idle_' + y[0]] = ImageTk.PhotoImage(Ork)

        # Blob
        for file in listdir('data/Blob/idle'):
            if file != 'desktop.ini':
                Blob = Image.open('data/Blob/idle/' + file)
                Blob = Blob.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Blob']['Blob_idle_' + y[0]] = ImageTk.PhotoImage(Blob)

        # Dragon
        for file in listdir('data/Dragon/idle'):
            if file != 'desktop.ini':
                Dragon = Image.open('data/Dragon/idle/' + file)
                Dragon = Dragon.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Dragon']['Dragon_idle_' + y[0]] = ImageTk.PhotoImage(Dragon)

        # Ghost
        for file in listdir('data/Ghost/idle'):
            if file != 'desktop.ini':
                Ghost = Image.open('data/Ghost/idle/' + file)
                Ghost = Ghost.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Ghost']['Ghost_idle_' + y[0]] = ImageTk.PhotoImage(Ghost)
        # Muddy
        for file in listdir('data/Muddy/idle'):
            if file != 'desktop.ini':
                Muddy = Image.open('data/Muddy/idle/' + file)
                Muddy = Muddy.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Muddy']['Muddy_idle_' + y[0]] = ImageTk.PhotoImage(Muddy)

        # Hero
        for file in listdir('data/Hero/idle'):
            if file != 'desktop.ini':
                Hero = Image.open('data/Hero/idle/' + file)
                Hero = Hero.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
                x = file.split('_')
                y = x[2].split('.')
                self.data['Hero']['Hero_idle_' + y[0]] = ImageTk.PhotoImage(Hero)

        # tout le hud
        portrait = Image.open('data/hero_face.png')
        portrait = portrait.resize((int(self.width * 120 / 1920), int(self.height * 210 / 1080)),
                                   resample=Image.NEAREST)
        self.data['hud']['portrait'] = ImageTk.PhotoImage(portrait)

        croix = Image.open('data/croix.png')
        croix = croix.resize((20, 20), resample=Image.NEAREST)
        self.data['hud']['croix'] = ImageTk.PhotoImage(croix)

        heart_full = Image.open('data/heart/heart_full.png')
        heart_full = heart_full.resize((int(0.03 * self.height), int(0.03 * self.height)), resample=Image.NEAREST)
        self.data['hud']['heart_full'] = ImageTk.PhotoImage(heart_full)

        heart_empty = Image.open('data/heart/heart_empty.png')
        heart_empty = heart_empty.resize((int(0.03 * self.height), int(0.03 * self.height)), resample=Image.NEAREST)
        self.data['hud']['heart_empty'] = ImageTk.PhotoImage(heart_empty)

        inventory_slot = Image.open('data/inventory_slot/inventory_slot.png')
        inventory_slot = inventory_slot.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
        self.data['hud']['inventory_slot'] = ImageTk.PhotoImage(inventory_slot)

        gold_pile = Image.open('data/gold_pile/gold_pile.png')
        gold_pile = gold_pile.resize((int(0.03 * self.height), int(0.03 * self.height)), resample=Image.NEAREST)
        self.data['hud']['gold_pile'] = ImageTk.PhotoImage(gold_pile)

        Poison = Image.open('data/afflictions/poison/poison_idle_0.png')
        Poison = Poison.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
        self.data['hud']['poison'] = ImageTk.PhotoImage(Poison)

        invisibility = Image.open('data/afflictions/invisibility/invisibility_idle_0.png')
        invisibility = invisibility.resize((taille_element_jeu, taille_element_jeu), resample=Image.NEAREST)
        self.data['hud']['invisibility'] = ImageTk.PhotoImage(invisibility)

        message_slot = Image.open('data/message_slot/message_slot.png')
        message_slot = message_slot.resize((int(0.35 * self.width), int(0.23 * self.height)), resample=Image.NEAREST)
        self.data['hud']['message_slot'] = ImageTk.PhotoImage(message_slot)

        # Contour
        Pixel_art_hero = Image.open('data/Pixel_art_hero/Pixel_art_hero.png')
        Pixel_art_hero = Pixel_art_hero.resize(
            (int((self.width - taille_element_jeu * 20) / 2), int((self.width - taille_element_jeu * 20) / 2)),
            resample=Image.NEAREST)
        self.data['hud']['Pixel_art_hero'] = ImageTk.PhotoImage(Pixel_art_hero)

        Tutoriel = Image.open('data/tuto/tuto.png')
        Tutoriel = Tutoriel.resize((int((self.width - taille_element_jeu * 20) / 2),
                                    int((self.width - taille_element_jeu * 20) / 2)), resample=Image.NEAREST)
        self.data['hud']['Tutoriel'] = ImageTk.PhotoImage(Tutoriel)

    def generateBackground(self):
        """Génère une liste d'image unique pour la méthode PartieJeu afin qu'il ne se modifie pas quand je régènère
        l'interface au prochain tour de jeu """
        self.background.clear()
        for j in range(20):
            for i in range(20):
                if theGame().floor.get(Coord(i, j)) == Map.empty:
                    self.background.append(self.data['walls'][random.randint(0, 11)])
                elif isinstance(theGame().floor.get(Coord(i, j)), Stairs):
                    self.background.append(self.data['stairs'][0])
                else:
                    self.background.append(self.data['floors'][random.randint(0, 7 * 4)])

    def partieJeu(self):
        """Cette méthode s'occupe de générer la map et les élèments sur l'interface graphique"""
        taille_jeu = int((32 / 1920) * self.width) * 20
        self.jeu.delete("all")
        self.jeu.create_image(-5, 0,
                              image=self.data['hud']['Pixel_art_hero'], anchor='nw')
        self.jeu.create_image(taille_jeu + int((self.width - taille_jeu) / 2),
                              (taille_jeu - (self.width - taille_jeu) // 2) // 2, image=self.data['hud']['Tutoriel'],
                              anchor='nw')
        for key, item in theGame().floor._elem.items():
            key.update(1)
        for i in range(20):
            for j in range(20):
                self.jeu.create_image(
                    int((self.width - taille_jeu) / 2) + int((32 / 1920) * self.width) * i,
                    int((32 / 1920) * self.width) * j, image=self.background[i + j * 20],
                    anchor='nw')
                if theGame().floor.get(Coord(i, j)) != Map.ground and theGame().floor.get(
                        Coord(i, j)) != Map.empty and not isinstance(theGame().floor.get(Coord(i, j)), Stairs):
                    if not isinstance(theGame().floor.get(Coord(i, j)), Creature) or isinstance(
                            theGame().floor.get(Coord(i, j)), Creature) and not theGame().floor.get(
                        Coord(i, j)).invisible:
                        self.jeu.create_image(
                            int((self.width - taille_jeu) / 2) + int((32 / 1920) * self.width) * i,
                            int((32 / 1920) * self.width) * j,
                            image=theGame().floor.get(Coord(i, j)).current_texture, anchor='nw')
        self.jeu.pack(side=TOP)

    def partieHud(self):
        """Cette méthode s'occupe de générer l'interface qui montre des informations comme la vie du héro ou son
        inventaire ainsi que d'afficher les messages du shell dans la fenêtre de jeu"""
        self.hud.delete('all')
        # portrait : int(self.width*120/1920),int(self.height*210/1080)
        taille_element_jeu = int((32 / 1920) * self.width)
        tailleJeu = int((32 / 1920) * self.width) * 20

        self.hud.create_image(int(self.width * 25 / 1920),
                              (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) - int(
                                  self.height * 67.5 / 1080) + 5, image=self.data['hud']['portrait'], anchor='nw')

        self.hud.create_rectangle(int(self.width * 25 / 1920),
                                  (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080),
                                  int(self.width * 25 / 1920) + int(self.width * 120 / 1920),
                                  (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                                      self.height * 210 / 1080) - int(self.height * 67.5 / 1080) + 5 + 4, width=5)

        self.hud.create_text((self.width * 1.2 / 12, (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080)),
                             text=theGame().hero.name,
                             font=("Algerian", int(0.012 * self.width)), fill='blue', anchor='nw')

        self.hud.create_text((width * 1.2 / 12, (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + (int(
            self.height * 210 / 1080) - int(self.height * 67.5 / 1080)) // 2 + 5),
                             text='Level : ' + str(theGame().hero.level),
                             font=("Algerian", int(0.012 * self.width)), fill='red', anchor='w')

        self.hud.create_text((width * 1.2 / 12, (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
            self.height * 210 / 1080) - int(self.height * 67.5 / 1080) + 5 + 4),
                             text='Xp : ' + str(theGame().hero.xp) + '/' + str(theGame().hero.level * 10),
                             font=("Algerian", int(0.012 * self.width)), fill='green', anchor='sw')

        self.hud.create_image((self.width * 1.2 / 12 + 150 + 2.5 * (taille_element_jeu + 3) + 20,
                               (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                                   self.height * 210 / 1080) - int(self.height * 67.5 / 1080) + 5 + 4),
                              image=self.data['Mana_potion']['Mana_potion_idle_0'], anchor='s')

        self.hud.create_text(
            (self.width * 1.2 / 12 + 150 + 2.5 * (taille_element_jeu + 3) + 20 + 2.1 * taille_element_jeu,
             (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                 self.height * 210 / 1080) - int(self.height * 67.5 / 1080) + 5 + 4),
            text=': ' + str(theGame().hero.mana) + ' / ' + str(theGame().hero.manamax),
            font=("Algerian", int(0.01 * self.width)), fill='black', anchor='s')

        for i in range(theGame().hero.hpmax):
            if i < 25:
                a = 0.16 * self.height
                b = 0.1 * self.width + i * int(0.03 * self.height)
            else:
                a = 0.16 * self.height + int(0.03 * self.height) * (i // 25)
                b = 0.1 * self.width + (i - 25 * (i // 25)) * int(0.03 * self.height)
            if i > theGame().hero.hp - 1:
                self.hud.create_image(b, (self.height - tailleJeu) // 4 + a, image=self.data['hud']['heart_empty'],
                                      anchor='nw')
            else:
                self.hud.create_image(b, (self.height - tailleJeu) // 4 + a, image=self.data['hud']['heart_full'],
                                      anchor='nw')

        self.hud.create_text(
            (self.width * 1.2 / 12 + 150 + 10 * (taille_element_jeu + 3) // 2 + 20,
             (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080)),
            text='Inventaire :', font=("Algerian", int(0.014 * self.width)), fill='purple',
            anchor='n')

        for i in range(10):
            self.hud.create_image(
                self.width * 1.2 / 12 + 150 + i * (taille_element_jeu + 3) + 20,
                (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                    0.014 * self.width) + 8 * self.height // 1080,
                image=self.data['hud']['inventory_slot'],
                anchor='nw')
            liste_input_inventaire = ['à', '&', 'é', '"', "'", '(', '-', 'è', '_', 'ç']
            if i != 0:
                self.hud.create_text(
                    (self.width * 1.2 / 12 + 150 + (i - 1) * (taille_element_jeu + 3) + 20 + 0.5 * taille_element_jeu,
                     (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                         0.014 * self.width) + taille_element_jeu + 8 * self.height // 1080),
                    text=f'{liste_input_inventaire[i]}',
                    font=("Arial", int(0.75 * taille_element_jeu)),
                    fill='blue', anchor='n')
            else:
                self.hud.create_text(
                    (self.width * 1.2 / 12 + 150 + 9 * (taille_element_jeu + 3) + 20 + 0.5 * taille_element_jeu,
                     (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                         0.014 * self.width) + taille_element_jeu + 8 * self.height // 1080),
                    text=f'{liste_input_inventaire[i]}',
                    font=("Arial", int(0.70 * taille_element_jeu)),
                    fill='blue', anchor='n')

        for i in range(len(theGame().hero._inventory)):
            self.hud.create_image(self.width * 1.2 / 12 + 150 + i * (taille_element_jeu + 3) + 20,
                                  (self.height - tailleJeu) // 4 + int(self.height * 10 / 1080) + int(
                                      0.014 * self.width) + 8 * self.height // 1080,
                                  image=theGame().hero._inventory[i].textures[0], anchor='nw')

        self.hud.create_image(self.width * 1.2 / 12 + 150 + 11 * (taille_element_jeu + 3) + 20,
                              (self.height - tailleJeu) // 4 + 2.5 * taille_element_jeu + 10,
                              image=self.data['hud']['gold_pile'], anchor='nw')

        self.hud.create_text(
            (self.width * 1.2 / 12 + 150 + 11 * (taille_element_jeu + 3) + 20 + taille_element_jeu,
             (self.height - tailleJeu) // 4 + 2.5 * taille_element_jeu + 10),
            text='  = ' + str(theGame().hero.gold), font=("Algerian", int(0.014 * self.width)),
            fill='blue', anchor='nw')

        self.hud.create_text(
            (self.width * 1.2 / 12 + 150 + 11 * (taille_element_jeu + 3) + 20,
             (self.height - tailleJeu) // 4 + 1.5 * taille_element_jeu + 5),
            text='Armure : ',
            font=("Algerian", int(0.014 * self.width)),
            fill='dark blue', anchor='nw')

        self.hud.create_image(self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20,
                              (self.height - tailleJeu) // 4 + 1.5 * taille_element_jeu + 5,
                              image=self.data['hud']['inventory_slot'], anchor='nw')
        if theGame().hero._armure is not None:
            self.hud.create_image(self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20,
                                  (self.height - tailleJeu) // 4 + 1.5 * taille_element_jeu + 5,
                                  image=theGame().hero._armure.textures[0], anchor='nw')
            self.hud.create_text(
                self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20 + taille_element_jeu,
                (self.height - tailleJeu) // 4 + 1.5 * taille_element_jeu + 5,
                text='(' + str(theGame().hero._armure.durability) + '/' + str(
                    theGame().hero._armure.maxdurability) + ')', font=("Algerian", int(0.010 * self.width)),
                fill='dark blue', anchor='nw')

        self.hud.create_text(
            (self.width * 1.2 / 12 + 150 + 11 * (taille_element_jeu + 3) + 20,
             (self.height - tailleJeu) // 4 + 0.5 * taille_element_jeu),
            text='Arme : ',
            font=("Algerian", int(0.014 * self.width)),
            fill='dark blue', anchor='nw')

        self.hud.create_image(self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20,
                              (self.height - tailleJeu) // 4 + 0.5 * taille_element_jeu,
                              image=self.data['hud']['inventory_slot'], anchor='nw')

        if theGame().hero._arme is not None:
            self.hud.create_image(self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20,
                                  (self.height - tailleJeu) // 4 + 0.5 * taille_element_jeu,
                                  image=theGame().hero._arme.textures[0], anchor='nw')
            self.hud.create_text(
                self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20 + taille_element_jeu,
                (self.height - tailleJeu) // 4 + 0.5 * taille_element_jeu,
                text='(' + str(theGame().hero._arme.durability) + '/' + str(
                    theGame().hero._arme.maxdurability) + ')', font=("Algerian", int(0.010 * self.width)),
                fill='dark blue', anchor='nw')

        self.hud.create_image((self.width + self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20) // 2,
                              (self.height - tailleJeu) // 2,
                              image=self.data['hud']['message_slot'],
                              anchor='center')
        if theGame()._message != []:
            a = theGame().readMessages()
            if len(a.split('\n')) <= 9:
                self.hud.create_text(
                    (self.width + self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20) // 2.25,
                    (self.height - tailleJeu) // 2, text=a, fill='black',
                    font=("Algerian", int(0.007 * self.width)), anchor='w')
            else:
                b = ''
                for i in a.split('\n')[0:8]:
                    b += i
                    b += '\n'
                c = ''
                for i in a.split('\n')[8:]:
                    c += i
                    c += '\n'
                self.hud.create_text(
                    (self.width + self.width * 1.2 / 12 + 150 + 15.5 * (taille_element_jeu + 3) + 20) // 2.25,
                    (self.height - tailleJeu) // 2, text=b, fill='black',
                    font=("Algerian", int(0.007 * self.width)), anchor='center')
                self.hud.create_text(
                    (self.width + self.width * 1.2 / 12 + 150 + 15.5 * (
                            taille_element_jeu + 3) + 20) // 2.25 + 150 + taille_element_jeu,
                    (self.height - tailleJeu) // 2, text=c, fill='black',
                    font=("Algerian", int(0.007 * self.width)), anchor='center')

        if theGame().hero.poison > 0:
            self.hud.create_image(self.width * 1.2 / 12 + 150 + 11 * (taille_element_jeu + 3) + 20,
                                  (self.height - tailleJeu) // 4 + 4 * taille_element_jeu,
                                  image=self.data['hud']['poison'], anchor='nw')
            self.hud.create_text(
                (self.width * 1.2 / 12 + 150 + 11 * (taille_element_jeu + 3) + 20 + taille_element_jeu,
                 (self.height - tailleJeu) // 4 + 4 * taille_element_jeu),
                text=': ' + str(theGame().hero.poison), font=("Algerian", int(0.009 * self.width)),
                anchor='nw')
        if theGame().hero.invisibility > 0:
            self.hud.create_image(self.width * 1.2 / 12 + 150 + 14 * (taille_element_jeu + 3) + 20,
                                  (self.height - tailleJeu) // 4 + 4 * taille_element_jeu,
                                  image=self.data['hud']['invisibility'], anchor='nw')
            self.hud.create_text(
                (self.width * 1.2 / 12 + 150 + 14 * (taille_element_jeu + 3) + 20 + taille_element_jeu,
                 (self.height - tailleJeu) // 4 + 4 * taille_element_jeu),
                text=': ' + str(theGame().hero.invisibility), font=("Algerian", int(0.009 * self.width)),
                anchor='nw')

        self.hud.pack(side=BOTTOM)


def theGame(game=Game(InterfaceJeu(width, height, fenetre))):
    return game


def heal(Creature, amount):
    """Fonction qui ajoute amount pv à la créature qui appelle cette fonction via une potion ou autre..."""
    if Creature.hp == Creature.hpmax:
        theGame().addMessage("You can't heal yourself when you're not injured")
        return False
    elif Creature.hp + amount > Creature.hpmax:
        Creature.hp = Creature.hpmax
    else:
        Creature.hp += amount
    return True


def ManaRecovery(Hero, amount):
    """Fonction qui ajoute amount mana à la créature qui appelle cette fonction via une potion ou autre..."""
    if Hero.mana == Hero.manamax:
        theGame().addMessage("You can't recover mana when you're full !")
        return False
    elif Hero.mana + amount > Hero.manamax:
        Hero.mana = Hero.manamax
    else:
        Hero.mana += amount
    return True


def curePoison(Creature):
    if Creature.poison > 0:
        Creature.poison = 0
        Creature.poison_delay = 0
        theGame().addMessage("Congratulation, poison has been removed !")
        return True
    else:
        theGame().addMessage("You can't cure poison if you're not poisonned !")
        return False


def teleport(Creature, unique):
    """Fonction qui téléporte la créature qui appelle cette fonction via une potion, une baguette ou autre..."""
    final = random.choice(theGame().floor._rooms).randEmptyCoord(theGame().floor)
    orig = theGame().floor.pos(Creature)
    delta = final - orig
    theGame().floor.move(Creature, delta)
    return unique


def onKeyRelease(event):
    """Fonction qui gère une partie des inputs"""
    moved = False
    c = event.char
    print(c)
    if c in Game._actions:
        Game._actions[c](theGame().hero)
    if c in [' ', ',', ';',':']:
        moved = True
    if c in list_input:
        theGame().useItem(list_input.index(c))
    if moved:
        theGame().hero.poisonRecovery()
        theGame().hero.invisibilityDecrease()
        print()
        print(theGame().floor)
        print(theGame().hero.description())
        theGame().floor.moveAllMonsters()
        theGame().interface.partieHud()


def launchGame():
    can.pack_forget()
    theGame().play()


"""Code qui s'exécute"""

fenetre.attributes('-fullscreen', True)
fenetre.geometry(str(width) + 'x' + str(height))

can = Canvas(fenetre, width=width, height=height, bg='light blue')

wallpaper = Image.open('data/wallpaper.gif')
wallpaper = wallpaper.resize((width, height), resample=Image.NEAREST)
wallpaper = ImageTk.PhotoImage(wallpaper)
can.create_image((width // 2, height // 2), image=wallpaper)

can.create_text((width // 2, height // 4), text='Rogue :', font=('Algerian', width // 40),
                fill='black', anchor='center')
can.create_text((width // 2, height // 4 + width // 40), text='The Spiral Of The Abyss', font=('Algerian', width // 40),
                fill='black', anchor='center')

start = Button(fenetre, text='play', padx=5 * width // 1920, pady=10 * height // 1080, background='light grey',
               font=('Algerian', width // 40), command=launchGame)

can.create_window((width // 2, 1.5 * height // 2), window=start)

can.pack()

fenetre.mainloop()
