from smart_rental import db, app
from sqlalchemy import text

with app.app_context():
    # 1️⃣ Add 'image' column to 'room' table
    try:
        db.session.execute(text('ALTER TABLE room ADD COLUMN image TEXT'))
        db.session.commit()
        print("✅ room.image column added successfully")
    except Exception as e:
        print("ℹ️ room.image column may already exist or error:", e)

    # 2️⃣ Add 'price_type' column to 'room' table (per day / per month)
    try:
        db.session.execute(text("ALTER TABLE room ADD COLUMN price_type TEXT DEFAULT 'per day'"))
        db.session.commit()
        print("✅ room.price_type column added successfully")
    except Exception as e:
        print("ℹ️ room.price_type column may already exist or error:", e)

    # 3️⃣ Add 'status' column to 'booking' table
    try:
        db.session.execute(text("ALTER TABLE booking ADD COLUMN status TEXT DEFAULT 'Booked'"))
        db.session.commit()
        print("✅ booking.status column added successfully")
    except Exception as e:
        print("ℹ️ booking.status column may already exist or error:", e)