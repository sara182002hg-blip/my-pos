import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Pro V.6", layout="wide")

def load_data_fast(url):
    try:
        response = requests.get(f"{url}&t={time.time()}", timeout=5)
        response.encoding = 'utf-8'
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data_fast(URL_PRODUCTS)
    df_s = load_data_fast(URL_STOCK)
    
    col_main, col_right = st.columns([2.3, 1.7])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row.iloc[0])
                p_price = float(row.iloc[1])
                p_img = row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else "https://via.placeholder.com/150"
                
                s_match = df_s[df_s.iloc[:, 0] == p_name] if not df_s.empty else pd.DataFrame()
                stock_now = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                qty_in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.image(p_img, use_container_width=True)
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"### {p_price:,.0f} ฿")
                        color = "red" if stock_now <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock_now}</span>", unsafe_allow_html=True)
                        
                        if stock_now > qty_in_cart:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                                if p_name not in st.session_state.cart:
                                    st.session_state.cart[p_name] = {'price': p_price, 'qty': 1}
                                else:
                                    st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ สินค้าหมด", disabled=True, use_container_width=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.success("✅ บันทึกยอดเรียบร้อย")
            
            # --- แก้ไข: นำ QR Code เข้าไปอยู่ในสลิป ---
            qr_html = ""
            if r['method'] == "📱 PromptPay":
                qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
                qr_html = f'<div style="text-align:center; margin-top:10px;"><img src="{qr_url}" style="width:180px; border:1px solid #ddd; padding:5px;"></div>'

            receipt_content = f"""
            <div style="background:#fff; color:#000; padding:15px; border:2px solid #333; font-family:monospace; border-radius:5px;">
                <h3 style="text-align:center; margin:0;">TAS POS RECEIPT</h3>
                <hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr>
                <div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวม</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="font-size:12px; margin-top:5px; text-align:center;">ชำระโดย: {r['method']}</p>
                {qr_html}
            </div>
            """
            st.markdown(receipt_content, unsafe_allow_html=True)
            
            if st.button("🔄 เริ่มการขายใหม่", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.info("ตะกร้าว่าง")
            else:
                for n, i in list(st.session_state.cart.items()):
                    total += i['price'] * i['qty']
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{i['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]
                        st.rerun()
                st.divider()
                st.title(f"{total:,.0f} ฿")
                method = st.radio("วิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 จ่ายเงิน", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    try:
                        requests.post(SCRIPT_URL, json={"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total, "method": method}, timeout=8)
                    except: pass
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปรายงานยอดขาย")
    df_sales = load_data_fast(URL_SALES)
    if not df_sales.empty:
        col_dt = df_sales.columns[0]
        col_total = df_sales.columns[3]
        df_sales[col_dt] = pd.to_datetime(df_sales[col_dt], dayfirst=True, errors='coerce')
        
        now = datetime.now()
        # กู้คืน: สรุปยอดรายสัปดาห์
        week_ago = now - timedelta(days=7)
        df_week = df_sales[df_sales[col_dt] >= week_ago]
        # กู้คืน: สรุปยอดรายวัน
        df_today = df_sales[df_sales[col_dt].dt.date == now.date()]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{df_today[col_total].sum():,.0f} ฿", f"{len(df_today)} บิล")
        m2.metric("รายสัปดาห์ (7 วันล่าสุด)", f"{df_week[col_total].sum():,.0f} ฿")
        m3.metric("ยอดขายเดือนนี้", f"{df_sales[df_sales[col_dt].dt.month == now.month][col_total].sum():,.0f} ฿")
        
        # เพิ่ม: ปุ่มสรุปยอดรายวันแบบละเอียด
        if st.button("📝 ดูสรุปยอดรายวันวันนี้"):
            st.table(df_today[[col_dt, 'รายการสินค้า', col_total, 'วิธีชำระ']])

        st.divider()
        st.subheader("📋 ประวัติรายการ")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 เช็คสต็อกสินค้า")
    st.dataframe(load_data_fast(URL_STOCK), use_container_width=True)
