from flask import Flask, render_template, flash, request, url_for, redirect
from dbconnect import connection

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


@app.route('/register/', methods=["GET","POST"])
def register_page():
    try:
        c, conn = connection()
        return("okay")
    except Exception as e:
        return(str(e))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


if __name__ == '__main__':
    app.debug = True
    app.run()
