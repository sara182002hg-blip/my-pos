import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏪 TAS POS SYSTEM (TEST MODE)")

# ลิงก์ตรงไปที่ชีต Stock ของคุณ (gid=228640428)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# ดึงข้อมูลแบบไม่มีการจำ (No Cache)
try:
    df = pd.read_csv(URL)
    st.success("✅ เชื่อมต่อข้อมูลสำเร็จ!")
    
    # แสดงข้อมูลเป็นตารางดิบๆ ให้ดูก่อน
    st.write("ตรวจสอบข้อมูลที่ดึงมาได้:")
    st.dataframe(df)
    
    # ถ้าดึงได้จริง จะสร้างปุ่มสินค้า
    st.divider()
    cols = st.columns(3)
    for i, row in df.iterrows():
        with cols[i % 3]:
            st.info(f"**{row['Name']}**\n\nราคา: {row['Price']} ฿\n\nสต็อก: {row['Stock']}")
            st.button(f"เลือก {row['Name']}", key=f"btn_{i}")

except Exception as e:
    st.error(f"❌ ยังดึงข้อมูลไม่ได้: {e}")
    st.info("กรุณาตรวจสอบว่าใน Google Sheets คุณได้กด 'Publish to web' และเลือกเป็น 'CSV' หรือยัง")
