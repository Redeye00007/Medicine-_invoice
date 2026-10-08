from flask import Flask, render_template, request, redirect, session, send_file
from database import create_db
import sqlite3
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4



app = Flask(__name__)

app.secret_key = "RMS_SECRET"


create_db()



# ================= LOGIN =================

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]


        con = sqlite3.connect("rms.db")

        cur = con.cursor()


        user = cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()


        con.close()



        if user:

            session["user"] = username

            return redirect("/dashboard")



    return render_template("login.html")





# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():


    if "user" not in session:
        return redirect("/")



    con = sqlite3.connect("rms.db")

    cur = con.cursor()


    count = cur.execute(
        "SELECT COUNT(*) FROM medicines"
    ).fetchone()[0]


    con.close()



    return render_template(
        "dashboard.html",
        count=count
    )





# ================= MEDICINE =================


@app.route("/medicine", methods=["GET","POST"])
def medicine():


    if "user" not in session:
        return redirect("/")



    con = sqlite3.connect("rms.db")

    cur = con.cursor()



    if request.method=="POST":


        cur.execute(
        """
        INSERT INTO medicines
        VALUES(NULL,?,?,?,?,?,?,?)
        """,
        (

        request.form.get("name"),

        request.form.get("company"),

        request.form.get("batch"),

        request.form.get("expiry"),

        request.form.get("buy"),

        request.form.get("sell"),

        request.form.get("stock")

        ))



        con.commit()



    medicines = cur.execute(
        "SELECT * FROM medicines"
    ).fetchall()



    con.close()



    return render_template(
        "medicine.html",
        medicines=medicines
    )







# ================= PURCHASE =================


@app.route("/purchase", methods=["GET","POST"])
def purchase():


    if "user" not in session:
        return redirect("/")



    if request.method=="POST":


        supplier = request.form.get("supplier","")



        product = request.form.getlist("product")

        qty = request.form.getlist("qty")

        mrp = request.form.getlist("mrp")

        price = request.form.getlist("price")



        total = 0



        for i in range(len(product)):


            q = int(qty[i]) if qty[i] else 0


            p = float(price[i]) if price[i] else 0



            total += q*p





        session["invoice"] = {


            "supplier": supplier,

            "product": product,

            "qty": qty,

            "mrp": mrp,

            "price": price,

            "total": total,

            "date": str(datetime.now().date())

        }




        return render_template(

            "invoice.html",

            supplier=supplier,

            product=product,

            qty=qty,

            mrp=mrp,

            price=price,

            total=total,

            date=datetime.now().date()

        )



    return render_template("purchase.html")







# ================= PDF =================


@app.route("/download_pdf")
def download_pdf():


    data = session.get("invoice")



    if not data:

        return "No Invoice Data"



    filename = "invoice.pdf"



    doc = SimpleDocTemplate(
        filename,
        pagesize=A4
    )



    styles = getSampleStyleSheet()



    content=[]



    content.append(
        Paragraph(
            "Procurement Invoice",
            styles["Title"]
        )
    )


    content.append(
        Spacer(1,20)
    )



    content.append(
        Paragraph(
            "Date: "+data["date"],
            styles["Normal"]
        )
    )


    content.append(
        Paragraph(
            "Supplier: "+data["supplier"],
            styles["Normal"]
        )
    )


    content.append(
        Spacer(1,20)
    )




    rows=[

        [
        "#",
        "Product",
        "Qty",
        "MRP",
        "Unit Price",
        "Total"
        ]

    ]



    grand=0



    for i in range(len(data["product"])):



        if data["product"][i]:


            q=int(data["qty"][i]) if data["qty"][i] else 0


            m=float(data["mrp"][i]) if data["mrp"][i] else 0


            p=float(data["price"][i]) if data["price"][i] else 0



            t=q*p


            grand+=t



            rows.append(

            [

            str(i+1),

            data["product"][i],

            str(q),

            str(m),

            str(p),

            str(t)

            ]

            )




    rows.append(

    [

    "",

    "",

    "",

    "",

    "Grand Total",

    str(grand)

    ]

    )




    table = Table(rows)



    table.setStyle(

    TableStyle([


    ("GRID",(0,0),(-1,-1),1,colors.black),


    ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),


    ("ALIGN",(0,0),(-1,-1),"CENTER")


    ])

    )



    content.append(table)



    content.append(
        Spacer(1,40)
    )



    content.append(
        Paragraph(
            "Copyright © 2026 Himel | Version 1.0",
            styles["Normal"]
        )
    )



    doc.build(content)



    return send_file(
        filename,
        as_attachment=True
    )






# ================= LOGOUT =================


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")





app.run(
    host="0.0.0.0",
    port=5012,
    debug=True
)