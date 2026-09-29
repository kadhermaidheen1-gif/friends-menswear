(function() {
    const bubble = document.getElementById('fm-bubble');
    const popup = document.getElementById('fm-popup');
    const closeBtn = document.getElementById('fm-close');
    const sendBtn = document.getElementById('fm-send');
    const input = document.getElementById('fm-input-field');
    const messages = document.getElementById('fm-messages');
    const langButtons = document.querySelectorAll('.lang-btn');
    const welcomeMsg = document.getElementById('welcome-msg');

    let history = [];
    let isOpen = false;
    let currentLang = localStorage.getItem('fm_lang') || 'en';

    // ---------- i18n ----------
    const i18n = {
        en: {
            placeholder: "Type your message...",
            welcome: "Hi! 👋 I'm Friends Menswear's virtual assistant. How can I help you today?",
            typing: "Typing...",
            error: "Sorry, something went wrong. Please try again."
        },
        ta: {
            placeholder: "உங்கள் செய்தியை டைப் செய்யுங்கள்...",
            welcome: "வணக்கம்! 👋 நான் Friends Menswear இன் மெய்நிகர் உதவியாளர். எப்படி உதவலாம்?",
            typing: "டைப் செய்கிறது...",
            error: "மன்னிக்கவும், ஏதோ தவறு நடந்தது. மீண்டும் முயற்சிக்கவும்."
        }
    };

    function t(key) { return i18n[currentLang][key]; }

    function applyLang() {
        input.placeholder = t('placeholder');
        welcomeMsg.textContent = t('welcome');

        // Swap any data-en / data-ta elements
        document.querySelectorAll('[data-en]').forEach(el => {
            const val = currentLang === 'ta' ? el.getAttribute('data-ta') : el.getAttribute('data-en');
            if (val) el.textContent = val;
        });

        // Language button active state
        langButtons.forEach(b => b.classList.toggle('active', b.dataset.lang === currentLang));

        // Reset welcome message in chat
        if (messages.children.length === 1) {
            messages.children[0].querySelector('.msg-text').textContent = t('welcome');
        }

        // Clear history so AI starts fresh in new language
        history = [];
    }

    langButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            currentLang = btn.dataset.lang;
            localStorage.setItem('fm_lang', currentLang);
            applyLang();
        });
    });

    // Apply saved lang on load
    applyLang();

    // ---------- Chat Open/Close ----------
    function openChat() {
        isOpen = true;
        popup.classList.add('visible');
        input.focus();
    }
    function closeChat() {
        isOpen = false;
        popup.classList.remove('visible');
    }

    bubble.addEventListener('click', () => isOpen ? closeChat() : openChat());
    closeBtn.addEventListener('click', closeChat);

    // ---------- Messages ----------
    function escapeHtml(s) {
        const div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `msg msg-${sender}`;
        div.innerHTML = `<div class="msg-text">${escapeHtml(text)}</div>`;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function addTyping() {
        const div = document.createElement('div');
        div.className = 'msg msg-bot msg-typing';
        div.id = 'fm-typing';
        div.innerHTML = `<div class="msg-text">${t('typing')}</div>`;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function removeTyping() {
        const el = document.getElementById('fm-typing');
        if (el) el.remove();
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        addTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: history,
                    lang: currentLang
                }),
            });
            const data = await response.json();
            removeTyping();
            history = data.history || [];
            addMessage(data.reply, 'bot');
        } catch (e) {
            removeTyping();
            addMessage(t('error'), 'bot');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // ---------- Load store info ----------
    fetch('/api/info').then(r => r.json()).then(info => {
        const addr = document.getElementById('store-address');
        const phone = document.getElementById('store-phone');
        const hours = document.getElementById('store-hours');
        if (addr && info.address && info.address !== '—') addr.textContent = info.address;
        if (phone && info.phone && info.phone !== '—') phone.textContent = info.phone;
        if (hours && info.hours && info.hours !== '—') hours.textContent = info.hours;
    }).catch(() => {});
})();