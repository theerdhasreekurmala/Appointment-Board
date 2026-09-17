from app import app, db, Appointment
from sqlalchemy.exc import OperationalError

def _mask(uri: str) -> str:
    if not uri:
        return 'None'
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(uri)
        if p.password:
            netloc = f"{p.username}:***@{p.hostname}"
            if p.port:
                netloc += f":{p.port}"
            return urlunparse((p.scheme, netloc, p.path or '', '', '', ''))
    except Exception:
        pass
    return uri

with app.app_context():
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print('SQLALCHEMY_DATABASE_URI:', _mask(uri))
    try:
        print('Engine dialect:', db.engine.dialect.name)
    except Exception as e:
        print('Engine error:', e)
    try:
        # list tables
        insp = db.inspect(db.engine)
        print('Tables:', insp.get_table_names())
    except Exception as e:
        print('Inspect error:', e)
    try:
        cnt = db.session.query(Appointment).count()
        print('Appointment rows count:', cnt)
        rows = db.session.query(Appointment).order_by(Appointment.id.desc()).limit(5).all()
        for r in rows:
            print('-', r.id, r.title, r.date, r.start_time, r.status)
    except OperationalError as oe:
        print('OperationalError:', oe)
    except Exception as e:
        print('Query error:', e)
