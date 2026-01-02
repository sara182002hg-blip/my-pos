import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS PLATINUM V21", layout="wide")

# ==========================================
# 2. V21 PLATINUM CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    
    /* Product Card V21 */
    .product-box { 
        background: #161b22; border: 1px solid #30363d; border-radius: 15px; 
        padding: 15px; text-align: center; margin-bottom: 20px;
    }
    .price-text { color: #d4af37; font-size: 24px; font-weight: bold; margin: 5px 0; }
    .stock-text { font-size: 12px; color: #8b949e; }
    
    /* Cart Bar Right Side */
    .cart-card { 
        background: #1c2128; border-radius: 12px; padding: 15px; 
        margin-bottom: 10px; border: 1px solid #30363d;
    }
    
    /* Premium Receipt */
    .receipt-container { 
        background: white; color: black; padding: 25px; border-radius: 10px; 
        font-family: 'Courier New', monospace; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .total-big { color: #d4af37; font-size: 40px; font-weight: bold; text-align: right; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE ENGINE
# ==========================================
@st.cache_data(ttl=2)
def load_data(key):
    try:
        r = requests.get(f"{CSV_URLS[key]}&nocache={time.time()}", timeout=10)
        r.encoding = 'utf-8-sig' 
        return pd.read_csv(StringIO(r.text)).dropna(how='all')
    except: return pd.DataFrame()

def call_gas(payload):
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=20)
        return res.status_code == 200
    except: return False

# Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='color:#d4af37; text-align:center;'>TAS PLATINUM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:12px; margin-top:-15px;'>POS SYSTEM ULTIMATE V21</p>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานยอดขาย", "📦 สต็อก & คลัง"])
    st.divider()
    if st.button("🔄 Sync Data (Force)", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ==========================================
# 4. หน้าขายสินค้า (🛒) - UI รูปแบบ V21
# ==========================================
if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data("products")
    df_s = load_data("stock")
    
    # ดึงสต็อก (Col0=Name, Col1=Qty)
    stock_dict = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict() if not df_s.empty else {}

    col_l, col_r = st.columns([2.3, 1.2])

    with col_l:
        st.markdown("### 📋 รายการเมนู")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                name = str(row.iloc[0]).strip()
                price = float(row.iloc[1])
                img = str(row.iloc[2])
                
                qty_in_cart = st.session_state.cart.get(name, {'q':0})['q']
                avail = int(stock_dict.get(name, 0)) - qty_in_cart

                with grid[i % 3]:
                    st.markdown(f'''<div class="product-box">
                        <img src="{img}" width="100%" style="height:150px; object-fit:cover; border-radius:10px;">
                        <div style="margin:10px 0; font-weight:600;">{name}</div>
                        <div class="price-text">{price:,.0f} ฿</div>
                        <div class="stock-text">คงเหลือในคลัง: {avail}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    if avail > 0:
                        if st.button(f"เลือก {name}", key=f"p_{i}", use_container_width=True):
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'p': price, 'q': 0})
                            st.session_state.cart[name]['q'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", disabled=True, key=f"ex_{i}", use_container_width=True)

    with col_r:
        # --- ส่วนแสดงใบเสร็จ (จะขึ้นมาหลังขาย) ---
        if st.session_state.receipt:
            rec = st.session_state.receipt
            st.markdown('<div class="receipt-container">', unsafe_allow_html=True)
            st.markdown(f"<center><b>TAS PLATINUM V21</b><br><small>{rec['id']}</small></center><hr>", unsafe_allow_html=True)
            for k, v in rec['items'].items():
                st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{k} x{v['q']}</span><span>{v['p']*v['q']:,.0f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<hr><div style='display:flex; justify-content:space-between; font-weight:bold;'><span>รวมสุทธิ</span><span>{rec['total']:,.0f} ฿</span></div>", unsafe_allow_html=True)
            
            if rec['method'] == "เงินสด":
                received = st.number_input("รับเงินมา", min_value=float(rec['total']), value=float(rec['total']), step=10.0)
                st.markdown(f"<h2 style='color:red; text-align:right; margin:0;'>ทอน: {received - rec['total']:,.0f} ฿</h2>", unsafe_allow_html=True)
            else:
                st.image(f"https://promptpay.io/{PROMPTPAY_ID}/{rec['total']}.png")
            
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", use_container_width=True):
                st.session_state.receipt = None; st.rerun()
        
        # --- ส่วนตะกร้าสินค้า (UI V21 เป๊ะๆ) ---
        else:
            st.markdown("### 🛒 ตะกร้าของฉัน")
            total = 0
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้า...")
            else:
                for k, v in list(st.session_state.cart.items()):
                    item_sum = v['p'] * v['q']
                    total += item_sum
                    with st.container():
                        c_info, c_plus, c_del = st.columns([2, 0.5, 0.5])
                        c_info.markdown(f"**{k}**<br><small>{v['p']} x {v['q']}</small>", unsafe_allow_html=True)
                        if c_plus.button("➕", key=f"add_qty_{k}"):
                            if int(stock_dict.get(k, 0)) > v['q']:
                                st.session_state.cart[k]['q'] += 1
                                st.rerun()
                        if c_del.button("🗑️", key=f"del_item_{k}"):
                            del st.session_state.cart[k]; st.rerun()
                
                st.markdown(f'<div class="total-big">{total:,.0f} ฿</div>', unsafe_allow_html=True)
                pay_m = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("🚀 ยืนยันการขาย", use_container_width=True, type="primary"):
                    now = datetime.now()
                    bid = f"POS{int(time.time())}"
                    payload = {
                        "action": "checkout",
                        "date": now.strftime("%d/%m/%Y"),
                        "time": now.strftime("%H:%M:%S"),
                        "bill_id": bid,
                        "total": float(total),
                        "method": pay_m,
                        "summary": ", ".join([f"{k}({v['q']})" for k,v in st.session_state.cart.items()])
                    }
                    if call_gas(payload):
                        st.session_state.receipt = {"id": bid, "total": total, "items": dict(st.session_state.cart), "method": pay_m}
                        st.session_state.cart = {}; st.cache_data.clear(); st.rerun()

# ==========================================
# 5. ANALYTICS (📊) - Fixed Datetime Bug
# ==========================================
elif menu == "📊 รายงานยอดขาย":
    st.markdown("### 📊 รายงานยอดขาย")
    df = load_data("sales")
    if not df.empty:
        try:
            # ตั้งชื่อคอลัมน์ให้ตรงกับรูป image_e0b88b.png
            df.columns = ['วันที่', 'เวลา', 'เลขบิล', 'ยอดเงิน', 'วิธีชำระเงิน', 'รายการสินค้า']
            df['ยอดเงิน'] = pd.to_numeric(df['ยอดเงิน'], errors='coerce').fillna(0)
            
            # บังคับให้เป็น Datetime ป้องกัน Red Error
            df['วันที่'] = pd.to_datetime(df['วันที่'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['วันที่'])

            today = datetime.now().date()
            val_today = df[df['วันที่'].dt.date == today]['ยอดเงิน'].sum()
            bill_today = len(df[df['วันที่'].dt.date == today])

            c1, c2 = st.columns(2)
            c1.metric("ยอดรวมวันนี้", f"{val_today:,.0f} ฿")
            c2.metric("จำนวนบิล", f"{bill_today} บิล")
            
            st.divider()
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        except Exception as e:
            st.error(f"ระบบตรวจพบปัญหาข้อมูล: {e}")
    else: st.warning("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อก & คลัง":
    st.markdown("### 📦 สถานะคลังสินค้า")
    st.dataframe(load_data("stock"), use_container_width=True)
