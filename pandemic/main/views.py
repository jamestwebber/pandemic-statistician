import os
import fractions
import functools
import operator as op
import math

from collections import defaultdict, Counter

from flask import g, session, render_template, redirect, url_for, flash

from .. import db
from .. import constants as c
from ..models import Game, City, Turn, PlayerSession, Character

from . import main, forms


@main.app_template_filter("to_percent")
def to_percent(v):
    return (
        "{:.1f}% ({})".format(
            v * 100.0, fractions.Fraction.from_float(v).limit_denominator()
        )
        if v > 0
        else "-"
    )


@main.app_template_filter("danger_level")
def danger_level(v):
    if v > 0.66:
        return "bg-danger"
    elif v > 0.33:
        return "bg-warning"
    else:
        return ""


@main.app_template_filter("to_glyph")
def to_glyph(v):
    return c.INFECTION_GLYPHS.get(v, "glyphicon glyphicon-question-sign")


@main.app_template_filter("color_i")
def color_i(color):
    return {"blue": 0, "yellow": 1, "black": 2, "red": 3}[color]


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


@main.route("/", methods=("GET", "POST"))
def begin():
    form = forms.BeginForm()

    if form.validate_on_submit():
        game = Game(
            funding_rate=form.funding_rate.data,
            extra_cards=form.extra_cards.data,
            turn_num=-1,
        )

        db.session.add(game)
        db.session.commit()

        for player_data in form.players.data:
            player_char = Character.query.filter_by(name=player_data["character"]).one()
            player = PlayerSession(
                player_name=player_data["player_name"],
                turn_num=int(player_data["turn_num"]),
                color_index=int(player_data["color_index"]),
                game_id=game.id,
                char_id=player_char.id,
            )
            db.session.add(player)

        session["game_id"] = game.id

        return redirect(url_for(".draw"))

    return render_template("begin.html", form=form)


@main.route("/draw", methods=("GET", "POST"))
@main.route("/draw/<int:game_id>", methods=("GET", "POST"))
def draw(game_id=None):
    if not (game_id or session.get("game_id", None)):
        flash("No game in progress", "error")
        return redirect(url_for("main.begin"))
    elif game_id:
        session["game_id"] = game_id

    game_id = session["game_id"]
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash("No game with that ID", "error")
        session["game_id"] = None
        return redirect(url_for(".begin"))

    turn = Turn.query.filter_by(game_id=game.id, turn_num=game.turn_num).one_or_none()
    if turn is None:
        turn = Turn(game_id=game.id, turn_num=game.turn_num, resilient_pop=None)
        db.session.add(turn)
    else:
        # this could break the game state otherwise
        turn.epidemic = []
        turn.infections = []

    db.session.commit()

    game_state = get_game_state(game)

    form = forms.DrawForm(game_state, game.characters)

    if form.validate_on_submit():
        if form.epidemic and form.epidemic.data:
            turn.epidemic = [City.query.filter_by(name=form.epidemic.data).first()]
            if "second_epidemic" in form and form.second_epidemic.data:
                turn.epidemic.append(
                    City.query.filter_by(name=form.second_epidemic.data).first()
                )

        db.session.commit()

        if (
            form.resilient_population
            and len(form.resilient_population.data) == c.NUM_PLAYERS
        ):
            return redirect(url_for(".resilientpop"))
        else:
            return redirect(url_for(".infect"))

    return render_template(
        "base_form.html", title="Draw Cards", game_state=game_state, form=form
    )


@main.route("/resilientpop", methods=("GET", "POST"))
def resilientpop():
    if session.get("game_id", None) is None:
        flash("No game in progress", "error")
        return redirect(url_for(".begin"))

    game_id = session["game_id"]
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash("No game with that ID", "error")
        session["game_id"] = None
        return redirect(url_for(".begin"))

    this_turn = Turn.query.filter_by(
        game_id=game.id, turn_num=game.turn_num
    ).one_or_none()
    if this_turn is None:
        flash("Need to draw cards first", "error")
        return redirect(url_for(".draw"))

    game_state = get_game_state(game)

    form = forms.ResilientPopForm(game_state)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        this_turn.resilient_pop = City.query.filter_by(
            name=form.resilient_city.data
        ).first()
        db.session.commit()

        return redirect(url_for(".infect"))

    return render_template(
        "base_form.html",
        title="Select Resilient City",
        game_state=game_state,
        form=form,
    )


@main.route("/infect", methods=("GET", "POST"))
@main.route("/infect/<int:game_id>", methods=("GET", "POST"))
def infect(game_id=None):
    if not (game_id or session.get("game_id", None)):
        flash("No game in progress", "error")
        return redirect(url_for(".begin"))
    elif game_id:
        session["game_id"] = game_id

    game_id = session["game_id"]
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash("No game with that ID", "error")
        session["game_id"] = None
        return redirect(url_for(".begin"))

    this_turn = Turn.query.filter_by(
        game_id=game.id, turn_num=game.turn_num
    ).one_or_none()
    if this_turn is None:
        flash("Not on the infection step right now", "error")
        return redirect(url_for(".draw"))

    game_state = get_game_state(game, False)

    if game.turn_num == -1:
        form = forms.SetupInfectForm(game_state)
    else:
        form = forms.InfectForm(game_state, game.characters)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        if form.cities.data:
            this_turn.infections = City.query.filter(
                City.name.in_(form.cities.data)
            ).all()

        game.turn_num += 1
        db.session.commit()

        return redirect(url_for(".draw"))

    return render_template(
        "base_form.html", title="Infect Cities", game_state=game_state, form=form
    )


@main.route("/history")
def history():
    games = Game.query.all()
    return render_template("summaries.html", games=games)


@main.route("/history/<int:game_id>")
def game_history(game_id):
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash("No game with that ID", "error")
        return redirect(url_for(".history"))

    return render_template(
        "game_history.html", game=game, game_state=get_game_state(game)
    )


@main.route("/replay/<int:game_id>/<turn_num>", methods=("GET", "POST"))
def replay(game_id, turn_num):
    turn_num = int(turn_num)
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash("No game with that ID", "error")
        return redirect(url_for(".begin"))

    form = forms.ReplayForm(game_id, game.characters)

    if form.validate_on_submit():
        if len(form.authorize.data) == c.NUM_PLAYERS:
            session["game_id"] = game_id
            game.turn_num = turn_num
            db.session.commit()

            return redirect(url_for(".draw"))
        else:
            flash("A replay was not authorized")
            return redirect(url_for(".game_history", game_id=form.game.data))

    return render_template("base_form.html", title="Redo Turn", form=form)
