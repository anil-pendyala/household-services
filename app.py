from flask import Flask, render_template, request, flash, session, redirect
from models import db, Customers, Professionals, Services, Requests
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import desc, func
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///household_services.db'  # Change to your actual database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional: Disable modification tracking

db.init_app(app)

with app.app_context():
    db.create_all()


def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = session['user_role']  # Get the role from the session
            if user_role != role:  # If the user's role does not match the required role
                flash("You do not have permission to access that page.", "danger")
                
                # Redirect user to their corresponding dashboard
                if user_role == 'customer':
                    return redirect('/customer/dashboard')  # Redirect customer to customer dashboard
                elif user_role == 'professional':
                    return redirect('/professional/dashboard')  # Redirect professional to professional dashboard
                else:
                    return redirect('/')

                # Optional: Add a fallback redirect if the user role is not recognized
                return redirect(url_for('unauthorized'))  # Fallback for undefined roles
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.context_processor
def inject_navbar_options():
    # Get user role from session
    user_role = session.get('user_role', 'guest')  # Default to 'guest' if not found

    navbar_options = {
        'customer': {'Dashboard': '/customer/dashboard', 'Book a Service': '/customer/list_services', 'Search Services': '/customer/pricing'},
        'professional': {'Dashboard': '/professional/dashboard', 'To Be Attended': '/professional/to_be_attended', 'Fulfilled Requests': '/professional/fulfilled_requests', 'My Profile': '/professional/profile'},
        'admin': {'Admin Dashboard': '/admin/dashboard', 'Manage Services':'/admin/services', 'Manage Users': '/admin/manage_users', 'Service Requests': '/admin/service_requests', 'Reports': '/admin/reports'},
        'guest': {'Home': '/', 'Services': '/services', 'Contact Us': '/contactus'}
    }

    # Return the navbar options for the current user role
    return {'navbar_options': navbar_options.get(user_role, navbar_options['guest'])}


def get_user_role(): 
    user_id = session.get('username', None)
    
    if user_id:
        # Query the user role based on user_id
        customer = db.session.query(Customers).filter_by(customer_id=user_id).first()
        professional = db.session.query(Professionals).filter_by(professional_id=user_id).first()

        if customer:
            return 'customer'
        elif professional:
            return 'professional'
        else:
            return 'guest'  # In case the user doesn't exist in either table
    else:
        return 'guest'
    
    
@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')

@app.route('/', methods = ['GET', 'POST'])
def show_home():
    return render_template('about.html')

# @app.route('/test', methods=['GET', 'POST'])
# def test():
#     username = request.form.get('username', 'Not Provided')
#     password = request.form.get('password', 'Not Provided')

#     return f'<h1>Welcome {username}!</h1><br>Username: {username}<br>Password: {password}'

# @app.route('/customer')
# def show_customer():
#     flash('Hello!')
#     return 'Welcome to customer!'

@app.route('/customer/register', methods = ['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Extract form data
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        address = request.form['address']
        pincode = request.form['pincode']

        # Check if the email already exists in the database
        existing_customer = Customers.query.filter_by(email=email).first()
        if existing_customer:
            flash('Email is already registered. Please login.', 'danger')
            return redirect('/customer/register')

        # Create a new customer record with plain password
        new_customer = Customers(
            email=email,
            password=password,  # Store password as plain text
            name=fullname,
            address=address,
            pincode=pincode
        )

        # Add the new customer to the database
        db.session.add(new_customer)
        db.session.commit()

        # Flash success message and redirect
        flash('Registration successful! Please login.', 'success')
        return redirect('/customer/register')

    return render_template('/customer/customer_register.html') 


@app.route('/professional/register', methods = ['GET', 'POST'])
def register_professional():
    services = db.session.query(Services).all()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        service_id = request.form['service_name']  # Get service_id from the form
        experience = float(request.form['experience'])
        doc_link = request.form['doc_link']
        address = request.form['address']
        pincode = request.form['pincode']
        
        # Insert the professional data into the database
        try:
            # Insert the new professional into the database
            new_professional = Professionals(
                email=email,
                password=password,
                name=fullname,
                service_id=service_id,  # Directly use the service_id
                experience=experience,
                doc_link=doc_link,
                address=address,
                pincode=pincode
            )
            
            db.session.add(new_professional)
            db.session.commit()
            return redirect('/professional/registration_request')  # Replace with the correct route

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('professional_register'))
    
    return render_template('/professional/professional_register.html', services = services)


@app.route('/professional/registration_request')
def show_status():
    return render_template('/professional/prof_register_request.html')


# @app.route('/customer/home', methods = ['GET', 'POST'])
# def show_customer_home():
#     customer_email = request.form.get('email')
#     customer_password = request.form.get('password')
#     customer_name = request.form.get('fullname')
#     customer_address = request.form.get('address')
#     customer_pincode = request.form.get('pincode')
#     return f'Email: {customer_email}<br>Password: {customer_password}<br>Name: {customer_name}<br>Address: {customer_address}<br>Pincode: {customer_pincode}'

# @app.route('/professional/home', methods = ['GET', 'POST'])
# def show_professional_home():
#     professional_email = request.form.get('email')
#     professional_password = request.form.get('password')
#     professional_name = request.form.get('fullname')
#     service = request.form.get('service_name')
#     experience = request.form.get('experience')
#     professional_address = request.form.get('address')
#     professional_pincode = request.form.get('pincode')
#     return f'{professional_email}<br>{professional_password}<br>{professional_name}<br>{service}<br>{experience}<br>{professional_address}<br>{professional_pincode}'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get credentials from the login form
        username = request.form['username']
        password = request.form['password']
        
        # Admin Check
        if username == 'admin' and password == 'admin1234':
            session['user_role'] = 'admin'
            session['username'] = 'Admin'
            return redirect('/admin/dashboard')

        # Check if the user exists in Customers table
        customer = db.session.query(Customers).filter_by(email=username, password=password).first()

        # Check if the user exists in Professionals table
        professional = db.session.query(Professionals).filter_by(email=username, password=password).first()

        # Check if the customer is blocked
        if customer:
            if customer.is_blocked:
                flash("Your account has been blocked.<br>Please contact support.", 'danger')
                return redirect('/login')
            session['user_id'] = customer.customer_id
            session['user_role'] = 'customer'
            session['username'] = customer.name
            return redirect('/customer/dashboard')  # Redirect to customer dashboard

        # Check if the professional is blocked
        elif professional:
            if professional.is_blocked:
                flash("Your account has been blocked. Please contact support.", 'danger')
                return redirect('/login')
            # Check if the professional is approved
            if professional.is_approved:
                session['user_id'] = professional.professional_id
                session['user_role'] = 'professional'
                session['username'] = professional.name
                return redirect('/professional/dashboard')  # Redirect to professional dashboard
            else:
                # Professional is not approved
                flash('Your documents are still under verification.', 'warning')
                return redirect('/login')

        else:
            # Invalid credentials
            flash('Invalid username or password.', 'danger')
            return redirect('/login')

    return render_template('login.html')



# @app.route('/customer/dashboard', methods = ['GET', 'POST'])
# def customer_dashboard():
#     return render_template('/customer/customer_dashboard.html')

# @app.route('/professional/dashboard', methods = ['GET', 'POST'])
# def professional_dashboard():
#     return render_template('/professional/professional_dashboard.html')


@app.route('/admin/addnew', methods=['GET', 'POST'])
@role_required('admin')

def add_new_service():
    if request.method == 'POST':
        # Get form data
        service_name = request.form.get('service_name')
        description = request.form.get('description')
        base_price = request.form.get('base_price')

        new_service = Services(
                service_name=service_name,
                description=description,
                base_price=float(base_price)
            )

        # Add the service to the database
        db.session.add(new_service)
        db.session.commit()

        flash('Service added successfully!', 'success')
    return render_template('/admin/add_new_service.html')
            

@app.route('/navbar')
def show_navbar():
    # customer_name = request.form.get('fullname')

    return render_template('base.html')

@app.route('/logout', methods = ['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect('/about')
    return render_template('logout.html')

@app.route('/about')
def show_about():
    return render_template('about.html')

@app.route('/customer/list_services', methods=['GET', 'POST'])
@role_required('customer')

def book_service():
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Filter services based on the search query
        all_services = Services.query.filter(
            Services.service_name.ilike(f"%{search_query}%") | 
            Services.description.ilike(f"%{search_query}%")
        ).all()
    else:
        # If no search query, fetch all services
        all_services = Services.query.all()
    
    return render_template(
        '/customer/list_services.html',
        services=all_services,
        search_query=search_query
    )


@app.route('/customer/book_service', methods=['GET', 'POST'])
@role_required('customer')

def confirm_request():
    service_id = request.args.get('service')
    selected_service = None

    if service_id:
        # Fetch the selected service from the database
        selected_service_obj = Services.query.filter_by(service_id=service_id).first()
        if selected_service_obj:
            selected_service = selected_service_obj.service_name

    if request.method == 'POST':
        # Capture booking details from the form
        service_type = request.form.get('service-type')
        description = request.form.get('description')
        service_date_str = request.form.get('date')  # This will be a string
        service_time = request.form.get('time')
        customer_id = session.get('user_id')  # Ensure the user is logged in and has a session

        if not customer_id:
            flash("Please log in to book a service.", "danger")
            return redirect('/login')

        # Convert the service_date string to a date object
        try:
            service_date = datetime.strptime(service_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect('/customer/book_service')

        # Find the service_id corresponding to the selected service name
        service_obj = Services.query.filter_by(service_name=service_type).first()
        if not service_obj:
            flash("Selected service is invalid.", "danger")
            return redirect('/customer/list_services')

        # Create a new service request
        new_request = Requests(
            service_id=service_obj.service_id,
            customer_id=customer_id,
            requirements=description,
            service_date=service_date,  # Pass the date object here
            service_time=service_time,
            status="Pending"
        )

        # Save the request to the database
        db.session.add(new_request)
        db.session.commit()
        flash("Service booked successfully!", "success")
        return redirect('/customer/dashboard')

    # Fetch all services for the dropdown
    services = Services.query.all()
    return render_template('/customer/book_service.html', services=services, selected_service=selected_service)


@app.route('/customer/pricing', methods=['GET', 'POST'])
@role_required('customer')

def show_pricing():
    search_query = request.args.get('search', '').strip()  # Get the search query from URL parameters
    
    if search_query:
        all_services = Services.query.filter(Services.service_name.ilike(f"%{search_query}%") |Services.description.ilike(f"%{search_query}%")).all()
    else:
        # Fetch all services if no search query
        all_services = Services.query.all()
    
    return render_template(
        '/guest/services.html',
        services=all_services,
        search_query=search_query
    )


@app.route('/services', methods=['GET'])
def show_services():
    search_query = request.args.get('search', '').strip()  # Get the search query from URL parameters
    
    if search_query:
        # Filter services based on the search query
        all_services = Services.query.filter(
            Services.service_name.ilike(f"%{search_query}%") |
            Services.description.ilike(f"%{search_query}%")
        ).all()
    else:
        # Fetch all services if no search query
        all_services = Services.query.all()
    
    return render_template(
        '/guest/services.html',
        services=all_services,
        search_query=search_query
    )


@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    # Query to get professionals with their service names
    professionals = db.session.query(Professionals, Services.service_name).join(Services, Professionals.service_id == Services.service_id).filter(Professionals.is_approved == False).all()
    
    # Pass the result to the template
    return render_template('admin/admin_dashboard.html', professionals=professionals)


@app.route('/contactus')
def contact_us():
    return render_template('/guest/contactus.html')


@app.route('/admin/services', methods=['GET'])
@role_required('admin')
def admin_services():
    services = Services.query.all()  # Fetch all services
    return render_template('/admin/admin_services.html', services=services)


@app.route('/admin/edit_service/<int:service_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_service(service_id):
    service = Services.query.get_or_404(service_id)

    if request.method == 'POST':
        # Update service details
        service.service_name = request.form.get('service_name')
        service.description = request.form.get('description')
        service.base_price = float(request.form.get('base_price'))

        db.session.commit()
        # flash("Service updated successfully!", "success")
        return redirect('/admin/services')

    return render_template('/admin/edit_service.html', service=service)


@app.route('/admin/delete_service/<int:service_id>', methods=['POST'])
@role_required('admin')
def delete_service(service_id):
    service = Services.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    # flash("Service deleted successfully!", "success")
    return redirect('/admin/services')


@app.route('/approve_professional/<int:professional_id>', methods=['POST'])
@role_required('admin')
def approve_professional(professional_id):
    # Fetch the professional and set is_approved to True
    professional = Professionals.query.get(professional_id)
    if professional:
        professional.is_approved = True
        db.session.commit()
        flash('Professional approved successfully!', 'success')
    else:
        flash('Professional not found.', 'danger')
    return redirect('/admin/dashboard')


@app.route('/reject_professional/<int:professional_id>', methods=['GET', 'POST'])
@role_required('admin')
def reject_professional(professional_id):
    if request.method == 'POST':
        # Reject the professional by deleting the record
        professional = Professionals.query.get(professional_id)
        if professional:
            db.session.delete(professional)
            db.session.commit()
        return redirect('/admin/dashboard')
    
    # Render confirmation page if GET request
    return render_template('admin/reject_professional.html', professional_id=professional_id)


@app.route('/customer/dashboard')
@role_required('customer')

def customer_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view your dashboard.", "danger")
        return redirect('/login')

    # Fetch active bookings (Pending, To Be Attended, Fulfilled)
    active_bookings = (
    db.session.query(Requests, Services.service_name, Professionals.name)
    .join(Services, Requests.service_id == Services.service_id)
    .outerjoin(Professionals, Requests.professional_id == Professionals.professional_id)
    .filter(Requests.customer_id == user_id, Requests.status.in_(['Pending', 'To Be Attended', 'Fulfilled']))
    .all()
    )


    # Fetch closed bookings (Canceled)
    closed_bookings = (
    db.session.query(Requests, Services.service_name, Professionals.name)
    .join(Services, Requests.service_id == Services.service_id)
    .outerjoin(Professionals, Requests.professional_id == Professionals.professional_id)
    .filter(Requests.customer_id == user_id, Requests.status == 'Closed')
    .all()
    )


    return render_template(
        '/customer/customer_dashboard.html',
        active_bookings=active_bookings,
        closed_bookings=closed_bookings
    )


@app.route('/customer/edit_booking/<int:request_id>', methods=['GET', 'POST'])
@role_required('customer')
def edit_booking(request_id):
    # Fetch the booking by ID
    booking = Requests.query.filter_by(request_id=request_id).first()

    if not booking:
        flash("Booking not found.", "danger")
        return redirect('/customer/dashboard')

    # Ensure the logged-in user owns the booking
    if booking.customer_id != session.get('user_id'):
        flash("You are not authorized to edit this booking.", "danger")
        return redirect('/customer/dashboard')

    if request.method == 'POST':
        # Update the booking details
        service_id = request.form.get('service-type')
        requirements = request.form.get('description')
        service_date = request.form.get('date')
        service_time = request.form.get('time')

        # Validate service existence
        service = Services.query.filter_by(service_id=service_id).first()
        if not service:
            flash("Invalid service selected.", "danger")
            return redirect(f'/customer/edit_booking/{request_id}')

        try:
            booking.service_id = service_id
            booking.requirements = requirements
            booking.service_date = datetime.strptime(service_date, '%Y-%m-%d').date()
            booking.service_time = service_time

            db.session.commit()
            flash("Booking updated successfully.", "success")
            return redirect('/customer/dashboard')
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(f'/customer/edit_booking/{request_id}')

    # Fetch all services for the dropdown
    services = Services.query.all()

    # Pre-fill the form with booking data
    booking_details = {
        "request_id": booking.request_id,
        "service_id": booking.service_id,
        "requirements": booking.requirements,
        "service_date": booking.service_date.strftime('%Y-%m-%d'),
        "service_time": booking.service_time,
    }

    return render_template(
        '/customer/edit_booking.html',
        booking=booking_details,
        services=services
    )


@app.route('/customer/cancel_booking/<int:request_id>', methods=['POST'])
@role_required('customer')
def cancel_booking(request_id):
    # Fetch the booking by ID
    booking = Requests.query.filter_by(request_id=request_id).first()

    if not booking:
        flash("Booking not found.", "danger")
        return redirect('/customer/dashboard')

    # Ensure the logged-in user owns the booking
    if booking.customer_id != session.get('user_id'):
        flash("You are not authorized to cancel this booking.", "danger")
        return redirect('/customer/dashboard')

    try:
        # Update the status of the booking to 'Canceled'
        booking.status = "Canceled"
        db.session.commit()
        flash("Booking canceled successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect('/customer/dashboard')


@app.route('/customer/finish_booking/<int:request_id>', methods=['POST'])
@role_required('customer')
def finish_booking(request_id):
    # Fetch the booking by ID
    booking = Requests.query.filter_by(request_id=request_id).first()

    if not booking:
        flash("Booking not found.", "danger")
        return redirect('/customer/dashboard')

    # Ensure the logged-in user owns the booking
    if booking.customer_id != session.get('user_id'):
        flash("You are not authorized to mark this booking as finished.", "danger")
        return redirect('/customer/dashboard')

    try:
        # Update the status to 'Closed' (or 'Finished')
        booking.status = "Closed"
        db.session.commit()
        flash("Service marked as finished successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect('/customer/dashboard')


@app.route('/admin/service_requests')
@role_required('admin')
def service_requests():
    # Query all requests
    pending_requests = (
        db.session.query(Requests, Services.service_name, Customers.name, Professionals.name)
        .outerjoin(Services, Requests.service_id == Services.service_id)
        .outerjoin(Customers, Requests.customer_id == Customers.customer_id)
        .outerjoin(Professionals, Requests.professional_id == Professionals.professional_id)
        .filter(Requests.status == "Pending")
        .all()
    )

    closed_requests = (
        db.session.query(Requests, Services.service_name, Customers.name, Professionals.name)
        .outerjoin(Services, Requests.service_id == Services.service_id)
        .outerjoin(Customers, Requests.customer_id == Customers.customer_id)
        .outerjoin(Professionals, Requests.professional_id == Professionals.professional_id)
        .filter(Requests.status == "Closed")
        .all()
    )

    canceled_requests = (
        db.session.query(Requests, Services.service_name, Customers.name, Professionals.name)
        .outerjoin(Services, Requests.service_id == Services.service_id)
        .outerjoin(Customers, Requests.customer_id == Customers.customer_id)
        .outerjoin(Professionals, Requests.professional_id == Professionals.professional_id)
        .filter(Requests.status == "Canceled")
        .all()
    )

    return render_template(
        '/admin/service_requests.html',
        pending_requests=pending_requests,
        closed_requests=closed_requests,
        canceled_requests=canceled_requests,
    )


@app.route('/professional/dashboard', methods=['GET', 'POST'])
@role_required('professional')
def professional_dashboard():
    # Fetch the logged-in professional's service_id
    professional_id = session.get('user_id')
    professional = Professionals.query.get(professional_id)

    if not professional:
        flash("Professional not found.", "danger")
        return redirect('/login')

    # Fetch the professional's service name
    service_name = Services.query.filter_by(service_id=professional.service_id).first().service_name

    # Fetch the pending requests for the professional's service
    pending_requests = db.session.query(Requests, Customers).join(Services).join(Customers).filter(
        Services.service_id == professional.service_id,
        Requests.status == 'Pending'
    ).all()

    # Fetch the to-be-attended requests (requests that have been accepted)
    to_be_attended_requests = db.session.query(Requests, Customers).join(Services).join(Customers).filter(
        Services.service_id == professional.service_id,
        Requests.status == 'To Be Attended'
    ).all()

    return render_template(
        '/professional/professional_dashboard.html',
        professional=professional,
        service_name=service_name,  # Pass the service name to the template
        pending_requests=pending_requests,
        to_be_attended_requests=to_be_attended_requests
    )


@app.route('/professional/accept_request/<int:request_id>', methods=['POST'])
@role_required('professional')
def accept_request(request_id):
    request = Requests.query.get(request_id)

    if not request:
        flash("Request not found.", "danger")
        return redirect('/professional/dashboard')

    # Get the professional's ID from the session (assuming logged-in professional's ID is in session)
    professional_id = session.get('user_id')

    if not professional_id:
        flash("Please log in to accept requests.", "danger")
        return redirect('/login')

    # Fetch the professional object from the database using the professional_id
    professional = Professionals.query.get(professional_id)

    if not professional:
        flash("Professional not found.", "danger")
        return redirect('/professional/dashboard')

    # Ensure the professional's service_id matches the service of the request
    if request.service_id != professional.service_id:
        flash("This request does not belong to your service.", "danger")
        return redirect('/professional/dashboard')

    # Update the request status to "To Be Attended"
    request.status = 'To Be Attended'

    # Assign the professional's ID to the request
    request.professional_id = professional_id

    # Commit the changes to the database
    db.session.commit()

    flash(f"Request for {request.requirements} has been accepted and is now 'To Be Attended'.", "success")
    return redirect('/professional/dashboard')


@app.route('/admin/manage_users', methods=['GET'])
@role_required('admin')
def manage_users():
    # Get search parameters
    user_type = request.args.get('user_type', 'professionals')
    search_query = request.args.get('search_query', '').strip()

    # Default active table
    active_table = None

    # Query for professionals (approved and not blocked)
    professionals = (
        db.session.query(
            Professionals.professional_id,
            Professionals.name,
            Services.service_name,
            Professionals.services_did,
            Professionals.rating
        )
        .join(Services, Professionals.service_id == Services.service_id)
        .filter(Professionals.is_approved == True, Professionals.is_blocked == False)
        .all()
    )

    # Query for blocked professionals
    blocked_professionals = (
        db.session.query(
            Professionals.professional_id,
            Professionals.name,
            Services.service_name
        )
        .join(Services, Professionals.service_id == Services.service_id)
        .filter(Professionals.is_blocked == True)
        .all()
    )

    # Query for customers
    customers = (
        db.session.query(Customers.customer_id, Customers.name, Customers.email, Customers.address, Customers.pincode)
        .filter(Customers.is_blocked == False)
        .all()
    )

    # Query for blocked customers
    blocked_customers = (
        db.session.query(Customers.customer_id, Customers.name, Customers.email)
        .filter(Customers.is_blocked == True)
        .all()
    )

    # Filter results based on the search query
    if search_query:
        if user_type == 'professionals':
            professionals = [p for p in professionals if search_query.lower() in p.name.lower()]
            blocked_professionals = [p for p in blocked_professionals if search_query.lower() in p.name.lower()]
            # Set active table
            active_table = 'professionalsTable' if professionals else 'blockedProfessionalsTable'
        elif user_type == 'customers':
            customers = [c for c in customers if search_query.lower() in c.name.lower() or search_query.lower() in c.email.lower()]
            blocked_customers = [c for c in blocked_customers if search_query.lower() in c.name.lower() or search_query.lower() in c.email.lower()]
            # Set active table
            active_table = 'customersTable' if customers else 'blockedCustomersTable'

    # Default to the first table if nothing is found
    if not active_table:
        active_table = 'professionalsTable'

    return render_template(
        'admin/manage_users.html',
        professionals=professionals,
        blocked_professionals=blocked_professionals,
        customers=customers,
        blocked_customers=blocked_customers,
        user_type=user_type,
        search_query=search_query,
        active_table=active_table
    )


@app.route('/admin/block_professional/<int:professional_id>', methods=['POST'])
@role_required('admin')
def block_professional(professional_id):
    professional = Professionals.query.get(professional_id)
    if professional:
        professional.is_blocked = True
        db.session.commit()
    return redirect('/admin/manage_users')


@app.route('/admin/unblock_professional/<int:professional_id>', methods=['POST'])
@role_required('admin')
def unblock_professional(professional_id):
    professional = Professionals.query.get(professional_id)
    if professional:
        professional.is_blocked = False
        db.session.commit()
    return redirect('/admin/manage_users')


@app.route('/admin/block_customer/<int:customer_id>', methods=['POST'])
@role_required('admin')
def block_customer(customer_id):
    customer = Customers.query.get(customer_id)
    if customer:
        customer.is_blocked = True
        db.session.commit()
    return redirect('/admin/manage_users')


@app.route('/admin/unblock_customer/<int:customer_id>', methods=['POST'])
@role_required('admin')
def unblock_customer(customer_id):
    customer = Customers.query.get(customer_id)
    if customer:
        customer.is_blocked = False
        db.session.commit()
    return redirect('/admin/manage_users')


@app.route('/professional/profile')
@role_required('professional')
def professional_profile():
    professional_id = session.get('user_id')
    if not professional_id:
        flash("Please log in to view your profile.", "danger")
        return redirect('/login')

    # Fetch the professional with the service_name by joining the Services table
    professional = db.session.query(Professionals, Services.service_name).join(Services).filter(Professionals.professional_id == professional_id).first()
    
    if not professional:
        flash("Professional not found.", "danger")
        return redirect('/login')

    # Get the number of services attended
    services_attended = db.session.query(Requests).filter_by(professional_id=professional.Professionals.professional_id, status='Closed').count()

    # Get the rating
    rating = professional.Professionals.rating

    return render_template(
        '/professional/professional_profile.html', 
        professional=professional, 
        services_attended=services_attended, 
        rating=rating
    )


@app.route('/customer/service_remarks/<int:request_id>', methods=['GET', 'POST'])
@role_required('customer')
def service_remarks(request_id):
    # Get the service request using the request_id
    service_request = Requests.query.get(request_id)

    if not service_request:
        flash("Service request not found.", "danger")
        return redirect('/customer/dashboard')

    # Fetch the corresponding professional for the request
    professional = Professionals.query.get(service_request.professional_id)

    if not professional:
        flash("Professional not found.", "danger")
        return redirect('/customer/dashboard')

    # Fetch the service details for the remarks page
    service = Services.query.get(service_request.service_id)
    if not service:
        flash("Service not found.", "danger")
        return redirect('/customer/dashboard')

    if request.method == 'POST':
        # Capture rating from the form
        rating = int(request.form['rating'])  # Directly cast to int since radio ensures valid input

        # Update the professional's average rating
        if professional.rating is None:
            # If no prior ratings, initialize the rating
            professional.rating = rating
        else:
            # Calculate the new average rating
            total_ratings = professional.services_did
            current_sum = professional.rating * total_ratings
            professional.rating = (current_sum + rating) / (total_ratings + 1)

        # Increment the number of services attended
        professional.services_did += 1

        # Mark the request as closed
        service_request.status = 'Closed'
        db.session.commit()

        flash("Service finished and rating submitted successfully.", "success")
        return redirect('/customer/dashboard')

    return render_template(
        'customer/service_remarks.html',
        service_name=service.service_name,
        requirements=service_request.requirements,
        service_date=service_request.service_date,
        professional_name=professional.name,
        request_id=request_id
    )


@app.route('/admin/reports', methods=['GET'])
@role_required('admin')
def admin_reports():
    # Top 5 highest-rated professionals
    highest_rated_professionals = db.session.query(
        Professionals.name, Professionals.professional_id, Professionals.rating
    ).order_by(Professionals.rating.desc()).limit(5).all()

    # Top 5 professionals by services done
    most_services_done_professionals = db.session.query(
        Professionals.name, Professionals.professional_id, Professionals.services_did
    ).order_by(Professionals.services_did.desc()).limit(5).all()

    # Top 5 customers with most requests
    top_customers = db.session.query(
        Customers.name, Customers.customer_id, func.count(Requests.customer_id).label("total_requests")
    ).join(Requests, Requests.customer_id == Customers.customer_id) \
        .group_by(Customers.customer_id, Customers.name) \
        .order_by(desc("total_requests")) \
        .limit(5).all()

    # Top 5 most demanded services
    most_demanded_services = db.session.query(
        Services.service_name, Services.service_id, func.count(Requests.service_id).label("total_requests")
    ).join(Requests, Requests.service_id == Services.service_id) \
        .group_by(Services.service_id, Services.service_name) \
        .order_by(desc("total_requests")) \
        .limit(5).all()

    # Pass the data to the template
    return render_template(
        "admin/reports.html",
        highest_rated_professionals=highest_rated_professionals,
        most_services_done_professionals=most_services_done_professionals,
        top_customers=top_customers,
        most_demanded_services=most_demanded_services
    )


@app.route('/professional/to_be_attended', methods=['GET'])
@role_required('professional')
def to_be_attended():
    # Get the professional's ID from the session (logged-in professional's ID)
    professional_id = session.get('user_id')
    
    if not professional_id:
        flash("Please log in to view your dashboard.", "danger")
        return redirect('/login')

    # Fetch requests with status 'To Be Attended' for this professional
    to_be_attended_requests = (
        db.session.query(Requests, Customers)
        .join(Customers, Customers.customer_id == Requests.customer_id)
        .filter(Requests.professional_id == professional_id, Requests.status == 'To Be Attended')
        .all()
    )
    
    return render_template(
        'professional/to_be_attended.html',
        to_be_attended_requests=to_be_attended_requests
    )


@app.route('/professional/fulfill_request/<int:request_id>', methods=['POST'])
@role_required('professional')
def fulfill_request(request_id):
    # Get the professional's ID from the session (logged-in professional's ID)
    professional_id = session.get('user_id')
    
    if not professional_id:
        flash("Please log in to view your dashboard.", "danger")
        return redirect('/login')

    # Fetch the request by ID
    service_request = Requests.query.get(request_id)

    if not service_request:
        flash("Service request not found.", "danger")
        return redirect('/professional/to_be_attended')

    # Ensure the request belongs to this professional and is in "To Be Attended" status
    if service_request.professional_id != professional_id or service_request.status != 'To Be Attended':
        flash("This request cannot be fulfilled by you.", "danger")
        return redirect('/professional/to_be_attended')

    # Update the status to "Fulfilled"
    service_request.status = 'Fulfilled'
    db.session.commit()

    flash(f"Request '{service_request.requirements}' marked as Fulfilled.", "success")
    return redirect('/professional/to_be_attended')


@app.route('/professional/fulfilled_requests', methods=['GET'])
@role_required('professional')
def fulfilled_requests():
    # Ensure the professional is logged in
    professional_id = session.get('user_id')
    if not professional_id:
        flash("Please log in to access your fulfilled requests.", "danger")
        return redirect('/login')

    # Fetch fulfilled requests for this professional
    fulfilled_requests = (
        db.session.query(Requests, Services.service_name)
        .join(Services, Requests.service_id == Services.service_id)
        .filter(Requests.professional_id == professional_id, Requests.status.in_(['Fulfilled', 'Closed']))
        .all()
    )

    return render_template(
        'professional/fulfilled_requests.html',
        fulfilled_requests=fulfilled_requests
    )


if __name__ == "__main__":
    app.run(host = '192.168.0.11', debug = True)