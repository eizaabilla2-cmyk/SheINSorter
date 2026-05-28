import streamlit as st
import pandas as pd
import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract

st.set_page_config(page_title="نظام فرز الطلبيات", layout="centered")

DATA_FILE = "products.csv"
COLUMNS = ["sku", "customer_name", "status"]


def load_data():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)

    df = pd.read_csv(DATA_FILE)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[COLUMNS]


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def empty_data():
    return pd.DataFrame(columns=COLUMNS)


def extract_skus_from_text(text):
    if not text:
        return []

    cleaned = text.replace("：", ":")
    cleaned = cleaned.replace("\n", " ")

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
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #070707 0%, #101114 100%);
            color: #F7F1E3;
            direction: rtl;
        }

        [data-testid="stHeader"] {
            background: rgba(7, 7, 7, 0);
        }

        [data-testid="stSidebar"] {
            background: #0B0C10;
            border-left: 1px solid rgba(212, 175, 55, 0.25);
        }

        h1, h2, h3 {
            color: #F7F1E3 !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }

        .main-title {
            background: linear-gradient(135deg, #D4AF37, #FFF1A8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 42px;
            font-weight: 900;
            line-height: 1.25;
            margin-bottom: 8px;
        }

        .subtitle {
            color: #B8B8B8;
            font-size: 15px;
            margin-bottom: 25px;
        }

        .gold-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(212, 175, 55, 0.28);
            border-radius: 22px;
            padding: 20px;
            margin: 14px 0;
            box-shadow: 0 8px 30px rgba(0,0,0,0.25);
        }

        .success-card {
            background: rgba(31, 122, 68, 0.16);
            border: 1px solid rgba(70, 220, 120, 0.3);
            border-radius: 18px;
            padding: 16px;
        }

        .warn-card {
            background: rgba(212, 175, 55, 0.13);
            border: 1px solid rgba(212, 175, 55, 0.35);
            border-radius: 18px;
            padding: 16px;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #D4AF37, #9C7A18);
            color: #111 !important;
            border: none;
            border-radius: 14px;
            font-weight: 800;
            padding: 0.65rem 1rem;
            width: 100%;
        }

        div.stButton > button:hover {
            border: 1px solid #FFF1A8;
            filter: brightness(1.08);
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] {
            background: #15171C !important;
            color: #F7F1E3 !important;
            border-radius: 14px !important;
        }

        .stDataFrame {
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 18px;
            overflow: hidden;
        }

        [data-testid="stMetricValue"] {
            color: #D4AF37;
        }

        hr {
            border-color: rgba(212, 175, 55, 0.25);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


apply_theme()

st.markdown('<div class="main-title">📦 نظام فرز طلبات شي إن الذكي</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">فرز أسرع، أخطاء أقل، وتتبع أوضح لكل زبونة.</div>', unsafe_allow_html=True)
st.markdown("---")

menu = [
    "📥 تسجيل سلة زبونة",
    "🔍 فرز البضاعة",
    "📊 لوحة التحكم",
    "🧹 إدارة البيانات"
]

choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

df = load_data()

if choice == "📥 تسجيل سلة زبونة":
    st.subheader("📝 تفكيك السلة وحفظ البيانات")

    with st.container():
        st.markdown('<div class="gold-card">', unsafe_allow_html=True)

        cust_name = st.text_input("👤 اسم الزبونة:")
        basket_data = st.text_area("📋 الصقي هنا كل أكواد أو تفاصيل الطلب:", height=220)

        found_skus = extract_skus_from_text(basket_data)

        if basket_data:
            st.info(f"تم رصد {len(found_skus)} كود محتمل داخل النص.")

        if st.button("🔥 حفظ القطع تلقائياً"):
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
                                "status": "لم يتم فرزه"
                            })
                        else:
                            repeated.append(sku)

                    if new_items:
                        df = pd.concat([df, pd.DataFrame(new_items)], ignore_index=True)
                        save_data(df)

                        st.success(f"✅ تم حفظ {len(new_items)} قطعة باسم ({cust_name})!")

                        with st.expander("عرض الأكواد التي تم حفظها"):
                            for item in new_items:
                                st.write(item["sku"])

                    if repeated:
                        st.warning(f"⚠️ تم تجاهل {len(repeated)} كود مكرر.")

                        with st.expander("عرض الأكواد المكررة"):
                            for sku in repeated:
                                st.write(sku)

                    if not new_items and repeated:
                        st.warning("كل الأكواد موجودة مسبقاً.")
                else:
                    st.error("❌ لم أجد أكواد صالحة. تأكدي أن الأكواد تبدأ بحرف S وتحتوي أرقام.")
            else:
                st.error("يجب إدخال اسم الزبونة والنص.")

        st.markdown('</div>', unsafe_allow_html=True)


elif choice == "🔍 فرز البضاعة":
    st.subheader("🔍 شاشة الفرز السريع")

    img_file_buffer = st.camera_input("📷 صوري الليبل بوضوح، خصوصاً السطر الذي يبدأ بحرف S")

    scanned_sku = ""

    if img_file_buffer is not None:
        scanned_sku = extract_sku_from_image(img_file_buffer)

        if scanned_sku:
            st.success(f"✅ تم استخراج SKU بنجاح: {scanned_sku}")
        else:
            st.warning("⚠️ لم أستطع قراءة SKU. قرّبي الليبل وخليه واضح ومضاء.")

    scan = st.text_input("صوري الكود أو اكتبي الـ SKU هنا:", value=scanned_sku)

    if scan:
        normalized_scan = scan.strip().lower()

        res = df[df["sku"].astype(str).str.lower().str.contains(normalized_scan, na=False)]

        if not res.empty:
            item = res.iloc[0]

            st.markdown('<div class="success-card">', unsafe_allow_html=True)
            st.success(f"👤 الزبونة: {item['customer_name']}")
            st.info(f"📌 الـ SKU: {item['sku']}")
            st.write(f"الحالة: {item['status']}")
            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ تم الفرز"):
                    df.loc[df["sku"].astype(str).str.lower() == str(item["sku"]).lower(), "status"] = "تم فرزه"
                    save_data(df)
                    st.rerun()

            with col2:
                if st.button("↩️ تراجع عن الفرز"):
                    df.loc[df["sku"].astype(str).str.lower() == str(item["sku"]).lower(), "status"] = "لم يتم فرزه"
                    save_data(df)
                    st.rerun()

        else:
            st.error("❌ هذه القطعة غير مسجلة!")


elif choice == "📊 لوحة التحكم":
    st.subheader("📊 ملخص الطلبيات")

    total = len(df)
    sorted_count = len(df[df["status"] == "تم فرزه"])
    unsorted_count = len(df[df["status"] != "تم فرزه"])

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي القطع", total)
    col2.metric("تم فرزها", sorted_count)
    col3.metric("المتبقي", unsorted_count)

    st.markdown("---")

    customers = sorted(df["customer_name"].dropna().unique().tolist())

    selected_customer = st.selectbox(
        "فلترة حسب الزبونة:",
        ["الكل"] + customers
    )

    filtered_df = df.copy()

    if selected_customer != "الكل":
        filtered_df = filtered_df[filtered_df["customer_name"] == selected_customer]

        c_total = len(filtered_df)
        c_sorted = len(filtered_df[filtered_df["status"] == "تم فرزه"])
        st.info(f"📦 {selected_customer}: تم فرز {c_sorted} من {c_total}")

        if c_total > 0:
            st.progress(c_sorted / c_total)

    status_filter = st.selectbox(
        "فلترة حسب الحالة:",
        ["الكل", "لم يتم فرزه", "تم فرزه"]
    )

    if status_filter != "الكل":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]

    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 تحميل البيانات المعروضة",
        data=csv,
        file_name="orders_filtered.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.subheader("📌 عداد كل زبونة")

    if not df.empty:
        summary = df.groupby("customer_name").agg(
            total=("sku", "count"),
            sorted_items=("status", lambda x: (x == "تم فرزه").sum())
        ).reset_index()

        summary["remaining"] = summary["total"] - summary["sorted_items"]
        summary["progress"] = summary["sorted_items"].astype(str) + " / " + summary["total"].astype(str)

        st.dataframe(summary, use_container_width=True)
    else:
        st.info("لا توجد بيانات بعد.")


else:
    st.subheader("🧹 إدارة البيانات")

    st.warning("قبل أي حذف، حمّلي نسخة احتياطية.")

    backup_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 تحميل Backup كامل",
        data=backup_csv,
        file_name="orders_backup.csv",
        mime="text/csv"
    )

    st.markdown("---")

    st.subheader("🗑️ مسح كل البيانات")

    confirm_delete_all = st.text_input("للمسح الكامل اكتبي: حذف الكل")

    if st.button("🗑️ مسح كل الطلبيات"):
        if confirm_delete_all == "حذف الكل":
            save_data(empty_data())
            st.success("✅ تم مسح كل الطلبيات.")
            st.rerun()
        else:
            st.error("اكتبي: حذف الكل لتأكيد المسح.")

    st.markdown("---")

    st.subheader("🧍 حذف زبونة معينة")

    customers = sorted(df["customer_name"].dropna().unique().tolist())

    if customers:
        customer_to_delete = st.selectbox("اختاري الزبونة:", customers)
        confirm_customer_delete = st.text_input("للتأكيد اكتبي اسم الزبونة كما هو:")

        if st.button("حذف بيانات هذه الزبونة"):
            if confirm_customer_delete == customer_to_delete:
                df = df[df["customer_name"] != customer_to_delete]
                save_data(df)
                st.success(f"✅ تم حذف بيانات {customer_to_delete}.")
                st.rerun()
            else:
                st.error("اسم التأكيد غير مطابق.")
    else:
        st.info("لا توجد زبائن لحذفهم.")