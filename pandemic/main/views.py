import fractions

from flask import session, render_template, redirect, url_for, flash

from . import get_game_state
from .. import db
from .. import constants as c
from ..models import Game, City, CityForecast, Turn, PlayerSession, Character

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
        elif (
            form.city_forecast
            and len(form.city_forecast.data) == c.NUM_PLAYERS
        ):
            return redirect(url_for(".forecast"))
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

        this_turn.resilient_pop = City.query.filter(
            City.name.in_(form.resilient_cities.data)
        ).all()
        db.session.commit()

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

    form = forms.ForecastForm(game_state)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash("Game ID did not match session", "error")
            return redirect(url_for(".begin"))

        for fc in form.forecast_cities.data:
            city = City.query.filter_by(name=fc["city_name"]).first()
            cf = CityForecast(
                game_id=game.id,
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
        "forecast.html",
        title="City Forecast",
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
