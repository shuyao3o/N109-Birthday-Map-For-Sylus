import base64
import time
import html 
import streamlit as st
import streamlit.components.v1 as components
from pyecharts import options as opts
from pyecharts.charts import Geo
from pyecharts.globals import ChartType, ThemeType
from supabase import create_client, Client
import random

# ==========================================
# 🔴 Supabase 密钥配置
# ==========================================
SUPABASE_URL = "https://yqggxqllcutqatwjxmyx.supabase.co"
SUPABASE_KEY = "sb_publishable_66sM5garleFYSyoxfoBizg_WeoUpnAy"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

if 'last_coord' not in st.session_state:
    st.session_state['last_coord'] = None

# ==========================================
# 🦅 N109区专属离线坐标矩阵
# ==========================================
CITY_COORDS = {
    "临空市": (119.00, 32.00), "伦敦": (-0.12, 51.50), "纽约": (-74.00, 40.71),
    "东京": (139.69, 35.68), "巴黎": (2.35, 48.85), "首尔": (126.97, 37.56),
    "北京": (116.40, 39.90), "上海": (121.47, 31.23), "广州": (113.26, 23.12),
    "深圳": (114.05, 22.52), "成都": (104.06, 30.67), "重庆": (106.50, 29.53),
    "杭州": (120.15, 30.28), "武汉": (114.30, 30.59), "西安": (108.94, 34.26),
    "南京": (118.79, 32.04), "香港": (114.16, 22.28), "台北": (121.56, 25.03)
}

def get_coordinates(city_name):
    city_lower = city_name.strip().lower()
    if city_lower.endswith("市") and len(city_lower) > 1:
        city_lower = city_lower[:-1]
    if city_lower in CITY_COORDS:
        return CITY_COORDS[city_lower]
    return None, None

# ==========================================
# 🎨 UI 定制
# ==========================================
st.set_page_config(page_title="N109区点亮计划", layout="wide", initial_sidebar_state="collapsed")

def set_bg_image(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: linear-gradient(rgba(10, 5, 16, 0.8), rgba(10, 5, 16, 0.85)), url(data:image/jpeg;base64,{encoded_string}) !important;
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        pass

set_bg_image("bg.jpg")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [class*="css"] {font-family: 'Noto Sans SC', sans-serif;}
    h1, h2, h3 {font-family: 'Orbitron', 'Noto Sans SC', sans-serif !important; color: #ff004d !important; text-shadow: 0 0 15px rgba(255, 0, 77, 0.8); letter-spacing: 1px;}
    .stApp {background: linear-gradient(135deg, #050208 0%, #0a0510 50%, #1a050a 100%); color: #e0d8e0;}
    [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, [data-baseweb="select"] > div {
        background-color: rgba(21, 10, 31, 0.8) !important; color: #ffb3c6 !important; border-color: #4a1525 !important;
    }
    [data-testid="stFormSubmitButton"] button, .stButton>button {
        background-color: rgba(20, 5, 15, 0.8) !important; color: #ff004d !important; border: 1px solid #ff004d !important; 
        box-shadow: 0 0 10px rgba(255, 0, 77, 0.3) inset, 0 0 10px rgba(255, 0, 77, 0.3) !important; 
        transition: all 0.3s ease-in-out !important; font-weight: bold !important; border-radius: 4px !important; 
    }
    [data-testid="stFormSubmitButton"] button:hover, .stButton>button:hover {
        background-color: #ff004d !important; color: #ffffff !important; box-shadow: 0 0 30px #ff004d !important; 
    }
    .signal-card {background-color: rgba(21, 10, 31, 0.8); border-left: 4px solid #ff004d; padding: 15px; margin-bottom: 15px; border-radius: 0 8px 8px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.5);}
    .signal-header {color: #c0f9ff; font-weight: bold; font-size: 1.1em; margin-bottom: 5px;} 
    .signal-city {color: #68aacd; font-size: 0.85em; margin-left: 10px;} 
    .signal-msg {color: #e0d8e0; font-size: 0.95em; line-height: 1.4;}
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🏍️ N109区点亮计划")

# 🦅 BGM
try:
    with open("bgm.mp3", "rb") as f:
        st.audio(f.read(), format="audio/mpeg", loop=True)
except:
    pass

# ⚠️ 优化1：加入缓存，每60秒更新一次数据，且只拉取1000条，不再卡顿！
@st.cache_data(ttl=60)
def fetch_data():
    try:
        response = supabase.table("blessings").select("*").limit(1000).execute()
        data = response.data
        if data: data.reverse()
        return data
    except Exception as e:
        return []

def save_data(name, city, lon, lat, message):
    try:
        data = {"name": name, "city": city, "longitude": float(lon), "latitude": float(lat), "message": message}
        supabase.table("blessings").insert(data).execute()
        fetch_data.clear() # 写入新数据后清空缓存
        return True
    except Exception as e:
        return False

# ⚠️ 优化2：地图点位精简，普通点位取消呼吸特效，保护浏览器
def render_map(data_list):
    geo = (
        Geo(init_opts=opts.InitOpts(width="100%", height="500px", theme=ThemeType.DARK, bg_color="transparent"))
        .add_schema(maptype="world", itemstyle_opts=opts.ItemStyleOpts(area_color="#374260", border_color="#68aacd"))
    )
    
    normal_pair = []
    highlight_pair = []
    last_coord = st.session_state.get('last_coord')

    if data_list:
        display_data = data_list[:200] # 最多同时渲染200个点，防止页面崩溃
        for i, item in enumerate(display_data):
            lon = item.get('longitude', 0)
            lat = item.get('latitude', 0)
            uid = f"{item.get('city', 'U')}_{i}"
            geo.add_coordinate(uid, lon, lat)
            
            if last_coord and abs(lon - last_coord[0]) < 0.0001 and abs(lat - last_coord[1]) < 0.0001:
                highlight_pair.append((uid, 1))
            else:
                normal_pair.append((uid, 1))
                
        if normal_pair:
            # 普通点改为 SCATTER（无耗能动画）
            geo.add("定位", normal_pair, type_=ChartType.SCATTER, symbol_size=5, color="#ff004d", label_opts=opts.LabelOpts(is_show=False))
        if highlight_pair:
            # 只有自己刚刚提交的点有呼吸动画
            geo.add("🎯 锁定", highlight_pair, type_=ChartType.EFFECT_SCATTER, symbol_size=18, color="#C0C0C0", effect_opts=opts.EffectOpts(is_show=True, scale=6), label_opts=opts.LabelOpts(is_show=False))
            
    geo.set_global_opts(title_opts=opts.TitleOpts(title="🎯 全球雷达响应", pos_left="center", title_textstyle_opts=opts.TextStyleOpts(color="#ff004d")))
    return geo.render_embed()

col1, col2 = st.columns([2, 1])
blessings_data = fetch_data()

with col1:
    st.markdown("### 🔴 为你闪烁的满城夜色")
    if st.button("🔄 重新扫描雷达"): st.rerun()
    components.html(render_map(blessings_data), height=550, scrolling=False)

with col2:
    st.markdown("### 📡 接入N109区频段")
    with st.form("blessing_form"):
        name = st.text_input("猎人代号")
        city = st.text_input("所在城市 (如: 上海, 伦敦)")
        
        col_lon_dir, col_lon_val = st.columns([1, 2])
        with col_lon_dir: lon_dir = st.selectbox("经度", ["东经 (E)", "西经 (W)"])
        with col_lon_val: manual_lon_abs = st.number_input("经度数值", value=0.00, format="%.2f")
            
        col_lat_dir, col_lat_val = st.columns([1, 2])
        with col_lat_dir: lat_dir = st.selectbox("纬度", ["北纬 (N)", "南纬 (S)"])
        with col_lat_val: manual_lat_abs = st.number_input("纬度数值", value=0.00, format="%.2f")
            
        message = st.text_area("你想对秦彻说的话")
        
        # 按钮布局
        submitted = st.form_submit_button("锁定并点亮坐标", use_container_width=True)
        fireworks_clicked = st.form_submit_button("🪶 想看礼花吗", use_container_width=True)

    if submitted:
        if not name or not city:
            st.warning("⚠️ 代号和城市不能为空哦！")
        else:
            final_lon, final_lat = get_coordinates(city)
            if final_lon is None and final_lat is None:
                final_lon = manual_lon_abs if "东经" in lon_dir else -manual_lon_abs
                final_lat = manual_lat_abs if "北纬" in lat_dir else -manual_lat_abs
            
            if final_lon != 0.0 or final_lat != 0.0:
                final_lon += random.uniform(-0.05, 0.05)
                final_lat += random.uniform(-0.05, 0.05)
                if save_data(name, city, final_lon, final_lat, message):
                    st.session_state['last_coord'] = (final_lon, final_lat)
                    st.success("🛰️ 信号接入成功！雷达正在重启...")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.error("❌ 未收录该城市！请手动输入经纬度！")

    # ⚠️ 优化3：点击礼花按钮，直接跳转到新页面，完美解决网页不弹礼花的问题！
    if fireworks_clicked:
        st.switch_page("pages/fireworks.py")

st.markdown("---")
st.markdown('### 截获的猎人小姐信号 (实时)')
if blessings_data:
    cols = st.columns(3)
    for i, item in enumerate(blessings_data[:12]):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="signal-card">
                <div class="signal-header">{item.get('name', '未知')} <span class="signal-city">📍 {item.get('city', '未知')}</span></div>
                <div class="signal-msg">"{item.get('message', '加密信号...')}"</div>
            </div>""", unsafe_allow_html=True)
