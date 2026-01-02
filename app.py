import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px
from io import StringIO
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PP_ID = "0945016189"

st.set_page_config(page_title="TAS POS PREMIUM", layout="wide")

# --- 2. PREMIUM DARK CSS ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Product Cards */
    .product-card {
        background: #1C1F26;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #30363D;
        text-align: center;
        transition: 0.3s;
    }
    .product-card:hover { border-color: #D4AF37; transform: translateY(-5px); }
    .product-card img { width: 100%; height: 160px; object-fit: cover; border-radius: 10px; margin-bottom: 10px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* Buttons */
    .stButton>button {
        background-color: #D4AF37; color: black; border-radius: 8px;
        font-weight: bold; border: none; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #FAFAD2; color: black; box-shadow: 0 4px 15px rgba(212,175,55,0.4); }
    
    /* Metrics */
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    div[data-testid="metric-container"] {
        background-color: #1C1F26; padding: 20px; border-radius: 15px; border: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CORE FUNCTIONS ---
def fetch_data(url):
    try:
        r = requests.get(f"{url}&ts={time.time()}", timeout=10)
        r.encoding = 'utf-8'
        return pd.read_csv(StringIO(r.text)).dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'order_finish' not in st.session_state: st.session_state.order_finish = None

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37;'>TAS PREMIUM</h1>", unsafe_allow_html=True)
    menu = st.radio("เมนูหลัก", ["🛒 ระบบขายสินค้า", "📊 วิเคราะห์ยอดขาย", "📦 จัดการสต็อก"], label_visibility="collapsed")
    st.divider()
    if st.button("🔄 ล้างข้อมูลแคช"):
        st.cache_data.clear()
        st.rerun()

# --- 5. PAGE: POS SYSTEM ---
if menu == "🛒 ระบบขายสินค้า":
    df_p = fetch_data(URL_PRODUCTS)
    col_l, col_r = st.columns([2.2, 1.3])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>รายการสินค้า</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name, p_price = str(row.iloc[0]), float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                with grid[i % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                        <img src="{p_img}">
                        <div style="font-weight:bold; font-size:18px;">{p_name}</div>
                        <div style="color:#D4AF37; font-size:22px; margin:5px 0;">{p_price:,.0f} ฿</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"เพิ่ม {p_name}", key=f"add_{i}"):
                        st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                        st.session_state.cart[p_name]['qty'] += 1
                        st.rerun()

    with col_r:
        if st.session_state.order_finish:
            res = st.session_state.order_finish
            qr = f"https://promptpay.io/{PP_ID}/{res['total']}.png"
            receipt_html = f"""
            <div id="print_area" style="background:white; color:black; padding:25px; font-family:monospace; border-radius:10px; width:300px; margin:auto;">
                <center><h2 style="margin:0;">TAS PREMIUM</h2><p>Receipt / ใบเสร็จ</p><hr style="border-top:1px dashed #000"></center>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                <hr style="border-top:1px dashed #000">
                <div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
                <center><p style="margin:10px 0;">ชำระโดย: {res['method']}</p></center>
                {f'<div style="display:flex;justify-content:space-between;"><span>รับเงิน:</span><span>{res["cash"]:,.2f}</span></div><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>เงินทอน:</span><span>{res["change"]:,.2f}</span></div>' if res['method'] == "เงินสด" else ""}
                {f'<center><img src="{qr}" width="180"></center>' if res['method'] == "พร้อมเพย์" else ""}
                <center style="font-size:10px;margin-top:15px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>ขอบคุณที่ใช้บริการ</center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            if st.button("🖨️ สั่งพิมพ์ใบเสร็จ"):
                st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`{receipt_html}`);w.document.close();setTimeout(function(){{w.print();w.close();}},500);</script>", height=0)
            if st.button("🔄 ขายต่อ"):
                st.session_state.order_finish = None; st.rerun()
        else:
            st.markdown("<h3 style='color:#D4AF37;'>ตะกร้าสินค้า</h3>", unsafe_allow_html=True)
            if not st.session_state.cart: st.info("ยังไม่มีสินค้า")
            else:
                total_all = 0
                for k, v in list(st.session_state.cart.items()):
                    total_all += v['price'] * v['qty']
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(k)
                    c2.write(f"x{v['qty']}")
                    if c3.button("🗑️", key=f"del_{k}"): del st.session_state.cart[k]; st.rerun()
                st.divider()
                st.markdown(f"## รวม: <span style='color:#D4AF37;'>{total_all:,.0f} ฿</span>", unsafe_allow_html=True)
                m = st.selectbox("ช่องทางชำระเงิน", ["เงินสด", "พร้อมเพย์"])
                cash_in = 0.0
                if m == "เงินสด":
                    cash_in = st.number_input("เงินที่รับมา", min_value=float(total_all))
                
                if st.button("🚀 ยืนยันชำระเงิน"):
                    requests.post(SCRIPT_URL, json={
                        "action": "checkout", "bill_id": f"B{int(time.time())}",
                        "summary": str(st.session_state.cart), "total": total_all, "method": m
                    })
                    st.session_state.order_finish = {"items": dict(st.session_state.cart), "total": total_all, "method": m, "cash": cash_in, "change": cash_in - total_all}
                    st.session_state.cart = {}; st.rerun()

# --- 6. PAGE: ANALYTICS ---
elif menu == "📊 วิเคราะห์ยอดขาย":
    st.markdown("<h2 style='color:#D4AF37;'>วิเคราะห์ยอดขาย Premium</h2>", unsafe_allow_html=True)
    df_s = fetch_data(URL_SALES)
    df_sum = fetch_data(URL_SUMMARY)
    
    if not df_s.empty:
        # Data Cleaning
        df_s.columns = df_s.columns.str.strip()
        date_col = df_s.columns[0]
        total_col = df_s.columns[2]
        df_s[date_col] = pd.to_datetime(df_s[date_col], dayfirst=True, errors='coerce')
        
        # Logic ตัดยอด
        today_str = datetime.now().strftime("%d/%m/%Y")
        is_cut = not df_sum[df_sum.iloc[:,0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # Metrics
        today_val = df_s[df_s[date_col].dt.date == datetime.now().date()][total_col].sum()
        week_val = df_s[df_s[date_col] >= (datetime.now() - timedelta(days=7))][total_col].sum()
        month_val = df_s[df_s[date_col].dt.month == datetime.now().month][total_col].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_cut else today_val:,.2f} ฿", delta="ตัดยอดแล้ว" if is_cut else "เปิดยอด")
        m2.metric("ยอดรวม 7 วัน", f"{week_val:,.2f} ฿")
        m3.metric("ยอดรวมเดือนนี้", f"{month_val:,.2f} ฿")
        
        # Chart
        st.markdown("### แนวโน้มยอดขายล่าสุด")
        chart_data = df_s.groupby(df_s[date_col].dt.date)[total_col].sum().reset_index()
        fig = px.bar(chart_data, x=date_col, y=total_col, color_discrete_sequence=['#D4AF37'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("📝 กดตัดยอดสรุปวัน (Reset)", disabled=is_cut):
            requests.post(SCRIPT_URL, json={"action": "save_summary", "date": today_str, "total": float(today_val)})
            st.success("บันทึกตัดยอดสำเร็จ!"); time.sleep(1); st.rerun()

# --- 7. PAGE: STOCK ---
elif menu == "📦 จัดการสต็อก":
    st.markdown("<h2 style='color:#D4AF37;'>สต็อกสินค้าคงเหลือ</h2>", unsafe_allow_html=True)
    st.dataframe(fetch_data(URL_STOCK), use_container_width=True)
