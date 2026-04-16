import streamlit as st
import random
import html
import time
from supabase import create_client

# ==========================================
# 🔴 Supabase 密钥配置
# ==========================================
SUPABASE_URL = "https://yqggxqllcutqatwjxmyx.supabase.co"
SUPABASE_KEY = "sb_publishable_66sM5garleFYSyoxfoBizg_WeoUpnAy"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="N109区 - 专属礼花", layout="wide", initial_sidebar_state="collapsed")

# 隐藏边栏和默认样式
st.markdown("""
    <style>
    body, .stApp { background: #050208 !important; color: #fff; overflow: hidden; }
    [data-testid="collapsedControl"] { display: none; }
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_data():
    try:
        return supabase.table("blessings").select("*").limit(500).execute().data
    except:
        return []

blessings_data = fetch_data()

if blessings_data:
    lucky_hunter = random.choice(blessings_data)
    safe_msg = html.escape(lucky_hunter.get('message', '秦彻，生日快乐！')).replace('\n', '<br>')
    safe_city = html.escape(lucky_hunter.get('city', '未知坐标'))
    
    st.markdown(f"""
    <div style="position:fixed; top:0; left:0; width:100vw; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; background:rgba(5,2,10,0.8); z-index:999;">
        <div style="background:rgba(15,5,20,0.8); backdrop-filter:blur(12px); border:1px solid rgba(255,0,77,0.5); padding:40px; border-radius:16px; box-shadow:0 0 40px rgba(255,0,77,0.8); text-align:center; max-width:80%; margin-bottom:30px;">
            <p style="color:#e0d8e0; font-size:2em; font-style:italic; line-height:1.5; text-shadow:0 0 10px rgba(255,255,255,0.8); margin-bottom: 20px;">
                "{safe_msg}"
            </p>
            <p style="color:#c0f9ff; font-size:1.5em; font-weight:bold; text-shadow:0 0 15px #c0f9ff; text-align:right;">
                —— (来自 {safe_city})
            </p>
        </div>
    </div>
    
    <!-- 粒子爆炸特效（不再受原网页 iframe 限制） -->
    <script>
        const colors = ['#ff004d', '#c0f9ff', '#ffffff', '#ff4b4b', '#ff8a8a'];
        for(let i=0; i<250; i++) {{
            const p = document.createElement('div');
            const size = Math.random() * 6 + 2; 
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            p.style.cssText = `position:fixed; width:${{size}}px; height:${{size}}px; background-color:${{color}}; border-radius:50%; box-shadow:0 0 ${{size*2}}px ${{color}}; z-index:998;`;
            
            let x = window.innerWidth / 2;
            let y = window.innerHeight / 2;
            
            const angle = Math.random() * Math.PI * 2;
            const velocity = Math.random() * 45 + 15; 
            let vx = Math.cos(angle) * velocity;
            let vy = Math.sin(angle) * velocity - 10; 
            
            p.style.left = x + 'px';
            p.style.top = y + 'px';
            document.body.appendChild(p);
            
            const update = () => {{
                vx *= 0.94; vy *= 0.94; vy += 0.8; 
                x += vx; y += vy;
                p.style.left = x + 'px'; p.style.top = y + 'px';
                let opacity = Math.max(0, (window.innerHeight + 100 - y) / window.innerHeight);
                p.style.opacity = opacity;
                if(opacity > 0) requestAnimationFrame(update);
                else p.remove();
            }};
            requestAnimationFrame(update);
        }}
    </script>
    """, unsafe_allow_html=True)
else:
    st.warning("目前数据库没有收到祝福信号。")

# 提供返回按钮
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    time.sleep(1) # 稍微延迟让大家先看礼花
    if st.button("⬅️ 返回主页雷达", use_container_width=True):
        # 假设你的主页面原本叫 app.py 或 main.py，下面这行会自动返回主页
        st.switch_page("app.py") # 如果你的主文件叫 main.py，这里就改成 main.py
