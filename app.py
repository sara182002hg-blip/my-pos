import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล (อัปเดต GID ตามลำดับชีตล่าสุด) ---
# สังเกตที่ gid ด้านท้ายลิงก์ครับ
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

# ลิงก์ Apps Script ของคุณ
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Ultra V.2", layout="wide")

# CSS จัดการรูปภาพและ UI ให้เป็นระเบียบ
st.markdown("""
    <style>
    .product-img {
        width: 100%;
        height: 180px;
        object-fit: contain;
        background: white;
        border-radius: 12px;
        border: 1px solid #f0f0f0;
    }
    .stMetric { background: #1e2130; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebarNav"] { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

def load_data_live(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        return pd.read_csv(StringIO(res.text)).dropna(how='all')
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# --- Sidebar เมนูระบบใหญ่ขึ้นเหมาะสมพอดี ---
st.sidebar.title("🏬 เมนูระบบ")
menu = st.sidebar.radio("", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"], label_visibility="collapsed")

if menu == "🛒 ขายสินค้า":
    df_p = load_data_live(URL_PRODUCTS)
    df_s = load_data_live(URL_STOCK)
    
    col_main, col_right = st.columns([2.5, 1.5])
    
    with col_main:
        # ระบบแยกหมวดหมู่สินค้า
        if not df_p.empty and 'Category' in df_p.columns:
            cats = ["ทั้งหมด"] + df_p['Category'].unique().tolist()
            selected_cat = st.selectbox("📂 เลือกหมวดหมู่", cats)
            if selected_cat != "ทั้งหมด":
                df_p = df_p[df_p['Category'] == selected_cat]

        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # ดึงสต็อกแบบ Real-time และป้องกัน Error ชื่อคอลัมน์
                s_match = df_s[df_s['Name'] == row['Name']] if 'Name' in df_s.columns else pd.DataFrame()
                stock = int(s_match.iloc[0]['Stock']) if not s_match.empty else 0
                cart_qty = st.session_state.cart.get(row['Name'], {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        # รูปภาพสินค้าขนาดเท่ากันเป๊ะ
                        img = row['Image_URL'] if 'Image_URL' in row and pd.notna(row['Image_URL']) else "https://via.placeholder.com/150"
                        st.markdown(f'<img src="{img}" class="product-img">', unsafe_allow_html=True)
                        st.markdown(f"**{row['Name']}**")
                        st.markdown(f"### {row['Price']:,} ฿")
                        
                        # สต็อกอัปเดตเรียลไทม์ (สีแดงถ้าเหลือน้อยกว่า 5)
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > cart_qty:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                                n = row['Name']
                                st.session_state.cart[n] = st.session_state.cart.get(n, {'price':row['Price'], 'qty':0})
                                st.session_state.cart[n]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ หมด", disabled=True, use_container_width=True)

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            qr_html = ""
            if r['method'] == "📱 PromptPay":
                qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
                qr_html = f'<div style="text-align: center; margin-top: 15px;"><img src="{qr_url}" width="220" style="border: 1px solid #ddd;"/></div>'

            st.markdown(f"""
            <div style="background:white; color:black; padding:25px; border-radius:10px; font-family:monospace; border:1px solid #ddd;">
                <h2 style="text-align:center; margin:0;">TAS POS</h2>
                <p style="text-align:center; font-size:10px;">ID: {r['id']}</p>
                <hr style="border-top: 1px dashed black;">
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n,i in r['items'].items()])}
                <hr style="border-top: 1px dashed black;">
                <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>รวมทั้งสิ้น</span><span>{r['total']:,} ฿</span></div>
                <p style="font-size:12px; margin-top:10px;">ชำระโดย: {r['method']}</p>
                {qr_html}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🖨️ สั่งพิมพ์ใบเสร็จ (Print)", use_container_width=True):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
                
            if st.button("🔄 เริ่มการขายใหม่", use_container_width=True, type="primary"):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า")
            else:
                for n, i in list(st.session_state.cart.items()):
                    total += i['price'] * i['qty']
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{n}** x{i['qty']}")
                    if c2.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]
                        st.rerun()
                st.divider()
                st.title(f"{total:,} ฿")
                method = st.radio("วิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยันยอดขาย", use_container_width=True, type="primary"):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    try:
                        requests.post(SCRIPT_URL, json={"action":"checkout", "bill_id":bill_id, "summary":summary, "total":total, "method":method}, timeout=5)
                        st.session_state.receipt = {"id":bill_id, "items":dict(st.session_state.cart), "total":total, "method":method}
                        st.session_state.cart = {}
                        st.rerun()
                    except: st.error("บันทึกไม่สำเร็จ ตรวจสอบเน็ตหรือ SCRIPT_URL")

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปยอดขาย")
    df_sales = load_data_live(URL_SALES)
    
    if not df_sales.empty:
        # ตรวจสอบชื่อคอลัมน์วันที่/เวลา ให้ตรงกับในชีต
        time_col = 'วันที่/เวลา' if 'วันที่/เวลา' in df_sales.columns else df_sales.columns[0]
        df_sales['วันที่'] = pd.to_datetime(df_sales[time_col]).dt.strftime("%d/%m/%Y")
        
        today = datetime.now().strftime("%d/%m/%Y")
        sales_today = df_sales[df_sales['วันที่'] == today]
        total_today = sales_today['ยอดรวม'].sum() if not sales_today.empty else 0
        
        c1, c2 = st.columns(2)
        c1.metric("ยอดขายวันนี้", f"{total_today:,} ฿")
        c2.metric("จำนวนบิลวันนี้", len(sales_today))
        
        # ปุ่มตัดยอดรายวัน
        if st.button("📅 กดบันทึกตัดยอดรายวัน (Daily Summary)", use_container_width=True, type="primary"):
            try:
                requests.post(SCRIPT_URL, json={"action":"save_summary", "date":today, "total":total_today, "bills":len(sales_today)})
                st.success("บันทึกตัดยอดลงชีต DailySummary แล้ว!")
            except: st.error("เกิดข้อผิดพลาดในการบันทึก")

        st.divider()
        # วิเคราะห์ยอดขายรายเดือน
        this_month = datetime.now().strftime("%m/%Y")
        df_sales['เดือน'] = pd.to_datetime(df_sales[time_col]).dt.strftime("%m/%Y")
        month_total = df_sales[df_sales['เดือน'] == this_month]['ยอดรวม'].sum()
        st.info(f"💰 ยอดขายรวมประจำเดือน {this_month}: **{month_total:,} ฿**")

        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลยอดขาย")

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อกสินค้าปัจจุบัน")
    df_stock = load_data_live(URL_STOCK)
    st.dataframe(df_stock, use_container_width=True)
