import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

# อัปเดตลิงก์ Apps Script ล่าสุดของพี่แล้ว
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM CSS (คงเดิมเป๊ะ)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #050505; color: #E0E0E0; }
    .product-box { background: rgba(28, 33, 40, 0.8); border: 1px solid #30363D; border-radius: 18px; padding: 15px; text-align: center; }
    .price-tag { font-size: 24px; color: #D4AF37; font-weight: 600; margin: 10px 0; }
    .receipt-container { background: #FFF; color: #000; padding: 25px; border-radius: 10px; font-family: 'Courier New', monospace; }
    .stButton>button { background: linear-gradient(90deg, #D4AF37, #F1D279); color: black !important; font-weight: 600; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATA ENGINE
# ==========================================
class POSDataEngine:
    @staticmethod
    def fetch(key):
        try:
            url = CSV_URLS[key]
            res = requests.get(f"{url}&nocache={time.time()}", timeout=10)
            if res.status_code == 200:
                res.encoding = 'utf-8'
                df = pd.read_csv(StringIO(res.text))
                return df.dropna(how='all')
        except: pass
        return pd.DataFrame()

    @staticmethod
    def post_sale(payload):
        try:
            res = requests.post(SCRIPT_URL, json=payload, timeout=10)
            return res.status_code == 200
        except: return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>PLATINUM POS</h1>", unsafe_allow_html=True)
    st.divider()
    choice = st.radio("เมนูหลัก", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"])
    st.divider()
    if st.button("🔄 Sync Data"): st.rerun()

# ==========================================
# 5. PAGE: POS SYSTEM (Real-time Stock)
# ==========================================
if choice == "🛒 หน้าขายสินค้า":
    df_p = POSDataEngine.fetch("products")
    df_s = POSDataEngine.fetch("stock")
    
    stock_map = {}
    if not df_s.empty:
        stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_l, col_r = st.columns([2.3, 1.4])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else "https://via.placeholder.com/200"
                
                current_stock = int(stock_map.get(p_name, 0))
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = current_stock - in_cart

                with grid[idx % 3]:
                    st.markdown(f"""<div class="product-box"><img src="{p_img}" width="100%" style="height:150px; object-fit:cover; border-radius:10px;">
                                <div style="margin:10px 0; font-weight:600;">{p_name}</div>
                                <div class="price-tag">{p_price:,.0f} ฿</div>
                                <div style="color:#888; font-size:12px; margin-bottom:10px;">ในคลัง: {available}</div></div>""", unsafe_allow_html=True)
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"sel_{idx}"):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else: st.button("สินค้าหมด", disabled=True, key=f"sold_{idx}")

    with col_r:
        if st.session_state.last_receipt:
            res = st.session_state.last_receipt
            qr_url = f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png"
            st.markdown(f"""<div class="receipt-container"><center><h3>TAS PREMIUM SHOP</h3><small>{res['bill_id']}</small></center><hr>
            {''.join([f'<div style="display:flex; justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
            <hr><div style="display:flex; justify-content:space-between; font-weight:bold; font-size:18px;"><span>รวมทั้งหมด</span><span>{res['total']:,.0f} ฿</span></div>
            {f'<center><img src="{qr_url}" width="150" style="margin-top:10px;"></center>' if res['method'] == "พร้อมเพย์" else ""}</div>""", unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", use_container_width=True):
                st.session_state.last_receipt = None; st.rerun()
        else:
            st.markdown("### 🛒 ตะกร้าของฉัน")
            total_val = 0
            if not st.session_state.cart: st.info("ตะกร้าว่างเปล่า")
            else:
                for k, v in list(st.session_state.cart.items()):
                    sub = v['price'] * v['qty']
                    total_val += sub
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{k}** x {v['qty']}")
                    if c2.button("🗑️", key=f"del_{k}"): del st.session_state.cart[k]; st.rerun()
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total_val:,.0f} ฿</h1>", unsafe_allow_html=True)
                method = st.radio("ชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    now = datetime.now()
                    bill_id = f"POS{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    payload = {"action": "checkout", "date": now.strftime("%d/%m/%Y"), "time": now.strftime("%H:%M:%S"), 
                               "bill_id": bill_id, "total": float(total_val), "method": method, "summary": summary}
                    if POSDataEngine.post_sale(payload):
                        st.session_state.last_receipt = {"bill_id": bill_id, "items": dict(st.session_state.cart), "total": total_val, "method": method}
                        st.session_state.cart = {}; st.cache_data.clear(); st.rerun()

# ==========================================
# 6. PAGE: ANALYTICS (ฉบับแยกวันที่และเวลา)
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ผลประกอบการ</h2>", unsafe_allow_html=True)
    df_sales = POSDataEngine.fetch("sales")
    
    if df_sales is not None and not df_sales.empty:
        try:
            # คอลัมน์: A=วันที่(0), B=เวลา(1), D=ยอดเงิน(3)
            df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
            df_sales.iloc[:, 3] = pd.to_numeric(df_sales.iloc[:, 3].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            now = datetime.now()
            today_total = df_sales[df_sales.iloc[:, 0].dt.date == now.date()].iloc[:, 3].sum()
            month_total = df_sales[df_sales.iloc[:, 0].dt.month == now.month].iloc[:, 3].sum()

            m1, m2 = st.columns(2)
            m1.metric("ยอดขายวันนี้", f"{today_total:,.2f} ฿")
            m2.metric("ยอดรวมเดือนนี้", f"{month_total:,.2f} ฿")
            
            st.divider()
            st.markdown("### 📜 ประวัติรายการล่าสุด")
            st.dataframe(df_sales.sort_values(by=df_sales.columns[0], ascending=False), use_container_width=True)
        except Exception as e:
            st.error(f"ระบบคำนวณขัดข้อง: {e}")
    else: st.info("ยังไม่มีข้อมูลการขาย")

# ==========================================
# 7. PAGE: STOCK
# ==========================================
elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้าปัจจุบัน</h2>", unsafe_allow_html=True)
    st.dataframe(POSDataEngine.fetch("stock"), use_container_width=True)
