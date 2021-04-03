from enum import EnumMeta
import os
from random import randint
from functools import wraps
from datetime import date
import re

# Flask Import
from flask import Flask, render_template, redirect, url_for
from flask.globals import request
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.github import make_github_blueprint, github

# For Github local authentication !
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# My Modules import
from verifyDetails import VerifyDetails
from verify_otp import SendOTP
from keys import git_client_id, git_client_secret, google_client_id, google_client_secret


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")


# Connect to DB Locally
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "sqlite:///students.db")
# db = SQLAlchemy(app)

# for server - TODO - active before deploy
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Github Register
github_blueprint = make_github_blueprint(
    client_id=git_client_id, client_secret=git_client_secret)
app.register_blueprint(github_blueprint, url_prefix='/github_login')


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

# Create ONCE
# db.create_all()


# Index Route
@app.route('/')
def index():
    return render_template("index.html")

# Registration Route


@app.route('/python-registration', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if account already exits
        all_stds = Student.query.all()
        for std in all_stds:
            if std.email == email:
                flash("You already have an account. Please Log In.")
                return redirect(url_for('login'))

        # Verify Name, Email and Password of REGEX !
        verifyData = VerifyDetails(name, email, password)

        if not verifyData.verifyName():
            flash("Enter a valid name !")
        elif not verifyData.verifyEmail():
            flash("Enter a valid email !")
        elif not verifyData.verifyPassword():
            flash(
                "Minimum eight characters, at least one uppercase letter, one number and one special symbol.")
        else:
            hashed_password = generate_password_hash(
                password=password, method='pbkdf2:sha256', salt_length=8)

            return redirect(url_for('verify_otp', std_name=name, std_email=email, std_password=hashed_password))

        return render_template("registration.html", name=name, email=email, password=password)

    return render_template("registration.html")


# Verify-Otp Route
otp = None


@app.route('/verify-otp/<std_name>/<std_email>/<std_password>', methods=["GET", "POST"])
def verify_otp(std_name, std_email, std_password):
    global otp

    if "service" not in request.base_url and request.method == "GET":

        flash(f"An OTP is send to your email ({std_email}) address.")
        otp = randint(123456, 987654)
        send_otp = SendOTP(user_name=std_name, user_email=std_email, otp=otp)
        send_otp.register_msgBody()
        send_otp.send_OTP()

    if request.method == "POST":
        enter_otp = int(request.form.get("otp"))
        if otp == enter_otp:
            new_student = Student(name=std_name, email=std_email,
                                  password=std_password, date_of_join=date.today().strftime("%B %d, %Y"))
            db.session.add(new_student)
            db.session.commit()

            # This line will authenticate the user with Flask-Login
            login_user(new_student)

            return redirect(url_for('home'))
        else:
            flash("OTP mismatched, another OTP send to your email address.")
            return redirect(url_for('verify_otp', std_name=std_name, std_email=std_email, std_password=std_password))

    return render_template("email-verification.html", name=std_name, email=std_email, password=std_password)

# Login Route


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if github.authorized:
        return redirect(url_for('github_login'))

    if request.method == "POST":
        email = request.form.get("email")

        verify_email = VerifyDetails(email=email)
        if verify_email.verifyEmail() == True:
            all_stds = Student.query.all()
            for std in all_stds:
                if std.email == email:
                    user_pass = request.form.get("password")
                    if check_password_hash(std.password, user_pass):
                        login_user(std)
                        return redirect(url_for('home'))
                    else:
                        flash("Wrong Credentials !")
                        return redirect(url_for('login'))
            flash("Register for a free account and start exploring.")
            return redirect(url_for('register'))
        else:
            flash("Enter a valid email address")
            return redirect(url_for('login'))

    return render_template("login.html")


otp = None
temp_mail = None


@app.route('/reset-password', methods=["POST", "GET"])
def reset_password():
    global otp, temp_mail

    if request.method == "POST":
        email = request.form.get("email")
        entered_otp = request.form.get("otp")

        user = Student.query.filter_by(email=email).first()

        if entered_otp != None:
            user = Student.query.filter_by(email=temp_mail).first()

            if int(entered_otp) == otp:
                password = request.form.get('password')
                confirm_pass = request.form.get('confirm-password')
                verify_pass = VerifyDetails(password=password)
                if verify_pass.verifyPassword():
                    if password == confirm_pass:
                        hashed_pass = generate_password_hash(password)

                        user.password = hashed_pass
                        db.session.commit()
                        flash(
                            "Your password changed successfully, Now you can login !")
                        return redirect(url_for('login'))
                    else:
                        flash("Password mismatched, Both the password must be same !")
                else:
                    flash(
                        "Minimum eight characters, at least one uppercase letter, one number and one special symbol.")
            else:
                flash("Otp Mismatched, Please try again !")
        elif user:
            temp_mail = email
            otp = randint(123456, 987654)
            send_otp = SendOTP(user_name=user.name, user_email=email, otp=otp)
            send_otp.forgot_password_msgBody()
            send_otp.send_OTP()
            flash(
                f"An OTP send to your email. Please verify and change your password for {user.name}.")
        else:
            flash(f"No account found on email address {email}")
        print("user mail is ", email)
        return render_template("reset-password.html", user_email=email)

    return render_template("reset-password.html")


@app.route('/github')
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))

    account_info = github.get('/user')

    if account_info.ok:
        account_info_json = account_info.json()

        all_stds = Student.query.all()
        for std in all_stds:
            if std.email == account_info_json['login']:
                login_user(std)
                return redirect(url_for('home'))

        new_student = Student(name=account_info_json['name'], email=account_info_json['login'],
                              password=account_info_json['id'], date_of_join=date.today().strftime("%B %d, %Y"))
        db.session.add(new_student)
        db.session.commit()

        # This line will authenticate the user with Flask-Login
        login_user(new_student)
        flash("Sign in with Github successfull.")
        return redirect(url_for('index'))

# Home Route


@app.route('/home-page')
@login_required
def home():
    assignments = Assignments.query.order_by(Assignments.id.asc())  # asc
    return render_template("home.html", heading="Assigments", posts=assignments)


# Post Route
@app.route('/post/<int:post_id>')
@login_required
def post(post_id):
    requested_post = Assignments.query.get(post_id)
    return render_template("post.html", heading=requested_post.title, post=requested_post)


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


# Logout Route
@app.route('/logout')
def logout():
    if github.authorized:
        del app.blueprints['github'].token
    logout_user()
    return redirect(url_for('index'))


''' ONLY ADMIN  FEATURES '''
# Create new Assignment Route


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

    return render_template("create-ass.html", assignment={
        "title": "", "subtitle": "", "body": "Write your assignment",
    }, type="Add Assignment")


@app.route('/edit-assignment/<int:post_id>', methods=["GET", "POST"])
@admin_only
def edit_assignment(post_id):
    assignment_to_edit = Assignments.query.get(post_id)

    if request.method == "POST":
        # TODO - fix indexing issue after update a post

        assignment_to_update = Assignments.query.filter_by(id=post_id).first()
        assignment_to_update.title = request.form.get('title')
        assignment_to_update.subtitle = request.form.get('subtitle')
        assignment_to_update.body = request.form.get('body')
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("create-ass.html", assignment=assignment_to_edit, type="Edit Assignment")


@app.route('/delete-assignment/<int:post_id>')
@admin_only
def delete_assignment(post_id):
    assignment_to_delete = Assignments.query.get(post_id)
    db.session.delete(assignment_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete-user/<int:user_id>')
@admin_only
def delete_user(user_id):
    user_to_delete = Student.query.get(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    return redirect(url_for('show_student_table'))


@app.route('/add-user', methods=["POST", "GET"])
@admin_only
def add_user():
    if request.method == "POST":
        password = request.form.get("password")
        new_student = Student(name=request.form.get("name"), email=request.form.get("email"),
                              password=generate_password_hash(password=password,
                                                              method='pbkdf2:sha256', salt_length=8),
                              date_of_join=date.today().strftime("%B %d, %Y"))
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('show_student_table'))

    return render_template("create-ass.html", assignment={
        "title": "", "subtitle": "", "body": "",
    }, type="Add User")


@app.route('/posts-table')
@admin_only
def show_post_table():
    assignments = Assignments.query.all()
    return render_template("admin.html", posts=assignments, type="posts")


@app.route('/students-table')
@admin_only
def show_student_table():
    students = Student.query.all()
    return render_template("admin.html", posts=students, type="users")


# Service worker route
@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js'), 200, {'Content-Type': 'text/javascript'}


# Errors Route

@app.route('/<route>')
def error404(route):
    return render_template("err.html", route=route)


@app.route('/admin-only/forbidden')
def admin_only():
    return render_template("err.html", err="forbidden")


@app.route('/under-development/<link>')
def onDev(link):
    return render_template("develop.html", msg=link)


if __name__ == "__main__":
    app.run(debug=True)  # For Development
    # app.run()  # For Production TODO - change defore deploy
