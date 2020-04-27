import os
from sqlalchemy import *
import click
from flask import current_app, g
from flask.cli import with_appcontext

DATABASEURI = "postgresql://NAME:PASSWORD@PATH"
engine = create_engine(DATABASEURI)

def init_db():
    try:
        g.conn = engine.connect()
        print("Connect to DB successfully!")
    except:
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None
    return g.conn

def close_db(e=None):
    try:
        g.conn.close()
    except Exception as e:
        pass

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)



