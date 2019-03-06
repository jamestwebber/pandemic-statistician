import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from config import config

import click

import pandemic.constants as constants

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
    import pandemic.models as models

    db.create_all()
    db.session.add_all(
        [
            models.City(name=city_name, color=city_color)
            for city_name, city_color in constants.CITIES.items()
        ]
    )
    db.session.add_all(
        [
            models.Character(
                name=name, first_name=first_name, middle_name=middle_name, icon=icon
            )
            for name, (first_name, middle_name, icon) in constants.CHARACTERS.items()
        ]
    )
    db.session.commit()


@app.cli.command("initdb")
def initdb_command():
    """Initializes the database."""
    init_db()
    print("Initialized the database.")


@app.cli.command("newchar")
@click.option("--first", help="First name", type=unicode)
@click.option("--middle", help="Middle name/initial/nickname", type=unicode)
@click.option("--last", help="Character name/last name", type=unicode)
@click.option("--icon", help="Glyphicon icon", type=unicode)
def newchar_command(first, middle, last, icon):
    import pandemic.models as models

    db.session.add(
        models.Character(name=last, first_name=first, middle_name=middle, icon=icon)
    )
    db.session.commit()
    print("Added new character: welcome, {} {} {}!".format(first, middle, last))
