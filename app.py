import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V16", layout="wide")

# --- 2. CSS FOR UNIFORMITY & PERFORMANCE ---
st.markdown("""
<style>
    .product-container {
        text-align: center;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background: white;
    }
    .product-img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 5px;
    }
    .stMetric { background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; }
    @media print { .no-print { display: none !important; } }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE (NO CACHE FOR STABILITY) ---
def get_data(url):
    try:
        # ดึงข้อมูลสดใหม่เสมอ ป้องกันปัญหาข้อมูลเก่าค้าง
        r = requests.get(f"{url}&ts={time.time()}", timeout=10)
        r.encoding = 'utf-8'
        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# Initialize Session States
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt_show' not in st.session_state: st.session_state.receipt_show = None

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.title("🏪 TAS POS System")
menu = st.sidebar.selectbox("เลือกหน้าการทำงาน", ["🛒 หน้าขายสินค้า", "📊 สรุปยอดขาย", "📦 สต็อกสินค้า"])

# --- 5. PAGE: POS SYSTEM ---
if menu == "🛒 หน้าขายสินค้า":
    df_p = get_data(URL_PRODUCTS)
    df_s = get_data(URL_STOCK)
    
    col_l, col_r = st.columns([2, 1.5])
    
    with col_l:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ใช้ Column Index เพื่อความชัวร์ (0=ชื่อ, 1=ราคา, 2=รูป)
            cols = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0])
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                
                with cols[idx % 3]:
                    st.markdown(f'''<div class="product-container">
                        <img src="{p_img}" class="product-img">
                        <p><b>{p_name}</b></p>
                        <h3 style="margin:0;">{p_price:,.0f} ฿</h3>
                    </div>''', unsafe_allow_html=True)
                    
                    if st.button(f"🛒 เพิ่มสินค้า", key=f"add_{idx}", use_container_width=True):
                        st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                        st.session_state.cart[p_name]['qty'] += 1
                        st.rerun()

    with col_r:
        if st.session_state.receipt_show:
            res = st.session_state.receipt_show
            qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{res['total']}.png"
            
            receipt_html = f"""
            <div id="receipt" style="background:white; color:black; padding:20px; font-family:monospace; border:1px solid #333; width:300px; margin:auto;">
                <center><h2>TAS POS</h2><p>ใบเสร็จรับเงิน</p><hr></center>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                <hr>
                <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:18px;"><span>รวมสุทธิ</span><span>{res['total']:,.0f} ฿</span></div>
                <p style="text-align:center;">วิธีชำระ: {res['method']}</p>
                {f'<div style="display:flex;justify-content:space-between;"><span>รับเงิน:</span><span>{res.get("received",0):,.2f}</span></div><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>เงินทอน:</span><span>{res.get("change",0):,.2f}</span></div>' if res['method'] == "เงินสด" else ""}
                {f'<center><img src="{qr_url}" width="160"></center>' if res['method'] == "พร้อมเพย์" else ""}
                <center style="font-size:10px; margin-top:10px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            if st.button("🖨️ สั่งพิมพ์ใบเสร็จ (Print)", type="primary", use_container_width=True):
                st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`{receipt_html}`);w.document.close();setTimeout(function(){{w.print();w.close();}},500);</script>", height=0)
            
            if st.button("🔄 เริ่มการขายใหม่", use_container_width=True):
                st.session_state.receipt_show = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้า")
            else:
                total_val = 0
                for n, v in list(st.session_state.cart.items()):
                    total_val += v['price'] * v['qty']
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{v['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]; st.rerun()
                
                st.divider()
                st.title(f"ยอดรวม: {total_val:,.0f} ฿")
                pay_m = st.radio("เลือกการชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                received = 0.0
                if pay_m == "เงินสด":
                    received = st.number_input("ยอดเงินที่รับมา", min_value=float(total_val), step=20.0)
                    st.write(f"เงินทอน: **{received - float(total_val):,.2f} ฿**")

                if st.button("🚀 ยืนยันการสั่งซื้อ", type="primary", use_container_width=True):
                    try:
                        requests.post(SCRIPT_URL, json={
                            "action": "checkout", "bill_id": f"B{int(time.time())}",
                            "summary": ", ".join([f"{k}x{v['qty']}" for k,v in st.session_state.cart.items()]),
                            "total": total_val, "method": pay_m
                        }, timeout=5)
                        st.session_state.receipt_show = {
                            "items": dict(st.session_state.cart), "total": total_val, 
                            "method": pay_m, "received": received, "change": received - float(total_val)
                        }
                        st.session_state.cart = {}
                        st.rerun()
                    except: st.error("บันทึกผิดพลาด แต่พิมพ์ใบเสร็จได้")

# --- 6. PAGE: SALES REPORT (ULTRA ACCURATE) ---
elif menu == "📊 สรุปยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = get_data(URL_SALES)
    df_sum = get_data(URL_SUMMARY)
    
    if not df_sales.empty:
        # แปลงวันที่ให้เป็น Format เดียวกัน (Day/Month/Year)
        date_col = df_sales.columns[0]
        val_col = df_sales.columns[2]
        df_sales[date_col] = pd.to_datetime(df_sales[date_col], dayfirst=True, errors='coerce')
        
        now = datetime.now()
        today_date = now.date()
        today_str = now.strftime("%d/%m/%Y")
        
        # ตรวจสอบว่าวันนี้กดสรุปยอดไปแล้วหรือยัง
        is_done = not df_sum[df_sum.iloc[:,0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # คำนวณยอด
        today_total = df_sales[df_sales[date_col].dt.date == today_date][val_col].sum()
        week_total = df_sales[df_sales[date_col] >= (now - timedelta(days=7))][val_col].sum()
        month_total = df_sales[df_sales[date_col].dt.month == now.month][val_col].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_done else today_total:,.2f} ฿", delta="ตัดยอดแล้ว" if is_done else "เปิดร้าน")
        m2.metric("สรุปยอด 7 วัน", f"{week_total:,.2f} ฿")
        m3.metric("สรุปยอดเดือนนี้", f"{month_total:,.2f} ฿")
        
        st.divider()
        if st.button("📝 บันทึกสรุปยอดปิดวัน (Reset ยอดวันนี้)", type="primary", use_container_width=True, disabled=is_done):
            try:
                requests.post(SCRIPT_URL, json={
                    "action": "save_summary", "date": today_str, 
                    "total": float(today_total), "bills": len(df_sales[df_sales[date_col].dt.date == today_date])
                }, timeout=10)
                st.success("บันทึกสำเร็จ!")
                time.sleep(1); st.rerun()
            except: st.error("บันทึกไม่สำเร็จ")

        st.subheader("ประวัติการขายล่าสุด")
        st.dataframe(df_sales.sort_values(by=date_col, ascending=False), use_container_width=True)

# --- 7. PAGE: STOCK ---
elif menu == "📦 สต็อกสินค้า":
    st.title("📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(get_data(URL_STOCK), use_container_width=True)
