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

st.set_page_config(page_title="TAS POS ULTIMATE V11", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PROFESSIONAL STYLING ---
st.markdown("""
<style>
    /* Product Image Uniformity */
    .product-img-container {
        width: 100%;
        height: 180px;
        overflow: hidden;
        border-radius: 10px;
        background: #f0f2f6;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .product-img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    /* Hide Streamlit Header */
    header {visibility: hidden;}
    /* Metrics Styling */
    [data-testid="stMetricValue"] { font-size: 28px; color: #007bff; }
    /* Button Customization */
    .stButton>button { border-radius: 8px; font-weight: 600; }
    /* Print Setup */
    @media print { .no-print { display: none !important; } }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=60) # Cache 1 minute for extreme speed
def get_remote_data(url):
    try:
        response = requests.get(f"{url}&ts={time.time()}", timeout=10)
        response.encoding = 'utf-8'
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

def find_column(df, patterns):
    for pattern in patterns:
        for col in df.columns:
            if pattern.lower() in col.lower(): return col
    return df.columns[0] if not df.empty else None

# Initialize Session States
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# --- 4. NAVIGATION ---
menu = st.sidebar.title("MENU")
page = st.sidebar.radio("Go to", ["🛒 Cashier Desk", "📊 Sales Report", "📦 Inventory"])

# --- 5. PAGE: CASHIER DESK ---
if page == "🛒 Cashier Desk":
    df_p = get_remote_data(URL_PRODUCTS)
    df_s = get_remote_data(URL_STOCK)
    
    col_prod, col_cart = st.columns([2, 1.3])
    
    with col_prod:
        st.subheader("📦 สินค้าทั้งหมด")
        if not df_p.empty:
            c_name = find_column(df_p, ["สินค้า", "name", "item"])
            c_price = find_column(df_p, ["ราคา", "price"])
            c_img = find_column(df_p, ["รูป", "image", "url", "img"])
            
            # Inventory Mapping
            s_name = find_column(df_s, ["สินค้า", "name"])
            s_qty = find_column(df_s, ["เหลือ", "stock", "qty"])
            stock_dict = pd.Series(df_s[s_qty].values, index=df_s[s_name].str.strip()).to_dict()

            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                name = str(row[c_name]).strip()
                price = float(row[c_price])
                img_url = str(row[c_img]) if c_img and pd.notna(row[c_img]) else ""
                current_stock = int(stock_dict.get(name, 0))
                in_cart = st.session_state.cart.get(name, {}).get('qty', 0)
                available = current_stock - in_cart
                
                with grid[idx % 3]:
                    with st.container(border=True):
                        # Image with forced aspect ratio
                        if img_url.startswith("http"):
                            st.markdown(f'<div class="product-img-container"><img src="{img_url}"></div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="product-img-container">📷 No Image</div>', unsafe_allow_html=True)
                        
                        st.write(f"**{name}**")
                        st.write(f"### {price:,.0f} ฿")
                        
                        status_color = "#28a745" if available > 5 else "#dc3545"
                        st.markdown(f"คงเหลือ: <span style='color:{status_color}; font-weight:bold;'>{available}</span>", unsafe_allow_html=True)
                        
                        if available > 0:
                            if st.button(f"🛒 เพิ่มลงตะกร้า", key=f"btn_{idx}", use_container_width=True):
                                st.session_state.cart[name] = st.session_state.cart.get(name, {'price': price, 'qty': 0})
                                st.session_state.cart[name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ สินค้าหมด", disabled=True, use_container_width=True, key=f"out_{idx}")

    with col_cart:
        if st.session_state.last_receipt:
            res = st.session_state.last_receipt
            qr_link = f"https://promptpay.io/{MY_PROMPTPAY}/{res['total']}.png"
            
            # Receipt HTML Template for Printing
            receipt_html = f"""
            <div id="receipt" style="width:300px; padding:20px; background:white; color:black; font-family:'Courier New', Courier, monospace; border:1px solid #ddd; margin:auto;">
                <center>
                    <h2 style="margin:0;">TAS POS</h2>
                    <p style="font-size:12px;">Tax Invoice (Abbr.)</p>
                    <hr style="border-top: 1px dashed black;">
                </center>
                <div style="font-size:14px;">
                    {''.join([f'<div style="display:flex; justify-content:space-between;"><span>{k} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for k,v in res['items'].items()])}
                </div>
                <hr style="border-top: 1px dashed black;">
                <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:18px;">
                    <span>TOTAL</span><span>{res['total']:,.0f} THB</span>
                </div>
                <center>
                    <p style="font-size:12px; margin-top:10px;">Payment: {res['method']}</p>
                    {f'<img src="{qr_link}" width="150" style="margin-top:10px;">' if res['method'] == "PromptPay" else ''}
                    <p style="font-size:11px; margin-top:10px;">Thank you for your visit</p>
                    <p style="font-size:10px;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            # Print Action
            if st.button("🖨️ พิมพ์ใบเสร็จ", type="primary", use_container_width=True):
                st.components.v1.html(f"""
                <script>
                var win = window.open('', 'PRINT', 'height=600,width=400');
                win.document.write('<html><head><title>Print Receipt</title></head><body>');
                win.document.write(`{receipt_html}`);
                win.document.write('</body></html>');
                win.document.close();
                win.focus();
                setTimeout(function(){{ win.print(); win.close(); }}, 500);
                </script>
                """, height=0)

            if st.button("🔄 เริ่มการขายใหม่", use_container_width=True):
                st.session_state.last_receipt = None
                st.rerun()
        
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                total_sum = 0
                for item, data in list(st.session_state.cart.items()):
                    subtotal = data['price'] * data['qty']
                    total_sum += subtotal
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{item}**")
                    c2.write(f"x{data['qty']}")
                    if c3.button("🗑️", key=f"del_{item}"):
                        del st.session_state.cart[item]
                        st.rerun()
                
                st.divider()
                st.write(f"### รวมทั้งสิ้น: :blue[{total_sum:,.0f} ฿]")
                pay_method = st.radio("ช่องทางการชำระเงิน", ["Cash", "PromptPay"], horizontal=True)
                
                if st.button("🚀 ยืนยันการสั่งซื้อ", type="primary", use_container_width=True):
                    with st.spinner("Saving..."):
                        # Prepare data for Apps Script
                        items_str = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                        payload = {
                            "action": "checkout",
                            "bill_id": f"B{int(time.time())}",
                            "summary": items_str,
                            "total": total_sum,
                            "method": pay_method
                        }
                        try:
                            requests.post(SCRIPT_URL, json=payload, timeout=5)
                            st.session_state.last_receipt = {"items": dict(st.session_state.cart), "total": total_sum, "method": pay_method}
                            st.session_state.cart = {}
                            st.cache_data.clear()
                            st.rerun()
                        except:
                            st.error("Error saving to database. Please check connection.")

# --- 6. PAGE: SALES REPORT ---
elif page == "📊 Sales Report":
    st.title("📊 รายงานยอดขาย")
    df_sales = get_remote_data(URL_SALES)
    df_sum = get_remote_data(URL_SUMMARY)
    
    if not df_sales.empty:
        c_date = find_column(df_sales, ["วัน", "date", "time"])
        c_val = find_column(df_sales, ["ยอด", "total", "price"])
        
        df_sales[c_date] = pd.to_datetime(df_sales[c_date], dayfirst=True, errors='coerce')
        now = datetime.now()
        
        # Check if already summary today
        today_str = now.strftime("%d/%m/%Y")
        is_already_summary = not df_sum[df_sum.iloc[:, 0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
        
        # Calculate Metrics
        sales_today = df_sales[df_sales[c_date].dt.date == now.date()][c_val].sum() if not is_already_summary else 0
        bill_count = len(df_sales[df_sales[c_date].dt.date == now.date()]) if not is_already_summary else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{sales_today:,.0f} ฿", f"{bill_count} บิล")
        m2.metric("รายสัปดาห์", f"{df_sales[df_sales[c_date] >= (now - timedelta(days=7))][c_val].sum():,.0f} ฿")
        m3.metric("รายเดือน", f"{df_sales[df_sales[c_date].dt.month == now.month][c_val].sum():,.0f} ฿")
        
        st.divider()
        if st.button("📝 บันทึกสรุปยอดปิดวัน (Reset ยอดขายหน้าจอ)", type="primary", disabled=is_already_summary):
            try:
                raw_today = df_sales[df_sales[c_date].dt.date == now.date()]
                requests.post(SCRIPT_URL, json={
                    "action": "save_summary",
                    "date": today_str,
                    "total": float(raw_today[c_val].sum()),
                    "bills": int(len(raw_today))
                }, timeout=10)
                st.success("สรุปยอดเรียบร้อยแล้ว!")
                st.cache_data.clear()
                st.rerun()
            except: st.error("Failed to save summary.")

        st.subheader("📋 ประวัติรายการล่าสุด")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

# --- 7. PAGE: INVENTORY ---
elif page == "📦 Inventory":
    st.title("📦 ระบบจัดการสต็อก")
    df_stock = get_remote_data(URL_STOCK)
    st.dataframe(df_stock, use_container_width=True, height=600)
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
