from . import db, constants as c


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

    def __hash__(self):
        return hash(
            c.Character(
                self.name, self.first_name, self.middle_name, self.haven, self.icon
            )
        )

    def __eq__(self, other):
        return hash(self) == hash(other)


epidemics = db.Table(
    "epidemics",
    db.Column("city_id", db.Integer, db.ForeignKey("cities.id"), primary_key=True),
    db.Column("turn_id", db.Integer, db.ForeignKey("turns.id"), primary_key=True),
)


class CityExile(db.Model):
    __tablename__ = "exiled_cities"
    turn_id = db.Column(db.Integer, db.ForeignKey("turns.id"), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), primary_key=True)
    count = db.Column(db.Integer, primary_key=True)

    city = db.relationship(
        "City",
        backref=db.backref("exiled", cascade="all, delete-orphan"),
        lazy=True,
        viewonly=True,
    )
    turn = db.relationship(
        "Turn",
        backref=db.backref("exiled", cascade="all, delete-orphan"),
        lazy=True,
        viewonly=True,
    )

    def __repr__(self):
        return f"<{self.city.name} ({self.count})>"


class CityInfection(db.Model):
    __tablename__ = "infections"
    turn_id = db.Column(db.Integer, db.ForeignKey("turns.id"), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), primary_key=True)
    count = db.Column(db.Integer, primary_key=True)

    city = db.relationship(
        "City",
        backref=db.backref("infections", cascade="all, delete-orphan"),
        lazy=True,
        viewonly=True,
    )
    turn = db.relationship(
        "Turn",
        backref=db.backref("infections", cascade="all, delete-orphan"),
        lazy=True,
        viewonly=True,
    )

    def __repr__(self):
        return f"{self.city.name} ({self.count})"


class CityForecast(db.Model):
    __tablename__ = "forecasts"
    turn_id = db.Column(db.Integer, db.ForeignKey("turns.id"), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), primary_key=True)
    stack_order = db.Column(db.Integer, primary_key=True)

    city = db.relationship(
        "City",
        backref=db.backref("forecasts", cascade="all, delete-orphan"),
        lazy=True,
        viewonly=True,
    )
    turn = db.relationship(
        "Turn",
        backref=db.backref("forecasts", cascade="all, delete-orphan"),
        lazy=True,
        viewonly=True,
    )

    def __repr__(self):
        return f"<{self.city.name} forecast to #{self.stack_order}>"


class City(db.Model):
    __tablename__ = "cities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)  # city name
    color = db.Column(db.String(32), nullable=False)  # (original) color of the city
    player_cards = db.Column(db.Integer, nullable=False)  # cards in player deck
    infection_cards = db.Column(db.Integer, nullable=False)  # cards in infection deck

    # turns when this city was drawn as an epidemic (many-to-one)
    epidemics = db.relationship(
        "Turn", secondary=epidemics, lazy=True, backref="epidemic"
    )

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(
            c.City(self.name, self.color, self.player_cards, self.infection_cards)
        )

    def __eq__(self, other):
        return hash(self) == hash(other)


class Turn(db.Model):
    __tablename__ = "turns"
    id = db.Column(db.Integer, primary_key=True)
    turn_num = db.Column(db.Integer)  # which turn this is
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    monitor = db.Column(db.Integer, default=0)  # monitor action(s) taken this turn
    skipped_epi = db.Column(db.Integer, default=0)  # epidemics skipped by monitoring

    def __repr__(self):
        return "<Turn {}: {} infected>".format(
            self.turn_num,
            ", ".join(ci.city.name for ci in self.infections)
            if self.infections
            else "No cities",
        )
