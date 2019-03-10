from collections import OrderedDict

from flask_wtf import FlaskForm

from wtforms import (
    Form,
    Field,
    StringField,
    IntegerField,
    BooleanField,
    SelectField,
    RadioField,
    FieldList,
    FormField,
    SelectMultipleField,
    SubmitField,
    HiddenField,
    ValidationError,
)
from wtforms.validators import InputRequired, NumberRange, AnyOf

from .. import constants as c
from ..models import Game, City, Turn

from ..main import widgets as wdg


def order_fields(fields, order):
    return OrderedDict((k, fields[k]) for k in order)


class PlayerField(Form):
    player_name = StringField("Name", validators=[InputRequired()])
    turn_num = HiddenField("num", validators=[InputRequired()])
    character = HiddenField("char", validators=[InputRequired(), AnyOf(c.CHARACTERS)])
    color_index = HiddenField("oolor", validators=[InputRequired()])


class BeginForm(FlaskForm):
    month = SelectField(
        "Current Month",
        choices=list(zip(c.MONTHS, c.MONTHS)),
        validators=[InputRequired()],
        widget=wdg.select_month,
        description="The month for this game",
    )
    players = FieldList(
        FormField(PlayerField, widget=wdg.player_widget, label="Player name"),
        label="",
        widget=wdg.PlayerListWidget(),
        min_entries=c.NUM_PLAYERS,
        max_entries=c.NUM_PLAYERS,
    )
    funding_rate = IntegerField(
        "Funding Rate",
        default=0,
        validators=[InputRequired(), NumberRange(0, 10)],
        description="How many R01s we have",
    )
    extra_cards = IntegerField(
        "Bonus Cards",
        default=0,
        validators=[InputRequired(), NumberRange(0)],
        description="Number of other cards (e.g. production cards) in the deck",
    )
    submit = SubmitField("Submit")


class DrawForm(FlaskForm):
    epidemic = SelectField(
        "Epidemic", description="If an epidemic was drawn, select the city affected"
    )
    second_epidemic = SelectField(
        "Epidemic", description="If a second epidemic was drawn"
    )
    resilient_population = SelectMultipleField(
        "Resilient Population",
        widget=wdg.authorization,
        description="Authorize Resilient Population",
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, characters, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]

        self.turn_num = game_state["turn_num"]

        if game_state["epi_risk"] == 0.0 or self.turn_num == -1:
            del self.epidemic
            del self.second_epidemic
            del self.resilient_population
        else:
            max_stack = max(city["stack"] for city in game_state["city_data"])
            epidemic_cities = [("", "")] + [
                (city["name"], city["name"])
                for city in game_state["city_data"]
                if city["stack"] == max_stack
            ]
            self.epidemic.choices = epidemic_cities

            if game_state["epi_risk"] > 1.0:
                self.second_epidemic.choices = epidemic_cities
            else:
                del self.second_epidemic

            self.resilient_population.choices = [
                (ch.character.name, ("Yes", ch.color_index)) for ch in characters
            ]

    @staticmethod
    def validate_resilient_population(field):
        if 0 < len(field.data) < c.NUM_PLAYERS:
            field.data = []
            raise ValidationError("All players must authorize Resilient Population")

    def validate_second_epidemic(self, field):
        if field.data and not self.epidemic.data:
            raise ValidationError("For one epidemic, use the other selector")


class SetupInfectForm(FlaskForm):
    cities = SelectMultipleField(
        "Infected Cities",
        widget=wdg.select_cities,
        description="Cities infected during setup",
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, *args, **kwargs):
        super(SetupInfectForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]
        self.epidemics = -1
        self.cities.choices = [
            (city["name"], city["name"]) for city in game_state["city_data"]
        ]

    def validate_cities(self, field):
        if len(field.data) != c.INFECTION_RATES[self.epidemics]:
            field.data = []
            raise ValidationError("You didn't infect the right number of cities")


class InfectForm(SetupInfectForm):
    skip_infection = SelectMultipleField(
        "One quiet night",
        widget=wdg.authorization,
        description="Skip this infection step",
    )

    _order = ["cities", "skip_infection", "submit", "game"]

    def __init__(self, game_state, characters, *args, **kwargs):
        super(InfectForm, self).__init__(game_state, *args, **kwargs)

        self.game.data = game_state["game_id"]
        self.epidemics = game_state["epidemics"]

        self.cities.description = "Cities infected this turn"
        self.skip_infection.choices = [
            (ch.character.name, ("Yes", ch.color_index)) for ch in characters
        ]

        choices = []
        for i in range(1, 7):
            choices.extend(
                (city["name"], city["name"])
                for city in game_state["city_data"]
                if city["stack"] == i
            )

            if len(choices) >= c.INFECTION_RATES[self.epidemics]:
                break

        self.cities.choices = choices

        self._fields = order_fields(self._fields, self._order)

    def validate_cities(self, field):
        if len(self.skip_infection.data) == c.NUM_PLAYERS:
            if len(field.data) > 0:
                field.data = []
                self.skip_infection.data = []
                raise ValidationError("You shouldn't be infecting any cities")
        else:
            super(InfectForm, self).validate_cities(field)

    @staticmethod
    def validate_skip_infection(field):
        if 0 < len(field.data) < c.NUM_PLAYERS:
            field.data = []
            raise ValidationError("All players must authorize this decision")


class ResilientPopForm(FlaskForm):
    resilient_city = SelectField(
        "Resilient City", description="Select the city chosen for resiliency"
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, *args, **kwargs):
        super(ResilientPopForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]
        self.resilient_city.choices = [
            (city["name"], city["name"])
            for city in game_state["city_data"]
            if city["stack"] == 0
        ]


class ReplayForm(FlaskForm):
    authorize = SelectMultipleField(
        "Redo Turn?",
        widget=wdg.authorization,
        description="Authorization required to replay this turn",
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_id, characters, *args, **kwargs):
        super(ReplayForm, self).__init__(*args, **kwargs)
        self.authorize.choices = [
            (ch.character.name, ("Yes", ch.color_index)) for ch in characters
        ]
        self.game.data = game_id

    @staticmethod
    def validate_authorize(field):
        if 0 < len(field.data) < c.NUM_PLAYERS:
            field.data = []
            raise ValidationError("All players must authorize this decision")
