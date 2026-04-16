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

SUPABASE_URL = "https://yqggxqllcutqatwjxmyx.supabase.co"
SUPABASE_KEY = "sb_publishable_66sM5garleFYSyoxfoBizg_WeoUpnAy"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

if 'last_coord' not in st.session_state:
    st.session_state['last_coord'] = None

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
    return CITY_COORDS.get(city_lower, (None, None))

# 只拉地图需要的坐标字段，最新200条 + 随机300条（共500条上限）
@st.cache_data(ttl=60)
def fetch_map_data():
    try:
        # 最新200条
        r1 = supabase.table("blessings").select("longitude,latitude,city").order("id", desc=True).limit(200).execute()
        # 随机偏移抽取300条（用offset随机化）
        count_r = supabase.table("blessings").select("id", count="exact").execute()
        total = count_r.count or 0
        offset = random.randint(0, max(0, total - 300)) if total > 300 else 0
        r2 = supabase.table("blessings").select("longitude,latitude,city").order("id").range(offset, offset + 299).execute()
        combined = {(d['longitude'], d['latitude']): d for d in (r2.data or []) + (r1.data or [])}
        return list(combined.values())
    except Exception as e:
        st.error(f"⚠️ 地图数据读取失败: {e}")
        return []

# 只拉瀑布流需要的12条
@st.cache_data(ttl=30)
def fetch_feed_data():
    try:
        r = supabase.table("blessings").select("name,city,message").order("id", desc=True).limit(12).execute()
        return r.data or []
    except Exception as e:
        st.error(f"⚠️ 信号读取失败: {e}")
        return []

def save_data(name, city, lon, lat, message):
    try:
        supabase.table("blessings").insert({
            "name": name, "city": city,
            "longitude": float(lon), "latitude": float(lat), "message": message
        }).execute()
        return True
    except Exception as e:
        st.error(f"⚠️ 数据库写入失败: {e}")
        return False

def get_random_blessing():
    try:
        count_r = supabase.table("blessings").select("id", count="exact").execute()
        total = count_r.count or 0
        if total == 0:
            return None
        offset = random.randint(0, total - 1)
        r = supabase.table("blessings").select("message,city").range(offset, offset).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None

def render_map(data_list):
    geo = (
        Geo(init_opts=opts.InitOpts(width="100%", height="500px", theme=ThemeType.DARK, bg_color="transparent"))
        .add_schema(
            maptype="world",
            itemstyle_opts=opts.ItemStyleOpts(area_color="#374260", border_color="#68aacd"),
            emphasis_itemstyle_opts=opts.ItemStyleOpts(area_color="#c0f9ff")
        )
    )
    normal_pair, highlight_pair = [], []
    last_coord = st.session_state.get('last_coord')
    for i, item in enumerate(data_list):
        lon, lat = item.get('longitude', 0), item.get('latitude', 0)
        uid = f"{item.get('city','?')}_{i}"
        geo.add_coordinate(uid, lon, lat)
        if last_coord and abs(lon - last_coord[0]) < 0.0001 and abs(lat - last_coord[1]) < 0.0001:
            highlight_pair.append((uid, 1))
        else:
            normal_pair.append((uid, 1))
    if normal_pair:
        geo.add("信号点", normal_pair, type_=ChartType.EFFECT_SCATTER, symbol_size=8, color="#ff004d",
                effect_opts=opts.EffectOpts(is_show=True, brush_type="stroke", scale=3, period=2.5),
                label_opts=opts.LabelOpts(is_show=False))
    if highlight_pair:
        geo.add("专属锁定", highlight_pair, type_=ChartType.EFFECT_SCATTER, symbol_size=18, color="#C0C0C0",
                effect_opts=opts.EffectOpts(is_show=True, brush_type="stroke", scale=6, period=1.5),
                label_opts=opts.LabelOpts(is_show=False))
    geo.set_global_opts(title_opts=opts.TitleOpts(title="全球雷达响应", pos_left="center",
                        title_textstyle_opts=opts.TextStyleOpts(color="#ff004d")))
    return geo.render_embed()

# ==================== UI ====================
st.set_page_config(page_title="N109区点亮计划", layout="wide", initial_sidebar_state="collapsed")

def set_bg_image(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(f"""<style>.stApp {{
            background: linear-gradient(rgba(10,5,16,0.8),rgba(10,5,16,0.85)),
            url(data:image/jpeg;base64,{encoded}) !important;
            background-size:cover !important; background-position:center !important;
            background-attachment:fixed !important;
        }}</style>""", unsafe_allow_html=True)
    except Exception:
        pass

set_bg_image("bg.jpg")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans SC',sans-serif;}
h1,h2,h3{font-family:'Orbitron','Noto Sans SC',sans-serif !important;color:#ff004d !important;text-shadow:0 0 15px rgba(255,0,77,0.8);letter-spacing:1px;}
.stApp{background:linear-gradient(135deg,#050208 0%,#0a0510 50%,#1a050a 100%);color:#e0d8e0;}
[data-baseweb="input"],[data-baseweb="input"]>div,[data-baseweb="input"] input,
[data-baseweb="textarea"],[data-baseweb="textarea"]>div,[data-baseweb="textarea"] textarea,
[data-baseweb="select"]>div{background-color:rgba(21,10,31,0.8) !important;color:#ffb3c6 !important;-webkit-text-fill-color:#ffb3c6 !important;border-color:#4a1525 !important;}
[data-testid="stFormSubmitButton"] button,.stButton>button{background-color:rgba(20,5,15,0.8) !important;color:#ff004d !important;border:1px solid #ff004d !important;box-shadow:0 0 10px rgba(255,0,77,0.3) inset,0 0 10px rgba(255,0,77,0.3) !important;transition:all 0.3s ease-in-out !important;font-weight:bold !important;border-radius:4px !important;text-transform:uppercase !important;letter-spacing:2px !important;}
[data-testid="stFormSubmitButton"] button:hover,.stButton>button:hover{background-color:#ff004d !important;color:#ffffff !important;box-shadow:0 0 30px #ff004d,0 0 10px #ffffff inset !important;transform:scale(1.02) !important;}
.signal-card{background-color:rgba(21,10,31,0.8);border-left:4px solid #ff004d;padding:15px;margin-bottom:15px;border-radius:0 8px 8px 0;box-shadow:0 2px 10px rgba(0,0,0,0.5);}
.signal-header{color:#c0f9ff;font-weight:bold;font-size:1.1em;margin-bottom:5px;}
.signal-city{color:#68aacd;font-size:0.85em;margin-left:10px;}
@keyframes signalBreathe{0%{opacity:0.5;}50%{opacity:1.0;text-shadow:0 0 10px rgba(192,249,255,0.4);}100%{opacity:0.5;}}
@keyframes dotBlink{0%{opacity:1;box-shadow:0 0 10px #ff004d;}50%{opacity:0.2;}100%{opacity:1;box-shadow:0 0 10px #ff004d;}}
.signal-msg{color:#e0d8e0;font-size:0.95em;line-height:1.4;animation:signalBreathe 4s infinite ease-in-out;}
.live-dot{display:inline-block;width:12px;height:12px;background-color:#ff004d;border-radius:50%;margin-right:10px;animation:dotBlink 1.5s infinite ease-in-out;}
[data-testid="stAudio"]{background:linear-gradient(90deg,rgba(255,0,77,0.15) 0%,rgba(21,10,31,0.6) 50%,rgba(192,249,255,0.15) 100%) !important;border:1px solid rgba(255,0,77,0.4) !important;border-radius:8px !important;padding:8px !important;margin-bottom:20px;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
.stTextInput label p,.stTextArea label p,.stNumberInput label p,.stSelectbox label p{color:#c0f9ff !important;text-shadow:0 0 8px rgba(192,249,255,0.6) !important;font-weight:bold !important;letter-spacing:1px !important;}
@media(max-width:768px){h1{font-size:1.8rem !important;text-align:center;}h3{font-size:1.3rem !important;text-align:center;}.stApp{background-attachment:scroll !important;}}
</style>""", unsafe_allow_html=True)

st.title("N109区点亮计划")

try:
    with open("bgm.mp3", "rb") as f:
        audio_bytes = f.read()
    st.audio(audio_bytes, format="audio/mpeg", loop=True)
    components.html("""<script>
        const set = () => { try { window.parent.document.querySelectorAll('audio').forEach(a=>a.volume=0.5); } catch(e){} };
        setTimeout(set,100); setTimeout(set,500); setTimeout(set,1000);
    </script>""", height=0, width=0)
except Exception:
    pass

col1, col2 = st.columns([2, 1])
map_data = fetch_map_data()

with col1:
    st.markdown("### 为你闪烁的满城夜色")
    st.markdown("<span style='color:#68aacd;font-size:0.85em;'>*信号微弱时雷达可能隐匿，请点击下方按钮重连。*</span>", unsafe_allow_html=True)
    if st.button("重新扫描 N109 区雷达"):
        st.cache_data.clear()
        st.rerun()
    components.html(render_map(map_data), height=550, scrolling=False)

with col2:
    st.markdown("### 接入N109区频段")
    with st.form("blessing_form"):
        name = st.text_input("猎人代号")
        city = st.text_input("所在城市 (如: 上海, 伦敦, 纽约)")
        st.markdown("<span style='color:#885566;font-size:0.85em;'>*非省会城市请手动输入经纬度*</span>", unsafe_allow_html=True)
        col_ld, col_lv = st.columns([1, 2])
        with col_ld: lon_dir = st.selectbox("经度方向", ["东经 (E)", "西经 (W)"])
        with col_lv: manual_lon = st.number_input("经度数值", value=0.00, format="%.2f", min_value=0.0, max_value=180.0)
        col_ad, col_av = st.columns([1, 2])
        with col_ad: lat_dir = st.selectbox("纬度方向", ["北纬 (N)", "南纬 (S)"])
        with col_av: manual_lat = st.number_input("纬度数值", value=0.00, format="%.2f", min_value=0.0, max_value=90.0)
        message = st.text_area("你想对秦彻说的话")
        c1, c2 = st.columns(2)
        with c1: submitted = st.form_submit_button("锁定并点亮坐标", use_container_width=True)
        with c2: fireworks_clicked = st.form_submit_button("想看礼花吗", use_container_width=True)

        if submitted:
            if not name or not city:
                st.warning("代号和城市不能为空！")
            else:
                coords = get_coordinates(city)
                final_lon, final_lat = coords if coords != (None, None) else (None, None)
                if final_lon is None:
                    if manual_lon != 0.00 or manual_lat != 0.00:
                        final_lon = manual_lon if lon_dir == "东经 (E)" else -manual_lon
                        final_lat = manual_lat if lat_dir == "北纬 (N)" else -manual_lat
                if final_lon is not None and final_lat is not None:
                    final_lon = float(final_lon) + random.uniform(-0.05, 0.05)
                    final_lat = float(final_lat) + random.uniform(-0.05, 0.05)
                    if save_data(name, city, final_lon, final_lat, message):
                        st.session_state['last_coord'] = (final_lon, final_lat)
                        st.cache_data.clear()
                        st.markdown(f"""<div style="background:rgba(21,10,31,0.8);border:1px solid #c0f9ff;border-left:4px solid #c0f9ff;padding:15px;border-radius:4px;box-shadow:0 0 15px rgba(192,249,255,0.2);margin-bottom:15px;">
                            <span style="color:#c0f9ff;font-weight:bold;">信号接入成功！</span><br>
                            <span style="color:#e0d8e0;">猎人 <span style="color:#ff004d;font-weight:bold;">{name}</span>，坐标已锁定！</span>
                        </div>""", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error(f"未收录【{city}】，请手动输入经纬度！")

        if fireworks_clicked:
            lucky = get_random_blessing()
            if lucky:
                safe_msg = html.escape(lucky.get('message', '')).replace('\n', '<br>')
                safe_city = html.escape(lucky.get('city', '未知坐标'))
                components.html(f"""<script>
                    const pd = window.parent.document;
                    const old = pd.getElementById('fw'); if(old) old.remove();
                    const ov = pd.createElement('div');
                    ov.id='fw';
                    ov.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:99999;pointer-events:none;display:flex;justify-content:center;align-items:center;overflow:hidden;background:rgba(5,2,10,0.5);backdrop-filter:blur(3px);';
                    const card = pd.createElement('div');
                    card.style.cssText='background:rgba(15,5,20,0.65);backdrop-filter:blur(12px);border:1px solid rgba(255,0,77,0.5);padding:40px;border-radius:16px;box-shadow:0 0 40px rgba(255,0,77,0.4);text-align:center;max-width:80%;z-index:100000;transform:scale(0);animation:popCard 0.6s cubic-bezier(0.175,0.885,0.32,1.275) forwards;';
                    card.innerHTML=`<style>@keyframes popCard{{to{{transform:scale(1);}}}}</style>
                        <p style="color:#e0d8e0;font-size:1.6em;font-style:italic;line-height:1.5;margin-bottom:20px;">"{safe_msg}"</p>
                        <p style="color:#c0f9ff;font-size:1.1em;font-weight:bold;text-align:right;">—— (来自 {safe_city})</p>`;
                    ov.appendChild(card);
                    const colors=['#ff004d','#c0f9ff','#ffffff','#ff4b4b','#ff8a8a'];
                    for(let i=0;i<250;i++){{
                        const p=pd.createElement('div');
                        const sz=Math.random()*5+2, cl=colors[Math.floor(Math.random()*colors.length)];
                        p.style.cssText=`position:absolute;width:${{sz}}px;height:${{sz}}px;background:${{cl}};border-radius:50%;box-shadow:0 0 ${{sz*2}}px ${{cl}};z-index:99998;`;
                        let x=window.parent.innerWidth/2+(Math.random()*300-150);
                        let y=window.parent.innerHeight/2+(Math.random()*100-50);
                        const a=Math.random()*Math.PI*2, v=Math.random()*45+15;
                        let vx=Math.cos(a)*v, vy=Math.sin(a)*v-10;
                        p.style.left=x+'px'; p.style.top=y+'px';
                        ov.appendChild(p);
                        const upd=()=>{{vx*=0.94;vy*=0.94;vy+=0.8;x+=vx;y+=vy;p.style.left=x+'px';p.style.top=y+'px';
                            let op=Math.max(0,(window.parent.innerHeight+100-y)/window.parent.innerHeight);
                            p.style.opacity=op;
                            if(y<window.parent.innerHeight+100&&op>0)requestAnimationFrame(upd);else p.remove();}};
                        requestAnimationFrame(upd);
                    }}
                    pd.body.appendChild(ov);
                    setTimeout(()=>{{const e=pd.getElementById('fw');if(e){{e.style.transition='opacity 0.6s';e.style.opacity='0';setTimeout(()=>e.remove(),600);}}}},4200);
                </script>""", height=0, width=0)
            else:
                st.warning("雷达尚未截获任何信号！")

st.markdown("---")
st.markdown('<span class="live-dot"></span>截获的猎人小姐信号 (实时)', unsafe_allow_html=True)
feed_data = fetch_feed_data()
if feed_data:
    cols = st.columns(3)
    for i, item in enumerate(feed_data):
        with cols[i % 3]:
            st.markdown(f"""<div class="signal-card">
                <div class="signal-header">{item.get('name','未知猎人')} <span class="signal-city">📍 {item.get('city','未知坐标')}</span></div>
                <div class="signal-msg">"{item.get('message','发送了一段加密信号...')}"</div>
            </div>""", unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#885566;'>当前频段安静，等待第一位猎人接入...</p>", unsafe_allow_html=True)
