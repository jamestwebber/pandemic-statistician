# coding=utf-8

# file of constants to keep things readable

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    color: str
    player_cards: int
    infection_cards: int


cities = [
    City("Atlanta", "blue", 1, 1),
    City("Chicago", "blue", 2, 2),
    City("London", "blue", 4, 3),
    City("New York", "blue", 4, 3),
    City("Washington", "blue", 4, 3),
    City("San Francisco", "blue", 2, 2),
    City("Denver", "blue", 2, 2),
    # City("Bogotá", "yellow", 2, 2),
    City("Buenos Aires", "yellow", 2, 2),
    City("Jacksonville", "yellow", 4, 3),
    City("Lagos", "yellow", 4, 3),
    # City("Lima", "yellow", 1, 1),
    City("São Paulo", "yellow", 4, 3),
    # City("Santiago", "yellow", 1, 1),
    City("Los Angeles", "yellow", 1, 1),
    # City("Mexico City", "yellow", 1, 1),
    City("Cairo", "black", 4, 3),
    City("Istanbul", "black", 4, 3),
    City("Tripoli", "black", 4, 3),
]


max_inf = max(city.infection_cards for city in cities)


@dataclass(frozen=True)
class Character:
    name: str
    first_name: str
    middle_name: str
    haven: str
    icon: str


characters = [
    Character("Administrator", "Shinji", "Avengeant", "Zante's", "glyphicon-pencil"),
    Character("Instructor", "Isabelle", "Ivanka X", "Fresno", "glyphicon-education"),
    Character("Radio Operator", "Ronald", "O'Brian", "4LOKO", "glyphicon-headphones"),
    Character("Laborer", "Lazarus", '"Larry" III³', "Fresno", "glyphicon-wrench"),
    Character("Farmer", "Furtle", '"the turtle"', "Fresno", "glyphicon-cutlery"),
]


infection_rates = [2, 2, 2, 3, 3, 4, 4, 5, 9]  # infection rates per epidemic
# note: -1 is game setup, infect 9 cities

color_codes = {"blue": 0, "yellow": 1, "black": 2, "red": 3}  # for CSS styles

# number of epidemics is based on the number of city cards in starting deck
epidemics = {0: 5, 36: 6, 44: 7, 51: 8, 57: 9, 62: 10}
num_players = 4  # four players, of course

# number of hands in initial hands, according to NUM_PLAYERS
initial_hand_size = {2: 4, 3: 3, 4: 2}
draw = 2  # draw two cards at a time
