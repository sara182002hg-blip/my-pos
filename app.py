import streamlit as st
import requests
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime

# --- CONFIGURATION ---
# ใช้ URL ของคุณที่ส่งมาล่าสุด
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"

st.set_page_config(page_title="Ultimate Premium POS", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #2ecc71; }
    .product-card { border: 1px solid #333; padding: 15px; border-radius: 10px; background: #1e1e1e; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE FUNCTIONS ---
def format_df_columns(df):
    """ ป้องกัน KeyError โดยการล้างชื่อคอลัมน์ให้เป็นตัวพิมพ์เล็กและไม่มีช่องว่าง """
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

@st.cache_data(ttl=60) # Cache ข้อมูล 1 นาทีเพื่อความเร็ว แต่รีเฟรชได้
def fetch_all_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            # แปลงเป็น DataFrame และจัดการคอลัมน์
            prods = format_df_columns(pd.DataFrame(res_json.get('products', [])))
            stock = format_df_columns(pd.DataFrame(res_json.get('stock', [])))
            return {"products": prods, "stock": stock}
    except Exception as e:
        st.error(f"เชื่อมต่อผิดพลาด: {e}")
    return None

def send_to_sheet(payload):
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        return res.status_code == 200
    except:
        return False

# --- INITIALIZE STATE ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'app_data' not in st.session_state:
    st.session_state.app_data = fetch_all_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 PREMIUM POS")
    menu = st.radio("เมนูหลัก", ["🛒 รายการขาย", "📊 รายงาน & สรุปยอด", "📦 สต็อกออนไลน์"])
    if st.button("🔄 Sync ข้อมูลใหม่ (Real-time)"):
        st.session_state.app_data = fetch_all_data()
        st.toast("อัปเดตข้อมูลล่าสุดแล้ว")

# --- MAIN LOGIC ---
if st.session_state.app_data is None:
    st.error("ไม่สามารถโหลดข้อมูลจาก Google Sheets ได้ กรุณาตรวจสอบ Apps Script")
else:
    df_prods = st.session_state.app_data['products']
    df_stock = st.session_state.app_data['stock']

    # --- 🛒 PAGE: SALES ---
    if menu == "🛒 รายการขาย":
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📦 รายการสินค้า")
            search = st.text_input("ค้นหาสินค้า...", placeholder="พิมพ์ชื่อสินค้าที่นี่")
            
            # แสดงสินค้าแบบ Grid
            items = df_prods[df_prods['name'].str.contains(search, case=False)] if 'name' in df_prods else df_prods
            
            p_cols = st.columns(3)
            for i, row in items.iterrows():
                with p_cols[i % 3]:
                    with st.container(border=True):
                        # ดึงข้อมูล Stock ที่ตรงกัน
                        p_id = str(row['id'])
                        s_row = df_stock[df_stock['id'].astype(str) == p_id]
                        current_qty = s_row['qty'].values[0] if not s_row.empty else 0
                        
                        st.markdown(f"**{row['name']}**")
                        st.markdown(f"### ฿{row['price']}")
                        st.caption(f"คงเหลือ: {current_qty}")
                        
                        if st.button("➕ เพิ่ม", key=f"btn_{p_id}", disabled=(current_qty <= 0)):
                            if p_id in st.session_state.cart:
                                st.session_state.cart[p_id]['qty'] += 1
                            else:
                                st.session_state.cart[p_id] = {'name': row['name'], 'price': float(row['price']), 'qty': 1}
                            st.rerun()

        with col2:
            st.subheader("🛒 ตะกร้า")
            total = 0
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้า")
            else:
                for p_id, item in list(st.session_state.cart.items()):
                    with st.container(border=True):
                        sub = item['price'] * item['qty']
                        total += sub
                        st.write(f"**{item['name']}**")
                        c1, c2, c3 = st.columns([1,1,2])
                        if c1.button("➖", key=f"m_{p_id}"):
                            st.session_state.cart[p_id]['qty'] -= 1
                            if st.session_state.cart[p_id]['qty'] <= 0: del st.session_state.cart[p_id]
                            st.rerun()
                        c2.write(f"x{item['qty']}")
                        if c3.button("➕", key=f"p_{p_id}"):
                            st.session_state.cart[p_id]['qty'] += 1
                            st.rerun()
                
                st.divider()
                st.metric("ยอดรวมสุทธิ", f"฿{total:,.2f}")
                
                pay_method = st.segmented_control("ชำระเงิน", ["เงินสด", "พร้อมเพย์"], default="เงินสด")
                
                if pay_method == "เงินสด":
                    received = st.number_input("รับเงิน", min_value=0.0, step=10.0)
                    if received >= total > 0:
                        st.success(f"เงินทอน: ฿{received - total:,.2f}")
                else:
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://promptpay.io/0812345678/{total}", caption="สแกนจ่ายที่นี่")

                if st.button("🔥 ยืนยันการขาย (ตัดสต็อก)", type="primary", use_container_width=True):
                    payload = {
                        "action": "recordSale",
                        "data": {
                            "items": str(st.session_state.cart),
                            "total": total,
                            "method": pay_method,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        },
                        "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                    }
                    if send_to_sheet(payload):
                        st.balloons()
                        st.session_state.cart = {}
                        st.session_state.app_data = fetch_all_data() # อัปเดตสต็อกทันที
                        st.success("บันทึกสำเร็จ!")
                        st.rerun()

    # --- 📊 PAGE: REPORT ---
    elif menu == "📊 รายงาน & สรุปยอด":
        st.subheader("📈 วิเคราะห์ยอดขาย")
        m1, m2, m3 = st.columns(3)
        # จำลองการสรุปผล (ในระบบจริงควรดึงจากแผ่น DailySummary)
        m1.metric("ยอดขายวันนี้", "฿12,450")
        m2.metric("จำนวนบิล", "42 บิล")
        m3.metric("สินค้าขายดี", "Espresso")
        
        st.divider()
        if st.button("⚠️ กดสรุปยอดรายวัน (รีเซ็ตยอด)", type="secondary"):
            if send_to_sheet({"action": "resetDaily"}):
                st.success("สรุปยอดและรีเซ็ตเรียบร้อยแล้ว!")
        
        st.info("ประวัติการซื้อล่าสุด (ดึงข้อมูลจากแผ่น Sales...)")
        # สามารถเพิ่มโค้ดแสดงตาราง Sales ตรงนี้ได้

    # --- 📦 PAGE: STOCK ---
    elif menu == "📦 สต็อกออนไลน์":
        st.subheader("ตรวจสอบคลังสินค้า")
        
        # ค้นหาคอลัมน์ qty ให้เจอ
        qty_col = 'qty' if 'qty' in df_stock else df_stock.columns[2] 
        
        # แจ้งเตือนสต็อกต่ำ
        low_stock = df_stock[df_stock[qty_col].astype(float) < 5]
        if not low_stock.empty:
            st.error(f"🚨 มีสินค้าใกล้หมดสต็อก! ({len(low_stock)} รายการ)")
            st.table(low_stock)
        
        st.dataframe(df_stock, use_container_width=True)
        st.caption(f"อัปเดตล่าสุดเมื่อ: {datetime.now().strftime('%H:%M:%S')}")
