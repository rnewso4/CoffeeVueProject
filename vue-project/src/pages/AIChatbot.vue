<script setup>
import { ref, watch, nextTick } from 'vue';
import { doc, getDoc } from 'firebase/firestore';
import { auth, db } from '@/firebase';
import { Dialog, InputText, Button, Toast } from 'primevue';
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

const dialogPt = {
    root: { class: 'ai-chat-dialog-root' },
    header: { class: 'ai-chat-dialog-header' },
};

/** 'up' | 'down' per assistant message id (after successful POST). */
const feedbackByMessageId = ref({});
const feedbackSubmittingId = ref(null);

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

function chatFeedbackUrl() {
    const base = apiBase();
    return base ? `${base}/api/chat/feedback` : '/api/chat/feedback';
}

async function buildAuthJsonHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const user = auth.currentUser;
    if (user) {
        try {
            headers['Authorization'] = `Bearer ${await user.getIdToken()}`;
        } catch {
            /* proceed without token */
        }
    }
    return headers;
}

function absoluteApiUrl(path) {
    const base = apiBase();
    const p = path.startsWith('/') ? path : `/${path}`;
    return base ? `${base}${p}` : p;
}

async function downloadReportFiles(entries) {
    for (const item of entries) {
        const filename =
            typeof item?.filename === 'string' && item.filename.trim() !== ''
                ? item.filename.trim()
                : 'download.pdf';
        const mimeType =
            typeof item?.mime_type === 'string' && item.mime_type.trim() !== ''
                ? item.mime_type.trim()
                : 'application/octet-stream';
        const base64Content =
            typeof item?.content_base64 === 'string' ? item.content_base64.trim() : '';
        const path = typeof item?.url === 'string' ? item.url : '';
        let blob;

        if (base64Content) {
            const binary = atob(base64Content);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i += 1) {
                bytes[i] = binary.charCodeAt(i);
            }
            blob = new Blob([bytes], { type: mimeType });
        } else if (path) {
            const url = absoluteApiUrl(path);
            const headers = await buildAuthJsonHeaders();
            delete headers['Content-Type'];
            const res = await fetch(url, {
                headers,
                signal: fetchTimeoutSignal(60_000),
            });
            if (!res.ok) {
                const errText = await res.text().catch(() => '');
                throw new Error(errText || `Download failed (${res.status}).`);
            }
            blob = await res.blob();
        } else {
            continue;
        }

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

async function setFeedback(messageId, value) {
    const cur = feedbackByMessageId.value[messageId];
    const next = cur === value ? null : value;

    if (next == null) {
        const copy = { ...feedbackByMessageId.value };
        delete copy[messageId];
        feedbackByMessageId.value = copy;
        return;
    }

    const msg = messages.value.find((m) => m.id === messageId && m.role === 'assistant');
    if (!msg) return;
    if (feedbackSubmittingId.value === messageId) return;

    feedbackSubmittingId.value = messageId;
    try {
        const headers = await buildAuthJsonHeaders();
        const res = await fetch(chatFeedbackUrl(), {
            method: 'POST',
            headers,
            body: JSON.stringify({
                assistant_response: msg.content,
                feedback: next,
                message_id: messageId,
            }),
            signal: fetchTimeoutSignal(30_000),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const detail =
                typeof data?.error === 'string'
                    ? data.error
                    : data?.detail || data?.message || `Request failed (${res.status})`;
            throw new Error(detail);
        }
        const copy = { ...feedbackByMessageId.value };
        copy[messageId] = next;
        feedbackByMessageId.value = copy;
    } catch (err) {
        console.error('Chat feedback error:', err);
        toast.add({
            severity: 'error',
            summary: 'Could not save feedback',
            detail: err?.message ?? 'Unknown error',
            life: 6000,
        });
    } finally {
        feedbackSubmittingId.value = null;
    }
}

function clearChat() {
    messages.value = [];
    feedbackByMessageId.value = {};
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

    const headers = await buildAuthJsonHeaders();

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

function onComposerKeydown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        send();
    }
}
</script>

<template>
    <Dialog
        :visible="props.visible"
        modal
        maximizable
        aria-labelledby="ai-chat-dialog-title"
        :style="{ width: 'min(440px, 92vw)' }"
        contentClass="ai-chat-dialog-content"
        :pt="dialogPt"
        @update:visible="(v) => props.setVisible(v)"
        @maximize="() => nextTick(() => scrollToBottom())"
        @unmaximize="() => nextTick(() => scrollToBottom())"
    >
        <template #header>
            <span id="ai-chat-dialog-title" class="ai-chat-dialog-title">New Chat</span>
        </template>
        <div class="ai-chat-wrap">
            <div ref="listRef" class="ai-chat-messages" role="log" aria-live="polite">
                <div v-if="messages.length === 0 && !loading" class="ai-chat-greeting">
                    <p class="ai-chat-greeting-line">
                        <span class="ai-chat-greeting-hi">Hi,</span>
                        <span class="ai-chat-greeting-help">How can I help you?</span>
                    </p>
                    <p class="ai-chat-greeting-note">
                        Ask about your café data or business. Chat uses POST /api/chat on your server; the OpenAI key stays on the server only.
                    </p>
                </div>
                <div
                    v-for="m in messages"
                    :key="m.id"
                    class="ai-chat-row"
                    :class="m.role === 'user' ? 'ai-chat-row--user' : 'ai-chat-row--assistant'"
                >
                    <template v-if="m.role === 'user'">
                        <div class="ai-chat-bubble">
                            {{ m.content }}
                        </div>
                    </template>
                    <div v-else class="ai-chat-assistant-block">
                        <div class="ai-chat-bubble">
                            {{ m.content }}
                        </div>
                        <div class="ai-chat-feedback" role="group" aria-label="Rate this response">
                            <span class="ai-chat-feedback-label">Was this helpful?</span>
                            <div class="ai-chat-feedback-buttons">
                                <Button
                                    type="button"
                                    size="small"
                                    text
                                    icon="pi pi-thumbs-up"
                                    class="ai-chat-feedback-btn"
                                    :disabled="feedbackSubmittingId === m.id"
                                    :class="{ 'ai-chat-feedback-btn--active': feedbackByMessageId[m.id] === 'up' }"
                                    :aria-pressed="feedbackByMessageId[m.id] === 'up'"
                                    :severity="feedbackByMessageId[m.id] === 'up' ? 'primary' : 'secondary'"
                                    aria-label="Mark response as helpful"
                                    @click="setFeedback(m.id, 'up')"
                                />
                                <Button
                                    type="button"
                                    size="small"
                                    text
                                    icon="pi pi-thumbs-down"
                                    class="ai-chat-feedback-btn"
                                    :disabled="feedbackSubmittingId === m.id"
                                    :class="{ 'ai-chat-feedback-btn--active': feedbackByMessageId[m.id] === 'down' }"
                                    :aria-pressed="feedbackByMessageId[m.id] === 'down'"
                                    :severity="feedbackByMessageId[m.id] === 'down' ? 'primary' : 'secondary'"
                                    aria-label="Mark response as not helpful"
                                    @click="setFeedback(m.id, 'down')"
                                />
                            </div>
                        </div>
                    </div>
                </div>
                <div v-if="loading" class="ai-chat-row ai-chat-row--assistant">
                    <div class="ai-chat-bubble ai-chat-bubble--typing">Thinking…</div>
                </div>
            </div>
            <div class="ai-chat-footer-row">
                <Button
                    type="button"
                    label="Clear conversation"
                    size="small"
                    severity="secondary"
                    text
                    class="ai-chat-clear"
                    :disabled="loading || (messages.length === 0 && !error)"
                    @click="clearChat"
                />
            </div>
            <p v-if="error" class="ai-chat-error">{{ error }}</p>
            <div class="ai-chat-composer">
                <div class="ai-chat-composer-pill">
                    <InputText
                        v-model="input"
                        class="ai-chat-input"
                        placeholder="Send a message…"
                        :disabled="loading || limitExceeded"
                        @keydown="onComposerKeydown"
                    />
                    <Button
                        type="button"
                        icon="pi pi-send"
                        rounded
                        text
                        severity="secondary"
                        class="ai-chat-send"
                        :disabled="loading || !input.trim() || limitExceeded"
                        aria-label="Send message"
                        @click="send"
                    />
                </div>
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

.ai-chat-messages {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: 0.35rem 0.35rem 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
}

.ai-chat-greeting {
    padding: 0.35rem 0.25rem 0.75rem;
    text-align: left;
}

.ai-chat-greeting-line {
    margin: 0 0 0.5rem;
    font-size: 1.05rem;
    line-height: 1.45;
    color: var(--p-text-color);
}

.ai-chat-greeting-hi {
    font-weight: 400;
    margin-right: 0.25rem;
}

.ai-chat-greeting-help {
    font-weight: 700;
}

.ai-chat-greeting-note {
    margin: 0;
    font-size: 0.8rem;
    line-height: 1.45;
    color: color-mix(in srgb, var(--p-text-color) 68%, transparent);
    max-width: 26rem;
}

.ai-chat-footer-row {
    display: flex;
    justify-content: center;
    padding: 0 0.25rem;
}

.ai-chat-clear {
    opacity: 0.85;
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

.ai-chat-assistant-block {
    max-width: 88%;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.35rem;
}

.ai-chat-assistant-block .ai-chat-bubble {
    max-width: 100%;
    align-self: stretch;
}

.ai-chat-feedback {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.15rem;
    padding-left: 0.15rem;
}

.ai-chat-feedback-label {
    font-size: 0.75rem;
    color: color-mix(in srgb, var(--p-text-color) 58%, transparent);
    user-select: none;
}

.ai-chat-feedback-buttons {
    display: flex;
    align-items: center;
    gap: 0.15rem;
}

.ai-chat-feedback-btn--active :deep(.p-button-icon) {
    opacity: 1;
}

.ai-chat-bubble {
    max-width: 88%;
    padding: 0.6rem 0.85rem;
    border-radius: 14px;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 0.95rem;
    line-height: 1.45;
    background: var(--p-surface-0);
    color: var(--p-text-color);
    border: 1px solid color-mix(in srgb, var(--p-content-border-color) 65%, transparent);
    box-shadow: 0 1px 2px color-mix(in srgb, var(--p-text-color) 6%, transparent);
}

.ai-chat-row--user .ai-chat-bubble,
.ai-chat-row--assistant .ai-chat-bubble {
    background: var(--p-surface-0);
    color: var(--p-text-color);
}

.ai-chat-bubble--typing {
    opacity: 0.88;
    font-style: italic;
}

.ai-chat-error {
    margin: 0;
    font-size: 0.85rem;
    color: var(--p-red-500);
}

.ai-chat-composer {
    padding-top: 0.35rem;
    margin-top: 0.15rem;
    border-top: 1px solid color-mix(in srgb, var(--p-content-border-color) 55%, transparent);
}

.ai-chat-composer-pill {
    display: flex;
    align-items: center;
    gap: 0.15rem;
    padding: 0.2rem 0.35rem 0.2rem 0.85rem;
    border-radius: 9999px;
    background: var(--p-surface-0);
    border: 1px solid color-mix(in srgb, var(--p-content-border-color) 70%, transparent);
    box-shadow: 0 1px 2px color-mix(in srgb, var(--p-text-color) 5%, transparent);
}

.ai-chat-composer-pill :deep(.p-inputtext) {
    flex: 1 1 auto;
    min-width: 0;
    border: none;
    background: transparent;
    box-shadow: none;
    outline: none;
    padding-left: 0;
    padding-right: 0.25rem;
    color: var(--p-text-color);
}

.ai-chat-composer-pill :deep(.p-inputtext:enabled:focus) {
    box-shadow: none;
    border: none;
}

.ai-chat-composer-pill :deep(.p-inputtext::placeholder) {
    color: color-mix(in srgb, var(--p-text-color) 68%, transparent);
}

.ai-chat-send :deep(.p-button-icon) {
    font-size: 1rem;
    color: var(--p-text-color);
}

/* Dark mode: bubbles and composer pill use charcoal surfaces (not white surface-0) */
.my-app-dark .ai-chat-bubble,
.my-app-dark .ai-chat-row--user .ai-chat-bubble,
.my-app-dark .ai-chat-row--assistant .ai-chat-bubble {
    background: var(--p-surface-800);
    color: var(--p-text-color);
    border-color: color-mix(in srgb, var(--p-surface-500) 45%, var(--p-surface-700) 55%);
    box-shadow: 0 1px 2px color-mix(in srgb, black 35%, transparent);
}

.my-app-dark .ai-chat-composer-pill {
    background: var(--p-surface-800);
    border-color: color-mix(in srgb, var(--p-surface-500) 40%, var(--p-surface-700) 60%);
    box-shadow: 0 1px 2px color-mix(in srgb, black 30%, transparent);
}

.ai-limit-body {
    margin: 0;
    line-height: 1.55;
    font-size: 0.95rem;
}
</style>

<style>
/* Dialog is portaled; target root/content by class added via pt + contentClass */
.p-dialog.ai-chat-dialog-root {
    overflow: hidden;
}

/* Compact height only when not maximized — inline max-height would override Prime's fullscreen */
.p-dialog.ai-chat-dialog-root:not(.p-dialog-maximized) {
    max-height: 78vh;
}

.p-dialog.ai-chat-dialog-root .p-dialog-header.ai-chat-dialog-header {
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    padding-inline: 3rem;
    border-bottom: none;
}

.p-dialog.ai-chat-dialog-root .p-dialog-header .ai-chat-dialog-title {
    font-weight: 600;
    font-size: 1rem;
    color: var(--p-text-color);
}

.p-dialog.ai-chat-dialog-root .p-dialog-header .p-dialog-header-actions {
    position: absolute;
    right: 0.35rem;
    top: 50%;
    transform: translateY(-50%);
    margin: 0;
}

.p-dialog.ai-chat-dialog-root .p-dialog-content.ai-chat-dialog-content {
    padding-top: 0.35rem !important;
    padding-bottom: 0.85rem !important;
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--p-surface-50) 90%, var(--p-primary-color) 10%) 0%,
        color-mix(in srgb, var(--p-surface-100) 82%, var(--p-primary-color) 18%) 100%
    );
    border-radius: 0 0 12px 12px;
}

.my-app-dark .p-dialog.ai-chat-dialog-root .p-dialog-content.ai-chat-dialog-content {
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--p-surface-900) 94%, var(--p-primary-color) 6%) 0%,
        color-mix(in srgb, var(--p-surface-950) 90%, var(--p-surface-700) 10%) 100%
    );
}

.p-dialog.ai-chat-dialog-root.p-dialog-maximized {
    max-height: none !important;
}

.p-dialog.ai-chat-dialog-root.p-dialog-maximized .p-dialog-content.ai-chat-dialog-content {
    border-radius: 0;
    flex: 1 1 auto;
    min-height: 0;
    max-height: none !important;
    flex-grow: 1;
}

.p-dialog.ai-chat-dialog-root.p-dialog-maximized .ai-chat-wrap {
    max-height: none !important;
    flex: 1 1 auto;
    min-height: 0;
    height: 100%;
}
</style>
