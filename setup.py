from setuptools import setup

setup(
    name="pandemic",
    packages=["pandemic"],
    include_package_data=True,
    install_requires=[
        "click",
        "flask",
        "sqlalchemy",
        "Flask-SQLAlchemy",
        "Bootstrap-Flask",
        "flask-wtf",
        "Flask-Script",
        "Flask-nav",
        "wtforms",
    ],
)
