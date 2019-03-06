from flask import Blueprint

main = Blueprint("main", __name__)

import pandemic.main.views as views
