import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. CONSTANTS & ENDPOINTS
# ==========================================
SHEET_ID = "2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe"
URLS = {
    "stock": f"https://docs.google.com/spreadsheets/d/e/{SHEET_ID}/pub?gid=228640428&single=true&output=csv",
    "sales": f"https://docs.google.com/spreadsheets/d/e/{SHEET_ID}/pub?gid=952949333&single=true&output=csv",
    "products": f"https://docs.google.com/spreadsheets/d/e/{SHEET_ID}/pub?gid=1258507712&single=true&output=csv",
    "summary": f"https://docs.google.com/spreadsheets/d/e/{SHEET_ID}/pub?gid=668209785&single=true&output=csv"
}
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PP_ID = "0945016189"

st.set_page_config(page_title="TAS POS ZENITH V22", layout="wide")

# ==========================================
# 2. THE ULTIMATE DARK CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans Thai', sans-serif; }
    .stApp { background-color: #080808; color: #FFFFFF; }
    
    /* Card Premium Look */
    .p-card {
        background: linear-gradient(145deg, #1a1a1a, #0f0f0f);
        border: 1px solid #333; border-radius: 20px; padding: 15px;
        text-align: center; transition: 0.4s ease;
    }
    .p-card:hover { border-color: #D4AF37; box-shadow: 0 0 20px rgba(212,175,55,0.15); }
    .p-card img { width: 100%; height: 170px; object-fit: cover; border-radius: 15px; margin-bottom: 12px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #222; }
    
    /* Premium Price */
    .p-price { font-size: 26px; color: #D4AF37; font-weight: 600; }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #080808; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    
    /* Metrics */
    div[data-testid="metric-container"] { background: #111; border: 1px solid #222; border-radius: 15px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC ENGINE
# ==========================================
def get_data(key):
    try:
        r = requests.get(f"{URLS[key]}&v={time.time()}", timeout=10)
        r.encoding = 'utf-8'
        return pd.read_csv(StringIO(r.text)).dropna(how='all')
    except: return pd.DataFrame()

# Session State Persistence
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt_data' not in st.session_state: st.session_state.receipt_data = None

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4059/4059635.png", width=80) # Icon ตกแต่ง
    st.markdown("<h2 style='text-align:center;'>ZENITH POS</h2>", unsafe_allow_html=True)
    page = st.selectbox("เลือกเมนู", ["🛒 POS ระบบขาย", "📈 วิเคราะห์ยอด", "📦 คลังสินค้า"])
    st.divider()
    if st.button("🔄 Sync Cloud Data"): st.cache_data.clear(); st.rerun()

# ==========================================
# 4. PAGE: POS SYSTEM
# ==========================================
if page == "🛒 POS ระบบขาย":
    df_p = get_data("products")
    df_s = get_data("stock")
    
    # ดึงสต็อกจริงมาเช็ค
    stock_dict = {}
    if not df_s.empty:
        stock_dict = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_main, col_cart = st.columns([2.2, 1.3])

    with col_main:
        st.markdown("<h3 style='color:#D4AF37;'>เมนูสินค้า</h3>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                
                # Logic เช็คสต็อก
                real_stock = int(stock_dict.get(p_name, 0))
                cart_qty = st.session_state.cart.get(p_name, {}).get('qty', 0)
                remain = real_stock - cart_qty

                with grid[i % 3]:
                    st.markdown(f"""
                    <div class="p-card">
                        <img src="{p_img}">
                        <div style="font-weight:400; height:25px; overflow:hidden;">{p_name}</div>
                        <div class="p-price">{p_price:,.0f} ฿</div>
                        <small style="color:{'#888' if remain > 0 else '#ff4b4b'}">คงเหลือ: {remain}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if remain > 0:
                        if st.button("🛒 เลือก", key=f"add_{i}", use_container_width=True):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("SOLD OUT", key=f"sold_{i}", disabled=True, use_container_width=True)

    with col_cart:
        if st.session_state.receipt_data:
            # --- DISPLAY RECEIPT ---
            r = st.session_state.receipt_data
            qr_code_url = f"https://promptpay.io/{PP_ID}/{r['total']}.png"
            
            receipt_html = f"""
            <div id="receipt" style="background:#FFF; color:#000; padding:25px; border-radius:10px; font-family:monospace; width:300px; margin:auto;">
                <center><b>TAS ZENITH SHOP</b><br><small>TAX# {r['bill_id']}</small><hr></center>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in r['items'].items()])}
                <hr>
                <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:18px;"><span>TOTAL</span><span>{r['total']:,.0f} ฿</span></div>
                <div style="margin-top:10px; font-size:12px;">Method: {r['method']}</div>
                {f'<div style="display:flex;justify-content:space-between;"><span>Received:</span><span>{r["cash"]:,.2f}</span></div><div style="display:flex;justify-content:space-between;font-weight:bold;"><span>Change:</span><span>{r["change"]:,.2f}</span></div>' if r['method'] == "เงินสด" else ""}
                {f'<center><img src="{qr_code_url}" width="180" style="margin-top:10px;"></center>' if r['method'] == "พร้อมเพย์" else ""}
                <hr><center><small>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small></center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            if st.button("🖨️ PRINT RECEIPT", type="primary", use_container_width=True):
                st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`{receipt_html}`);w.document.close();setTimeout(function(){{w.print();w.close();}},500);</script>", height=0)
            if st.button("NEXT ORDER ➡️", use_container_width=True):
                st.session_state.receipt_data = None; st.rerun()
        else:
            # --- SHOPPING CART ---
            st.markdown("<h3 style='color:#D4AF37;'>ตะกร้าปัจจุบัน</h3>", unsafe_allow_html=True)
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า")
            else:
                grand_total = 0
                for name, item in list(st.session_state.cart.items()):
                    sub = item['price'] * item['qty']
                    grand_total += sub
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2.5, 1, 1])
                        c1.markdown(f"**{name}**\n\n{item['price']:,.0f} ฿")
                        c2.write(f"x{item['qty']}")
                        if c3.button("🗑️", key=f"del_{name}"):
                            del st.session_state.cart[name]; st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{grand_total:,.0f} ฿</h1>", unsafe_allow_html=True)
                method = st.radio("ชำระเงินโดย", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                cash = 0.0
                if method == "เงินสด":
                    cash = st.number_input("เงินที่ได้รับ", min_value=float(grand_total), step=20.0)
                
                if st.button("🏁 จบการขาย", type="primary", use_container_width=True):
                    with st.spinner("📦 Syncing with Cloud..."):
                        bill_id = f"T{int(time.time())}"
                        try:
                            # ส่งข้อมูลเข้า Google Apps Script
                            requests.post(SCRIPT_URL, json={
                                "action": "checkout", "bill_id": bill_id,
                                "summary": str(st.session_state.cart), "total": grand_total, "method": method
                            }, timeout=10)
                            
                            st.session_state.receipt_data = {
                                "bill_id": bill_id, "items": dict(st.session_state.cart),
                                "total": grand_total, "method": method, "cash": cash, "change": cash - grand_total
                            }
                            st.session_state.cart = {}; st.rerun()
                        except:
                            st.error("⚠️ ไม่สามารถติดต่อ Server ได้ แต่คุณสามารถพิมพ์ใบเสร็จจากหน้านี้ได้")

# ==========================================
# 5. PAGE: ANALYTICS
# ==========================================
elif page == "📈 วิเคราะห์ยอด":
    st.markdown("<h2 style='color:#D4AF37;'>📈 สรุปผลประกอบการ</h2>", unsafe_allow_html=True)
    df_sales = get_data("sales")
    df_sum = get_data("summary")
    
    if not df_sales.empty:
        # Data Prep
        df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
        val_col = df_sales.columns[2]
        date_col = df_sales.columns[0]
        
        # Checking Close Day
        now = datetime.now()
        today_str = now.strftime("%d/%m/%Y")
        is_done = not df_sum[df_sum.iloc[:, 0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # Stats
        day_total = df_sales[df_sales[date_col].dt.date == now.date()][val_col].sum()
        week_total = df_sales[df_sales[date_col] >= (now - timedelta(days=7))][val_col].sum()
        month_total = df_sales[df_sales[date_col].dt.month == now.month][val_col].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_done else day_total:,.0f} ฿", delta="ปิดยอดแล้ว" if is_done else "กำลังขาย")
        m2.metric("ยอดรวม 7 วัน", f"{week_total:,.0f} ฿")
        m3.metric("ยอดรวมเดือนนี้", f"{month_total:,.0f} ฿")
        
        st.divider()
        if st.button("🌓 ปิดยอดวันและสรุปผล", use_container_width=True, disabled=is_done):
            requests.post(SCRIPT_URL, json={"action": "save_summary", "date": today_str, "total": float(day_total)})
            st.success("บันทึกสำเร็จ!"); time.sleep(1); st.rerun()
        
        st.dataframe(df_sales.sort_values(by=date_col, ascending=False), use_container_width=True)

# ==========================================
# 6. PAGE: STOCK
# ==========================================
else:
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้าปัจจุบัน</h2>", unsafe_allow_html=True)
    st.dataframe(get_data("stock"), use_container_width=True, height=600)
