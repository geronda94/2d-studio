const API_BASE_URL = '/api';

// AUTH_PLAN Ф1: единая обёртка над fetch — cookie-сессия + CSRF + реакция на 401.
// Немутирующие методы не требуют CSRF.
function _readCookie(name) {
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}

export async function apiFetch(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = _readCookie('csrf');
    if (csrf && !headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', csrf);
  }
  const response = await window.fetch(url, {
    credentials: 'include',
    ...options,
    headers,
  });
  if (response.status === 401 && !String(url).includes('/auth/')) {
    window.dispatchEvent(new CustomEvent('auth:unauthorized'));
  }
  return response;
}

export async function restorePresentation(id) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${id}/restore`, { method: 'POST' });
  if (!response.ok) throw new Error('Failed to restore presentation');
  return response.json();
}

export async function fetchFolders(includeArchived = false) {
  const url = includeArchived
    ? `${API_BASE_URL}/presentations/folders?include_archived=true`
    : `${API_BASE_URL}/presentations/folders`;
  const response = await apiFetch(url);
  if (!response.ok) throw new Error('Failed to fetch folders');
  return response.json();
}

export async function fetchProjectsSummary() {
  const response = await apiFetch(`${API_BASE_URL}/projects/summary`);
  if (!response.ok) throw new Error('Failed to fetch projects');
  return response.json();
}

export async function fetchProjectSummary(slug) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${slug}/summary`);
  if (!response.ok) throw new Error('Failed to fetch project');
  return response.json();
}

export async function fetchFolderSummary(slug, includeArchived = false) {
  const url = includeArchived
    ? `${API_BASE_URL}/presentations/folders/${slug}/summary?include_archived=true`
    : `${API_BASE_URL}/presentations/folders/${slug}/summary`;
  const response = await apiFetch(url);
  if (!response.ok) throw new Error('Failed to fetch folder');
  return response.json();
}

export async function createFolder(projectId, payload) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/folders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('Failed to create folder');
  return response.json();
}

export async function updateFolder(folderId, payload) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/folders/${folderId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('Failed to update folder');
  return response.json();
}

export async function deleteFolder(folderId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/folders/${folderId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete folder');
  return response.json();
}

export async function deletePresentation(presentationId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete presentation');
  return response.json();
}

export async function fetchProjects() {
  const response = await apiFetch(`${API_BASE_URL}/projects/`);
  if (!response.ok) throw new Error('Failed to fetch projects');
  return response.json();
}

export async function createProject({ title, description, template, slug }) {
  const response = await apiFetch(`${API_BASE_URL}/projects/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, template, slug }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create project');
  }
  return response.json();
}

export async function generateSlides(presentationId, { script, slideCount, apply = false } = {}) {
  const response = await apiFetch(`${API_BASE_URL}/ai/presentations/${presentationId}/generate-slides`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script, slide_count: slideCount, apply }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Generation failed');
  }
  return response.json();
}

export async function applyChangeSet(presentationId, ops, dryRun = true) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/change-set`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ops, dry_run: dryRun }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Change-set failed');
  }
  return response.json();
}

export async function fetchBrief(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/brief`);
  if (!response.ok) throw new Error('Failed to fetch brief');
  return response.json();
}

export async function updateBrief(projectId, brief) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/brief`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(brief),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update brief');
  }
  return response.json();
}

export async function fetchPalettes() {
  const response = await apiFetch(`${API_BASE_URL}/projects/palettes`);
  if (!response.ok) throw new Error('Failed to fetch palettes');
  return response.json();
}

export async function fetchPalettesSummary() {
  const response = await apiFetch(`${API_BASE_URL}/projects/palettes/summary`);
  if (!response.ok) throw new Error('Failed to fetch palettes');
  return response.json();
}

export async function forkProject(projectId, title) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/fork`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fork project');
  }
  return response.json();
}

export async function copyPalette(projectId, fromProject) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/palette/copy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_project: fromProject }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to copy palette');
  }
  return response.json();
}

export async function fetchTokenCoverage(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/tokens/coverage`);
  if (!response.ok) throw new Error('Failed to fetch coverage');
  return response.json();
}

export async function repairTokens(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/tokens/repair`, {
    method: 'POST'
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to repair tokens');
  }
  return response.json();
}

export async function updateProject(projectId, { title, description, default_variant }) {
  const body = {}
  if (title !== undefined) body.title = title
  if (description !== undefined) body.description = description
  if (default_variant !== undefined) body.default_variant = default_variant
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update project');
  }
  return response.json();
}

export async function deleteProject(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE'
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete project');
  }
  return response.json();
}

export async function copyPaletteToPresentation(presentationId, fromProject) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/palette/copy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_project: fromProject }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to copy palette to presentation');
  }
  return response.json();
}

export async function clearPresentationPalette(presentationId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/palette/clear`, {
    method: 'POST'
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to clear presentation palette');
  }
  return response.json();
}

export async function applyProjectVariant(projectId, variant) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/apply-variant`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ variant }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to apply variant');
  }
  return response.json();
}

export async function fetchProjectBySlug(slug) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${slug}`);
  if (!response.ok) throw new Error('Failed to fetch project');
  return response.json();
}

export async function fetchProjectColors(projectId) {
  try {
    const tokensRes = await apiFetch(`${API_BASE_URL}/projects/${projectId}/tokens`);
    if (tokensRes.ok) {
      const data = await tokensRes.json();
      if (data.tokens && Object.keys(data.tokens).length > 0) {
        // Map the tokens dict { "bg-base": { key, type, value } } to legacy array [ { name, value } ]
        return Object.values(data.tokens).map(t => ({
          name: t.key,
          value: t.value,
          category: t.type === 'color' ? 'solid' : 'other',
          custom: t.custom === true
        }));
      }
    }
  } catch (err) {
    console.error('Failed to fetch tokens', err);
  }
  return [];
}

export async function upsertProjectTokens(projectId, tokensObj) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/tokens`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tokens: tokensObj })
  });
  if (!response.ok) throw new Error('Failed to update project tokens');
  return response.json();
}

export async function deleteProjectToken(projectId, key) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/tokens/${encodeURIComponent(key)}`, {
    method: 'DELETE'
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete token');
  }
  return response.json();
}

export async function fetchPresets() {
  const response = await apiFetch(`${API_BASE_URL}/presets/`);
  if (!response.ok) throw new Error('Failed to fetch presets');
  return response.json();
}

export async function fetchPresentationStyle(presentationId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/style`);
  if (!response.ok) throw new Error('Failed to fetch presentation style');
  return response.json();
}

export async function updatePresentationStyle(presentationId, { style_preset, style_lock }) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/style`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ style_preset, style_lock }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update presentation style');
  }
  return response.json();
}

export async function fetchComponents() {
  const response = await apiFetch(`${API_BASE_URL}/components/?_t=${Date.now()}`);
  if (!response.ok) throw new Error('Failed to fetch components');
  return response.json();
}

export async function fetchPresentations() {
  const response = await apiFetch(`${API_BASE_URL}/presentations/`);
  if (!response.ok) throw new Error('Failed to fetch presentations');
  return response.json();
}

export async function fetchPresentation(id) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${id}`);
  if (!response.ok) throw new Error('Failed to fetch presentation');
  return response.json();
}

export async function fetchPresentationTokens(id) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${id}/tokens`);
  if (!response.ok) throw new Error('Failed to fetch presentation tokens');
  return response.json();
}

export async function fetchVariants() {
  const response = await apiFetch(`${API_BASE_URL}/variants/?_t=${Date.now()}`);
  if (!response.ok) throw new Error('Failed to fetch style variants');
  return response.json();
}

export async function createPresentation(payload) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('Failed to create presentation');
  return response.json();
}

export async function updatePresentation(id, data) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to update presentation');
  return response.json();
}

export async function updateSlide(slideId, payload) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/slides/${slideId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = new Error('Failed to update slide');
    try { err.detail = await response.json(); } catch { /* тело ошибки не JSON — оставляем generic */ }
    throw err;
  }
  return response.json();
}
export async function createSlide(presentationId, payload) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/slides`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create slide');
  return response.json();
}

export async function deleteSlide(slideId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/slides/${slideId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete slide');
  return response.json();
}

// --- SceneEngine ---------------------------------------------------------
export async function createScene(presentationId, payload) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/scenes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = new Error('Failed to create scene');
    try { err.detail = await response.json(); } catch { /* noop */ }
    throw err;
  }
  return response.json();
}

export async function updateScene(sceneId, payload) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/scenes/${sceneId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = new Error('Failed to update scene');
    try { err.detail = await response.json(); } catch { /* noop */ }
    throw err;
  }
  return response.json();
}

export async function deleteScene(sceneId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/scenes/${sceneId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete scene');
  return response.json();
}

export async function fetchSceneTemplates() {
  const response = await apiFetch(`${API_BASE_URL}/scene-library/templates`);
  if (!response.ok) throw new Error('Failed to fetch scene templates');
  return response.json();
}

export async function fetchSceneTemplate(slug) {
  const response = await apiFetch(`${API_BASE_URL}/scene-library/templates/${encodeURIComponent(slug)}`);
  if (!response.ok) throw new Error('Failed to fetch scene template');
  return response.json();
}

export async function fetchSceneEnvironments() {
  const response = await apiFetch(`${API_BASE_URL}/scene-library/environments`);
  if (!response.ok) throw new Error('Failed to fetch scene environments');
  return response.json();
}

export async function fetchSceneObjects() {
  const response = await apiFetch(`${API_BASE_URL}/scene-library/objects`);
  if (!response.ok) throw new Error('Failed to fetch scene objects');
  return response.json();
}

export async function fetchSceneCharacters() {
  const response = await apiFetch(`${API_BASE_URL}/scene-library/characters`);
  if (!response.ok) throw new Error('Failed to fetch scene characters');
  return response.json();
}

export async function fetchTextToVisemes(text, start = 700, end = 6000) {
  const response = await apiFetch(`${API_BASE_URL}/scene-library/text-to-visemes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, start, end }),
  });
  if (!response.ok) throw new Error('Failed to convert text to visemes');
  return response.json();
}

export async function uploadMedia(presentationId, file, fileType = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (fileType) {
    formData.append('file_type', fileType);
  }
  
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/media`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) throw new Error('Failed to upload media');
  return response.json();
}

export async function deleteMedia(presentationId, mediaId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/media/${mediaId}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete media');
  return response.json();
}

export async function fetchProjectMedia(presentationId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/global-media`);
  if (!response.ok) throw new Error('Failed to fetch project media');
  return response.json();
}

export const downloadMediaFromUrl = async (presentationId, url) => {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/media/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  })
  if (!response.ok) throw new Error('Failed to download media from URL')
  return response.json()
}

export const searchMedia = async (query, source = 'searxng', type = 'image', engines = '') => {
  try {
    const url = new URL(`${API_BASE_URL}/presentations/search/media`, window.location.origin);
    url.searchParams.append('q', query);
    url.searchParams.append('source', source);
    url.searchParams.append('type', type);
    if (engines) {
      url.searchParams.append('engines', engines);
    }
    const response = await apiFetch(url.toString());
    if (!response.ok) throw new Error('Search failed');
    const data = await response.json();
    return data.results || [];
  } catch (e) {
    console.error('Search error:', e);
    return [];
  }
}

export const searchSfx = async (presentationId, query = '') => {
  const url = new URL(`${API_BASE_URL}/presentations/${presentationId}/media/search-sfx`, window.location.origin);
  url.searchParams.append('query', query);
  const response = await apiFetch(url.toString());
  if (!response.ok) throw new Error('SFX Search failed');
  return response.json();
}

export const downloadSfx = async (presentationId, url, name = '') => {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/media/download-sfx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, name })
  });
  if (!response.ok) throw new Error('Failed to download SFX');
  return response.json();
}

export const generateAIVoice = async (presentationId, payload) => {
  const response = await apiFetch(`${API_BASE_URL}/ai/presentations/${presentationId}/generate-speech`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch (e) {
      throw new Error(`Server returned status ${response.status}`);
    }
    let detail = errorData.detail;
    if (Array.isArray(detail)) {
      detail = detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
    }
    throw new Error(detail || 'Failed to generate AI voice');
  }
  return response.json();
}

// --- AUTH_PLAN Ф2: доступ и команда проекта ---
export async function fetchPresentationAccess(presentationId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/access`);
  if (!response.ok) return { role: null, can_edit: false, can_style: false, authenticated: false };
  return response.json();
}

export async function fetchProjectMembers(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/members`);
  if (!response.ok) throw new Error('Failed to fetch members');
  return response.json();
}

export async function addProjectMember(projectId, email, role, scopeFolderId = null) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role, scope_folder_id: scopeFolderId }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Failed to add member');
  }
  return response.json();
}

export async function updateProjectMember(projectId, userId, role, scopeFolderId = null) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/members/${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role, scope_folder_id: scopeFolderId }),
  });
  if (!response.ok) throw new Error('Failed to update member');
  return response.json();
}

export async function removeProjectMember(projectId, userId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/members/${userId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to remove member');
  return response.json();
}

export async function transferProject(projectId, email) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/transfer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Failed to transfer');
  }
  return response.json();
}

export async function changePassword(currentPassword, newPassword) {
  const response = await apiFetch(`${API_BASE_URL}/auth/password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Не удалось сменить пароль');
  }
  return response.json();
}

export async function fetchProjectFolders(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/folders`);
  if (!response.ok) return [];
  return response.json();
}

// --- AUTH_PLAN Ф5: администрирование пользователей (только супер-админ) ---
export async function fetchAdminUsers() {
  const response = await apiFetch(`${API_BASE_URL}/admin/users`);
  if (!response.ok) throw new Error('Нет доступа');
  return response.json();
}

export async function updateAdminUser(userId, patch) {
  const response = await apiFetch(`${API_BASE_URL}/admin/users/${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Ошибка');
  }
  return response.json();
}

export async function resetUserPassword(userId, newPassword) {
  const response = await apiFetch(`${API_BASE_URL}/admin/users/${userId}/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_password: newPassword }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Ошибка');
  }
  return response.json();
}

// --- AUTH_PLAN: API-ключи пользователя ---
export async function fetchApiKeys() {
  const response = await apiFetch(`${API_BASE_URL}/api-keys/`);
  if (!response.ok) throw new Error('Не удалось загрузить ключи');
  return response.json();
}

export async function createApiKey(label, scopes = ['read', 'write'], opts = {}) {
  const response = await apiFetch(`${API_BASE_URL}/api-keys/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label, scopes, ...opts }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Ошибка');
  }
  return response.json();
}

export async function revokeApiKey(keyId) {
  const response = await apiFetch(`${API_BASE_URL}/api-keys/${keyId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Не удалось отозвать ключ');
  return response.json();
}

// --- BRAND KIT проекта ---
export async function fetchPresentationConfig(presentationId) {
  const response = await apiFetch(`${API_BASE_URL}/presentations/${presentationId}/config`);
  if (!response.ok) return { config: {} };
  return response.json();
}

export async function fetchProjectConfig(projectId) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/config`);
  if (!response.ok) return { config: {} };
  return response.json();
}

export async function updateProjectConfig(projectId, config) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Не удалось сохранить конфиг');
  }
  return response.json();
}

// --- ENTERPRISE Ф2: версии проекта ---
export async function fetchProjectRevisions(projectId, limit = 50) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/revisions?limit=${limit}`);
  if (!response.ok) throw new Error('Не удалось загрузить историю');
  return response.json();
}

export async function getProjectRevision(projectId, n) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/revisions/${n}`);
  if (!response.ok) throw new Error('Ревизия не найдена');
  return response.json();
}

export async function createProjectCheckpoint(projectId, label = 'checkpoint') {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/checkpoint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Не удалось создать точку');
  }
  return response.json();
}

export async function restoreProjectRevision(projectId, n, dryRun = true) {
  const response = await apiFetch(`${API_BASE_URL}/projects/${projectId}/revisions/${n}/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dry_run: dryRun }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Не удалось откатить');
  }
  return response.json();
}

// --- ENTERPRISE Ф3: делегирования ботов ---
export async function fetchDelegations() {
  const response = await apiFetch(`${API_BASE_URL}/delegations/me`);
  if (!response.ok) throw new Error('Не удалось загрузить делегирования');
  return response.json();
}

export async function requestDelegation(botUserId, subjectEmail, projectId = null) {
  const response = await apiFetch(`${API_BASE_URL}/delegations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bot_user_id: botUserId, subject_email: subjectEmail, project_id: projectId }),
  });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(typeof d.detail === 'string' ? d.detail : 'Не удалось запросить');
  }
  return response.json();
}

export async function approveDelegation(id) {
  const response = await apiFetch(`${API_BASE_URL}/delegations/${id}/approve`, { method: 'POST' });
  if (!response.ok) throw new Error('Не удалось одобрить');
  return response.json();
}

export async function revokeDelegation(id) {
  const response = await apiFetch(`${API_BASE_URL}/delegations/${id}/revoke`, { method: 'POST' });
  if (!response.ok) throw new Error('Не удалось отозвать');
  return response.json();
}
