import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# ==========================================
# 1. การตั้งค่าระบบ (Config)
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

# URL จาก Google Apps Script ของพี่
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS PLATINUM V21", layout="wide")

# --- UI Custom Style ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #0e1117; color: white; }
    .product-card { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; text-align: center; }
    .price-text { color: #d4af37; font-size: 22px; font-weight: bold; }
    .receipt-box { background: white; color: black; padding: 25px; border-radius: 10px; font-family: 'Courier New'; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันจัดการข้อมูล
# ==========================================
@st.cache_data(ttl=3)
def get_data(key):
    try:
        r = requests.get(f"{CSV_URLS[key]}&nocache={time.time()}", timeout=10)
        df = pd.read_csv(StringIO(r.text))
        return df.dropna(how='all')
    except: return pd.DataFrame()

def post_sale(payload):
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=15)
        return res.status_code == 200
    except: return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'checkout' not in st.session_state: st.session_state.checkout = None

# ==========================================
# 3. เมนูหลัก (Sidebar)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color:#d4af37;'>TAS PLATINUM</h2>", unsafe_allow_html=True)
    menu = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"])
    st.divider()
    if st.button("🔄 Sync Data (Force)"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 4. หน้าขายสินค้า
# ==========================================
if menu == "🛒 หน้าขายสินค้า":
    df_p = get_data("products")
    df_s = get_data("stock")
    
    # ดึงสต็อก (A=ชื่อ, B=จำนวน)
    stock_dict = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict() if not df_s.empty else {}

    col_l, col_r = st.columns([2.2, 1.3])

    with col_l:
        st.markdown("### 📋 รายการเมนู")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                name = str(row.iloc[0]).strip()
                price = float(row.iloc[1])
                img = str(row.iloc[2])
                
                in_cart = st.session_state.cart.get(name, {'q':0})['q']
                avail = int(stock_dict.get(name, 0)) - in_cart

                with grid[i % 3]:
                    st.markdown(f'''<div class="product-card">
                        <img src="{img}" width="100%" style="height:140px; object-fit:cover; border-radius:8px;">
                        <div style="margin:10px 0;">{name}</div>
                        <div class="price-text">{price:,.0f} ฿</div>
                        <div style="font-size:12px; color:#8b949e;">คลังเหลือ: {avail}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    if avail > 0:
                        if st.button(f"เลือก {name}", key=f"add_{i}", use_container_width=True):
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'p': price, 'q': 0})
                            st.session_state.cart[name]['q'] += 1
                            st.rerun()
                    else: st.button("สินค้าหมด", disabled=True, key=f"ex_{i}", use_container_width=True)

    with col_r:
        if st.session_state.checkout:
            res = st.session_state.checkout
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.markdown(f"<center><b>TAS PLATINUM V21</b><br><small>{res['id']}</small></center><hr>", unsafe_allow_html=True)
            for k, v in res['items'].items():
                st.write(f"{k} x{v['q']} : {v['p']*v['q']:,.0f}")
            st.markdown(f"<hr><b>รวมสุทธิ: {res['total']:,.0f} ฿</b>", unsafe_allow_html=True)
            
            if res['method'] == "เงินสด":
                cash = st.number_input("รับเงินมา", min_value=float(res['total']), step=10.0)
                st.markdown(f"<h2 style='color:red; text-align:right;'>ทอน: {cash - res['total']:,.0f} ฿</h2>", unsafe_allow_html=True)
            else:
                st.image(f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png")
            
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", use_container_width=True):
                st.session_state.checkout = None; st.rerun()
        else:
            st.markdown("### 🛒 ตะกร้าของฉัน")
            total = 0
            for k, v in list(st.session_state.cart.items()):
                total += v['p'] * v['q']
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{k}** x{v['q']}")
                if c2.button("🗑️", key=f"del_{k}"): del st.session_state.cart[k]; st.rerun()
            
            st.markdown(f"<h1 style='text-align:right; color:#d4af37;'>{total:,.0f} ฿</h1>", unsafe_allow_html=True)
            pay_m = st.radio("ช่องทางชำระ", ["เงินสด", "พร้อมเพย์"], horizontal=True)
            if total > 0 and st.button("🚀 ยืนยันการขาย", use_container_width=True, type="primary"):
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
                if post_sale(payload):
                    st.session_state.checkout = {"id": bid, "total": total, "items": dict(st.session_state.cart), "method": pay_m}
                    st.session_state.cart = {}; st.cache_data.clear(); st.rerun()

# ==========================================
# 5. หน้าวิเคราะห์ (แก้บัค DateTime)
# ==========================================
elif menu == "📊 รายงานวิเคราะห์":
    st.markdown("### 📊 วิเคราะห์ผลประกอบการ")
    df = get_data("sales")
    if not df.empty:
        try:
            # 1. แปลงวันที่ (คอลัมน์ A)
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], dayfirst=True, errors='coerce')
            # 2. แปลงยอดเงิน (คอลัมน์ D)
            df.iloc[:, 3] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
            
            # ลบแถวที่แปลงวันที่ไม่ได้ (เช่น แถว Header ที่ติดมา)
            df = df.dropna(subset=[df.columns[0]])

            today = datetime.now().date()
            val_today = df[df.iloc[:, 0].dt.date == today].iloc[:, 3].sum()
            count_today = len(df[df.iloc[:, 0].dt.date == today])

            c1, c2 = st.columns(2)
            c1.metric("ยอดขายวันนี้", f"{val_today:,.0f} ฿")
            c2.metric("จำนวนบิลวันนี้", f"{count_today} บิล")
            
            st.divider()
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")
            st.info("ตรวจสอบว่าใน Google Sheets หน้า Sales คอลัมน์ D คือยอดเงินใช่หรือไม่?")
    else: st.warning("ยังไม่มีข้อมูลการขาย")

elif menu == "📦 สต็อก & คลัง":
    st.markdown("### 📦 รายการสินค้าในคลัง")
    st.dataframe(get_data("stock"), use_container_width=True)
