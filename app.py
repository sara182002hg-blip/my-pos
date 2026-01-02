import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. CONFIGURATION (ลิงก์ข้อมูลตามที่คุณให้มา) ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189"

st.set_page_config(page_title="TAS POS MASTER V14", layout="wide")

# --- 2. CSS & PRINTING ENGINE ---
st.markdown("""
<style>
    /* คุมขนาดรูปสินค้า 1:1 */
    .product-card img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-radius: 10px;
    }
    .main { background-color: #f5f7f9; }
    .stButton>button { border-radius: 10px; font-weight: bold; }
    
    /* ระบบ Print */
    @media print {
        header, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; }
        .print-area { display: block !important; width: 100% !important; border: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA LOADER ---
def load_sheet(url):
    try:
        # ใช้ Cache Busting เพื่อความสดใหม่ของข้อมูล
        res = requests.get(f"{url}&ts={time.time()}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"การดึงข้อมูลผิดพลาด: {e}")
        return pd.DataFrame()

# Initialize Session
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt_data' not in st.session_state: st.session_state.receipt_data = None

# Sidebar
menu = st.sidebar.radio("📋 เลือกเมนู", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 เช็คสต็อก"])

# --- 4. PAGE: ขายสินค้า ---
if menu == "🛒 ขายสินค้า":
    df_p = load_sheet(URL_PRODUCTS)
    df_s = load_sheet(URL_STOCK)
    
    if df_p.empty:
        st.warning("⚠️ ไม่พบข้อมูลสินค้าใน Google Sheets กรุณาตรวจสอบลิงก์ Products")
    else:
        col1, col2 = st.columns([2.2, 1.8])
        
        with col1:
            st.subheader("📦 รายการสินค้า")
            # ใช้ตำแหน่งคอลัมน์แทนชื่อ เพื่อป้องกันชื่อเปลี่ยน
            # สมมติลำดับ: 0=ชื่อ, 1=ราคา, 2=รูป
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                try:
                    p_name = str(row.iloc[0])
                    p_price = float(row.iloc[1])
                    p_img = str(row.iloc[2]) if len(row) > 2 else ""
                    
                    with grid[i % 3]:
                        with st.container(border=True):
                            if p_img.startswith("http"):
                                st.markdown(f'<div class="product-card"><img src="{p_img}"></div>', unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="height:180px; background:#ddd; border-radius:10px; display:flex; align-items:center; justify-content:center;">📷 ไม่มีรูป</div>', unsafe_allow_html=True)
                            
                            st.write(f"**{p_name}**")
                            st.write(f"### {p_price:,.0f} ฿")
                            
                            if st.button(f"🛒 เพิ่มสินค้า", key=f"p_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                except: continue

        with col2:
            if st.session_state.receipt_data:
                res = st.session_state.receipt_data
                qr_code = f"https://promptpay.io/{MY_PROMPTPAY}/{res['total']}.png"
                
                receipt_html = f"""
                <div id="receipt" style="background:white; color:black; padding:20px; border:2px solid #333; font-family:monospace; border-radius:5px; width:320px; margin:auto;">
                    <center><h2 style="margin:0;">TAS POS</h2><p>ใบเสร็จรับเงิน</p><hr></center>
                    {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                    <hr>
                    <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:18px;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
                    <p style="text-align:center;">ชำระโดย: {res['method']}</p>
                    {f'<div style="display:flex;justify-content:space-between;"><span>รับเงิน:</span><span>{res["cash"]:,.2f}</span></div><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>เงินทอน:</span><span>{res["change"]:,.2f}</span></div>' if res['method']=='เงินสด' else ''}
                    {f'<center><img src="{qr_code}" width="180"></center>' if res['method']=='พร้อมเพย์' else ''}
                    <center style="font-size:10px; margin-top:10px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</center>
                </div>
                """
                st.markdown(receipt_html, unsafe_allow_html=True)
                
                if st.button("🖨️ สั่งพิมพ์ใบเสร็จ", type="primary", use_container_width=True):
                    st.components.v1.html(f"<script>var prtContent = `{receipt_html}`; var WinPrint = window.open('', '', 'width=400,height=600'); WinPrint.document.write(prtContent); WinPrint.document.close(); WinPrint.focus(); WinPrint.print(); WinPrint.close();</script>", height=0)
                
                if st.button("🔄 เริ่มการขายใหม่", use_container_width=True):
                    st.session_state.receipt_data = None
                    st.rerun()
            
            else:
                st.subheader("🛒 ตะกร้าสินค้า")
                if not st.session_state.cart:
                    st.info("ยังไม่มีสินค้าในตะกร้า")
                else:
                    total = 0
                    for n, v in list(st.session_state.cart.items()):
                        total += v['price'] * v['qty']
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{n}**")
                        c2.write(f"x{v['qty']}")
                        if c3.button("🗑️", key=f"del_{n}"):
                            del st.session_state.cart[n]; st.rerun()
                    
                    st.divider()
                    st.title(f"รวม: {total:,.0f} ฿")
                    m = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                    
                    cash_received = 0
                    if m == "เงินสด":
                        cash_received = st.number_input("เงินที่รับมา", min_value=float(total), step=10.0)
                        st.write(f"เงินทอน: **{cash_received - float(total):,.2f} ฿**")

                    if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                        try:
                            payload = {"action": "checkout", "bill_id": f"B{int(time.time())}", "summary": str(st.session_state.cart), "total": total, "method": m}
                            requests.post(SCRIPT_URL, json=payload, timeout=5)
                            st.session_state.receipt_data = {"items": dict(st.session_state.cart), "total": total, "method": m, "cash": cash_received, "change": cash_received - float(total)}
                            st.session_state.cart = {}
                            st.rerun()
                        except: st.error("บันทึกไม่สำเร็จ แต่คุณสามารถพิมพ์ใบเสร็จได้")

# --- 5. PAGE: รายงานยอดขาย ---
elif menu == "📊 รายงานยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_s = load_sheet(URL_SALES)
    df_sum = load_sheet(URL_SUMMARY)
    
    if df_s.empty:
        st.info("ยังไม่มีประวัติการขาย")
    else:
        # กำหนดชื่อคอลัมน์สำหรับประมวลผล (อิงตำแหน่ง 0=วันที่, 2=ยอดรวม)
        df_s.iloc[:, 0] = pd.to_datetime(df_s.iloc[:, 0], dayfirst=True, errors='coerce')
        val_col = df_s.columns[2] # สมมติยอดรวมอยู่คอลัมน์ที่ 3
        date_col = df_s.columns[0]

        now = datetime.now()
        today_str = now.strftime("%d/%m/%Y")
        
        # ตรวจสอบว่าวันนี้ตัดยอดไปหรือยัง
        is_cut = not df_sum[df_sum.iloc[:, 0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # คำนวณ Metrics
        sales_today = df_s[df_s[date_col].dt.date == now.date()][val_col].sum()
        sales_weekly = df_s[df_s[date_col] >= (now - timedelta(days=7))][val_col].sum()
        sales_monthly = df_s[df_s[date_col].dt.month == now.month][val_col].sum()
        
        m1, m2, m3 = st.columns(3)
        # ยอดวันนี้จะเป็น 0 ทันทีถ้าตัดยอดไปแล้ว
        m1.metric("ยอดขายวันนี้", f"{0 if is_cut else sales_today:,.0f} ฿", delta="ตัดยอดแล้ว" if is_cut else "เปิดร้านอยู่")
        m2.metric("ยอดขาย 7 วันที่ผ่านมา", f"{sales_weekly:,.0f} ฿")
        m3.metric("ยอดขายเดือนนี้", f"{sales_monthly:,.0f} ฿")
        
        st.divider()
        if st.button("📝 บันทึกสรุปยอดรายวัน (Reset ยอดวันนี้)", type="primary", disabled=is_cut):
            try:
                requests.post(SCRIPT_URL, json={"action": "save_summary", "date": today_str, "total": float(sales_today), "bills": len(df_s[df_s[date_col].dt.date == now.date()])}, timeout=10)
                st.success("ตัดยอดสำเร็จ!")
                time.sleep(1); st.rerun()
            except: st.error("ล้มเหลว")

        st.subheader("📋 ประวัติการขายทั้งหมด")
        st.dataframe(df_s.sort_values(by=date_col, ascending=False), use_container_width=True)

# --- 6. PAGE: สต็อก ---
elif menu == "📦 เช็คสต็อก":
    st.title("📦 ข้อมูลสต็อกสินค้า")
    st.dataframe(load_sheet(URL_STOCK), use_container_width=True)
