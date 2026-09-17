from app import db, app
import traceback

with app.app_context():
    try:
        db.create_all()
        print('CREATE_OK')
    except Exception:
        traceback.print_exc()
        print('CREATE_ERR')
