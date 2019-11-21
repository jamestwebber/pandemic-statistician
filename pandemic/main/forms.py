from collections import OrderedDict

from flask_wtf import FlaskForm

from wtforms import (
    Form,
    IntegerField,
    SelectField,
    FieldList,
    FormField,
    SelectMultipleField,
    SubmitField,
    HiddenField,
    ValidationError,
)
from wtforms.validators import InputRequired, NumberRange, AnyOf

from .. import constants as c

from ..main import widgets as wdg


def order_fields(fields, order):
    return OrderedDict((k, fields[k]) for k in order if k in fields)


def auth_valid(field):
    return bool(field and len(field.data) == c.num_players)


def validate_auth(field, field_name):
    if 0 < len(field.data) < c.num_players:
        field.data = []
        raise ValidationError(f"All players must authorize {field_name}")


class PlayerField(Form):
    turn_num = HiddenField("num", validators=[InputRequired()])
    character = HiddenField(
        "char", validators=[InputRequired(), AnyOf([ch.name for ch in c.characters])]
    )
    color_index = HiddenField("color", validators=[InputRequired()])


class CityForecastField(Form):
    stack_order = HiddenField("order", validators=[InputRequired()])
    city_name = HiddenField(
        "city", validators=[InputRequired(), AnyOf([city.name for city in c.cities])]
    )


class MonitorField(Form):
    monitor_count = IntegerField(
        "Actions Used",
        default=0,
        validators=[InputRequired(), NumberRange(0, 4)],
        description="What's the frequency?",
    )
    epidemics_seen = IntegerField(
        "Epidemics Discarded",
        default=0,
        validators=[InputRequired(), NumberRange(0, 4)],
        description="Bullets dodged",
    )

    def validate_epidemics_seen(self, field):
        if field.data > 0 and not self.monitor_count.data:
            raise ValidationError("Can't skip an epidemic without monitoring")


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
    submit = SubmitField("Submit")


class DrawForm(FlaskForm):
    exile_cities = SelectMultipleField(
        "Exile Cities", widget=wdg.select_cities, description="City cards sent to box 6"
    )
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
    city_forecast = SelectMultipleField(
        "City Forecast", widget=wdg.authorization, description="Authorize City Forecast"
    )
    lockdown = SelectMultipleField(
        "Lockdown", widget=wdg.authorization, description="Authorize City Lockdown"
    )
    inoculation = SelectMultipleField(
        "Inoculation",
        widget=wdg.authorization,
        description="Authorize Inoculation Unit",
    )
    relocation = SelectMultipleField(
        "Relocation",
        widget=wdg.authorization,
        description="Relocation (Unfunded Event)",
    )
    monitor = FormField(MonitorField, label="Monitor")
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, characters, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]

        self.turn_num = game_state["turn_num"]

        if self.turn_num == -1:
            del self.exile_cities
            del self.resilient_population
            del self.city_forecast
            del self.lockdown
            del self.inoculation
            del self.relocation
            del self.monitor
        else:
            character_list = [(ch.character.name, ch) for ch in characters]

            if game_state["funding"] > 0:
                self.resilient_population.choices = character_list[:]
                self.city_forecast.choices = character_list[:]
                self.inoculation.choices = character_list[:]
            else:
                del self.resilient_population
                del self.city_forecast
                del self.inoculation

            if c.possible_lockdown:
                self.lockdown.choices = character_list[:]
            else:
                del self.lockdown

            if c.possible_relocation:
                self.relocation.choices = character_list[:]
            else:
                del self.relocation

            self.exile_cities.choices = [
                (city.name, (city, 0))
                for city in game_state["stack"][0]
                if city != c.hollow_men
                for _ in range(game_state["stack"][0][city])
            ]

        if game_state["epi_risk"] == 0.0 or self.turn_num == -1:
            del self.epidemic
            del self.second_epidemic
        else:
            epi_stack = -6 if game_state["stack"][-6] else max(game_state["stack"])
            epidemic_cities = [("", "")] + [
                (city.name, city.name) for city in game_state["stack"][epi_stack]
            ]
            self.epidemic.choices = epidemic_cities

            if game_state["epi_risk"] > 1.0:
                self.second_epidemic.choices = epidemic_cities
            else:
                del self.second_epidemic

    def validate_resilient_population(self, field):
        validate_auth(field, "Resilient Population")

    def validate_city_forecast(self, field):
        validate_auth(field, "City Forecast")

    def validate_lockdown(self, field):
        validate_auth(field, "Lockdown")

    def validate_inoculation(self, field):
        validate_auth(field, "Inoculation")

    def validate_relocation(self, field):
        validate_auth(field, "Relocation")

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
            (city.name, (city, 1))
            for city in game_state["stack"][1]
            for _ in range(game_state["stack"][1][city])
        ]

    def validate_cities(self, field, setup=True):
        n_infected = sum(1 for n in field.data if n != c.hollow_men.name)
        if n_infected != (c.infection_rates[self.epidemics] + c.setup_men * setup):
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
        if game_state["funding"] > 0:
            self.skip_infection.choices = [(ch.character.name, ch) for ch in characters]
        else:
            del self.skip_infection

        choices = []
        for i in range(1, max(game_state["stack"]) + 1):
            choices.extend(
                (city.name, (city, i))
                for city in game_state["stack"][i]
                for _ in range(game_state["stack"][i][city])
            )

            if len(choices) >= c.infection_rates[self.epidemics]:
                break

        self.cities.choices = choices

        self._fields = order_fields(self._fields, self._order)

    def validate_cities(self, field):
        if auth_valid(self.skip_infection):
            if len(field.data) > 0:
                field.data = []
                self.skip_infection.data = []
                raise ValidationError("You shouldn't be infecting any cities")
        else:
            super(InfectForm, self).validate_cities(field, setup=False)

    def validate_skip_infection(self, field):
        validate_auth(field, "One Quiet Night")


class RemoveCityForm(FlaskForm):
    cities = SelectMultipleField(
        "Resilient Cities",
        widget=wdg.select_cities,
        description="Select resilient pop and/or lockdown cities",
    )
    submit = SubmitField("Submit")
    game = HiddenField("game_id", validators=[InputRequired()])

    def __init__(self, game_state, max_s, city_flag, *args, **kwargs):
        super(RemoveCityForm, self).__init__(*args, **kwargs)

        self.game.data = game_state["game_id"]
        self.city_flag = city_flag

        if city_flag & 8:
            self.cities.description = "Select cities for inoculation"
        elif city_flag & 4:
            self.cities.description = "Select cities for relocation"
        elif city_flag == 2:
            self.cities.description = "Select lockdown city"
        elif city_flag == 1:
            self.cities.description = "Select cities (up to 2) for resilient pop"

        self.cities.choices = [
            (city.name, (city, i))
            for i in range(0, max_s + 1)
            for city in game_state["stack"][i]
            if city != c.hollow_men
            for _ in range(game_state["stack"][i][city])
        ]

    def validate_cities(self, field):
        n_cities = len(field.data)
        u_cities = len(set(field.data))

        expected_n, expected_u = c.city_flags.get(self.city_flag, (3, 3))

        if n_cities == 0:
            raise ValidationError("You didn't select any cities")
        elif n_cities > expected_n:
            field.data = []
            raise ValidationError(f"You can pick at most {expected_n} city cards")
        elif u_cities > expected_u:
            field.data = []
            raise ValidationError(
                f"You can remove at most {expected_u} different cities"
            )


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
                city
                for city in game_state["stack"][i]
                for _ in range(game_state["stack"][i][city])
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
        validate_auth(field, "a replay")
