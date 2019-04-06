import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from config import config

import click

from . import constants

bootstrap = Bootstrap()
db = SQLAlchemy()
nav = Nav()


@nav.navigation()
def navbar():
    return Navbar(
        "Pandemic!",
        View("Begin", "main.begin"),
        View("Draw", "main.draw"),
        View("Infect", "main.infect"),
        View("History", "main.history"),
    )


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)
    nav.init_app(app)

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app


app = create_app(os.getenv("FLASK_CONFIG") or "default")


def init_db():
    from . import models

    db.create_all()
    db.session.add_all(
        [
            models.City(
                name=city.name,
                color=city.color,
                player_cards=city.player_cards,
                infection_cards=city.infection_cards,
            )
            for city in constants.cities
        ]
    )
    db.session.add_all(
        [
            models.Character(
                name=char.name,
                first_name=char.first_name,
                middle_name=char.middle_name,
                haven=char.haven,
                icon=char.icon,
            )
            for char in constants.characters
        ]
    )
    db.session.commit()


@app.cli.command("initdb")
def initdb_command():
    """Initializes the database."""
    init_db()
    print("Initialized the database.")


@app.cli.command("addchar")
@click.option("--first", help="First name")
@click.option("--middle", help="Middle name/initial/nickname")
@click.option("--last", help="Character name/last name")
@click.option("--haven", help="Home haven")
@click.option("--icon", help="Glyphicon icon")
def addchar_command(first, middle, last, haven, icon):
    from . import models

    db.session.add(
        models.Character(
            name=last, first_name=first, middle_name=middle, haven=haven, icon=icon
        )
    )
    db.session.commit()
    print(f"Added new character: welcome, {first} {middle} {last} from {haven}!")


@app.cli.command("addcity")
@click.option("--name", help="City name")
@click.option("--color", help="Region color")
@click.option("--player_cards", type=int, help="# of cards added to player deck")
@click.option("--infection_cards", type=int, help="# of cards added to infection deck")
def addcity_command(name, color, player_cards, infection_cards):
    from . import models

    db.session.add(
        models.City(
            name=name,
            color=color,
            player_cards=player_cards,
            infection_cards=infection_cards,
        )
    )
    db.session.commit()
    print(f"Added new city: {name} ({color})")
