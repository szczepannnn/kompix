from flask import Flask, render_template, flash, request, url_for, redirect, session
from dbconnect import connection
from wtforms import Form, PasswordField, BooleanField, TextField, validators
from passlib.hash import sha256_crypt
import gc

app = Flask(__name__)
app.secret_key = 'super secret key'

@app.route('/')
def homepage():
    return render_template("homepage.html")


@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error = ''
    try:
        if request.method == "POST":
            attempted_username = request.form['username']
            attempted_password = request.form['password']

            #flash(attempted_username)
            #flash(attempted_password)

            if attempted_username == "admin" and attempted_password == 'admin':
                return redirect(url_for('homepage'))
            else:
                error = 'Niepoprawna kombinacja nazwy użytkownika i hasła. Spróbuj ponownie.'
        return render_template("login.html", error=error)

    except Exception as e:
        return render_template("login.html", error=error)


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
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s) ", (username, password, email))
                print("Inserted", c.rowcount, "row(s) of data.")
                conn.commit()
                flash("Thanks for registering!")
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
