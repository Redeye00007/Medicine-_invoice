from flask import Flask, render_template, request, redirect, session, send_file
from database import create_db

import sqlite3
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = "MEDICINE_SYSTEM_SECRET_KEY_123"


# =========================================================
# DATABASE
# =========================================================

create_db()


# =========================================================
# SHOP INFORMATION
# =========================================================

@app.context_processor
def inject_shop_info():

    return {
        "shop_name": app.config.get(
            "SHOP_NAME",
            "YOUR MEDICINE SHOP"
        ),

        "shop_address": app.config.get(
            "SHOP_ADDRESS",
            "Your Shop Address"
        ),

        "shop_phone": app.config.get(
            "SHOP_PHONE",
            "01XXXXXXXXX"
        )
    }


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        con = sqlite3.connect("rms.db")

        cur = con.cursor()

        user = cur.execute(
            """
            SELECT *
            FROM users
            WHERE username=?
            AND password=?
            """,
            (
                username,
                password
            )
        ).fetchone()

        con.close()

        if user:

            session["user"] = username

            return redirect("/dashboard")

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

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


# =========================================================
# MEDICINE MANAGEMENT
# =========================================================

@app.route("/medicine", methods=["GET", "POST"])
def medicine():

    if "user" not in session:

        return redirect("/")

    con = sqlite3.connect("rms.db")

    cur = con.cursor()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        )

        company = request.form.get(
            "company",
            ""
        )

        batch = request.form.get(
            "batch",
            ""
        )

        expiry = request.form.get(
            "expiry",
            ""
        )

        buy = request.form.get(
            "buy",
            "0"
        )

        sell = request.form.get(
            "sell",
            "0"
        )

        stock = request.form.get(
            "stock",
            "0"
        )

        cur.execute(
            """
            INSERT INTO medicines
            VALUES(NULL, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                company,
                batch,
                expiry,
                buy,
                sell,
                stock
            )
        )

        con.commit()

    medicines = cur.execute(
        "SELECT * FROM medicines"
    ).fetchall()

    con.close()

    return render_template(
        "medicine.html",
        medicines=medicines
    )


# =========================================================
# PURCHASE
# =========================================================

@app.route("/purchase", methods=["GET", "POST"])
def purchase():

    if "user" not in session:

        return redirect("/")

    if request.method == "POST":

        supplier = request.form.get(
            "supplier",
            ""
        )

        product = request.form.getlist(
            "product[]"
        )

        qty = request.form.getlist(
            "qty[]"
        )

        mrp = request.form.getlist(
            "mrp[]"
        )

        price = request.form.getlist(
            "price[]"
        )

        total = 0

        for i in range(len(product)):

            q = 0

            p = 0

            if i < len(qty) and qty[i]:

                try:
                    q = int(qty[i])
                except:
                    q = 0

            if i < len(price) and price[i]:

                try:
                    p = float(price[i])
                except:
                    p = 0

            total += q * p

        session["invoice"] = {

            "supplier": supplier,

            "product": product,

            "qty": qty,

            "mrp": mrp,

            "price": price,

            "total": total,

            "date": str(
                datetime.now().date()
            )
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

    return render_template(
        "purchase.html"
    )


# =========================================================
# PURCHASE PDF
# =========================================================

@app.route("/download_pdf")
def download_pdf():

    data = session.get(
        "invoice"
    )

    if not data:

        return "No Invoice Data"

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "Procurement Invoice",
            styles["Title"]
        )
    )

    content.append(
        Spacer(1, 20)
    )

    content.append(
        Paragraph(
            "Date: " + str(
                data["date"]
            ),
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            "Supplier: " + str(
                data["supplier"]
            ),
            styles["Normal"]
        )
    )

    content.append(
        Spacer(1, 20)
    )

    rows = [

        [
            "#",
            "Product",
            "Qty",
            "Unit Price",
            "MRP",
            "Total"
        ]

    ]

    grand = 0

    for i in range(
        len(data["product"])
    ):

        name = data["product"][i].strip()

        if not name:

            continue

        try:

            q = int(
                data["qty"][i]
            ) if (
                i < len(data["qty"])
                and data["qty"][i]
            ) else 0

        except:

            q = 0

        try:

            m = float(
                data["mrp"][i]
            ) if (
                i < len(data["mrp"])
                and data["mrp"][i]
            ) else 0

        except:

            m = 0

        try:

            p = float(
                data["price"][i]
            ) if (
                i < len(data["price"])
                and data["price"][i]
            ) else 0

        except:

            p = 0

        item_total = q * p

        grand += item_total

        rows.append(
            [
                str(i + 1),
                name,
                str(q),
                f"{p:.2f}",
                f"{m:.2f}",
                f"{item_total:.2f}"
            ]
        )

    rows.append(
        [
            "",
            "",
            "",
            "",
            "Grand Total",
            f"{grand:.2f}"
        ]
    )

    table = Table(rows)

    table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            )

        ])
    )

    content.append(table)

    def add_footer(
        canv,
        doc
    ):

        canv.saveState()

        canv.setFont(
            "Helvetica",
            9
        )

        canv.drawCentredString(
            A4[0] / 2,
            30,
            "Copyright © 2026 Himel | Version 1.0"
        )

        canv.restoreState()

    doc.build(
        content,
        onFirstPage=add_footer,
        onLaterPages=add_footer
    )

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="invoice.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# SALES PAGE
# =========================================================

@app.route("/sales", methods=["GET"])
def sales():

    if "user" not in session:

        return redirect("/")

    return render_template(
        "sales.html"
    )


# =========================================================
# SALES INVOICE
# =========================================================

@app.route(
    "/sales_invoice",
    methods=["GET", "POST"]
)
def sales_invoice():

    if "user" not in session:

        return redirect("/")

    # -----------------------------------------------------
    # CREATE SALES INVOICE
    # -----------------------------------------------------

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name",
            "Walk-in Customer"
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        try:

            discount_percent = float(
                request.form.get(
                    "discount_percent",
                    0
                ) or 0
            )

        except:

            discount_percent = 0

        try:

            received = float(
                request.form.get(
                    "received",
                    0
                ) or 0
            )

        except:

            received = 0

        # -------------------------------------------------
        # PRODUCTS
        # -------------------------------------------------

        product_names = request.form.getlist(
            "product_name[]"
        )

        quantities = request.form.getlist(
            "qty[]"
        )

        prices = request.form.getlist(
            "price[]"
        )

        products = []

        total = 0

        for i in range(
            len(product_names)
        ):

            name = product_names[i].strip()

            if not name:

                continue

            # Quantity

            try:

                qty = float(
                    quantities[i]
                )

            except:

                qty = 1

            # Price

            try:

                price = float(
                    prices[i]
                )

            except:

                price = 0

            amount = qty * price

            total += amount

            products.append({

                "name": name,

                "qty": qty,

                "price": price,

                "amount": amount

            })

        # -------------------------------------------------
        # CALCULATION
        # -------------------------------------------------

        discount = (
            total
            * discount_percent
            / 100
        )

        payable = (
            total - discount
        )

        due = (
            payable - received
        )

        # -------------------------------------------------
        # BILL NUMBER
        # -------------------------------------------------

        bill_no = datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )

        # -------------------------------------------------
        # INVOICE DATA
        # -------------------------------------------------

        invoice = {

            "bill_no": bill_no,

            "customer_name":
                customer_name,

            "location":
                location,

            "phone":
                phone,

            "date":
                datetime.now().strftime(
                    "%d.%b.%Y"
                ),

            "time":
                datetime.now().strftime(
                    "%I:%M:%S %p"
                ),

            "products":
                products,

            "total":
                total,

            "discount_percent":
                discount_percent,

            "discount":
                discount,

            "payable":
                payable,

            "received":
                received,

            "due":
                due
        }

        # -------------------------------------------------
        # SAVE IN SESSION
        # -------------------------------------------------

        session["sales_invoice"] = invoice

        return redirect(
            "/sales_invoice"
        )

    # -----------------------------------------------------
    # SHOW INVOICE
    # -----------------------------------------------------

    invoice = session.get(
        "sales_invoice"
    )

    return render_template(
        "sales_invoice.html",
        invoice=invoice
    )


# =========================================================
# SALES PDF
# =========================================================

@app.route("/download_sales_pdf")
def download_sales_pdf():

    invoice = session.get("sales_invoice")

    if not invoice:
        return "No Sales Invoice Found"

    from io import BytesIO

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=35,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    content = []

    # ================= SHOP HEADER =================

    shop_name = app.config.get(
        "SHOP_NAME",
        "Era Medicine Shop"
    )

    shop_address = app.config.get(
        "SHOP_ADDRESS",
        "Station Road (Nearest New Medilab), Kishoreganj."
    )

    shop_phone = app.config.get(
        "SHOP_PHONE",
        "01913-116240"
    )

    content.append(
        Paragraph(
            f"<b><font size='18'>{shop_name}</font></b>",
            styles["Title"]
        )
    )

    content.append(
        Paragraph(
            shop_address,
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Hot Line: {shop_phone}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            "@gmail.com",
            styles["Normal"]
        )
    )

    content.append(
        Spacer(1, 6)
    )

    content.append(
        Paragraph(
            "<b><font size='15'>Sales Invoice</font></b>",
            styles["Heading2"]
        )
    )

    content.append(
        Spacer(1, 5)
    )


    # ================= CUSTOMER DETAILS =================

    customer_data = [

        [
            Paragraph(
                f"<b>Bill No.:</b> {invoice['bill_no']}",
                styles["Normal"]
            ),

            Paragraph(
                f"<b>Date:</b> {invoice['date']}",
                styles["Normal"]
            )
        ],

        [
            Paragraph(
                f"<b>C.Name:</b> {invoice.get('customer_name', 'Walk-in Customer')}",
                styles["Normal"]
            ),

            Paragraph(
                f"<b>Time:</b> {invoice['time']}",
                styles["Normal"]
            )
        ],

        [
            Paragraph(
                f"<b>Location:</b> {invoice.get('location', '-') or '-'}",
                styles["Normal"]
            ),

            Paragraph(
                f"<b>Phone:</b> {invoice.get('phone', '-') or '-'}",
                styles["Normal"]
            )
        ]

    ]


    customer_table = Table(
        customer_data,
        colWidths=[270, 230]
    )

    customer_table.setStyle(
        TableStyle([

            ("LINEABOVE", (0,0), (-1,0), 1, colors.black),

            ("LINEBELOW", (0,-1), (-1,-1), 1, colors.black),

            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

            ("LEFTPADDING", (0,0), (-1,-1), 2),

            ("RIGHTPADDING", (0,0), (-1,-1), 2),

            ("TOPPADDING", (0,0), (-1,-1), 5),

            ("BOTTOMPADDING", (0,0), (-1,-1), 5)

        ])
    )

    content.append(customer_table)

    content.append(
        Spacer(1, 8)
    )


    # ================= PRODUCT TABLE =================

    table_data = [

        [
            "S.No.",
            "Product Name",
            "Qty",
            "Price",
            "Amount"
        ]

    ]


    for i, product in enumerate(
        invoice.get("products", []),
        start=1
    ):

        qty = product.get("qty", 0)
        price = product.get("price", 0)
        amount = product.get("amount", 0)

        if float(qty).is_integer():
            qty_text = str(int(qty))
        else:
            qty_text = f"{qty:g}"

        table_data.append([

            str(i),

            product.get("name", ""),

            qty_text,

            f"{float(price):.2f}",

            f"{float(amount):.2f}"

        ])


    product_table = Table(
        table_data,
        colWidths=[
            50,
            225,
            55,
            80,
            90
        ],
        repeatRows=1
    )


    product_table.setStyle(
        TableStyle([

            # Header
            (
                "FONTNAME",
                (0,0),
                (-1,0),
                "Helvetica-Bold"
            ),

            (
                "ALIGN",
                (0,0),
                (-1,0),
                "CENTER"
            ),

            (
                "LINEABOVE",
                (0,0),
                (-1,0),
                1,
                colors.black
            ),

            (
                "LINEBELOW",
                (0,0),
                (-1,0),
                1,
                colors.black
            ),

            # Body
            (
                "LINEBELOW",
                (0,-1),
                (-1,-1),
                1,
                colors.black
            ),

            (
                "ALIGN",
                (0,1),
                (0,-1),
                "LEFT"
            ),

            (
                "ALIGN",
                (1,1),
                (1,-1),
                "LEFT"
            ),

            (
                "ALIGN",
                (2,1),
                (-1,-1),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0,0),
                (-1,-1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0,0),
                (-1,-1),
                5
            ),

            (
                "LEFTPADDING",
                (0,0),
                (-1,-1),
                4
            ),

            (
                "RIGHTPADDING",
                (0,0),
                (-1,-1),
                4
            )

        ])
    )


    content.append(product_table)

    content.append(
        Spacer(1, 8)
    )


    # ================= TOTAL =================

    summary_data = [

        [
            Paragraph(
                "<b>Total Tk. :</b>",
                styles["Normal"]
            ),

            Paragraph(
                f"<b>{invoice['total']:.2f}</b>",
                styles["Normal"]
            )
        ],

        [
            Paragraph(
                "Discount (-) :",
                styles["Normal"]
            ),

            Paragraph(
                f"{invoice['discount']:.2f}",
                styles["Normal"]
            )
        ],

        [
            Paragraph(
                "Payable Tk. :",
                styles["Normal"]
            ),

            Paragraph(
                f"<b>{invoice['payable']:.2f}</b>",
                styles["Normal"]
            )
        ],

        [
            Paragraph(
                "Received Tk. :",
                styles["Normal"]
            ),

            Paragraph(
                f"{invoice['received']:.2f}",
                styles["Normal"]
            )
        ],

        [
            Paragraph(
                "Due Tk. :",
                styles["Normal"]
            ),

            Paragraph(
                f"{invoice['due']:.2f}",
                styles["Normal"]
            )
        ]

    ]


    summary_table = Table(
        summary_data,
        colWidths=[350, 150]
    )


    summary_table.setStyle(
        TableStyle([

            (
                "LINEABOVE",
                (0,0),
                (-1,0),
                1,
                colors.black
            ),

            (
                "ALIGN",
                (0,0),
                (0,-1),
                "RIGHT"
            ),

            (
                "ALIGN",
                (1,0),
                (1,-1),
                "RIGHT"
            ),

            (
                "FONTNAME",
                (0,0),
                (-1,0),
                "Helvetica-Bold"
            ),

            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0,0),
                (-1,-1),
                4
            ),

            (
                "BOTTOMPADDING",
                (0,0),
                (-1,-1),
                4
            ),

            (
                "LEFTPADDING",
                (0,0),
                (-1,-1),
                3
            ),

            (
                "RIGHTPADDING",
                (0,0),
                (-1,-1),
                3
            )

        ])
    )


    content.append(summary_table)


    # ================= SIGNATURE =================

    content.append(
        Spacer(1, 25)
    )

    content.append(
        Paragraph(
            "Signature Of<br/>[Salesman]",
            styles["Normal"]
        )
    )


    # ================= THANK YOU =================

    content.append(
        Spacer(1, 25)
    )

    content.append(
        Paragraph(
            "<b>....Thank You....</b>",
            styles["Normal"]
        )
    )


    content.append(
        Spacer(1, 5)
    )

    content.append(
        Paragraph(
            "Developed By:- Dream Soft Tech, Mo:-0171",
            styles["Normal"]
        )
    )


    # ================= BUILD PDF =================

    doc.build(content)

    buffer.seek(0)


    return send_file(
        buffer,
        as_attachment=True,
        download_name=
        f"sales_invoice_{invoice['bill_no']}.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    shop_name = input(
        "Enter Shop Name: "
    )

    shop_address = input(
        "Enter Shop Address: "
    )

    shop_phone = input(
        "Enter Shop Phone: "
    )

    port_input = input(
        "Enter port number (Default 5000): "
    )

    if port_input.strip():

        try:

            port = int(
                port_input
            )

        except:

            print(
                "Invalid port. Using 5000."
            )

            port = 5000

    else:

        port = 5000

    # -----------------------------------------------------
    # SHOP CONFIG
    # -----------------------------------------------------

    app.config[
        "SHOP_NAME"
    ] = shop_name

    app.config[
        "SHOP_ADDRESS"
    ] = shop_address

    app.config[
        "SHOP_PHONE"
    ] = shop_phone

    # -----------------------------------------------------
    # START MESSAGE
    # -----------------------------------------------------

    print(
        "\n=============================="
    )

    print(
        "🧾 Medicine Management System"
    )

    print(
        "=============================="
    )

    print(
        f"🏪 Shop: {shop_name}"
    )

    print(
        f"📍 Address: {shop_address}"
    )

    print(
        f"📞 Phone: {shop_phone}"
    )

    print(
        f"🌐 Port: {port}"
    )

    print(
        "==============================\n"
    )

    # -----------------------------------------------------
    # RUN FLASK
    # -----------------------------------------------------

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )