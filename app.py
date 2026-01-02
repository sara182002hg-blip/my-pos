import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO

# --- ลิงก์ที่แปลงเป็น CSV เรียบร้อยแล้วจาก Google Sheets ของคุณ ---
# 1. หน้า เมนู (GID: 1258507712)
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
# 2. หน้า Sales (GID: 952949333)
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
# 3. หน้า Stock (GID: 228640428)
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# ลิงก์ Apps Script ล่าสุดของคุณ
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz36dYw2mJI2Nr4aqCLswtd4v4wq3AhleY_tFWfBRRSw2YwlyAzla55gclUVlHR2ulB/exec"

st.set_page_config(page_title="TAS POS", layout="wide")

# ✅ ฟังก์ชันโหลดข้อมูลที่เสถียรที่สุด
def load_data(url):
    try:
        # บังคับรีเฟรชข้อมูลด้วย timestamp
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        # กรองแถวว่างเพื่อป้องกัน TypeError
        return df.dropna(subset=['Name']).reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}

menu = st.sidebar.radio("ระบบจัดการ", ["🛒 ขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data(URL_PRODUCTS)
    col_main, col_cart = st.columns([3, 1.5])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ✅ จัดเรียง 3 คอลัมน์ตามคำขอ
            grid = st.columns(3) 
            for i, row in df_p.iterrows():
                with grid[i % 3]:
                    with st.container(border=True):
                        # ✅ แสดงรูปภาพสูง 200px
                        img = str(row.get('Image_URL', ""))
                        if img.startswith('http'):
                            st.image(img, height=200, use_container_width=True)
                        else:
                            st.write("🖼️ (ไม่มีรูปภาพ)")
                        
                        st.write(f"**{row['Name']}**")
                        st.write(f"฿ {row['Price']:,}")
                        
                        if st.button("➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
        else:
            st.warning("⚠️ ข้อมูลในชีตยังไม่มา โปรดรอ 1-2 นาทีหลังการกด Publish")

    with col_cart:
        st.subheader("🛒 ตะกร้า")
        total_sum = 0
        for name, item in list(st.session_state.cart.items()):
            total_sum += item['price'] * item['qty']
            st.write(f"{name} x{item['qty']} ({item['price']*item['qty']:,}฿)")
        
        if st.session_state.cart:
            st.divider()
            st.header(f"รวม: {total_sum:,} ฿")
            if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": "เงินสด"}
                
                if requests.post(SCRIPT_URL, json=payload).status_code == 200:
                    st.session_state.cart = {}
                    st.success("บันทึกยอดขายสำเร็จ!")
                    st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อก":
    st.title("📦 สต็อกสินค้าคงเหลือ")
    df_stock = load_data(URL_STOCK)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
