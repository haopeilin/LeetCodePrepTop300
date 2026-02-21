let questionsIndex = [];   // lightweight list (id, title, difficulty, tags)
let activeTags = new Set();
let searchQuery = "";
let currentDifficulty = "";

const questionsListEl = document.getElementById('questionsList');
const tagsContainerEl = document.getElementById('tagsContainer');
const searchInput = document.getElementById('searchInput');
const difficultyFilter = document.getElementById('difficultyFilter');
const resultsInfo = document.getElementById('resultsInfo');

async function init() {
    // Load the lightweight index only (~33 KB)
    try {
        const res = await fetch('data/index.json');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        questionsIndex = await res.json();
    } catch (err) {
        questionsListEl.innerHTML =
            `<div style="padding:48px;color:#c00">Failed to load questions index: ${err.message}</div>`;
        return;
    }

    // Build tag sidebar
    const tags = new Set();
    questionsIndex.forEach(q => {
        if (q.tags) q.tags.forEach(t => tags.add(t));
    });

    Array.from(tags).sort().forEach(tag => {
        const btn = document.createElement('button');
        btn.className = 'tag-btn';
        btn.textContent = tag;
        btn.onclick = () => toggleTag(tag, btn);
        tagsContainerEl.appendChild(btn);
    });

    // Pre-activate tag from URL param (e.g. coming back from question page)
    const urlTag = new URLSearchParams(window.location.search).get('tag');
    if (urlTag) {
        const matchingBtn = Array.from(tagsContainerEl.querySelectorAll('.tag-btn'))
            .find(b => b.textContent === urlTag);
        if (matchingBtn) {
            activeTags.add(urlTag);
            matchingBtn.classList.add('active');
            setTimeout(() => matchingBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
        }
    }

    searchInput.addEventListener('input', e => {
        searchQuery = e.target.value.toLowerCase();
        renderQuestions();
    });

    difficultyFilter.addEventListener('change', e => {
        currentDifficulty = e.target.value;
        renderQuestions();
    });

    renderQuestions();
}

function toggleTag(tag, btn) {
    if (activeTags.has(tag)) {
        activeTags.delete(tag);
        btn.classList.remove('active');
    } else {
        activeTags.clear();
        document.querySelectorAll('.tags-container .tag-btn.active').forEach(b => b.classList.remove('active'));
        activeTags.add(tag);
        btn.classList.add('active');
    }
    renderQuestions();
}

function renderQuestions() {
    const filtered = questionsIndex.filter(q => {
        if (currentDifficulty && q.difficulty !== currentDifficulty) return false;

        if (activeTags.size > 0) {
            if (!q.tags) return false;
            for (let tag of activeTags) {
                if (!q.tags.includes(tag)) return false;
            }
        }

        if (searchQuery) {
            const text = (q.title || '').toLowerCase();
            if (!text.includes(searchQuery)) return false;
        }

        return true;
    });

    resultsInfo.textContent = `Showing ${filtered.length} questions`;
    questionsListEl.innerHTML = '';

    filtered.forEach(q => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.onclick = () => openQuestion(q.id);

        const diffClass = (q.difficulty || 'easy').toLowerCase();
        const tagsHtml = (q.tags || []).slice(0, 3)
            .map(t => `<span class="tag-btn" style="border-color:transparent;background:var(--surface-color);padding:2px 6px;font-size:10px;">${t}</span>`)
            .join('');

        card.innerHTML = `
            <div class="q-header">
                <div>
                    <h3 class="q-title">${q.id}. ${q.title}</h3>
                    <div style="display:flex;gap:8px;margin-top:4px;">
                        ${tagsHtml}
                        ${(q.tags || []).length > 3 ? `<span style="font-size:10px;color:var(--text-secondary)">+${q.tags.length - 3}</span>` : ''}
                    </div>
                </div>
                <span class="badge ${diffClass}">${q.difficulty}</span>
            </div>
            <div class="q-snippet" style="color:var(--text-secondary);font-size:13px;margin-top:6px;">
                ${(q.tags || []).join(' · ') || '&nbsp;'}
            </div>
        `;

        questionsListEl.appendChild(card);
    });
}

function openQuestion(id) {
    window.location.href = `question.html?id=${id}`;
}

document.addEventListener('DOMContentLoaded', init);
