import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. SETTINGS & LINKS ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PP_ID = "0945016189"

st.set_page_config(page_title="TAS POS PREMIUM V20", layout="wide")

# --- 2. PREMIUM BLACK CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .product-card {
        background: #1C2128; padding: 15px; border-radius: 12px;
        border: 1px solid #30363D; text-align: center; margin-bottom: 10px;
    }
    .product-card img { width: 100%; height: 160px; object-fit: cover; border-radius: 8px; }
    .price-tag { color: #D4AF37; font-size: 22px; font-weight: bold; margin: 10px 0; }
    .stButton>button {
        background-color: #D4AF37; color: #000; border-radius: 8px; font-weight: bold; border: none;
    }
    .stMetric { background-color: #1C2128 !important; border: 1px solid #30363D !important; border-radius: 12px !important; padding: 15px !important; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. POWERFUL DATA ENGINE ---
def load_live_data(url):
    try:
        r = requests.get(f"{url}&ts={time.time()}", timeout=10)
        r.encoding = 'utf-8'
        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'checkout_done' not in st.session_state: st.session_state.checkout_done = None

# --- 4. NAVIGATION ---
menu = st.sidebar.radio("📋 เมนูระบบ", ["🛒 ขายสินค้า", "📊 สรุปรายงานยอดขาย", "📦 คลังสต็อก"])

# --- 5. PAGE: POS SYSTEM ---
if menu == "🛒 ขายสินค้า":
    df_p = load_live_data(URL_PRODUCTS)
    col1, col2 = st.columns([2, 1.2])

    with col1:
        st.markdown("<h2 style='color:#D4AF37;'>🛒 เลือกรายการสินค้า</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row.iloc[0])
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                
                with grid[i % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{p_img}">
                        <div style="font-weight:bold; margin-top:10px;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"➕ เพิ่ม {p_name}", key=f"p_{i}", use_container_width=True):
                        st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                        st.session_state.cart[p_name]['qty'] += 1
                        st.rerun()

    with col2:
        if st.session_state.checkout_done:
            res = st.session_state.checkout_done
            qr_link = f"https://promptpay.io/{PP_ID}/{res['total']}.png"
            receipt_html = f"""
            <div style="background:white; color:black; padding:20px; font-family:monospace; border-radius:10px; width:280px; margin:auto; border:1px solid #000;">
                <center><h3>TAS PREMIUM POS</h3><hr></center>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-weight:bold;font-size:18px;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
                <center><p>ชำระโดย: {res['method']}</p></center>
                {f'<div style="display:flex;justify-content:space-between;"><span>รับเงิน:</span><span>{res["cash"]:,.0f}</span></div><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>เงินทอน:</span><span>{res["change"]:,.0f}</span></div>' if res['method'] == "เงินสด" else ""}
                {f'<center><img src="{qr_link}" width="160"></center>' if res['method'] == "พร้อมเพย์" else ""}
                <hr><center><small>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small></center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            if st.button("🖨️ พิมพ์ใบเสร็จ", use_container_width=True):
                st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`{receipt_html}`);w.document.close();w.print();w.close();</script>", height=0)
            if st.button("🔄 เริ่มการขายใหม่", use_container_width=True):
                st.session_state.checkout_done = None; st.rerun()
        else:
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้าสินค้า</h3>", unsafe_allow_html=True)
            if not st.session_state.cart: st.info("ไม่มีสินค้าในตะกร้า")
            else:
                total_all = 0
                for k, v in list(st.session_state.cart.items()):
                    total_all += v['price'] * v['qty']
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(k); c2.write(f"x{v['qty']}")
                    if c3.button("🗑️", key=f"del_{k}"): del st.session_state.cart[k]; st.rerun()
                
                st.divider()
                st.markdown(f"## รวม: <span style='color:#D4AF37;'>{total_all:,.0f} ฿</span>", unsafe_allow_html=True)
                pay_mode = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                cash_received = 0
                if pay_mode == "เงินสด":
                    cash_received = st.number_input("เงินที่รับมา", min_value=float(total_all))
                
                if st.button("✅ ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                    try:
                        requests.post(SCRIPT_URL, json={
                            "action": "checkout", "total": total_all, "method": pay_mode,
                            "summary": str(st.session_state.cart)
                        }, timeout=5)
                    except: pass # ป้องกัน UI ค้างถ้าเน็ตช้าแต่ข้อมูลส่งไปแล้ว
                    st.session_state.checkout_done = {
                        "items": dict(st.session_state.cart), "total": total_all,
                        "method": pay_mode, "cash": cash_received, "change": cash_received - total_all
                    }
                    st.session_state.cart = {}; st.rerun()

# --- 6. PAGE: REPORTS (FIXED ALL) ---
elif menu == "📊 สรุปรายงานยอดขาย":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ข้อมูลการขาย</h2>", unsafe_allow_html=True)
    df_sales = load_live_data(URL_SALES)
    df_sum = load_live_data(URL_SUMMARY)

    if not df_sales.empty:
        # ล้างข้อมูลวันที่ให้ชัวร์
        df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
        val_col = df_sales.columns[2]
        date_col = df_sales.columns[0]
        
        today = datetime.now().date()
        today_str = datetime.now().strftime("%d/%m/%Y")
        
        # ตรวจสอบการตัดยอด
        is_closed = not df_sum[df_sum.iloc[:, 0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # คำนวณรายได้
        today_total = df_sales[df_sales[date_col].dt.date == today][val_col].sum()
        week_total = df_sales[df_sales[date_col] >= (datetime.now() - timedelta(days=7))][val_col].sum()
        month_total = df_sales[df_sales[date_col].dt.month == today.month][val_col].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_closed else today_total:,.0f} ฿", delta="ตัดยอดแล้ว" if is_closed else "ปกติ")
        m2.metric("สรุป 7 วันล่าสุด", f"{week_total:,.0f} ฿")
        m3.metric("สรุปเดือนนี้", f"{month_total:,.0f} ฿")
        
        st.divider()
        if st.button("📝 กดปิดยอดรายวัน (Reset ยอดวันนี้)", type="primary", use_container_width=True, disabled=is_closed):
            requests.post(SCRIPT_URL, json={"action": "save_summary", "date": today_str, "total": float(today_total)})
            st.success("บันทึกสรุปยอดสำเร็จ!"); time.sleep(1); st.rerun()

        st.subheader("📋 ประวัติบิลล่าสุด")
        st.dataframe(df_sales.sort_values(by=date_col, ascending=False), use_container_width=True)

# --- 7. PAGE: STOCK ---
elif menu == "📦 คลังสต็อก":
    st.markdown("<h2 style='color:#D4AF37;'>📦 ตรวจสอบสต็อก</h2>", unsafe_allow_html=True)
    if st.button("🔄 อัปเดตข้อมูลล่าสุด"): st.rerun()
    st.dataframe(load_live_data(URL_STOCK), use_container_width=True)
