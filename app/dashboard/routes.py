import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from app.models import db, User, Categoria, Producto

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Por favor logueate primero", "error")
        return redirect(url_for("auth.login"))
    users = User.query.all()
    productos = Producto.query.all()
    return render_template("dashboard.html", users=users, productos=productos)

@dashboard_bp.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    if "user" not in session:
        flash("Por favor logueate primero", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        color = request.form.get("color")
        descripcion = request.form.get("descripcion")
        categoria_id = request.form.get("categoria_id")
        talle = request.form["talle"]

        imagen = request.files.get("imagen")
        imagen_url = None
        if imagen and imagen.filename != "":
            filename = secure_filename(imagen.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            imagen.save(filepath)
            imagen_url = f"/static/uploads/{filename}"

        nuevo_producto = Producto(
            nombre=nombre, precio=precio, stock=stock,
            color=color, descripcion=descripcion,
            categoria_id=categoria_id, talle=talle,
            imagen_url=imagen_url
        )
        db.session.add(nuevo_producto)
        db.session.commit()

        flash("Producto agregado correctamente", "success")
        return redirect(url_for("dashboard.dashboard"))

    categorias = Categoria.query.all()
    return render_template("agregar_producto.html", categorias=categorias)
