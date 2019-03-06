# coding=utf-8

# file of constants to keep things readable

from collections import OrderedDict, namedtuple


CITIES = OrderedDict(
    [
        ("Atlanta", "blue"),
        ("Chicago", "blue"),
        ("Essen", "blue"),
        ("London", "blue"),
        ("Madrid", "blue"),
        ("Milan", "blue"),
        ("Montreal", "blue"),
        ("New York", "blue"),
        ("Paris", "blue"),
        ("San Francisco", "blue"),
        ("St. Petersburg", "blue"),
        ("Washington", "blue"),
        ("Bogotá", "yellow"),
        ("Buenos Aires", "yellow"),
        ("Johannesburg", "yellow"),
        ("Khartoum", "yellow"),
        ("Kinshasa", "yellow"),
        ("Lagos", "yellow"),
        ("Lima", "yellow"),
        ("Los Angeles", "yellow"),
        ("Mexico City", "yellow"),
        ("Miami", "yellow"),
        ("Santiago", "yellow"),
        ("São Paulo", "yellow"),
        ("Algiers", "black"),
        ("Baghdad", "black"),
        ("Cairo", "black"),
        ("Chennai", "black"),
        ("Delhi", "black"),
        ("Istanbul", "black"),
        ("Karachi", "black"),
        ("Kolkata", "black"),
        ("Moscow", "black"),
        ("Mumbai", "black"),
        ("Riyadh", "black"),
        ("Tehran", "black"),
        ("Bangkok", "red"),
        ("Beijing", "red"),
        ("Ho Chi Minh City", "red"),
        ("Hong Kong", "red"),
        ("Jakarta", "red"),
        ("Manila", "red"),
        ("Osaka", "red"),
        ("Seoul", "red"),
        ("Shanghai", "red"),
        ("Sydney", "red"),
        ("Taipei", "red"),
        ("Tokyo", "red"),
    ]
)

Character = namedtuple("Character", ("first_name", "middle_name", "icon"))

CHARACTERS = OrderedDict(
    [
        ("TRAITOR", Character("Shinji", '"Judas"', "glyphicon-fire")),
        ("Researcher", Character("Rachel", "R", "glyphicon-search")),
        ("Quarantine Specialist", Character("Quincy", "Q", "glyphicon-alert")),
        ("Operations Expert", Character("Omar", "Obama", "glyphicon-home")),
        ("Colonel", Character("Carlos", "Camino", "glyphicon-star")),
        ("Generalist", Character("Samantha", "Q", "glyphicon-wrench")),
        ("Medic", Character("", "", "glyphicon-plus-sign")),
        ("Scientist", Character("", "", "glyphicon-education")),
        ("Smith-Soldier", Character("Simón", '"Sparks"', "glyphicon-star-empty")),
        ("Virologist", Character("Victoria", '"Valkyrie"', "glyphicon-certificate")),
        ("Immunologist", Character("Icarus", "I", "glyphicon-ok-circle")),
    ]
)

# months in the year
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

INFECTION_RATES = [2, 2, 2, 3, 3, 4, 4, 9]  # infection rates per epidemic
# note: -1 is game setup, infect 9 cities

EPIDEMICS = 5  # number of epidemics in the deck
NUM_PLAYERS = 4  # four players, of course
INITIAL_HAND_SIZE = {
    2: 4,
    3: 3,
    4: 2,
}  # number of hands in initial hands, according to NUM_PLAYERS
DRAW = 2  # draw two cards at a time
CODA_COLOR = "yellow"  # color of the COdA virus
