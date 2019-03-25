import functools
import math
import operator as op
from collections import defaultdict, Counter

from flask import Blueprint, flash

from pandemic import constants as c
from pandemic.models import Turn


main = Blueprint("main", __name__)


def resolve_epidemic(stack, epidemic_city, max_stack, inc_stack):
    if stack[max_stack][epidemic_city] < 1:
        flash("WARNING: this epidemic shouldn't be possible, check records!")
    else:
        stack[max_stack][epidemic_city] -= 1
        stack[0][epidemic_city] += 1

    if inc_stack:
        for s in range(max_stack, -1, -1):
            stack[s + 1] = stack[s]
        stack[0] = Counter()


def ncr(n, r):
    r = min(r, n - r)
    if r < 0:
        return 0.0

    numer = functools.reduce(op.mul, range(n, n - r, -1), 1)
    denom = math.factorial(r)

    return numer / denom


def hg_pmf(k, M, n, N):
    return ncr(n, k) * ncr(M - n, N - k) / ncr(M, N)


def get_game_state(game, draw_phase=True):
    turns = (
        Turn.query.filter_by(game_id=game.id)
        .filter(Turn.turn_num <= game.turn_num)
        .order_by(Turn.turn_num)
        .all()
    )

    # deck size after dealing the initial hands
    post_setup_deck_size = (
        c.BASE_DECK_SIZE
        + c.EPIDEMICS
        + game.funding_rate
        + game.extra_cards
        - c.NUM_PLAYERS * c.INITIAL_HAND_SIZE[c.NUM_PLAYERS]
    )
    # number of post-setup cards drawn so far
    if game.turn_num == -1:
        ps_cards_drawn = 0
    else:
        ps_cards_drawn = (len(turns) - 1 - draw_phase) * c.DRAW
    # how many cards are left
    deck_size = post_setup_deck_size - ps_cards_drawn

    stack = defaultdict(Counter)
    for city_name in c.CITIES:
        stack[1][city_name] = c.CARDS_PER_CITY

    epidemics = 0
    for i, turn in enumerate(turns):
        max_s = max(s for s in stack if sum(stack[s].values()) > 0)
        inc_stack = i < len(turns) - 1 or (not draw_phase)

        if turn.epidemic:
            epidemics += 1
            resolve_epidemic(stack, turn.epidemic[0].name, max_s, inc_stack)

            if len(turn.epidemic) == 2:
                epidemics += 1
                resolve_epidemic(stack, turn.epidemic[1].name, max_s, inc_stack)

        if turn.resilient_pop:
            # TODO: could be two cards
            stack[0][turn.resilient_pop.name] -= 1
            stack[-1][turn.resilient_pop.name] += 1

        infected_cities = sorted(
            turn.infections,
            key=lambda city: min(i for i in stack if stack[i][city.name] > 0),
        )

        for city in infected_cities:
            if stack[1][city.name] < 1:
                flash(
                    "WARNING: looks like a city was infected too early, check records!"
                )
            else:
                stack[1][city.name] -= 1
                stack[0][city.name] += 1

            if sum(stack[1].values()) == 0:
                for s in range(2, max_s + 1):
                    stack[s - 1] = stack[s]
                stack[max_s] = Counter()

    stack = defaultdict(
        list, {i: stack[i] for i in stack if sum(stack[i].values()) > 0}
    )
    max_s = max(stack)

    epidemic_stacks = Counter((i % c.EPIDEMICS) for i in range(post_setup_deck_size))
    epidemic_blocks = list(epidemic_stacks.elements())

    i_block = epidemic_blocks[ps_cards_drawn]
    j_block = epidemic_blocks[ps_cards_drawn + 1]

    for i in epidemic_blocks[:ps_cards_drawn]:
        epidemic_stacks[i] -= 1

    if game.turn_num > -1:
        if i_block < epidemics:
            if j_block < epidemics:
                # this epidemic has already been drawn
                epidemic_risk = 0.0
            else:
                # the second card could be one
                epidemic_risk = 1.0 / epidemic_stacks[j_block]
        elif i_block == j_block:
            # both are same block, and it hasn't been drawn yet
            epidemic_risk = 2.0 / epidemic_stacks[i_block]
        else:
            # first card is definitely an epidemic, second one might be!
            assert epidemic_stacks[i_block] == 1
            epidemic_risk = 1.0 + 1.0 / epidemic_stacks[j_block]
    else:
        epidemic_risk = 0.0

    infection_rate = c.INFECTION_RATES[epidemics]

    city_probs = defaultdict(list)

    for i in range(1, max_s + 1):
        n = sum(stack[i].values())
        if n <= infection_rate:
            for city_name in stack[i]:
                city_probs[city_name].append(1.0)
        elif infection_rate > 0:
            for city_name in stack[i]:
                city_probs[city_name].extend(
                    (i, hg_pmf(j, n, stack[i][city_name], infection_rate))
                    for j in range(1, stack[i][city_name] + 1)
                )

            infection_rate -= n
        else:
            for city_name in stack[i]:
                city_probs[city_name].append((i, 0.0))

    for i in (-1, 0):
        for city_name in stack[i]:
            city_probs[city_name].append((i, 0.0))

    epi_probs = defaultdict(
        float,
        {
            city_name: stack[max_s][city_name] / sum(stack[max_s].values())
            for city_name in stack[max_s]
        },
    )

    r_stack = defaultdict(list)
    for i in sorted(stack):
        for city_name in stack[i]:
            r_stack[city_name].extend((i,) * stack[i][city_name])

    city_data = [
        dict(
            name=city_name,
            color=city_color,
            stack=r_stack[city_name],
            inf_risk=city_probs[city_name],
            epi_risk=epi_probs[city_name],
        )
        for city_name, city_color in c.CITIES.items()
    ]

    return {
        "game_id": game.id,
        "turn_num": game.turn_num,
        "turns": turns,
        "deck_size": deck_size,
        "epi_risk": epidemic_risk,
        "epidemics": epidemics,
        "city_data": city_data,
        "cards_per_city": c.CARDS_PER_CITY,
    }

# down here to avoid circular imports
from ..main import views

