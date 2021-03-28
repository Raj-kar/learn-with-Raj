from operator import countOf
import os
from random import randint
from functools import wraps
from datetime import date
import re

# Flask Import
from flask import Flask, render_template, redirect, url_for, abort
from flask.globals import request
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# My Modules import
from verifyDetails import VerifyDetails
from verify_otp import SendOTP


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")


# Connect to DB Locally
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///students.db")
# db = SQLAlchemy(app)

# for server - TODO - active before deploy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = None
        try:
            current_user_id = current_user.id
        except Exception as e:
            print(e)
        finally:
            # If id is not 1 then return abort with 403 error
            if current_user_id != 1:
                return redirect(url_for('admin_only'))
            # Otherwise continue with the route function
            return f(*args, **kwargs)

    return decorated_function


# CONFIGURE TABLES - use UserMixin for login controls !
class Student(UserMixin, db.Model):
    __tablename__ = "student_data"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    date_of_join = db.Column(db.String(250), nullable=False)
    

class Assignments(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
## Create ONCE
# db.create_all()


## Index Route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('python_registration'))

## Registration Route
@app.route('/python-registration', methods = ["POST", "GET"])
def python_registration():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Check if account already exits
        all_stds = Student.query.all()
        for std in all_stds:
            if std.email == email:
                flash("You already have an account. Please Log In.")
                return redirect(url_for('index'))
        
        # Verify Name, Email and Password of REGEX !
        verifyData = VerifyDetails(name, email, password)
        
        if not verifyData.verifyName():
            flash("Enter a valid name !")
        elif not verifyData.verifyEmail():
            flash("Enter a valid email !")
        elif not verifyData.verifyPassword():
            flash("Minimum eight characters, at least one uppercase letter, one number and one special symbol.")
        else:
            hashed_password = generate_password_hash(
                password=password, method='pbkdf2:sha256', salt_length=8)

            return redirect(url_for('verify_otp', std_name=name, std_email=email, std_password=hashed_password))
            
        return render_template("index.html",name=name, email=email, password=password)
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    return render_template("index.html")


## Verify-Otp Route
otp = None
@app.route('/verify-otp/<std_name>/<std_email>/<std_password>', methods=["GET", "POST"])
def verify_otp(std_name, std_email, std_password):
    global otp

    if request.method == "GET":
        flash(f"An OTP is send to your email ({std_email}) address.")
        otp = randint(123456, 987654)
        # print(otp) # TODO - For Testing
        send_otp = SendOTP(user_name=std_name, user_email=std_email, otp=otp)
        send_otp.register_msgBody()
        send_otp.send_otp()

    if request.method == "POST":
        enter_otp = int(request.form.get("otp"))
        if enter_otp == otp:
            otp = None
            new_student = Student(name=std_name, email=std_email,
                                  password=std_password, date_of_join=date.today().strftime("%B %d, %Y"))
            db.session.add(new_student)
            db.session.commit()
            
            # This line will authenticate the user with Flask-Login
            login_user(new_student)
            
            flash("Registration Completed. Now you can Log In.")
            return redirect(url_for('index'))
        else:
            flash("OTP mismatched, another OTP send to your email address.")
            return redirect(url_for('verify_otp', std_name=std_name, std_email=std_email, std_password=std_password))

    return render_template("email-verification.html", name=std_name, email=std_email, password=std_password)


## Login Route
@app.route('/login', methods=["POST"])
def login():
    # Check if account not exits
    email = request.form.get("email")

    verify_email = VerifyDetails(email=email)

    if verify_email.verifyEmail():
        all_stds = Student.query.all()
        for std in all_stds:
            if std.email == email:
                name = std.name.split(" ")[0]
                flash(f"Welcome back {name}.")
                return redirect(url_for('verify_password', email=email))
        flash("Register for a free account and start exploring.")
        return redirect(url_for('index'))
    else:
        flash("Enter a valid email address")
        return redirect(url_for('index'))


## Verify Password Route
@app.route('/verify-password/<email>', methods=["POST", "GET"])
def verify_password(email):
    if request.method == "POST":
        password = request.form.get("password")
        student = Student.query.filter_by(email=email).first()
        if check_password_hash(student.password, password):
            login_user(student)
            # flash("LOGIN SUCESSFULLY !")
            return redirect(url_for('home'))
        else:
            flash("WRONG PASSWORD !")

    return render_template("validate_password.html", std_email=email)


## Home Route
@app.route('/home-page')
@login_required
def home():
    assignments = Assignments.query.all()
    return render_template("index-home.html", heading="Assigments", posts=assignments)


## Post Route
@app.route('/post/<int:post_id>')
@login_required
def post(post_id):
    requested_post = Assignments.query.get(post_id)
    return render_template("index-post.html", heading=requested_post.title, post=requested_post)


@app.route('/search/search-post', methods=["GET", "POST"])
def search_post():
    if request.method == "GET":
        return redirect(url_for('error404', route="Method-not-allowed"))
    
    if request.method == "POST":
        search_key = request.form.get("keywords").lower()
        assignments = Assignments.query.all()
        ass_list = []
        count = 0
        for each in assignments:
            if search_key in each.title.lower() or search_key in each.subtitle.lower():
                count += 1
                ass_list.append(each)
            elif search_key in each.body.lower():
                count += 1
                ass_list.append(each)
                    
        return render_template("index-home.html", heading=f"Find {count} results on {search_key} .", posts=ass_list)


## Logout Route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


''' ONLY ADMIN  FEATURES '''
## Create new Assignment Route
@app.route('/create-assignment', methods=["POST", "GET"])
@admin_only
def create_assignment():
    if request.method == "POST":
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        body = request.form.get('body')

        new_assignment = Assignments(title=title, subtitle=subtitle, body=body, author=current_user.name,
                                     date=date.today().strftime("%B %d, %Y"))
        db.session.add(new_assignment)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("create-ass.html")


@app.route('/delete-assignment/<int:post_id>')
@admin_only
def delete_assignment(post_id):
    assignment_to_delete = Assignments.query.get(post_id)
    db.session.delete(assignment_to_delete)
    db.session.commit()
    return redirect(url_for('home'))




## Errors Route

@app.route('/<route>')
def error404(route):
    return render_template("err.html", route=route)


@app.route('/admin-only/forbidden')
def admin_only():
    return render_template("err.html", err = "forbidden")


@app.route('/under-development/<link>')
def onDev(link):
    return render_template("develop.html", msg=link)



if __name__ == "__main__":
    # app.run(debug=True) # For Development 
    app.run()  # For Production TODO - change defore deploy
