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
    turn_num = HiddenField("num", validators=[InputRequired()])
    character = HiddenField(
        "char", validators=[InputRequired(), AnyOf([ch.name for ch in c.characters])]
    )
    color_index = HiddenField("oolor", validators=[InputRequired()])


class CityForecastField(Form):
    stack_order = HiddenField("order", validators=[InputRequired()])
    city_name = HiddenField(
        "city", validators=[InputRequired(), AnyOf([city.name for city in c.cities])]
    )


class BeginForm(FlaskForm):
    players = FieldList(
        FormField(PlayerField, widget=wdg.player_widget, label="Player"),
        label="",
        widget=wdg.DivListWidget(wdg.character_list()),
        min_entries=c.num_players,
        max_entries=c.num_players,
    )
    funding_rate = IntegerField(
        "Ration Level",
        default=0,
        validators=[InputRequired(), NumberRange(0, 10)],
        description="How many burritos we have",
    )
    extra_cards = IntegerField(
        "Bonus Cards",
        default=9,
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
    second_resilient_population = SelectMultipleField(
        "Resilient Population (2nd Epidemic)",
        widget=wdg.authorization,
        description="Authorize Resilient Population during second epidemic",
    )
    city_forecast = SelectMultipleField(
        "City Forecast", widget=wdg.authorization, description="Authorize City Forecast"
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, characters, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]

        self.turn_num = game_state["turn_num"]

        if self.turn_num == -1:
            del self.resilient_population
            del self.second_resilient_population
            del self.city_forecast
        else:
            character_list = [(ch.character.name, ch) for ch in characters]
            self.resilient_population.choices = character_list[:]
            self.city_forecast.choices = character_list[:]

            if game_state["epi_risk"] > 1.0:
                self.second_resilient_population.choices = character_list[:]
            else:
                del self.second_resilient_population

        if game_state["epi_risk"] == 0.0 or self.turn_num == -1:
            del self.epidemic
            del self.second_epidemic
        else:
            max_stack = max(game_state["stack"])
            epidemic_cities = [("", "")] + [
                (city_name, city_name) for city_name in game_state["stack"][max_stack]
            ]
            self.epidemic.choices = epidemic_cities

            if game_state["epi_risk"] > 1.0:
                self.second_epidemic.choices = epidemic_cities
            else:
                del self.second_epidemic

    def validate_resilient_population(self, field):
        if 0 < len(field.data) < c.num_players:
            field.data = []
            raise ValidationError("All players must authorize Resilient Population")

    def validate_second_resilient_population(self, field):
        if 0 < len(field.data) < c.num_players:
            field.data = []
            raise ValidationError("All players must authorize Resilient Population")
        if len(field.data) > 0 and not self.second_epidemic.data:
            raise ValidationError("There wasn't a second epidemic during this turn")

    def validate_city_forecast(self, field):
        if 0 < len(field.data) < c.num_players:
            field.data = []
            raise ValidationError("All players must authorize City Forecast")

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
            (city_name, c.city_dict[city_name])
            for city_name in game_state["stack"][1]
            for j in range(game_state["stack"][1][city_name])
        ]

    def validate_cities(self, field):
        if len(field.data) != c.infection_rates[self.epidemics]:
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
        self.skip_infection.choices = [(ch.character.name, ch) for ch in characters]

        choices = []
        for i in range(1, max(game_state["stack"]) + 1):
            choices.extend(
                (city_name, c.city_dict[city_name])
                for city_name in game_state["stack"][i]
                for j in range(game_state["stack"][i][city_name])
            )

            if len(choices) >= c.infection_rates[self.epidemics]:
                break

        self.cities.choices = choices

        self._fields = order_fields(self._fields, self._order)

    def validate_cities(self, field):
        if len(self.skip_infection.data) == c.num_players:
            if len(field.data) > 0:
                field.data = []
                self.skip_infection.data = []
                raise ValidationError("You shouldn't be infecting any cities")
        else:
            super(InfectForm, self).validate_cities(field)

    def validate_skip_infection(self, field):
        if 0 < len(field.data) < c.num_players:
            field.data = []
            raise ValidationError("All players must authorize this decision")


class ResilientPopForm(FlaskForm):
    resilient_cities = SelectMultipleField(
        "Resilient Cities",
        widget=wdg.select_cities,
        description="Select the city chosen for resiliency (up to 2 copies)",
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, r_stack, *args, **kwargs):
        super(ResilientPopForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]

        self.resilient_cities.choices = [
            (city_name, c.city_dict[city_name])
            for city_name in game_state["stack"][r_stack]
            for i in range(game_state["stack"][r_stack][city_name])
        ]

    def validate_resilient_cities(self, field):
        if len(field.data) not in (1, 2):
            field.data = []
            raise ValidationError("You must pick one or two city cards")
        elif len(field.data) == 2 and field.data[0] != field.data[1]:
            field.data = []
            raise ValidationError("The two cards must be for the same city")


class ForecastForm(FlaskForm):
    forecast_cities = FieldList(
        FormField(CityForecastField, widget=wdg.forecast_widget, label="City"),
        label="",
        min_entries=8,
        max_entries=8,
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, *args, **kwargs):
        super(ForecastForm, self).__init__(*args, **kwargs)

        cities = []
        for i in range(1, max(game_state["stack"]) + 1):
            cities.extend(
                c.city_dict[city_name]
                for city_name in game_state["stack"][i]
                for j in range(game_state["stack"][i][city_name])
            )
            if len(cities) >= 8:
                break

        self.forecast_cities.widget = wdg.DivListWidget(wdg.city_list(cities))

        self.game.data = game_state["game_id"]


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
        self.authorize.choices = [(ch.character.name, ch) for ch in characters]
        self.game.data = game_id

    def validate_authorize(self, field):
        if 0 < len(field.data) < c.num_players:
            field.data = []
            raise ValidationError("All players must authorize this decision")
