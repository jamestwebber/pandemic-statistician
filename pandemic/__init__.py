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
    this_app = Flask(__name__)
    this_app.config.from_object(config[config_name])
    config[config_name].init_app(this_app)

    bootstrap.init_app(this_app)
    db.init_app(this_app)
    nav.init_app(this_app)

    from .main import main as main_blueprint

    this_app.register_blueprint(main_blueprint)

    return this_app


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
    app.logger.info("Initialized the database.")
