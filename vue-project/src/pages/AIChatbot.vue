<script setup>
import { ref, watch, nextTick } from 'vue';
import { doc, getDoc } from 'firebase/firestore';
import { auth, db } from '@/firebase';
import { Dialog, Textarea, Button, Toast } from 'primevue';
import { useToast } from 'primevue/usetoast';

const TOKEN_COST_LIMIT = 1.0;

const props = defineProps({
    visible: Boolean,
    setVisible: { type: Function, required: true },
});

const toast = useToast();

const messages = ref([]);
const input = ref('');
const loading = ref(false);
const error = ref('');
const listRef = ref(null);
const limitExceeded = ref(false);

async function checkTokenCost() {
    const user = auth.currentUser;
    if (!user) return;
    try {
        const snap = await getDoc(doc(db, 'users', user.uid));
        if (snap.exists()) {
            const cost = Number(snap.data().token_cost) || 0;
            limitExceeded.value = cost >= TOKEN_COST_LIMIT;
        }
    } catch (err) {
        console.error('Token cost check failed:', err);
    }
}

let idCounter = 0;
const nextId = () => ++idCounter;

function apiBase() {
    return (import.meta.env.VITE_UBUNTU_SERVER || '').replace(/\/$/, '');
}

function chatUrl() {
    const base = apiBase();
    return base ? `${base}/api/chat` : '/api/chat';
}

function absoluteApiUrl(path) {
    const base = apiBase();
    const p = path.startsWith('/') ? path : `/${path}`;
    return base ? `${base}${p}` : p;
}

async function downloadReportFiles(entries) {
    for (const item of entries) {
        const path = typeof item?.url === 'string' ? item.url : '';
        const filename =
            typeof item?.filename === 'string' && item.filename.trim() !== ''
                ? item.filename.trim()
                : 'download.pdf';
        if (!path) continue;
        const url = absoluteApiUrl(path);
        const res = await fetch(url, { signal: fetchTimeoutSignal(60_000) });
        if (!res.ok) {
            const errText = await res.text().catch(() => '');
            throw new Error(errText || `Download failed (${res.status}).`);
        }
        const blob = await res.blob();
        const href = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = href;
        a.download = filename;
        a.rel = 'noopener';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(href);
    }
}

/** Avoid hanging forever if the API host has no /api/chat or never responds. */
function fetchTimeoutSignal(ms) {
    if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
        return AbortSignal.timeout(ms);
    }
    const c = new AbortController();
    setTimeout(() => c.abort(), ms);
    return c.signal;
}

function scrollToBottom() {
    nextTick(() => {
        const el = listRef.value;
        if (el) el.scrollTop = el.scrollHeight;
    });
}

watch(
    () => props.visible,
    (v) => {
        if (v) {
            scrollToBottom();
            checkTokenCost();
        }
    }
);

function clearChat() {
    messages.value = [];
    error.value = '';
    input.value = '';
}

async function send() {
    const text = input.value.trim();
    if (!text || loading.value || limitExceeded.value) return;

    error.value = '';
    const userMsg = { id: nextId(), role: 'user', content: text };
    messages.value = [...messages.value, userMsg];
    input.value = '';
    loading.value = true;
    scrollToBottom();

    const payload = {
        messages: messages.value.map(({ role, content }) => ({ role, content })),
    };

    const url = chatUrl();

    const headers = { 'Content-Type': 'application/json' };
    const user = auth.currentUser;
    if (user) {
        try {
            headers['Authorization'] = `Bearer ${await user.getIdToken()}`;
        } catch { /* proceed without token */ }
    }

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
            signal: fetchTimeoutSignal(90_000),
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            if (res.status === 403 && data?.limit_exceeded) {
                limitExceeded.value = true;
                messages.value = messages.value.filter(m => m.id !== userMsg.id);
                return;
            }
            const detail =
                typeof data?.error === 'string'
                    ? data.error
                    : data?.detail || data?.message || `Request failed (${res.status})`;
            throw new Error(detail);
        }

        if (typeof data?.token_cost === 'number' && data.token_cost >= TOKEN_COST_LIMIT) {
            limitExceeded.value = true;
        }

        const reply =
            typeof data?.reply === 'string'
                ? data.reply
                : data?.choices?.[0]?.message?.content ?? null;

        if (reply == null || reply === '') {
            throw new Error('Invalid response from server.');
        }

        const downloads = Array.isArray(data?.downloads) ? data.downloads : [];
        if (downloads.length > 0) {
            try {
                await downloadReportFiles(downloads);
            } catch (dlErr) {
                console.error('Report download:', dlErr);
                const detail = dlErr?.message ?? 'Could not download report.';
                toast.add({
                    severity: 'warn',
                    summary: 'Report download',
                    detail,
                    life: 6000,
                });
            }
        }

        messages.value = [
            ...messages.value,
            { id: nextId(), role: 'assistant', content: String(reply) },
        ];
    } catch (err) {
        console.error('Chat error:', err);
        let msg = err?.message ?? 'Could not reach chat service.';
        if (err?.name === 'AbortError' || err?.name === 'TimeoutError') {
            msg =
                'Request timed out. Your API must expose POST /api/chat with OPENAI_API_KEY on the server. Check the host in VITE_UBUNTU_SERVER or the Vite proxy target.';
        }
        error.value = msg;
        toast.add({ severity: 'error', summary: 'Chat failed', detail: msg, life: 8000 });
    } finally {
        loading.value = false;
        scrollToBottom();
    }
}

function onKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
    }
}
</script>

<template>
    <Dialog
        :visible="props.visible"
        modal
        header="AI Chatbot"
        :style="{ width: 'min(440px, 92vw)', maxHeight: '78vh' }"
        contentClass="ai-chat-dialog-content"
        @update:visible="(v) => props.setVisible(v)"
    >
        <div class="ai-chat-wrap">
            <div class="ai-chat-toolbar">
                <Button type="button" label="Clear chat" size="small" severity="secondary" text @click="clearChat" />
            </div>
            <div ref="listRef" class="ai-chat-messages" role="log" aria-live="polite">
                <p v-if="messages.length === 0 && !loading" class="ai-chat-hint">
                    Ask a question about your café data or business. Requires POST /api/chat on your backend (OpenAI key stays on the server only).
                </p>
                <div
                    v-for="m in messages"
                    :key="m.id"
                    class="ai-chat-row"
                    :class="m.role === 'user' ? 'ai-chat-row--user' : 'ai-chat-row--assistant'"
                >
                    <div class="ai-chat-bubble">
                        {{ m.content }}
                    </div>
                </div>
                <div v-if="loading" class="ai-chat-row ai-chat-row--assistant">
                    <div class="ai-chat-bubble ai-chat-bubble--typing">Thinking…</div>
                </div>
            </div>
            <p v-if="error" class="ai-chat-error">{{ error }}</p>
            <div class="ai-chat-composer">
                <Textarea
                    v-model="input"
                    class="ai-chat-input"
                    autoResize
                    rows="2"
                    placeholder="Type a message…"
                    :disabled="loading || limitExceeded"
                    @keydown="onKeydown"
                />
                <Button type="button" label="Send" :disabled="loading || !input.trim() || limitExceeded" @click="send" />
            </div>
        </div>
        <Toast position="bottom-right" />
    </Dialog>

    <Dialog
        :visible="limitExceeded"
        modal
        header="Usage Limit Reached"
        :style="{ width: 'min(400px, 90vw)' }"
        :closable="true"
        @update:visible="(v) => { limitExceeded = v }"
    >
        <p class="ai-limit-body">
            You've exceeded the maximum token usage limit. Please contact an
            administrator to continue using the AI&nbsp;chatbot.
        </p>
        <template #footer>
            <Button label="OK" @click="limitExceeded = false" />
        </template>
    </Dialog>
</template>

<style scoped>
.ai-chat-wrap {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-height: 280px;
    max-height: min(62vh, 520px);
}

.ai-chat-toolbar {
    display: flex;
    justify-content: flex-end;
}

.ai-chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 0.25rem 0.25rem 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
}

.ai-chat-hint {
    margin: 0;
    padding: 0.75rem;
    font-size: 0.9rem;
    opacity: 0.75;
    text-align: center;
}

.ai-chat-row {
    display: flex;
    width: 100%;
}

.ai-chat-row--user {
    justify-content: flex-end;
}

.ai-chat-row--assistant {
    justify-content: flex-start;
}

.ai-chat-bubble {
    max-width: 88%;
    padding: 0.55rem 0.75rem;
    border-radius: 12px;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 0.95rem;
    line-height: 1.45;
}

.ai-chat-row--user .ai-chat-bubble {
    background: var(--p-primary-color);
    color: var(--p-primary-contrast-color);
    border-bottom-right-radius: 4px;
}

.ai-chat-row--assistant .ai-chat-bubble {
    background: var(--p-content-border-color);
    color: var(--p-text-color);
    border-bottom-left-radius: 4px;
}

.ai-chat-bubble--typing {
    opacity: 0.85;
    font-style: italic;
}

.ai-chat-error {
    margin: 0;
    font-size: 0.85rem;
    color: var(--p-red-500);
}

.ai-chat-composer {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-top: 0.25rem;
    border-top: 1px solid var(--p-content-border-color);
}

.ai-chat-input {
    width: 100%;
}

.ai-limit-body {
    margin: 0;
    line-height: 1.55;
    font-size: 0.95rem;
}
</style>

<style>
.ai-chat-dialog-content {
    padding-top: 0.5rem !important;
}
</style>
