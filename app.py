from flask import Flask, request, render_template, url_for, session, redirect, jsonify
import os
import re
import psycopg2
from functions import *

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/activities.html", methods=["GET"])
def render_activities():
    activities = fetch_activities_from_database()
    if activities:
        return render_template("activities.html", activities=activities)
    else:
        return render_template("activities.html", message="Inga aktiviteter hittades.")
  
@app.route("/logincancellation.html", methods=["GET", "POST"])
def render_logincancellation():
    if request.method == "POST":
        booking_id = request.form.get("booking_id") # Sparar datan användaren skriver in på hemsidan i booking_id variabeln
        if booking_id:
            if delete_booking_from_database(booking_id):
                return render_template("logincancellation.html", message="Avbokat")
            else:
                return render_template("logincancellation.html", message="Hittade ingen bokning med det id")
        else:
            return render_template("logincancellation.html", message="Inget bokningsid angivet")
    else:
         return render_template("logincancellation.html")

@app.route("/loginboka.html", methods=["GET"])
def render_loginboka():
    return render_template("loginboka.html")
   
@app.route("/loginbookingconfirmed.html", methods=["POST", "GET"])
def de_login_booking():
    activity = request.form.get("activity")
    date  = request.form.get("date")
    time = request.form.get("time")
    email = request.form.get("email")
    phone = request.form.get("phone")
    input_data = (activity, date, time, email, phone)

    # Regex-mönster för att validera e-postadress
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    # Regex-mönster för att validera telefonnummer (exakt 10 siffror)
    phone_pattern = r"^\d{10}$"
    

    # Validera e-postadress
    if not re.match(email_pattern, request.form["email"]):
        return render_template("/loginboka.html", message="<span style='color: white;'>Felaktig e-postadress!</span>")

    # Validera telefonnummer
    if not re.match(phone_pattern, request.form["phone"]):
        return render_template("/loginboka.html", message="<span style='color: white;'>Felaktigt telefonnummer, fyll i 10 siffror!</span>")
    
    if input_data:
        conn = psycopg2.connect(**conn_details)
        cur = conn.cursor()
        cur.execute("SELECT * FROM bookinginformation WHERE activity = %s AND date = %s AND time = %s", (activity, date, time,))
        available_time = cur.fetchone()
        if available_time == None:
            pass
        else:
            return render_template("/loginboka.html", message="<span style='color: white;'>Tiden upptagen, välj en annan tid</span>")
    
    if input_data:
        if booking_confirmed(activity, date, time, email, phone):
            conn = psycopg2.connect(**conn_details)
            cur = conn.cursor()
            cur.execute("SELECT booking_id, date, time, price FROM user_bookings_view WHERE email = %s AND date = %s AND time = %s", (email, date, time,)) #Uppdaterad för att visa pris genom vår view.
            booking_info = cur.fetchone()
            cur.close()
            conn.close()
            if booking_info:
                booking_id = booking_info[0]
                booking_datetime = booking_info[1]
                booking_time = booking_info[2]
                booking_price = booking_info[3]
                return render_template("loginbookingconfirmed.html", message="Bokningsinformationen har lagts till.", booking_id=booking_id, booking_datetime=booking_datetime, booking_time=booking_time, booking_price=booking_price)
            else:
                return render_template("loginbookingconfirmed.html", message="Ingen bokning hittades med den angivna e-postadressen.")
        else:
            return render_template("loginbookingconfirmed.html", message="Det gick inte att lägga till bokningsinformationen.")
    else:
        return render_template("loginbookingconfirmed.html", message="Nödvändiga uppgifter saknas.")  # Vi når aldrig denna???    

@app.route("/loginbookingfail.html", methods=["POST", "GET"])
def render_loginbookingfail():
    return render_template("loginbookingfail.html")

@app.route("/bookings.html", methods=["GET", "POST"])
def get_user_bookings():
    # Här kan du använda sessionsinformationen eller någon form av autentisering för att identifiera den aktuella användaren
    # Antag att användarens e-postadress är lagrad i sessionsvariabeln 'email'

    if "email" in session:  # Förutsatt att du har lagrat användarens e-postadress i sessionsvariabeln 'email'
        email = session["email"]
        user_bookings = fetch_user_bookings_from_database(email)
        if user_bookings is not None:
            return render_template("bookings.html", bookings=user_bookings)
        else:
            return render_template("bookings.html", message="Inga bokningar hittades för den aktuella användaren.")
    else:
        return jsonify({"error": "Användaren är inte inloggad"}), 401  # 401 Unauthorized om användaren inte är inloggad




if __name__ == "__main__":
    app.run(debug=True)   