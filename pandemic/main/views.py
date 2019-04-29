from collections import Counter
from fractions import Fraction

from flask import session, render_template, redirect, url_for, flash

from . import get_game_state
from .. import db
from .. import constants as c
from ..models import (
    Game,
    City,
    CityForecast,
    CityInfection,
    Turn,
    PlayerSession,
    Character,
)

from . import main, forms


@main.app_template_filter("to_percent")
def to_percent(v, odds=True):
    if v > 0.01:
        pct = f"{v * 100.0:.1f}%"
    elif v > 0:
        pct = f"{v * 100.0:.1g}%"
    else:
        return ""

    if odds:
        return f"{pct} ({Fraction.from_float(v).limit_denominator()})"
    else:
        return pct


@main.app_template_filter("danger_level")
def danger_level(v):
    if v > 0.33:
        return "bg-danger"
    elif v > 0.25:
        return "bg-warning"
    else:
        return ""


@main.app_template_filter("color_i")
def color_i(color):
    return c.color_codes[color]


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
        db.session.commit()

    game_state = get_game_state(game)

    form = forms.DrawForm(game_state, game.characters)

    if form.validate_on_submit():
        if form.epidemic and form.epidemic.data:
            turn.epidemic = [City.query.filter_by(name=form.epidemic.data).one()]
            if form.second_epidemic and form.second_epidemic.data:
                turn.epidemic.append(
                    City.query.filter_by(name=form.second_epidemic.data).one()
                )
                res_s = 2
            else:
                res_s = 1
        else:
            res_s = 0

        do_res_pop = forms.validate_auth(form.resilient_population)

        if forms.validate_auth(form.second_resilient_population):
            # only possible if there are two epidemics
            do_res_pop = True
            res_s = 1

        do_forecast = forms.validate_auth(form.city_forecast)

        db.session.commit()

        if do_res_pop:
            # if res pop was played, we look at stack 0 (if no epidemics), 1 (if one),
            # or 2 (if res_pop was played on the first of two)
            # if there were two epidemics and res pop was played on the second,
            # we look at stack 1 for the city (there will only be one)
            return redirect(
                url_for(".resilientpop", r_stack=res_s, also_forecast=int(do_forecast))
            )
        elif do_forecast:
            return redirect(url_for(".forecast"))
        else:
            return redirect(url_for(".infect"))

    return render_template(
        "base_form.html", title="Draw Cards", game_state=game_state, form=form
    )


@main.route("/resilientpop/<int:r_stack>", methods=("GET", "POST"))
@main.route("/resilientpop/<int:r_stack>/<int:also_forecast>", methods=("GET", "POST"))
def resilientpop(r_stack=0, also_forecast=0):
    if session.get("game_id", None) is None:
        flash("No game in progress", "error")
        return redirect(url_for(".begin"))

    game_id = session["game_id"]
    game = Game.query.filter_by(id=game_id).one_or_none()
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

    form = forms.ResilientPopForm(game_state, r_stack)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        print(form.resilient_cities.data)

        this_turn.resilient_pop = City.query.filter(
            City.name.in_(form.resilient_cities.data)
        ).one()
        this_turn.res_pop_count = len(form.resilient_cities.data)
        if len(this_turn.epidemic) == 1:
            this_turn.res_pop_epi = 1
        elif len(this_turn.epidemic) == 2:
            this_turn.res_pop_epi = 3 - r_stack
        else:
            this_turn.res_pop_epi = 0

        db.session.commit()

        if also_forecast:
            return redirect(url_for(".forecast"))
        else:
            return redirect(url_for(".infect"))

    return render_template(
        "base_form.html",
        title="Select Resilient City",
        game_state=game_state,
        form=form,
    )


@main.route("/forecast", methods=("GET", "POST"))
def forecast():
    if session.get("game_id", None) is None:
        flash("No game in progress", "error")
        return redirect(url_for(".begin"))

    game_id = session["game_id"]
    game = Game.query.filter_by(id=game_id).one_or_none()
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

    game_state = get_game_state(game, draw_phase=False)

    form = forms.ForecastForm(game_state)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        for fc in form.forecast_cities.data:
            city = City.query.filter_by(name=fc["city_name"]).one()
            cf = CityForecast(
                city_id=city.id,
                turn_id=this_turn.id,
                turn=this_turn,
                city=city,
                stack_order=int(fc["stack_order"]) + 1,
            )
            this_turn.forecasts.append(cf)

        db.session.commit()

        return redirect(url_for(".infect"))

    return render_template(
        "forecast.html", title="City Forecast", game_state=game_state, form=form
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
    game = Game.query.filter_by(id=game_id).one_or_none()
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

    game_state = get_game_state(game, draw_phase=False)

    if game.turn_num == -1:
        form = forms.SetupInfectForm(game_state)
    else:
        form = forms.InfectForm(game_state, game.characters)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        infected_cities = Counter(form.cities.data)

        for city_name in infected_cities:
            city = City.query.filter_by(name=city_name).one()
            ci = CityInfection(
                city_id=city.id,
                turn_id=this_turn.id,
                turn=this_turn,
                city=city,
                count=infected_cities[city_name],
            )
            this_turn.infections.append(ci)

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
        if forms.validate_auth(form.authorize):
            session["game_id"] = game_id
            game.turn_num = turn_num

            turns = (
                Turn.query.filter_by(game_id=game.id)
                .filter(Turn.turn_num >= turn_num)
                .all()
            )
            for turn in turns:
                db.session.delete(turn)

            db.session.commit()

            return redirect(url_for(".draw"))
        else:
            flash("A replay was not authorized")
            return redirect(url_for(".game_history", game_id=form.game.data))

    return render_template("base_form.html", title="Redo Turn", form=form)
