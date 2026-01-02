import streamlit as st
import pandas as pd
import requests
import time
import json
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. CORE SYSTEM CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv",
    "summary": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
}
# ==========================================
# 1. CORE SYSTEM CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv",
    "summary": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
}

# --- วางลิงก์ใหม่ตรงนี้ครับ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzO9AocZxITbOVURUpuaYXkkwLwgMLRWYUb_LSiY3SxjbPYz36MWkg1Ean000MVcWi6/exec"
# ---------------------------

PROMPTPAY_ID = "0945016189"
st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM UI: GLASSMORPHISM BLACK THEME
# ==========================================
st.markdown(f"""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * {{ font-family: 'Kanit', sans-serif; }}
    .stApp {{ background-color: #050505; color: #E0E0E0; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #111, #000); border-right: 1px solid #333; }}
    
    /* Custom Product Cards */
    .product-box {{
        background: rgba(28, 33, 40, 0.8);
        border: 1px solid #30363D;
        border-radius: 18px;
        padding: 15px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-align: center;
        backdrop-filter: blur(10px);
    }}
    .product-box:hover {{
        border-color: #D4AF37;
        transform: scale(1.03);
        box-shadow: 0 10px 20px rgba(212, 175, 55, 0.2);
    }}
    .img-container img {{ width: 100%; height: 180px; object-fit: cover; border-radius: 12px; }}
    
    /* Price and Text */
    .price-tag {{ font-size: 24px; color: #D4AF37; font-weight: 600; margin: 10px 0; }}
    .stock-label {{ font-size: 12px; color: #888; }}
    
    /* Button Premium */
    .stButton>button {{
        background: linear-gradient(90deg, #D4AF37, #F1D279);
        color: black !important; border: none; border-radius: 10px;
        font-weight: 600; transition: 0.3s; width: 100%; height: 45px;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(212,175,55,0.4); }}
    
    /* Metric Cards */
    div[data-testid="metric-container"] {{
        background: #161B22; border: 1px solid #30363D; border-radius: 15px; padding: 20px;
    }}
    [data-testid="stMetricValue"] {{ color: #D4AF37 !important; font-size: 32px !important; }}
    
    /* Receipt Styles */
    .receipt-container {{
        background: #FFF; color: #000; padding: 30px; border-radius: 10px;
        box-shadow: 0 0 20px rgba(255,255,255,0.1); font-family: 'Courier New', Courier, monospace;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ROBUST DATA ENGINE
# ==========================================
class POSDataEngine:
    @staticmethod
    def fetch(key):
        try:
            url = CSV_URLS[key]
            response = requests.get(f"{url}&nocache={time.time()}", timeout=15)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                df.columns = df.columns.str.strip()
                return df.dropna(how='all')
        except Exception as e:
            st.error(f"Data Fetch Error ({key}): {e}")
        return pd.DataFrame()

    @staticmethod
    def post_to_gsheet(payload):
        try:
            res = requests.post(SCRIPT_URL, json=payload, timeout=20)
            return res.status_code == 200
        except:
            return False

# Initialize Session States for Persistence
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None
if 'active_tab' not in st.session_state: st.session_state.active_tab = "🛒 POS"

# ==========================================
# 4. MAIN NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>PLATINUM POS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>Version 21.0 Premium</p>", unsafe_allow_html=True)
    st.divider()
    
    choice = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"], label_visibility="collapsed")
    
    st.divider()
    if st.button("🔄 Sync Data (Force)"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.info("System Online: Connected to Google Cloud")

# ==========================================
# 5. PAGE: POS SYSTEM (THE CORE)
# ==========================================
if choice == "🛒 หน้าขายสินค้า":
    df_p = POSDataEngine.fetch("products")
    df_s = POSDataEngine.fetch("stock")
    
    # Create Stock Dictionary for Speed
    stock_map = {}
    if not df_s.empty:
        stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict()

    col_l, col_r = st.columns([2.3, 1.4])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if df_p.empty:
            st.warning("กำลังโหลดข้อมูลสินค้า...")
        else:
            # Grid Layout
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                current_stock = int(stock_map.get(p_name, 0))
                
                # Check how many already in cart
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = current_stock - in_cart

                with grid[idx % 3]:
                    st.markdown(f"""
                    <div class="product-box">
                        <div class="img-container"><img src="{p_img if p_img else 'https://via.placeholder.com/200'}"></div>
                        <div style="margin-top:10px; font-weight:600; height:30px;">{p_name}</div>
                        <div class="price-tag">{p_price:,.0f} ฿</div>
                        <div class="stock-label">คงเหลือ: {available} ชิ้น</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"p_{idx}"):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"out_{idx}", disabled=True)

    with col_r:
        if st.session_state.last_receipt:
            # --- RECEIPT VIEW ---
            res = st.session_state.last_receipt
            qr_url = f"https://promptpay.io/{PROMPTPAY_ID}/{res['total']}.png"
            
            receipt_html = f"""
            <div id="receipt-box" class="receipt-container">
                <center>
                    <h2 style="margin:0;">TAS PREMIUM SHOP</h2>
                    <small>เลขที่บิล: {res['bill_id']}</small>
                    <hr style="border-top: 1px dashed #000;">
                </center>
                <table style="width:100%; border-collapse: collapse;">
                    {''.join([f'<tr><td style="padding:5px 0;">{k} x{v["qty"]}</td><td style="text-align:right;">{v["price"]*v["qty"]:,.0f}</td></tr>' for k,v in res['items'].items()])}
                </table>
                <hr style="border-top: 1px dashed #000;">
                <div style="display:flex; justify-content:space-between; font-size:20px; font-weight:bold;">
                    <span>ยอดรวมสุทธิ</span><span>{res['total']:,.0f} ฿</span>
                </div>
                <div style="margin-top:10px; font-size:14px;">
                    ชำระโดย: {res['method']}<br>
                    {f"รับเงินสด: {res['cash']:,.2f} ฿<br>เงินทอน: {res['change']:,.2f} ฿" if res['method'] == "เงินสด" else ""}
                </div>
                {f'<center><div style="margin:15px 0;"><img src="{qr_url}" width="180"></div><p style="font-size:12px;">สแกนเพื่อชำระเงิน (เบอร์: {PROMPTPAY_ID})</p></center>' if res['method'] == "พร้อมเพย์" else ""}
                <hr style="border-top: 1px dashed #000;">
                <center><small>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>*** ขอบคุณที่มาอุดหนุน ***</small></center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🖨️ พิมพ์ใบเสร็จ"):
                    st.components.v1.html(f"<script>var w=window.open('','','width=400,height=600');w.document.write(`<html><head><style>body{{margin:0;}}</style></head><body>{receipt_html}</body></html>`);w.document.close();setTimeout(function(){{w.print();w.close();}},500);</script>", height=0)
            with c2:
                if st.button("➕ เปิดบิลใหม่", type="primary"):
                    st.session_state.last_receipt = None
                    st.rerun()
        else:
            # --- CART VIEW ---
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้าของฉัน</h3>", unsafe_allow_html=True)
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า... กรุณาเลือกสินค้า")
            else:
                total_val = 0
                for name, data in list(st.session_state.cart.items()):
                    subtotal = data['price'] * data['qty']
                    total_val += subtotal
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{name}**\n\n{data['price']:,.0f} x {data['qty']}")
                        if c2.button("➕", key=f"plus_{name}"):
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                        if c3.button("🗑️", key=f"rem_{name}"):
                            del st.session_state.cart[name]
                            st.rerun()
                
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total_val:,.0f} ฿</h1>", unsafe_allow_html=True)
                
                pay_method = st.radio("วิธีการชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                cash_received = 0.0
                if pay_method == "เงินสด":
                    cash_received = st.number_input("ยอดเงินที่รับ", min_value=float(total_val), step=20.0, format="%.2f")
                    st.markdown(f"### เงินทอน: <span style='color:#00FF00;'>{cash_received - float(total_val):,.2f} ฿</span>", unsafe_allow_html=True)
                
                if st.button("🚀 ยืนยันการขายและออกใบเสร็จ", type="primary"):
                    bill_id = f"POS{int(time.time())}"
                    summary_text = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    
                    with st.spinner("📦 กำลังตัดสต็อกและบันทึกข้อมูล..."):
                        success = POSDataEngine.post_to_gsheet({
                            "action": "checkout",
                            "bill_id": bill_id,
                            "summary": summary_text,
                            "total": float(total_val),
                            "method": pay_method
                        })
                        
                        if success:
                            st.session_state.last_receipt = {
                                "bill_id": bill_id,
                                "items": dict(st.session_state.cart),
                                "total": total_val,
                                "method": pay_method,
                                "cash": cash_received,
                                "change": cash_received - float(total_val)
                            }
                            st.session_state.cart = {}
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ การเชื่อมต่อล้มเหลว ข้อมูลไม่ถูกบันทึก!")

# ==========================================
# 6. PAGE: ANALYTICS (DEEP INSIGHT)
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ผลประกอบการ</h2>", unsafe_allow_html=True)
    df_sales = POSDataEngine.fetch("sales")
    df_sum = POSDataEngine.fetch("summary")
    
    if df_sales.empty:
        st.info("ไม่พบข้อมูลการขายในขณะนี้")
    else:
        # Preprocessing Dates
        df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
        val_col = df_sales.columns[2]
        date_col = df_sales.columns[0]
        
        now = datetime.now()
        today = now.date()
        today_str = now.strftime("%d/%m/%Y")
        
        # Checking Daily Summary Status
        is_closed = False
        if not df_sum.empty:
            is_closed = not df_sum[df_sum.iloc[:,0].astype(str).str.contains(today_str)].empty
        
        # Aggregations
        today_val = df_sales[df_sales[date_col].dt.date == today][val_col].sum()
        week_val = df_sales[df_sales[date_col] >= (now - timedelta(days=7))][val_col].sum()
        month_val = df_sales[df_sales[date_col].dt.month == now.month][val_col].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_closed else today_val:,.2f} ฿", delta="CLOSED" if is_closed else "ACTIVE")
        m2.metric("ยอดรวม 7 วัน", f"{week_val:,.2f} ฿")
        m3.metric("ยอดรวมเดือนนี้", f"{month_val:,.2f} ฿")
        
        st.divider()
        
        tab1, tab2 = st.tabs(["📉 ประวัติรายการขาย", "📝 บันทึกสรุปยอดปิดวัน"])
        
        with tab1:
            st.dataframe(df_sales.sort_values(by=date_col, ascending=False), use_container_width=True)
            
        with tab2:
            if is_closed:
                st.success(f"✅ วันนี้ ({today_str}) สรุปยอดปิดวันเรียบร้อยแล้ว")
            else:
                st.warning("⚠️ โปรดตรวจสอบข้อมูลก่อนกด 'ปิดยอดวัน' ยอดวันนี้จะถูกย้ายเข้าสู่ DailySummary และรีเซ็ตหน้าจอ")
                if st.button("Confirm: บันทึกปิดยอดวันนี้"):
                    with st.spinner("Saving summary..."):
                        ok = POSDataEngine.post_to_gsheet({
                            "action": "save_summary",
                            "date": today_str,
                            "total": float(today_val),
                            "bills": len(df_sales[df_sales[date_col].dt.date == today])
                        })
                        if ok:
                            st.success("บันทึกสำเร็จ!")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()

# ==========================================
# 7. PAGE: STOCK MANAGEMENT
# ==========================================
elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้าออนไลน์</h2>", unsafe_allow_html=True)
    df_stock = POSDataEngine.fetch("stock")
    
    if not df_stock.empty:
        # Highlight low stock
        def highlight_low(s):
            return ['background-color: #5b2121' if v < 10 else '' for v in s]
        
        st.write("รายการสินค้าในระบบทั้งหมด (ดึงข้อมูลล่าสุดจาก Cloud)")
        st.dataframe(df_stock, use_container_width=True, height=500)
    else:
        st.error("ไม่สามารถเชื่อมต่อข้อมูลสต็อกได้")
