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
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv",
    "summary": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
}
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM UI: STYLING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #050505; color: #E0E0E0; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #111, #000); border-right: 1px solid #333; }
    .product-box {
        background: rgba(28, 33, 40, 0.8); border: 1px solid #30363D; border-radius: 18px;
        padding: 15px; text-align: center; backdrop-filter: blur(10px);
    }
    .img-container img { width: 100%; height: 160px; object-fit: cover; border-radius: 12px; }
    .price-tag { font-size: 24px; color: #D4AF37; font-weight: 600; margin: 10px 0; }
    .receipt-container {
        background: #FFF; color: #000; padding: 25px; border-radius: 10px;
        font-family: 'Courier New', monospace; line-height: 1.2;
    }
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
            response = requests.get(f"{url}&nocache={time.time()}", timeout=15)
            response.encoding = 'utf-8-sig' # ป้องกันภาษาต่างดาว
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                df.columns = df.columns.str.strip()
                return df.dropna(how='all')
        except Exception as e:
            st.error(f"Data Fetch Error ({key}): {e}")
        return pd.DataFrame()

    @staticmethod
    def post_to_gsheet(payload):
        try:
            res = requests.post(SCRIPT_URL, json=payload, timeout=20)
            return res.status_code == 200
        except: return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>PLATINUM POS</h1>", unsafe_allow_html=True)
    choice = st.radio("MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"], label_visibility="collapsed")
    st.divider()
    if st.button("🔄 Sync Data (Force)", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ==========================================
# 5. POS SYSTEM
# ==========================================
if choice == "🛒 หน้าขายสินค้า":
    df_p = POSDataEngine.fetch("products")
    df_s = POSDataEngine.fetch("stock")
    
    # Mapping สต็อก (Col0=ชื่อ, Col1=จำนวน)
    stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict() if not df_s.empty else {}

    col_l, col_r = st.columns([2.3, 1.4])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                
                # เช็คสต็อกจริงหักลบในตะกร้า
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = int(stock_map.get(p_name, 0)) - in_cart

                with grid[idx % 3]:
                    st.markdown(f'''<div class="product-box">
                        <div class="img-container"><img src="{p_img if p_img else 'https://via.placeholder.com/200'}"></div>
                        <div style="margin-top:10px; font-weight:600;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div class="stock-label">คงเหลือ: {available}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"p_{idx}"):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else: st.button("สินค้าหมด", key=f"out_{idx}", disabled=True)

    with col_r:
        if st.session_state.last_receipt:
            # --- VIEW: ใบเสร็จ ---
            res = st.session_state.last_receipt
            st.markdown('<div class="receipt-container">', unsafe_allow_html=True)
            st.markdown(f"<center><h2 style='margin:0;'>TAS PREMIUM SHOP</h2><small>ID: {res['bill_id']}</small><hr></center>", unsafe_allow_html=True)
            for k, v in res['items'].items():
                st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{k} x{v['qty']}</span><span>{v['price']*v['qty']:,.0f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<hr><div style='display:flex; justify-content:space-between; font-weight:bold; font-size:18px;'><span>ยอดรวมสุทธิ</span><span>{res['total']:,.0f} ฿</span></div>", unsafe_allow_html=True)
            
            if res['method'] == "เงินสด":
                st.markdown(f"<small>รับเงินสด: {res['cash']:,.2f}<br>เงินทอน: {res['change']:,.2f}</small>", unsafe_allow_html=True)
            else:
                st.image(f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png", width=200)
            st.markdown(f"<hr><center><small>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small></center></div>", unsafe_allow_html=True)
            
            if st.button("➕ เปิดบิลใหม่", type="primary", use_container_width=True):
                st.session_state.last_receipt = None; st.rerun()
        else:
            # --- VIEW: ตะกร้าสินค้า ---
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้าสินค้า</h3>", unsafe_allow_html=True)
            total_val = 0
            if not st.session_state.cart: st.info("ตะกร้าว่างเปล่า...")
            else:
                for name, data in list(st.session_state.cart.items()):
                    total_val += data['price'] * data['qty']
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2.5, 1, 1])
                        c1.markdown(f"**{name}**\n\n{data['price'] * data['qty']:,.0f} ฿")
                        if c2.button("➕", key=f"plus_{name}"):
                            # ป้องกันบวกเกินสต็อก
                            if int(stock_map.get(name, 0)) > st.session_state.cart[name]['qty']:
                                st.session_state.cart[name]['qty'] += 1; st.rerun()
                        if c3.button("🗑️", key=f"rem_{name}"):
                            del st.session_state.cart[name]; st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total_val:,.0f} ฿</h1>", unsafe_allow_html=True)
                pay_method = st.radio("การชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                cash_received = 0.0
                if pay_method == "เงินสด":
                    cash_received = st.number_input("เงินที่รับมา", min_value=float(total_val), step=100.0)
                    st.markdown(f"**เงินทอน: {cash_received - float(total_val):,.2f} ฿**")
                
                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    bill_id = f"POS{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    
                    if POSDataEngine.post_to_gsheet({
                        "action": "checkout", "bill_id": bill_id, "summary": summary,
                        "total": float(total_val), "method": pay_method
                    }):
                        st.session_state.last_receipt = {
                            "bill_id": bill_id, "items": dict(st.session_state.cart),
                            "total": total_val, "method": pay_method, "cash": cash_received,
                            "change": cash_received - float(total_val)
                        }
                        st.session_state.cart = {}; st.cache_data.clear(); st.rerun()
                    else: st.error("❌ บันทึกล้มเหลว!")

# ==========================================
# 6. ANALYTICS (Fixed Column Bug)
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ยอดขาย</h2>", unsafe_allow_html=True)
    df_sales = POSDataEngine.fetch("sales")
    
    if not df_sales.empty:
        try:
            # แปลงวันที่
            df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
            df_sales.iloc[:, 2] = pd.to_numeric(df_sales.iloc[:, 2], errors='coerce').fillna(0) # ยอดเงิน
            
            now = datetime.now()
            today_sales = df_sales[df_sales.iloc[:, 0].dt.date == now.date()].iloc[:, 2].sum()
            bill_count = len(df_sales[df_sales.iloc[:, 0].dt.date == now.date()])

            c1, c2 = st.columns(2)
            c1.metric("ยอดขายวันนี้", f"{today_sales:,.2f} ฿")
            c2.metric("จำนวนบิล", f"{bill_count} บิล")
            
            st.divider()
            st.dataframe(df_sales.sort_index(ascending=False), use_container_width=True)
        except Exception as e: st.warning(f"Error in Report: {e}")
    else: st.info("ยังไม่มีข้อมูลการขาย")

elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้า</h2>", unsafe_allow_html=True)
    st.dataframe(POSDataEngine.fetch("stock"), use_container_width=True)
