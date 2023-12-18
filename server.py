import random
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_login import LoginManager, login_required, current_user, UserMixin, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from notifier import Email
import os

login_manager = LoginManager()
app = Flask(__name__)
ckeditor = CKEditor(app)
db = SQLAlchemy()
email = Email()
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", 'sqlite:///blogIt.db')
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

db.init_app(app)
login_manager.init_app(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(250), nullable=False, unique=True)
    Email = db.Column(db.String(250), nullable=False, unique=True)
    Password = db.Column(db.String(250), nullable=False)
    Blogs = db.relationship('Blogs', backref='user', lazy=True)


class Blogs(db.Model):
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(250), nullable=False, unique=True)
    SubTitle = db.Column(db.String(250), nullable=False)
    BlogContent = db.Column(db.String(250), nullable=False, unique=True)
    ImgUrl = db.Column(db.String(500), nullable=True)
    Date = date.today().strftime("%B %d,%Y")


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def email_collector():
    if request.method == "POST":
        email.email_notifier()
        return redirect(url_for('home'))


@app.before_request
def before_request():
    g.email_collector = email_collector


@app.route("/register", methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        password_encrypt = generate_password_hash(
            request.form.get("password"),
            method='pbkdf2:sha256',
            salt_length=8
        )
        user_data = User(
            Username=request.form.get("username"),
            Email=request.form.get("email"),
            Password=password_encrypt
        )
        db.session.add(user_data)
        db.session.commit()
        login_user(user_data)
        return redirect(url_for('login'))
    return render_template("Register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user:
        if request.method == "POST":
            name = request.form["username"]
            password = request.form["password"]
            user = db.session.execute(db.select(User).where(User.Username == name)).scalar()
            if not user:
                flash("The username doesn't exist, please try again")
                return redirect(url_for("register_user"))
            elif not check_password_hash(user.Password, password):
                flash("The credentials doesn't match")
                return redirect(url_for("login"))
            if user and check_password_hash(user.Password, password):
                login_user(user)
                return redirect(url_for('dash', name=current_user.Username))
            else:
                return redirect(url_for('login'))
        return render_template("Login.html")
    else:
        return redirect(url_for('register'))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/", methods=["GET", "POST"])
def home():
    blogs = db.session.execute(db.select(Blogs)).scalars().all()
    if not blogs:
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        else:
            return redirect(url_for('dash', name=current_user.Username))
    else:
        g.email_collector()
        random_blog = random.choice(blogs)
        remaining_data = [blog for blog in blogs if blog.Id != random_blog.Id]
        remaining_data_subset = remaining_data[:2]
        blog_like = [blog for blog in blogs if blog.Id != random_blog.Id and blog not in remaining_data_subset]
        return render_template("index.html", blog=blog_like, remaining_data=remaining_data_subset,
                               blog_data=random_blog, user=current_user)


@app.route("/userdash/<string:name>", methods=["GET", "POST"])
@login_required
def dash(name):
    if current_user.is_authenticated:
        blog_data = db.session.execute(db.select(Blogs).where(Blogs.userId == current_user.id)).scalars().all()
        return render_template("UserDash.html", user=current_user, blogs=blog_data)
    else:
        print("User not authenticated")
        return redirect(url_for('login_user'))


@app.route("/blog/<string:title>", methods=["GET", "POST"])
def blog(title):
    id = request.args.get("id")
    blog_data = db.get_or_404(Blogs, id)
    g.email_collector()
    return render_template("Blog.html", blog=blog_data)


@app.route("/createblog", methods=["GET", "POST"])
def create():
    title = request.form.get("title")
    url = request.form.get("url")
    content = request.form.get("ckeditor")

    if request.method == "POST":
        blog_data = Blogs(
            userId=current_user.id,
            Title=title,
            SubTitle=current_user.Username,
            BlogContent=content,
            ImgUrl=url
        )
        db.session.add(blog_data)
        db.session.commit()
        return redirect(url_for("dash", name=current_user.Username))
    return render_template("Create.html", blog=title)


@app.route("/updateblog/<string:user>/<int:id>/<string:title>", methods=["GET", "POST"])
def update(user, id, title):
    data = db.get_or_404(Blogs, id)
    g.email_collector()

    if request.method == "POST":
        data.Title = request.form.get("title")
        data.BlogContent = request.form.get("ckeditor")
        data.ImgUrl = request.form.get("url")
        db.session.commit()
        return redirect(url_for('dash', name=current_user.Username))
    return render_template("Create.html", is_edit=True, blog=data)


@app.route("/delete/<string:user>/<int:id>/<string:title>", methods=["GET", "POST"])
def delete(id, title, user):
    delete_data = db.get_or_404(Blogs, id)
    g.email_collector()
    db.session.delete(delete_data)
    db.session.commit()
    return redirect(url_for('dash', name=current_user.Username))


if __name__ == "__main__":
    app.run(debug=False)
