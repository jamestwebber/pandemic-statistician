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
            '<div class="btn col-xs-3 btn-option">'
            '<span class="glyphicon {}" aria-hidden="true"></span>'
            " {}</div>"
        ).format(char.icon, char.name)
        for char in c.characters
    )
    html.append("</div></div>")

    return "".join(html)


def city_list(cities):
    html = [
        '<div class="row">',
        '<label class="control-label" for="Cities">Cities</label>',
        '<div class="js-grid">',
    ]

    html.extend(
        f'<div class="btn city-{city.color} col-xs-3"> {city.name}</div>'
        for city in cities
    )
    html.append("</div></div>")

    return "".join(html)


class DivListWidget(widgets.ListWidget):
    """
    Renders a list of fields as a list of Bootstrap `div class="row"` elements.
    """

    def __init__(self, item_html):
        super(DivListWidget, self).__init__()
        self.item_html = item_html

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs["class"] += " js-item-grid"
        html = [self.item_html, f"<ol {widgets.html_params(**kwargs)}>"]
        for subfield in field:
            if hasattr(subfield, "color_index"):
                subfield.color_index.data = int(subfield.id.split("-")[-1])
            html.extend(('<li class="row form-control">', subfield(), "</li>"))
        html.append("</ol>")
        return widgets.HTMLString("".join(html))


def player_widget(field, **kwargs):
    field_id = kwargs.pop("id", field.id)

    errors = {"character": ""}

    if field.errors:
        if "character" in field.errors:
            errors["character"] = "".join(
                '<p class="help-block">{}</p>'.format(error)
                for error in field.errors["character"]
            )

    html = [
        "<div {}>".format(widgets.html_params(id=field_id, class_="col-xs-2")),
        field.turn_num(),
        field.character(),
        field.color_index(),
        '</div><div class="col-xs-8 js-grid-target {}"></div>'.format(field.id),
    ]

    if errors["character"]:
        html.append('<div class="col-xs-4">{}</div>'.format(errors["character"]))

    return widgets.HTMLString("".join(html))


def forecast_widget(field, **kwargs):
    field_id = kwargs.pop("id", field.id)

    errors = {"city_name": ""}
    if field.errors:
        if "city_name" in field.errors:
            errors["city_name"] = "".join(
                '<p class="help-block">{}</p>'.format(error)
                for error in field.errors["city_name"]
            )

    html = [
        "<div {}>".format(widgets.html_params(id=field_id, class_="col-xs-2")),
        '<label for="{}">{}</label> '.format(field_id, field.label),
        field.city_name(),
        field.stack_order(),
        '</div><div class="col-xs-8 js-grid-target {}"></div>'.format(field.id),
    ]

    if errors["city_name"]:
        html.append('<div class="col-xs-4">{}</div>'.format(errors["city_name"]))

    return widgets.HTMLString("".join(html))


def select_cities(field, **kwargs):
    kwargs.setdefault("type", "checkbox")
    field_id = kwargs.pop("id", field.id)
    html = [
        "<div {}>".format(
            widgets.html_params(id=field_id, class_="row", data_toggle="buttons")
        )
    ]
    stack_0 = 1
    for value, (city, stack), checked in field.iter_choices():
        if stack > stack_0:
            html.append(
                "</div><div {}>".format(
                    widgets.html_params(
                        id=field_id, class_="row", data_toggle="buttons"
                    )
                )
            )
            stack_0 = stack
        choice_id = f"{field_id}-{value}"
        options = dict(
            kwargs, name=field.name, value=value, id=choice_id, autocomplete="off"
        )
        if checked:
            options["checked"] = "checked"
        html.append(
            (
                '<div class="btn city-{} col-sm-3"><input {} /> '
                '<label for="{}">{}</label></div>'
            ).format(city.color, widgets.html_params(**options), field_id, city.name)
        )
    html.append("</div>")
    return widgets.HTMLString("".join(html))


def authorization(field, **kwargs):
    kwargs.setdefault("type", "checkbox")
    field_id = kwargs.pop("id", field.id)
    html = [
        "<div {}>".format(
            widgets.html_params(id=field_id, class_="row", data_toggle="buttons")
        )
    ]
    for value, ch, checked in field.iter_choices():
        choice_id = f"{field_id}-{value}"
        options = dict(
            kwargs, name=field.name, value=value, id=choice_id, autocomplete="off"
        )
        if checked:
            options["checked"] = "checked"
        html.append(
            (
                '<div class="btn players-{} col-xs-2"><input {} /> <label for="{}">'
                '<span class="glyphicon {}" aria-hidden="true"></span> Yes</label>'
                "</div>"
            ).format(
                ch.color_index,
                widgets.html_params(**options),
                field_id,
                ch.character.icon,
            )
        )
    html.append("</div>")
    return widgets.HTMLString("".join(html))
