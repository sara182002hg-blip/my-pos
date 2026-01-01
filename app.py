import streamlit as st
import pandas as pd

# ลิงก์ตรงไปที่ชีต Stock ของคุณ
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwu (รหัสยาวๆ ของคุณ) /pub?gid=228640428&single=true&output=csv"

st.set_page_config(layout="wide")
st.title("🏪 TAS POS SYSTEM")

# ฟังก์ชันดึงข้อมูลแบบเรียบง่าย
@st.cache_data(ttl=1)
def get_data():
    try:
        # ใช้ลิงก์ที่คุณส่งมา (gid=228640428)
        sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
        df = pd.read_csv(sheet_url)
        return df
    except:
        return pd.DataFrame()

df = get_data()

if df.empty:
    st.error("❌ เชื่อมต่อ Google Sheets ไม่สำเร็จ กรุณาเช็คการแชร์ไฟล์")
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        # แสดงรายการสินค้าแบบตารางเพื่อให้เห็นว่าข้อมูลมาจริงไหม
        st.write("### รายการสินค้าในสต็อก")
        st.dataframe(df, use_container_width=True)
        
        # แสดงแบบปุ่ม
        st.divider()
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                st.info(f"**{row['Name']}**\n\n{row['Price']} ฿\n\nคงเหลือ: {row['Stock']}")
                st.button(f"เพิ่ม {row['Name']}", key=i)
    
    with col2:
        st.write("🛒 ตะกร้าสินค้า")
        st.info("ระบบพร้อมใช้งาน")

if st.button("🔄 บังคับอัปเดตข้อมูล"):
    st.cache_data.clear()
    st.rerun()
