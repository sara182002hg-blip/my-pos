import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"

st.set_page_config(page_title="Ultimate Premium POS", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #2ecc71; }
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE FUNCTIONS ---
def fix_columns(df):
    """ ป้องกัน KeyError โดยการล้างชื่อคอลัมน์ให้เป็นตัวพิมพ์เล็กทั้งหมด """
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

@st.cache_data(ttl=10) # ดึงข้อมูลใหม่ทุก 10 วินาทีเมื่อมีการรีเฟรช
def fetch_all_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            # ดึงข้อมูลและปรับชื่อคอลัมน์ทันที
            prods = fix_columns(pd.DataFrame(res_json.get('products', [])))
            stock = fix_columns(pd.DataFrame(res_json.get('stock', [])))
            return {"products": prods, "stock": stock}
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
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
    menu = st.radio("เมนูหลัก", ["🛒 รายการขาย", "📊 รายงานยอดขาย", "📦 สต็อกออนไลน์"])
    if st.button("🔄 Sync ข้อมูลใหม่"):
        st.session_state.app_data = fetch_all_data()
        st.rerun()

# --- MAIN LOGIC ---
if st.session_state.app_data is None:
    st.warning("⚠️ กำลังพยายามดึงข้อมูล... หากนานเกินไปกรุณาตรวจสอบการตั้งค่า Google Sheets")
else:
    df_prods = st.session_state.app_data['products']
    df_stock = st.session_state.app_data['stock']

    # --- 🛒 PAGE: SALES ---
    if menu == "🛒 รายการขาย":
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📦 รายการสินค้า")
            # ช่องค้นหา
            search = st.text_input("🔍 ค้นหาสินค้า...", placeholder="พิมพ์ชื่อสินค้าที่ต้องการ")
            
            # กรองสินค้าตามชื่อ (รองรับคอลัมน์ 'name')
            name_col = 'name' if 'name' in df_prods else df_prods.columns[1]
            items = df_prods[df_prods[name_col].str.contains(search, case=False)] if search else df_prods
            
            # แสดงสินค้าแบบ Grid 3 คอลัมน์
            p_cols = st.columns(3)
            for i, row in items.iterrows():
                with p_cols[i % 3]:
                    with st.container(border=True):
                        p_id = str(row['id']) if 'id' in row else str(row.iloc[0])
                        p_name = row[name_col]
                        p_price = float(row['price']) if 'price' in row else 0.0
                        
                        # หาจำนวน Stock ที่ตรงกัน
                        id_col_stock = 'id' if 'id' in df_stock else df_stock.columns[0]
                        qty_col_stock = 'qty' if 'qty' in df_stock else df_stock.columns[2]
                        s_row = df_stock[df_stock[id_col_stock].astype(str) == p_id]
                        current_qty = int(s_row[qty_col_stock].values[0]) if not s_row.empty else 0
                        
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"### ฿{p_price:,.2f}")
                        st.caption(f"คงเหลือ: {current_qty}")
                        
                        if st.button("➕ เพิ่ม", key=f"add_{p_id}", disabled=(current_qty <= 0)):
                            if p_id in st.session_state.cart:
                                st.session_state.cart[p_id]['qty'] += 1
                            else:
                                st.session_state.cart[p_id] = {'name': p_name, 'price': p_price, 'qty': 1}
                            st.rerun()

        with col2:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.write("ไม่มีสินค้าในตะกร้า")
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
                st.metric("ยอดรวมทั้งสิ้น", f"฿{total:,.2f}")
                
                pay_method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if pay_method == "เงินสด":
                    received = st.number_input("รับเงินมา", min_value=0.0, value=float(total))
                    if received >= total > 0:
                        st.success(f"เงินทอน: ฿{received - total:,.2f}")
                else:
                    # สร้าง QR Code แบบ Dynamic
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://promptpay.io/0812345678/{total}"
                    st.image(qr_url, caption="สแกนเพื่อชำระเงิน")

                if st.button("✅ ยืนยันการขาย (ตัดสต็อก)", type="primary"):
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
                        st.success("บันทึกสำเร็จ!")
                        st.session_state.cart = {}
                        st.session_state.app_data = fetch_all_data() # อัปเดตข้อมูลทันที
                        st.rerun()

    # --- 📊 PAGE: REPORT ---
    elif menu == "📊 รายงานยอดขาย":
        st.subheader("📊 วิเคราะห์ภาพรวมยอดขาย")
        m1, m2, m3 = st.columns(3)
        # ตัวอย่างการแสดงผลรายงาน (สามารถขยายเพิ่มตามข้อมูลใน Sheet Sales)
        m1.metric("เป้ายอดขาย", "฿50,000", "+5%")
        m2.metric("จำนวนรายการวันนี้", "12 รายการ")
        m3.metric("สถานะระบบ", "Online")
        
        st.info("💡 ระบบรายงานกำลังซิงค์ข้อมูลจากหน้า DailySummary ใน Google Sheets")
        
        if st.button("📝 ส่งรายงานสรุปยอดเข้ากลุ่ม (ถ้ามี)"):
            st.toast("กำลังส่งข้อมูลรายงาน...")

    # --- 📦 PAGE: STOCK ---
    elif menu == "📦 สต็อกออนไลน์":
        st.subheader("📦 คลังสินค้าคงเหลือ")
        
        # ค้นหาคอลัมน์ qty ให้ถูกต้อง
        id_col = 'id' if 'id' in df_stock else df_stock.columns[0]
        qty_col = 'qty' if 'qty' in df_stock else df_stock.columns[2]
        
        # แจ้งเตือนสินค้าสต็อกต่ำ (< 5 ชิ้น)
        low_stock = df_stock[df_stock[qty_col].astype(float) < 5]
        if not low_stock.empty:
            st.error(f"🚨 สินค้าใกล้หมด {len(low_stock)} รายการ!")
            st.dataframe(low_stock, use_container_width=True)
        
        st.dataframe(df_stock, use_container_width=True, hide_index=True)
