import streamlit as st
import pandas as pd
import requests
from io import StringIO

# 1. ลิงก์ใหม่ (Force CSV)
# ผมใช้ลิงก์โดยตรงเพื่อให้ระบบไม่สับสน
STOCK_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 2. ฟังก์ชันดึงข้อมูลแบบใหม่ (ข้ามระบบ Cache ทั้งหมด)
def get_fresh_data():
    try:
        # ใช้ requests ดึงข้อมูลดิบเพื่อความชัวร์
        response = requests.get(STOCK_CSV_URL)
        response.encoding = 'utf-8'
        data = StringIO(response.text)
        new_df = pd.read_csv(data)
        
        # จัดการชื่อคอลัมน์
        new_df.columns = new_df.columns.str.strip()
        new_df['Price'] = pd.to_numeric(new_df['Price'], errors='coerce').fillna(0)
        new_df['Stock'] = pd.to_numeric(new_df['Stock'], errors='coerce').fillna(0).astype(int)
        return new_df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# 3. โหลดข้อมูล
df_pos = get_fresh_data()

# 4. แสดงผลหน้าจอ
st.title("🏪 TAS POS SYSTEM")

# ถ้าดึงข้อมูลได้สำเร็จ
if not df_pos.empty:
    st.success("✅ เชื่อมต่อข้อมูลสำเร็จ!")
    
    # ตรวจสอบว่าในไฟล์มีข้อมูลจริงไหม
    if len(df_pos) > 0:
        c1, c2 = st.columns([3, 2])
        
        with c1:
            st.subheader("📦 สินค้าพร้อมขาย")
            grid = st.columns(3)
            for i, row in df_pos.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#262730; border:1px solid #444; padding:15px; border-radius:10px; text-align:center;">
                            <img src="{row['Image_URL']}" style="height:100px; width:100px; object-fit:contain; background:white; border-radius:8px;">
                            <h4 style="margin:10px 0;">{row['Name']}</h4>
                            <h3 style="color:#f1c40f;">{row['Price']:,} ฿</h3>
                            <p style="color:#2ecc71;">สต็อกคงเหลือ: {row['Stock']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        st.button(f"เลือก {row['Name']}", key=f"id_{i}")
                    else:
                        st.button("สินค้าหมด", key=f"id_{i}", disabled=True)
        
        with c2:
            st.subheader("🛒 สรุปรายการ")
            st.info("ระบบกำลังเตรียมความพร้อม...")
            
    else:
        st.warning("ดึงข้อมูลได้แล้ว แต่ไม่พบรายการสินค้าในชีต Stock (ลองเช็คแถวที่ 2 เป็นต้นไป)")
else:
    st.error("❌ ไม่สามารถดึงข้อมูลได้ กรุณากดปุ่ม Reboot ในหน้า Manage App")

# ปุ่มรีเซ็ตด่วน
if st.sidebar.button("🔄 บังคับโหลดใหม่"):
    st.rerun()
