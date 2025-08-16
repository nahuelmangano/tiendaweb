from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User, Role

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user"] = user.username
            flash("Login exitoso", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Usuario o contraseña incorrectos", "error")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe", "error")
            return redirect(url_for("auth.register"))

        new_user = User(username=username)
        new_user.set_password(password)

        # Rol por defecto
        role_user = Role.query.filter_by(name="user").first()
        if not role_user:
            role_user = Role(name="user")
            db.session.add(role_user)
            db.session.commit()

        new_user.roles.append(role_user)

        db.session.add(new_user)
        db.session.commit()

        flash("Registro exitoso, ahora podés ingresar", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))
