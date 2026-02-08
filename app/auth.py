import random
from datetime import datetime, timedelta

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db, now_iso


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def login():
    return render_template("login.html")


@auth_bp.route("/dashboard")
def dashboard():
    user_phone = session.get("user_phone")
    if not user_phone:
        return redirect(url_for("auth.login"))
    db = get_db()
    medicines = db.execute(
        "SELECT id, name, price, expiry_date, stock_quantity FROM medicines ORDER BY name"
    ).fetchall()
    message = request.args.get("message")
    error = request.args.get("error")
    return render_template(
        "dashboard.html",
        phone=user_phone,
        medicines=medicines,
        message=message,
        error=error,
    )


@auth_bp.route("/auth/request-otp", methods=["POST"])
def request_otp():
    phone = request.form.get("phone", "").strip()
    if not phone:
        return render_template("login.html", error="Please enter your phone number.")

    db = get_db()
    latest = db.execute(
        "SELECT * FROM otp_requests WHERE phone = ? ORDER BY id DESC LIMIT 1",
        (phone,),
    ).fetchone()

    if latest:
        expires_at = datetime.fromisoformat(latest["expires_at"])
        if datetime.utcnow() < expires_at and latest["verified"] == 0:
            remaining = int((expires_at - datetime.utcnow()).total_seconds())
            return render_template(
                "login.html",
                error=f"OTP already sent. Please wait {remaining} seconds to resend.",
                phone=phone,
            )

    otp_code = f"{random.randint(0, 9999):04d}"
    otp_hash = generate_password_hash(otp_code)

    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(seconds=current_app.config["OTP_EXPIRY_SECONDS"])

    db.execute(
        """
        INSERT INTO otp_requests (phone, otp_hash, created_at, expires_at, attempts, verified)
        VALUES (?, ?, ?, ?, 0, 0)
        """,
        (phone, otp_hash, created_at.isoformat(), expires_at.isoformat()),
    )
    db.commit()

    print(f"[MediSmart OTP Demo] OTP for {phone}: {otp_code}")

    return render_template(
        "login.html",
        info="OTP sent successfully (simulated). Check server console.",
        phone=phone,
    )


@auth_bp.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    phone = request.form.get("phone", "").strip()
    otp = request.form.get("otp", "").strip()

    if not phone or not otp:
        return render_template("login.html", error="Phone and OTP are required.", phone=phone)

    db = get_db()
    latest = db.execute(
        "SELECT * FROM otp_requests WHERE phone = ? ORDER BY id DESC LIMIT 1",
        (phone,),
    ).fetchone()

    if not latest:
        return render_template("login.html", error="No OTP request found.", phone=phone)

    expires_at = datetime.fromisoformat(latest["expires_at"])
    if datetime.utcnow() > expires_at:
        return render_template("login.html", error="OTP expired. Please request a new one.", phone=phone)

    if latest["attempts"] >= current_app.config["OTP_MAX_ATTEMPTS"]:
        return render_template(
            "login.html",
            error="Maximum verification attempts exceeded. Please request a new OTP.",
            phone=phone,
        )

    if not check_password_hash(latest["otp_hash"], otp):
        db.execute(
            "UPDATE otp_requests SET attempts = attempts + 1 WHERE id = ?",
            (latest["id"],),
        )
        db.commit()
        remaining_attempts = current_app.config["OTP_MAX_ATTEMPTS"] - (latest["attempts"] + 1)
        return render_template(
            "login.html",
            error=f"Invalid OTP. {remaining_attempts} attempts remaining.",
            phone=phone,
        )

    db.execute(
        "UPDATE otp_requests SET verified = 1 WHERE id = ?",
        (latest["id"],),
    )

    user = db.execute("SELECT * FROM users WHERE phone_number = ?", (phone,)).fetchone()
    if not user:
        db.execute(
            "INSERT INTO users (phone_number, created_at) VALUES (?, ?)",
            (phone, now_iso()),
        )

    db.commit()

    session["user_phone"] = phone

    return redirect(url_for("auth.dashboard"))


@auth_bp.route("/orders/place", methods=["POST"])
def place_order():
    user_phone = session.get("user_phone")
    if not user_phone:
        return redirect(url_for("auth.login"))

    medicine_id = request.form.get("medicine_id", "").strip()
    quantity = request.form.get("quantity", "").strip()
    payment_mode = request.form.get("payment_mode", "").strip()

    if not medicine_id or not quantity or not payment_mode:
        return redirect(url_for("auth.dashboard", error="Please complete all order fields."))

    try:
        quantity_value = int(quantity)
    except ValueError:
        return redirect(url_for("auth.dashboard", error="Quantity must be a whole number."))

    if quantity_value <= 0:
        return redirect(url_for("auth.dashboard", error="Quantity must be at least 1."))

    if payment_mode not in {"COD", "UPI"}:
        return redirect(url_for("auth.dashboard", error="Invalid payment mode selected."))

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE phone_number = ?", (user_phone,)).fetchone()
    if not user:
        return redirect(url_for("auth.dashboard", error="User record not found. Please login again."))

    medicine = db.execute(
        "SELECT id, stock_quantity FROM medicines WHERE id = ?",
        (medicine_id,),
    ).fetchone()
    if not medicine:
        return redirect(url_for("auth.dashboard", error="Selected medicine not found."))

    if quantity_value > medicine["stock_quantity"]:
        return redirect(
            url_for("auth.dashboard", error="Not enough stock available for that quantity.")
        )

    db.execute(
        """
        INSERT INTO orders (user_id, medicine_id, quantity, payment_mode, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user["id"], medicine["id"], quantity_value, payment_mode, "Placed", now_iso()),
    )
    db.commit()

    return redirect(url_for("auth.dashboard", message="Order placed successfully."))


@auth_bp.route("/auth/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
