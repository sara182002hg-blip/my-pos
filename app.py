import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta
import plotly.express as px  # เพิ่มกราฟวิเคราะห์กลับมา

# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
}

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V22", layout="wide")

# ==========================================
# 2. PREMIUM CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #050505; color: #E0E0E0; }
    .product-box { background: rgba(28, 33, 40, 0.9); border: 1px solid #D4AF37; border-radius: 15px; padding: 15px; text-align: center; margin-bottom: 10px; transition: 0.3s; }
    .product-box:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(212, 175, 55, 0.3); }
    .price-tag { font-size: 24px; color: #D4AF37; font-weight: 600; margin: 5px 0; }
    .receipt-container { background: #FFF; color: #000; padding: 25px; border-radius: 10px; font-family: 'Courier New', monospace; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .metric-card { background: #1c2128; padding: 20px; border-radius: 15px; border-left: 5px solid #D4AF37; }
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
                df = pd.read_csv(StringIO(res.text))
                return df.dropna(how='all')
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
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3514/3514491.png", width=100)
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>TAS PLATINUM</h1>", unsafe_allow_html=True)
    menu = st.selectbox("เมนูควบคุม", ["🛒 ขายสินค้า (POS)", "📊 รายงานวิเคราะห์", "📦 จัดการสต็อก", "🛠️ ตั้งค่าระบบ"])
    if st.button("🔄 รีเฟรชข้อมูล"): st.rerun()

# ==========================================
# 5. PAGE: POS SYSTEM (ขายสินค้า)
# ==========================================
if menu == "🛒 ขายสินค้า (POS)":
    df_p = DataEngine.fetch("products")
    df_s = DataEngine.fetch("stock")
    
    # ดึงข้อมูลสต็อกล่าสุดมาโชว์ที่ปุ่ม
    stock_map = {}
    if not df_s.empty:
        stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    c_left, c_right = st.columns([2, 1.2])

    with c_left:
        st.markdown("<h2 style='color:#D4AF37;'>เมนูสินค้า</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            cols = st.columns(3)
            for i, row in df_p.iterrows():
                name = str(row.iloc[0]).strip()
                price = float(row.iloc[1])
                img = str(row.iloc[2]) if len(row) > 2 else "https://via.placeholder.com/200"
                
                # คำนวณสต็อกที่เหลือ (สต็อกในชีต - ในตะกร้า)
                raw_stock = int(stock_map.get(name, 0))
                in_cart = st.session_state.cart.get(name, {}).get('qty', 0)
                available = raw_stock - in_cart

                with cols[i % 3]:
                    st.markdown(f"""<div class="product-box">
                        <img src="{img}" width="100%" style="height:140px; object-fit:cover; border-radius:10px;">
                        <div style="margin-top:10px; font-weight:600;">{name}</div>
                        <div class="price-tag">{price:,.0f} ฿</div>
                        <div style="font-size:12px; color:#888;">คงเหลือ: {available}</div>
                    </div>""", unsafe_allow_html=True)
                    if available > 0:
                        if st.button(f"➕ เพิ่ม {name}", key=f"btn_{i}"):
                            if name not in st.session_state.cart:
                                st.session_state.cart[name] = {'price': price, 'qty': 1}
                            else:
                                st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", disabled=True, key=f"sold_{i}")

    with c_right:
        if st.session_state.last_receipt:
            res = st.session_state.last_receipt
            st.markdown(f"""<div class="receipt-container">
                <center><h2 style="margin:0;">TAS SHOP</h2><p>เลขที่: {res['bill_id']}</p></center>
                <hr>
                {''.join([f'<div style="display:flex; justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                <hr>
                <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:20px;">
                    <span>ยอดสุทธิ</span><span>{res['total']:,.0f} ฿</span>
                </div>
                <p style="text-align:center; margin-top:10px;">ขอบคุณที่ใช้บริการครับ</p>
            </div>""", unsafe_allow_html=True)
            if st.button("✅ รับทราบ / บิลถัดไป", use_container_width=True):
                st.session_state.last_receipt = None; st.rerun()
        else:
            st.markdown("### 🧺 ตะกร้าสินค้า")
            total = 0
            for k, v in list(st.session_state.cart.items()):
                total += v['price'] * v['qty']
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{k}** x {v['qty']}")
                if c2.button("❌", key=f"del_{k}"): del st.session_state.cart[k]; st.rerun()
            
            st.divider()
            st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total:,.0f} ฿</h1>", unsafe_allow_html=True)
            method = st.radio("ช่องทางชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
            
            if total > 0:
                if st.button("💳 ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                    now = datetime.now()
                    bill_id = f"TAS{int(time.time())}"
                    items_str = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    
                    payload = {
                        "action": "checkout",
                        "date": now.strftime("%d/%m/%Y"), # คอลัมน์ A
                        "time": now.strftime("%H:%M:%S"), # คอลัมน์ B
                        "bill_id": bill_id,               # คอลัมน์ C
                        "total": float(total),             # คอลัมน์ D
                        "method": method,                 # คอลัมน์ E
                        "summary": items_str              # คอลัมน์ F
                    }
                    
                    if DataEngine.post_to_gsheet(payload):
                        st.session_state.last_receipt = {"bill_id": bill_id, "items": dict(st.session_state.cart), "total": total}
                        st.session_state.cart = {}
                        st.rerun()

# ==========================================
# 6. PAGE: ANALYTICS (แก้ไขยอด 0 บาท)
# ==========================================
elif menu == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ข้อมูลการขาย</h2>", unsafe_allow_html=True)
    df = DataEngine.fetch("sales")
    
    if not df.empty:
        try:
            # แปลงวันที่ให้เป็น Format ที่ถูกต้อง (คอลัมน์ A คือ index 0)
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], dayfirst=True, errors='coerce')
            # ดึงยอดเงิน (คอลัมน์ D คือ index 3)
            df.iloc[:, 3] = pd.to_numeric(df.iloc[:, 3].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            # คำนวณยอด
            today = datetime.now().date()
            sales_today = df[df.iloc[:, 0].dt.date == today].iloc[:, 3].sum()
            sales_month = df[df.iloc[:, 0].dt.month == datetime.now().month].iloc[:, 3].sum()
            total_bills = len(df)

            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f'<div class="metric-card"><small>ยอดขายวันนี้</small><h3>{sales_today:,.2f} ฿</h3></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><small>ยอดขายเดือนนี้</small><h3>{sales_month:,.2f} ฿</h3></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-card"><small>จำนวนบิลทั้งหมด</small><h3>{total_bills} รายการ</h3></div>', unsafe_allow_html=True)

            # กราฟยอดขายรายวัน
            st.markdown("### 📈 กราฟแนวโน้มยอดขาย")
            daily_sales = df.groupby(df.iloc[:, 0].dt.date)[df.columns[3]].sum().reset_index()
            daily_sales.columns = ['วันที่', 'ยอดขาย']
            fig = px.line(daily_sales, x='วันที่', y='ยอดขาย', markers=True, template="plotly_dark")
            fig.update_traces(line_color='#D4AF37')
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📋 ประวัติการขายล่าสุด")
            st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")
    else:
        st.info("ยังไม่มีข้อมูลการขายในระบบ")

# ==========================================
# 7. PAGE: STOCK & SETTINGS
# ==========================================
elif menu == "📦 จัดการสต็อก":
    st.markdown("<h2 style='color:#D4AF37;'>📦 สต็อกสินค้าคงเหลือ</h2>", unsafe_allow_html=True)
    st.dataframe(DataEngine.fetch("stock"), use_container_width=True)

elif menu == "🛠️ ตั้งค่าระบบ":
    st.markdown("### 🛠️ การตั้งค่า")
    st.write(f"**Apps Script URL:** `{SCRIPT_URL}`")
    st.write(f"**PromptPay ID:** `{PROMPTPAY_ID}`")
    if st.button("ล้างแคชข้อมูล"):
        st.cache_data.clear()
        st.success("ล้างข้อมูลเรียบร้อย")
