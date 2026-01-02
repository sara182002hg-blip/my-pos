import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. CORE SYSTEM CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM UI: V21 GLASSMORPHISM BLACK THEME
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
    .receipt-container {{ background: #FFF; color: #000; padding: 30px; border-radius: 10px; font-family: 'Courier New', monospace; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATA ENGINE
# ==========================================
class DataEngine:
    @staticmethod
    def fetch(key):
        try:
            url = CSV_URLS[key]
            res = requests.get(f"{url}&nocache={time.time()}", timeout=10)
            if res.status_code == 200:
                res.encoding = 'utf-8'
                return pd.read_csv(StringIO(res.text)).dropna(how='all')
        except: pass
        return pd.DataFrame()

    @staticmethod
    def post_to_gsheet(payload):
        try:
            return requests.post(SCRIPT_URL, json=payload, timeout=10).status_code == 200
        except: return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# ==========================================
# 4. MAIN NAVIGATION (V21 Style)
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>TAS PLATINUM</h1>", unsafe_allow_html=True)
    st.divider()
    choice = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"])
    st.divider()
    if st.button("🔄 Sync Data (Force)"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. PAGE: POS SYSTEM (V21 UI + REALTIME STOCK)
# ==========================================
if choice == "🛒 หน้าขายสินค้า":
    df_p = DataEngine.fetch("products")
    df_s = DataEngine.fetch("stock")
    
    stock_map = {}
    if not df_s.empty:
        # ดึงสต็อกจริงมาเตรียมไว้ (ช่องที่ 2 ของหน้า Stock)
        stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_l, col_r = st.columns([2.3, 1.4])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                
                # คำนวณสต็อกคงเหลือจริง
                current_stock = int(stock_map.get(p_name, 0))
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = current_stock - in_cart

                with grid[idx % 3]:
                    st.markdown(f"""
                    <div class="product-box">
                        <div class="img-container"><img src="{p_img if p_img else 'https://via.placeholder.com/200'}"></div>
                        <div style="margin-top:10px; font-weight:600; height:30px;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div class="stock-label">คงเหลือในคลัง: {available}</div>
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
            receipt_html = f"""<div class="receipt-container"><center><h2>TAS PREMIUM</h2><small>{res['bill_id']}</small><hr></center>
            {''.join([f'<div style="display:flex; justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
            <hr><div style="display:flex; justify-content:space-between; font-size:20px; font-weight:bold;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
            <center><img src="{qr_url}" width="180" style="margin-top:15px;"></center></div>"""
            st.markdown(receipt_html, unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", use_container_width=True):
                st.session_state.last_receipt = None; st.rerun()
        else:
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้าของฉัน</h3>", unsafe_allow_html=True)
            total_val = 0
            if not st.session_state.cart: st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                for name, data in list(st.session_state.cart.items()):
                    subtotal = data['price'] * data['qty']
                    total_val += subtotal
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{name}**\n\n{data['price']:,.0f} x {data['qty']}")
                        if c2.button("➕", key=f"plus_{name}"): st.session_state.cart[name]['qty'] += 1; st.rerun()
                        if c3.button("🗑️", key=f"rem_{name}"): del st.session_state.cart[name]; st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total_val:,.0f} ฿</h1>", unsafe_allow_html=True)
                pay_method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    now = datetime.now()
                    bill_id = f"POS{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    payload = {
                        "action": "checkout", "date": now.strftime("%d/%m/%Y"), "time": now.strftime("%H:%M:%S"),
                        "bill_id": bill_id, "total": float(total_val), "method": pay_method, "summary": summary
                    }
                    if DataEngine.post_to_gsheet(payload):
                        st.session_state.last_receipt = {"bill_id": bill_id, "items": dict(st.session_state.cart), "total": total_val}
                        st.session_state.cart = {}; st.rerun()

# ==========================================
# 6. PAGE: ANALYTICS (FIXED COLUMN D FOR TOTAL)
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 รายงานยอดขาย</h2>", unsafe_allow_html=True)
    df = DataEngine.fetch("sales")
    if not df.empty:
        try:
            # คอลัมน์ A(0)=วันที่, D(3)=ยอดเงิน
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], dayfirst=True, errors='coerce')
            df.iloc[:, 3] = pd.to_numeric(df.iloc[:, 3].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            today = datetime.now().date()
            val_today = df[df.iloc[:, 0].dt.date == today].iloc[:, 3].sum()
            val_month = df[df.iloc[:, 0].dt.month == datetime.now().month].iloc[:, 3].sum()

            m1, m2 = st.columns(2)
            m1.metric("ยอดขายวันนี้", f"{val_today:,.2f} ฿")
            m2.metric("ยอดขายเดือนนี้", f"{val_month:,.2f} ฿")
            st.divider()
            st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")
    else: st.info("ยังไม่มีข้อมูลการขาย")

# ==========================================
# 7. PAGE: STOCK
# ==========================================
elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 รายการสินค้าในคลัง</h2>", unsafe_allow_html=True)
    st.dataframe(DataEngine.fetch("stock"), use_container_width=True)
