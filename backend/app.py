"""
Prestige Motors — Luxury Car Resale Showroom
Flask backend with REST API, server-side UI, admin panel, and PayPal integration.
"""

import os
import uuid
from datetime import datetime
from functools import wraps

import requests
from flask import (Flask, jsonify, request, render_template,
                   abort, session, redirect, url_for, flash)

# ── Absolute paths so the app works from any working directory ───────────────
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_FOLDER   = os.path.join(BASE_DIR, "frontend", "static")

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
app.secret_key = os.environ.get("SECRET_KEY", "prestige-motors-secret-2024")

# ── Config ────────────────────────────────────────────────────────────────────
PAYPAL_SERVICE_URL = os.environ.get("PAYPAL_SERVICE_URL", "https://payment-w1qr.onrender.com")
PAYMENT_API_KEY    = os.environ.get("API_KEY", "")
ADMIN_USERNAME     = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD     = os.environ.get("ADMIN_PASSWORD", "prestige@admin2024")

# ── Jinja2 filters ────────────────────────────────────────────────────────────
@app.template_filter("price")
def price_filter(value):
    return f"${value:,.0f}"

@app.template_filter("commas")
def commas_filter(value):
    return f"{value:,}"

# ── Payment headers ───────────────────────────────────────────────────────────
def _payment_headers():
    return {
        "X-API-Key":     PAYMENT_API_KEY,
        "Authorization": f"Bearer {PAYMENT_API_KEY}",
        "Content-Type":  "application/json",
    }

# ── Admin auth decorator ──────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ════════════════════════════════════════════════════════════════════════════
# In-memory car store  (seeded with 9 luxury vehicles)
# ════════════════════════════════════════════════════════════════════════════

BRAND_GRADIENTS = {
    "Lamborghini": "linear-gradient(135deg,#0a0a0a 0%,#1a0800 50%,#ff6b00 100%)",
    "Ferrari":     "linear-gradient(135deg,#0a0000 0%,#2a0000 50%,#cc0000 100%)",
    "Porsche":     "linear-gradient(135deg,#0a0a0a 0%,#1a1a1a 50%,#8a8a8a 100%)",
    "McLaren":     "linear-gradient(135deg,#000a0a 0%,#001a1a 50%,#ff6600 100%)",
    "Bentley":     "linear-gradient(135deg,#000a05 0%,#001505 50%,#1a5c2a 100%)",
    "Rolls-Royce": "linear-gradient(135deg,#050510 0%,#0a0a20 50%,#c9a84c 100%)",
    "Aston Martin":"linear-gradient(135deg,#000a05 0%,#001a0f 50%,#005b37 100%)",
    "Mercedes-AMG":"linear-gradient(135deg,#0a0a0a 0%,#1a1a1a 50%,#c0c0c0 100%)",
    "BMW":         "linear-gradient(135deg,#00000a 0%,#00001a 50%,#1c69d4 100%)",
}
DEFAULT_GRADIENT = "linear-gradient(135deg,#0a0a0a,#1a1a2e)"

SEED_CARS = [
    {"id":"car-001","brand":"Lamborghini","model":"Huracán EVO","year":2023,"price":285000,"mileage":3200,"fuel_type":"Petrol","transmission":"Automatic","color":"Arancio Borealis","engine":"5.2L V10","power_hp":640,"torque_nm":600,"acceleration_0_100":2.9,"top_speed_kmh":325,"description":"The Huracán EVO represents the pinnacle of naturally aspirated V10 performance. With its all-wheel-drive system and LDVI predictive vehicle dynamics control, every corner becomes an event. This stunning Arancio Borealis example has covered just 3,200 miles from new and is presented in immaculate condition.","available":True,"sold":False},
    {"id":"car-002","brand":"Ferrari","model":"488 GTB","year":2022,"price":245000,"mileage":7800,"fuel_type":"Petrol","transmission":"Automatic","color":"Rosso Corsa","engine":"3.9L V8 Twin-Turbo","power_hp":660,"torque_nm":760,"acceleration_0_100":3.0,"top_speed_kmh":330,"description":"Ferrari's twin-turbocharged masterpiece. In classic Rosso Corsa with a tan leather interior, this single-owner car comes with full Ferrari service history.","available":True,"sold":False},
    {"id":"car-003","brand":"Porsche","model":"911 Turbo S","year":2023,"price":215000,"mileage":5100,"fuel_type":"Petrol","transmission":"Automatic","color":"GT Silver Metallic","engine":"3.8L Flat-6 Twin-Turbo","power_hp":650,"torque_nm":800,"acceleration_0_100":2.7,"top_speed_kmh":330,"description":"The definitive everyday supercar capable of 0-100 km/h in 2.7 seconds yet perfectly docile in traffic. Equipped with the Lightweight Sport Package and carbon ceramic brakes.","available":True,"sold":False},
    {"id":"car-004","brand":"McLaren","model":"720S","year":2022,"price":299000,"mileage":4600,"fuel_type":"Petrol","transmission":"Automatic","color":"Papaya Spark","engine":"4.0L V8 Twin-Turbo","power_hp":720,"torque_nm":770,"acceleration_0_100":2.9,"top_speed_kmh":341,"description":"The McLaren 720S pushes every boundary of what a road car can achieve. Carbon fibre MonoCell II chassis with active aerodynamics. In rare Papaya Spark with MSO black accents.","available":True,"sold":False},
    {"id":"car-005","brand":"Bentley","model":"Continental GT Speed","year":2023,"price":310000,"mileage":2800,"fuel_type":"Petrol","transmission":"Automatic","color":"Viridian","engine":"6.0L W12 Twin-Turbo","power_hp":659,"torque_nm":900,"acceleration_0_100":3.6,"top_speed_kmh":335,"description":"Bentley's most dynamic grand tourer blending handcrafted luxury with genuine supercar performance. Viridian with the Mulliner Driving Specification.","available":True,"sold":False},
    {"id":"car-006","brand":"Rolls-Royce","model":"Ghost Black Badge","year":2023,"price":420000,"mileage":1900,"fuel_type":"Petrol","transmission":"Automatic","color":"Black Diamond","engine":"6.75L V12 Twin-Turbo","power_hp":603,"torque_nm":900,"acceleration_0_100":4.8,"top_speed_kmh":250,"description":"The most powerful Ghost ever made. Darkened brightware, 21-inch forged alloys and 603 bhp twin-turbo V12. Starlight Headliner and bespoke Black Diamond exterior.","available":True,"sold":False},
    {"id":"car-007","brand":"Aston Martin","model":"DBS Superleggera","year":2022,"price":315000,"mileage":6200,"fuel_type":"Petrol","transmission":"Automatic","color":"Xenon Grey","engine":"5.2L V12 Twin-Turbo","power_hp":725,"torque_nm":900,"acceleration_0_100":3.4,"top_speed_kmh":340,"description":"Superleggera means super lightweight. Extensive carbon fibre throughout. Comes with full Aston Martin provenance and Q by Aston Martin options.","available":True,"sold":False},
    {"id":"car-008","brand":"Mercedes-AMG","model":"GT Black Series","year":2022,"price":340000,"mileage":8100,"fuel_type":"Petrol","transmission":"Automatic","color":"Selenite Grey Magno","engine":"4.0L V8 Twin-Turbo","power_hp":730,"torque_nm":800,"acceleration_0_100":3.2,"top_speed_kmh":325,"description":"The most powerful series-production AMG ever and the Nurburgring production car lap record holder. Flat-plane crank V8 borrowed from the AMG GT3 race car. Matte Selenite Grey Magno.","available":True,"sold":False},
    {"id":"car-009","brand":"BMW","model":"M8 Competition Coupe","year":2023,"price":148000,"mileage":9400,"fuel_type":"Petrol","transmission":"Automatic","color":"Frozen Marina Bay Blue","engine":"4.4L V8 Twin-Turbo","power_hp":625,"torque_nm":750,"acceleration_0_100":3.2,"top_speed_kmh":305,"description":"The ultimate expression of BMW performance and luxury. Individual Frozen Marina Bay Blue finish with full Merino leather interior package.","available":True,"sold":False},
]

cars: dict = {}

def _seed_cars():
    for car in SEED_CARS:
        c = car.copy()
        c["gradient"]   = BRAND_GRADIENTS.get(c["brand"], DEFAULT_GRADIENT)
        c["created_at"] = datetime.utcnow().isoformat()
        cars[c["id"]]   = c

_seed_cars()


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════

def _car_or_404(car_id):
    car = cars.get(car_id)
    if not car:
        abort(404, description=f"Car '{car_id}' not found.")
    return car

def _apply_filters(car_list):
    brand  = request.args.get("brand","").strip().lower()
    fuel   = request.args.get("fuel_type","").strip().lower()
    min_p  = request.args.get("min_price", type=int)
    max_p  = request.args.get("max_price", type=int)
    search = request.args.get("search","").strip().lower()
    result = car_list
    if brand:  result = [c for c in result if c["brand"].lower() == brand]
    if fuel:   result = [c for c in result if c["fuel_type"].lower() == fuel]
    if min_p:  result = [c for c in result if c["price"] >= min_p]
    if max_p:  result = [c for c in result if c["price"] <= max_p]
    if search: result = [c for c in result if search in c["brand"].lower()
                         or search in c["model"].lower() or search in c["color"].lower()]
    return result


# ════════════════════════════════════════════════════════════════════════════
# Public HTML routes
# ════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    car_list   = _apply_filters(list(cars.values()))
    brands     = sorted({c["brand"] for c in cars.values()})
    fuel_types = sorted({c["fuel_type"] for c in cars.values()})
    return render_template("index.html", cars=car_list, brands=brands,
        fuel_types=fuel_types, total=len(cars),
        available_count=sum(1 for c in cars.values() if c["available"]))

@app.route("/car/<string:car_id>")
def car_detail(car_id):
    car     = _car_or_404(car_id)
    similar = [c for c in cars.values() if c["brand"] == car["brand"] and c["id"] != car_id][:3]
    return render_template("car_detail.html", car=car, similar=similar)


# ════════════════════════════════════════════════════════════════════════════
# Admin — Auth
# ════════════════════════════════════════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        if (request.form.get("username","").strip() == ADMIN_USERNAME and
                request.form.get("password","") == ADMIN_PASSWORD):
            session["admin_logged_in"] = True
            session["admin_user"]      = ADMIN_USERNAME
            return redirect(url_for("admin_dashboard"))
        error = "Invalid username or password."
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ════════════════════════════════════════════════════════════════════════════
# Admin — Dashboard & Car Management
# ════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    car_list = list(cars.values())
    stats = {
        "total":     len(car_list),
        "available": sum(1 for c in car_list if c["available"] and not c["sold"]),
        "sold":      sum(1 for c in car_list if c["sold"]),
        "brands":    len({c["brand"] for c in car_list}),
    }
    return render_template("admin_dashboard.html", cars=car_list, stats=stats,
                           brands=sorted(BRAND_GRADIENTS.keys()))

@app.route("/admin/cars/add", methods=["POST"])
@login_required
def admin_add_car():
    data    = request.form
    required = ["brand","model","year","price","fuel_type","transmission","color"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        flash(f"Missing required fields: {', '.join(missing)}", "error")
        return redirect(url_for("admin_dashboard"))

    brand  = data["brand"].strip()
    car_id = str(uuid.uuid4())
    cars[car_id] = {
        "id": car_id, "brand": brand,
        "model":             data["model"].strip(),
        "year":              int(data["year"]),
        "price":             float(data["price"]),
        "mileage":           int(data.get("mileage") or 0),
        "fuel_type":         data["fuel_type"].strip(),
        "transmission":      data["transmission"].strip(),
        "color":             data["color"].strip(),
        "engine":            data.get("engine","").strip(),
        "power_hp":          int(data.get("power_hp") or 0),
        "torque_nm":         int(data.get("torque_nm") or 0),
        "acceleration_0_100":float(data.get("acceleration_0_100") or 0),
        "top_speed_kmh":     int(data.get("top_speed_kmh") or 0),
        "description":       data.get("description","").strip(),
        "available":         True,
        "sold":              False,
        "gradient":          BRAND_GRADIENTS.get(brand, DEFAULT_GRADIENT),
        "created_at":        datetime.utcnow().isoformat(),
    }
    flash(f"{data['year']} {brand} {data['model']} added to showroom!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/cars/<string:car_id>/delete", methods=["POST"])
@login_required
def admin_delete_car(car_id):
    _car_or_404(car_id)
    name = f"{cars[car_id]['brand']} {cars[car_id]['model']}"
    del cars[car_id]
    flash(f"{name} removed from showroom.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/cars/<string:car_id>/toggle", methods=["POST"])
@login_required
def admin_toggle_availability(car_id):
    car = _car_or_404(car_id)
    car["available"]  = not car["available"]
    car["updated_at"] = datetime.utcnow().isoformat()
    status = "available" if car["available"] else "hidden"
    flash(f"{car['brand']} {car['model']} is now {status}.", "success")
    return redirect(url_for("admin_dashboard"))


# ════════════════════════════════════════════════════════════════════════════
# Health & Info
# ════════════════════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return jsonify({"status":"healthy","timestamp":datetime.utcnow().isoformat()}), 200

@app.route("/info")
def info():
    return jsonify({"app":"Prestige Motors","version":os.environ.get("APP_VERSION","1.0.0"),
                    "total_cars":len(cars),"paypal_service":PAYPAL_SERVICE_URL}), 200


# ════════════════════════════════════════════════════════════════════════════
# Cars REST API
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/cars", methods=["GET"])
def get_cars():
    return jsonify(_apply_filters(list(cars.values()))), 200

@app.route("/api/cars/<string:car_id>", methods=["GET"])
def get_car(car_id):
    return jsonify(_car_or_404(car_id)), 200

@app.route("/api/cars", methods=["POST"])
def create_car():
    data    = request.get_json(force=True, silent=True) or {}
    required = ["brand","model","year","price","fuel_type","transmission","color"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error":f"Missing fields: {', '.join(missing)}"}), 400
    brand  = data["brand"].strip()
    car_id = str(uuid.uuid4())
    car = {"id":car_id,"brand":brand,"model":data["model"].strip(),
           "year":int(data["year"]),"price":float(data["price"]),
           "mileage":int(data.get("mileage",0)),"fuel_type":data["fuel_type"].strip(),
           "transmission":data["transmission"].strip(),"color":data["color"].strip(),
           "engine":data.get("engine",""),"power_hp":int(data.get("power_hp",0)),
           "torque_nm":int(data.get("torque_nm",0)),
           "acceleration_0_100":float(data.get("acceleration_0_100",0)),
           "top_speed_kmh":int(data.get("top_speed_kmh",0)),
           "description":data.get("description",""),"available":True,"sold":False,
           "gradient":BRAND_GRADIENTS.get(brand,DEFAULT_GRADIENT),
           "created_at":datetime.utcnow().isoformat()}
    cars[car_id] = car
    return jsonify(car), 201

@app.route("/api/cars/<string:car_id>", methods=["PUT"])
def update_car(car_id):
    car  = _car_or_404(car_id)
    data = request.get_json(force=True, silent=True) or {}
    for f in ["price","mileage","available","description","color","engine","power_hp","torque_nm"]:
        if f in data:
            car[f] = data[f]
    car["updated_at"] = datetime.utcnow().isoformat()
    return jsonify(car), 200

@app.route("/api/cars/<string:car_id>", methods=["DELETE"])
def delete_car(car_id):
    _car_or_404(car_id)
    del cars[car_id]
    return jsonify({"message":f"Car '{car_id}' removed."}), 200


# ════════════════════════════════════════════════════════════════════════════
# PayPal Payment
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/cars/<string:car_id>/purchase", methods=["POST"])
def purchase_car(car_id):
    car = _car_or_404(car_id)
    if car.get("sold"):      return jsonify({"error":"This car has already been sold."}), 409
    if not car.get("available"): return jsonify({"error":"This car is not available."}), 409
    data    = request.get_json(force=True, silent=True) or {}
    payload = {"item_id":car_id,"item_name":f"{car['year']} {car['brand']} {car['model']}",
               "amount":car["price"],"currency":"USD",
               "buyer_name":data.get("buyer_name",""),"buyer_email":data.get("buyer_email","")}
    try:
        resp = requests.post(f"{PAYPAL_SERVICE_URL}/create-payment",
                             json=payload, headers=_payment_headers(), timeout=10)
        resp.raise_for_status()
        pd = resp.json()
        if pd.get("status") == "approved":
            car.update({"sold":True,"available":False,"payment_id":pd.get("payment_id"),
                        "updated_at":datetime.utcnow().isoformat()})
        return jsonify({"car":car,"payment":pd}), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error":"Payment service unavailable."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error":"Payment service timed out."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error":f"Payment error: {e}"}), 502

@app.route("/api/payment/status/<string:payment_id>")
def payment_status(payment_id):
    try:
        resp = requests.get(f"{PAYPAL_SERVICE_URL}/payment-status/{payment_id}",
                            headers=_payment_headers(), timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error":f"Payment error: {e}"}), 502


# ════════════════════════════════════════════════════════════════════════════
# Error handlers
# ════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e): return jsonify({"error":str(e)}), 404

@app.errorhandler(400)
def bad_request(e): return jsonify({"error":str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)),
            debug=os.environ.get("FLASK_ENV")=="development")
