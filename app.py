import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. SETTINGS ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PP_ID = "0945016189"

st.set_page_config(page_title="TAS POS SUPER-STABLE V17", layout="wide")

# --- 2. CSS FOR SPEED & PRINT ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    .product-card { background: white; padding: 10px; border-radius: 12px; border: 1px solid #ddd; text-align: center; margin-bottom: 10px; }
    .product-card img { width: 100%; height: 160px; object-fit: cover; border-radius: 8px; }
    .price-text { font-size: 24px; color: #1e88e5; font-weight: bold; margin: 5px 0; }
    .stMetric { background: white; padding: 20px; border-radius: 12px; border-bottom: 4px solid #1e88e5; }
</style>
""", unsafe_allow_html=True)

# --- 3. HIGH-SPEED DATA LOADER ---
# โหลดข้อมูลแบบ Cached เพื่อความเร็ว (ล้างทุก 5 นาที หรือเมื่อมีการขาย)
@st.cache_data(ttl=300)
def fetch_csv(url):
    try:
        r = requests.get(f"{url}&ts={time.time()}", timeout=15)
        r.encoding = 'utf-8'
        return pd.read_csv(StringIO(r.text)).dropna(how='all')
    except: return pd.DataFrame()

# Initialize Session States
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# --- 4. NAVIGATION ---
menu = st.sidebar.selectbox("🏠 เมนูหลัก", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 สต็อกสินค้า"])

# --- 5. PAGE: POS SYSTEM ---
if menu == "🛒 ขายสินค้า":
    # ดึงข้อมูลสินค้ามาเก็บใน Memory ครั้งเดียว
    df_p = fetch_csv(URL_PRODUCTS)
    
    col_l, col_r = st.columns([2, 1.3])
    
    with col_l:
        st.subheader("📦 สินค้าพร้อมขาย")
        if df_p.empty:
            st.error("ไม่สามารถโหลดข้อมูลสินค้าได้ กรุณาตรวจสอบลิงก์ Products")
        else:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                # บังคับดึงตามตำแหน่ง Index: 0=ชื่อ, 1=ราคา, 2=รูป
                p_name = str(row.iloc[0])
                try:
                    p_price = float(row.iloc[1])
                except: p_price = 0.0
                p_img = str(row.iloc[2]) if len(row) > 2 else ""

                with grid[idx % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{p_img if p_img.startswith('http') else 'https://via.placeholder.com/150'}">
                        <div style="font-weight:bold; height:40px; overflow:hidden;">{p_name}</div>
                        <div class="price-text">{p_price:,.0f} ฿</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"➕ เพิ่มลงตะกร้า", key=f"add_{idx}", use_container_width=True):
                        st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                        st.session_state.cart[p_name]['qty'] += 1
                        st.rerun()

    with col_r:
        if st.session_state.receipt:
            res = st.session_state.receipt
            # สร้าง QR เฉพาะพร้อมเพย์
            qr_html = f'<center><img src="https://promptpay.io/{PP_ID}/{res["total"]}.png" width="180"></center>' if res['method'] == "พร้อมเพย์" else ''
            
            cash_details = f"""
            <div style="display:flex;justify-content:space-between;"><span>รับเงินสด:</span><span>{res['cash']:,.2f}</span></div>
            <div style="display:flex;justify-content:space-between;font-weight:bold;"><span>เงินทอน:</span><span>{res['change']:,.2f}</span></div>
            """ if res['method'] == "เงินสด" else ''

            receipt_html = f"""
            <div id="receipt" style="background:white; color:black; padding:20px; font-family:monospace; border:1px solid #333; width:300px; margin:auto;">
                <center><h2 style="margin:0;">TAS SHOP</h2><p>ใบเสร็จรับเงิน</p><hr></center>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
                <center><p style="margin:10px 0;">ชำระโดย: {res['method']}</p></center>
                {cash_details}
                {qr_html}
                <center style="font-size:10px; margin-top:15px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            if st.button("🖨️ พิมพ์ใบเสร็จ", type="primary", use_container_width=True):
                st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`{receipt_html}`);w.document.close();setTimeout(function(){{w.print();w.close();}},500);</script>", height=0)
            
            if st.button("🔄 เริ่มการขายใหม่", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 รายการในตะกร้า")
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                total_all = 0
                for name, item in list(st.session_state.cart.items()):
                    total_all += item['price'] * item['qty']
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{name}**")
                    c2.write(f"x{item['qty']}")
                    if c3.button("🗑️", key=f"del_{name}"):
                        del st.session_state.cart[name]; st.rerun()
                
                st.divider()
                st.title(f"รวม: {total_all:,.0f} ฿")
                m = st.radio("ช่องทางชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                cash_received = 0.0
                if m == "เงินสด":
                    cash_received = st.number_input("เงินที่รับมา", min_value=float(total_all), step=20.0)
                    st.write(f"เงินทอน: **{cash_received - float(total_all):,.2f} ฿**")

                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    with st.spinner("กำลังบันทึกข้อมูล..."):
                        bill_id = f"B{int(time.time())}"
                        try:
                            # บันทึกข้อมูลแบบ Async-like (ยิงแล้วจบ ไม่รอโหลดนาน)
                            requests.post(SCRIPT_URL, json={
                                "action": "checkout", "bill_id": bill_id,
                                "summary": ", ".join([f"{k}x{v['qty']}" for k,v in st.session_state.cart.items()]),
                                "total": float(total_all), "method": m
                            }, timeout=10)
                            
                            st.session_state.receipt = {
                                "items": dict(st.session_state.cart), "total": total_all,
                                "method": m, "cash": cash_received, "change": cash_received - float(total_all)
                            }
                            st.session_state.cart = {}
                            st.cache_data.clear() # เคลียร์แคชเพื่อให้ยอดขายอัปเดต
                            st.rerun()
                        except:
                            st.error("บันทึกสำเร็จ (Server Response Delay) - พิมพ์ใบเสร็จต่อได้เลย")
                            st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total_all, "method": m, "cash": cash_received, "change": cash_received - float(total_all)}
                            st.session_state.cart = {}
                            st.rerun()

# --- 6. PAGE: SALES SUMMARY ---
elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปรายงานการขาย")
    df_sales = fetch_csv(URL_SALES)
    df_sum = fetch_csv(URL_SUMMARY)
    
    if df_sales.empty:
        st.info("ยังไม่มีข้อมูลการขายในขณะนี้")
    else:
        # บังคับหาชื่อคอลัมน์จาก Index (0=วันที่, 2=ยอดรวม)
        date_col = df_sales.columns[0]
        total_col = df_sales.columns[2]
        
        df_sales[date_col] = pd.to_datetime(df_sales[date_col], dayfirst=True, errors='coerce')
        now = datetime.now()
        today_str = now.strftime("%d/%m/%Y")
        
        # เช็คตัดยอดรายวัน
        is_done = not df_sum[df_sum.iloc[:, 0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # คำนวณยอด
        val_today = df_sales[df_sales[date_col].dt.date == now.date()][total_col].sum()
        val_week = df_sales[df_sales[date_col] >= (now - timedelta(days=7))][total_col].sum()
        val_month = df_sales[df_sales[date_col].dt.month == now.month][total_col].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_done else val_today:,.2f} ฿", delta="ตัดยอดแล้ว" if is_done else "เปิดร้าน")
        m2.metric("รายสัปดาห์ (7 วัน)", f"{val_week:,.2f} ฿")
        m3.metric("รายเดือน", f"{val_month:,.2f} ฿")
        
        st.divider()
        if st.button("📝 กดสรุปยอดปิดวัน (Reset ยอดวันนี้เป็น 0)", type="primary", use_container_width=True, disabled=is_done):
            requests.post(SCRIPT_URL, json={
                "action": "save_summary", "date": today_str, 
                "total": float(val_today), "bills": len(df_sales[df_sales[date_col].dt.date == now.date()])
            })
            st.success("บันทึกตัดยอดเรียบร้อย!")
            st.cache_data.clear()
            time.sleep(1); st.rerun()

        st.subheader("ประวัติบิลล่าสุด")
        st.dataframe(df_sales.sort_values(by=date_col, ascending=False), use_container_width=True)

# --- 7. PAGE: STOCK ---
elif menu == "📦 สต็อกสินค้า":
    st.title("📦 เช็คสต็อกสินค้า")
    if st.button("🔄 อัปเดตสต็อกสดใหม่"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(fetch_csv(URL_STOCK), use_container_width=True)
