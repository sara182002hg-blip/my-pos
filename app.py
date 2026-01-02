import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล (คงเดิม) ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Stable V10", layout="wide")

# CSS บังคับรูปเท่ากัน
st.markdown("""<style>
    [data-testid="stImage"] img { height: 180px; object-fit: contain; background: #f9f9f9; border-radius: 5px; }
    @media print { .no-print { display: none !important; } }
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=120)
def fetch_data(url):
    try:
        res = requests.get(f"{url}&cache_bus={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except: return pd.DataFrame()

def get_col(df, names):
    for c in df.columns:
        if any(n.lower() in c.lower() for n in names): return c
    return df.columns[0] if not df.empty else None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = fetch_data(URL_PRODUCTS)
    df_s = fetch_data(URL_STOCK)
    col_main, col_right = st.columns([2.2, 1.8])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            c_name = get_col(df_p, ["สินค้า", "name"])
            c_price = get_col(df_p, ["ราคา", "price"])
            c_img = get_col(df_p, ["รูป", "image", "url"])
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name, p_price = str(row[c_name]), float(row[c_price])
                p_img = str(row[c_img]) if c_img and pd.notna(row[c_img]) else ""
                s_match = df_s[df_s.iloc[:,0] == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0,1]) if not s_match.empty else 0
                with grid[i % 3]:
                    with st.container(border=True):
                        st.image(p_img if p_img.startswith("http") else "https://via.placeholder.com/150", use_container_width=True)
                        st.write(f"**{p_name}**\n\n### {p_price:,.0f} ฿")
                        if stock > st.session_state.cart.get(p_name, {}).get('qty', 0):
                            if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else: st.button("❌ หมด", disabled=True, use_container_width=True)

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            qr_html = f'<div style="text-align:center;"><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" width="180"></div>' if r['method'] == "📱 PromptPay" else ""
            receipt_html = f"""<div style="background:white; color:black; padding:20px; border:2px solid #333; font-family:monospace; border-radius:5px;">
                <h3 style="text-align:center;">TAS POS RECEIPT</h3><hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวมสุทธิ</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="text-align:center; margin-top:10px;">ชำระโดย: {r['method']}</p>{qr_html}</div>"""
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            # ปุ่มพิมพ์ที่ปรับปรุงใหม่
            if st.button("🖨️ พิมพ์ใบเสร็จ", use_container_width=True):
                st.components.v1.html(f"<script>var prtContent = '{receipt_html}'; var WinPrint = window.open('', '', 'left=0,top=0,width=800,height=900,toolbar=0,scrollbars=0,status=0'); WinPrint.document.write(prtContent); WinPrint.document.close(); WinPrint.focus(); WinPrint.print(); WinPrint.close();</script>", height=0)

            if st.button("🔄 เริ่มการขายใหม่", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = sum(i['price'] * i['qty'] for i in st.session_state.cart.values())
            for n, i in list(st.session_state.cart.items()):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{n}** x{i['qty']}")
                if c2.button("🗑️", key=f"del_{n}"): del st.session_state.cart[n]; st.rerun()
            if total > 0:
                method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    try: requests.post(SCRIPT_URL, json={"action":"checkout","bill_id":f"B{int(time.time())}","summary":", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()]),"total":total,"method":method}, timeout=1)
                    except: pass
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                    st.session_state.cart = {}
                    st.cache_data.clear() # ล้าง Cache ทันทีเพื่อให้รายงานยอดขายอัปเดต
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = fetch_data(URL_SALES)
    df_sum = fetch_data(URL_SUMMARY)
    if not df_sales.empty:
        c_date = get_col(df_sales, ["วัน", "time", "date"])
        c_total = get_col(df_sales, ["ยอด", "total", "รวม"])
        
        # ปรับ Logic การกรองวันที่ให้แม่นยำขึ้น
        df_sales[c_date] = pd.to_datetime(df_sales[c_date], dayfirst=True, errors='coerce')
        now_date = datetime.now().date()
        df_today = df_sales[df_sales[c_date].dt.date == now_date]
        
        today_str = datetime.now().strftime("%d/%m/%Y")
        is_cut = not df_sum[df_sum.iloc[:, 0] == today_str].empty if not df_sum.empty else False
        
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_cut else df_today[c_total].sum():,.0f} ฿")
        m2.metric("รายสัปดาห์", f"{df_sales[df_sales[c_date] >= (datetime.now() - timedelta(days=7))][c_total].sum():,.0f} ฿")
        m3.metric("รายเดือน", f"{df_sales[df_sales[c_date].dt.month == datetime.now().month][c_total].sum():,.0f} ฿")
        
        if st.button("📝 บันทึกสรุปยอดรายวัน", type="primary", disabled=is_cut):
            try:
                requests.post(SCRIPT_URL, json={"action":"save_summary","date":today_str,"total":float(df_today[c_total].sum()),"bills":int(len(df_today))}, timeout=5)
                st.success("บันทึกสำเร็จ!")
                st.cache_data.clear()
                time.sleep(1); st.rerun()
            except: st.error("บันทึกไม่สำเร็จ")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 เช็คสต็อกสินค้า")
    st.dataframe(fetch_data(URL_STOCK), use_container_width=True)
