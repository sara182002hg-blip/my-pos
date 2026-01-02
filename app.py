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
MY_PROMPTPAY = "0945016189"

st.set_page_config(page_title="TAS POS TURBO V15", layout="wide")

# --- 2. FAST CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .product-box img { width: 100%; height: 160px; object-fit: cover; border-radius: 12px; margin-bottom: 8px; }
    .stButton>button { border-radius: 8px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    [data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; color: #1e88e5; }
</style>
""", unsafe_allow_html=True)

# --- 3. HIGH PERFORMANCE DATA ENGINE ---
@st.cache_data(ttl=30) # Cache 30 seconds to speed up UI
def fetch_data(url):
    try:
        r = requests.get(f"{url}&nocache={time.time()}", timeout=10)
        r.encoding = 'utf-8'
        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

def get_col_name(df, hints):
    for h in hints:
        for c in df.columns:
            if h.lower() in c.lower(): return c
    return df.columns[0] if not df.empty else None

# Session States
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# Sidebar
st.sidebar.title("🚀 TAS POS Turbo")
page = st.sidebar.radio("เมนูหลัก", ["🛒 ระบบขายสินค้า", "📊 รายงานยอดขาย", "📦 เช็คสต็อก"])

# --- 4. PAGE: POS SYSTEM ---
if page == "🛒 ระบบขายสินค้า":
    df_p = fetch_data(URL_PRODUCTS)
    df_s = fetch_data(URL_STOCK)
    
    c_l, c_r = st.columns([2.2, 1.8])
    
    with c_l:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ดึงสต็อกมาทำ Dict เพื่อความไวสูงสุด
            s_name_col = get_col_name(df_s, ["สินค้า", "item"])
            s_qty_col = get_col_name(df_s, ["คงเหลือ", "stock", "qty"])
            stock_dict = pd.Series(df_s[s_qty_col].values, index=df_s[s_name_col].astype(str).str.strip()).to_dict()

            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                name = str(row.iloc[0]).strip()
                price = float(row.iloc[1])
                img = str(row.iloc[2]) if len(row) > 2 else ""
                
                # คำนวณสต็อกที่เหลือจริงๆ (สต็อกในชีต - ในตะกร้า)
                current_stock = int(stock_dict.get(name, 0)) - st.session_state.cart.get(name, {}).get('qty', 0)
                
                with grid[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f'<div class="product-box"><img src="{img if img.startswith("http") else ""}"></div>', unsafe_allow_html=True)
                        st.write(f"**{name}**")
                        st.write(f"### {price:,.0f} ฿")
                        
                        if current_stock > 0:
                            if st.button(f"🛒 เพิ่ม", key=f"add_{idx}", use_container_width=True):
                                st.session_state.cart[name] = st.session_state.cart.get(name, {'price': price, 'qty': 0})
                                st.session_state.cart[name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ หมด", disabled=True, use_container_width=True)

    with c_r:
        if st.session_state.receipt:
            r = st.session_state.receipt
            qr = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
            
            # Template ใบเสร็จ
            receipt_html = f"""
            <div id="p" style="background:white; color:black; padding:20px; border:1px solid #000; font-family:monospace; border-radius:10px; width:300px; margin:auto;">
                <center><h2 style="margin:0;">TAS POS</h2><small>ใบเสร็จรับเงิน</small></center><hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in r['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-weight:bold;font-size:18px;"><span>รวมสุทธิ</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="text-align:center;">ชำระโดย: {r['method']}</p>
                {f'<div style="display:flex;justify-content:space-between;"><span>รับเงิน:</span><span>{r["cash"]:,.2f}</span></div><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>เงินทอน:</span><span>{r["change"]:,.2f}</span></div>' if r['method']=='เงินสด' else ''}
                {f'<center><img src="{qr}" width="160"></center>' if r['method']=='พร้อมเพย์' else ''}
                <center style="font-size:10px;margin-top:10px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            if st.button("🖨️ พิมพ์ใบเสร็จ", type="primary", use_container_width=True):
                st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`{receipt_html}`);w.document.close();setTimeout(function(){{w.print();w.close();}},500);</script>", height=0)
            
            if st.button("🔄 ขายรายการถัดไป", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart:
                st.info("ว่างเปล่า")
            else:
                total_all = 0
                for n, v in list(st.session_state.cart.items()):
                    sub = v['price'] * v['qty']
                    total_all += sub
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{v['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]; st.rerun()
                
                st.divider()
                st.title(f"ยอดรวม: {total_all:,.0f} ฿")
                m = st.radio("การชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                cash_in = 0.0
                if m == "เงินสด":
                    cash_in = st.number_input("เงินที่รับมา", min_value=float(total_all), step=20.0)
                    st.write(f"เงินทอน: **{cash_in - float(total_all):,.2f} ฿**")

                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    try:
                        p = {"action": "checkout", "bill_id": f"B{int(time.time())}", "summary": str(st.session_state.cart), "total": total_all, "method": m}
                        requests.post(SCRIPT_URL, json=p, timeout=5)
                        st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total_all, "method": m, "cash": cash_in, "change": cash_in - float(total_all)}
                        st.session_state.cart = {}
                        st.cache_data.clear() # ล้างแคชเพื่อให้รายงานอัปเดตทันที
                        st.rerun()
                    except: st.error("บันทึกไม่สำเร็จ แต่คุณพิมพ์ใบเสร็จได้")

# --- 5. PAGE: SALES REPORT (FIXED & ACCURATE) ---
elif page == "📊 รายงานยอดขาย":
    st.title("📊 รายงานสรุปยอดขาย")
    df_sales = fetch_data(URL_SALES)
    df_sum = fetch_data(URL_SUMMARY)
    
    if not df_sales.empty:
        # เตรียมข้อมูลวันที่
        date_col = df_sales.columns[0]
        val_col = get_col_name(df_sales, ["ยอด", "total", "รวม"])
        df_sales[date_col] = pd.to_datetime(df_sales[date_col], dayfirst=True, errors='coerce')
        
        now = datetime.now()
        today_date = now.date()
        today_str = now.strftime("%d/%m/%Y")
        
        # 1. เช็คว่าตัดยอดวันนี้ไปหรือยัง
        is_cut = not df_sum[df_sum.iloc[:, 0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # 2. คำนวณยอดต่างๆ
        # วันนี้
        sales_today = df_sales[df_sales[date_col].dt.date == today_date][val_col].sum()
        # สัปดาห์นี้ (7 วันย้อนหลัง)
        sales_weekly = df_sales[df_sales[date_col] >= (now - timedelta(days=7))][val_col].sum()
        # เดือนนี้
        sales_monthly = df_sales[df_sales[date_col].dt.month == now.month][val_col].sum()

        m1, m2, m3 = st.columns(3)
        # ถ้ายอดวันนี้โดนตัดไปแล้ว จะแสดงเป็น 0 ตามหลักบัญชี POS
        m1.metric("ยอดขายวันนี้", f"{0 if is_cut else sales_today:,.2f} ฿", delta="ตัดยอดแล้ว" if is_cut else "เปิดยอด")
        m2.metric("รายสัปดาห์ (7 วัน)", f"{sales_weekly:,.2f} ฿")
        m3.metric("รายเดือนนี้", f"{sales_monthly:,.2f} ฿")
        
        st.divider()
        if st.button("📝 บันทึกสรุปยอดปิดวัน (Reset ยอดวันนี้)", type="primary", use_container_width=True, disabled=is_cut):
            try:
                requests.post(SCRIPT_URL, json={
                    "action": "save_summary", "date": today_str, 
                    "total": float(sales_today), "bills": len(df_sales[df_sales[date_col].dt.date == today_date])
                }, timeout=10)
                st.success("ตัดยอดสำเร็จ!")
                st.cache_data.clear()
                time.sleep(1); st.rerun()
            except: st.error("เกิดข้อผิดพลาดในการบันทึก")

        st.subheader("📋 ประวัติรายการล่าสุด")
        st.dataframe(df_sales.sort_values(by=date_col, ascending=False), use_container_width=True)

# --- 6. PAGE: STOCK ---
elif page == "📦 เช็คสต็อก":
    st.title("📦 ตรวจสอบสต็อกสินค้า")
    st.dataframe(fetch_data(URL_STOCK), use_container_width=True, height=500)
    if st.button("🔄 อัปเดตข้อมูลเดี๋ยวนี้"):
        st.cache_data.clear()
        st.rerun()
