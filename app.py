import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# ==========================================
# 1. SETUP & CONFIGURATION (ตรวจสอบ GID ให้ตรง)
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

# Web App URL จาก Google Apps Script
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM CSS STYLING (V21 PLATINUM)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #050505; color: #E0E0E0; }
    
    /* Product Card Customization */
    .product-box { 
        background: linear-gradient(145deg, #1c2128, #111418);
        border: 1px solid #30363D; border-radius: 15px; padding: 15px; 
        text-align: center; transition: 0.3s;
    }
    .product-box:hover { border-color: #D4AF37; transform: translateY(-5px); }
    .price-tag { font-size: 24px; color: #D4AF37; font-weight: 600; margin: 5px 0; }
    
    /* Cart & Receipt Styles */
    .cart-container { background: #161B22; border-radius: 12px; padding: 20px; border: 1px solid #30363D; }
    .receipt-container { 
        background: #FFFFFF; color: #000000; padding: 30px; 
        border-radius: 10px; font-family: 'Courier New', monospace;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    /* Button Customization */
    .stButton>button { border-radius: 8px; font-weight: 400; transition: 0.2s; }
    .stButton>button:hover { background-color: #D4AF37; color: black; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE DATA ENGINE (High Performance)
# ==========================================
class TAS_Engine:
    @staticmethod
    @st.cache_data(ttl=2) # หน่วงน้อยลง ตัดสต็อกเรียลไทม์มากขึ้น
    def fetch_data(key):
        try:
            res = requests.get(f"{CSV_URLS[key]}&nocache={time.time()}", timeout=10)
            res.encoding = 'utf-8'
            df = pd.read_csv(StringIO(res.text))
            return df.dropna(how='all')
        except:
            return pd.DataFrame()

    @staticmethod
    def send_transaction(payload):
        try:
            r = requests.post(SCRIPT_URL, json=payload, timeout=20)
            return r.status_code == 200
        except:
            return False

# Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt_data' not in st.session_state: st.session_state.receipt_data = None

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>TAS PLATINUM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:12px;'>POS SYSTEM ULTIMATE V21</p>", st.markdown("---", unsafe_allow_html=True))
    menu = st.radio("เมนูหลัก", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"])
    
    st.markdown("---")
    if st.button("🔄 Sync Data (Force)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. POS INTERFACE
# ==========================================
if menu == "🛒 หน้าขายสินค้า":
    df_p = TAS_Engine.fetch_data("products")
    df_s = TAS_Engine.fetch_data("stock")
    
    # Map Stock เรียลไทม์ (A=Name, B=Qty)
    stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict() if not df_s.empty else {}

    col_menu, col_cart = st.columns([2.1, 1.4])

    with col_menu:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2])
                
                # Check Real-time Stock
                in_cart_qty = st.session_state.cart.get(p_name, {}).get('q', 0)
                available = int(stock_map.get(p_name, 0)) - in_cart_qty

                with grid[i % 3]:
                    st.markdown(f'''
                    <div class="product-box">
                        <img src="{p_img}" width="100%" style="height:150px; object-fit:cover; border-radius:10px;">
                        <div style="margin-top:10px; font-weight:600;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div style="font-size:12px; color:#888;">คงเหลือในคลัง: {available}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"btn_{i}", use_container_width=True):
                            if p_name not in st.session_state.cart:
                                st.session_state.cart[p_name] = {'p': p_price, 'q': 1}
                            else:
                                st.session_state.cart[p_name]['q'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", disabled=True, key=f"off_{i}", use_container_width=True)

    with col_cart:
        if st.session_state.receipt_data:
            # --- จอแสดงใบเสร็จหลังชำระเงิน ---
            res = st.session_state.receipt_data
            st.markdown('<div class="receipt-container">', unsafe_allow_html=True)
            st.markdown(f"<center><h2 style='margin:0;'>TAS SHOP</h2><small>ID: {res['id']}</small></center><hr>", unsafe_allow_html=True)
            for k, v in res['items'].items():
                st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{k} x{v['q']}</span><span>{v['p']*v['q']:,.0f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<hr><div style='display:flex; justify-content:space-between; font-weight:bold; font-size:20px;'><span>ยอดสุทธิ</span><span>{res['total']:,.0f} ฿</span></div>", unsafe_allow_html=True)
            
            if res['method'] == "เงินสด":
                cash_received = st.number_input("เงินสดที่รับมา", min_value=float(res['total']), step=10.0, key="cash_input")
                st.markdown(f"<h2 style='color:black; text-align:right; margin-top:10px;'>เงินทอน: {cash_received - res['total']:,.0f} ฿</h2>", unsafe_allow_html=True)
            else:
                st.image(f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png", caption="สแกนเพื่อชำระเงิน")
            
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("✅ เสร็จสิ้น / บิลถัดไป", use_container_width=True, type="primary"):
                st.session_state.receipt_data = None
                st.rerun()
        else:
            # --- หน้าตะกร้าสินค้า ---
            st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
            st.markdown("### 🛒 ตะกร้าสินค้า")
            grand_total = 0
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า...")
            else:
                for k, v in list(st.session_state.cart.items()):
                    sub = v['p'] * v['q']
                    grand_total += sub
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{k}** x{v['q']} ({sub:,.0f} ฿)")
                    if c2.button("🗑️", key=f"del_{k}"):
                        del st.session_state.cart[k]
                        st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{grand_total:,.0f} ฿</h1>", unsafe_allow_html=True)
                method = st.radio("วิธีการชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("🚀 ยืนยันการขายและตัดสต็อก", use_container_width=True, type="primary"):
                    now = datetime.now()
                    bill_id = f"TX{int(time.time())}"
                    # ข้อมูลส่งไป Google Sheets (ตามที่พี่แยกคอลัมน์แล้ว)
                    payload = {
                        "action": "checkout",
                        "date": now.strftime("%d/%m/%Y"),
                        "time": now.strftime("%H:%M:%S"),
                        "bill_id": bill_id,
                        "total": float(grand_total),
                        "method": method,
                        "summary": ", ".join([f"{k}({v['q']})" for k,v in st.session_state.cart.items()])
                    }
                    if TAS_Engine.send_transaction(payload):
                        st.session_state.receipt_data = {"id": bill_id, "items": dict(st.session_state.cart), "total": grand_total, "method": method}
                        st.session_state.cart = {}
                        st.cache_data.clear()
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. ANALYTICS (FIXED DATETIME RED ERROR)
# ==========================================
elif menu == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ยอดขาย</h2>", unsafe_allow_html=True)
    df = TAS_Engine.fetch_data("sales")
    
    if not df.empty:
        try:
            # แปลงวันที่ให้ปลอดภัย (รองรับทั้งแยกคอลัมน์และรวมคอลัมน์)
            df.columns = ['วันที่', 'เวลา', 'เลขบิล', 'ยอดเงิน', 'วิธีชำระ', 'รายการ']
            df['วันที่'] = pd.to_datetime(df['วันที่'], dayfirst=True, errors='coerce')
            df['ยอดเงิน'] = pd.to_numeric(df['ยอดเงิน'], errors='coerce').fillna(0)
            
            # กรองข้อมูลที่ผิดพลาดออก
            df = df.dropna(subset=['วันที่'])
            
            today = datetime.now().date()
            val_today = df[df['วันที่'].dt.date == today]['ยอดเงิน'].sum()
            count_today = len(df[df['วันที่'].dt.date == today])

            m1, m2 = st.columns(2)
            m1.metric("ยอดรวมวันนี้", f"{val_today:,.2f} ฿")
            m2.metric("จำนวนบิลวันนี้", f"{count_today} บิล")
            
            st.divider()
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            
        except Exception as e:
            st.error(f"ระบบตรวจพบปัญหาข้อมูล: {e}")
            st.info("แนะนำ: กดปุ่ม Sync Data (Force) เพื่อดึงข้อมูลใหม่อีกครั้ง")
    else:
        st.info("ยังไม่มีข้อมูลการขายในฐานข้อมูล")

elif menu == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 ตรวจสอบคลังสินค้า</h2>", unsafe_allow_html=True)
    df_s = TAS_Engine.fetch_data("stock")
    if not df_s.empty:
        st.dataframe(df_s, use_container_width=True, height=500)
    else:
        st.warning("ไม่สามารถดึงข้อมูลสต็อกได้")
