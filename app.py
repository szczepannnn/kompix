from flask import Flask, render_template, flash, request, url_for, redirect, session, jsonify
from dbconnect import connection
from wtforms import Form, PasswordField, BooleanField, TextField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import gc
import stripe
from stripe import Customer, Charge



app = Flask(__name__)
app.secret_key = 'super secret key'

pub_key = 'pk_test_kTJOiboHBxPEtMuTarqpLoY500bwth8eUA'
secret_key = 'sk_test_G3tcIN8o0dpUi7EXfoqvdBwA00iLsAUROl'

stripe.api_key = secret_key


@app.route('/thanks', methods=['POST', 'GET'])
def thanks():
    print("tutaj")
    c, conn = connection()
    sql_select_Query = "select * from koszyk WHERE username = (%s)"
    c.execute(sql_select_Query, (session['username'],))
    records_koszyk = c.fetchall()
    c.execute("INSERT INTO oplacone (username, products_komp, adres_dostawy, telefon) VALUES (%s, %s, %s, %s)", (records_koszyk[0][1],records_koszyk[0][2],records_koszyk[0][3],records_koszyk[0][4]))
    c.execute("DELETE FROM koszyk WHERE username=(%s)", (session['username'],))
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return render_template('thanks.html')


@app.route('/stripe', methods=['POST'])
def stripe1():
    c, conn = connection()
    sql_select_Query = "select * from koszyk WHERE username = (%s)"
    c.execute(sql_select_Query, (session['username'],))
    records_koszyk = c.fetchall()
    d, conn = connection()
    sql_select_Query = "select * from komputery"
    d.execute(sql_select_Query)
    records_komputery = d.fetchall()
    if c.rowcount == 0 or records_koszyk[0][2] == "":
        return render_template("koszyk.html", j_computers=0, suma=0)
    else:
        products = records_koszyk[0][2]
        splitedproducts = []
        splitedproducts = products.split(", ");

        j_computers = len(splitedproducts)
        i = 0
        suma = 0
        for i in range(0, j_computers):
            splitedproducts[i] = int(splitedproducts[i]) - 1
            suma = suma + records_komputery[int(splitedproducts[i])][2]

    customer = stripe.Customer.create(email=request.form['stripeEmail'], source=request.form['stripeToken'])
    suma = suma*100
    charge = stripe.Charge.create(
        customer=customer.id,
        amount=suma,
        currency='PLN',
        description='Twój koszyk'
    )
    return redirect(url_for('thanks'))

class Payform(Form):
    street = TextField('Ulica:', [validators.Length(min=3, max=20)])
    housenumber = TextField('Numer domu/mieszkania:', [validators.Length(min=0, max=3)])
    city = TextField('Miasto:', [validators.Length(min=3, max=20)])
    postalcode = TextField('Kod pocztowy:', [validators.Length(min=6, max=7)])
    phone = TextField('Numer telefonu:', [validators.Length(min=6, max=10)])


@app.route('/pay/', methods=["GET", "POST"])
def pay():
    try:
        form = Payform(request.form)
        c, conn = connection()
        sql_select_Query = "select * from koszyk WHERE username = (%s)"
        c.execute(sql_select_Query, (session['username'],))
        records_koszyk = c.fetchall()
        d, conn = connection()
        sql_select_Query = "select * from komputery"
        d.execute(sql_select_Query)
        records_komputery = d.fetchall()
        if c.rowcount == 0 or records_koszyk[0][2] == "":
            return render_template("koszyk.html", j_computers=0, suma=0)
        else:
            products = records_koszyk[0][2]
            splitedproducts = []
            splitedproducts = products.split(", ");

            j_computers = len(splitedproducts)
            i = 0
            suma = 0
            for i in range(0, j_computers):
                splitedproducts[i] = int(splitedproducts[i]) - 1
                suma = suma + records_komputery[int(splitedproducts[i])][2]

        print(suma)

        if request.method == "POST" and form.validate():
            street = form.street.data
            housenumber = form.housenumber.data
            city = form.city.data
            postalcode = form.postalcode.data

            phone = form.phone.data
            adress = street + "," + housenumber + "," + city + "," + postalcode

            e, conn = connection()
            e.execute("UPDATE koszyk SET adres_dostawy = (%s), telefon = (%s)  WHERE username = (%s)", (adress, phone, session['username'], ))
            flash("Dane zapisane")
            conn.commit()
            e.close()
            conn.close()
            gc.collect()
            return render_template("pay.html", suma=suma, pub_key=pub_key)

        return render_template("pay.html", form=form, suma=suma, pub_key=pub_key)
    except Exception as e:
        flash(str(e))
        return render_template("pay.html", form=form)


@app.route('/add_to_cart_komp', methods=["GET", "POST"])
def addToCartKomp():
    ProductID=int(request.form["productId"])
    print(ProductID)
    c, conn = connection()

    c.execute("SELECT * FROM koszyk WHERE username = (%s)", (session['username'],))
    records = c.fetchall()

    if c.rowcount == 0:
        c.execute("INSERT INTO koszyk (username, products_komp) VALUES (%s, %s) ", (session['username'], ProductID))
        print("Inserted", c.rowcount, "row(s) of data.")
        conn.commit()
        flash("Koszyk został stworzony oraz produkt został dodany do koszyka.")
        c.close()
        conn.close()
        gc.collect()
        c, conn = connection()
        c.execute("SELECT * FROM komputery WHERE uid = (%s)", (ProductID,))
        records2 = c.fetchall()
        new2 = records2[0][3] - 1;
        c.execute("UPDATE komputery SET iloscsztuk = (%s) WHERE uid = (%s)", (new2, ProductID))
        print("Inserted", c.rowcount, "row(s) of data.")
        conn.commit()
        c.close()
        conn.close()
        gc.collect()

    else:
        if records[0][2] == "":
            records = list(records)
            new = str(ProductID)
            print(new)
            print(session['username'])
            c.execute("UPDATE koszyk SET products_komp = (%s) WHERE username = (%s)", (new, session['username']))
            print("Inserted", c.rowcount, "row(s) of data.")
            flash("Produkt został dodany do koszyka.")
            conn.commit()
            c.close()
            conn.close()
            gc.collect()

            c, conn = connection()
            c.execute("SELECT * FROM komputery WHERE uid = (%s)", (ProductID,))
            records1 = c.fetchall()
            new1 = records1[0][3] - 1;
            c.execute("UPDATE komputery SET iloscsztuk = (%s) WHERE uid = (%s)", (new1, ProductID))
            print("Inserted", c.rowcount, "row(s) of data.")
            conn.commit()
            c.close()
            conn.close()
            gc.collect()
        else:
            records = list(records)
            new = records[0][2] + ", " + str(ProductID)
            print(new)
            print(session['username'])
            c.execute("UPDATE koszyk SET products_komp = (%s) WHERE username = (%s)", (new, session['username']))
            print("Inserted", c.rowcount, "row(s) of data.")
            flash("Produkt został dodany do koszyka.")
            conn.commit()
            c.close()
            conn.close()
            gc.collect()

            c, conn = connection()
            c.execute("SELECT * FROM komputery WHERE uid = (%s)", (ProductID,))
            records1 = c.fetchall()
            new1 = records1[0][3]-1;
            c.execute("UPDATE komputery SET iloscsztuk = (%s) WHERE uid = (%s)", (new1, ProductID))
            print("Inserted", c.rowcount, "row(s) of data.")
            conn.commit()
            c.close()
            conn.close()
            gc.collect()

    return jsonify(status="success")


@app.route('/remove_from_cart_komp', methods=["GET", "POST"])
def removeFromCartKomp():
    ProductID=int(request.form["productId"])
    c, conn = connection()

    c.execute("SELECT * FROM koszyk WHERE username = (%s)", (session['username'],))
    records_komp=c.fetchall()
    products = records_komp[0][2]
    splitedproducts = []
    splitedproducts = products.split(", ");
    j_computers = len(splitedproducts)
    print(j_computers)
    new = ""
    for i in range(0, j_computers):
        if i != j_computers:
            if i != ProductID:
                new = new + splitedproducts[i] + ", "
                print(new)
            else:
                c.execute("SELECT * FROM komputery WHERE uid = (%s)", (splitedproducts[i],))
                records2 = c.fetchall()
                new2 = records2[0][3] + 1
                c.execute("UPDATE komputery SET iloscsztuk = (%s) WHERE uid = (%s)", (new2, splitedproducts[i],))
                conn.commit()
    new = new[:-2]

    c.execute("UPDATE koszyk SET products_komp = (%s) WHERE username = (%s)", (new, session['username'],))
    conn.commit()
    c.close()
    conn.close()
    gc.collect()

    return jsonify(status="success")


@app.route('/koszyk', methods=["GET", "POST"])
def koszyk():
    c, conn = connection()
    sql_select_Query = "select * from koszyk WHERE username = (%s)"
    c.execute(sql_select_Query,(session['username'],))
    records_koszyk = c.fetchall()
    d, conn = connection()
    sql_select_Query = "select * from komputery"
    d.execute(sql_select_Query)
    records_komputery = d.fetchall()
    if c.rowcount == 0 or records_koszyk[0][2] == "":
        return render_template("koszyk.html", j_computers=0, suma=0)
    else:
        products = records_koszyk[0][2]
        splitedproducts = []
        splitedproducts = products.split(", ");

        j_computers = len(splitedproducts)
        i=0
        suma=0
        for i in range(0, j_computers):
            splitedproducts[i] = int(splitedproducts[i])-1
            suma = suma+records_komputery[int(splitedproducts[i])][2]
        link_computers = []
        for product in splitedproducts:
            link_computers.append("images/product/" + records_komputery[int(product)][4] + ".jpg")

        return render_template("koszyk.html", products_computers=splitedproducts,imagesource_computers=link_computers, records_computers=records_komputery, j_computers=j_computers, suma=suma)


@app.route('/')
def homepage():
    return render_template("homepage.html")


@app.route('/komputery')
def komputery():
    try:
        c, conn = connection()
        sql_select_Query = "select * from komputery"
        c.execute(sql_select_Query)
        records = c.fetchall()
        number_of_rows = c.rowcount
        number_of_rows2 = number_of_rows // 2
        i=0
        link =[]
        for rows in records:
            link.append("images/product/" + records[i][4]+".jpg")
            i=i+1
        return render_template("komputery.html", records=records, products=rows, imagesource=link, number_of_rows1=number_of_rows, number_of_rows2=number_of_rows2)

    except Exception as e:
        error = "Błąd ładaowania produktów z bazy danych."
        flash(error)
        return render_template("komputery.html")


@app.route('/komputery/produkt/<int:productId>')
def productPage(productId=1):
    c, conn = connection()
    sql_select_Query = "select * from komputery"
    c.execute(sql_select_Query)
    records = c.fetchall()
    number_of_rows = c.rowcount
    number_of_rows2 = number_of_rows // 2
    image = []
    image.append("images/product/" + records[productId-1][4] + ".jpg")
    image.append("images/product/" + records[productId-1][5] + ".jpg")
    return render_template("produkt.html", records=records, imagesource=image, number_of_rows1=number_of_rows, number_of_rows2=number_of_rows2, productId=productId)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Musisz być zalogowany.")
            return redirect(url_for('login_page'))
    return wrap


@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("Wylogowanie przebiegło pomyślnie")
    gc.collect()
    return redirect(url_for('homepage'))


@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":

            data = c.execute("SELECT * FROM users WHERE username = (%s)", (request.form['username'],))
            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                flash("Logowanie przebiegło pomyślnie.")
                return redirect(url_for("homepage"))
            else:
                error = "Niepoprawne dane logowania, spróbuj ponownie."
                flash(error)
        gc.collect()

        return render_template("login.html")

    except Exception as e:
        error = "Niepoprawne dane logowania, spróbuj ponownie."
        flash(error)
        return render_template("login.html")


@app.route('/search', methods=['POST'])
def search():
    c, conn = connection()
    sql_select_Query = "select * from komputery"
    c.execute(sql_select_Query)
    records_computers = c.fetchall()
    i_computers = 0
    j_computers = 0
    productsToRender_computer = []
    if request.form["search"].lower() is "":
        flash("Puste wyszukiwanie.")
    else:
        for rows in records_computers:
            if request.form["search"].lower() in records_computers[i_computers][1].lower():
                productsToRender_computer.append(i_computers)
                j_computers = j_computers + 1
            i_computers = i_computers + 1
    link_computers = []
    for product in productsToRender_computer:
        link_computers.append("images/product/" + records_computers[product][4] + ".jpg")
    return render_template('search.html', products_computers=productsToRender_computer, imagesource_computers=link_computers, records_computers=records_computers, j_computers=j_computers)


class RegistrationForm(Form):
    username = TextField('Nazwa użytkownika:', [validators.Length(min=4, max=20)])
    email = TextField('Adres e-mail:', [validators.Length(min=6, max=50)])
    password = PasswordField('Hasło:', [validators.Length(min=6, max=50),
        validators.Required(),
        validators.EqualTo('confirm', message='Hasła muszą sie zgadzać!')
    ])
    confirm = PasswordField('Powtórz hasło:')
    accept_tos = BooleanField('Akceptuję <a href="/regulamin/">regulamin sklepu</a> (zaktualizowane 15.08.2019).', [validators.Required()])


@app.route('/register/', methods=["GET", "POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            c.execute("SELECT * FROM users WHERE username = (%s)", (username,))

            if c.rowcount > 0:
                flash("Ta nazwa użytkownika jest już zajęta, wybierz inną.")
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s) ", (username, password, email))
                print("Inserted", c.rowcount, "row(s) of data.")
                conn.commit()
                flash("Dziękujemy za rejestrację!")
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('homepage'))

        return render_template("register.html", form=form)

    except Exception as e:
        return (str(e))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


if __name__ == '__main__':
    app.debug = True
    app.run()
