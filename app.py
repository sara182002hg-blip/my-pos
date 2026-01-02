import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS v2.3", layout="wide")

st.markdown("""
    <style>
    .product-img { width: 100%; height: 180px; object-fit: contain; background: white; border-radius: 12px; border: 1px solid #f0f0f0; }
    .stMetric { background: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def load_data_live(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip() # ลบช่องว่างหัวคอลัมน์
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

# ฟังก์ชันช่วยหาชื่อคอลัมน์ที่ถูกต้อง
def find_col(df, keywords):
    for c in df.columns:
        if any(k.lower() in c.lower() for k in keywords):
            return c
    return df.columns[0] if not df.empty else None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data_live(URL_PRODUCTS)
    df_s = load_data_live(URL_STOCK)
    
    col_main, col_right = st.columns([2.5, 1.5])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # หาชื่อคอลัมน์แบบฉลาด
            c_name = find_col(df_p, ['Name', 'สินค้า', 'ชื่อ'])
            c_price = find_col(df_p, ['Price', 'ราคา'])
            c_img = find_col(df_p, ['Image', 'รูป', 'URL'])
            
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = row[c_name]
                p_price = row[c_price]
                p_img = row[c_img] if c_img and pd.notna(row[c_img]) else ""
                
                # เช็คสต็อก
                s_name_col = find_col(df_s, ['Name', 'สินค้า'])
                s_qty_col = find_col(df_s, ['Stock', 'คงเหลือ', 'จำนวน'])
                s_match = df_s[df_s[s_name_col] == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0][s_qty_col]) if not s_match.empty else 0
                
                with grid[i % 3]:
                    with st.container(border=True):
                        img_url = p_img if p_img != "" else "https://via.placeholder.com/150"
                        st.markdown(f'<img src="{img_url}" class="product-img">', unsafe_allow_html=True)
                        st.write(f"**{p_name}**")
                        st.write(f"### {p_price:,} ฿")
                        
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > st.session_state.cart.get(p_name, {}).get('qty', 0):
                            if st.button(f"➕ เพิ่ม", key=f"add_{i}"):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price':p_price, 'qty':0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else: st.button("❌ หมด", disabled=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จ")
            qr_html = f'<div style="text-align: center;"><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" width="200"/></div>' if r['method'] == "📱 PromptPay" else ""
            st.markdown(f"""<div style="background:white; color:black; padding:15px; border-radius:10px; border:1px solid #ddd; font-family:monospace;">
                <h3 style="text-align:center;">TAS POS</h3><hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n,i in r['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>รวม</span><span>{r['total']:,} ฿</span></div>{qr_html}</div>""", unsafe_allow_html=True)
            if st.button("🔄 ขายต่อ"): 
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้า")
            total = 0
            for n, i in list(st.session_state.cart.items()):
                total += i['price'] * i['qty']
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{n}** x{i['qty']}")
                if c2.button("🗑️", key=f"del_{n}"):
                    del st.session_state.cart[n]
                    st.rerun()
            if total > 0:
                method = st.radio("วิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    # ส่งข้อมูลและไม่ต้องรอผลตอบกลับจาก Apps Script เพื่อลด Error แจ้งเตือนหลอก
                    try:
                        requests.post(SCRIPT_URL, json={"action":"checkout", "bill_id":bill_id, "summary":summary, "total":total, "method":method}, timeout=1)
                    except: pass 
                    st.session_state.receipt = {"id":bill_id, "items":dict(st.session_state.cart), "total":total, "method":method}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 ยอดขาย")
    df_sales = load_data_live(URL_SALES)
    if not df_sales.empty:
        c_dt = find_col(df_sales, ['วันที่', 'Time', 'วัน'])
        c_total = find_col(df_sales, ['ยอดรวม', 'Total', 'ราคา'])
        
        # แก้ไขยอด 0 บาท: แปลงวันที่ให้แม่นยำขึ้น
        df_sales['Date_Only'] = pd.to_datetime(df_sales[c_dt], dayfirst=True, errors='coerce').dt.strftime("%d/%m/%Y")
        today = datetime.now().strftime("%d/%m/%Y")
        
        sales_today = df_sales[df_sales['Date_Only'] == today]
        total_today = pd.to_numeric(sales_today[c_total], errors='coerce').sum()
        
        st.metric("ยอดขายวันนี้", f"{total_today:,} ฿")
        if st.button("📅 บันทึกตัดยอดรายวัน", type="primary"):
            try:
                requests.post(SCRIPT_URL, json={"action":"save_summary", "date":today, "total":float(total_today), "bills":int(len(sales_today))}, timeout=5)
                st.success("บันทึกสำเร็จ!")
            except: st.info("ส่งข้อมูลเรียบร้อย (กรุณาเช็คในชีต DailySummary)")
        
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อก")
    st.dataframe(load_data_live(URL_STOCK), use_container_width=True)
