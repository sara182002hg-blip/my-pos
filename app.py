import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# ✅ ลิงก์ Apps Script ล่าสุดของคุณ
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Ultra", layout="wide")

# ปรับปรุง UI และขนาดรูปภาพให้เท่ากัน
st.markdown("""
    <style>
    .product-img {
        width: 100%;
        height: 180px;
        object-fit: contain;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    [data-testid="stSidebarNav"] { font-size: 20px !important; }
    .stMetric { background: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ฟังก์ชันโหลดข้อมูล Real-time
def load_data_live(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        return pd.read_csv(StringIO(res.text)).dropna(how='all')
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# --- Sidebar เมนูระบบขนาดใหญ่ ---
st.sidebar.title("🏬 เมนูระบบ")
menu = st.sidebar.radio("", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 สต็อกสินค้า"], label_visibility="collapsed")

if menu == "🛒 ขายสินค้า":
    df_p = load_data_live(URL_PRODUCTS)
    df_s = load_data_live(URL_STOCK)
    
    col_main, col_right = st.columns([2.5, 1.5])
    
    with col_main:
        # ระบบหมวดหมู่สินค้า
        if not df_p.empty and 'Category' in df_p.columns:
            cats = ["ทั้งหมด"] + df_p['Category'].unique().tolist()
            selected_cat = st.selectbox("📂 หมวดหมู่สินค้า", cats)
            if selected_cat != "ทั้งหมด":
                df_p = df_p[df_p['Category'] == selected_cat]

        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # ดึงสต็อกแบบ Real-time
                s_match = df_s[df_s['Name'] == row['Name']]
                stock = int(s_match.iloc[0]['Stock']) if not s_match.empty else 0
                cart_qty = st.session_state.cart.get(row['Name'], {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        # แสดงรูปภาพขนาดเท่ากัน
                        img = row['Image_URL'] if 'Image_URL' in row and pd.notna(row['Image_URL']) else "https://via.placeholder.com/150"
                        st.markdown(f'<img src="{img}" class="product-img">', unsafe_allow_html=True)
                        st.markdown(f"**{row['Name']}**")
                        st.markdown(f"### {row['Price']:,} ฿")
                        
                        # แจ้งเตือนสต็อกสีแดง
                        st.markdown(f"คงเหลือ: <span style='color:{'red' if stock <= 5 else '#00ff00'}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > cart_qty:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"btn_{i}", use_container_width=True):
                                n = row['Name']
                                st.session_state.cart[n] = st.session_state.cart.get(n, {'price':row['Price'], 'qty':0})
                                st.session_state.cart[n]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ สินค้าหมด", disabled=True, use_container_width=True)

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            qr_html = ""
            if r['method'] == "📱 PromptPay":
                qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
                qr_html = f'<div style="text-align: center; margin-top: 15px;"><img src="{qr_url}" width="220" style="border: 1px solid #ddd;"/></div>'

            st.markdown(f"""
            <div id="receipt-area" style="background:white; color:black; padding:25px; border-radius:10px; font-family:monospace; border:1px solid #eee;">
                <h2 style="text-align:center; margin:0;">TAS POS</h2>
                <p style="text-align:center; font-size:10px;">ID: {r['id']}</p>
                <hr style="border-top: 1px dashed black;">
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n,i in r['items'].items()])}
                <hr style="border-top: 1px dashed black;">
                <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>รวมทั้งสิ้น</span><span>{r['total']:,} ฿</span></div>
                <p style="font-size:12px; margin-top:10px;">Payment: {r['method']}</p>
                {qr_html}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🖨️ สั่งพิมพ์ใบเสร็จ", use_container_width=True):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
                
            if st.button("🔄 เริ่มการขายใหม่", use_container_width=True, type="primary"):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                for n, i in list(st.session_state.cart.items()):
                    sub = i['price'] * i['qty']
                    total += sub
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{n}** x{i['qty']}")
                    if c2.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]
                        st.rerun()
                
                st.divider()
                st.title(f"{total:,} ฿")
                method = st.radio("ช่องทางชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยันการขาย", use_container_width=True, type="primary"):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    try:
                        requests.post(SCRIPT_URL, json={"action":"checkout", "bill_id":bill_id, "summary":summary, "total":total, "method":method}, timeout=5)
                        st.session_state.receipt = {"id":bill_id, "items":dict(st.session_state.cart), "total":total, "method":method}
                        st.session_state.cart = {}
                        st.rerun()
                    except: st.error("การเชื่อมต่อล้มเหลว")

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปรายงานการขาย")
    df_sales = load_data_live(URL_SALES)
    
    if not df_sales.empty:
        # เตรียมข้อมูลวันที่
        today = datetime.now().strftime("%d/%m/%Y")
        df_sales['วันที่'] = pd.to_datetime(df_sales['วัน/เวลา']).dt.strftime("%d/%m/%Y")
        sales_today = df_sales[df_sales['วันที่'] == today]
        
        # ส่วนแสดงผลสรุปบน Dashboard
        c1, c2, c3 = st.columns(3)
        current_total = sales_today['ยอดรวม'].sum() if not sales_today.empty else 0
        c1.metric("ยอดขายวันนี้", f"{current_total:,} ฿")
        c2.metric("จำนวนบิลวันนี้", len(sales_today))
        
        if st.button("📅 ตัดยอดและบันทึกสรุปรายวัน", use_container_width=True, type="primary"):
            res = requests.post(SCRIPT_URL, json={"action":"save_summary", "date":today, "total":current_total, "bills":len(sales_today)})
            if res.status_code == 200: st.success("บันทึกตัดยอดลงชีต DailySummary เรียบร้อย!")
        
        st.divider()
        
        # ยอดขายย้อนหลัง 7 วัน
        st.subheader("📅 ยอดขายย้อนหลัง 7 วัน")
        last_7_days = [(datetime.now() - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(7)]
        weekly_stats = df_sales[df_sales['วันที่'].isin(last_7_days)].groupby('วันที่')['ยอดรวม'].sum()
        st.bar_chart(weekly_stats)
        
        # สรุปยอดรายเดือน
        this_month = datetime.now().strftime("%m/%Y")
        df_sales['เดือน'] = pd.to_datetime(df_sales['วัน/เวลา']).dt.strftime("%m/%Y")
        month_total = df_sales[df_sales['เดือน'] == this_month]['ยอดรวม'].sum()
        st.info(f"💰 ยอดขายรวมประจำเดือนนี้ ({this_month}): **{month_total:,} ฿**")

        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.warning("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 เช็คสต็อกสินค้า")
    df_stock = load_data_live(URL_STOCK)
    st.dataframe(df_stock, use_container_width=True)
