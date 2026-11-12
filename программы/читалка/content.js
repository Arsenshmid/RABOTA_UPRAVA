(() => {
    // --- Утилиты ---
    function getORP(word) {
        const len = word.length;
        if (len === 1) return 0;
        if (len <= 5) return 1;
        if (len <= 9) return 2;
        if (len <= 13) return 3;
        return 4;
    }

    function renderWord(wordEl, word) {
        if (!word) {
            wordEl.innerHTML = '<span class="spritz-center">•</span>';
            return;
        }
        const orp = getORP(word);
        const left = word.substring(0, orp);
        const center = word[orp];
        const right = word.substring(orp + 1);

        wordEl.innerHTML = `
            <span class="spritz-left">${left}</span>
            <span class="spritz-center">${center}</span>
            <span class="spritz-right">${right}</span>
        `;
    }

    // --- Инициализация UI через Shadow DOM ---
    let host = document.getElementById('spritz-host-root');
    if (!host) {
        host = document.createElement('div');
        host.id = 'spritz-host-root';
        const shadow = host.attachShadow({ mode: 'closed' });
        
        // Инжектим стили прямо в Shadow
        const style = document.createElement('style');
        style.textContent = document.querySelector('link[rel="stylesheet"][href*="styles.css"]') 
            ? '' // Если браузер подхватил link, но в Shadow лучше продублировать критичное
            : '';
        // Дублируем нужные стили в Shadow, чтобы гарантировать изоляцию
        style.textContent = `
            .spritz-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; font-family: sans-serif; color: #e0e0e0; }
            .spritz-reader-box { background: #1e1e1e; border: 1px solid #333; border-radius: 12px; padding: 40px 60px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; min-width: 400px; }
            .spritz-word-display { font-family: "Courier New", monospace; font-size: 32px; font-weight: bold; color: #fff; height: 50px; line-height: 50px; display: flex; justify-content: center; margin-bottom: 20px; }
            .spritz-left { display: inline-block; text-align: right; min-width: 150px; }
            .spritz-center { color: #ff3b30; display: inline-block; width: 20px; text-align: center; }
            .spritz-right { display: inline-block; text-align: left; min-width: 150px; }
            .spritz-controls { display: flex; gap: 15px; align-items: center; justify-content: center; margin-top: 20px; }
            .spritz-btn { background: #333; color: #fff; border: 1px solid #555; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }
            .spritz-btn:hover { background: #444; }
            .spritz-btn.primary { background: #007aff; border-color: #007aff; }
            .spritz-wpm { display: flex; align-items: center; gap: 10px; margin-top: 15px; font-size: 14px; color: #aaa; }
            .spritz-wpm input { width: 200px; }
            .spritz-progress { margin-top: 15px; font-size: 12px; color: #666; }
        `;
        shadow.appendChild(style);

        const container = document.createElement('div');
        container.className = 'spritz-container';
        container.innerHTML = `
            <div class="spritz-reader-box">
                <div class="spritz-word-display" id="s-word">
                    <span class="spritz-center">•</span>
                </div>
                <div class="spritz-controls">
                    <button class="spritz-btn primary" id="s-play">Старт</button>
                    <button class="spritz-btn" id="s-close">Закрыть</button>
                </div>
                <div class="spritz-wpm">
                    <span>WPM:</span>
                    <input type="range" id="s-wpm" min="150" max="800" value="350" step="50">
                    <span id="s-wpm-val">350</span>
                </div>
                <div class="spritz-progress" id="s-progress">0 / 0</div>
            </div>
        `;
        shadow.appendChild(container);
        document.body.appendChild(host);
    }

    // --- Логика движка ---
    const shadowRoot = host.shadowRoot;
    const wordEl = shadowRoot.getElementById('s-word');
    const playBtn = shadowRoot.getElementById('s-play');
    const closeBtn = shadowRoot.getElementById('s-close');
    const wpmSlider = shadowRoot.getElementById('s-wpm');
    const wpmVal = shadowRoot.getElementById('s-wpm-val');
    const progressEl = shadowRoot.getElementById('s-progress');

    let words = [];
    let currentIndex = 0;
    let intervalId = null;
    let isPlaying = false;

    function updateProgress() {
        progressEl.textContent = `${currentIndex} / ${words.length}`;
    }

    function tick() {
        if (currentIndex >= words.length) {
            stop();
            renderWord(wordEl, '');
            playBtn.textContent = 'Заново';
            return;
        }
        renderWord(wordEl, words[currentIndex]);
        currentIndex++;
        updateProgress();
    }

    function start() {
        if (words.length === 0) return;
        isPlaying = true;
        playBtn.textContent = 'Пауза';
        const wpm = parseInt(wpmSlider.value, 10);
        const delay = 60000 / wpm; // 60 сек / WPM
        intervalId = setInterval(tick, delay);
    }

    function stop() {
        isPlaying = false;
        playBtn.textContent = 'Старт';
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    }

    function openReader(text) {
        words = text.trim().split(/\s+/).filter(w => w.length > 0);
        if (words.length === 0) return;
        
        currentIndex = 0;
        host.classList.add('active');
        renderWord(wordEl, words[0]);
        updateProgress();
        playBtn.textContent = 'Старт';
        
        // Авто-старт
        start();
    }

    function closeReader() {
        stop();
        host.classList.remove('active');
        words = [];
        currentIndex = 0;
    }

    // --- Обработчики событий ---
    playBtn.addEventListener('click', () => {
        if (isPlaying) {
            stop();
        } else {
            if (currentIndex >= words.length) currentIndex = 0; // Если закончили, начинаем заново
            start();
        }
    });

    closeBtn.addEventListener('click', closeReader);

    wpmSlider.addEventListener('input', (e) => {
        wpmVal.textContent = e.target.value;
        if (isPlaying) {
            stop();
            start(); // Перезапуск с новым WPM
        }
    });

    // Закрытие по клику на фон (вне бокса) или Escape
    host.addEventListener('click', (e) => {
        if (e.target === host) closeReader();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && host.classList.contains('active')) {
            closeReader();
        }
        // Пробел для паузы/старта, когда ридер открыт
        if (e.code === 'Space' && host.classList.contains('active') && e.target === document.body) {
            e.preventDefault();
            playBtn.click();
        }
    });

    // --- Триггер по хоткею ---
    // В Manifest V3 команды commands перехватываются в background, 
    // но для content script проще использовать глобальный listener, 
    // либо зарегистрировать через chrome.commands (требует background).
    // Чтобы не плодить файлы, сделаем надежный перехват сочетания клавиш прямо тут.
    
    document.addEventListener('keydown', (e) => {
        // Alt + Shift + R
        if (e.altKey && e.shiftKey && e.code === 'KeyR') {
            e.preventDefault();
            const selection = window.getSelection().toString().trim();
            if (selection) {
                openReader(selection);
            } else {
                // Визуальный фидбек, если ничего не выделено
                const toast = document.createElement('div');
                toast.textContent = 'Выдели текст сначала';
                toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#ff3b30;color:#fff;padding:10px 20px;border-radius:6px;z-index:2147483647;font-family:sans-serif;';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 2000);
            }
        }
    });

})();