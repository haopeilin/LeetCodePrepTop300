let currentQ = null;
let indexData = [];   // lightweight index, loaded once for prev/next navigation

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (!id) {
        showError('No question ID specified.');
        return;
    }

    // Load lightweight index for prev/next nav (33 KB, cached after first load)
    try {
        const idxRes = await fetch('data/index.json');
        if (!idxRes.ok) throw new Error(`HTTP ${idxRes.status}`);
        indexData = await idxRes.json();
    } catch (err) {
        showError(`Failed to load index: ${err.message}`);
        return;
    }

    // Load full question data
    await loadQuestion(id);
    initResizer();
});

async function loadQuestion(id) {
    try {
        const res = await fetch(`data/${id}.json`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const q = await res.json();
        currentQ = q;
        renderQuestion(q);
        updateNavButtons(q);
    } catch (err) {
        showError(`Failed to load question ${id}: ${err.message}`);
    }
}

function showError(msg) {
    const layout = document.querySelector('.q-split-layout');
    if (layout) layout.innerHTML = `<div style="padding:48px;color:#5f6368">${msg}</div>`;
}

function renderQuestion(q) {
    document.title = `${q.id}. ${q.title} - LeetCode Prep`;

    document.getElementById('qTitle').textContent = `${q.id}. ${q.title}`;

    const diffEl = document.getElementById('qDifficulty');
    diffEl.textContent = q.difficulty;
    diffEl.className = `badge ${(q.difficulty || 'easy').toLowerCase()}`;

    // Tags
    const tagsContainer = document.getElementById('qTagsContainer');
    tagsContainer.innerHTML = (q.tags || []).map(tag =>
        `<a href="index.html?tag=${encodeURIComponent(tag)}" class="q-tag-badge q-tag-link" title="Browse ${tag} questions">${tag}</a>`
    ).join('');

    document.getElementById('qDescription').innerHTML =
        q.content || '<i>No description available.</i>';

    document.getElementById('qJavaSnippet').textContent =
        q.java_snippet || '// No Java snippet available.\nclass Solution {\n}\n';

    document.getElementById('qSolutionHtml').innerHTML =
        q.solution || '<i>No detailed solution available for this question.</i>';

    // Syntax highlight
    if (window.hljs) {
        document.querySelectorAll('pre code').forEach(block => {
            block.removeAttribute('data-highlighted');
            hljs.highlightElement(block);
        });
    }

    // Scroll both panes to top
    document.querySelectorAll('.q-pane').forEach(p => p.scrollTop = 0);
}

function updateNavButtons(q) {
    const idx = indexData.findIndex(d => String(d.id) === String(q.id));
    const total = indexData.length;
    document.getElementById('qNavLabel').textContent = `${idx + 1} / ${total}`;
    document.getElementById('prevBtn').disabled = idx <= 0;
    document.getElementById('nextBtn').disabled = idx >= total - 1;
}

async function navigateQuestion(direction) {
    if (!currentQ) return;
    const idx = indexData.findIndex(d => String(d.id) === String(currentQ.id));
    const next = indexData[idx + direction];
    if (!next) return;
    history.pushState(null, '', `question.html?id=${next.id}`);
    await loadQuestion(next.id);
}

function copyCode() {
    const code = document.getElementById('qJavaSnippet').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('copyBtn');
        btn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        btn.style.color = '#1e8e3e';
        btn.style.borderColor = '#34a853';
        setTimeout(() => {
            btn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy`;
            btn.style.color = '';
            btn.style.borderColor = '';
        }, 2000);
    });
}

// ── Draggable resizer ────────────────────────────────────────────
function initResizer() {
    const layout = document.getElementById('splitLayout');
    const leftPane = document.getElementById('leftPane');
    const rightPane = document.getElementById('rightPane');
    const handle = document.getElementById('resizeHandle');

    const MIN_LEFT_PCT = 20;
    const MAX_LEFT_PCT = 45;
    let leftPct = 38;
    applyWidths(leftPct);

    let dragging = false, startX = 0, startPct = 0;

    handle.addEventListener('mousedown', e => {
        dragging = true;
        startX = e.clientX;
        startPct = leftPct;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        layout.classList.add('q-resizing');
    });

    document.addEventListener('mousemove', e => {
        if (!dragging) return;
        const totalW = layout.getBoundingClientRect().width;
        const dPct = ((e.clientX - startX) / totalW) * 100;
        leftPct = Math.min(MAX_LEFT_PCT, Math.max(MIN_LEFT_PCT, startPct + dPct));
        applyWidths(leftPct);
    });

    document.addEventListener('mouseup', () => {
        if (!dragging) return;
        dragging = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        layout.classList.remove('q-resizing');
    });

    function applyWidths(pct) {
        leftPane.style.flex = 'none';
        rightPane.style.flex = 'none';
        leftPane.style.width = `${pct}%`;
        rightPane.style.width = `${100 - pct}%`;
    }
}
