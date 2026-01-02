import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล (GID ตรงตามลำดับชีตล่าสุดที่คุณจัดเรียง) ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Ultra V.2.1", layout="wide")

# CSS จัดรูปภาพให้เท่ากันและ UI สวยงาม
st.markdown("""
    <style>
    .product-img { width: 100%; height: 180px; object-fit: contain; background: white; border-radius: 12px; border: 1px solid #f0f0f0; }
    .stMetric { background: #1e2130; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebarNav"] { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

def load_data_live(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

# --- Sidebar ---
menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data_live(URL_PRODUCTS)
    df_s = load_data_live(URL_STOCK)
    
    col_main, col_right = st.columns([2.5, 1.5])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ระบบค้นหาคอลัมน์อัตโนมัติป้องกัน Error
            col_name = 'Name' if 'Name' in df_p.columns else df_p.columns[0]
            col_price = 'Price' if 'Price' in df_p.columns else df_p.columns[1]
            col_img = 'Image_URL' if 'Image_URL' in df_p.columns else None
            
            # ระบบหมวดหมู่
            if 'Category' in df_p.columns:
                cats = ["ทั้งหมด"] + df_p['Category'].unique().tolist()
                sel_cat = st.selectbox("📂 เลือกหมวดหมู่", cats)
                if sel_cat != "ทั้งหมด":
                    df_p = df_p[df_p['Category'] == sel_cat]

            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # ดึงสต็อกจริง
                p_name = row[col_name]
                s_match = df_s[df_s['Name'] == p_name] if 'Name' in df_s.columns else pd.DataFrame()
                stock = int(s_match.iloc[0]['Stock']) if not s_match.empty else 0
                cart_qty = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        img_url = row[col_img] if col_img and pd.notna(row[col_img]) else "https://via.placeholder.com/150"
                        st.markdown(f'<img src="{img_url}" class="product-img">', unsafe_allow_html=True)
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"### {row[col_price]:,} ฿")
                        
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > cart_qty:
                            if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price':row[col_price], 'qty':0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ หมด", disabled=True, use_container_width=True)
        else:
            st.warning("ไม่พบข้อมูลสินค้า กรุณาตรวจสอบชีต Products")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จ")
            qr_html = ""
            if r['method'] == "📱 PromptPay":
                qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
                qr_html = f'<div style="text-align: center; margin-top: 15px;"><img src="{qr_url}" width="220"/></div>'

            st.markdown(f"""
            <div style="background:white; color:black; padding:20px; border-radius:10px; font-family:monospace; border:1px solid #ddd;">
                <h2 style="text-align:center; margin:0;">TAS POS</h2>
                <hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n,i in r['items'].items()])}
                <hr>
                <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>รวม</span><span>{r['total']:,} ฿</span></div>
                {qr_html}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🖨️ พิมพ์ใบเสร็จ", use_container_width=True):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            if st.button("🔄 ขายต่อ", use_container_width=True, type="primary"):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้า")
            total = 0
            for n, i in list(st.session_state.cart.items()):
                total += i['price'] * i['qty']
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{n}** x{i['qty']}")
                if c2.button("🗑️", key=f"del_{n}"):
                    del st.session_state.cart[n]
                    st.rerun()
            
            if total > 0:
                st.divider()
                st.title(f"{total:,} ฿")
                method = st.radio("วิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยัน", use_container_width=True, type="primary"):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    requests.post(SCRIPT_URL, json={"action":"checkout", "bill_id":bill_id, "summary":summary, "total":total, "method":method})
                    st.session_state.receipt = {"id":bill_id, "items":dict(st.session_state.cart), "total":total, "method":method}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 ยอดขาย")
    df_sales = load_data_live(URL_SALES)
    if not df_sales.empty:
        # ใช้ระบบค้นหาคอลัมน์วันที่อัตโนมัติ
        col_dt = 'วันที่/เวลา' if 'วันที่/เวลา' in df_sales.columns else df_sales.columns[0]
        df_sales['วันที่'] = pd.to_datetime(df_sales[col_dt]).dt.strftime("%d/%m/%Y")
        today = datetime.now().strftime("%d/%m/%Y")
        total_today = df_sales[df_sales['วันที่'] == today]['ยอดรวม'].sum()
        
        st.metric("ยอดขายวันนี้", f"{total_today:,} ฿")
        if st.button("📅 ตัดยอดรายวัน"):
            requests.post(SCRIPT_URL, json={"action":"save_summary", "date":today, "total":total_today, "bills":len(df_sales[df_sales['วันที่'] == today])})
            st.success("บันทึกแล้ว")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อก")
    st.dataframe(load_data_live(URL_STOCK), use_container_width=True)
