from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///test.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Initialize the database."""
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)
    seed()


def seed():
    """Seed the database with sample data."""
    import models
    # the rooms
    roomnumbers = ['1560', '1561', '1562', '1563', '1564',
                   '1565', '1665', '1663', '1662', '1661', '1660']
    for roomnumber in roomnumbers:
        r = models.Room(number=roomnumber)
        db_session.add(r)

    # the types of team
    db_session.add(
        models.TeamType(
            name='default',
            priority=4,
            advance_time=7 * 2  # 2 weeks
        )
    )
    db_session.add(
        models.TeamType(
            name='other_team',
            priority=4,
            advance_time=7 * 2  # 2 weeks
        )
    )
    db_session.add(
        models.TeamType(
            name='class',
            priority=3,
            advance_time=7 * 2  # 2 weeks
        )
    )
    db_session.add(
        models.TeamType(
            name='colab_class',
            priority=2,
            advance_time=7 * 2  # 2 weeks
        )
    )
    db_session.add(
        models.TeamType(
            name='senior_project',
            priority=1,
            advance_time=7 * 2  # 2 weeks
        )
    )

    db_session.commit()
