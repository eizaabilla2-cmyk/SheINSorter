import streamlit as st
import pandas as pd
import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract

st.set_page_config(page_title="نظام فرز الطلبيات", layout="centered")

if not os.path.exists("products.csv"):
    pd.DataFrame(columns=["sku", "customer_name", "status"]).to_csv("products.csv", index=False)


def extract_skus_from_text(text):
    if not text:
        return []

    cleaned = text.replace("：", ":")
    cleaned = cleaned.replace("\n", " ")

    # يلقط أكواد شي إن اللي تبدأ بحرف s وبعدها حروف اختيارية ثم أرقام
    # مثل: si..., sz..., sb..., swnight...
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


st.title("📦 نظام فرز طلبات شي إن الذكي")
st.markdown("---")

menu = ["📥 تسجيل سلة زبونة", "🔍 فرز البضاعة غداً", "📊 لوحة التحكم"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

if choice == "📥 تسجيل سلة زبونة":
    st.subheader("📝 تفكيك السلة وحفظ البيانات")

    cust_name = st.text_input("👤 اسم الزبونة:")
    basket_data = st.text_area("📋 الصقي هنا تفاصيل الطلب من شي إن:", height=200)

    if st.button("🔥 حفظ القطع تلقائياً"):
        if cust_name and basket_data:
            skus = extract_skus_from_text(basket_data)

            if skus:
                df = pd.read_csv("products.csv")

                new_items = []
                for sku in skus:
                    exists = df["sku"].astype(str).str.lower().eq(sku.lower()).any()

                    if not exists:
                        new_items.append({
                            "sku": sku,
                            "customer_name": cust_name,
                            "status": "لم يتم فرزه"
                        })

                if new_items:
                    df = pd.concat([df, pd.DataFrame(new_items)], ignore_index=True)
                    df.to_csv("products.csv", index=False)
                    st.success(f"✅ تم حفظ {len(new_items)} قطعة باسم ({cust_name})!")

                    with st.expander("عرض الأكواد التي تم حفظها"):
                        for item in new_items:
                            st.write(item["sku"])
                else:
                    st.warning("كل الأكواد موجودة مسبقاً.")
            else:
                st.error("❌ لم أجد أكواد SKU تبدأ بـ si أو sz.")
        else:
            st.error("يجب إدخال الاسم والنص!")

elif choice == "🔍 فرز البضاعة غداً":
    st.subheader("🔍 شاشة الفرز السريع")

    img_file_buffer = st.camera_input("📷 صوري الليبل بوضوح، خصوصاً السطر الذي يبدأ بـ si أو sz")

    scanned_sku = ""

    if img_file_buffer is not None:
        scanned_sku = extract_sku_from_image(img_file_buffer)

        if scanned_sku:
            st.success(f"✅ تم استخراج SKU بنجاح: {scanned_sku}")
        else:
            st.warning("⚠️ لم أستطع قراءة SKU. قرّبي الليبل وخليه واضح ومضاء.")

    scan = st.text_input("صوري الكود أو اكتبي الـ SKU هنا:", value=scanned_sku)

    if scan:
        df = pd.read_csv("products.csv")
        normalized_scan = scan.strip().lower()

        res = df[df["sku"].astype(str).str.lower().str.contains(normalized_scan, na=False)]

        if not res.empty:
            item = res.iloc[0]
            st.success(f"👤 الزبونة: {item['customer_name']}")
            st.info(f"📌 الـ SKU: {item['sku']}")
            st.write(f"الحالة: {item['status']}")
            if st.button("✅ تم الفرز"):
                df.loc[df["sku"].astype(str).str.lower() == str(item["sku"]).lower(), "status"] = "تم فرزه"
                df.to_csv("products.csv", index=False)
                st.rerun()
            else:
                st.error("❌ هذه القطعة غير مسجلة!")

            st.subheader("📊 ملخص الطلبيات")
            df = pd.read_csv("products.csv")
            st.metric("إجمالي القطع", len(df))
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 تحميل الملف للطباعة", data=csv, file_name="orders.csv", mime="text/csv")
        else:
            st.subheader("📊 ملخص الطلبيات")

            df = pd.read_csv("products.csv")

            st.metric("إجمالي القطع", len(df))

            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 تحميل الملف للطباعة",
                data=csv,
                file_name="orders.csv",
                mime="text/csv"
            )