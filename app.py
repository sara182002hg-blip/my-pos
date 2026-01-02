import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS V21", layout="wide")

# ==========================================
# 2. V21 PLATINUM STYLING (สีทอง-ดำ)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    
    /* Product Card */
    .product-card { 
        background: #161b22; border: 1px solid #30363d; border-radius: 15px; 
        padding: 15px; text-align: center; transition: 0.3s;
    }
    .product-card:hover { border-color: #d4af37; transform: translateY(-5px); }
    .price-tag { color: #d4af37; font-size: 22px; font-weight: bold; }
    
    /* Cart Styling */
    .cart-item { 
        background: #1c2128; border-radius: 10px; padding: 12px; 
        margin-bottom: 10px; border-left: 4px solid #d4af37;
    }
    
    /* Receipt Styling */
    .receipt-box { 
        background: white; color: black; padding: 30px; border-radius: 12px; 
        font-family: 'Courier New', monospace; box-shadow: 0 8px 20px rgba(0,0,0,0.5);
    }
    
    /* Buttons */
    .stButton>button { border-radius: 8px; transition: 0.2s; }
    .stButton>button:hover { border-color: #d4af37; color: #d4af37; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE FUNCTIONS (Fixed Encoding & Logic)
# ==========================================
@st.cache_data(ttl=2)
def get_sheet_data(key):
    try:
        r = requests.get(f"{CSV_URLS[key]}&nocache={time.time()}", timeout=10)
        r.encoding = 'utf-8-sig' # แก้ปัญหาภาษาไทยเป็นต่างดาว
        df = pd.read_csv(StringIO(r.text))
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

def send_to_google(payload):
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=20)
        return res.status_code == 200
    except:
        return False

# Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'order_success' not in st.session_state: st.session_state.order_success = None

# ==========================================
# 4. SIDEBAR (V21 Style)
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#d4af37; text-align:center;'>TAS V21</h1>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("เมนูใช้งาน", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 สต็อกสินค้า"])
    st.divider()
    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. POS SYSTEM (🛒)
# ==========================================
if menu == "🛒 ขายสินค้า":
    df_p = get_sheet_data("products")
    df_s = get_sheet_data("stock")
    
    # ดึงข้อมูลสต็อกล่าสุด
    stock_map = {}
    if not df_s.empty:
        stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_main, col_side = st.columns([2.2, 1.3])

    with col_main:
        st.markdown("### 📋 รายการสินค้า")
        if not df_p.empty:
            p_grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2])
                
                # คำนวณสต็อกเรียลไทม์
                in_cart = st.session_state.cart.get(p_name, {'q': 0})['q']
                current_stock = int(stock_map.get(p_name, 0)) - in_cart

                with p_grid[i % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{p_img}" width="100%" style="height:140px; object-fit:cover; border-radius:10px;">
                        <div style="margin:10px 0; font-size:16px;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div style="font-size:12px; color:#888;">คงเหลือ: {current_stock}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if current_stock > 0:
                        if st.button(f"เลือก {p_name}", key=f"add_{i}", use_container_width=True):
                            if p_name in st.session_state.cart:
                                st.session_state.cart[p_name]['q'] += 1
                            else:
                                st.session_state.cart[p_name] = {'p': p_price, 'q': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"sold_{i}", disabled=True, use_container_width=True)
        else:
            st.warning("ไม่พบข้อมูลสินค้า")

    with col_side:
        if st.session_state.order_success:
            # จอแสดงใบเสร็จหลังจบการขาย
            order = st.session_state.order_success
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.markdown(f"<center><b>TAS POS V21</b><br><small>{order['id']}</small></center><hr>", unsafe_allow_html=True)
            for k, v in order['items'].items():
                st.write(f"{k} x{v['q']} : {v['p']*v['q']:,.0f} ฿")
            st.markdown(f"<hr><b>ยอดสุทธิ: {order['total']:,.0f} ฿</b>", unsafe_allow_html=True)
            
            if order['method'] == "เงินสด":
                cash = st.number_input("เงินที่รับมา", min_value=float(order['total']), step=10.0)
                st.markdown(f"<h2 style='color:red; text-align:right;'>เงินทอน: {cash - order['total']:,.0f}</h2>", unsafe_allow_html=True)
            else:
                st.image(f"https://promptpay.io/{PROMPTPAY_ID}/{order['total']}.png")
            
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("➕ เริ่มบิลใหม่", use_container_width=True, type="primary"):
                st.session_state.order_success = None
                st.rerun()
        else:
            st.markdown("### 🛒 ตะกร้าสินค้า")
            grand_total = 0
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า")
            else:
                for k, v in list(st.session_state.cart.items()):
                    item_total = v['p'] * v['q']
                    grand_total += item_total
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="cart-item">
                            <b>{k}</b><br>
                            <span style="color:#d4af37;">{v['p']:,.0f} x {v['q']} = {item_total:,.0f} ฿</span>
                        </div>
                        """, unsafe_allow_html=True)
                        c1, c2 = st.columns(2)
                        if c1.button("➕", key=f"plus_{k}"):
                            # ตรวจสต็อกก่อนบวกเพิ่ม
                            if int(stock_map.get(k, 0)) > st.session_state.cart[k]['q']:
                                st.session_state.cart[k]['q'] += 1
                                st.rerun()
                            else: st.error("สต็อกหมด")
                        if c2.button("🗑️", key=f"del_{k}"):
                            del st.session_state.cart[k]
                            st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#d4af37;'>{grand_total:,.0f} ฿</h1>", unsafe_allow_html=True)
                pay_method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("🚀 ยืนยันการขาย", use_container_width=True, type="primary"):
                    now = datetime.now()
                    bill_id = f"POS{int(time.time())}"
                    
                    payload = {
                        "action": "checkout",
                        "date": now.strftime("%d/%m/%Y"),
                        "time": now.strftime("%H:%M:%S"),
                        "bill_id": bill_id,
                        "total": float(grand_total),
                        "method": pay_method,
                        "summary": ", ".join([f"{k}({v['q']})" for k,v in st.session_state.cart.items()])
                    }
                    
                    if send_to_google(payload):
                        st.session_state.order_success = {
                            "id": bill_id, "total": grand_total, 
                            "items": dict(st.session_state.cart), "method": pay_method
                        }
                        st.session_state.cart = {}
                        st.cache_data.clear()
                        st.rerun()

# ==========================================
# 6. ANALYTICS (📊) - Fixed Datetime Bug
# ==========================================
elif menu == "📊 รายงานยอดขาย":
    st.markdown("### 📊 วิเคราะห์ผลประกอบการ")
    df = get_sheet_data("sales")
    
    if not df.empty:
        try:
            # ป้องกันปัญหาคอลัมน์ไม่ตรง
            df.columns = ['วันที่', 'เวลา', 'เลขบิล', 'ยอดเงิน', 'วิธีชำระ', 'รายการ']
            df['ยอดเงิน'] = pd.to_numeric(df['ยอดเงิน'], errors='coerce').fillna(0)
            
            # แก้บั๊ก Datetime Red Box
            df['วันที่'] = pd.to_datetime(df['วันที่'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['วันที่'])
            
            today = datetime.now().date()
            val_today = df[df['วันที่'].dt.date == today]['ยอดเงิน'].sum()
            bill_today = len(df[df['วันที่'].dt.date == today])

            m1, m2 = st.columns(2)
            m1.metric("ยอดขายวันนี้", f"{val_today:,.0f} ฿")
            m2.metric("จำนวนบิลวันนี้", f"{bill_today} บิล")
            
            st.divider()
            st.write("ประวัติการขายล่าสุด")
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        except Exception as e:
            st.error(f"โครงสร้างข้อมูลใน Sheet ไม่ถูกต้อง: {e}")
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อกสินค้า":
    st.markdown("### 📦 สถานะคลังสินค้าคงเหลือ")
    df_s = get_sheet_data("stock")
    if not df_s.empty:
        st.dataframe(df_s, use_container_width=True)
    else:
        st.warning("ไม่สามารถดึงข้อมูลสต็อกได้")
