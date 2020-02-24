import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from math import trunc
import datetime


from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///taxes.db")


@app.route("/")
@login_required
def index():
    data = db.execute("SELECT * FROM progress WHERE user_id=:user", user=session["user_id"])[0]
    return render_template("index.html", data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Username needed", 400)
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Fill in your password", 400)
        if not (request.form.get("password") == request.form.get("confirmation")):
            return apology("Passwords do not match", 400)
        else:
            result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                                username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
            if not result:
                return apology("Duplicate username")
        username = db.execute("SELECT user_id FROM users WHERE username=:username",
                              username=request.form.get("username"))[0]["user_id"]
        db.execute("INSERT INTO progress (user_id) VALUES (:user)", user=username)
        return redirect("/")
    else:
        return render_template("register.html")


# Change Password
@app.route("/pwchange", methods=["GET", "POST"])
@login_required
def pwchange():
    if request.method == "POST":
        # Standard definitions and check
        current = request.form.get("password")
        new = request.form.get("newpassword")
        confirm = request.form.get("confirmation")
        previous = db.execute("SELECT hash FROM users WHERE id = :id", id=session["user_id"])
        fields = [current, new, confirm]

        if exist(fields) == False:
            return apology("Fill all fields")
        if not check_password_hash(previous[0]["hash"], current):
            return apology("Wrong Password", 400)
        if new != confirm:
            return apology("New Passwords Do Not Match", 400)

        change = db.execute("UPDATE users SET hash = :hash WHERE user_id = :id",
                            hash=generate_password_hash(new), id=session["user_id"])
        if not change:
            return apology("Update Failed", 400)
        return redirect("/logout")
    else:
        return render_template("pwchange.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = request.args.get("username")
    unavaliable = db.execute("SELECT username FROM users")
    if not(len(username)) > 0:
        return jsonify(False)
    for unavaliable in unavaliable:
        if username == unavaliable["username"]:
            return jsonify(False)
    return jsonify(True)


@app.route("/personal", methods=["GET", "POST"])
@login_required
def personal():
    if request.method == "POST":
        """Definitions and checks"""
        first = request.form.get("first")
        middle = request.form.get("middle")
        last = request.form.get("last")
        age = request.form.get("age")
        gender = request.form.get("gender")
        citizenship = request.form.get("citizenship")
        fields = [first, last, age, gender, citizenship]
        number = [age]

        if exist(fields) == False:
            return apology("Fill all fields")
        if posinteger(number) == False:
            return apology("Values should be 0 or positive")

        """Fill database"""
        insert = db.execute("INSERT INTO personal (user_id, first, middle, last, age, gender, citizenship) VALUES (:user, :first, :middle, :last, :age, :gender, :citizenship)",
                            user=session["user_id"], age=age, gender=gender, citizenship=citizenship, first=first, middle=middle, last=last)
        update = db.execute("UPDATE progress SET personal = 1")
        if not insert or not update:
            return apology("Update Failed")
        return redirect("/")

    else:
        progress = db.execute("SELECT personal FROM progress WHERE user_id=:user", user=session["user_id"])[0]['personal']
        if progress == 1:
            data = db.execute("SELECT * FROM personal WHERE user_id=:user", user=session["user_id"])[0]
        else:
            data = None
        return render_template("personal.html", progress=progress, data=data)


@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    if request.method == "POST":
        """Definitions and checks"""
        ordinary = request.form.get("ordinary")
        ordinaryvalue = request.form.get("ordinaryvalue")
        special = request.form.get("special")
        specialvalue = request.form.get("specialvalue")
        director = request.form.get("director")
        directorvalue = request.form.get("directorvalue")
        expense = request.form.get("expense")
        expensevalue = request.form.get("expensevalue")
        other = request.form.get("other")
        othervalue = request.form.get("othervalue")
        fields = [ordinary, ordinaryvalue, special, specialvalue, director, directorvalue, expense, expensevalue, other, othervalue]
        number = [ordinaryvalue, specialvalue, directorvalue, expensevalue, othervalue]

        if exist(fields) == False:
            return apology("Fill all fields")
        if posinteger(number) == False:
            return apology("Values should be 0 or positive")

        """Insert into DB"""
        insert = db.execute("INSERT INTO income (user_id, ordinary, ordinaryvalue, special, specialvalue, director, directorvalue, expense, expensevalue, other, othervalue) VALUES (:user, :ordinary, :ordinaryvalue, :special, :specialvalue, :director, :directorvalue, :expense, :expensevalue, :other, :othervalue)",
                            user=session["user_id"], ordinary=ordinary, ordinaryvalue=ordinaryvalue, special=special, specialvalue=specialvalue, director=director, directorvalue=directorvalue, expense=expense, expensevalue=expensevalue, other=other, othervalue=othervalue)
        update = db.execute("UPDATE progress SET income=1 WHERE user_id=:user", user=session["user_id"])
        if not insert or not update:
            return apology("Update failed")

        return redirect("/")

    else:
        progress = db.execute("SELECT income FROM progress WHERE user_id=:user", user=session["user_id"])[0]['income']
        if progress == 1:
            data = db.execute("SELECT * FROM income WHERE user_id=:user", user=session["user_id"])[0]
        else:
            data = None
        return render_template("income.html", data=data, progress=progress)


@app.route("/asset", methods=["GET", "POST"])
@login_required
def asset():
    if request.method == "POST":
        occupied = request.form.get("occupied")
        nonoccupied = request.form.get("nonoccupied")
        nonresidential = request.form.get("nonresidential")
        petrol = request.form.get("petrol")
        disel = request.form.get("disel")
        rating = request.form.get("rating")
        electric = request.form.get("electric")
        fields = [occupied, nonoccupied, nonresidential, petrol, disel, rating, electric]
        number = [occupied, nonoccupied, nonresidential, petrol, disel]

        if exist(fields) == False:
            return apology("Fill all fields")
        if posinteger(number) == False:
            return apology("Values should be 0 or positive")
        if posfloat(number) == False:
            return apology("Values should be 0 or positive")
        if (int(disel) == 0 and int(rating) != 0) or (int(disel) != 0 and int(rating) == 0):
            return apology("Fill in valid disel cc or rating")
        electric = "{0:.2f}".format(float(electric))

        insert = db.execute("INSERT INTO asset (user_id, occupied, nonoccupied, nonresidential, petrol, disel, rating, electric) VALUES (:user, :occupied, :nonoccupied, :nonresidential, :petrol, :disel, :rating, :electric)",
                            user=session["user_id"], occupied=occupied, nonoccupied=nonoccupied, nonresidential=nonresidential, petrol=petrol, disel=disel, rating=rating, electric=electric)
        update = db.execute("UPDATE progress SET asset = 1")
        if not insert or not update:
            return apology("Update Failed")
        return redirect("/")
    else:
        progress = db.execute("SELECT asset FROM progress WHERE user_id=:user", user=session["user_id"])[0]['asset']
        if progress == 1:
            data = db.execute("SELECT * FROM asset WHERE user_id=:user", user=session["user_id"])[0]
        else:
            data = None
        return render_template("asset.html", data=data, progress=progress)


@app.route("/deduction", methods=["GET", "POST"])
@login_required
def deduction():
    if request.method == "POST":
        deduction = request.form.get("deduction")
        donation = request.form.get("deduction")
        fields = [deduction, donation]
        number = [deduction, donation]

        if exist(fields) == False:
            return apology("Fill all fields")
        if posinteger(number) == False:
            return apology("Values should be 0 or positive")
        insert = db.execute("INSERT INTO deduction (user_id, deduction, donation) VALUES (:user, :deduction, :donation)",
                            user=session["user_id"], deduction=deduction, donation=donation)
        update = db.execute("UPDATE progress SET deduction = 1")
        if not insert or not update:
            return apology("Update Failed")
        return redirect("/")
    else:
        progress = db.execute("SELECT deduction FROM progress WHERE user_id=:user", user=session["user_id"])[0]['deduction']
        if progress == 1:
            data = db.execute("SELECT * FROM deduction WHERE user_id=:user", user=session["user_id"])[0]
        else:
            data = None
        return render_template("deduction.html", data=data, progress=progress)


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    x = datetime.datetime.now()
    date = x.strftime("%d") + " " + x.strftime("%b") + " " + x.strftime("%Y")

    personal = db.execute("SELECT * FROM personal WHERE user_id=:user", user=session["user_id"])[0]
    income = db.execute("SELECT * FROM income WHERE user_id=:user", user=session["user_id"])[0]
    asset = db.execute("SELECT * FROM asset WHERE user_id=:user", user=session["user_id"])[0]
    deduction = db.execute("SELECT * FROM deduction WHERE user_id=:user", user=session["user_id"])[0]

    occupied = occupiedtax(asset["occupied"])
    nonoccupied = nonoccupiedtax(asset["nonoccupied"])
    nonresidential = nonresidentialtax(asset["nonresidential"])
    petrol = petroltax(asset["petrol"])
    disel = diseltax(asset["disel"], asset["rating"])
    electric = electrictax(asset["electric"])

    if personal["citizenship"] == 0:
        incometax = local(income["ordinaryvalue"], income["specialvalue"], income["directorvalue"],
                          income["expensevalue"], income["othervalue"], deduction["deduction"], deduction["donation"])
    elif personal["citizenship"] == 1:
        incometax = foreign(income["ordinaryvalue"], income["specialvalue"], income["directorvalue"],
                            income["expensevalue"], income["othervalue"], deduction["deduction"], deduction["donation"])

    return render_template("report.html", occupied=occupied, nonoccupied=nonoccupied, nonresidential=nonresidential, petrol=petrol, disel=disel, electric=electric,
                           incometax=incometax, personal=personal, income=income, asset=asset, deduction=deduction, date=date)


@app.route("/clear", methods=["GET"])
@login_required
def clear():
    """Receive section to remove and remove from database"""
    section = request.args.get("section")
    db.execute("DELETE FROM :section WHERE user_id=:user", section=section, user=session['user_id'])
    db.execute("UPDATE progress SET :section=0 WHERE user_id=:user", section=section, user=session['user_id'])
    return jsonify(True)


@app.route("/wipe", methods=["GET", "POST"])
@login_required
def wipe():
    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("wipe.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def exist(fields):
    for item in fields:
        if not item:
            return False
            break
    return True


def posinteger(number):
    for item in number:
        if int(item) < 0:
            return False
            break


def posfloat(number):
    for item in number:
        if float(item) < 0:
            return False
            break


def occupiedtax(annual):
    if annual <= 8000:
        return 0

    if annual <= 55000:
        return (annual-8000)*0.04

    if annual >= 130000:
        return (9380 + (annual-130000) * 0.16)

    if annual > 55000 and annual < 130000:
        tax = 1880
        annual = annual - 55000
        i = trunc(annual/15000)
        rate = 0.06
        j = 0
        while j < i:
            tax = tax + 15000 * rate
            rate += + 0.02
            annual -= 15000
            if j == i-1:
                tax = tax + annual * rate
            j += 1
        return tax


def nonoccupiedtax(annual):
    if annual <= 30000:
        return (annual * 0.10)
    if annual >= 90000:
        return (12000 + (annual-90000)*0.20)

    if annual > 30000 and annual < 90000:
        tax = 3000
        annual = annual - 30000
        i = trunc(annual/15000)
        rate = 0.12
        j = 0
        while j < i:
            tax = tax + 15000 * rate
            rate += + 0.02
            annual -= 15000
            if j == i-1:
                tax = tax + annual * rate
            j += 1
        return tax


def nonresidentialtax(annual):
    return (annual*0.10)


def petroltax(ec):
    if ec <= 600:
        return (200*1.564)
    if ec <= 1000:
        return (200 + 0.125*(ec-600))*1.564
    if ec <= 1600:
        return (250 + 0.375*(ec-1000))*1.564
    if ec <= 3000:
        return (475 + 0.75*(ec-1600))*1.564
    if ec > 3000:
        return (1525+(ec-3000))*1.564


def diseltax(ec, rating):
    if ec <= 600:
        tax = (200*1.564)
    elif ec <= 1000:
        tax = (200 + 0.125*(ec-600))*1.564
    elif ec <= 1600:
        tax = (250 + 0.375*(ec-1000))*1.564
    elif ec <= 3000:
        tax = (475 + 0.75*(ec-1600))*1.564
    elif ec > 3000:
        tax = (1525 + (ec-3000))*1.564

    if rating == 0:
        special = 0
    elif rating == 1:
        special = (tax * 6 - 100)*2
    elif rating == 2:
        special = ((0.625 * ec) - 100)*2
    elif rating == 3:
        special = ((0.20 * ec) - 100)*2

    return (tax+special)


def electrictax(pr):
    if pr <= 7.5:
        return 200*1.564
    if pr <= 32.5:
        return (200 + 2*(pr - 7.5))*1.564
    if pr <= 70:
        return (250 + 6*(pr-32.5))*1.564
    if pr <= 157.5:
        return (465 + 12*(pr-70))*1.564
    if pr > 157.5:
        return (1525 + 16*(pr-157.5))*1.564


def local(ordinaryvalue, specialvalue, directorvalue, expensevalue, othervalue, deduction, donation):
    income = ordinaryvalue + specialvalue + directorvalue
    relief = expensevalue + deduction + donation

    if relief > 80000:
        relief = 80000

    taxable = income - relief

    if taxable <= 20000:
        return 0
    if taxable <= 30000:
        return (taxable - 20000)*0.02
    if taxable <= 40000:
        return (200 + (taxable-30000)*0.035)
    if taxable >= 320000:
        return (44550 + (taxable-320000)*0.22)

    if taxable > 40000 and taxable < 320000:
        rates = [0.07, 0.115, 0.15, 0.18, 0.19, 0.195, 0.2]
        tax = 550
        taxable = taxable - 40000
        i = trunc(taxable/40000)

    j = 0
    while j < i:
        tax = tax + 40000 * rates[j]
        taxable -= 40000
        if j == i-1:
            tax = tax + taxable * rates[j+1]
        j += 1
    return tax


def foreign(ordinaryvalue, specialvalue, directorvalue, expensevalue, othervalue, deduction, donation):
    local = ordinaryvalue - expensevalue - deduction
    foreign = ordinaryvalue - expensevalue
    other = specialvalue + directorvalue + othervalue - donation

    if local <= 20000:
        localtax = 0
    if local <= 30000:
        localtax = (local - 20000)*0.02
    if local <= 40000:
        localtax = (200 + (local-30000)*0.035)
    if local >= 320000:
        localtax = (44550 + (local-320000)*0.22)

    if local > 40000 and local < 320000:
        rates = [0.07, 0.115, 0.15, 0.18, 0.19, 0.195, 0.2]
        localtax = 550
        local = local - 40000
        i = trunc(local/40000)

    j = 0
    while j < i:
        localtax = localtax + 40000 * rates[j]
        annual -= 40000
        if j == i-1:
            localtax = localtax + local * rates[j+1]
        j += 1

    if localtax > foriegn * 0.15:
        employment = localtax
    else:
        employment = foriegn * 0.15

    total = employment + other * 0.22
    return total