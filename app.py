import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Ultra V3", layout="wide")

# CSS จัด UI และรูปภาพ
st.markdown("""
    <style>
    .product-img { width: 100%; height: 160px; object-fit: contain; background: white; border-radius: 10px; border: 1px solid #eee; }
    .stMetric { background: #1e2130; padding: 15px; border-radius: 10px; }
    .cart-box { background: #262730; padding: 15px; border-radius: 10px; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

def load_data_live(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data_live(URL_PRODUCTS)
    df_s = load_data_live(URL_STOCK)
    
    col_main, col_right = st.columns([2.2, 1.8])
    
    with col_main:
        st.subheader("📦 สินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = row.iloc[0]
                p_price = row.iloc[1]
                p_img = row.iloc[3] if len(row) > 3 else ""
                
                # เช็คสต็อก Real-time
                s_match = df_s[df_s.iloc[:, 0] == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.markdown(f'<img src="{p_img}" class="product-img">', unsafe_allow_html=True)
                        st.write(f"**{p_name}**")
                        st.write(f"**{p_price:,} ฿**")
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > in_cart:
                            if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price':p_price, 'qty':0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else: st.button("❌ หมด", disabled=True, key=f"sold_{i}", use_container_width=True)

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จ")
            qr_code = f'<center><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" width="200"></center>' if r['method'] == "📱 PromptPay" else ""
            st.markdown(f"""
                <div style="background:white; color:black; padding:20px; border-radius:10px; font-family:monospace;">
                    <h2 style="text-align:center;">TAS POS</h2>
                    <hr>
                    {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n,i in r['items'].items()])}
                    <hr>
                    <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>รวมทั้งสิ้น</span><span>{r['total']:,} ฿</span></div>
                    <p>วิธีชำระ: {r['method']}</p>
                    {qr_code}
                </div>
            """, unsafe_allow_html=True)
            if st.button("🖨️ พิมพ์ใบเสร็จ"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            if st.button("🔄 เริ่มการขายใหม่", type="primary"): 
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                with st.container(border=True):
                    for n, i in list(st.session_state.cart.items()):
                        subtotal = i['price'] * i['qty']
                        total += subtotal
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**{n}**")
                        c2.write(f"x{i['qty']}")
                        if c3.button("🗑️", key=f"del_{n}"):
                            del st.session_state.cart[n]
                            st.rerun()
                
                st.markdown(f"### รวม: {total:,} ฿")
                method = st.radio("วิธีจ่ายเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                
                if st.button("🚀 ยืนยันและชำระเงิน", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    try:
                        requests.post(SCRIPT_URL, json={"action":"checkout", "bill_id":bill_id, "summary":summary, "total":total, "method":method}, timeout=5)
                        st.session_state.receipt = {"items":dict(st.session_state.cart), "total":total, "method":method}
                        st.session_state.cart = {}
                        st.rerun()
                    except: st.error("บันทึกลงชีตไม่สำเร็จ ตรวจสอบเน็ตหรือ Apps Script")

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 ยอดขายและการตัดยอด")
    df_sales = load_data_live(URL_SALES)
    df_sum = load_data_live(URL_SUMMARY)
    
    today = datetime.now().strftime("%d/%m/%Y")
    
    if not df_sales.empty:
        # ปรับการดึงวันที่ให้ตรงกับ Google Sheets (รองรับ / และ -)
        col_dt = df_sales.columns[0]
        df_sales['Date_Only'] = pd.to_datetime(df_sales[col_dt], errors='coerce').dt.strftime("%d/%m/%Y")
        
        # เช็คว่าตัดยอดวันนี้ไปหรือยัง
        is_cut = not df_sum[df_sum.iloc[:, 0] == today].empty if not df_sum.empty else False
        
        sales_today = df_sales[df_sales['Date_Only'] == today]
        total_today = pd.to_numeric(sales_today.iloc[:, 3], errors='coerce').sum()
        
        c1, c2 = st.columns(2)
        c1.metric("ยอดขายวันนี้", f"{0 if is_cut else total_today:,} ฿")
        c2.metric("จำนวนบิลวันนี้", f"{0 if is_cut else len(sales_today)} บิล")
        
        if st.button("📅 บันทึกตัดยอดรายวัน", type="primary", disabled=is_cut):
            requests.post(SCRIPT_URL, json={"action":"save_summary", "date":today, "total":float(total_today), "bills":int(len(sales_today))})
            st.success("ตัดยอดสำเร็จ!")
            time.sleep(1)
            st.rerun()
            
        st.divider()
        st.subheader("📝 ประวัติการขาย")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อกสินค้า")
    st.dataframe(load_data_live(URL_STOCK), use_container_width=True)
