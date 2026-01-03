import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

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
# 2. PREMIUM UI: GLASSMORPHISM BLACK THEME
# ==========================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * {{ font-family: 'Kanit', sans-serif; }}
    .stApp {{ background-color: #050505; color: #E0E0E0; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #111, #000); border-right: 1px solid #333; }}
    .product-box {{
        background: rgba(28, 33, 40, 0.8);
        border: 1px solid #30363D;
        border-radius: 18px;
        padding: 15px;
        text-align: center;
        backdrop-filter: blur(10px);
    }}
    .price-tag {{ font-size: 24px; color: #D4AF37; font-weight: 600; margin: 10px 0; }}
    .stButton>button {{
        background: linear-gradient(90deg, #D4AF37, #F1D279);
        color: black !important; border-radius: 10px; font-weight: 600; width: 100%;
    }}
    .receipt-container {{
        background: #FFF; color: #000; padding: 30px; border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ROBUST DATA ENGINE
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
        except:
            return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# ==========================================
# 4. MAIN NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>PLATINUM POS</h1>", unsafe_allow_html=True)
    choice = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"], label_visibility="collapsed")
    if st.button("🔄 Sync Data"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. PAGE: POS SYSTEM
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
        if df_p.empty:
            st.warning("กำลังโหลดข้อมูลสินค้า...")
        else:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                current_stock = int(stock_map.get(p_name, 0))
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = current_stock - in_cart

                with grid[idx % 3]:
                    st.markdown(f"""
                    <div class="product-box">
                        <img src="{p_img if p_img else 'https://via.placeholder.com/200'}" style="width:100%; border-radius:12px; height:150px; object-fit:cover;">
                        <div style="margin-top:10px; font-weight:600;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div style="font-size:12px; color:#888;">คงเหลือ: {available}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"p_{idx}"):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("หมด", key=f"out_{idx}", disabled=True)

    with col_r:
        if st.session_state.last_receipt:
            res = st.session_state.last_receipt
            qr_url = f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png"
            st.markdown(f"""
            <div class="receipt-container">
                <center><h2>RECEIPT</h2><small>บิล: {res['bill_id']}</small></center>
                <hr>
                <table style="width:100%;">
                    {''.join([f'<tr><td>{k} x{v["qty"]}</td><td style="text-align:right;">{v["price"]*v["qty"]:,.0f}</td></tr>' for k,v in res['items'].items()])}
                </table>
                <hr>
                <div style="display:flex; justify-content:space-between; font-weight:bold;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
                <center><img src="{qr_url}" width="150"></center>
            </div>
            """, unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", type="primary"):
                st.session_state.last_receipt = None
                st.rerun()
        else:
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้า</h3>", unsafe_allow_html=True)
            total_val = 0
            for name, data in list(st.session_state.cart.items()):
                total_val += data['price'] * data['qty']
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{name}**\n{data['price']:,.0f} x {data['qty']}")
                    if c2.button("➕", key=f"add_{name}"):
                        st.session_state.cart[name]['qty'] += 1
                        st.rerun()
                    if c3.button("🗑️", key=f"del_{name}"):
                        del st.session_state.cart[name]
                        st.rerun()
            
            if total_val > 0:
                st.markdown(f"## {total_val:,.0f} ฿")
                pay_method = st.radio("ชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("🚀 ยืนยันการขาย", type="primary"):
                    bill_id = f"POS{int(time.time())}"
                    now = datetime.now()
                    
                    # ส่วนสำคัญ: ส่งข้อมูลให้ตรงกับ Google Apps Script
                    payload = {
                        "action": "checkout",
                        "date": now.strftime("%d/%m/%Y"), # Column A
                        "time": now.strftime("%H:%M:%S"), # Column B
                        "bill_id": bill_id,               # Column C
                        "total": float(total_val),        # Column D
                        "method": pay_method,             # Column E
                        "summary": ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()]) # Column F
                    }
                    
                    if POSDataEngine.post_to_gsheet(payload):
                        st.session_state.last_receipt = {"bill_id": bill_id, "items": dict(st.session_state.cart), "total": total_val}
                        st.session_state.cart = {}
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("บันทึกไม่สำเร็จ!")

# ==========================================
# 6. PAGE: ANALYTICS
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ยอดขาย</h2>", unsafe_allow_html=True)
    df_sales = POSDataEngine.fetch("sales")
    if not df_sales.empty:
        st.dataframe(df_sales, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลการขาย")

# ==========================================
# 7. PAGE: STOCK MANAGEMENT
# ==========================================
elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้า</h2>", unsafe_allow_html=True)
    df_stock = POSDataEngine.fetch("stock")
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.error("โหลดข้อมูลสต็อกไม่ได้")
