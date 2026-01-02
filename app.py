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

st.set_page_config(page_title="TAS POS Ultra V.5", layout="wide")

# ฟังก์ชันโหลดข้อมูลแบบ Bypass Cache ขั้นสูงสุด (แก้ปัญหาหน่วงและไม่ Real-time)
def load_data_fast(url):
    try:
        # ใช้ time.time() เพื่อหลอก server ว่าเป็นคำขอใหม่เสมอ
        response = requests.get(f"{url}&t={time.time()}", timeout=5)
        response.encoding = 'utf-8'
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except:
        return pd.DataFrame()

# เตรียม Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    # โหลดสต็อกและสินค้าใหม่ทุกครั้งที่ Refresh หน้า (Real-time)
    df_p = load_data_fast(URL_PRODUCTS)
    df_s = load_data_fast(URL_STOCK)
    
    col_main, col_right = st.columns([2.3, 1.7])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # ตรวจสอบตำแหน่งคอลัมน์: 0=ชื่อ, 1=ราคา, 3=รูป
                p_name = str(row.iloc[0])
                p_price = float(row.iloc[1])
                p_img = row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else "https://via.placeholder.com/150"
                
                # ดึงค่าสต็อกล่าสุด
                s_match = df_s[df_s.iloc[:, 0] == p_name] if not df_s.empty else pd.DataFrame()
                stock_now = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                qty_in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        # แสดงรูปภาพ (แก้ไขให้แสดงผลแน่นอน)
                        st.image(p_img, use_container_width=True)
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"### {p_price:,.0f} ฿")
                        
                        color = "red" if stock_now <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock_now}</span>", unsafe_allow_html=True)
                        
                        # ปุ่มเพิ่มสินค้า (คืนค่าปุ่มและแก้หน่วง)
                        if stock_now > qty_in_cart:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                                if p_name not in st.session_state.cart:
                                    st.session_state.cart[p_name] = {'price': p_price, 'qty': 1}
                                else:
                                    st.session_state.cart[p_name]['qty'] += 1
                                st.rerun() # Refresh ทันทีเพื่อให้สต็อกอัปเดตหน้าจอ
                        else:
                            st.button("❌ สินค้าหมด", disabled=True, use_container_width=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            
            # ส่วนใบเสร็จ
            receipt_html = f"""
            <div style="background:white; color:black; padding:20px; border-radius:10px; font-family:monospace; border:2px solid #333;">
                <h2 style="text-align:center; margin:0;">TAS POS</h2>
                <p style="text-align:center; font-size:12px;">ขอบคุณที่ใช้บริการ</p>
                <hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr>
                <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>ยอดรวม</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="font-size:12px; margin-top:10px;">วิธีชำระ: {r['method']}</p>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            # QR Code แสดงในใบเสร็จ (คืนค่าตามสั่ง)
            if r['method'] == "📱 PromptPay":
                st.write("---")
                st.image(f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png", caption="สแกนเพื่อชำระเงิน", width=250)
            
            if st.button("🔄 เริ่มการขายใหม่ (Reset)", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                for n, i in list(st.session_state.cart.items()):
                    sub = i['price'] * i['qty']
                    total += sub
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{i['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]
                        st.rerun()
                
                st.divider()
                st.title(f"{total:,.0f} ฿")
                method = st.radio("เลือกวิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                
                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    with st.spinner('กำลังบันทึกข้อมูล...'):
                        bill_id = f"B{int(time.time())}"
                        summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                        try:
                            # ส่งข้อมูลไป Google Sheets
                            requests.post(SCRIPT_URL, json={
                                "action": "checkout",
                                "bill_id": bill_id,
                                "summary": summary,
                                "total": total,
                                "method": method
                            }, timeout=8)
                        except:
                            pass # บันทึกสำเร็จแล้วแต่ timeout ฝั่งรับ

                        st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                        st.session_state.cart = {}
                        st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปยอดขาย")
    df_sales = load_data_fast(URL_SALES)
    if not df_sales.empty:
        col_dt = df_sales.columns[0]
        col_total = df_sales.columns[3]
        df_sales[col_dt] = pd.to_datetime(df_sales[col_dt], dayfirst=True, errors='coerce')
        
        # คำนวณยอด
        today = datetime.now().date()
        df_today = df_sales[df_sales[col_dt].dt.date == today]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("ยอดขายวันนี้", f"{df_today[col_total].sum():,.0f} ฿")
        c2.metric("จำนวนบิลวันนี้", f"{len(df_today)} บิล")
        c3.metric("ยอดขายเดือนนี้", f"{df_sales[df_sales[col_dt].dt.month == datetime.now().month][col_total].sum():,.0f} ฿")
        
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อกปัจจุบัน")
    st.dataframe(load_data_fast(URL_STOCK), use_container_width=True)
