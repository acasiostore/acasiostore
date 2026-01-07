from flask import Flask, render_template, abort, request, flash, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# SMTP Configuration - Using environment variables for Render
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')  # Empty default
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # EMPTY DEFAULT - NO PASSWORD HERE!
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')      # Empty default
# Load data files
with open("data/categories.json") as f:
    categories = json.load(f)
with open("data/products.json") as f:
    products = json.load(f)
with open("data/generic_categories.json") as f:
    generic_categories = json.load(f)

# Load best_sellers.json if it exists
try:
    with open("data/best_sellers.json") as f:
        best_sellers = json.load(f)
    print(f"Loaded {len(best_sellers)} best sellers")
except FileNotFoundError:
    best_sellers = []

# Shopping cart in session
@app.before_request
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = {}


# ----- Helper Functions -----
def get_category(slug):
    for c in categories:
        if c["slug"] == slug:
            return c
    return None


def get_generic_category(slug):
    for c in generic_categories:
        if c["slug"] == slug:
            return c
    return None


def get_product(slug):
    for p in products:
        if p["slug"] == slug:
            return p
    return None


def calculate_cart_total():
    total = 0
    cart = session.get('cart', {})
    for slug, item in cart.items():
        product = get_product(slug)
        if product:
            price = product["price"]
            if product.get("sale", {}).get("on_sale"):
                discount = product["sale"]["discount_percent"]
                price = price * (1 - discount / 100)
            total += price * item['quantity']
    return total


def send_email_via_smtp(to_email, subject, html_content):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"A CASIO STORE.pk <{SMTP_USERNAME}>"
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Connect to SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def send_order_emails_smtp(customer_info, cart_items, total_amount):
    """Send order confirmation emails to customer and admin"""
    try:
        # Prepare order items HTML
        items_html = ""
        for slug, item in cart_items.items():
            product = get_product(slug)
            if product:
                price = product["price"]
                if product.get("sale", {}).get("on_sale"):
                    discount = product["sale"]["discount_percent"]
                    price = price * (1 - discount / 100)

                items_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{product['name']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{product['currency']}{price:,.0f}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{product['currency']}{price * item['quantity']:,.0f}</td>
                </tr>
                """

        # HTML for CUSTOMER email
        customer_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                .order-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Thank You for Your Order!</h1>
                </div>

                <p>Dear <strong>{customer_info['name']}</strong>,</p>
                <p>Your order has been received successfully. We will process it within 24 hours and contact you for confirmation.</p>

                <h3>Order Summary:</h3>
                <table class="order-table">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; text-align: left;">Product</th>
                            <th style="padding: 10px; text-align: center;">Qty</th>
                            <th style="padding: 10px; text-align: right;">Price</th>
                            <th style="padding: 10px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                        <tr>
                            <td colspan="3" style="padding: 10px; text-align: right; font-weight: bold;">Total Amount:</td>
                            <td style="padding: 10px; text-align: right; font-weight: bold;">{total_amount:,.0f}</td>
                        </tr>
                    </tbody>
                </table>

                <h3>Customer Information:</h3>
                <ul>
                    <li><strong>Name:</strong> {customer_info['name']}</li>
                    <li><strong>Email:</strong> {customer_info['email']}</li>
                    <li><strong>Phone:</strong> {customer_info['phone1']}</li>
                    <li><strong>Address:</strong> {customer_info['address']}</li>
                </ul>

                <p><strong>Payment Method:</strong> Cash on Delivery</p>
                <p><strong>Estimated Delivery:</strong> 3-7 working days</p>

                <p>We will contact you shortly for order confirmation and delivery details.</p>
                <p>Thank you for shopping with A CASIO STORE.pk!</p>

                <div class="footer">
                    <p>A CASIO STORE.pk<br>
                    Phone: +92 346 2738961<br>
                    Email: acasiostore@gmail.com</p>
                </div>
            </div>
        </body>
        </html>
        """

        # HTML for ADMIN email
        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .alert {{ background-color: #d4edda; color: #155724; padding: 15px; border-radius: 5px; }}
                .order-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert">
                    <h2>🛒 New Order Received!</h2>
                    <p>Order placed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <h3>Customer Information:</h3>
                <ul>
                    <li><strong>Name:</strong> {customer_info['name']}</li>
                    <li><strong>Email:</strong> {customer_info['email']}</li>
                    <li><strong>Phone 1:</strong> {customer_info['phone1']}</li>
                    <li><strong>Phone 2:</strong> {customer_info['phone2']}</li>
                    <li><strong>Address:</strong> {customer_info['address']}</li>
                </ul>

                <h3>Order Details:</h3>
                <table class="order-table">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; text-align: left;">Product</th>
                            <th style="padding: 10px; text-align: center;">Qty</th>
                            <th style="padding: 10px; text-align: right;">Price</th>
                            <th style="padding: 10px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                        <tr>
                            <td colspan="3" style="padding: 10px; text-align: right; font-weight: bold;">Total Amount:</td>
                            <td style="padding: 10px; text-align: right; font-weight: bold;">{total_amount:,.0f}</td>
                        </tr>
                    </tbody>
                </table>

                <p><strong>Action Required:</strong> Contact customer within 24 hours to confirm order.</p>

                <hr>
                <p><small>This is an automated email from A CASIO STORE.pk order system.</small></p>
            </div>
        </body>
        </html>
        """

        # Send emails
        customer_sent = send_email_via_smtp(
            customer_info['email'],
            "Order Confirmation - A CASIO STORE.pk",
            customer_html
        )

        admin_sent = send_email_via_smtp(
            ADMIN_EMAIL,
            f"🛒 New Order from {customer_info['name']}",
            admin_html
        )

        if customer_sent and admin_sent:
            print("✅ Both emails sent successfully via SMTP")
            return True
        elif admin_sent:
            print("⚠️ Admin email sent, but customer email failed")
            return False
        else:
            print("❌ Failed to send emails")
            return False

    except Exception as e:
        print(f"❌ Error in email sending process: {e}")
        return False


# ----- Routes -----
@app.route("/")
def home():
    featured_products = []
    for p in products[:12]:
        prod = p.copy()
        if prod.get("sale", {}).get("on_sale"):
            discount = prod["sale"]["discount_percent"]
            prod["sale"]["discounted_price"] = prod["price"] * (1 - discount / 100)
        featured_products.append(prod)

    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

    return render_template(
        "home.html",
        categories=categories,
        featured_products=featured_products,
        best_sellers=best_sellers,
        cart_count=cart_count,
        get_product=get_product
    )


@app.route("/category/<slug>")
def category_page(slug):
    category = get_category(slug)
    if not category:
        abort(404)
    cat_products = [p for p in products if p["category"] == slug]
    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

    return render_template("category.html",
                           category=category,
                           products=cat_products,
                           cart_count=cart_count)


@app.route("/product/<slug>")
def product_details(slug):
    product = get_product(slug)
    if not product:
        abort(404)

    sale_price = None
    if product.get("sale", {}).get("on_sale"):
        discount = product["sale"]["discount_percent"]
        sale_price = product["price"] * (1 - discount / 100)

    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

    return render_template(
        "details.html",
        product=product,
        sale_price=sale_price,
        cart_count=cart_count
    )


@app.route("/generic/<slug>")
def generic_category(slug):
    cat = get_generic_category(slug)
    if not cat:
        abort(404)

    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

    return render_template(
        "category_generic.html",
        title=cat["title"],
        description=cat["description"],
        products=cat["products"],
        cart_count=cart_count
    )


@app.route("/sale_page")
def sale_page():
    sale_products = []
    for p in products:
        if p.get("sale") and p["sale"].get("on_sale"):
            prod = p.copy()
            discount = prod["sale"]["discount_percent"]
            prod["sale"]["discounted_price"] = prod["price"] * (1 - discount / 100)
            sale_products.append(prod)

    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

    return render_template("sale.html",
                           products=sale_products,
                           cart_count=cart_count)


@app.route("/warranty")
def warranty():
    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())
    return render_template("warranty.html", cart_count=cart_count)


# Cart Routes
@app.route("/add-to-cart/<slug>", methods=['POST'])
def add_to_cart(slug):
    product = get_product(slug)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})

    cart = session.get('cart', {})
    quantity = int(request.form.get('quantity', 1))

    if slug in cart:
        cart[slug]['quantity'] += quantity
    else:
        cart[slug] = {
            'quantity': quantity,
            'added_at': datetime.now().isoformat()
        }

    session['cart'] = cart
    session.modified = True

    cart_count = sum(item['quantity'] for item in cart.values())

    return jsonify({
        'success': True,
        'message': f'{product["name"]} added to cart',
        'cart_count': cart_count
    })


@app.route("/update-cart/<slug>", methods=['POST'])
def update_cart(slug):
    cart = session.get('cart', {})
    quantity = int(request.form.get('quantity', 1))

    if slug in cart:
        if quantity <= 0:
            del cart[slug]
        else:
            cart[slug]['quantity'] = quantity
        session['cart'] = cart
        session.modified = True

    return jsonify({
        'success': True,
        'cart_count': sum(item['quantity'] for item in cart.values())
    })


@app.route("/remove-from-cart/<slug>", methods=['POST'])
def remove_from_cart(slug):
    cart = session.get('cart', {})
    if slug in cart:
        del cart[slug]
        session['cart'] = cart
        session.modified = True

    return jsonify({
        'success': True,
        'cart_count': sum(item['quantity'] for item in cart.values())
    })


@app.route("/cart")
def view_cart():
    cart_items = []
    cart = session.get('cart', {})
    total = 0

    for slug, item in cart.items():
        product = get_product(slug)
        if product:
            price = product["price"]
            if product.get("sale", {}).get("on_sale"):
                discount = product["sale"]["discount_percent"]
                price = price * (1 - discount / 100)

            item_total = price * item['quantity']
            total += item_total

            cart_items.append({
                'slug': slug,
                'product': product,
                'quantity': item['quantity'],
                'price': price,
                'total': item_total
            })

    cart_count = sum(item['quantity'] for item in cart.values())

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total,
        cart_count=cart_count,
        get_product=get_product
    )


@app.route("/checkout", methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        customer_info = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone1': request.form.get('phone1'),
            'phone2': request.form.get('phone2'),
            'address': request.form.get('address')
        }

        cart = session.get('cart', {})
        total = calculate_cart_total()

        # Send emails using SMTP
        if send_order_emails_smtp(customer_info, cart, total):
            session['cart'] = {}
            session.modified = True

            flash('Order placed successfully! Confirmation email has been sent.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Order received! We will contact you shortly. (Email confirmation pending)', 'info')
            # Still clear cart even if email fails
            session['cart'] = {}
            session.modified = True
            return redirect(url_for('home'))

    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('view_cart'))

    total = calculate_cart_total()
    cart_count = sum(item['quantity'] for item in cart.values())

    return render_template(
        "checkout.html",
        total=total,
        cart_count=cart_count,
        get_product=get_product
    )


@app.route("/cart-count")
def cart_count():
    count = sum(item['quantity'] for item in session.get('cart', {}).values())
    return jsonify({'count': count})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
