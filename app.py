import streamlit as st
import pandas as pd
import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract

st.set_page_config(page_title="Processing SHEIN Order", layout="centered")

DATA_FILE = "products.csv"
COLUMNS = ["sku", "customer_name", "status", "order_complete"]

STATUS_NOT_ARRIVED = "لم يصل"
STATUS_ARRIVED = "وصل"


def load_data():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

    df = pd.read_csv(DATA_FILE)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = False if col == "order_complete" else ""

    df["status"] = df["status"].replace({
        "لم يتم فرزه": STATUS_NOT_ARRIVED,
        "تم فرزه": STATUS_ARRIVED,
        "تم تسليمه": STATUS_ARRIVED,
        "": STATUS_NOT_ARRIVED
    }).fillna(STATUS_NOT_ARRIVED)

    df["order_complete"] = df["order_complete"].fillna(False).astype(bool)

    return df[COLUMNS]


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def empty_data():
    return pd.DataFrame(columns=COLUMNS)


def extract_skus_from_text(text):
    if not text:
        return []

    cleaned = text.replace("：", ":").replace("\n", " ")
    skus = re.findall(r"\b[sS][a-zA-Z]{0,12}\d{8,30}\b", cleaned)

    unique_skus = []
    seen = set()

    for sku in skus:
        sku = sku.strip()
        key = sku.lower()

        if key not in seen:
            seen.add(key)
            unique_skus.append(sku)

    return unique_skus


def extract_sku_from_image(image_file):
    image = Image.open(image_file).convert("RGB")
    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    text = pytesseract.image_to_string(gray, config="--psm 6")
    skus = extract_skus_from_text(text)

    return skus[0] if skus else ""


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --bg: #05030A;
            --card: rgba(255,255,255,0.07);
            --card2: rgba(120,35,255,0.18);
            --line: rgba(255,255,255,0.14);
            --purple: #7A23FF;
            --purple2: #B388FF;
            --text: #F7F4FF;
            --muted: #BDB5D6;
            --green: #48E88B;
            --red: #FF6178;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 50% -10%, rgba(122,35,255,0.65), transparent 42%),
                linear-gradient(180deg, #090512 0%, #05030A 100%) !important;
            color: var(--text) !important;
            direction: rtl;
            overflow-x: hidden !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            display: none !important;
        }

        .main .block-container {
            max-width: 940px !important;
            padding: 28px 28px 42px 28px !important;
            margin-top: 14px;
            margin-bottom: 24px;
            background: rgba(5, 3, 10, 0.74);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 28px;
            box-shadow: 0 0 90px rgba(122,35,255,0.22);
            backdrop-filter: blur(16px);
        }

        .brand {
            text-align: center;
            font-size: 20px;
            font-weight: 900;
            color: white;
            direction: ltr;
            margin-bottom: 10px;
        }

        .brand span {
            color: var(--purple2);
        }

        .hero {
            text-align: center;
            padding: 28px 0 22px 0;
            position: relative;
        }

        .hero::before {
            content: "";
            position: absolute;
            left: 50%;
            top: -28px;
            transform: translateX(-50%);
            width: 85%;
            height: 190px;
            background: radial-gradient(ellipse at center, rgba(154,88,255,0.8), rgba(122,35,255,0.25) 48%, transparent 72%);
            filter: blur(26px);
            z-index: 0;
        }

        .hero-title {
            position: relative;
            z-index: 1;
            direction: ltr;
            font-family: Impact, "Arial Black", sans-serif;
            font-size: clamp(42px, 9vw, 84px);
            line-height: 0.98;
            letter-spacing: -1px;
            color: white;
            text-transform: uppercase;
            text-shadow: 0 0 28px rgba(179,136,255,0.48);
        }

        .hero-subtitle {
            position: relative;
            z-index: 1;
            max-width: 650px;
            margin: 18px auto 0 auto;
            color: var(--muted);
            line-height: 1.8;
            font-size: 14px;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            font-weight: 900 !important;
        }

        label, p, span, div {
            font-family: Arial, sans-serif;
        }

        .glass-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 18px 50px rgba(0,0,0,0.24);
        }

        .purple-card {
            background: linear-gradient(145deg, rgba(122,35,255,0.25), rgba(255,255,255,0.055));
            border: 1px solid rgba(179,136,255,0.28);
            border-radius: 22px;
            padding: 20px;
            margin: 16px 0;
        }

        .complete-card {
            background: linear-gradient(145deg, rgba(72,232,139,0.16), rgba(255,255,255,0.05));
            border: 1px solid rgba(72,232,139,0.35);
            border-radius: 22px;
            padding: 20px;
            margin: 16px 0;
        }

        .pending-card {
            background: linear-gradient(145deg, rgba(122,35,255,0.20), rgba(255,255,255,0.05));
            border: 1px solid rgba(179,136,255,0.25);
            border-radius: 22px;
            padding: 20px;
            margin: 16px 0;
        }

        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 6px 13px;
            font-size: 11px;
            font-weight: 900;
            direction: ltr;
        }

        .badge-complete {
            background: rgba(72,232,139,0.12);
            color: var(--green);
            border: 1px solid rgba(72,232,139,0.35);
        }

        .badge-pending {
            background: rgba(122,35,255,0.22);
            color: var(--purple2);
            border: 1px solid rgba(179,136,255,0.35);
        }

        div.stButton > button {
            background: linear-gradient(135deg, #7A23FF, #4B00C9) !important;
            color: white !important;
            border: 1px solid rgba(179,136,255,0.45) !important;
            border-radius: 14px !important;
            font-weight: 900 !important;
            padding: 0.72rem 1rem !important;
            width: 100%;
            box-shadow: 0 0 24px rgba(122,35,255,0.26);
        }

        div.stButton > button:hover {
            filter: brightness(1.15);
            border: 1px solid white !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] {
            background: rgba(255,255,255,0.08) !important;
            color: white !important;
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.16) !important;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 16px;
        }

        [data-testid="stMetricValue"] {
            color: white !important;
            font-size: 32px !important;
            font-weight: 900 !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
        }

        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #7A23FF, #B388FF) !important;
        }

        hr {
            border-color: rgba(255,255,255,0.12) !important;
            margin: 24px 0 !important;
        }

        @media (max-width: 768px) {
            .main .block-container {
                width: calc(100% - 14px) !important;
                max-width: calc(100% - 14px) !important;
                margin: 7px auto 16px auto !important;
                padding: 18px 14px 30px 14px !important;
                border-radius: 20px !important;
            }

            .brand {
                font-size: 18px !important;
                margin-top: 8px;
            }

            .hero {
                padding: 22px 0 18px 0 !important;
            }

            .hero::before {
                width: 100%;
                height: 150px;
                top: -8px;
            }

            .hero-title {
                font-size: 38px !important;
                line-height: 1.02 !important;
                letter-spacing: -0.5px !important;
            }

            .hero-subtitle {
                font-size: 13px !important;
                line-height: 1.75 !important;
                padding: 0 6px;
            }

            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 0.8rem !important;
            }

            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }

            .glass-card,
            .purple-card,
            .complete-card,
            .pending-card {
                padding: 15px !important;
                border-radius: 18px !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 28px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


apply_theme()

st.markdown(
    """
    <div class="brand">SHEIN<span>sort.</span></div>
    <div class="hero">
        <div class="hero-title">Processing<br>SHEIN Order</div>
        <div class="hero-subtitle">
            نظام بسيط لتسجيل طلبات الزبائن، متابعة القطع التي وصلت، وتحديد الطلبات المكتملة.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

menu = [
    "تسجيل سلة",
    "فرز القطع",
    "لوحة التحكم",
    "تعديل الطلبات",
    "إدارة البيانات"
]

choice = st.selectbox("القسم", menu)

df = load_data()

if choice == "تسجيل سلة":
    st.subheader("تسجيل سلة زبونة")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    cust_name = st.text_input("اسم الزبونة")
    basket_data = st.text_area("الصقي هنا أكواد أو تفاصيل الطلب", height=220)

    found_skus = extract_skus_from_text(basket_data)

    if basket_data:
        st.info(f"تم العثور على {len(found_skus)} كود محتمل.")

    if st.button("حفظ القطع"):
        if cust_name and basket_data:
            skus = extract_skus_from_text(basket_data)

            if skus:
                new_items = []
                repeated = []

                for sku in skus:
                    exists = df["sku"].astype(str).str.lower().eq(sku.lower()).any()

                    if not exists:
                        new_items.append({
                            "sku": sku,
                            "customer_name": cust_name,
                            "status": STATUS_NOT_ARRIVED,
                            "order_complete": False
                        })
                    else:
                        repeated.append(sku)

                if new_items:
                    df = pd.concat([df, pd.DataFrame(new_items)], ignore_index=True)
                    save_data(df)
                    st.success(f"تم حفظ {len(new_items)} قطعة باسم {cust_name}.")

                    with st.expander("الأكواد المحفوظة"):
                        for item in new_items:
                            st.write(item["sku"])

                if repeated:
                    st.warning(f"تم تجاهل {len(repeated)} كود مكرر.")
            else:
                st.error("لم يتم العثور على أكواد صالحة.")
        else:
            st.error("يرجى إدخال اسم الزبونة والنص.")

    st.markdown('</div>', unsafe_allow_html=True)


elif choice == "فرز القطع":
    st.subheader("فرز القطع")

    st.markdown('<div class="purple-card">', unsafe_allow_html=True)

    img_file_buffer = st.camera_input("صوّري ملصق القطعة بوضوح")

    scanned_sku = ""

    if img_file_buffer is not None:
        scanned_sku = extract_sku_from_image(img_file_buffer)

        if scanned_sku:
            st.success(f"تم استخراج الكود: {scanned_sku}")
        else:
            st.warning("لم يتم التعرف على الكود. قرّبي الصورة وحسّني الإضاءة.")

    scan = st.text_input("اكتبي أو صوّري كود القطعة", value=scanned_sku)

    if scan:
        normalized_scan = scan.strip().lower()
        res = df[df["sku"].astype(str).str.lower().str.contains(normalized_scan, na=False)]

        if not res.empty:
            item = res.iloc[0]

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.success(f"الزبونة: {item['customer_name']}")
            st.info(f"الكود: {item['sku']}")
            st.write(f"الحالة الحالية: {item['status']}")
            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("وصلت القطعة"):
                    df.loc[df["sku"].astype(str).str.lower() == str(item["sku"]).lower(), "status"] = STATUS_ARRIVED
                    save_data(df)
                    st.rerun()

            with col2:
                if st.button("لم تصل"):
                    df.loc[df["sku"].astype(str).str.lower() == str(item["sku"]).lower(), "status"] = STATUS_NOT_ARRIVED
                    save_data(df)
                    st.rerun()

        else:
            st.error("هذه القطعة غير مسجلة.")

    st.markdown('</div>', unsafe_allow_html=True)


elif choice == "لوحة التحكم":
    st.subheader("لوحة التحكم")

    total = len(df)
    arrived_count = len(df[df["status"] == STATUS_ARRIVED])
    remaining_count = total - arrived_count
    completed_customers = df.groupby("customer_name")["order_complete"].max().sum() if not df.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي القطع", total)
    c2.metric("وصل", arrived_count)
    c3.metric("المتبقي", remaining_count)

    st.markdown("---")
    st.subheader("طلبات الزبائن")

    if not df.empty:
        summary = df.groupby("customer_name").agg(
            total=("sku", "count"),
            arrived=("status", lambda x: (x == STATUS_ARRIVED).sum()),
            complete=("order_complete", "max")
        ).reset_index()

        summary["remaining"] = summary["total"] - summary["arrived"]

        for _, row in summary.iterrows():
            name = row["customer_name"]
            total_items = int(row["total"])
            arrived = int(row["arrived"])
            remaining = int(row["remaining"])
            complete = bool(row["complete"])

            card_class = "complete-card" if complete else "pending-card"
            badge_class = "badge-complete" if complete else "badge-pending"
            badge = "مكتمل" if complete else "غير مكتمل"

            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<span class="badge {badge_class}">{badge}</span>', unsafe_allow_html=True)
            st.markdown(f"### {name}")

            m1, m2, m3 = st.columns(3)
            m1.metric("كل القطع", total_items)
            m2.metric("وصل", arrived)
            m3.metric("المتبقي", remaining)

            if total_items > 0:
                st.progress(arrived / total_items)

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        selected_customer = st.selectbox(
            "عرض تفاصيل زبونة",
            ["الكل"] + sorted(df["customer_name"].dropna().unique().tolist())
        )

        filtered_df = df.copy()

        if selected_customer != "الكل":
            filtered_df = filtered_df[filtered_df["customer_name"] == selected_customer]

        st.dataframe(filtered_df, use_container_width=True)

    else:
        st.info("لا توجد بيانات حالياً.")


elif choice == "تعديل الطلبات":
    st.subheader("تعديل الطلبات")

    customers = sorted(df["customer_name"].dropna().unique().tolist())

    if customers:
        customer = st.selectbox("اختاري الزبونة", customers)
        customer_df = df[df["customer_name"] == customer]

        total_items = len(customer_df)
        arrived = len(customer_df[customer_df["status"] == STATUS_ARRIVED])
        remaining = total_items - arrived
        current_complete = bool(customer_df["order_complete"].max())

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.metric("إجمالي القطع", total_items)
        st.metric("وصل", arrived)
        st.metric("المتبقي", remaining)

        complete_value = st.checkbox("الطلب مكتمل", value=current_complete)

        if st.button("حفظ حالة الطلب"):
            df.loc[df["customer_name"] == customer, "order_complete"] = complete_value
            save_data(df)
            st.success("تم حفظ حالة الطلب.")
            st.rerun()

        if st.button("اعتبار كل القطع وصلت"):
            df.loc[df["customer_name"] == customer, "status"] = STATUS_ARRIVED
            save_data(df)
            st.rerun()

        if st.button("إرجاع كل القطع إلى لم يصل"):
            df.loc[df["customer_name"] == customer, "status"] = STATUS_NOT_ARRIVED
            save_data(df)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("تعديل القطع")

        editable = customer_df[["sku", "status"]].copy()

        edited = st.data_editor(
            editable,
            use_container_width=True,
            hide_index=True,
            column_config={
                "sku": st.column_config.TextColumn("الكود", disabled=True),
                "status": st.column_config.SelectboxColumn(
                    "الحالة",
                    options=[STATUS_NOT_ARRIVED, STATUS_ARRIVED],
                    required=True
                )
            }
        )

        if st.button("حفظ تعديلات القطع"):
            for i, row in edited.iterrows():
                sku = row["sku"]
                new_status = row["status"]
                df.loc[df["sku"] == sku, "status"] = new_status

            save_data(df)
            st.success("تم حفظ تعديلات القطع.")
            st.rerun()

    else:
        st.info("لا يوجد زبائن حالياً.")


else:
    st.subheader("إدارة البيانات")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    if st.button("مسح كل الطلبيات"):
        save_data(empty_data())
        st.success("تم مسح كل الطلبيات.")
        st.rerun()

    st.markdown("---")

    customers = sorted(df["customer_name"].dropna().unique().tolist())

    if customers:
        customer_to_delete = st.selectbox("اختر زبون لحذفه", customers)

        if st.button("حذف هذا الزبون"):
            df = df[df["customer_name"] != customer_to_delete]
            save_data(df)
            st.success(f"تم حذف بيانات {customer_to_delete}.")
            st.rerun()
    else:
        st.info("لا يوجد زبائن لحذفهم.")

    st.markdown('</div>', unsafe_allow_html=True)