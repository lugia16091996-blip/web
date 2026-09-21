import streamlit as st
import streamlit.components.v1 as components


def render_tts_player(clean_text_for_speech, auto_play=False):
  """Hàm render component giao diện phát audio bằng HTML/JS."""
  # Chuyển đổi cờ boolean thành chuỗi 'true'/'false' để truyền vào JS
  auto_play_js = "true" if auto_play else "false"

  tts_html = """
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; font-family: sans-serif;">
        <p style="font-size: 13px; color: #555; margin-bottom: 12px;">
            Giọng đọc: tự động ưu tiên giọng miền Nam nếu máy có, không thì dùng giọng hệ thống mặc định.
        </p>

        <div style="text-align: center; margin-top: 5px;">
            <button onclick="playSpeech()" style="background-color: #FF4B4B; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-right: 5px;">▶ Nghe</button>
            <button onclick="pauseSpeech()" style="background-color: #FFA500; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-right: 5px;">⏸ Tạm dừng</button>
            <button onclick="stopSpeech()" style="background-color: #808080; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer;">⏹ Dừng</button>
            <button onclick="runDiagnostic()" style="background-color: #2b6cb0; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-left: 5px;">🔧 Test / Chẩn đoán</button>
        </div>

        <pre id="diagBox" style="display:none; margin-top: 12px; background:#111; color:#0f0; padding:10px; border-radius:6px; font-size:12px; white-space:pre-wrap; word-break:break-all;"></pre>

        <div id="bookTextContent" style="display:none;">REPLACE_ME_TEXT</div>
    </div>

    <script>
        let synth = window.speechSynthesis;
        let keepAliveTimer = null;

        function pickVietnameseVoice() {
            let voices = synth.getVoices();
            if (!voices || voices.length === 0) return null;

            let southern = voices.find(v => 
                v.lang && v.lang.toLowerCase().startsWith('vi') && 
                /nam minh|gia huy|mien nam|miền nam|south|vi-vn-standard-c|vi-vn-standard-d|vi-vn-wavenet-c|vi-vn-wavenet-d/i.test(v.name)
            );
            if (southern) return southern;

            let anyVi = voices.find(v => v.lang && v.lang.toLowerCase().startsWith('vi'));
            return anyVi || null;
        }

        function playSpeech() {
            if (synth.paused) {
                synth.resume();
                return;
            }
            if (synth.speaking) {
                synth.cancel();
            }

            let textToRead = document.getElementById('bookTextContent').innerText;
            if (!textToRead.trim()) return;

            let utterance = new SpeechSynthesisUtterance(textToRead);
            utterance.lang = 'vi-VN';
            let voice = pickVietnameseVoice();
            if (voice) utterance.voice = voice;
            utterance.onerror = function (e) {
                console.log('speech error:', e.error);
            };
            synth.speak(utterance);
        }

        function pauseSpeech() {
            if (synth.speaking) {
                synth.pause();
            }
        }

        function stopSpeech() {
            if (keepAliveTimer) clearInterval(keepAliveTimer);
            keepAliveTimer = null;
            synth.cancel();
        }

        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = function () {};
        }

        function runDiagnostic() {
            let box = document.getElementById('diagBox');
            box.style.display = 'block';
            let lines = [];
            lines.push('URL protocol: ' + location.protocol);
            lines.push('Secure context: ' + window.isSecureContext);
            let voices = synth.getVoices();
            lines.push('Số giọng đọc: ' + voices.length);
            box.textContent = lines.join('\\n');
        }

        // TỰ ĐỘNG PHÁT NẾU CỜ AUTO_PLAY LÀ TRUE
        window.addEventListener('DOMContentLoaded', () => {
            if (REPLACE_ME_AUTOPLAY) {
                // Đợi 1 giây để danh sách giọng đọc (voices) kịp load xong rồi mới gọi phát
                setTimeout(() => {
                    playSpeech();
                }, 1000);
            }
        });
    </script>
    """

  # Thay thế nội dung văn bản và trạng thái autoplay an toàn bằng hàm replace
  tts_html = tts_html.replace("REPLACE_ME_TEXT", clean_text_for_speech)
  tts_html = tts_html.replace("REPLACE_ME_AUTOPLAY", auto_play_js)

  components.html(tts_html, height=340, scrolling=True)


def render_audio_section(edited_reading_content, total_pages):
  """Hàm gom toàn bộ Phần 3 (Audio) và Phần 4 (Nút chuyển trang) vào một chỗ."""
  st.markdown("### 🔊 Trình phát Audio")

  # Làm sạch văn bản
  clean_text_for_speech = (
      edited_reading_content.replace('"', "'")
      .replace("\n", " ")
      .replace("\r", " ")
  )

  # Lấy cờ trạng thái
  is_auto_playing = st.session_state.get("auto_play_triggered", False)

  # Truyền cờ vào hàm render TTS HTML
  render_tts_player(clean_text_for_speech, auto_play=is_auto_playing)

  # Reset cờ ngay sau khi render để không bị lặp lại
  if is_auto_playing:
    st.session_state.auto_play_triggered = False

  # Nút chuyển trang kế tiếp & Auto Play
  col_btn1, col_btn2 = st.columns([1, 1])
  with col_btn1:
    if st.button("⏭️ Trang kế tiếp & Phát", use_container_width=True):
      if st.session_state.current_page + 1 <= total_pages:
        st.session_state.current_page += 2
        st.session_state.auto_play_triggered = True
        st.rerun()
      else:
        st.info("🎉 Đã đến trang cuối cùng của tài liệu rồi bạn ơi!")