from collections import Counter
from fractions import Fraction

from flask import flash, redirect, render_template, session, url_for

from pandemic import constants as c, db
from pandemic.main import forms, main
from pandemic.main.state import get_game_state
from pandemic.models import (
    Character,
    City,
    CityExile,
    CityForecast,
    CityInfection,
    Game,
    PlayerSession,
    Turn,
)


@main.app_template_filter("to_percent")
def to_percent(v: float, odds: bool = True):
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
def danger_level(v: float):
    if v > 0.33:
        return "bg-danger"
    elif v > 0.25:
        return "bg-warning"
    else:
        return ""


@main.app_template_filter("color_i")
def color_i(color: str):
    return c.color_codes[color]


def check_game_id(game_id: int = None):
    if not (game_id or session.get("game_id", None)):
        flash("No game in progress", "error")
        return None, None, redirect(url_for(".begin"))
    elif game_id:
        session["game_id"] = game_id

    game_id = session["game_id"]
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash("No game with that ID", "error")
        session["game_id"] = None
        return None, None, redirect(url_for(".begin"))

    this_turn = Turn.query.filter_by(
        game_id=game.id, turn_num=game.turn_num
    ).one_or_none()

    return game, this_turn, None


def exile_cities(this_turn: Turn, removed_cities: Counter):
    for city_name in removed_cities:
        city = City.query.filter_by(name=city_name).one()
        ci = CityExile(
            city_id=city.id,
            turn_id=this_turn.id,
            turn=this_turn,
            city=city,
            count=removed_cities[city_name],
        )
        this_turn.exiled.append(ci)


@main.route("/", methods=("GET", "POST"))
def begin():
    form = forms.BeginForm()

    if form.validate_on_submit():
        game = Game(funding_rate=form.funding_rate.data, turn_num=-1)

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
def draw(game_id: int = None):
    game, this_turn, redi = check_game_id(game_id)
    if redi is not None:
        return redi

    if this_turn is None:
        this_turn = Turn(game_id=game.id, turn_num=game.turn_num)
        db.session.add(this_turn)
        db.session.commit()

    game_state = get_game_state(game)

    form = forms.DrawForm(game_state, game.characters)

    if form.validate_on_submit():
        if form.exile_cities and form.exile_cities.data:
            exile_cities(this_turn, Counter(form.exile_cities.data))

        if form.epidemic and form.epidemic.data:
            this_turn.epidemic = [City.query.filter_by(name=form.epidemic.data).one()]
            if form.second_epidemic and form.second_epidemic.data:
                this_turn.epidemic.append(
                    City.query.filter_by(name=form.second_epidemic.data).one()
                )
                max_s = 2
            else:
                max_s = 1
        else:
            max_s = 0

        n_cities = int(forms.auth_valid(form.resilient_population)) + int(
            forms.auth_valid(form.lockdown)
        )

        do_forecast = forms.auth_valid(form.city_forecast)

        db.session.commit()

        if n_cities > 0:
            # less precise but easier to code version: show all the cities up to
            # the max stack, and rely on players to make correct selections (...)
            return redirect(
                url_for(
                    ".removecity",
                    max_stack=max_s,
                    n_cities=n_cities,
                    also_forecast=int(do_forecast),
                )
            )
        elif do_forecast:
            return redirect(url_for(".forecast"))
        else:
            return redirect(url_for(".infect"))

    return render_template(
        "base_form.html", title="Draw Cards", game_state=game_state, form=form
    )


@main.route(
    "/removecity/<int:max_stack>/<int:n_cities>/<int:also_forecast>",
    methods=("GET", "POST"),
)
def removecity(max_stack: int = 0, n_cities: int = 1, also_forecast: int = 0):
    game, this_turn, redi = check_game_id()
    if redi is not None:
        return redi

    if this_turn is None:
        flash("Need to draw cards first", "error")
        return redirect(url_for(".draw"))

    game_state = get_game_state(game)

    form = forms.RemoveCityForm(game_state, max_stack, n_cities)

    if form.validate_on_submit():
        if form.game.data != game.id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        exile_cities(this_turn, Counter(form.cities.data))

        db.session.commit()

        if also_forecast:
            return redirect(url_for(".forecast"))
        else:
            return redirect(url_for(".infect"))

    return render_template(
        "base_form.html", title="Remove Cities", game_state=game_state, form=form
    )


@main.route("/forecast", methods=("GET", "POST"))
def forecast():
    game, this_turn, redi = check_game_id()
    if redi is not None:
        return redi

    if this_turn is None:
        flash("Need to draw cards first", "error")
        return redirect(url_for(".draw"))

    game_state = get_game_state(game, draw_phase=False)

    form = forms.ForecastForm(game_state)

    if form.validate_on_submit():
        if form.game.data != game.id:
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
def infect(game_id: int = None):
    game, this_turn, redi = check_game_id(game_id)

    if this_turn is None:
        flash("Not on the infection step right now", "error")
        return redirect(url_for(".draw"))

    game_state = get_game_state(game, draw_phase=False)

    if game.turn_num == -1:
        form = forms.SetupInfectForm(game_state)
    else:
        form = forms.InfectForm(game_state, game.characters)

    if form.validate_on_submit():
        if form.game.data != game.id:
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
def game_history(game_id: int):
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash("No game with that ID", "error")
        return redirect(url_for(".history"))

    return render_template(
        "game_history.html", game=game, game_state=get_game_state(game)
    )


@main.route("/replay/<int:game_id>/<turn_num>", methods=("GET", "POST"))
def replay(game_id: int, turn_num: str):
    turn_num = int(turn_num)
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash("No game with that ID", "error")
        return redirect(url_for(".begin"))

    form = forms.ReplayForm(game_id, game.characters)

    if form.validate_on_submit():
        if forms.auth_valid(form.authorize):
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
