import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="Ultimate POS System Pro", layout="wide", initial_sidebar_state="expanded")

# --- CORE FUNCTIONS: DATA MANAGEMENT ---
def normalize_dataframe(df):
    """ ปรับแต่งโครงสร้าง DataFrame ให้มาตรฐานเพื่อป้องกัน KeyError """
    if df is not None and not df.empty:
        # ลบช่องว่างหัว-ท้าย และปรับเป็นตัวพิมพ์เล็กทั้งหมด
        df.columns = [str(c).strip().lower() for c in df.columns]
        # จัดการข้อมูลที่เป็น NaN ให้เป็นค่าว่างหรือ 0
        df = df.fillna('')
    return df

@st.cache_data(ttl=2) # ลดเวลา Cache เพื่อให้สต็อกอัปเดตไวขึ้น
def fetch_all_remote_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            return {
                "products": normalize_dataframe(pd.DataFrame(res_json.get('products', []))),
                "stock": normalize_dataframe(pd.DataFrame(res_json.get('stock', [])))
            }
    except Exception as e:
        st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {e}")
    return None

def post_transaction(payload):
    """ ส่งข้อมูลการขายและอัปเดตสต็อก """
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        return res.status_code == 200
    except Exception as e:
        st.error(f"❌ ระบบส่งข้อมูลขัดข้อง: {e}")
        return False

# --- SESSION INITIALIZATION ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'app_data' not in st.session_state: st.session_state.app_data = fetch_all_remote_data()
if 'show_receipt' not in st.session_state: st.session_state.show_receipt = False
if 'last_bill' not in st.session_state: st.session_state.last_bill = {}

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("💎 PREMIUM POS")
    st.markdown("---")
    menu = st.radio("เมนูหลักทางการ", ["🛒 ระบบการขาย", "📊 วิเคราะห์ & รายงาน", "📦 จัดการคลังสินค้า"], index=0)
    st.markdown("---")
    if st.button("🔄 รีเฟรชฐานข้อมูล", use_container_width=True):
        st.session_state.app_data = fetch_all_remote_data()
        st.rerun()

# --- MAIN LOGIC ---
if st.session_state.app_data:
    df_p = st.session_state.app_data['products']
    df_s = st.session_state.app_data['stock']

    # --- PAGE: SALE SYSTEM ---
    if menu == "🛒 ระบบการขาย":
        col_main, col_cart = st.columns([2, 1])

        with col_main:
            st.subheader("📦 เลือกสินค้า")
            search_query = st.text_input("🔍 ค้นหาชื่อสินค้า...", placeholder="พิมพ์ชื่อสินค้าที่ต้องการ")
            
            # กรองสินค้าตามชื่อ
            if search_query:
                display_prods = df_p[df_p['name'].astype(str).str.contains(search_query, case=False)]
            else:
                display_prods = df_p

            if display_prods.empty:
                st.warning("⚠️ ไม่พบข้อมูลสินค้า")
            else:
                grid = st.columns(3)
                for i, (idx, row) in enumerate(display_prods.iterrows()):
                    with grid[i % 3]:
                        with st.container(border=True):
                            p_id = str(row['id']).strip()
                            # ป้องกัน KeyError โดยการเช็ค id ในสต็อกอย่างละเอียด
                            s_match = df_s[df_s['id'].astype(str).str.strip() == p_id]
                            stock_qty = int(s_match['qty'].values[0]) if not s_match.empty else 0
                            
                            st.markdown(f"**{row['name']}**")
                            st.markdown(f"## ฿{float(row['price']):,.2f}")
                            
                            if stock_qty <= 5:
                                st.error(f"คงเหลือ: {stock_qty} (ใกล้หมด!)")
                            else:
                                st.caption(f"คงเหลือในสต็อก: {stock_qty}")

                            if st.button("➕ เพิ่มเข้าตะกร้า", key=f"btn_{p_id}", disabled=(stock_qty <= 0), use_container_width=True):
                                if p_id in st.session_state.cart:
                                    st.session_state.cart[p_id]['qty'] += 1
                                else:
                                    st.session_state.cart[p_id] = {'name': row['name'], 'price': float(row['price']), 'qty': 1}
                                st.toast(f"เพิ่ม {row['name']} แล้ว")
                                st.rerun()

        with col_cart:
            st.subheader("🛒 รายการในตะกร้า")
            grand_total = 0
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                for p_id, item in list(st.session_state.cart.items()):
                    with st.container(border=True):
                        sub_total = item['price'] * item['qty']
                        grand_total += sub_total
                        st.markdown(f"**{item['name']}**")
                        st.markdown(f"ยอด: ฿{sub_total:,.2f}")
                        
                        c1, c2, c3 = st.columns([1,1,1])
                        if c1.button("➖", key=f"minus_{p_id}"):
                            st.session_state.cart[p_id]['qty'] -= 1
                            if st.session_state.cart[p_id]['qty'] <= 0: del st.session_state.cart[p_id]
                            st.rerun()
                        c2.markdown(f"### {item['qty']}")
                        if c3.button("➕", key=f"plus_{p_id}"):
                            st.session_state.cart[p_id]['qty'] += 1
                            st.rerun()

                st.divider()
                st.metric("ยอดชำระสุทธิ", f"฿{grand_total:,.2f}")
                pay_method = st.radio("เลือกช่องทางชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("💳 ยืนยันการชำระเงิน", type="primary", use_container_width=True):
                    if grand_total > 0:
                        now = datetime.now()
                        # สร้างรายการสินค้าในรูปแบบที่อ่านง่ายสำหรับ Sheet
                        items_summary = ", ".join([f"{v['name']}({v['qty']})" for v in st.session_state.cart.values()])
                        
                        bill_payload = {
                            "date": now.strftime("%d/%m/%Y"),
                            "time": now.strftime("%H:%M:%S"),
                            "bill_no": f"POS{int(now.timestamp())}",
                            "total": grand_total,
                            "method": pay_method,
                            "items": items_summary
                        }

                        final_payload = {
                            "action": "recordSale",
                            "data": list(bill_payload.values()), # ส่งเฉพาะ List ของข้อมูลให้ตรงคอลัมน์
                            "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                        }

                        if post_transaction(final_payload):
                            st.session_state.last_bill = {**bill_payload, "raw_cart": st.session_state.cart.copy()}
                            st.session_state.show_receipt = True
                            st.session_state.cart = {}
                            st.session_state.app_data = fetch_all_remote_data()
                            st.rerun()

    # --- SYSTEM: RECEIPT DIALOG (ห้ามหาย) ---
    if st.session_state.show_receipt:
        @st.dialog("🧾 ใบเสร็จรับเงินอิเล็กทรอนิกส์")
        def show_receipt_dialog():
            b = st.session_state.last_bill
            st.markdown(f"### เลขที่บิล: {b['bill_no']}")
            st.write(f"📅 วันที่: {b['date']} | ⏰ เวลา: {b['time']}")
            st.divider()
            
            for pid, item in b['raw_cart'].items():
                st.write(f"{item['name']} x{item['qty']} = ฿{item['price']*item['qty']:,.2f}")
            
            st.divider()
            st.markdown(f"## ยอดรวมทั้งสิ้น: ฿{b['total']:,.2f}")
            st.markdown(f"**การชำระเงิน:** {b['method']}")

            if b['method'] == "พร้อมเพย์":
                qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://promptpay.io/{PROMPTPAY_ID}/{b['total']}"
                st.image(qr_api, caption=f"พร้อมเพย์: {PROMPTPAY_ID}", width=250)

            st.info("💡 สามารถกดปุ่มด้านล่างเพื่อพิมพ์หรือบันทึก")
            if st.button("🖨️ พิมพ์ใบเสร็จ (Print)", use_container_width=True):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            
            if st.button("เสร็จสิ้นและปิด", use_container_width=True):
                st.session_state.show_receipt = False
                st.rerun()
        show_receipt_dialog()

    # --- PAGE: REPORT ---
    elif menu == "📊 วิเคราะห์ & รายงาน":
        st.subheader("📈 สรุปผลการดำเนินงาน")
        st.write("ระบบทำการบันทึกข้อมูลเข้า Google Sheets อัตโนมัติ")
        st.info("คอลัมน์ในแผ่น Sales: วันที่ | เวลา | เลขที่บิล | ยอดเงิน | วิธีชำระเงิน | รายการสินค้า")
        # ส่วนนี้สามารถดึงข้อมูล Sales มาแสดงเป็นกราฟได้ในอนาคต

    # --- PAGE: STOCK ---
    elif menu == "📦 จัดการคลังสินค้า":
        st.subheader("📦 ตรวจสอบรายการสินค้าคงคลัง")
        # แสดงตารางสต็อกพร้อมการตกแต่ง
        st.dataframe(
            df_s, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "id": "รหัสสินค้า",
                "name": "ชื่อสินค้า",
                "qty": st.column_config.NumberColumn("คงเหลือ", format="%d ชิ้น")
            }
        )
