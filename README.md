# pandemic-statistician

The missing character! Every team of world-traveling disease fighters needs someone to do the stats.

This is an ever-so-slightly overbuilt online assistant for the board game [Pandemic Legacy](http://www.zmangames.com/store/p31/Pandemic_Legacy.html) as well as [Season 2](https://zmangames.com/en/products/pandemic-legacy-season-2/). This has been built for a specific group and contains a lot of **spoilers**, especially if you explore the git history!

The project is built as a Flask website, and the structure was strongly influenced by the [Flasky](https://github.com/miguelgrinberg/flasky) project to learn what I was doing. Some pieces of the code were copied wholesale and might not even work, I haven't tried to use them yet. It uses Flask, Flask-Bootstrap, Flask-SQLAlchemy (and SQLAlchemy), Flask-WTF (and WTForms), and Flask-Nav.

Also I hope this doesn't violate [zmangames](http://www.zmangames.com)'s copyright, but it feels like fair use to me? You should definitely buy Pandemic Legacy if you haven't already, it's really good. You can tell because I made a thing for it.

## What's new in version 0.2

Based on the previous game session (in which the server got into a broken state due to user error and was henceforth useless), I've rewritten the data model. The new app models a Game as a series of Turns, and allows for the possibility of going back to a previous turn to change what happened. One hiccup is that this can make the app think something is broken (i.e. a city was infected when that should be impossible) and the current solution is to wipe out the turns following the edited one&mdash;that's unfortunate because it doesn't allow for minor tweaks in game state.

## What's new in version 0.3

I've added character selection and tracking, so it will remember who played each character in each game. This required a little bit of Python and a whole lot of JavaScript to make the interface work nicely. I've also added epidemic tracking, so you will know how likely it is to draw the next epidemic (assuming you set up the deck in the way described in the rules).

### TODOs

* Update to Python 3
* Update game mechanics for Season 2
* Make it much easier to correct mistakes in a game, potentially by making a better admin interface
