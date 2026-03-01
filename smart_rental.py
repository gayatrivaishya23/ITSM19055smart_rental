from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import db, User, Room, Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rental.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- HOME ----------------
@app.route("/")
def home():
    page = request.args.get('page', 1, type=int)
    rooms = Room.query.paginate(page=page, per_page=5)
    return render_template("rooms.html", rooms=rooms)

# ---------------- SEARCH ----------------
@app.route("/search_rooms")
def search_rooms():
    location = request.args.get("location", "")
    min_price = request.args.get("min", 0, type=int)
    max_price = request.args.get("max", 100000, type=int)

    rooms = Room.query.filter(
        Room.location.ilike(f"%{location}%"),
        Room.price.between(min_price, max_price)
    ).all()

    return jsonify([{
        "id": r.id,
        "title": r.title,
        "location": r.location,
        "price": r.price,
        "price_type": r.price_type
    } for r in rooms])

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("register.html", error="Username already exists.")

        hashed_password = generate_password_hash(request.form["password"])
        role = request.form.get("role", "tenant")

        user = User(username=username, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role in ["owner", "superowner"]:
        rooms = Room.query.filter_by(owner_id=current_user.id).all()
        tenants = User.query.filter(User.role=="tenant").all()
        bookings = Booking.query.all()
        return render_template("owner_dashboard.html", rooms=rooms, tenants=tenants, bookings=bookings)
    else:
        bookings = Booking.query.filter_by(user_id=current_user.id).all()
        return render_template("tenant_dashboard.html", bookings=bookings)

# ---------------- ADD ROOM ----------------
@app.route("/add_room", methods=["GET","POST"])
@login_required
def add_room():
    # Owner ya superowner dono room add kar sakte hain
    if current_user.role not in ["owner", "superowner"]:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        image = request.files.get("image")
        filename = image.filename if image else 'default.jpg'
        if image:
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        price = float(request.form["price"])
        price_type = request.form.get("price_type", "per_day")

        room = Room(
            title=request.form["title"],
            location=request.form["location"],
            price=price,
            price_type=price_type,
            image=filename,
            owner_id=current_user.id
        )
        db.session.add(room)
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("add_room.html")

# ---------------- EDIT ROOM ----------------
@app.route("/edit_room/<int:id>", methods=["GET", "POST"])
@login_required
def edit_room(id):
    room = Room.query.get_or_404(id)
    if room.owner_id != current_user.id and current_user.role != "superowner":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        room.title = request.form["title"]
        room.location = request.form["location"]
        room.price = float(request.form["price"])
        room.price_type = request.form.get("price_type", "per_day")

        image = request.files.get("image")
        if image:
            filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            room.image = filename

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_room.html", room=room)

# ---------------- DELETE ROOM ----------------
@app.route("/delete_room/<int:id>")
@login_required
def delete_room(id):
    room = Room.query.get_or_404(id)
    # Sirf room ka owner ya superowner delete kar sakta hai
    if room.owner_id == current_user.id or current_user.role == "superowner":
        db.session.delete(room)
        db.session.commit()
    return redirect(url_for("dashboard"))# ---------------- BOOK ----------------
@app.route("/book/<int:room_id>")
@login_required
def book(room_id):
    # Redirect to payment page
    return redirect(url_for("payment", room_id=room_id))

# ---------------- PAYMENT ----------------
@app.route("/payment/<int:room_id>", methods=["GET", "POST"])
@login_required
def payment(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == "POST":
        # Mark room as booked
        room.is_booked = True
        booking = Booking(room_id=room.id, user_id=current_user.id)
        db.session.add(booking)
        db.session.commit()
        return render_template("payment_success.html")
    return render_template("payment.html", room=room)
# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # superowner
        if not User.query.filter_by(username="superowner").first():
            super_owner = User(username="superowner", password=generate_password_hash("superpassword"), role="superowner")
            db.session.add(super_owner)
            db.session.commit()

    # app.run(debug=True)  # ❌ Commented for Render
