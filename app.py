import streamlit as st
import pandas as pd
import os
import re
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# إعدادات الصفحة لتكون بوضعية تدعم العربية
st.set_page_config(page_title="نظام فرز الطلبيات", layout="centered")

# إعداد ملف البيانات
if not os.path.exists('products.csv'):
    pd.DataFrame(columns=['sku', 'customer_name', 'status']).to_csv('products.csv', index=False)

st.title("📦 نظام فرز طلبات شي إن الذكي")
st.markdown("---")

# القائمة الجانبية
menu = ["📥 تسجيل سلة زبونة", "🔍 فرز البضاعة غداً", "📊 لوحة التحكم"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# --- الشاشة الأولى: تسجيل السلة ---
if choice == "📥 تسجيل سلة زبونة":
    st.subheader("📝 تفكيك السلة وحفظ البيانات")
    cust_name = st.text_input("👤 اسم الزبونة:")
    basket_data = st.text_area("📋 الصقي هنا تفاصيل الطلب من شي إن:", height=200)

    if st.button("🔥 حفظ القطع تلقائياً"):
        if cust_name and basket_data:
            skus = re.findall(r'(?:SKU|sku)?\s*:?\s*([A-Z0-9]{10,22})', basket_data)
            if not skus: skus = re.findall(r'\b[A-Z0-9]{8,22}\b', basket_data)

            if skus:
                skus = list(set(skus))
                df = pd.read_csv('products.csv')
                new_items = [{'sku': s, 'customer_name': cust_name, 'status': 'لم يتم فرزه'} for s in skus if
                             not s.isdigit() or len(s) > 8]
                if new_items:
                    df = pd.concat([df, pd.DataFrame(new_items)], ignore_index=True)
                    df.to_csv('products.csv', index=False)
                    st.success(f"✅ تم حفظ {len(new_items)} قطعة باسم ({cust_name})!")
                else:
                    st.warning("لم يتم العثور على رموز SKU صالحة.")
            else:
                st.error("❌ لم أجد أكواداً في النص!")
        else:
            st.error("يجب إدخال الاسم والنص!")

# --- الشاشة الثانية: الفرز السريع بالكاميرا واليدوي ---
elif choice == "🔍 فرز البضاعة غداً":
    st.subheader("🔍 شاشة الفرز السريع")

    # 1. تشغيل الكاميرا داخل المتصفح لالتقاط الباركود
    img_file_buffer = st.camera_input("📷 وجهي باركود الكيس نحو الكاميرا بوضوح")
    scanned_sku = ""

    if img_file_buffer is not None:
        # تحويل الصورة الملتقطة لصيغة مخصصة لفك الباركود
        bytes_data = img_file_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # قراءة الأسطر السوداء
        barcodes = decode(cv2_img)
        if barcodes:
            for barcode in barcodes:
                scanned_sku = barcode.data.decode('utf-8').strip()
                st.success(f"✅ تم قراءة الباركود بنجاح: {scanned_sku}")
        else:
            st.warning("⚠️ لم يتم رصد باركود واضح حتى الآن، قّربي الكيس أو حَسّني الإضاءة.")

    # 2. مستطيل الإدخال: يستقبل الكود تلقائياً من الكاميرا أو يمكنكِ الكتابة فيه يدوياً
    scan = st.text_input("امسحي الباركود أو اكتبي الـ SKU هنا:", value=scanned_sku)

    if scan:
        df = pd.read_csv('products.csv')
        res = df[df['sku'].astype(str).str.contains(scan, case=False, na=False)]
        if not res.empty:
            item = res.iloc[0]
            st.success(f"👤 الزبونة: {item['customer_name']}")
            st.info(f"📌 الـ SKU: {item['sku']}")
            if st.button("✅ تم الفرز (وضعها في الكيس)"):
                df.loc[df['sku'].astype(str) == item['sku'], 'status'] = "تم فرزه"
                df.to_csv('products.csv', index=False)
                st.rerun()
        else:
            st.error("❌ هذه القطعة غير مسجلة!")

# --- الشاشة الثالثة: التحكم ---
else:
    st.subheader("📊 ملخص الطلبيات")
    df = pd.read_csv('products.csv')
    st.metric("إجمالي القطع", len(df))
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 تحميل الملف للطباعة", data=csv, file_name='orders.csv', mime='text/csv')