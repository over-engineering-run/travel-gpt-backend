def init_db(db, db_migrate, flask_app, params):

    # config
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = params['db_dsn']

    # init db and migrate
    db.init_app(flask_app)
    db_migrate.init_app(flask_app, db)

    # create
    with flask_app.app_context():
        db.create_all()

    return db, db_migrate
