import streamlit as st
import streamlit.components.v1 as components


def render_tts_player(clean_text_for_speech, auto_play=False):
  """Hàm render component giao diện phát audio bằng HTML/JS."""
  # Chuyển đổi cờ boolean thành chuỗi 'true'/'false' để truyền vào JS
  auto_play_js = "true" if auto_play else "false"

  tts_html = """
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; font-family: sans-serif;">
        <p style="font-size: 13px; color: #555; margin: 0 0 8px 0;">
            Chọn giọng đọc (gõ để tìm theo tên hoặc mã ngôn ngữ, ví dụ: "vi", "hoaimy", "nam minh").
        </p>

        <input id="voiceSearch" type="text" placeholder="🔍 Tìm giọng..."
            style="width: 100%; box-sizing: border-box; padding: 8px; font-size: 14px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 6px;">

        <label style="font-size: 13px; color: #333; display: block; margin-bottom: 6px;">
            <input id="viOnly" type="checkbox" checked> Chỉ hiện giọng tiếng Việt
        </label>

        <select id="voiceSelect"
            style="width: 100%; box-sizing: border-box; padding: 8px; font-size: 14px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 4px;">
        </select>
        <div id="voiceCount" style="font-size: 12px; color: #777; margin-bottom: 6px;">Đang tải danh sách giọng...</div>
        <div style="margin-bottom: 10px;">
            <button onclick="testVoice()" style="background-color: #2f855a; color: white; border: none; padding: 6px 12px; font-size: 13px; border-radius: 5px; cursor: pointer; margin-right: 5px;">🎧 Nghe thử giọng này</button>
            <button onclick="loadVoices(true)" style="background-color: #718096; color: white; border: none; padding: 6px 12px; font-size: 13px; border-radius: 5px; cursor: pointer;">🔄 Tải lại danh sách</button>
        </div>

        <div style="text-align: center; margin-top: 5px;">
            <button onclick="playSpeech()" style="background-color: #FF4B4B; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-right: 5px;">▶ Nghe</button>
            <button onclick="pauseSpeech()" style="background-color: #FFA500; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-right: 5px;">⏸ Tạm dừng</button>
            <button onclick="stopSpeech()" style="background-color: #808080; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer;">⏹ Dừng</button>
            <button onclick="runDiagnostic()" style="background-color: #2b6cb0; color: white; border: none; padding: 10px 18px; font-size: 15px; border-radius: 5px; cursor: pointer; margin-top: 5px;">🔧 Test / Chẩn đoán</button>
        </div>

        <pre id="diagBox" style="display:none; margin-top: 12px; background:#111; color:#0f0; padding:10px; border-radius:6px; font-size:12px; white-space:pre-wrap; word-break:break-all;"></pre>

        <div id="bookTextContent" style="display:none;">REPLACE_ME_TEXT</div>
    </div>

    <script>
        let synth = window.speechSynthesis;
        let keepAliveTimer = null;
        let allVoices = [];
        let selectedKey = null; // dạng "tên|lang"

        const searchBox = document.getElementById('voiceSearch');
        const viOnlyBox = document.getElementById('viOnly');
        const sel = document.getElementById('voiceSelect');
        const countLabel = document.getElementById('voiceCount');

        function voiceKey(v) { return v.name + '|' + v.lang; }
        function isVi(v) {
            return v.lang && v.lang.toLowerCase().replace('_', '-').startsWith('vi');
        }

        // Lưu / đọc lựa chọn (có thể bị chặn trong iframe nên bọc try/catch)
        function saveChoice() {
            try { localStorage.setItem('tts_voice', selectedKey || ''); } catch (e) {}
        }
        function loadChoice() {
            try { return localStorage.getItem('tts_voice') || null; } catch (e) { return null; }
        }

        function pickDefaultVoice() {
            let southern = allVoices.find(v =>
                isVi(v) &&
                /nam minh|gia huy|mien nam|miền nam|south|vi-vn-standard-c|vi-vn-standard-d|vi-vn-wavenet-c|vi-vn-wavenet-d/i.test(v.name)
            );
            if (southern) return southern;
            return allVoices.find(isVi) || null;
        }

        function getSelectedVoice() {
            if (selectedKey) {
                let v = allVoices.find(x => voiceKey(x) === selectedKey);
                if (v) return v;
            }
            return pickDefaultVoice();
        }

        function renderVoiceList() {
            let q = searchBox.value.trim().toLowerCase();
            let viOnly = viOnlyBox.checked;

            let hasVi = allVoices.some(isVi);
            let list = allVoices.filter(v => {
                if (viOnly && hasVi && !isVi(v)) return false;
                if (!q) return true;
                return (v.name + ' ' + v.lang).toLowerCase().indexOf(q) !== -1;
            });

            // Giọng tiếng Việt lên đầu
            list.sort((a, b) => (isVi(b) ? 1 : 0) - (isVi(a) ? 1 : 0));

            sel.innerHTML = '';
            list.forEach(v => {
                let opt = document.createElement('option');
                opt.value = voiceKey(v);
                opt.textContent = v.name + ' | ' + v.lang + ' | ' + (v.localService ? 'trên máy' : 'trực tuyến');
                if (voiceKey(v) === selectedKey) opt.selected = true;
                sel.appendChild(opt);
            });

            // Nếu giọng đang chọn không nằm trong danh sách lọc thì không chọn gì cả
            if (!list.some(v => voiceKey(v) === selectedKey)) {
                sel.selectedIndex = -1;
            }

            countLabel.textContent = 'Hiển thị ' + list.length + ' / ' + allVoices.length + ' giọng' +
                (viOnly && !hasVi ? ' (máy này không có giọng tiếng Việt nào, nên hiện tất cả)' : '');
        }

        function loadVoices(manual) {
            let v = synth.getVoices();
            if (!v || v.length === 0) {
                countLabel.textContent = 'Chưa lấy được danh sách giọng từ trình duyệt (đang thử lại...)';
                return;
            }
            allVoices = v;
            if (!selectedKey) {
                selectedKey = loadChoice();
                if (!selectedKey) {
                    let d = pickDefaultVoice();
                    if (d) selectedKey = voiceKey(d);
                }
            }
            renderVoiceList();
        }

        sel.addEventListener('change', function () {
            selectedKey = sel.value;
            saveChoice();
        });
        searchBox.addEventListener('input', renderVoiceList);
        viOnlyBox.addEventListener('change', renderVoiceList);

        // Danh sách giọng có thể tải chậm, nên thử nhiều lần
        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = loadVoices;
        }
        loadVoices();
        let tries = 0;
        let voiceTimer = setInterval(function () {
            tries++;
            if (allVoices.length === 0) loadVoices();
            if (allVoices.length > 0 || tries >= 20) clearInterval(voiceTimer);
        }, 500);

        // Hiện mọi lỗi JS ra hộp chẩn đoán để biết chính xác chuyện gì xảy ra
        window.onerror = function (msg, src, line) {
            let box = document.getElementById('diagBox');
            box.style.display = 'block';
            box.textContent += 'LỖI JS: ' + msg + ' (dòng ' + line + ')' + '\\n';
        };

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
            let voice = getSelectedVoice();
            if (voice) {
                utterance.voice = voice;
                utterance.lang = voice.lang;
            }
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

        // Đọc một câu mẫu đúng ngôn ngữ của giọng, để biết giọng chọn có thật sự được áp dụng không
        function testVoice() {
            let voice = getSelectedVoice();
            if (!voice) {
                alert('Chưa có giọng nào được chọn.');
                return;
            }
            let sample = isVi(voice)
                ? 'Xin chào, đây là giọng đọc thử.'
                : 'Hello, this is a voice test.';
            synth.cancel();
            let u = new SpeechSynthesisUtterance(sample);
            u.voice = voice;
            u.lang = voice.lang;
            u.onerror = function (e) { alert('Lỗi đọc thử: ' + e.error); };
            synth.speak(u);
        }

        function runDiagnostic() {
            let box = document.getElementById('diagBox');
            box.style.display = 'block';
            let voices = synth.getVoices();
            let vi = voices.filter(isVi);
            let lines = [];
            lines.push('Trình duyệt: ' + navigator.userAgent);
            lines.push('URL protocol: ' + location.protocol);
            lines.push('Secure context: ' + window.isSecureContext);
            lines.push('Tổng số giọng: ' + voices.length);
            lines.push('Số giọng tiếng Việt: ' + vi.length);
            let cur = getSelectedVoice();
            lines.push('Giọng đang dùng: ' + (cur ? cur.name + ' | ' + cur.lang : '(mặc định của máy)'));
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

  components.html(tts_html, height=460, scrolling=True)


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
        st.session_state.current_page += 1
        st.session_state.auto_play_triggered = True
        st.rerun()
      else:
        st.info("🎉 Đã đến trang cuối cùng của tài liệu rồi bạn ơi!")