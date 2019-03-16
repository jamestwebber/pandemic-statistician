# coding=utf-8

# file of constants to keep things readable

from collections import OrderedDict, namedtuple


CITIES = OrderedDict(
    [
        ("London", "blue"),
        ("New York", "blue"),
        ("Washington", "blue"),
        ("Jacksonville", "yellow"),
        ("Lagos", "yellow"),
        ("São Paulo", "yellow"),
        ("Cairo", "black"),
        ("Istanbul", "black"),
        ("Tripoli", "black"),
    ]
)
CARDS_PER_CITY = 3

Character = namedtuple("Character", ("first_name", "middle_name", "icon"))

CHARACTERS = OrderedDict(
    [
        ("Administrator", Character("Shinji", "Avengeant", "glyphicon-pencil")),
        ("Instructor", Character("Isabelle", "Ivanka X", "glyphicon-education")),
        ("Radio Operator", Character("Ronald", "O'Brian", "glyphicon-headphones")),
        ("Laborer", Character("Lazarus", '"Larry" III³', "glyphicon-wrench")),
        ("Farmer", Character("Furtle", "", "glyphicon-cutlery")),
    ]
)

INFECTION_RATES = [2, 2, 2, 3, 3, 4, 4, 5, 9]  # infection rates per epidemic
# note: -1 is game setup, infect 9 cities

INFECTION_GLYPHS = {
    -1: "glyphicon glyphicon-remove-sign",
    0: "glyphicon glyphicon-ok-sign",
    1: "glyphicon glyphicon-exclamation-sign",
    2: "glyphicon glyphicon-info-sign",
}

BASE_DECK_SIZE = 36
EPIDEMICS = 5  # number of epidemics in the deck
NUM_PLAYERS = 4  # four players, of course
INITIAL_HAND_SIZE = {
    2: 4,
    3: 3,
    4: 2,
}  # number of hands in initial hands, according to NUM_PLAYERS
DRAW = 2  # draw two cards at a time
