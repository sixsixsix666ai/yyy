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

# 从环境变量获取API密钥（更安全）
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "sk-drvRI8SfNEUPUYr2nTLDFVc6fPi4Ng5n6dDIhntYUeVjlrSa")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "ZTA2Y2FiYjY5NWMyNDg2MmE1ZTkzNzZiZWQyMTRlYmMtMTc0NTk0MzEwNw==")

# 检查API密钥是否已设置
if not STABILITY_API_KEY or not HEYGEN_API_KEY:
    st.error("请确保已正确设置Stability AI和HeyGen的API密钥")
    st.stop()

# 动作预设映射（用户输入的动作映射到HeyGen动画）
ANIMATION_PRESETS = {
    "走路": "walking_01",
    "跑步": "running_01",
    "跳舞": "dancing_01",
    "挥手": "waving_01",
    "说话": "talking_01",
    "婚礼": "wedding_ceremony",
    "派对": "party_celebration",
    "演讲": "public_speaking",
    "思考": "thinking_01",
    "展示": "presenting_01",
    "战斗": "fighting_01",
    "运动": "sports_01"
}

class StabilityAIDiagnostic:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.base_url = "https://api.stability.ai"
        self.text_to_image_endpoint = f"{self.base_url}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        self.engines_endpoint = f"{self.base_url}/v1/engines/list"

    def _validate_api_key(self) -> bool:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        try:
            response = requests.get(self.engines_endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                engines = response.json()
                if len(engines) > 0:
                    st.success(f"[API密钥有效] 检测到可用模型: {', '.join([eng['id'] for eng in engines[:2]])}")
                    return True
            elif response.status_code == 401:
                st.error("[错误] API密钥无效或未授权，请检查密钥是否正确")
            else:
                st.error(f"[错误] 验证失败，状态码: {response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            st.error(f"[网络错误] 验证API密钥失败: {str(e)}")
            return False

    def generate_image(self, prompt: str, width=1024, height=1024) -> bytes:
        """使用Stability AI生成图像"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {
            "text_prompts": [{"text": prompt}],
            "width": width,
            "height": height,
            "samples": 1,
            "steps": 30,
            "cfg_scale": 7.0,
            "output_format": "png"
        }
        
        with st.spinner("正在使用Stability AI生成图像..."):
            try:
                response = requests.post(
                    self.text_to_image_endpoint,
                    headers=headers,
                    json=data,
                    timeout=120
                )
                if response.status_code != 200:
                    st.error(f"[请求失败] 状态码: {response.status_code}")
                    st.error(f"错误内容: {response.text}")
                    return None
                
                data = response.json()
                if "artifacts" not in data or len(data["artifacts"]) == 0:
                    st.error("[错误] 响应中未包含图像数据")
                    return None
                
                image_data = base64.b64decode(data["artifacts"][0]["base64"])
                st.success(f"[成功] 图像生成完成")
                return image_data
            except requests.exceptions.RequestException as e:
                st.error(f"[请求异常] 图像生成失败: {str(e)}")
                return None
            except base64.binascii.Error as e:
                st.error(f"[数据解析错误] 图像数据解码失败: {str(e)}")
                return None

class HeyGenAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.base_url = "https://api.heygen.com/v1"  # 修正为v1 API
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def create_avatar(self, image_data_list: list, name: str) -> str:
        """创建高质量虚拟人（支持多张照片）"""
        url = f"{self.base_url}/avatar/create"
        
        # 构建多角度照片数据
        avatar_images = []
        poses = ["front", "left", "right", "front_full", "left_full", "right_full"]
        
        for i, img_data in enumerate(image_data_list):
            if i >= len(poses): 
                break  # 最多使用6张照片
                
            avatar_images.append({
                "pose": poses[i],
                "image": base64.b64encode(img_data).decode("utf-8")
            })
        
        if len(avatar_images) < 3:
            st.error("至少需要3张照片来创建虚拟人模型")
            return None
        
        data = {
            "avatar_name": name,
            "avatar_style": "realistic",
            "avatar_images": avatar_images
        }
        
        with st.spinner("创建3D虚拟人模型中..."):
            try:
                response = requests.post(url, headers=self.headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        avatar_id = result["data"]["avatar_id"]
                        st.success(f"虚拟人创建成功！ID: {avatar_id}")
                        return avatar_id
                    else:
                        st.error(f"创建失败: {result.get('msg', '未知错误')}")
                else:
                    st.error(f"创建失败: {response.text}")
                return None
            except Exception as e:
                st.error(f"创建异常: {str(e)}")
                return None
    
    def upload_media(self, image_data: bytes) -> str:
        """上传场景图到HeyGen媒体库"""
        url = f"{self.base_url}/media/upload"
        
        data = {
            "media_type": "image",
            "media_content": base64.b64encode(image_data).decode("utf-8")
        }
        
        with st.spinner("上传场景图中..."):
            try:
                response = requests.post(url, headers=self.headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        media_id = result["data"]["media_id"]
                        return media_id
                    else:
                        st.error(f"上传失败: {result.get('msg', '未知错误')}")
                else:
                    st.error(f"上传失败: {response.text}")
                return None
            except Exception as e:
                st.error(f"上传异常: {str(e)}")
                return None
    
    def generate_video(self, avatar_id: str, script: str, media_id: str = None, animation: str = "talking_01") -> str:
        """生成带背景的虚拟人视频"""
        url = f"{self.base_url}/video/generate"
        
        # 自动检测语言选择合适的声音
        lang = "en"  # 默认为英语
        if any(char in script for char in "你好吗谢谢再见"):
            lang = "zh"
        
        voice_id = "2d5b0e6cf36f460aa7fc47e3eee4ba54"  # 默认英语女声
        if lang == "zh":
            voice_id = "b8e9d294b1d54b3daa0e7d3c4a3a2c7a"  # 中文女声
        
        # 构建视频请求
        video_input = {
            "avatar_id": avatar_id,
            "voice": {
                "voice_id": voice_id
            },
            "background": {
                "type": "media" if media_id else "color",
                "value": media_id or "#ffffff"
            },
            "animation": {
                "type": "preset",
                "preset_id": animation
            },
            "text": script
        }
        
        data = {"video_input": video_input}
        
        with st.spinner("生成AI视频中..."):
            try:
                response = requests.post(url, headers=self.headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        video_id = result["data"]["video_id"]
                        st.info(f"视频生成中... ID: {video_id}")
                        return video_id
                    else:
                        st.error(f"生成失败: {result.get('msg', '未知错误')}")
                else:
                    st.error(f"生成失败: {response.text}")
                return None
            except Exception as e:
                st.error(f"生成异常: {str(e)}")
                return None
    
    def check_video_status(self, video_id: str) -> dict:
        """检查视频生成状态"""
        url = f"{self.base_url}/videos/{video_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return result["data"]
                else:
                    st.error(f"查询失败: {result.get('msg', '未知错误')}")
            else:
                st.error(f"查询失败: {response.text}")
            return None
        except Exception as e:
            st.error(f"查询异常: {str(e)}")
            return None

# Streamlit 界面
st.set_page_config(
    page_title="AI虚拟人场景生成器",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI虚拟人场景生成器")
st.subheader("上传人物照片 + 描述场景 + 选择动作 = 生成定制化视频")

# 初始化API客户端
stability_client = StabilityAIDiagnostic(STABILITY_API_KEY)
heygen_client = HeyGenAPI(HEYGEN_API_KEY)

# 验证API密钥
with st.expander("API密钥验证"):
    if st.button("验证API密钥"):
        with st.spinner("正在验证API密钥..."):
            stability_valid = stability_client._validate_api_key()
            if stability_valid:
                st.success("Stability AI API密钥验证通过")
            else:
                st.error("Stability AI API密钥验证失败")
                
            # HeyGen验证通过生成视频测试
            st.write("HeyGen API将在视频生成时验证")

# 分步表单
with st.form("video_generation_form"):
    # 第一步：上传人物照片
    st.header("1️⃣ 上传人物照片")
    st.write("请上传3-10张清晰的人物照片，包括正脸、侧身、全身照等多角度照片")
    
    uploaded_files = st.file_uploader(
        "选择人物照片 (支持JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="最少3张，最多10张不同角度照片"
    )
    
    # 显示上传的缩略图
    if uploaded_files:
        cols = st.columns(min(4, len(uploaded_files)))
        for i, file in enumerate(uploaded_files):
            with cols[i % len(cols)]:
                img = Image.open(file)
                st.image(img, caption=f"照片 {i+1}", use_column_width=True)
    
    # 第二步：场景描述
    st.header("2️⃣ 描述幻想世界")
    scene_prompt = st.text_area(
        "详细描述你的幻想场景和服装",
        "赛博朋克风格的城市夜景，霓虹灯闪烁，人物穿着华丽的民族服饰",
        height=100,
        help="例如：'梦幻宇宙中的婚礼现场，星光璀璨，人物穿着发光婚纱'"
    )
    
    # 第三步：动作选择
    st.header("3️⃣ 选择人物动作")
    action_options = list(ANIMATION_PRESETS.keys())
    selected_action = st.selectbox(
        "选择主要动作",
        options=action_options,
        index=4,  # 默认为"说话"
        help="根据场景选择合适的动作"
    )
    
    # 第四步：视频脚本
    st.header("4️⃣ 添加人物台词")
    video_script = st.text_area(
        "输入人物要说的话或旁白",
        "欢迎来到这个不可思议的世界！在这里，现实与幻想交织，一切皆有可能...",
        height=120,
        help="人物将说出这些内容，支持中英文"
    )
    
    # 提交按钮
    submit_button = st.form_submit_button("✨ 生成魔法视频")

# 处理表单提交
if submit_button:
    # 验证输入
    if not uploaded_files or len(uploaded_files) < 3:
        st.error("请上传至少3张人物照片")
        st.stop()
    
    if len(uploaded_files) > 10:
        st.error("最多只能上传10张照片")
        st.stop()
    
    if not scene_prompt.strip():
        st.error("请输入场景描述")
        st.stop()
    
    if not video_script.strip():
        st.error("请输入视频脚本")
        st.stop()
    
    # 创建进度容器
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 1. 生成场景图
    status_text.subheader("第一步：生成幻想世界场景...")
    scene_image_data = stability_client.generate_image(scene_prompt)
    progress_bar.progress(20)
    
    if not scene_image_data:
        st.error("场景生成失败，无法继续")
        st.stop()
    
    # 显示生成的场景
    scene_image = Image.open(BytesIO(scene_image_data))
    st.image(scene_image, caption="生成的场景", use_column_width=True)
    
    # 2. 上传场景图到HeyGen
    status_text.subheader("第二步：上传场景到视频平台...")
    media_id = heygen_client.upload_media(scene_image_data)
    progress_bar.progress(40)
    
    if not media_id:
        st.error("场景上传失败，无法继续")
        st.stop()
    
    # 3. 创建虚拟人模型
    status_text.subheader("第三步：创建3D虚拟人模型...")
    image_data_list = [file.getvalue() for file in uploaded_files]
    avatar_id = heygen_client.create_avatar(image_data_list, f"avatar_{int(time.time())}")
    progress_bar.progress(60)
    
    if not avatar_id:
        st.error("虚拟人创建失败，无法继续")
        st.stop()
    
    # 4. 生成视频
    status_text.subheader("第四步：合成魔法视频...")
    animation_preset = ANIMATION_PRESETS.get(selected_action, "talking_01")
    video_id = heygen_client.generate_video(
        avatar_id, 
        video_script, 
        media_id,
        animation_preset
    )
    progress_bar.progress(80)
    
    if not video_id:
        st.error("视频生成任务创建失败")
        st.stop()
    
    # 5. 轮询检查视频状态
    status_text.subheader("第五步：渲染最终效果...")
    max_attempts = 30  # 最多尝试30次
    video_url = None
    
    for attempt in range(max_attempts):
        progress = 80 + int(20 * (attempt / max_attempts))
        progress_bar.progress(min(progress, 99))
        
        status_text.write(f"视频渲染中 ({attempt+1}/{max_attempts})...")
        status_data = heygen_client.check_video_status(video_id)
        
        if status_data:
            status = status_data.get("status")
            if status == "completed":
                video_url = status_data.get("video_url")
                st.success("🎉 视频生成完成！")
                break
            elif status == "failed":
                st.error(f"❌ 视频生成失败: {status_data.get('error_message', '未知错误')}")
                break
            elif status == "processing":
                status_text.write(f"当前进度: {status_data.get('progress', 0)}%")
        
        time.sleep(10)  # 等待10秒再检查
    
    progress_bar.progress(100)
    
    # 显示结果
    if video_url:
        st.video(video_url)
        st.download_button(
            label="下载视频",
            data=requests.get(video_url).content,
            file_name="magic_video.mp4",
            mime="video/mp4"
        )
    else:
        st.warning("视频生成超时，请稍后在HeyGen平台查看结果")

# 添加使用说明
with st.expander("使用指南"):
    st.markdown("""
    ### 如何创建完美AI视频：
    1. **上传照片**：3-10张不同角度的人物照片（正脸、侧脸、全身）
    2. **描述场景**：详细说明幻想世界（如："赛博朋克城市中的民族服饰游行"）
    3. **选择动作**：根据场景选择人物主要动作
    4. **添加台词**：输入人物要说的内容或旁白
    5. **生成视频**：点击按钮等待魔法发生！
    
    ### 最佳实践：
    - 使用清晰、高质量的人物照片
    - 场景描述越详细，效果越惊艳
    - 动作选择要符合场景（如婚礼选"婚礼"，派对选"跳舞"）
    - 中文台词会自动匹配中文语音
    
    ### 技术说明：
    - 后端使用Stability AI生成场景
    - 使用HeyGen创建3D虚拟人并合成视频
    - 整个过程需要3-10分钟
    """)
