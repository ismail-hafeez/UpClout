const BASE_URL = 'http://localhost:5000/api';

// ── Showcase Wall: module-level cache (fetched once, reused instantly) ──────
let _showcaseCache: any[] | null = null;
let _showcaseFetchPromise: Promise<any[]> | null = null;

export const apiGetShowcaseWall = (): Promise<any[]> => {
  // Return instantly from cache if already loaded
  if (_showcaseCache !== null) return Promise.resolve(_showcaseCache);

  // Deduplicate in-flight requests (if called twice before first resolves)
  if (_showcaseFetchPromise) return _showcaseFetchPromise;

  _showcaseFetchPromise = fetch(`${BASE_URL}/profiles/showcase/wall`)
    .then(res => (res.ok ? res.json() : []))
    .then((data: any[]) => {
      _showcaseCache = data;
      // Pre-warm browser image cache in the background
      data.forEach(p => { const img = new Image(); img.src = p.profile_pic; });
      return data;
    })
    .catch(() => {
      _showcaseFetchPromise = null; // Allow retry on error
      return [];
    });

  return _showcaseFetchPromise;
};

// Token helpers
export const getToken = (): string | null => localStorage.getItem('token');
export const setToken = (token: string) => localStorage.setItem('token', token);
export const clearToken = () => localStorage.removeItem('token');

export const getAvatarUrl = (url?: string | null): string => {
  if (!url) return '';
  if (url.startsWith('/uploads/')) return `http://localhost:5000${url}`;
  return url;
};

export const setCurrentUser = (user: object) =>
  localStorage.setItem('currentUser', JSON.stringify(user));
export const getCurrentUser = () => {
  const raw = localStorage.getItem('currentUser');
  return raw ? JSON.parse(raw) : null;
};
export const clearCurrentUser = () => localStorage.removeItem('currentUser');

// Core fetch wrapper
const request = async (
  path: string,
  options: RequestInit = {}
): Promise<any> => {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Request failed');
  return data;
};

// Auth
export const apiRegister = (body: {
  username: string;
  email: string;
  password: string;
  displayName?: string;
  userType?: string;
}) => request('/auth/register', { method: 'POST', body: JSON.stringify(body) });

export const apiLogin = (body: { username: string; password: string }) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify(body) });

export const apiMe = () => request('/auth/me');
export const apiGetBrandStats = () => request('/auth/brand-stats');
export const apiGetBrandRecommendations = () => request('/auth/recommendations');
export const apiGetAnalytics = (username: string) => request(`/analytics/${username}`);
export const apiGetRisingStars = () => request('/analytics/rising-stars');
export const apiGetProfileDetails = (username: string) => request(`/profiles/${username}`);

// Conversations
export const apiGetConversations = () => request('/conversations');

export const apiStartConversation = (recipientId: string) =>
  request('/conversations', {
    method: 'POST',
    body: JSON.stringify({ recipientId }),
  });

export const apiGetMessages = (conversationId: string, page = 1) =>
  request(`/conversations/${conversationId}/messages?page=${page}&limit=40`);

export const apiUploadFile = (conversationId: string, file: File) => {
  const token = getToken();
  const form = new FormData();
  form.append('file', file);
  return fetch(`${BASE_URL}/conversations/${conversationId}/files`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  }).then((r) => r.json());
};

export const apiSearchUsers = (q: string) =>
  request(`/auth/search-pg?q=${encodeURIComponent(q)}`);

export const apiUpdateProfile = (body: { displayName?: string; avatarUrl?: string }) =>
  request('/auth/profile', { method: 'PATCH', body: JSON.stringify(body) });

export const apiUploadAvatar = (file: File) => {
  const token = getToken();
  const form = new FormData();
  form.append('avatar', file);
  return fetch(`${BASE_URL}/auth/avatar`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  }).then(async (r) => {
    const data = await r.json();
    if (!r.ok) throw new Error(data.message || 'Upload failed');
    return data;
  });
};

// Users, Ratings & Connections
export const apiGetUserProfile = (id: string) => request(`/users/${id}`);

export const apiGetConnectionRequests = () => request('/users/connections/requests');
export const apiGetAcceptedConnections = () => request('/users/connections/accepted');
export const apiAcceptConnectionRequest = (reqId: string) => request(`/users/connections/${reqId}/accept`, { method: 'POST' });
export const apiRejectConnectionRequest = (reqId: string) => request(`/users/connections/${reqId}/reject`, { method: 'POST' });
export const apiUnaddConnection = (reqId: string) => request(`/users/connections/${reqId}`, { method: 'DELETE' });
export const apiGetConnectionStatus = (id: string) => request(`/users/${id}/connection-status`);
export const apiSendConnectionRequest = (id: string) => request(`/users/${id}/connect`, { method: 'POST' });

export const apiGetReviews = (id: string, page = 1) => request(`/users/${id}/reviews?page=${page}&limit=10`);

export const apiSubmitReview = (id: string, body: { rating: number; comment?: string }) =>
  request(`/users/${id}/reviews`, { method: 'POST', body: JSON.stringify(body) });

// Campaigns
export const apiCreateCampaign = (body: any) => request('/campaigns', { method: 'POST', body: JSON.stringify(body) });
export const apiGetCampaigns = () => request('/campaigns');

// Collaborations
export const apiCreateCollaboration = (body: any) => request('/collaborations', { method: 'POST', body: JSON.stringify(body) });
export const apiGetCollaborations = () => request('/collaborations');
export const apiGetPublicCollaborations = (userId: string) => request(`/collaborations/user/${userId}`);
export const apiMarkCollaborationsSeen = () => request('/collaborations/mark-seen', { method: 'PUT' });
export const apiRejectCollaboration = (id: string) => request(`/collaborations/${id}/reject`, { method: 'DELETE' });
export const apiUpdateCollaborationStatus = (id: string, status: string) => request(`/collaborations/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) });
export const apiUpdateCollaborationDeliverables = (id: string, deliverables: any[]) => request(`/collaborations/${id}/deliverables`, { method: 'PUT', body: JSON.stringify({ deliverables }) });
export const apiUpdateCollaborationPayment = (id: string, status: string, amount?: number) => request(`/collaborations/${id}/payment`, { method: 'PUT', body: JSON.stringify({ status, amount }) });
export const apiSubmitCollabReview = (collabId: string, rating: number, comment: string) => request(`/collaborations/${collabId}/review`, { method: 'POST', body: JSON.stringify({ rating, comment }) });
export const apiUpdateCampaignStatus = (id: string, status: string) => request(`/campaigns/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) });

// Owly Conversations
export const apiGetOwlyConversations = () => request('/owly/conversations');
export const apiGetOwlyMessages = (conversationId: string) => request(`/owly/conversations/${conversationId}/messages`);
export const apiCreateOwlyConversation = () => request('/owly/conversations', { method: 'POST' });
export const apiDeleteOwlyConversation = (conversationId: string) => request(`/owly/conversations/${conversationId}`, { method: 'DELETE' });

// Owly Chat (streaming — needs custom fetch with auth)
export const apiOwlyChat = async (message: string, conversationId: string | null) => {
  const token = getToken();
  return fetch(`${BASE_URL}/owly/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
};