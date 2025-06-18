import streamlit as st
import requests
import json
import base64
import time
import logging
import os
from PIL import Image
from io import BytesIO

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)

# 从环境变量获取API密钥
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "sk-drvRI8SfNEUPUYr2nTLDFVc6fPi4Ng5n6dDIhntYUeVjlrSa")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "ZTA2Y2FiYjY5NWMyNDg2MmE1ZTkzNzZiZWQyMTRlYmMtMTc0NTk0MzEwNw==")

# 检查API密钥
if not STABILITY_API_KEY or not HEYGEN_API_KEY:
    st.error("请确保已正确设置Stability AI和HeyGen的API密钥")
    st.stop()

# 动作预设映射
ANIMATION_PRESETS = {
    "Walking": "walking_01",
    "Running": "running_01",
    "Dancing": "dancing_01",
    "Waving": "waving_01",
    "Talking": "talking_01",
    "Wedding": "wedding_ceremony",
    "Party": "party_celebration",
    "Speech": "public_speaking",
    "Thinking": "thinking_01",
    "Presenting": "presenting_01",
    "Fighting": "fighting_01",
    "Sports": "sports_01"
}

# 简单翻译函数（实际应用中应替换为专业翻译API）
def translate_to_english(text):
    """基础中文到英文翻译"""
    translations = {
        "赛博朋克": "cyberpunk",
        "民族服饰": "ethnic costume",
        "婚礼现场": "wedding scene",
        "宇宙": "cosmic",
        "梦幻": "dreamy",
        "办公室": "office",
        "商务装": "business attire",
        "霓虹灯": "neon lights",
        "星光": "starlight",
        "森林": "forest",
        "海滩": "beach",
        "城市": "city",
        "未来": "futuristic",
        "古代": "ancient",
        "魔法": "magical",
        "科技": "technology"
    }
    
    for cn, en in translations.items():
        text = text.replace(cn, en)
    return text

class StabilityAIDiagnostic:
    # ...保持不变...

class HeyGenAPI:
    # ...保持不变...

# Streamlit 界面
st.set_page_config(
    page_title="AI Virtual Scene Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Virtual Scene Generator")
st.subheader("Upload photos + Describe scene + Select action = Create custom video")

# 初始化API客户端
stability_client = StabilityAIDiagnostic(STABILITY_API_KEY)
heygen_client = HeyGenAPI(HEYGEN_API_KEY)

# 分步表单
with st.form("video_generation_form"):
    # 第一步：上传人物照片
    st.header("1️⃣ Upload Photos")
    st.write("Please upload 3-10 clear photos including front, side, and full-body shots")
    
    uploaded_files = st.file_uploader(
        "Select photos (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Minimum 3, maximum 10 photos from different angles"
    )
    
    # 显示上传的缩略图
    if uploaded_files:
        cols = st.columns(min(4, len(uploaded_files)))
        for i, file in enumerate(uploaded_files):
            with cols[i % len(cols)]:
                img = Image.open(file)
                st.image(img, caption=f"Photo {i+1}", use_column_width=True)
    
    # 第二步：场景描述（英文）
    st.header("2️⃣ Describe Fantasy Scene")
    scene_prompt = st.text_area(
        "Describe your fantasy scene and clothing in English",
        "Cyberpunk city night scene with neon lights, person in gorgeous ethnic costume",
        height=100,
        help="Example: 'Dreamy cosmic wedding scene with sparkling starlight, person in glowing wedding dress'"
    )
    
    # 第三步：动作选择
    st.header("3️⃣ Select Action")
    action_options = list(ANIMATION_PRESETS.keys())
    selected_action = st.selectbox(
        "Select main action",
        options=action_options,
        index=4,  # Default to "Talking"
        help="Choose action that fits the scene"
    )
    
    # 第四步：视频脚本
    st.header("4️⃣ Add Dialogue")
    video_script = st.text_area(
        "What should the person say?",
        "Welcome to this incredible world! Here, reality and fantasy intertwine, anything is possible...",
        height=120,
        help="The character will say these words, supports multiple languages"
    )
    
    # 提交按钮
    submit_button = st.form_submit_button("✨ Generate Magic Video")

# 处理表单提交
if submit_button:
    # 验证输入
    if not uploaded_files or len(uploaded_files) < 3:
        st.error("Please upload at least 3 photos")
        st.stop()
    
    if len(uploaded_files) > 10:
        st.error("Maximum 10 photos allowed")
        st.stop()
    
    if not scene_prompt.strip():
        st.error("Please enter scene description")
        st.stop()
    
    if not video_script.strip():
        st.error("Please enter dialogue")
        st.stop()
    
    # 创建进度容器
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 1. 生成场景图（确保使用英文）
    status_text.subheader("Step 1: Generating fantasy scene...")
    
    # 如果需要，可以添加自动翻译
    # english_prompt = translate_to_english(scene_prompt)
    # st.write(f"Translated prompt: {english_prompt}")
    
    scene_image_data = stability_client.generate_image(scene_prompt)  # 直接使用用户输入的英文
    progress_bar.progress(20)
    
    if not scene_image_data:
        st.error("Scene generation failed, cannot continue")
        st.stop()
    
    # 显示生成的场景
    scene_image = Image.open(BytesIO(scene_image_data))
    st.image(scene_image, caption="Generated Scene", use_column_width=True)
    
    # 2. 上传场景图到HeyGen
    status_text.subheader("Step 2: Uploading scene to video platform...")
    media_id = heygen_client.upload_media(scene_image_data)
    progress_bar.progress(40)
    
    if not media_id:
        st.error("Scene upload failed, cannot continue")
        st.stop()
    
    # 3. 创建虚拟人模型
    status_text.subheader("Step 3: Creating 3D avatar...")
    image_data_list = [file.getvalue() for file in uploaded_files]
    avatar_id = heygen_client.create_avatar(image_data_list, f"avatar_{int(time.time())}")
    progress_bar.progress(60)
    
    if not avatar_id:
        st.error("Avatar creation failed, cannot continue")
        st.stop()
    
    # 4. 生成视频
    status_text.subheader("Step 4: Synthesizing magic video...")
    animation_preset = ANIMATION_PRESETS.get(selected_action, "talking_01")
    video_id = heygen_client.generate_video(
        avatar_id, 
        video_script, 
        media_id,
        animation_preset
    )
    progress_bar.progress(80)
    
    if not video_id:
        st.error("Video generation task creation failed")
        st.stop()
    
    # 5. 轮询检查视频状态
    status_text.subheader("Step 5: Rendering final result...")
    max_attempts = 30
    video_url = None
    
    for attempt in range(max_attempts):
        progress = 80 + int(20 * (attempt / max_attempts))
        progress_bar.progress(min(progress, 99))
        
        status_text.write(f"Video rendering ({attempt+1}/{max_attempts})...")
        status_data = heygen_client.check_video_status(video_id)
        
        if status_data:
            status = status_data.get("status")
            if status == "completed":
                video_url = status_data.get("video_url")
                st.success("🎉 Video generation completed!")
                break
            elif status == "failed":
                st.error(f"❌ Video generation failed: {status_data.get('error_message', 'Unknown error')}")
                break
            elif status == "processing":
                status_text.write(f"Current progress: {status_data.get('progress', 0)}%")
        
        time.sleep(10)
    
    progress_bar.progress(100)
    
    # 显示结果
    if video_url:
        st.video(video_url)
        st.download_button(
            label="Download Video",
            data=requests.get(video_url).content,
            file_name="magic_video.mp4",
            mime="video/mp4"
        )
    else:
        st.warning("Video generation timed out, please check later on HeyGen platform")

# 添加使用说明
with st.expander("User Guide"):
    st.markdown("""
    ### How to create perfect AI videos:
    1. **Upload photos**: 3-10 photos from different angles (front, side, full-body)
    2. **Describe scene**: Detail your fantasy world (e.g., "Cyberpunk city with ethnic costume parade")
    3. **Select action**: Choose character action fitting the scene
    4. **Add dialogue**: What the character should say
    5. **Generate video**: Click and wait for the magic!
    
    ### Best practices:
    - Use clear, high-quality photos
    - More detailed scene descriptions = better results
    - Match action to scene (e.g., "Wedding" for wedding scenes)
    - Chinese dialogue automatically matches Chinese voice
    
    ### Technical notes:
    - Backend uses Stability AI for scene generation
    - Uses HeyGen for 3D avatar creation and video synthesis
    - Process takes 3-10 minutes
    """)
