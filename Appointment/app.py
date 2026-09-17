from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv is optional; if it's not installed we rely on real env vars
    pass

app = Flask(__name__)

# Configure database via DATABASE_URL environment variable. Fallback to sqlite for local dev.
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///appointments.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(20), nullable=False)  # YYYY-MM-DD
    start_time = db.Column(db.String(10), nullable=False)  # HH:MM
    end_time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='scheduled')
    created_at = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'created_at': self.created_at,
        }

def parse_datetime(date_str, time_str):
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def has_conflict(date, start_time, end_time, exclude_id=None):
    start_dt = parse_datetime(date, start_time)
    end_dt = parse_datetime(date, end_time)
    q = Appointment.query.filter(Appointment.date == date, Appointment.status != 'cancelled')
    if exclude_id:
        q = q.filter(Appointment.id != exclude_id)
    for r in q.all():
        existing_start = parse_datetime(r.date, r.start_time)
        existing_end = parse_datetime(r.date, r.end_time)
        if start_dt < existing_end and existing_start < end_dt:
            return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/appointments', methods=['GET'])
def list_appointments():
    date = request.args.get('date')
    status = request.args.get('status')
    q = Appointment.query
    if date:
        q = q.filter(Appointment.date == date)
    if status:
        q = q.filter(Appointment.status == status)
    rows = q.order_by(Appointment.date, Appointment.start_time).all()
    return jsonify([r.to_dict() for r in rows])

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.json or {}
    required = ['title', 'date', 'start_time', 'end_time']
    for f in required:
        if not data.get(f):
            return jsonify({'error': 'Please fill in the meeting title, date, start time, and end time.'}), 400
    try:
        s = parse_datetime(data['date'], data['start_time'])
        e = parse_datetime(data['date'], data['end_time'])
    except Exception:
        return jsonify({'error': 'Please choose a valid date and time.'}), 400
    if e <= s:
        return jsonify({'error': 'End time must be later than the start time.'}), 400
    if has_conflict(data['date'], data['start_time'], data['end_time']):
        return jsonify({'error': 'This time slot is already booked.'}), 409
    appt = Appointment(
        title=data.get('title'),
        description=data.get('description',''),
        date=data.get('date'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        status='scheduled',
        created_at=datetime.utcnow().isoformat()
    )
    db.session.add(appt)
    db.session.commit()
    return jsonify({'id': appt.id}), 201

@app.route('/api/appointments/<int:aid>', methods=['PUT'])
def update_appointment(aid):
    data = request.json or {}
    appt = Appointment.query.get(aid)
    if not appt:
        return jsonify({'error': 'Appointment not found.'}), 404
    title = data.get('title', appt.title)
    desc = data.get('description', appt.description)
    date = data.get('date', appt.date)
    start_time = data.get('start_time', appt.start_time)
    end_time = data.get('end_time', appt.end_time)
    status = data.get('status', appt.status)
    try:
        s = parse_datetime(date, start_time)
        e = parse_datetime(date, end_time)
    except Exception:
        return jsonify({'error': 'Please choose a valid date and time.'}), 400
    if e <= s:
        return jsonify({'error': 'End time must be later than the start time.'}), 400
    if status != 'cancelled' and has_conflict(date, start_time, end_time, exclude_id=aid):
        return jsonify({'error': 'This time slot is already booked.'}), 409
    appt.title = title
    appt.description = desc
    appt.date = date
    appt.start_time = start_time
    appt.end_time = end_time
    appt.status = status
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/appointments/<int:aid>', methods=['DELETE'])
def cancel_appointment(aid):
    appt = Appointment.query.get(aid)
    if not appt:
        return jsonify({'error': 'Appointment not found.'}), 404
    appt.status = 'cancelled'
    db.session.commit()
    return jsonify({'ok': True})

def seed_if_empty():
    if Appointment.query.count() == 0:
        now = datetime.utcnow().isoformat()
        samples = [
            Appointment(title='Daily Standup', description='Team sync', date='2026-09-20', start_time='09:00', end_time='09:15', status='scheduled', created_at=now),
            Appointment(title='Client Call', description='Discuss roadmap', date='2026-09-20', start_time='10:00', end_time='11:00', status='scheduled', created_at=now),
            Appointment(title='Design Review', description='Review mockups', date='2026-09-21', start_time='14:00', end_time='15:00', status='cancelled', created_at=now),
        ]
        db.session.bulk_save_objects(samples)
        db.session.commit()

def _mask_db_uri(uri: str) -> str:
    if not uri:
        return 'None'
    # hide password
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

if __name__ == '__main__':
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print('STARTING app — using DATABASE_URI =', _mask_db_uri(db_uri))
    with app.app_context():
        try:
            db.create_all()
            seed_if_empty()
            print('DB tables ensured (create_all completed)')
        except Exception as e:
            import traceback
            print('ERROR creating tables:')
            traceback.print_exc()
    app.run(debug=True)
