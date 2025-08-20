from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import db, Producto
from app import mail
from flask_mail import Message
from config import Config
import mercadopago
import os

tienda_bp = Blueprint('tienda', __name__)

# Config MercadoPago
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))




@tienda_bp.route("/tienda")
def tienda():
    productos = Producto.query.order_by(Producto.id).all()
    carrito = session.get("carrito", {})

    for producto in productos:
        cantidad_en_carrito = carrito.get(str(producto.id), 0)
        producto.stock_temporal = producto.stock - cantidad_en_carrito

    return render_template("tienda.html", productos=productos)



@tienda_bp.route("/producto/<int:producto_id>")
def producto_page(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    return render_template("producto.html", producto=producto)

@tienda_bp.route("/carrito")
def ver_carrito():
    carrito = session.get("carrito", {})  # ahora es dict
    productos_carrito = []
    total = 0

    for producto_id_str, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id_str))
        if producto:
            # Creamos un atributo temporal para la cantidad
            producto.cantidad = cantidad
            productos_carrito.append(producto)
            total += float(producto.precio) * cantidad

    return render_template("carrito.html", productos=productos_carrito, total=total)



@tienda_bp.route("/agregar_carrito/<int:producto_id>")
def agregar_carrito(producto_id):
    if "carrito" not in session:
        session["carrito"] = {}

    carrito = session["carrito"]

    # Si el producto ya está en el carrito, sumamos 1 a la cantidad
    if str(producto_id) in carrito:
        carrito[str(producto_id)] += 1
    else:
        carrito[str(producto_id)] = 1

    session["carrito"] = carrito
    flash("Producto agregado al carrito", "success")
    return redirect(url_for("tienda.tienda"))


# Eliminar producto del carrito (resta 1 o elimina si cantidad=1)
# Eliminar producto del carrito (resta 1 o elimina si cantidad=1)
@tienda_bp.route("/eliminar_carrito/<int:producto_id>")
def eliminar_carrito(producto_id):
    carrito = session.get("carrito", {})

    producto_id_str = str(producto_id)

    if producto_id_str in carrito:
        if carrito[producto_id_str] > 1:
            carrito[producto_id_str] -= 1
            flash("Se ha restado 1 unidad del producto", "info")
        else:
            carrito.pop(producto_id_str)
            flash("Producto eliminado del carrito", "info")

    session["carrito"] = carrito
    return redirect(url_for("tienda.ver_carrito"))




@tienda_bp.route("/comprar_carrito", methods=["POST"])
def comprar_carrito():
    email = request.form.get("email")
    carrito = session.get("carrito", [])

    if not carrito:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for("tienda.ver_carrito"))

    productos_comprados = []
    items_mp = []

    for item_id in carrito:
        producto = Producto.query.get(item_id)
        if producto and producto.stock > 0:
            producto.stock -= 1
            productos_comprados.append(producto)

            # Agregar producto a la preferencia de MercadoPago
            items_mp.append({
                "title": producto.nombre,
                "quantity": 1,
                "unit_price": float(producto.precio),
                "currency_id": "ARS"
            })

    db.session.commit()
    session["carrito"] = []

    # Enviar email con detalle de compra (opcional)
    if email:
        try:
            detalle = "\n".join(
                [f"- {p.nombre} | Talle: {p.talle} | Precio: ${p.precio}" for p in productos_comprados]
            )
            cuerpo = (
                f"Gracias por tu compra!\n\n"
                f"Estos son los productos que elegiste:\n"
                f"{detalle}\n\n"
                "Saludos,\nEl equipo de Mi Tienda"
            )
            msg = Message(subject="Detalles de tu compra - Mi Tienda", recipients=[email], body=cuerpo)
            mail.send(msg)
            flash("Compra realizada con éxito. Revisa tu correo.", "success")
        except Exception as e:
            flash(f"Compra realizada, pero no se pudo enviar el email: {e}", "warning")
    else:
        flash("Compra realizada con éxito!", "success")

    # Crear preferencia en MercadoPago
    if items_mp:
        import mercadopago
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

        preference_data = {
            "items": items_mp,
            "payer": {"email": email} if email else {}
        }
        preference_response = sdk.preference().create(preference_data)
        preference_id = preference_response["response"]["id"]

        # Mostrar checkout con MercadoPago
        # 🚀 Acá pasamos preference_id y public key al template
    return render_template(
        "checkout.html",
        preference_id=preference_id,
        PUBLIC_KEY=Config.MP_PUBLIC_KEY
    )

    

    return redirect(url_for("tienda.tienda"))

