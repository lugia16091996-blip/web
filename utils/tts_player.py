import asyncio
import os
import tempfile
import edge_tts
import streamlit as st

async def _generate_audio_file(text: str, voice: str, output_file: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def text_to_speech_mp3(text: str, voice_name: str = "vi-VN-HoaiMyNeural") -> str:
    """
    Sinh file MP3 từ văn bản sử dụng edge-tts.
    Trả về đường dẫn tới file MP3 tạm thời.
    """
    fp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_filename = fp.name
    fp.close()

    try:
        asyncio.run(_generate_audio_file(text, voice_name, temp_filename))
    except Exception as e:
        print(f"Lỗi tạo TTS: {e}")
        return None

    return temp_filename

def render_audio_section(edited_reading_content, total_pages):
    """Hàm gom toàn bộ Phần 3 (Audio) và Phần 4 (Nút chuyển trang) dùng MP3."""
    st.markdown("### 🔊 Trình phát Audio")

    # 1. Tối giản giao diện: Chỉ để selectbox chọn giọng miền Nam chuẩn
    voice_options = {
        "Nữ Miền Nam (Hoài Mỹ)": "vi-VN-HoaiMyNeural",
        "Nam Miền Nam (Nam Minh)": "vi-VN-NamMinhNeural"
    }
    
    if "selected_voice_label" not in st.session_state:
        st.session_state.selected_voice_label = "Nữ Miền Nam (Hoài Mỹ)"

    selected_label = st.selectbox(
        "Chọn giọng đọc:", 
        options=list(voice_options.keys()),
        index=list(voice_options.keys()).index(st.session_state.selected_voice_label),
        label_visibility="collapsed" # Ẩn nhãn cho giao diện tối giản
    )
    st.session_state.selected_voice_label = selected_label
    chosen_voice_code = voice_options[selected_label]

    # 2. Làm sạch văn bản chuẩn bị đọc
    clean_text_for_speech = (
        edited_reading_content.replace('"', "'")
        .replace("\n", " ")
        .replace("\r", " ")
    )

    # 3. Tiến hành sinh file MP3 ngầm (tốc độ mặc định 1.0, không giới hạn ký tự rườm rà)
    audio_file_path = None
    if clean_text_for_speech.strip():
        with st.spinner("Đang tạo giọng đọc..."):
            audio_file_path = text_to_speech_mp3(clean_text_for_speech, voice_name=chosen_voice_code)

    # Lấy cờ trạng thái tự động phát (khi bấm chuyển trang)
    is_auto_playing = st.session_state.get("auto_play_triggered", False)

    # 4. Phát audio bằng widget chuẩn của Streamlit (hỗ trợ autoplay mượt mà mọi thiết bị)
    if audio_file_path and os.path.exists(audio_file_path):
        st.audio(audio_file_path, format="audio/mp3", autoplay=is_auto_playing)

    # Reset cờ auto play ngay sau khi render xong
    if is_auto_playing:
        st.session_state.auto_play_triggered = False

    # 5. Nút chuyển trang kế tiếp & Auto Play
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("⏭️ Trang kế tiếp & Phát", use_container_width=True):
            if st.session_state.current_page + 1 <= total_pages:
                st.session_state.current_page += 2  # Hoặc +2 tùy logic app của mày
                st.session_state.auto_play_triggered = True
                st.rerun()
            else:
                st.info("🎉 Đã đến trang cuối cùng của tài liệu rồi bạn ơi!")