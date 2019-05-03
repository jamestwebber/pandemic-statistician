from collections import Counter, defaultdict

from flask import current_app, flash

from pandemic import constants as c
from pandemic.main.risk import epi_infection_risk, infection_risk
from pandemic.models import Turn


def print_stack(stack):
    for i in sorted(stack):
        stack_str = "\n\t".join(f"{city.name} ({stack[i][city]})" for city in stack[i])
        current_app.logger.debug(f"\nstack {i}:\n\t{stack_str}\n\n")


def clean_stack(stack):
    return defaultdict(
        Counter,
        {i: ct for i, ct in ((i, Counter(stack[i].elements())) for i in stack) if ct},
    )


def increment_stack(stack):
    return defaultdict(
        Counter, {(i + (i >= 0) * 1): Counter(stack[i].elements()) for i in stack}
    )


def decrement_stack(stack):
    return defaultdict(
        Counter, {(i - (i > 0) * 1): Counter(stack[i].elements()) for i in stack}
    )


def epidemic(stack, epidemic_city):
    if stack[max(stack)][epidemic_city] < 1:
        flash("WARNING: this epidemic shouldn't be possible, check records!")
    else:
        stack[max(stack)][epidemic_city] -= 1
        stack[0][epidemic_city] += 1

    return clean_stack(stack)


def get_game_state(game, draw_phase=True):
    turns = (
        Turn.query.filter_by(game_id=game.id)
        .filter(Turn.turn_num <= game.turn_num)
        .order_by(Turn.turn_num)
        .all()
    )

    city_cards = sum(city.player_cards for city in c.cities)
    epidemic_cards = c.epidemics[min(k for k in c.epidemics if k > city_cards)]

    # deck size after dealing the initial hands
    post_setup_deck_size = (
        city_cards
        + epidemic_cards
        + game.funding_rate
        + game.extra_cards
        - c.num_players * c.initial_hand_size[c.num_players]
    )

    # number of post-setup cards drawn so far
    if game.turn_num == -1:
        ps_cards_drawn = 0
        epidemics = -1
    else:
        ps_cards_drawn = (len(turns) - 1 - draw_phase) * c.draw
        epidemics = 0

    # how many cards are left
    deck_size = post_setup_deck_size - ps_cards_drawn

    stack = defaultdict(Counter)
    for city in c.cities:
        stack[1][city] = city.infection_cards

    current_app.logger.debug(f"----- TURN {len(turns) - 1} ---------\n\n")

    for i, turn in enumerate(turns):
        stack = clean_stack(stack)
        current_app.logger.debug(f"\non turn {turn.turn_num}:")
        print_stack(stack)

        if turn.epidemic and turn.resilient_pop:
            current_app.logger.debug(
                f"resilient pop:\t{turn.resilient_pop} ({turn.res_pop_count})"
            )
            current_app.logger.debug(f"epidemic: {', '.join(map(str, turn.epidemic))}")

            epidemics += 1
            stack = epidemic(stack, turn.epidemic[0])

            if turn.res_pop_epi == 1:
                stack[0][turn.resilient_pop] -= turn.res_pop_count
                stack[-1][turn.resilient_pop] += turn.res_pop_count

            stack = increment_stack(stack)

            if len(turn.epidemic) == 2:
                epidemics += 1
                stack = epidemic(stack, turn.epidemic[1])

                if turn.res_pop_epi == 2:
                    stack[0][turn.resilient_pop] -= turn.res_pop_count
                    stack[-1][turn.resilient_pop] += turn.res_pop_count

                stack = increment_stack(stack)
        elif turn.resilient_pop:
            current_app.logger.debug(
                f"resilient pop:\t{turn.resilient_pop} ({turn.res_pop_count})"
            )
            stack[0][turn.resilient_pop] -= turn.res_pop_count
            stack[-1][turn.resilient_pop] += turn.res_pop_count

            stack = clean_stack(stack)
        elif turn.epidemic:
            current_app.logger.debug(f"epidemic: {', '.join(map(str, turn.epidemic))}")
            epidemics += 1
            stack = increment_stack(epidemic(stack, turn.epidemic[0]))

            if len(turn.epidemic) == 2:
                epidemics += 1
                stack = increment_stack(epidemic(stack, turn.epidemic[1]))

        if turn.forecasts:
            current_app.logger.debug("forecast")

            new_stack = defaultdict(Counter, {0: stack[0], -1: stack[-1]})
            for cf in turn.forecasts:
                new_stack[cf.stack_order][cf.city] += 1
                j = min(j for j in stack if j > 0 and stack[j][cf.city] > 0)
                stack[j][cf.city] -= 1

            for j in range(1, max(stack) + 1):
                new_stack[j + 8] = stack[j]

            stack = new_stack
            print_stack(stack)

        stack = clean_stack(stack)

        infected_cities = Counter({ci.city: ci.count for ci in turn.infections})

        current_app.logger.debug(
            f"infected:\t{', '.join(city.name for city in infected_cities.elements())}"
        )

        while sum(infected_cities.values()):
            while sum(stack[1].values()) == 0:
                stack = decrement_stack(stack)

            # all of the infected cities currently in top group
            possible_cities = infected_cities & stack[1]

            if not len(possible_cities):
                flash(
                    "WARNING: looks like a city was infected too early, check records!"
                )
                break

            for city in possible_cities.elements():
                infected_cities[city] -= 1
                stack[1][city] -= 1
                stack[0][city] += 1

        while sum(stack[1].values()) == 0:
            stack = decrement_stack(stack)

    stack = clean_stack(stack)

    print_stack(stack)

    epidemic_stacks = Counter((i % epidemic_cards) for i in range(post_setup_deck_size))
    epidemic_blocks = list(epidemic_stacks.elements())

    i_block = epidemic_blocks[ps_cards_drawn]
    j_block = epidemic_blocks[ps_cards_drawn + 1]

    for i in epidemic_blocks[:ps_cards_drawn]:
        epidemic_stacks[i] -= 1

    if game.turn_num > -1:
        if i_block < epidemics:
            if j_block < epidemics:
                assert i_block == j_block
                # this epidemic has already been drawn
                epidemic_risk = 0.0
            else:
                assert epidemic_stacks[i_block] == 1
                # the second card could be one
                epidemic_risk = 1.0 / epidemic_stacks[j_block]
            # next epidemic is in the next block somewhere
            epidemic_in = epidemic_stacks[i_block] + epidemic_stacks[i_block + 1]
        elif i_block == j_block:
            # both are same block, and it hasn't been drawn yet
            epidemic_risk = 2.0 / epidemic_stacks[i_block]
            # next epidemic is in this block
            epidemic_in = epidemic_stacks[i_block]
        else:
            # first card is definitely an epidemic, second one might be!
            assert epidemic_stacks[i_block] == 1
            epidemic_risk = 1.0 + 1.0 / epidemic_stacks[j_block]
            # next epidemic is... right now! and then the next block
            epidemic_in = epidemic_stacks[j_block]
    else:
        epidemic_risk = 0.0
        epidemic_in = epidemic_stacks[0]

    epi_risk = defaultdict(
        float,
        {
            city: stack[max(stack)][city] / sum(stack[max(stack)].values())
            for city in stack[max(stack)]
        },
    )

    inf_risk = infection_risk(stack, c.infection_rates[epidemics], 1.0 - epidemic_risk)

    epi_inf_risk = epi_infection_risk(
        stack, c.infection_rates[epidemics + 1], epidemic_risk, epi_risk
    )

    city_data = [
        dict(
            name=city.name,
            color=city.color,
            inf_risk=inf_risk[city],
            epi_risk=epi_risk[city],
            epi_inf_risk=epi_inf_risk[city],
        )
        for city in c.cities
    ]

    return {
        "game_id": game.id,
        "turn_num": game.turn_num,
        "turns": turns,
        "deck_size": deck_size,
        "epi_risk": epidemic_risk,
        "epi_in": epidemic_in,
        "epidemics": epidemics,
        "city_data": city_data,
        "stack": stack,
    }
