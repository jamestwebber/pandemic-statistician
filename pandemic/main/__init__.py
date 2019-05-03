from flask import Blueprint

main = Blueprint("main", __name__)

from pandemic.main import views
