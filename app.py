from flask import Flask, render_template, redirect, url_for, request
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField
from datetime import date, timedelta
from wtforms.validators import DataRequired
import calendar
from collections import defaultdict

# Main app config
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

# config Mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'test'
app.config['MYSQL_DB'] = 'test'
mysql = MySQL(app)


class Html5form(FlaskForm):
    date_today = date.today()
    first_day = date_today.replace(day=1)
    last_day = date_today.replace(
        day=calendar.monthrange(date_today.year, date_today.month)[1])
    start_date = DateField("Start at", [DataRequired(), ], default=first_day)
    end_date = DateField("End at", [DataRequired(), ], default=last_day)


# home route
@app.route("/")
def main():
    form = Html5form()
    start_date = form.first_day
    end_date = form.last_day

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)
    # Cursor for employee_list
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM employee_list"
    cur.execute(sql)
    results = cur.fetchall()
    cur.close()
    all_bill = {}
    all_bill = defaultdict(list)
    for i, k in results:
        for single_day in daterange(start_date, end_date):
            foo = single_day.strftime("%Y-%m-%d")
            # print(foo, i)
            # Cursor for dat and meal
            cur = mysql.connection.cursor()
            sql = "SELECT date, meal FROM bill WHERE id="+str(i)+" and date='"+foo+"'"
            # print(sql)
            cur.execute(sql)
            bill = cur.fetchone()
            if bill:
                all_bill[foo].append(bill[1])
    # print(all_bill)
    return render_template('home.html',
                           results=results,
                           form=form,
                           bill=all_bill)


class MainForm(FlaskForm):
    until = DateField(label="Date",
                      format="%Y-%m-%d",
                      default=date.today,
                      validators=[DataRequired(), ])


@app.route('/add', methods=['GET', 'POST'])
def add():
    # Cursor for all employee_list
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM employee_list"
    cur.execute(sql)
    results = cur.fetchall()
    # print(results)
    form1 = MainForm()
    for i, k in results:
        if request.method == 'POST':
            tdate = form1.until.data
            # tdate1 = tdate.strftime('%Y-%m-%d')
            id = i
            # print(type(tdate1), type(id))
            if request.form.getlist(k):
                check = 1
            else:
                check = 0
            # print(type(check))
            # Cursor
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO bill(id, date, meal) VALUES (%s, %s, %s)",
                        (id, tdate, check))
            # commit
            mysql.connection.commit()
            cur.close()
    if request.method == 'POST':
        return redirect(url_for('main'))
    else:
        return render_template('add.html', form=form1, results=results)


class ExpForm(FlaskForm):
    until = DateField(label="Date",
                      format="%Y-%m-%d",
                      default=date.today,
                      validators=[DataRequired(), ])
    taka = IntegerField()


@app.route('/addexpence', methods=['GET', 'POST'])
def addexpance():
    form1 = ExpForm()
    if request.method == 'POST':
        tdate = form1.until.data
        # tdate1 = tdate.strftime('%Y-%m-%d')
        bdt = form1.taka.data
        # Cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO exp(date, expence) VALUES (%s, %s)",
                    (tdate, bdt))
        # commit
        mysql.connection.commit()
        cur.close()
    if request.method == 'POST':
        return redirect(url_for('main'))
    else:
        return render_template('addexp.html', form=form1)


@app.route('/bill')
def bill():
    all_meal = []
    exp_bill = []
    per_person_cost = []
    company_per_cost = []
    you_per_cost = []
    cost = 0.5
    ex_meal_total = 0
    # Cursor for employee_list
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM employee_list"
    cur.execute(sql)
    results = cur.fetchall()
    cur.close()
    # meal add
    for i, k in results:
        id = i
        cur = mysql.connection.cursor()
        sql = "SELECT CAST(SUM(meal) AS SIGNED) FROM bill WHERE id="+str(id)
        cur.execute(sql)
        one_meal = cur.fetchone()
        cur.close()
        if one_meal:
            all_meal.append(one_meal)
    # print(all_meal)
    form = Html5form()
    start_date = form.first_day
    end_date = form.last_day

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)
    for single_day in daterange(start_date, end_date):
        foo = single_day.strftime("%Y-%m-%d")
        # print(foo)
        # Cursor for date and expense
        cur = mysql.connection.cursor()
        sql = "SELECT * FROM exp WHERE date='"+foo+"'"
        # print(sql)
        cur.execute(sql)
        ex_bill = cur.fetchone()
        # print(ex_bill)
        if ex_bill:
            exp_bill.append(ex_bill)
        cur.close()
    # Cursor for total expence
    cur = mysql.connection.cursor()
    sql = "SELECT SUM(expence) FROM exp;"
    # print(sql)
    cur.execute(sql)
    ex_bill_total = cur.fetchone()
    # print(ex_bill)
    cur.close()
    for meal_all in all_meal:
        ex_meal_total += meal_all[0]
        # print(ex_meal_total)
    per_meal_cost = round(ex_bill_total[0]/ex_meal_total)
    for i in all_meal:
        per_person_cost.append(i[0]*per_meal_cost)
    company_per_cost = [round(x * cost) for x in per_person_cost]
    you_per_cost = [round(x * cost) for x in per_person_cost]
    return render_template('bill.html',
                           results=results,
                           meal=all_meal,
                           exp_bill=exp_bill,
                           ex_bill_total=ex_bill_total,
                           ex_meal_total=ex_meal_total,
                           per_meal_cost=per_meal_cost,
                           per_person_cost=per_person_cost,
                           company_per_cost=company_per_cost,
                           you_per_cost=you_per_cost)


if __name__ == '__main__':
    app.run(debug=True)
