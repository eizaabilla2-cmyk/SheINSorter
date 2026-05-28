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

else:
    st.subheader("📊 ملخص الطلبيات")
    df = pd.read_csv("products.csv")
    st.metric("إجمالي القطع", len(df))
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 تحميل الملف للطباعة", data=csv, file_name="orders.csv", mime="text/csv")