import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS สูตรลับ: บังคับ Grid และ รูปภาพให้เท่ากัน 100%
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* สร้างกล่องสินค้าสีเข้ม */
    .product-container {
        background-color: #1a1c24;
        padding: 10px;
        border-radius: 15px;
        border: 1px solid #333;
        margin-bottom: 20px;
        text-align: center;
    }

    /* กล่องสีขาวล็อกขนาดรูปภาพ (สำคัญมาก) */
    .img-frame {
        width: 100%;
        height: 180px; /* ล็อกความสูงเท่ากันทุกใบ */
        background-color: white; /* พื้นหลังสีขาวช่วยให้รูปเด่นและดูเท่ากัน */
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin-bottom: 12px;
    }

    .img-frame img {
        max-width: 90%;
        max-height: 90%;
        object-fit: contain; /* ป้องกันรูปบิดเบี้ยว */
    }

    .product-name {
        color: white !important;
        font-weight: bold;
        height: 2.5em; /* ล็อกไว้ 2 บรรทัด */
        overflow: hidden;
        margin-bottom: 5px;
        font-size: 1.05em;
    }

    .product-price {
        color: #f1c40f !important;
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
    }

    .stButton>button {
        width: 100%;
        background-color: #28a745;
        color: white;
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* ปรับแต่งตัวหนังสือส่วนอื่นๆ */
    h1, h2, h3, p, span, label, .stMarkdown { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

st.title("🏪 TAS PROFESSIONAL POS")

df_products = load_products()
col1, col2 = st.columns([3.2, 1.2])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # แสดงผลด้วย HTML เพื่อการควบคุมที่แม่นยำ
                st.markdown(f"""
                    <div class="product-container">
                        <div class="img-frame">
                            <img src="{row['Image_URL']}">
                        </div>
                        <div class="product-name">{row['Name']}</div>
                        <div class="product-price">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # ปุ่มกดวางต่อท้าย container
                if st.button(f"เลือก {row['Name']}", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.info("กำลังโหลดสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.write(f"⬜ {item['Name']} : {item['Price']:,} ฿")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันชำระเงิน", type="primary", use_container_width=True):
            bill_id = "B" + pd.Timestamp.now().strftime("%y%m%d%H%M%S")
            items_str = ", ".join(df_cart['Name'].tolist())
            final_url = f"{API_URL}?bill_id={bill_id}&items={items_str}&total={total}&payment_type={method}"
            
            try:
                requests.get(final_url, timeout=0.001)
            except: pass 
            
            st.session_state.last_bill = {"total": total, "type": method}
            st.session_state.cart = []
            st.rerun()

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกยอด {last['total']:,} ฿ สำเร็จ!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("เลือกสินค้าเพื่อเพิ่มลงตะกร้า")
