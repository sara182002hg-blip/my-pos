import streamlit as st
import pandas as pd
import requests
import time
import json
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. CORE SYSTEM CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv",
    "summary": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
}
# อัปเดตลิงก์ Apps Script ล่าสุดของพี่แล้ว
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzO9AocZxITbOVURUpuaYXkkwLwgMLRWYUb_LSiY3SxjbPYz36MWkg1Ean000MVcWi6/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM UI: GLASSMORPHISM BLACK THEME (คงเดิมเป๊ะ)
# ==========================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * {{ font-family: 'Kanit', sans-serif; }}
    .stApp {{ background-color: #050505; color: #E0E0E0; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #111, #000); border-right: 1px solid #333; }}
    .product-box {{
        background: rgba(28, 33, 40, 0.8);
        border: 1px solid #30363D; border-radius: 18px; padding: 15px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-align: center; backdrop-filter: blur(10px);
    }}
    .product-box:hover {{ border-color: #D4AF37; transform: scale(1.03); box-shadow: 0 10px 20px rgba(212, 175, 55, 0.2); }}
    .img-container img {{ width: 100%; height: 180px; object-fit: cover; border-radius: 12px; }}
    .price-tag {{ font-size: 24px; color: #D4AF37; font-weight: 600; margin: 10px 0; }}
    .stock-label {{ font-size: 12px; color: #888; }}
    .stButton>button {{
        background: linear-gradient(90deg, #D4AF37, #F1D279);
        color: black !important; border: none; border-radius: 10px;
        font-weight: 600; transition: 0.3s; width: 100%; height: 45px;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(212,175,55,0.4); }}
    div[data-testid="metric-container"] {{ background: #161B22; border: 1px solid #30363D; border-radius: 15px; padding: 20px; }}
    [data-testid="stMetricValue"] {{ color: #D4AF37 !important; font-size: 32px !important; }}
    .receipt-container {{ background: #FFF; color: #000; padding: 30px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ROBUST DATA ENGINE (FIXED FETCHING)
# ==========================================
class POSDataEngine:
    @staticmethod
    def fetch(key):
        try:
            url = CSV_URLS[key]
            response = requests.get(f"{url}&nocache={time.time()}", timeout=15)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                df.columns = df.columns.str.strip() # ล้างชื่อคอลัมน์
                return df.dropna(how='all')
        except Exception as e:
            st.error(f"Data Fetch Error ({key}): {e}")
        return pd.DataFrame()

    @staticmethod
    def post_to_gsheet(payload):
        try:
            res = requests.post(SCRIPT_URL, json=payload, timeout=20)
            return res.status_code == 200
        except:
            return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# ==========================================
# 4. MAIN NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>PLATINUM POS</h1>", unsafe_allow_html=True)
    st.divider()
    choice = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"], label_visibility="collapsed")
    st.divider()
    if st.button("🔄 Sync Data (Force)"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. PAGE: POS SYSTEM (เชื่อมข้อมูลสต็อกแบบเรียลไทม์)
# ==========================================
if choice == "🛒 หน้าขายสินค้า":
    df_p = POSDataEngine.fetch("products")
    # ดึงข้อมูลจากชีต Stock โดยตรงเพื่อให้มั่นใจว่า "เรียลไทม์" ที่สุดก่อนขาย
    df_s = POSDataEngine.fetch("stock")
    
    stock_map = {}
    if not df_s.empty:
        # ใช้ Column Index 0 (ชื่อสินค้า) และ Index 1 (จำนวนคงเหลือ)
        stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_l, col_r = st.columns([2.3, 1.4])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if df_p.empty:
            st.warning("กำลังโหลดข้อมูลสินค้า...")
        else:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                
                # ดึงค่าสต็อกที่เพิ่งโหลดมา (ทำให้หน้าขายกับหน้าสต็อกตรงกันเป๊ะ)
                current_stock = int(stock_map.get(p_name, 0))
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = current_stock - in_cart

                with grid[idx % 3]:
                    st.markdown(f"""
                    <div class="product-box">
                        <div class="img-container"><img src="{p_img if p_img else 'https://via.placeholder.com/200'}"></div>
                        <div style="margin-top:10px; font-weight:600; height:30px;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div class="stock-label">คงเหลือในคลัง: {available} ชิ้น</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"p_{idx}"):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"out_{idx}", disabled=True)

    with col_r:
        if st.session_state.last_receipt:
            res = st.session_state.last_receipt
            qr_url = f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png"
            receipt_html = f"""<div id="receipt-box" class="receipt-container"><center><h2 style="margin:0;">TAS PREMIUM SHOP</h2><small>เลขที่บิล: {res['bill_id']}</small><hr style="border-top:1px dashed #000;"></center><table style="width:100%; border-collapse: collapse;">{''.join([f'<tr><td style="padding:5px 0;">{k} x{v["qty"]}</td><td style="text-align:right;">{v["price"]*v["qty"]:,.0f}</td></tr>' for k,v in res['items'].items()])}</table><hr style="border-top:1px dashed #000;"><div style="display:flex; justify-content:space-between; font-size:20px; font-weight:bold;"><span>ยอดรวมสุทธิ</span><span>{res['total']:,.0f} ฿</span></div><div style="margin-top:10px; font-size:14px;">ชำระโดย: {res['method']}<br>{f"รับเงินสด: {res['cash']:,.2f} ฿<br>เงินทอน: {res['change']:,.2f} ฿" if res['method'] == "เงินสด" else ""}</div>{f'<center><div style="margin:15px 0;"><img src="{qr_url}" width="180"></div></center>' if res['method'] == "พร้อมเพย์" else ""}<hr style="border-top:1px dashed #000;"><center><small>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small></center></div>"""
            st.markdown(receipt_html, unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", type="primary", use_container_width=True):
                st.session_state.last_receipt = None
                st.rerun()
        else:
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้าของฉัน</h3>", unsafe_allow_html=True)
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า...")
            else:
                total_val = 0
                for name, data in list(st.session_state.cart.items()):
                    subtotal = data['price'] * data['qty']
                    total_val += subtotal
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{name}**\n\n{data['price']:,.0f} x {data['qty']}")
                        if c2.button("➕", key=f"plus_{name}"):
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                        if c3.button("🗑️", key=f"rem_{name}"):
                            del st.session_state.cart[name]
                            st.rerun()
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total_val:,.0f} ฿</h1>", unsafe_allow_html=True)
                pay_method = st.radio("วิธีการชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                cash_received = 0.0
                if pay_method == "เงินสด":
                    cash_received = st.number_input("ยอดเงินที่รับ", min_value=float(total_val), step=20.0)
                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    bill_id = f"POS{int(time.time())}"
                    summary_text = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    if POSDataEngine.post_to_gsheet({"action": "checkout", "bill_id": bill_id, "summary": summary_text, "total": float(total_val), "method": pay_method}):
                        st.session_state.last_receipt = {"bill_id": bill_id, "items": dict(st.session_state.cart), "total": total_val, "method": pay_method, "cash": cash_received, "change": cash_received - float(total_val)}
                        st.session_state.cart = {}; st.cache_data.clear(); st.rerun()

# ==========================================
# 6. PAGE: ANALYTICS (ฉบับแก้ไขด่วน - เจาะจงเฉพาะหน้านี้)
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ผลประกอบการ</h2>", unsafe_allow_html=True)
    df_sales = POSDataEngine.fetch("sales")
    
    if df_sales is None or df_sales.empty:
        st.info("📢 ยังไม่มีข้อมูลการขายบันทึกในระบบ")
    else:
        try:
            # 1. กำหนดตำแหน่งคอลัมน์ (Index) แทนการใช้ชื่อ
            # ช่องที่ 0 = วันที่เวลา (A), ช่องที่ 2 = ยอดเงิน (C)
            col_date = 0 
            col_amount = 2 

            # 2. แปลงข้อมูลวันที่ให้ Python อ่านออก
            df_sales.iloc[:, col_date] = pd.to_datetime(df_sales.iloc[:, col_date], dayfirst=True, errors='coerce')
            
            # 3. เตรียมตัวแปรคำนวณ
            now = datetime.now()
            today_date = now.date()
            
            # คำนวณยอดขายวันนี้
            today_total = df_sales[df_sales.iloc[:, col_date].dt.date == today_date].iloc[:, col_amount].sum()
            
            # คำนวณยอดขาย 7 วันล่าสุด
            last_7_days = now - timedelta(days=7)
            week_total = df_sales[df_sales.iloc[:, col_date] >= last_7_days].iloc[:, col_amount].sum()
            
            # คำนวณยอดขายเดือนนี้
            month_total = df_sales[df_sales.iloc[:, col_date].dt.month == now.month].iloc[:, col_amount].sum()

            # 4. แสดงผล Metric (สีทองสวยงามแบบเดิม)
            m1, m2, m3 = st.columns(3)
            m1.metric("ยอดขายวันนี้", f"{today_total:,.2f} ฿")
            m2.metric("ยอดรวม 7 วัน", f"{week_total:,.2f} ฿")
            m3.metric("ยอดรวมเดือนนี้", f"{month_total:,.2f} ฿")
            
            st.divider()
            
            # 5. แสดงตารางรายการขายทั้งหมด
            st.markdown("### 📜 ประวัติการขายล่าสุด")
            # จัดเรียงจากใหม่ไปเก่า
            df_display = df_sales.sort_values(by=df_sales.columns[col_date], ascending=False)
            st.dataframe(df_display, use_container_width=True)
            
        except Exception as e:
            # ถ้ายังไม่ได้อีก จะโชว์ Error บอกเราว่าผิดที่ตรงไหน
            st.error(f"⚠️ การดึงข้อมูลผิดพลาด: {e}")
            st.info("ตรวจสอบว่าใน Google Sheets (หน้า Sales) คอลัมน์ C คือยอดเงินใช่หรือไม่?")
            
# ==========================================
# 7. PAGE: STOCK MANAGEMENT (คงเดิม)
# ==========================================
elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้าออนไลน์</h2>", unsafe_allow_html=True)
    df_stock = POSDataEngine.fetch("stock")
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True, height=500)


