# coding=utf-8

# file of constants. Many need to be updated per-game because I'm too lazy to code them

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    color: str
    player_cards: int
    infection_cards: int


cities = [
    City("Atlanta", "blue", 1, 0),  # due to lockdown
    City("Chicago", "blue", 2, 2),
    # City("Johannesburg", "blue", 2, 2),
    City("London", "blue", 4, 3),
    City("New York", "blue", 4, 3),
    City("Washington", "blue", 4, 3),
    City("San Francisco", "blue", 2, 2),
    City("Denver", "blue", 2, 2),
    City("Paris", "blue", 2, 2),
    City("Frankfurt", "blue", 2, 2),
    City("St. Petersburg", "blue", 1, 1),
    City("Bogotá", "yellow", 2, 2),
    City("Buenos Aires", "yellow", 2, 2),
    # City("Dar es Salaam", "yellow", 2, 2),
    City("Jacksonville", "yellow", 4, 3),
    City("Khartoum", "yellow", 1, 1),
    City("Kinshasa", "yellow", 1, 1),
    City("Lagos", "yellow", 4, 3),
    City("Lima", "yellow", 1, 1),
    City("Los Angeles", "yellow", 1, 1),
    # City("Mexico City", "yellow", 1, 1),
    City("São Paulo", "yellow", 4, 3),
    City("Santiago", "yellow", 1, 1),
    # City("Antananarivo", "black", 2, 2),
    City("Baghdad", "black", 2, 2),
    City("Cairo", "black", 4, 3),
    # City("Delhi", "black", 1, 1),
    City("Istanbul", "black", 4, 3),
    City("Kolkata", "black", 1, 1),
    City("Moscow", "black", 1, 0),  # due to lockdown
    # City("New Mumbai", "black", 2, 2),
    # City("Riyadh", "black", 2, 2),
    City("Tehran", "black", 1, 1),
    City("Tripoli", "black", 4, 3),
    # the hollow men
    City("Hollow Men Gather", "white", 0, 4),
]

# copy for convenience
hollow_men = City("Hollow Men Gather", "white", 0, 4)

# cards exiled to box six, needs to be updated per game
player_cards_in_box_six = Counter()
infection_cards_in_box_six = Counter(
    {
        City("Istanbul", "black", 4, 3): 1,
        City("Jacksonville", "yellow", 4, 3): 1,
        City("Kinshasa", "yellow", 1, 1): 1,
        City("Lima", "yellow", 1, 1): 1,
        City("Los Angeles", "yellow", 1, 1): 1,
        City("San Francisco", "blue", 2, 2): 1,
        City("Washington", "blue", 4, 3): 2,
    }
)

possible_lockdown = False  # TODO: Check after next game

max_inf = max(city.infection_cards for city in cities if city != hollow_men)


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
    Character(
        "Sanitation Officer",
        "Sandy",
        "McSandpersonface",
        "Doña Mago",
        "glyphicon-trash",
    ),
    Character("Captain", "Swash", "B. Uckler", "Doña Mago", "glyphicon-globe"),
]


infection_rates = [2, 2, 2, 3, 3, 4, 4, 5, 9]  # infection rates per epidemic
# note: -1 is game setup, infect 9 cities

# color codes for CSS styles
color_codes = {"blue": 0, "yellow": 1, "black": 2, "red": 3, "white": 4}

# number of non-player cards in the deck (varies per game, needs to be kept up-to-date)
extra_cards = 15  # TODO: Check after next game

# number of epidemics is based on the number of city cards in starting deck
epidemics = {36: 5, 44: 6, 51: 7, 57: 8, 62: 9, -1: 10}
num_players = 4  # four players, of course

# number of hands in initial hands, according to NUM_PLAYERS
initial_hand_size = {2: 4, 3: 3, 4: 2}
draw = 2  # draw two cards at a time
monitor = 4  # monitor discards four cards
