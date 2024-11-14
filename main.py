import os.path

import time

from flask import Flask, render_template, request, url_for, redirect, session
import pymysql
from werkzeug.utils import secure_filename

from mylib import *

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = './static/photos'

app.secret_key = "super secret key"


@app.route('/')
def welcome():
    return render_template("welcome.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        cur = make_connection()
        city = request.form["T1"]
        sp = request.form["T2"]
        s1 = "SELECT * from hospital_doctor where city='"+city+"' and speciality='"+sp+"'"
        cur.execute(s1)
        data = cur.fetchall()
        return render_template("search_data.html", v=data)
    else:
        return render_template("search_data.html")


@app.route("/view_details", methods=["GET", "POST"])
def view_details():
    if request.method == "POST":
        city = request.form["H0"]
        state = request.form["H1"]
        email = request.form["H2"]
        cur = make_connection()
        s1 = "SELECT * from doctordata where email='"+email+"'"
        cur.execute(s1)
        m = cur.rowcount
        if m > 0:
            data = cur.fetchone()
            return render_template("view_details.html", v=data, city=city, state=state)
        else:
            return render_template("view_details.html", msg="Data not found")
    else:
        return render_template("view_details")


# find a hospital
@app.route("/search_hospital", methods=["GET", "POST"])
def search_hospital():
    if request.method == "POST":
        city = request.form["T1"]
        state = request.form["T2"]
        cur = make_connection()
        s1 = "SELECT * from hospitaldata where city='"+city+"' and state='"+state+"'"
        cur.execute(s1)
        m = cur.rowcount
        if m > 0:
            data = cur.fetchall()
            return render_template("search_hospital1.html", v=data)
        else:
            return render_template("search_hospital1.html", msg="Data not found")
    else:
        return render_template("search_hospital.html")


# auth error
@app.route("/auth_error")
def auth_error():
    return render_template("auth_error.html")


# for login
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["T1"]
        password = request.form["T2"]

        cn = pymysql.connect(host="localhost", port=3306, passwd="", user="root", db="doctor_finder", autocommit=True)
        s1 = "select * from logindata where email='"+email+"' AND password='"+password+"'"
        cur = cn.cursor()
        cur.execute(s1)
        n = cur.rowcount
        if n == 1:
            data = cur.fetchone()
            ut = data[2]  # fetch usertype from column index 2
            # create session
            session["email"] = email
            session["usertype"] = ut
            # send to page
            if ut == "admin":
                return redirect(url_for("admin_home"))
            elif ut == "hospital":
                return redirect(url_for("hospital_home"))
            else:
                return render_template("login.html", msg="Usertype does not exist")
        else:
            return render_template("login.html", msg="Email or Password is incorrect")
    else:
        return render_template("login.html")


# logout
@app.route("/logout")
def logout():
    # check and remove session
    if "email" in session:
        # remove keys email,usertype from session
        session.pop("email", None)
        session.pop("usertype", None)
        return redirect(url_for("welcome"))
    else:
        return redirect(url_for("welcome"))


# admin registration
@app.route('/admin_reg', methods=["GET", "POST"])
def admin_reg():
    if request.method == "POST":
        # receive form data
        name = request.form["T1"]
        address = request.form["T2"]
        contact = request.form["T3"]
        email = request.form["T4"]
        password = request.form["T5"]
        con_pass = request.form["T6"]
        usertype = "admin"
        if password != con_pass:
            msg = "Password and confirm password must be same"
            return render_template("admin_reg.html", msg=msg)
        else:
            cn = pymysql.connect(host="localhost", port=3306, user="root", passwd="", db="doctor_finder", autocommit=True)
            sql1 = "insert into admindata values('"+name+"','"+address+"','"+contact+"','"+email+"')"
            sql2 = "insert into logindata values('"+email+"','"+password+"','"+usertype+"')"
            cur = cn.cursor()
            cur.execute(sql1)
            m = cur.rowcount
            cur.execute(sql2)
            n = cur.rowcount
            if m == 1 and n == 1:
                msg = "Data saved and login created"
            elif m == 1:
                msg = "Only data is saved"
            elif n == 1:
                msg = "Only login is created"
            else:
                msg = "No data is saved and no login created"
            return render_template('admin_reg.html', msg=msg)
    else:
        return render_template("admin_reg.html")


# show admin
@app.route('/show_admin')
def show_admin():
    cn = pymysql.connect(host="localhost", port=3306, user="root", passwd="", db="doctor_finder", autocommit=True)
    s1 = "select * from admindata"
    cur = cn.cursor()
    cur.execute(s1)
    a = cur.rowcount
    if a > 0:
        # fetch data
        data = cur.fetchall()
        return render_template("show_admin.html", v=data)
    else:
        return render_template("show_admin.html", msg="no data")


# admin_home
@app.route("/admin_home")
def admin_home():
    # check session
    if "usertype" in session:
        usertype = session["usertype"]
        email = session["email"]
        if usertype == "admin":
            cur = make_connection()
            s1 = "select * from admindata where email='"+email+"'"
            s2 = "select * from hospitaldata where user_email='"+email+"'"
            cur.execute(s1)
            a = cur.rowcount
            photo = check_photo(email)
            if a > 0:
                data = cur.fetchone()
                cur.execute(s2)
                b = cur.rowcount
                if b > 0:
                    d = cur.fetchall()
                    return render_template("admin_home.html", e1=email, photo=photo, data=data, block=d)
                return render_template("admin_home.html", e1=email, photo=photo, data=data)
        else:
            return redirect(url_for("auth_error"))
    else:
        return redirect(url_for("auth_error"))


# hospital home
@app.route("/hospital_home")
def hospital_home():
    # check session
    if "email" in session:
        email = session["email"]
        ut = session["usertype"]
        if ut == "hospital":
            cur = make_connection()
            s1 = "select * from hospitaldata where email='"+email+"'"
            cur.execute(s1)
            a = cur.rowcount
            photo = check_photo(email)
            if a > 0:
                data = cur.fetchone()
                return render_template("hospital_home.html", photo=photo, data=data)
        else:
            return redirect(url_for("auth_error"))
    else:
        return redirect(url_for("auth_error"))


# photo upload format
@app.route('/admin_photo')
def admin_photo():
    return render_template('photo_upload_admin.html')


# save admin photo upload
@app.route('/admin_photo1', methods=["GET", "POST"])
def admin_photo1():
    if 'usertype' in session:
        usertype = session['usertype']
        email = session['email']
        if usertype == 'admin':
            if request.method == 'POST':
                file = request.files['F1']
                if file:
                    path = os.path.basename(file.filename)
                    file_ext = os.path.splitext(path)[1][1:]
                    filename = str(int(time.time())) + '.' + file_ext
                    filename = secure_filename(filename)
                    conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="", db="doctor_finder", autocommit=True)
                    cur = conn.cursor()
                    sql = "insert into photodata values('"+email+"','"+filename+"')"

                    try:
                        cur.execute(sql)
                        n = cur.rowcount
                        if n == 1:
                            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                            return render_template("photo_upload_admin1.html", result="success")
                        else:
                            return render_template("photo_upload_admin1.html", result="failure")
                    finally:
                        return render_template("photo_upload_admin1.html", result="upload successfully")

                else:
                    return render_template("photo_upload_admin.html")
            else:
                return redirect(url_for("auth_error"))
        else:
            return redirect(url_for("auth_error"))


# change uploaded photo admin
@app.route('/change_admin_photo')
def change_admin_photo():
    if 'usertype' in session:
        usertype = session['usertype']
        email = session['email']
        if usertype == 'admin':
            photo = check_photo(email)
            conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="", db="doctor_finder", autocommit=True)
            cur = conn.cursor()
            sql = "delete from photodata where user_email='"+email+"'"
            cur.execute(sql)
            n = cur.rowcount
            if n > 0:
                os.remove("./static/photos/"+photo)
                return render_template("change_admin_photo.html", data="success")
            else:
                return render_template("change_admin_photo.html", data="failure")
        else:
            return redirect(url_for("auth_error"))
    else:
        return redirect(url_for("auth_error"))


# edit admin
@app.route('/edit_admin', methods=["GET", "POST"])
def edit_admin():
    if request.method == "POST":
        email = request.form["H1"]
        cn = pymysql.connect(host="localhost", port=3306, user="root", db="doctor_finder", passwd="", autocommit=True)
        s1 = "select * from admindata where email='"+email+"'"
        cur = cn.cursor()
        cur.execute(s1)
        a = cur.rowcount
        if a > 0:
            data = cur.fetchone()
            return render_template("edit_admin.html", v=data)
        else:
            return render_template("edit_admin.html", msg="No data found")
    else:
        return redirect(url_for("admin_home"))


# Save Edits admin
@app.route('/edit_admin1', methods=["GET", "POST"])
def edit_admin1():
    if request.method == "POST":
        # grab from data
        name = request.form["T1"]
        address = request.form["T2"]
        contact = request.form["T3"]
        email = request.form["T4"]

        cn = pymysql.connect(host="localhost", port=3306, user="root", db="doctor_finder", passwd="", autocommit=True)
        s1 = "update admindata set name='"+name+"',address='"+address+"',contact='"+contact+"' where email='"+email+"'"
        cur = cn.cursor()
        cur.execute(s1)
        a = cur.rowcount
        if a > 0:
            return render_template("edit_admin.html", msg="Data Changed and saved successfully")
        else:
            return render_template("edit_admin.html", msg="Data changed are not saved")
    else:
        return redirect(url_for("admin_home"))


# change password admin
@app.route('/admin_password', methods=["GET", "POST"])
def admin_password():
    if 'usertype' in session:
        usertype = session['usertype']
        email = session['email']
        if usertype == 'admin':
            if request.method == 'POST':
                old = request.form['T1']
                new = request.form['T2']
                conf = request.form["T3"]
                cur = make_connection()
                if new == conf:
                    cur.execute("update logindata set password='"+new+"' where password='"+old+"' AND email='"+email+"'")
                    n = cur.rowcount
                    if n > 0:
                        return render_template('admin_password.html', result="Password Changed")
                    else:
                        return render_template('admin_password.html', result="Invalid Old Password")
                else:
                    return render_template("admin_password.html", result="password and confirm password does not match")
            else:
                return render_template('admin_password.html')
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# hospital Registration
@app.route('/hospital_reg', methods=["GET", "POST"])
def hospital_reg():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == 'admin':
            if request.method == "POST":
                # receive data
                name = request.form["T1"]
                licence_no = request.form["T2"]
                address = request.form["T3"]
                city = request.form["T4"]
                state = request.form["T5"]
                contact = request.form["T6"]
                ppn = request.form["T7"]
                gen_bed = request.form["T8"]
                ac_bed = request.form["T9"]
                email = request.form["T10"]
                password = request.form["T11"]
                con_pass = request.form["T12"]
                usertype = "hospital"
                if password != con_pass:
                    msg = "Password not matched"
                else:
                    cn = pymysql.connect(host="localhost", port=3306, user="root", passwd="", db="doctor_finder", autocommit=True)
                    sql1 = "insert into hospitaldata values('"+name+"','"+licence_no+"','"+address+"','"+city+"','"+state+"','"+contact+"','"+ppn+"','"+gen_bed+"','"+ac_bed+"','"+email+"','"+user_email+"',0)"
                    sql2 = "insert into logindata values('"+email+"','"+password+"','"+usertype+"')"
                    cur = cn.cursor()
                    cur.execute(sql1)
                    m = cur.rowcount
                    cur.execute(sql2)
                    n = cur.rowcount
                    if m == 1 and n == 1:
                        msg = "Data saved and login created"
                    elif m == 1:
                        msg = "Only data is saved"
                    elif n == 1:
                        msg = "Only login is created"
                    else:
                        msg = "No data is saved and no login created"
                return render_template('hospital_reg.html', msg=msg)
            else:
                return render_template("hospital_reg.html")
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# show hospital inside admin
@app.route("/show_hospital_admin")
def show_hospital_admin():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "admin":
            cur = make_connection()
            s1 = "select * from hospitaldata where user_email='"+user_email+"'"
            cur.execute(s1)
            a = cur.rowcount
            if a > 0:
                # fetch data
                data = cur.fetchall()
                return render_template("show_hospital_admin.html", v=data)
            else:
                render_template("show_hospital_admin.html", msg="No data")
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# edit hospital data
@app.route("/edit_hospital_data", methods=["GET", "POST"])
def edit_hospital_data():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "admin":
            if request.method == "POST":
                email = request.form["H1"]
                cur = make_connection()
                s1 = "select * from hospitaldata where email='"+email+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                a = cur.rowcount
                if a > 0:
                    data = cur.fetchone()
                    return render_template("edit_hospital_data.html", v=data)
                else:
                    return render_template("edit_hospital_data.html", msg="No data found")
            else:
                return redirect(url_for("show_hospital_admin"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# Save edited hospital data
@app.route('/edit_hospital_data1', methods=["GET", "POST"])
def edit_hospital_data1():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "admin":
            if request.method == "POST":
                # grab from data
                name = request.form["T1"]
                licence_no = request.form["T2"]
                address = request.form["T3"]
                city = request.form["T4"]
                state = request.form["T5"]
                contact = request.form["T6"]
                ppn = request.form["T7"]
                gen_bed = request.form["T8"]
                ac_bed = request.form["T9"]
                email = request.form["T10"]

                cur = make_connection()
                s1 = "update hospitaldata set name='"+name+"',licence_no='"+licence_no+"',address='"+address+"',city='"+city+"',state='"+state+"',contact='"+contact+"',ppn_status='"+ppn+"',general_beds='"+gen_bed+"',ac_beds='"+ac_bed+"' where email='"+email+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                a = cur.rowcount
                if a > 0:
                    return render_template("edit_hospital_data1.html", msg="Data Changed and saved successfully")
                else:
                    return render_template("edit_hospital_data1.html", msg="Data changed are not saved")
            else:
                return redirect(url_for("show_hospital_admin"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# delete hospital inside admin
@app.route("/delete_hospital_data", methods=["GET", "POST"])
def delete_hospital_data():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "admin":
            if request.method == "POST":
                email = request.form["H1"]
                cur = make_connection()
                s1 = "select * from hospitaldata where email='"+email+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                n = cur.rowcount
                if n > 0:
                    data = cur.fetchone()
                    return render_template("delete_hospital_data.html", v=data)
                else:
                    return render_template("delete_hospital_data.html", msg="No data found")
            else:
                return redirect(url_for("show_hospital_admin"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# deleting hospital
@app.route('/delete_hospital_data1', methods=["GET", "POST"])
def delete_hospital_data1():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "admin":
            if request.method == "POST":
                email = request.form["H1"]

                cur = make_connection()
                s1 = "delete from hospitaldata where email='"+email+"' and user_email='"+user_email+"'"
                s2 = "delete from logindata where email='"+email+"'"
                cur.execute(s1)
                n = cur.rowcount
                cur.execute(s2)
                m = cur.rowcount
                if n > 0 and m > 0:
                    return render_template("delete_hospital_data1.html", msg="Data deleted Successfully")
                else:
                    return render_template("delete_hospital_data1.html", msg="Data not deleted")
            else:
                return redirect(url_for("show_hospital_admin"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# edit hospital data in hospital home
@app.route("/edit_hospital", methods=["GET", "POST"])
def edit_hospital():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                email = request.form["H1"]
                cur = make_connection()
                s1 = "select * from hospitaldata where email='"+email+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                a = cur.rowcount
                if a > 0:
                    data = cur.fetchone()
                    return render_template("edit_hospital.html", v=data)
                else:
                    return render_template("edit_hospital.html", msg="No data found")
            else:
                return redirect(url_for("hospital_home"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# Save edited hospital data inside hospital home
@app.route('/edit_hospital1', methods=["GET", "POST"])
def edit_hospital1():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                # grab from data
                name = request.form["T1"]
                licence_no = request.form["T2"]
                address = request.form["T3"]
                city = request.form["T4"]
                state = request.form["T5"]
                contact = request.form["T6"]
                ppn = request.form["T7"]
                gen_bed = request.form["T8"]
                ac_bed = request.form["T9"]
                email = request.form["T10"]

                cur = make_connection()
                s1 = "update hospitaldata set name='"+name+"',licence_no='"+licence_no+"',address='"+address+"',city='"+city+"',state='"+state+"',contact='"+contact+"',ppn_status='"+ppn+"',general_beds='"+gen_bed+"',ac_beds='"+ac_bed+"' where email='"+email+"'"
                cur.execute(s1)
                a = cur.rowcount
                if a > 0:
                    return render_template("edit_hospital1.html", msg="Data Changed and saved successfully")
                else:
                    return render_template("edit_hospital1.html", msg="Data changed are not saved")
            else:
                return redirect(url_for("hospital_home"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# save hospital photo upload
@app.route('/hospital_photo1', methods=["GET", "POST"])
def hospital_photo1():
    if "usertype" in session:
        usertype = session['usertype']
        email = session['email']
        if usertype == 'hospital':
            if request.method == 'POST':
                file = request.files['F1']
                if file:
                    path = os.path.basename(file.filename)
                    file_ext = os.path.splitext(path)[1][1:]
                    filename = str(int(time.time())) + '.' + file_ext
                    filename = secure_filename(filename)
                    conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="", db="doctor_finder", autocommit=True)
                    cur = conn.cursor()
                    sql = "insert into photodata values('"+email+"','"+filename+"')"

                    try:
                        cur.execute(sql)
                        n = cur.rowcount
                        if n == 1:
                            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                            return render_template("photo_upload_hospital1.html", result="success")
                        else:
                            return render_template("photo_upload_hospital1.html", result="failure")
                    finally:
                        return render_template("photo_upload_hospital1.html", result="upload successfully")
                else:
                    return render_template("hospital_home.html")
            else:
                return redirect(url_for("auth_error"))
        else:
            return redirect(url_for("auth_error"))


# change uploaded photo hospital
@app.route('/change_hospital_photo')
def change_hospital_photo():
    if 'usertype' in session:
        usertype = session['usertype']
        email = session['email']
        if usertype == 'hospital':
            photo = check_photo(email)
            cur = make_connection()
            sql = "delete from photodata where user_email='"+email+"'"
            cur.execute(sql)
            n = cur.rowcount
            if n > 0:
                os.remove("./static/photos/"+photo)
                return render_template("change_hospital_photo.html", data="success")
            else:
                return render_template("change_hospital_photo.html", data="failure")
        else:
            return redirect(url_for("auth_error"))
    else:
        return redirect(url_for("auth_error"))


# change password hospital
@app.route('/hospital_password', methods=["GET", "POST"])
def hospital_password():
    if 'usertype' in session:
        usertype = session['usertype']
        email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                old = request.form["T1"]
                new = request.form["T2"]
                conf = request.form["T3"]
                cur = make_connection()
                if new == conf:
                    cur.execute("update logindata set password='"+new+"' where password='"+old+"' AND email='"+email+"'")
                    n = cur.rowcount
                    if n > 0:
                        return render_template('hospital_password.html', result="Password Changed")
                    else:
                        return render_template('hospital_password.html', result="Invalid Old Password")
                else:
                    return render_template("hospital_password.html", result="password and confirm password does not match")
            else:
                return render_template('hospital_password.html')
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# Doctor Registration
@app.route('/doctor_reg', methods=["GET", "POST"])
def doctor_reg():
    if 'usertype' in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                # received data
                name = request.form["T1"]
                address = request.form["T2"]
                contact = request.form["T3"]
                speciality = request.form["T4"]
                working_exp = request.form["T5"]
                current_hospital = request.form["T6"]
                days = request.form.getlist("T7")
                mon = "no"
                tue = "no"
                wed = "no"
                thur = "no"
                fri = "no"
                sat = "no"
                sun = "no"
                if "mon" in days:
                    mon = "yes"
                if "tue" in days:
                    tue = "yes"
                if "wed" in days:
                    wed = "yes"
                if "thur" in days:
                    thur = "yes"
                if "fri" in days:
                    fri = "yes"
                if "sat" in days:
                    sat = "yes"
                if "sun" in days:
                    sun = "yes"
                mor_shift = request.form["T8"]
                eve_shift = request.form["T9"]
                email = request.form["T10"]
                cur = make_connection()
                s1 = "insert into doctordata values('"+name+"','"+address+"','"+contact+"','"+speciality+"','"+working_exp+"','"+current_hospital+"','"+mor_shift+"','"+eve_shift+"','"+email+"',0,'"+mon+"','"+tue+"','"+wed+"','"+thur+"','"+fri+"','"+sat+"','"+sun+"','"+user_email+"')"
                cur.execute(s1)
                m = cur.rowcount
                if m > 0:
                    msg = "Data Saved"
                else:
                    msg = "No data Saved"
                return render_template('/doctor_reg.html', msg=msg)
            else:
                return render_template("doctor_reg.html")


# show doctor data inside hospital
@app.route('/show_doctors')
def show_doctors():
    if 'usertype' in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            cur = make_connection()
            s1 = "select * from doctordata where user_email='"+user_email+"'"
            cur.execute(s1)
            a = cur.rowcount
            if a > 0:
                # fetch data
                data = cur.fetchall()
                return render_template("show_doctors.html", v=data)
            else:
                return render_template("show_doctors.html", msg="No data found")


# edit doctor data in hospital home
@app.route('/edit_doctor', methods=["GET", "POST"])
def edit_doctor():
    if 'usertype' in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                doctor_id = request.form["H1"]
                cur = make_connection()
                s1 = "select * from doctordata where doctor_no='"+doctor_id+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                a = cur.rowcount
                if a > 0:
                    data = cur.fetchone()
                    return render_template("edit_doctor.html", v=data)
                else:
                    return render_template("edit_doctor_data.html", msg="No data found")
            else:
                return redirect(url_for("show_doctors"))


# edit doctor data1
@app.route('/edit_doctor1', methods=["GET", "POST"])
def edit_doctor1():
    if 'usertype' in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                name = request.form["T1"]
                address = request.form["T2"]
                contact = request.form["T3"]
                speciality = request.form["T4"]
                work_exp = request.form["T5"]
                current_hospital = request.form["T6"]
                days = request.form.getlist("T10")
                mon = "no"
                tue = "no"
                wed = "no"
                thur = "no"
                fri = "no"
                sat = "no"
                sun = "no"
                if "mon" in days:
                    mon = "yes"
                if "tue" in days:
                    tue = "yes"
                if "wed" in days:
                    wed = "yes"
                if "thur" in days:
                    thur = "yes"
                if "fri" in days:
                    fri = "yes"
                if "sat" in days:
                    sat = "yes"
                if "sun" in days:
                    sun = "yes"
                mor_shift = request.form["T7"]
                eve_shift = request.form["T8"]
                email = request.form["T9"]
                doctor_id = request.form["T11"]

                cur = make_connection()
                s1 = "update doctordata set name='"+name+"',address='"+address+"',contact='"+contact+"',speciality='"+speciality+"',working_exp='"+work_exp+"',current_hospital='"+current_hospital+"',mor_shift='"+mor_shift+"',eve_shift='"+eve_shift+"',email='"+email+"',mon='"+mon+"',tue='"+tue+"',wed='"+wed+"',thur='"+thur+"',fri='"+fri+"',sat='"+sat+"',sun='"+sun+"' where doctor_no='"+doctor_id+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                a = cur.rowcount
                if a > 0:
                    return render_template("edit_doctor1.html", msg="Data Updated")
                else:
                    return render_template("edit_doctor1.html", msg="Data not found")
            else:
                return redirect(url_for("show_doctors"))


# delete doctor by hospital
@app.route("/delete_doctor", methods=["GET", "POST"])
def delete_doctor():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                doctor_id = request.form["H1"]
                cur = make_connection()
                s1 = "select * from doctordata where doctor_no='"+doctor_id+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                n = cur.rowcount
                if n > 0:
                    data = cur.fetchone()
                    return render_template("delete_doctor.html", v=data)
                else:
                    return render_template("delete_doctor.html", msg="No data found")
            else:
                return redirect(url_for("show_doctors"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# deleting doctor
@app.route('/delete_doctor1', methods=["GET", "POST"])
def delete_doctor1():
    if "usertype" in session:
        usertype = session['usertype']
        user_email = session['email']
        if usertype == "hospital":
            if request.method == "POST":
                doctor_id = request.form["H1"]
                cur = make_connection()
                s1 = "delete from doctordata where doctor_no='"+doctor_id+"' and user_email='"+user_email+"'"
                cur.execute(s1)
                m = cur.rowcount
                if m > 0:
                    return render_template("delete_doctor1.html", msg="Data deleted Successfully")
                else:
                    return render_template("delete_doctor1.html", msg="Data not deleted")
            else:
                return redirect(url_for("show_doctors"))
        else:
            return redirect(url_for('auth_error'))
    else:
        return redirect(url_for('auth_error'))


# contact
@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
