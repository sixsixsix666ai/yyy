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
    st.error("Please ensure Stability AI and HeyGen API keys are set")
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
                    st.success(f"[API Key Valid] Available models: {', '.join([eng['id'] for eng in engines[:2]])}")
                    return True
            elif response.status_code == 401:
                st.error("[Error] Invalid API key or unauthorized")
            else:
                st.error(f"[Error] Validation failed, status code: {response.status_code}")
            return False
        except requests.exceptions.RequestException as e:
            st.error(f"[Network Error] API key validation failed: {str(e)}")
            return False

    def generate_image(self, prompt: str, width=1024, height=1024) -> bytes:
        """Generate image using Stability AI"""
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
        
        with st.spinner("Generating image with Stability AI..."):
            try:
                response = requests.post(
                    self.text_to_image_endpoint,
                    headers=headers,
                    json=data,
                    timeout=120
                )
                if response.status_code != 200:
                    st.error(f"[Request Failed] Status code: {response.status_code}")
                    st.error(f"Error content: {response.text}")
                    return None
                
                data = response.json()
                if "artifacts" not in data or len(data["artifacts"]) == 0:
                    st.error("[Error] No image data in response")
                    return None
                
                image_data = base64.b64decode(data["artifacts"][0]["base64"])
                st.success("[Success] Image generated")
                return image_data
            except requests.exceptions.RequestException as e:
                st.error(f"[Request Exception] Image generation failed: {str(e)}")
                return None
            except base64.binascii.Error as e:
                st.error(f"[Data Parsing Error] Image data decoding failed: {str(e)}")
                return None

class HeyGenAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.base_url = "https://api.heygen.com/v1"
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def create_avatar(self, image_data_list: list, name: str) -> str:
        """Create high-quality avatar"""
        url = f"{self.base_url}/avatar/create"
        
        # Prepare multi-angle photos
        avatar_images = []
        poses = ["front", "left", "right", "front_full", "left_full", "right_full"]
        
        for i, img_data in enumerate(image_data_list):
            if i >= len(poses): 
                break  # Max 6 photos
                
            avatar_images.append({
                "pose": poses[i],
                "image": base64.b64encode(img_data).decode("utf-8")
            })
        
        if len(avatar_images) < 3:
            st.error("At least 3 photos required to create avatar")
            return None
        
        data = {
            "avatar_name": name,
            "avatar_style": "realistic",
            "avatar_images": avatar_images
        }
        
        with st.spinner("Creating 3D avatar model..."):
            try:
                response = requests.post(url, headers=self.headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        avatar_id = result["data"]["avatar_id"]
                        st.success(f"Avatar created! ID: {avatar_id}")
                        return avatar_id
                    else:
                        st.error(f"Creation failed: {result.get('msg', 'Unknown error')}")
                else:
                    st.error(f"Creation failed: Status {response.status_code}")
                return None
            except Exception as e:
                st.error(f"Creation exception: {str(e)}")
                return None
    
    def upload_media(self, image_data: bytes) -> str:
        """Upload scene image to HeyGen media library (updated endpoint)"""
        url = f"{self.base_url}/media"  # 修正为正确的端点
        
        # 创建正确的数据格式
        data = {
            "media": base64.b64encode(image_data).decode("utf-8"),
            "media_type": "image"
        }
        
        with st.spinner("Uploading scene image..."):
            try:
                response = requests.post(url, headers=self.headers, json=data)
                
                # 调试信息
                st.write(f"Request URL: {url}")
                st.write(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        media_id = result["data"]["media_id"]
                        return media_id
                    else:
                        st.error(f"Upload failed: {result.get('msg', 'Unknown error')}")
                else:
                    # 显示更详细的错误信息
                    error_msg = f"Upload failed: Status {response.status_code}"
                    if response.text:
                        error_msg += f", Response: {response.text[:200]}"
                    st.error(error_msg)
                return None
            except Exception as e:
                st.error(f"Upload exception: {str(e)}")
                return None
    
    def generate_video(self, avatar_id: str, script: str, media_id: str = None, animation: str = "talking_01") -> str:
        """Generate video with background"""
        url = f"{self.base_url}/video/generate"
        
        # Auto-detect language for voice
        lang = "en"  # Default English
        if any(char in script for char in "你好吗谢谢再见"):
            lang = "zh"
        
        voice_id = "2d5b0e6cf36f460aa7fc47e3eee4ba54"  # Default English female
        if lang == "zh":
            voice_id = "b8e9d294b1d54b3daa0e7d3c4a3a2c7a"  # Chinese female
        
        # Build video request
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
        
        with st.spinner("Generating AI video..."):
            try:
                response = requests.post(url, headers=self.headers, json=data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0:
                        video_id = result["data"]["video_id"]
                        st.info(f"Video generation started... ID: {video_id}")
                        return video_id
                    else:
                        st.error(f"Generation failed: {result.get('msg', 'Unknown error')}")
                else:
                    st.error(f"Generation failed: Status {response.status_code}")
                return None
            except Exception as e:
                st.error(f"Generation exception: {str(e)}")
                return None
    
    def check_video_status(self, video_id: str) -> dict:
        """Check video generation status"""
        url = f"{self.base_url}/videos/{video_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return result["data"]
                else:
                    st.error(f"Query failed: {result.get('msg', 'Unknown error')}")
            else:
                st.error(f"Query failed: Status {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Query exception: {str(e)}")
            return None

# Streamlit UI
st.set_page_config(
    page_title="AI Virtual Scene Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Virtual Scene Generator")
st.subheader("Upload photos + Describe scene + Select action = Create custom video")

# Initialize API clients
stability_client = StabilityAIDiagnostic(STABILITY_API_KEY)
heygen_client = HeyGenAPI(HEYGEN_API_KEY)

# Step-by-step form
with st.form("video_generation_form"):
    # Step 1: Upload photos
    st.header("1️⃣ Upload Photos")
    st.write("Please upload 3-10 clear photos including front, side, and full-body shots")
    
    uploaded_files = st.file_uploader(
        "Select photos (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Minimum 3, maximum 10 photos from different angles"
    )
    
    # Show uploaded thumbnails
    if uploaded_files:
        cols = st.columns(min(4, len(uploaded_files)))
        for i, file in enumerate(uploaded_files):
            with cols[i % len(cols)]:
                img = Image.open(file)
                st.image(img, caption=f"Photo {i+1}", use_column_width=True)
    
    # Step 2: Scene description
    st.header("2️⃣ Describe Fantasy Scene")
    scene_prompt = st.text_area(
        "Describe your fantasy scene and clothing in English",
        "Cyberpunk city night scene with neon lights, person in gorgeous ethnic costume",
        height=100,
        help="Example: 'Dreamy cosmic wedding scene with sparkling starlight, person in glowing wedding dress'"
    )
    
    # Step 3: Action selection
    st.header("3️⃣ Select Action")
    action_options = list(ANIMATION_PRESETS.keys())
    selected_action = st.selectbox(
        "Select main action",
        options=action_options,
        index=4,  # Default to "Talking"
        help="Choose action that fits the scene"
    )
    
    # Step 4: Video script
    st.header("4️⃣ Add Dialogue")
    video_script = st.text_area(
        "What should the person say?",
        "Welcome to this incredible world! Here, reality and fantasy intertwine, anything is possible...",
        height=120,
        help="The character will say these words, supports multiple languages"
    )
    
    # Submit button
    submit_button = st.form_submit_button("✨ Generate Magic Video")

# Process form submission
if submit_button:
    # Validate input
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
    
    # Create progress container
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 1. Generate scene image
    status_text.subheader("Step 1: Generating fantasy scene...")
    scene_image_data = stability_client.generate_image(scene_prompt)
    progress_bar.progress(20)
    
    if not scene_image_data:
        st.error("Scene generation failed, cannot continue")
        st.stop()
    
    # Show generated scene
    scene_image = Image.open(BytesIO(scene_image_data))
    st.image(scene_image, caption="Generated Scene", use_column_width=True)
    
    # 2. Upload scene to HeyGen (使用修复后的端点)
    status_text.subheader("Step 2: Uploading scene to video platform...")
    media_id = heygen_client.upload_media(scene_image_data)
    progress_bar.progress(40)
    
    if not media_id:
        st.error("Scene upload failed, cannot continue")
        st.stop()
    
    # 3. Create avatar model
    status_text.subheader("Step 3: Creating 3D avatar...")
    image_data_list = [file.getvalue() for file in uploaded_files]
    avatar_id = heygen_client.create_avatar(image_data_list, f"avatar_{int(time.time())}")
    progress_bar.progress(60)
    
    if not avatar_id:
        st.error("Avatar creation failed, cannot continue")
        st.stop()
    
    # 4. Generate video
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
    
    # 5. Poll for video status
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
    
    # Show result
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

# User guide
with st.expander("User Guide"):
    st.markdown("""
    ### How to create perfect AI videos:
    1. **Upload photos**: 3-10 photos from different angles (front, side, full-body)
    2. **Describe scene**: Detail your fantasy world in English
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
