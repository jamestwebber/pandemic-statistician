# pandemic-statistician

The missing character! Every team of world-traveling disease fighters needs someone to do the stats.

This is an ever-so-slightly overbuilt online assistant for the board game [Pandemic Legacy](http://www.zmangames.com/store/p31/Pandemic_Legacy.html) as well as [Season 2](https://zmangames.com/en/products/pandemic-legacy-season-2/). This has been built for a specific group and contains a lot of **spoilers**, especially if you explore the git history!

The project is built as a Flask website, and the structure was strongly influenced by the [Flasky](https://github.com/miguelgrinberg/flasky) project to learn what I was doing. Some pieces of the code were copied wholesale and might not even work, I haven't tried to use them yet. It uses Flask, Flask-Bootstrap, Flask-SQLAlchemy (and SQLAlchemy), Flask-WTF (and WTForms), and Flask-Nav.

Also I hope this doesn't violate [zmangames](http://www.zmangames.com)'s copyright, but it feels like fair use to me? You should definitely buy Pandemic Legacy if you haven't already, it's really good. You can tell because I made a thing for it.

### TODOs

* Update game mechanics for Season 2 [in progress]
* Make it much easier to correct mistakes in a game, potentially by making a better admin interface
