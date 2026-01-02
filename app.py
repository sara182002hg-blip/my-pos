import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- ลิงก์ข้อมูลจาก Google Sheets ของคุณ ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"

st.set_page_config(page_title="TAS POS", layout="wide")

def load_data(url):
    try:
        # บังคับรีเฟรชข้อมูล
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        df = pd.read_csv(StringIO(res.text))
        # ✅ ขั้นตอนสำคัญ: ลบแถวที่ไม่มีชื่อสินค้าทิ้ง เพื่อป้องกัน TypeError
        df = df.dropna(subset=['Name']).reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()

menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า", "📊 ยอดขาย"])

if menu == "🛒 ขายสินค้า":
    st.subheader("📦 รายการสินค้า")
    df_p = load_data(URL_PRODUCTS)
    
    if not df_p.empty:
        # ✅ แสดงผล 3 คอลัมน์
        grid = st.columns(3)
        for i, row in df_p.iterrows():
            with grid[i % 3]:
                with st.container(border=True):
                    # ✅ ป้องกันแอปเด้ง: ตรวจสอบลิงก์รูปภาพก่อนแสดงผล
                    img_url = str(row.get('Image_URL', ""))
                    try:
                        if img_url.startswith("http"):
                            st.image(img_url, height=200, use_container_width=True)
                        else:
                            st.info("ไม่มีรูปภาพ")
                    except:
                        st.error("ลิงก์รูปมีปัญหา")
                    
                    st.write(f"**{row['Name']}**")
                    st.write(f"ราคา: {row['Price']:,} ฿")
                    st.button("เพิ่มลงตะกร้า", key=f"add_{i}")
    else:
        st.warning("⚠️ ไม่พบข้อมูลสินค้าในชีต 'เมนู'")

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        st.dataframe(df_sales, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")
