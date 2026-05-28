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
COLUMNS = ["sku", "customer_name", "status"]

STATUS_NOT_ARRIVED = "لم يصل"
STATUS_ARRIVED = "وصل"
STATUS_DELIVERED = "تم تسليمه"


def load_data():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

    df = pd.read_csv(DATA_FILE)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS]

    # تحويل الحالات القديمة للنظام الجديد
    df["status"] = df["status"].replace({
        "لم يتم فرزه": STATUS_NOT_ARRIVED,
        "تم فرزه": STATUS_ARRIVED,
        "": STATUS_NOT_ARRIVED
    })

    df["status"] = df["status"].fillna(STATUS_NOT_ARRIVED)

    return df


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

    if skus:
        return skus[0]

    return ""


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --bg: #05030A;
            --panel: #0C0814;
            --card: rgba(255,255,255,0.055);
            --card2: rgba(122, 35, 255, 0.18);
            --line: rgba(255,255,255,0.14);
            --purple: #7A23FF;
            --purple2: #B388FF;
            --text: #F7F4FF;
            --muted: #AFA7C7;
            --green: #46E68A;
            --red: #FF5D73;
            --gold: #E9C46A;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 50% 0%, rgba(122,35,255,0.55) 0%, rgba(122,35,255,0.20) 22%, transparent 48%),
                linear-gradient(180deg, #090512 0%, #05030A 100%) !important;
            color: var(--text) !important;
            direction: rtl;
            overflow-x: hidden !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        .main .block-container {
            max-width: 1050px !important;
            padding: 34px 38px 52px 38px !important;
            margin-top: 18px;
            margin-bottom: 25px;
            background: rgba(5, 3, 10, 0.82);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 28px;
            box-shadow: 0 0 80px rgba(122,35,255,0.22);
            backdrop-filter: blur(14px);
        }

        [data-testid="stSidebar"] {
            background: #090512 !important;
            border-left: 1px solid rgba(122,35,255,0.35);
        }

        .top-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            direction: ltr;
            margin-bottom: 28px;
        }

        .logo {
            font-size: 19px;
            font-weight: 900;
            color: white;
            letter-spacing: -0.5px;
        }

        .logo span {
            color: var(--purple2);
        }

        .nav-links {
            display: flex;
            gap: 22px;
            font-size: 10px;
            font-weight: 800;
            color: var(--muted);
            text-transform: uppercase;
        }

        .hero {
            text-align: center;
            padding: 44px 10px 34px 10px;
            position: relative;
        }

        .hero::before {
            content: "";
            position: absolute;
            left: 50%;
            top: -20px;
            transform: translateX(-50%);
            width: 78%;
            height: 220px;
            background: radial-gradient(ellipse at center, rgba(154,88,255,0.85), rgba(122,35,255,0.28) 45%, transparent 72%);
            filter: blur(26px);
            z-index: 0;
        }

        .hero-title {
            position: relative;
            z-index: 1;
            direction: ltr;
            font-family: Impact, "Arial Black", sans-serif;
            font-size: clamp(44px, 9vw, 92px);
            line-height: 0.95;
            letter-spacing: -1.8px;
            color: white;
            text-shadow: 0 0 28px rgba(179,136,255,0.45);
            text-transform: uppercase;
        }

        .hero-subtitle {
            position: relative;
            z-index: 1;
            max-width: 620px;
            margin: 18px auto 0 auto;
            color: var(--muted);
            line-height: 1.8;
            font-size: 14px;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            font-weight: 900 !important;
        }

        .glass-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 22px;
            margin: 16px 0;
            box-shadow: 0 22px 55px rgba(0,0,0,0.28);
        }

        .purple-card {
            background: linear-gradient(145deg, rgba(122,35,255,0.28), rgba(255,255,255,0.045));
            border: 1px solid rgba(179,136,255,0.28);
            border-radius: 22px;
            padding: 22px;
            margin: 16px 0;
            box-shadow: 0 0 38px rgba(122,35,255,0.16);
        }

        .complete-card {
            background: linear-gradient(145deg, rgba(70,230,138,0.17), rgba(255,255,255,0.045));
            border: 1px solid rgba(70,230,138,0.38);
            border-radius: 22px;
            padding: 22px;
            margin: 16px 0;
        }

        .pending-card {
            background: linear-gradient(145deg, rgba(122,35,255,0.21), rgba(255,255,255,0.045));
            border: 1px solid rgba(179,136,255,0.28);
            border-radius: 22px;
            padding: 22px;
            margin: 16px 0;
        }

        .delivered-card {
            background: linear-gradient(145deg, rgba(233,196,106,0.18), rgba(255,255,255,0.04));
            border: 1px solid rgba(233,196,106,0.36);
            border-radius: 22px;
            padding: 22px;
            margin: 16px 0;
        }

        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 6px 13px;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 0.7px;
            direction: ltr;
        }

        .badge-ready {
            background: rgba(70,230,138,0.14);
            color: var(--green);
            border: 1px solid rgba(70,230,138,0.32);
        }

        .badge-pending {
            background: rgba(122,35,255,0.20);
            color: var(--purple2);
            border: 1px solid rgba(179,136,255,0.32);
        }

        .badge-delivered {
            background: rgba(233,196,106,0.15);
            color: var(--gold);
            border: 1px solid rgba(233,196,106,0.32);
        }

        div.stButton > button {
            background: linear-gradient(135deg, #7A23FF, #4B00C9) !important;
            color: white !important;
            border: 1px solid rgba(179,136,255,0.45) !important;
            border-radius: 14px !important;
            font-weight: 900 !important;
            padding: 0.72rem 1rem !important;
            width: 100%;
            box-shadow: 0 0 22px rgba(122,35,255,0.25);
        }

        div.stButton > button:hover {
            filter: brightness(1.16);
            border: 1px solid white !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] {
            background: rgba(255,255,255,0.07) !important;
            color: white !important;
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.13) !important;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.055);
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
            margin: 28px 0 !important;
        }

        @media (max-width: 768px) {
            .main .block-container {
                width: calc(100% - 16px) !important;
                max-width: calc(100% - 16px) !important;
                margin: 8px auto 18px auto !important;
                padding: 20px 14px 34px 14px !important;
                border-radius: 22px !important;
            }

            .top-nav {
                display: block;
                text-align: center;
            }

            .nav-links {
                justify-content: center;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 12px;
                font-size: 9px;
            }

            .hero {
                padding: 28px 0 22px 0;
            }

            .hero::before {
                width: 100%;
                height: 170px;
                top: -8px;
            }

            .hero-title {
                font-size: 42px !important;
                line-height: 1 !important;
                letter-spacing: -1px !important;
            }

            .hero-subtitle {
                font-size: 13px !important;
                line-height: 1.7 !important;
            }

            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 0.75rem !important;
            }

            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }

            .glass-card,
            .purple-card,
            .complete-card,
            .pending-card,
            .delivered-card {
                padding: 15px !important;
                border-radius: 18px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


apply_theme()

st.markdown(
    """
    <div class="top-nav">
        <div class="logo">SHEIN<span>sort.</span></div>
        <div class="nav-links">
            <span>Add Order</span>
            <span>Scan</span>
            <span>Dashboard</span>
            <span>Delivery</span>
        </div>
    </div>

    <div class="hero">
        <div class="hero-title">Processing<br>SHEIN Order</div>
        <div class="hero-subtitle">
            نظام فرز وتتبع ذكي لطلبات شي إن — من تسجيل السلة، إلى وصول القطع، وحتى تسليم الطلب كامل للزبونة.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

menu = [
    "📥 تسجيل سلة زبونة",
    "🔍 فرز البضاعة",
    "📊 لوحة التحكم",
    "✏️ تعديل يدوي",
    "🧹 إدارة البيانات"
]

choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

df = load_data()

if choice == "📥 تسجيل سلة زبونة":
    st.subheader("تسجيل سلة زبونة")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    cust_name = st.text_input("اسم الزبونة")
    basket_data = st.text_area("الصقي هنا كل أكواد أو تفاصيل الطلب", height=220)

    found_skus = extract_skus_from_text(basket_data)

    if basket_data:
        st.info(f"تم رصد {len(found_skus)} كود محتمل داخل النص.")

    if st.button("حفظ القطع تلقائياً"):
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
                            "status": STATUS_NOT_ARRIVED
                        })
                    else:
                        repeated.append(sku)

                if new_items:
                    df = pd.concat([df, pd.DataFrame(new_items)], ignore_index=True)
                    save_data(df)
                    st.success(f"تم حفظ {len(new_items)} قطعة باسم {cust_name}.")

                    with st.expander("عرض الأكواد التي تم حفظها"):
                        for item in new_items:
                            st.write(item["sku"])

                if repeated:
                    st.warning(f"تم تجاهل {len(repeated)} كود مكرر.")
            else:
                st.error("لم أجد أكواد صالحة. تأكدي أن الأكواد تبدأ بحرف S وتحتوي أرقام.")
        else:
            st.error("يجب إدخال اسم الزبونة والنص.")

    st.markdown('</div>', unsafe_allow_html=True)


elif choice == "🔍 فرز البضاعة":
    st.subheader("فرز البضاعة")

    st.markdown('<div class="purple-card">', unsafe_allow_html=True)

    img_file_buffer = st.camera_input("صوري الليبل بوضوح، خصوصاً السطر الذي يبدأ بحرف S")

    scanned_sku = ""

    if img_file_buffer is not None:
        scanned_sku = extract_sku_from_image(img_file_buffer)

        if scanned_sku:
            st.success(f"تم استخراج SKU: {scanned_sku}")
        else:
            st.warning("لم أستطع قراءة SKU. قرّبي الليبل وخليه واضح ومضاء.")

    scan = st.text_input("صوري الكود أو اكتبي الـ SKU هنا", value=scanned_sku)

    if scan:
        normalized_scan = scan.strip().lower()
        res = df[df["sku"].astype(str).str.lower().str.contains(normalized_scan, na=False)]

        if not res.empty:
            item = res.iloc[0]

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.success(f"الزبونة: {item['customer_name']}")
            st.info(f"SKU: {item['sku']}")
            st.write(f"الحالة الحالية: {item['status']}")
            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

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

            with col3:
                if st.button("تم تسليمها"):
                    df.loc[df["sku"].astype(str).str.lower() == str(item["sku"]).lower(), "status"] = STATUS_DELIVERED
                    save_data(df)
                    st.rerun()

        else:
            st.error("هذه القطعة غير مسجلة.")

    st.markdown('</div>', unsafe_allow_html=True)


elif choice == "📊 لوحة التحكم":
    st.subheader("لوحة التحكم")

    total = len(df)
    arrived_count = len(df[df["status"].isin([STATUS_ARRIVED, STATUS_DELIVERED])])
    delivered_count = len(df[df["status"] == STATUS_DELIVERED])
    remaining_count = total - arrived_count

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي القطع", total)
    col2.metric("وصل", arrived_count)
    col3.metric("المتبقي", remaining_count)

    col4, col5 = st.columns(2)
    col4.metric("تم تسليمه", delivered_count)
    col5.metric("غير مسلم", total - delivered_count)

    st.markdown("---")
    st.subheader("حالة كل زبونة")

    if not df.empty:
        summary = df.groupby("customer_name").agg(
            total=("sku", "count"),
            arrived=("status", lambda x: x.isin([STATUS_ARRIVED, STATUS_DELIVERED]).sum()),
            delivered=("status", lambda x: (x == STATUS_DELIVERED).sum())
        ).reset_index()

        summary["remaining"] = summary["total"] - summary["arrived"]
        summary["ready"] = summary["remaining"] == 0
        summary["fully_delivered"] = summary["delivered"] == summary["total"]

        for _, row in summary.iterrows():
            name = row["customer_name"]
            total_items = int(row["total"])
            arrived = int(row["arrived"])
            delivered = int(row["delivered"])
            remaining = int(row["remaining"])
            ready = bool(row["ready"])
            fully_delivered = bool(row["fully_delivered"])

            if fully_delivered:
                card_class = "delivered-card"
                badge = "DELIVERED"
                badge_class = "badge-delivered"
                mark = "🟣"
            elif ready:
                card_class = "complete-card"
                badge = "READY"
                badge_class = "badge-ready"
                mark = "✅"
            else:
                card_class = "pending-card"
                badge = "PENDING"
                badge_class = "badge-pending"
                mark = "⏳"

            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<span class="badge {badge_class}">{badge}</span>', unsafe_allow_html=True)
            st.markdown(f"### {mark} {name}")

            c1, c2, c3 = st.columns(3)
            c1.metric("كل القطع", total_items)
            c2.metric("وصل", arrived)
            c3.metric("ضايل", remaining)

            c4, c5 = st.columns(2)
            c4.metric("تم تسليمه", delivered)
            c5.metric("جاهز؟", "نعم" if ready else "لا")

            if total_items > 0:
                st.progress(arrived / total_items)

            if fully_delivered:
                st.success("تم تسليم الطلب كامل للزبونة.")
            elif ready:
                st.success("كل القطع وصلت — جاهز للتسليم.")
            else:
                st.warning(f"لسه ضايل {remaining} قطعة.")

            if ready and not fully_delivered:
                if st.button(f"تسليم طلب {name} كامل", key=f"deliver_{name}"):
                    df.loc[df["customer_name"] == name, "status"] = STATUS_DELIVERED
                    save_data(df)
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        customers = sorted(df["customer_name"].dropna().unique().tolist())
        selected_customer = st.selectbox("عرض تفاصيل زبونة", ["الكل"] + customers)

        filtered_df = df.copy()
        if selected_customer != "الكل":
            filtered_df = filtered_df[filtered_df["customer_name"] == selected_customer]

        status_filter = st.selectbox("فلترة حسب الحالة", ["الكل", STATUS_NOT_ARRIVED, STATUS_ARRIVED, STATUS_DELIVERED])
        if status_filter != "الكل":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]

        st.dataframe(filtered_df, use_container_width=True)

        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "تحميل البيانات المعروضة",
            data=csv,
            file_name="orders_filtered.csv",
            mime="text/csv"
        )
    else:
        st.info("لا توجد بيانات بعد.")


elif choice == "✏️ تعديل يدوي":
    st.subheader("تعديل يدوي لحالة الطلبات")

    customers = sorted(df["customer_name"].dropna().unique().tolist())

    if customers:
        customer = st.selectbox("اختاري الزبونة", customers)
        customer_df = df[df["customer_name"] == customer]

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write(f"عدد القطع: {len(customer_df)}")
        st.write(f"وصل: {len(customer_df[customer_df['status'].isin([STATUS_ARRIVED, STATUS_DELIVERED])])}")
        st.write(f"لم يصل: {len(customer_df[customer_df['status'] == STATUS_NOT_ARRIVED])}")
        st.write(f"تم تسليمه: {len(customer_df[customer_df['status'] == STATUS_DELIVERED])}")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("اعتبار كل قطع الزبونة وصلت"):
            df.loc[df["customer_name"] == customer, "status"] = STATUS_ARRIVED
            save_data(df)
            st.rerun()

        if st.button("تسليم طلب الزبونة كامل"):
            df.loc[df["customer_name"] == customer, "status"] = STATUS_DELIVERED
            save_data(df)
            st.rerun()

        if st.button("إرجاع كل قطع الزبونة إلى لم يصل"):
            df.loc[df["customer_name"] == customer, "status"] = STATUS_NOT_ARRIVED
            save_data(df)
            st.rerun()

        st.markdown("---")

        for index, row in customer_df.iterrows():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write(f"SKU: {row['sku']}")
            st.write(f"الحالة الحالية: {row['status']}")

            new_status = st.selectbox(
                "تغيير الحالة",
                [STATUS_NOT_ARRIVED, STATUS_ARRIVED, STATUS_DELIVERED],
                index=[STATUS_NOT_ARRIVED, STATUS_ARRIVED, STATUS_DELIVERED].index(row["status"])
                if row["status"] in [STATUS_NOT_ARRIVED, STATUS_ARRIVED, STATUS_DELIVERED] else 0,
                key=f"status_{index}"
            )

            if st.button("حفظ هذه القطعة", key=f"save_{index}"):
                df.loc[index, "status"] = new_status
                save_data(df)
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("لا توجد زبائن بعد.")


else:
    st.subheader("إدارة البيانات")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.warning("قبل أي حذف، حمّلي نسخة احتياطية.")

    backup_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "تحميل Backup كامل",
        data=backup_csv,
        file_name="orders_backup.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("مسح كل البيانات")

    confirm_delete_all = st.text_input("للمسح الكامل اكتبي: حذف الكل")

    if st.button("مسح كل الطلبيات"):
        if confirm_delete_all == "حذف الكل":
            save_data(empty_data())
            st.success("تم مسح كل الطلبيات.")
            st.rerun()
        else:
            st.error("اكتبي: حذف الكل لتأكيد المسح.")

    st.markdown("---")

    st.subheader("حذف زبونة معينة")

    customers = sorted(df["customer_name"].dropna().unique().tolist())

    if customers:
        customer_to_delete = st.selectbox("اختاري الزبونة", customers)
        confirm_customer_delete = st.text_input("للتأكيد اكتبي اسم الزبونة كما هو")

        if st.button("حذف بيانات هذه الزبونة"):
            if confirm_customer_delete == customer_to_delete:
                df = df[df["customer_name"] != customer_to_delete]
                save_data(df)
                st.success(f"تم حذف بيانات {customer_to_delete}.")
                st.rerun()
            else:
                st.error("اسم التأكيد غير مطابق.")
    else:
        st.info("لا توجد زبائن لحذفهم.")

    st.markdown('</div>', unsafe_allow_html=True)