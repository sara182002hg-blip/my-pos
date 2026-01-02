import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ลิงก์ข้อมูลที่แปลงเป็น CSV ให้แล้ว (GID ตรงตามชีตของคุณ) ---
# หน้า "เมนู" (สินค้า)
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
# หน้า "Sales" (ยอดขาย)
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
# หน้า "Stock" (สต็อก)
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# ลิงก์ Apps Script ของคุณ
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz36dYw2mJI2Nr4aqCLswtd4v4wq3AhleY_tFWfBRRSw2YwlyAzla55gclUVlHR2ulB/exec"

st.set_page_config(page_title="TAS POS", layout="wide")

# ✅ ฟังก์ชันโหลดข้อมูลและป้องกันหน้าจอแดง (TypeError)
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        # กรองเฉพาะแถวที่มีชื่อสินค้า (ป้องกัน Error จากแถวว่างด้านล่าง)
        return df.dropna(subset=['Name']).reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}

menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data(URL_PRODUCTS)
    col_main, col_cart = st.columns([3, 1.5])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ✅ แสดงผล 3 คอลัมน์ตามที่คุณต้องการ
            grid = st.columns(3) 
            for i, row in df_p.iterrows():
                with grid[i % 3]:
                    with st.container(border=True):
                        # ✅ แสดงรูปสูง 200px และดัก Error รูปภาพ
                        img = str(row.get('Image_URL', ""))
                        if img.startswith('http'):
                            st.image(img, height=200, use_container_width=True)
                        else:
                            st.info("🖼️ ไม่มีรูปภาพ")
                        
                        st.write(f"**{row['Name']}**")
                        st.write(f"ราคา: {row['Price']:,} ฿")
                        
                        if st.button("➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
        else:
            st.warning("⚠️ ไม่พบข้อมูลสินค้า โปรดตรวจสอบการ Publish CSV")

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
                    st.success("บันทึกสำเร็จ!")
                    st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อก":
    st.title("📦 สต็อกสินค้า")
    df_stock = load_data(URL_STOCK)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
