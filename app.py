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
# 2. PREMIUM CSS (V21 STYLING)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #0e1117; color: white; }
    .product-card { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; text-align: center; }
    .price-text { color: #d4af37; font-size: 22px; font-weight: bold; }
    .receipt-box { background: white; color: black; padding: 25px; border-radius: 10px; font-family: 'Courier New'; }
    .change-text { color: #d32f2f; font-size: 28px; font-weight: bold; text-align: right; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. STABLE DATA ENGINE
# ==========================================
@st.cache_data(ttl=2)
def load_data(key):
    try:
        # ใช้ utf-8-sig เพื่อแก้ปัญหาภาษาต่างดาว
        r = requests.get(f"{CSV_URLS[key]}&nocache={time.time()}", timeout=10)
        r.encoding = 'utf-8-sig' 
        df = pd.read_csv(StringIO(r.text))
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"การเชื่อมต่อฐานข้อมูล {key} ขัดข้อง")
        return pd.DataFrame()

def sync_sale(data):
    try:
        res = requests.post(SCRIPT_URL, json=data, timeout=15)
        return res.status_code == 200
    except:
        return False

# Session State Initialization
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'checkout_done' not in st.session_state: st.session_state.checkout_done = None

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color:#d4af37; text-align:center;'>TAS PLATINUM</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:12px;'>POS SYSTEM ULTIMATE V21</p>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"])
    st.divider()
    if st.button("🔄 Sync Data (Force)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. POS INTERFACE (🛒)
# ==========================================
if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data("products")
    df_s = load_data("stock")
    
    # ดึงสต็อก (คอลัมน์แรก=ชื่อ, คอลัมน์สอง=จำนวน)
    stock_dict = {}
    if not df_s.empty:
        stock_dict = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_l, col_r = st.columns([2.2, 1.3])

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
                    st.markdown(f'''<div class="product-card">
                        <img src="{img}" width="100%" style="height:140px; object-fit:cover; border-radius:8px;">
                        <div style="margin:10px 0; font-weight:bold;">{name}</div>
                        <div class="price-text">{price:,.0f} ฿</div>
                        <div style="font-size:12px; color:#8b949e;">คลังคงเหลือ: {avail}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    if avail > 0:
                        if st.button(f"เลือก {name}", key=f"add_{i}", use_container_width=True):
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'p': price, 'q': 0})
                            st.session_state.cart[name]['q'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", disabled=True, key=f"sold_{i}", use_container_width=True)

    with col_r:
        if st.session_state.checkout_done:
            # จอแสดงใบเสร็จและเงินทอน
            res = st.session_state.checkout_done
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.markdown(f"<center><b>TAS PLATINUM V21</b><br><small>{res['id']}</small></center><hr>", unsafe_allow_html=True)
            for k, v in res['items'].items():
                st.write(f"{k} x{v['q']} : {v['p']*v['q']:,.0f} ฿")
            st.markdown(f"<hr><h3 style='margin:0;'>ยอดสุทธิ: {res['total']:,.0f} ฿</h3>", unsafe_allow_html=True)
            
            if res['method'] == "เงินสด":
                cash = st.number_input("เงินที่รับมา", min_value=float(res['total']), step=10.0, format="%.2f")
                st.markdown(f'<div class="change-text">เงินทอน: {cash - res['total']:,.0f} ฿</div>', unsafe_allow_html=True)
            else:
                st.image(f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png")
                st.info("ลูกค้าสแกนเรียบร้อยแล้ว?")
            
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่ (Clear)", use_container_width=True, type="primary"):
                st.session_state.checkout_done = None
                st.rerun()
        else:
            st.markdown("### 🛒 ตะกร้าสินค้า")
            total_price = 0
            if not st.session_state.cart:
                st.write("ยังไม่มีสินค้าในตะกร้า")
            else:
                for k, v in list(st.session_state.cart.items()):
                    total_price += v['p'] * v['q']
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{k}** x{v['q']}")
                    if c2.button("🗑️", key=f"del_{k}"):
                        del st.session_state.cart[k]
                        st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#d4af37;'>{total_price:,.0f} ฿</h1>", unsafe_allow_html=True)
                pay_type = st.radio("ช่องทางชำระ", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("🚀 ยืนยันการขาย", use_container_width=True, type="primary"):
                    now = datetime.now()
                    bid = f"POS{int(time.time())}"
                    summary_str = ", ".join([f"{k}({v['q']})" for k,v in st.session_state.cart.items()])
                    
                    payload = {
                        "action": "checkout",
                        "date": now.strftime("%d/%m/%Y"),
                        "time": now.strftime("%H:%M:%S"),
                        "bill_id": bid,
                        "total": float(total_price),
                        "method": pay_type,
                        "summary": summary_str
                    }
                    
                    if sync_sale(payload):
                        st.session_state.checkout_done = {
                            "id": bid, "total": total_price, 
                            "items": dict(st.session_state.cart), "method": pay_type
                        }
                        st.session_state.cart = {}
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการบันทึกข้อมูล กรุณาลองอีกครั้ง")

# ==========================================
# 6. ANALYTICS (📊)
# ==========================================
elif menu == "📊 รายงานวิเคราะห์":
    st.markdown("### 📊 วิเคราะห์ผลประกอบการ")
    df = load_data("sales")
    
    if not df.empty:
        try:
            # ตั้งชื่อคอลัมน์ใหม่เพื่อให้คำนวณง่าย (ตรงตาม Apps Script)
            df.columns = ['วันที่', 'เวลา', 'เลขบิล', 'ยอดเงิน', 'วิธีชำระ', 'รายการ']
            
            # แปลงยอดเงินเป็นตัวเลข
            df['ยอดเงิน'] = pd.to_numeric(df['ยอดเงิน'], errors='coerce').fillna(0)
            
            # แปลงวันที่ให้ถูกต้อง
            df['วันที่'] = pd.to_datetime(df['วันที่'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['วันที่']) # ลบแถวที่แปลงวันที่ไม่ได้

            today = datetime.now().date()
            sales_today = df[df['วันที่'].dt.date == today]['ยอดเงิน'].sum()
            bills_today = len(df[df['วันที่'].dt.date == today])

            c1, c2 = st.columns(2)
            c1.metric("ยอดขายวันนี้", f"{sales_today:,.2f} ฿")
            c2.metric("จำนวนบิลวันนี้", f"{bills_today} บิล")
            
            st.divider()
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        except Exception as e:
            st.warning(f"ระบบกำลังปรับปรุงรูปแบบข้อมูลในชีท: {e}")
    else:
        st.info("ยังไม่มีข้อมูลการขายในระบบ")

# ==========================================
# 7. STOCK (📦)
# ==========================================
elif menu == "📦 สต็อก & คลัง":
    st.markdown("### 📦 รายการสินค้าคงคลัง")
    df_s = load_data("stock")
    if not df_s.empty:
        st.dataframe(df_s, use_container_width=True)
    else:
        st.warning("ไม่สามารถโหลดข้อมูลสต็อกได้")
