from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import db, Producto
from app import mail
from flask_mail import Message

tienda_bp = Blueprint("tienda", __name__)

@tienda_bp.route("/tienda")
def tienda():
    productos = Producto.query.order_by(Producto.id).all()
    return render_template("tienda.html", productos=productos)

@tienda_bp.route("/producto/<int:producto_id>")
def producto_page(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    return render_template("producto.html", producto=producto)

@tienda_bp.route("/carrito")
def ver_carrito():
    carrito = session.get("carrito", [])
    productos_carrito, total = [], 0
    for item_id in carrito:
        producto = Producto.query.get(item_id)
        if producto:
            productos_carrito.append(producto)
            total += float(producto.precio)
    return render_template("carrito.html", productos=productos_carrito, total=total)

@tienda_bp.route("/agregar_carrito/<int:producto_id>")
def agregar_carrito(producto_id):
    if "carrito" not in session:
        session["carrito"] = []
    session["carrito"].append(producto_id)
    flash("Producto agregado al carrito", "success")
    return redirect(url_for("tienda.tienda"))

@tienda_bp.route("/eliminar_carrito/<int:producto_id>")
def eliminar_carrito(producto_id):
    if "carrito" in session and producto_id in session["carrito"]:
        session["carrito"].remove(producto_id)
        flash("Producto eliminado del carrito", "info")
    return redirect(url_for("tienda.ver_carrito"))

@tienda_bp.route("/comprar_carrito", methods=["POST"])
def comprar_carrito():
    email = request.form.get("email")
    carrito = session.get("carrito", [])
    if not carrito:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for("tienda.ver_carrito"))

    productos_comprados = []
    for item_id in carrito:
        producto = Producto.query.get(item_id)
        if producto and producto.stock > 0:
            producto.stock -= 1
            productos_comprados.append(producto)
    db.session.commit()
    session["carrito"] = []

    if email:
        try:
            detalle = "\n".join(
                [f"- {p.nombre} | Talle: {p.talle} | Precio: ${p.precio}" for p in productos_comprados]
            )
            cuerpo = (
                f"Gracias por tu compra!\n\n"
                f"Estos son los productos que elegiste:\n"
                f"{detalle}\n\n"
                "Pasos para pagar:\n"
                "1. Realiza una transferencia a la cuenta XXXX.\n"
                "2. Envía el comprobante a mangano.nahuel@gmail.com.\n"
                "3. Una vez confirmado el pago, enviaremos tu pedido.\n\n"
                "Saludos,\nEl equipo de Mi Tienda"
            )
            msg = Message(subject="Detalles de tu compra - Mi Tienda", recipients=[email], body=cuerpo)
            mail.send(msg)
            flash("Compra realizada con éxito. Revisa tu correo.", "success")
        except Exception as e:
            flash(f"Compra realizada, pero no se pudo enviar el email: {e}", "warning")
    else:
        flash("Compra realizada con éxito!", "success")

    return redirect(url_for("tienda.tienda"))
