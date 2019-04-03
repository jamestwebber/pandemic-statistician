from . import db


class PlayerSession(db.Model):
    __tablename__ = "sessions"
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), primary_key=True)
    char_id = db.Column(db.Integer, db.ForeignKey("characters.id"), primary_key=True)

    # when they go in the turn order
    turn_num = db.Column(db.Integer, nullable=False)
    # index into the four gamepiece colors
    color_index = db.Column(db.Integer, nullable=False)

    game = db.relationship("Game", backref="characters", lazy=True)
    character = db.relationship("Character", backref="games", lazy=True)

    def __repr__(self):
        return f"<Game {self.game_id} - {self.character.name}>"


class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    funding_rate = db.Column(db.Integer, nullable=False)  # funding rate
    extra_cards = db.Column(db.Integer, nullable=False)  # bonus cards
    turn_num = db.Column(db.Integer, nullable=False)  # the current turn
    turns = db.relationship("Turn", backref="game", lazy="subquery")

    def __repr__(self):
        return f"<Game {self.id}, Turn {self.turn_num}, FR {self.funding_rate}>"


class Character(db.Model):
    __tablename__ = "characters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)  # character name/role
    first_name = db.Column(db.String(32), nullable=False)  # first name
    middle_name = db.Column(db.String(32), nullable=False)  # middle name/initial
    haven = db.Column(db.String(32), nullable=False)  # home haven
    icon = db.Column(db.String(32), nullable=False)  # glyphicon used for buttons

    def __repr__(self):
        return f"{self.first_name} {self.middle_name} {self.name} from {self.haven}"


draws = db.Table(
    "draws",
    db.Column("city_id", db.Integer, db.ForeignKey("cities.id"), primary_key=True),
    db.Column("turn_id", db.Integer, db.ForeignKey("turns.id"), primary_key=True),
)

epidemics = db.Table(
    "epidemics",
    db.Column("city_id", db.Integer, db.ForeignKey("cities.id"), primary_key=True),
    db.Column("turn_id", db.Integer, db.ForeignKey("turns.id"), primary_key=True),
)


class CityInfection(db.Model):
    __tablename__ = "infections"
    turn_id = db.Column(db.Integer, db.ForeignKey("turns.id"), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), primary_key=True)
    count = db.Column(db.Integer, primary_key=True)

    city = db.relationship("City", backref="infections", lazy=True)
    turn = db.relationship("Turn", backref="infections", lazy=True)

    def __repr__(self):
        return f"<{self.count} infection(s) of {self.city.name}>"


class CityForecast(db.Model):
    __tablename__ = "forecasts"
    turn_id = db.Column(db.Integer, db.ForeignKey("turns.id"), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), primary_key=True)
    stack_order = db.Column(db.Integer, primary_key=True)

    city = db.relationship("City", backref="forecasts", lazy=True)
    turn = db.relationship("Turn", backref="forecasts", lazy=True)

    def __repr__(self):
        return f"<{self.city.name} forecast to #{self.stack_order}>"


class City(db.Model):
    __tablename__ = "cities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)  # city name
    color = db.Column(db.String(32), nullable=False)  # (original) color of the city

    # turns when this city was drawn as an epidemic
    epidemics = db.relationship(
        "Turn", secondary=epidemics, lazy=True, backref="epidemic"
    )

    def __repr__(self):
        return self.name


class Turn(db.Model):
    __tablename__ = "turns"
    id = db.Column(db.Integer, primary_key=True)
    turn_num = db.Column(db.Integer)  # which turn this is
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)

    # turns when a city was exiled using resilient population (one-to-many)
    res_pop_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=True)
    res_pop_count = db.Column(db.Integer, nullable=True)
    resilient_pop = db.relationship("City", lazy=True, backref="resilient_pops")

    def __repr__(self):
        return "<Turn {}: {} infected>".format(
            self.turn_num,
            ", ".join(ci.city.name for ci in self.infections)
            if self.infections
            else "No cities",
        )
