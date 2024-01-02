from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, DecimalField, SubmitField,TimeField
from wtforms.validators import DataRequired, NumberRange
from flask import Flask, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from wtforms import StringField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import backref



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

csrf = CSRFProtect(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    place = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    place = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    has_driver_license = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(10), nullable=False, default='employee')  # Add this line

    def __repr__(self):
        return f"Employee('{self.username}', '{self.name}', '{self.role}')"

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, FloatField
from wtforms.validators import DataRequired, NumberRange
from sqlalchemy import JSON


class SeatAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('add_bus.id'), nullable=False)
    seat_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False)
    bus = db.relationship('AddBus', backref=db.backref('seats', uselist=True, cascade='delete,all'))


class AddBus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_name = db.Column(db.String(50), nullable=False)
    starting_point = db.Column(db.String(50), nullable=False)
    ending_point = db.Column(db.String(50), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    time_duration = db.Column(db.String(50), nullable=False)
    departure_time = db.Column(db.String(50), nullable=False)


class AddBusForm(FlaskForm):
    bus_name = StringField('Bus Name', validators=[DataRequired()])
    starting_point = StringField('Starting Point', validators=[DataRequired()])
    ending_point = StringField('Ending Point', validators=[DataRequired()])
    total_seats = IntegerField('Total Seats', validators=[DataRequired(), NumberRange(min=1)])
    time_duration = StringField('Time Duration', validators=[DataRequired()])
    departure_time = StringField('Departure Time', validators=[DataRequired()])
    submit = SubmitField('Add Bus')


class BookingForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    selected_seat = SelectField('Select a Seat', validators=[DataRequired()])
    submit = SubmitField('Reserve Seat')

    def set_seat_choices(self, available_seats):
        booked_seats = {seat for seat, status in available_seats.items() if status == 'booked'}
        self.selected_seat.choices = [(seat, seat) for seat in available_seats if seat not in booked_seats]


class SelectStopForm(FlaskForm):
    stops = SelectField('Select a Stop', validators=[DataRequired()])
    submit = SubmitField('Select Stop')


@app.route('/book_bus/<int:bus_id>', methods=['GET', 'POST'])
def book_bus(bus_id):
    bus = AddBus.query.get_or_404(bus_id)
    form_book = BookingForm()

    # Set choices for available seats
    form_book.set_seat_choices({f'seat_{i}': getattr(bus, f'seat_{i}', '') for i in range(1, bus.total_seats + 1)})

    if form_book.validate_on_submit():
        selected_seat = form_book.selected_seat.data

        # Check if the selected seat is available
        if getattr(bus, selected_seat, '') == 'booked':
            flash(f'Seat {selected_seat} is already booked. Please select another seat.', 'danger')
        else:
            # Check if the seat is already booked in the SeatAvailability table
            existing_booking = SeatAvailability.query.filter_by(bus_id=bus.id, seat_number=selected_seat, status='booked').first()

            if existing_booking:
                flash(f'Seat {selected_seat} is already booked. Please select another seat.', 'danger')
            else:
                # Mark the selected seat as booked
                setattr(bus, selected_seat, 'booked')

                # Create a booking record in the SeatAvailability table
                booking = SeatAvailability(bus_id=bus.id, seat_number=selected_seat, status='booked')
                db.session.add(booking)

                db.session.commit()

                flash(f'Seat {selected_seat} booked successfully!', 'success')
                return redirect(url_for('booking_confirmation', bus_id=bus.id))

    return render_template('book_bus.html', form_book=form_book, bus=bus, available_seats={f'seat_{i}': getattr(bus, f'seat_{i}', '') for i in range(1, bus.total_seats + 1)})



# Route to handle selecting a stop
@app.route('/select_stop/<int:bus_id>', methods=['POST'])
def select_stop(bus_id):
    form_stop = SelectStopForm()

    bus = AddBus.query.get_or_404(bus_id)  # Fetch the bus object

    if form_stop.validate_on_submit():
        selected_stop = form_stop.stops.data
        # Handle the selected stop as needed
        flash(f'Stop {selected_stop} selected!', 'success')
        # Now that a stop is selected, redirect to the booking page
        return redirect(url_for('book_bus', bus_id=bus.id))

    return redirect(url_for('display_booking_page', bus_id=bus.id))


@app.route('/booking_confirmation/<int:bus_id>')
def booking_confirmation(bus_id):
    # Query all booked seat details for a specific bus from the database
    bookings = SeatAvailability.query.filter_by(bus_id=bus_id, status='booked').all()

    return render_template('booking_confirmation.html', bookings=bookings)


# @app.route('/bus_details')
# def bus_details():
    

#     stops_and_charges = [
#         ('kottakkal', 'Kottakkal : ₹30'),
#         ('ramanattukara', 'Ramanattukara : ₹35'),
#         ('feroke', 'Feroke : ₹40'),
#         ('calicut', 'Calicut : ₹50')
#     ]

#     return render_template('book_bus.html', stops_and_charges=stops_and_charges)


@app.route('/add_bus', methods=['GET', 'POST'])
def add_bus():
    form = AddBusForm()

    if form.validate_on_submit():
        # Create the bus without seat availability
        bus = AddBus(
            bus_name=form.bus_name.data,
            starting_point=form.starting_point.data,
            ending_point=form.ending_point.data,
            total_seats=form.total_seats.data,
            time_duration=form.time_duration.data,
            departure_time=form.departure_time.data,
        )

        # Add the bus to the database
        db.session.add(bus)
        db.session.commit()

        # Add seat availability for the bus with correct bus_id
        seat_availability = [
            SeatAvailability(bus_id=bus.id, seat_number=f"seat_{i}") for i in range(1, form.total_seats.data + 1)
        ]

        # Update bus_id in each SeatAvailability instance
        for seat in seat_availability:
            seat.bus_id = bus.id

        db.session.bulk_save_objects(seat_availability)
        db.session.commit()

        flash('Bus details added successfully!', 'success')
        return redirect(url_for('employee_dashboard'))

    return render_template('add_bus.html', form=form)


@app.route('/edit_bus/<int:bus_id>', methods=['GET', 'POST'])
def edit_bus(bus_id):
    bus = AddBus.query.get_or_404(bus_id)
    form = AddBusForm(obj=bus)

    if form.validate_on_submit():
        # Update bus details from the form
        form.populate_obj(bus)
        db.session.commit()
        flash('Bus details updated successfully!', 'success')
        return redirect(url_for('employee_dashboard'))

    return render_template('edit_bus.html', form=form, bus_id=bus_id)


@app.route('/delete_bus/<int:bus_id>')
def delete_bus(bus_id):
    bus = AddBus.query.get_or_404(bus_id)
    db.session.delete(bus)
    db.session.commit()
    flash('Bus deleted successfully!', 'success')
    return redirect(url_for('employee_dashboard'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.password == password:
            flash('Admin login successful!', 'success')
            session['admin_id'] = admin.id  # Store admin ID in the session
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login unsuccessful. Please check your username and password.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('You do not have access to the admin dashboard.', 'danger')
        return redirect(url_for('homepage'))

    total_users = User.query.count()
    total_employees = Employee.query.count()
    users = User.query.all()
    employees = Employee.query.all()
    total_bus_count = AddBus.query.count()

    return render_template('admin_dashboard.html', users=users, employees=employees, total_users=total_users, total_employees=total_employees,total_bus_count=total_bus_count)
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Route to delete an employee
@app.route('/delete_employee/<int:employee_id>')
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/')
def homepage():
    return render_template("home.html")

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        age = request.form.get('age')
        place = request.form.get('place')
        gender = request.form.get('gender')
        phone_number = request.form.get('phone_number')
        user = User(username=username, password=password, name=name, age=age, place=place, gender=gender, phone_number=phone_number)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_user.html')

@app.route('/register_employee', methods=['GET', 'POST'])
def register_employee():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        age = request.form.get('age')
        place = request.form.get('place')
        gender = request.form.get('gender')
        phone_number = request.form.get('phone_number')
        has_driver_license = 'has_driver_license' in request.form
        employee = Employee(username=username, password=password, name=name, age=age, place=place, gender=gender, phone_number=phone_number, has_driver_license=has_driver_license)
        db.session.add(employee)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_employee.html')


from flask import session
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        employee = Employee.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id  # Store user ID in the session
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        elif employee and employee.password == password:
            session['employee_id'] = employee.id  # Store employee ID in the session
            flash('Login successful!', 'success')
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')

       

@app.route('/employee_dashboard')
def employee_dashboard():
    bus_details=AddBus.query.all()
    total_users = User.query.count()
    total_employees = Employee.query.count()
    
    total_bus_count = AddBus.query.count()
    return render_template('employee_dashboard.html',bus_details=bus_details,total_bus_count=total_bus_count, total_users=total_users, total_employees=total_employees)

@app.route('/dashboard')
def dashboard():
    bus_details = AddBus.query.all()
    return render_template('dashboard.html', bus_details=bus_details)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

