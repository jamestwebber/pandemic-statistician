
from wtforms import widgets

from .. import constants as c


def character_list():
    html = [
        '<div class="row">',
        '<label class="control-label" for="characters">Characters</label>',
        '<div class="js-grid">',
    ]

    html.extend(
        (
            '<div class="btn col-xs-3">'
            '<span class="glyphicon {}" aria-hidden="true"></span>'
            " {}</div>"
        ).format(c.CHARACTERS[char].icon, char)
        for char in c.CHARACTERS
    )
    html.append("</div></div>")

    return "".join(html)


class PlayerListWidget(widgets.ListWidget):
    """
    Renders a list of fields as a list of Bootstrap `div class="row"` elements.
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs["class"] += " js-player-grid"
        html = [character_list(), "<ol %s>" % (widgets.html_params(**kwargs))]
        for subfield in field:
            subfield.color_index.data = int(subfield.id.split("-")[-1])
            html.extend(('<li class="row form-control">', subfield(), "</li>"))
        html.append("</ol>")
        return widgets.HTMLString("".join(html))


def player_widget(field, **kwargs):
    field_id = kwargs.pop("id", field.id)

    errors = {"player_name": "", "character": ""}

    if field.errors:
        if "player_name" in field.errors:
            errors["player_name"] = "".join(
                '<p class="help-block">{}</p>'.format(error)
                for error in field.errors["player_name"]
            )
        if "character" in field.errors:
            errors["character"] = "".join(
                '<p class="help-block">{}</p>'.format(error)
                for error in field.errors["character"]
            )

    html = [
        "<div {}>".format(widgets.html_params(id=field_id, class_="col-xs-3")),
        '<label for="{}">{}</label> '.format(field_id, field.label),
        field.player_name(),
        errors["player_name"],
        field.turn_num(),
        field.character(),
        field.color_index(),
        '</div><div class="col-xs-2 js-grid-target {}"></div>'.format(field.id),
    ]

    if errors["character"]:
        html.append('<div class="col-xs-3">{}</div>'.format(errors["character"]))

    return widgets.HTMLString("".join(html))


def select_month(field, **kwargs):
    kwargs.setdefault("type", "radio")
    field_id = kwargs.pop("id", field.id)
    html = [
        "<div %s>"
        % widgets.html_params(
            id=field_id, class_="btn-group col-sm-12", data_toggle="buttons"
        )
    ]
    for value, label, checked in field.iter_choices():
        choice_id = "%s-%s" % (field_id, value)
        options = dict(
            kwargs, name=field.name, value=value, id=choice_id, autocomplete="off"
        )
        if checked:
            options["checked"] = "checked"
        html.append(
            (
                '<div class="btn month col-sm-3"><input {} /> '
                '<label for="{}">{}</label></div>'
            ).format(widgets.html_params(**options), field_id, label)
        )
    html.append("</div>")
    return widgets.HTMLString("".join(html))


def select_cities(field, **kwargs):
    kwargs.setdefault("type", "checkbox")
    field_id = kwargs.pop("id", field.id)
    html = [
        "<div %s>"
        % widgets.html_params(
            id=field_id, class_="btn-group row", data_toggle="buttons"
        )
    ]
    for value, label, checked in field.iter_choices():
        choice_id = "%s-%s" % (field_id, value)
        options = dict(
            kwargs, name=field.name, value=value, id=choice_id, autocomplete="off"
        )
        if checked:
            options["checked"] = "checked"
        html.append(
            (
                '<div class="btn city-{} col-sm-3"><input {} /> '
                '<label for="{}">{}</label></div>'
            ).format(c.CITIES[value], widgets.html_params(**options), field_id, label)
        )
    html.append("</div>")
    return widgets.HTMLString("".join(html))


def authorization(field, **kwargs):
    kwargs.setdefault("type", "checkbox")
    field_id = kwargs.pop("id", field.id)
    html = [
        "<div %s>"
        % widgets.html_params(
            id=field_id, class_="btn-group col-sm-12", data_toggle="buttons"
        )
    ]
    for value, (label, ci), checked in field.iter_choices():
        choice_id = "%s-%s" % (field_id, value)
        options = dict(
            kwargs, name=field.name, value=value, id=choice_id, autocomplete="off"
        )
        if checked:
            options["checked"] = "checked"
        html.append(
            (
                '<div class="btn players-{} col-sm-2"><input {} /> <label for="{}">'
                '<span class="glyphicon {}" aria-hidden="true"></span> {}</label></div>'
            ).format(
                ci,
                widgets.html_params(**options),
                field_id,
                c.CHARACTERS[value].icon,
                label,
            )
        )
    html.append("</div>")
    return widgets.HTMLString("".join(html))
