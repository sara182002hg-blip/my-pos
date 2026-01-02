import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFd4Q3VTiqyhFhiI0Atu6Hu-ZZQ_0tP3PgE6jej9Q3igT2LtBV4g9te0Fw-hV0F9M/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Professional", layout="wide")

# ปรับขนาด Sidebar และ Font (เมนูระบบใหญ่ขึ้น)
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { font-size: 20px !important; }
    .stButton>button { border-radius: 8px; }
    .product-card { border: 1px solid #ddd; padding: 10px; border-radius: 10px; text-align: center; background: #262730; }
    </style>
    """, unsafe_allow_html=True)

# ฟังก์ชันโหลดข้อมูล (ใส่ Cache เพื่อความเร็ว ลดการหน่วง)
@st.cache_data(ttl=5) # ข้อมูลจะสดใหม่ทุก 5 วินาที
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=5)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# --- Sidebar เมนูระบบ ---
st.sidebar.header("🏬 เมนูระบบ")
menu = st.sidebar.radio("", ["🛒 ขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"], label_visibility="collapsed")

if menu == "🛒 ขายสินค้า":
    df_p = load_data(URL_PRODUCTS)
    df_s = load_data(URL_STOCK)
    
    col_main, col_right = st.columns([2.5, 1.5])
    
    with col_main:
        # แยกหมวดหมู่สินค้า
        if not df_p.empty and 'Category' in df_p.columns:
            categories = ["ทั้งหมด"] + df_p['Category'].unique().tolist()
            selected_cat = st.selectbox("📂 เลือกหมวดหมู่สินค้า", categories)
            if selected_cat != "ทั้งหมด":
                df_p = df_p[df_p['Category'] == selected_cat]
        
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3) # ปรับเป็น 3 คอลัมน์เพื่อให้เห็นรูปชัดขึ้น
            for i, row in df_p.iterrows():
                # ดึงสต็อกจริง
                stock_qty = 0
                if not df_s.empty:
                    match = df_s[df_s['Name'] == row['Name']]
                    stock_qty = match.iloc[0]['Stock'] if not match.empty else 0

                with grid[i % 3]:
                    with st.container(border=True):
                        # แสดงรูปภาพสินค้า
                        img_url = row['Image_URL'] if 'Image_URL' in row and pd.notna(row['Image_URL']) else "https://via.placeholder.com/150"
                        st.image(img_url, use_container_width=True)
                        st.markdown(f"**{row['Name']}**")
                        st.markdown(f"<span style='color:#00ff00;'>{row['Price']:,} ฿</span>", unsafe_allow_html=True)
                        st.caption(f"คงเหลือ: {stock_qty}")
                        
                        cart_qty = st.session_state.cart.get(row['Name'], {}).get('qty', 0)
                        if stock_qty > cart_qty:
                            if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                                name = row['Name']
                                st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                                st.session_state.cart[name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ หมด", key=f"out_{i}", use_container_width=True, disabled=True)

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            
            # ส่วนใบเสร็จ HTML
            qr_html = ""
            if r['method'] == "📱 PromptPay":
                qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
                qr_html = f'<div style="text-align: center; margin-top: 10px;"><img src="{qr_url}" width="200" style="border: 1px solid #ddd;"/></div>'

            receipt_content = f"""
            <div id="receipt-print" style="background-color: white; color: black; padding: 20px; border-radius: 5px; font-family: monospace;">
                <div style="text-align: center;"><h2>TAS POS</h2><p>ID: {r['id']}</p></div>
                <hr style="border-top: 1px dashed black;">
                {''.join([f'<div style="display: flex; justify-content: space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n, i in r['items'].items()])}
                <hr style="border-top: 1px dashed black;">
                <div style="display: flex; justify-content: space-between; font-size: 20px; font-weight: bold;"><span>TOTAL</span><span>{r['total']:,} ฿</span></div>
                <p style="font-size: 12px; margin-top: 5px;">Payment: {r['method']}</p>
                {qr_html}
            </div>
            """
            st.markdown(receipt_content, unsafe_allow_html=True)
            
            # ปุ่มสั่งปริ้นใบเสร็จทันที
            if st.button("🖨️ สั่งพิมพ์ใบเสร็จ (Print)", use_container_width=True):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            
            if st.button("✅ เริ่มการขายใหม่", use_container_width=True, type="primary"):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart:
                st.info("ว่างเปล่า")
            else:
                total_sum = 0
                for name, item in list(st.session_state.cart.items()):
                    total_sum += item['price'] * item['qty']
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{name}** (x{item['qty']})")
                    if c2.button("🗑️", key=f"del_{name}"):
                        del st.session_state.cart[name]
                        st.rerun()
                st.divider()
                st.title(f"รวม: {total_sum:,} ฿")
                pay_method = st.radio("ชำระโดย", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("✅ ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    st.session_state.receipt = {"id": bill_id, "items": dict(st.session_state.cart), "total": total_sum, "method": pay_method}
                    try:
                        requests.post(SCRIPT_URL, json={"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": pay_method}, timeout=3)
                    except: pass
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        # แก้ไขการดึงชื่อคอลัมน์ให้ตรงตามภาพ
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
        if 'ยอดรวม' in df_sales.columns:
            st.metric("ยอดขายรวมทั้งหมด", f"{df_sales['ยอดรวม'].sum():,} ฿")
    else:
        st.warning("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อก":
    st.title("📦 สต็อกสินค้าคงเหลือ")
    df_stock = load_data(URL_STOCK)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
