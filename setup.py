from setuptools import setup

setup(
    name="pandemic",
    version="0.2",
    packages=["pandemic"],
    include_package_data=True,
    install_requires=[
        "click",
        "flask",
        "Flask-SQLAlchemy",
        "Flask-Bootstrap",
        "Flask-WTF",
        "Flask-nav",
        "wtforms",
    ],
)
