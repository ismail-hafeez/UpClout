import React, { useState, useRef } from 'react';
import { apiUpdateProfile, apiUploadAvatar, setCurrentUser, getCurrentUser, getAvatarUrl } from '../services/api';
import './EditProfileModal.css';

interface EditProfileModalProps {
  onClose: () => void;
  onSaved: (updatedUser: any) => void;
}

const EditProfileModal: React.FC<EditProfileModalProps> = ({ onClose, onSaved }) => {
  const currentUser = getCurrentUser();
  const [displayName, setDisplayName] = useState(currentUser?.displayName || '');
  const [previewSrc, setPreviewSrc] = useState<string>(getAvatarUrl(currentUser?.avatarUrl));
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [removedAvatar, setRemovedAvatar] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fallbackAvatar = `https://api.dicebear.com/7.x/thumbs/svg?seed=${currentUser?.username}`;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setRemovedAvatar(false);
    setPreviewSrc(URL.createObjectURL(file));
    setError('');
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      let updatedUser: any;

      if (selectedFile) {
        const res = await apiUploadAvatar(selectedFile);
        updatedUser = res.user;
        // Also update display name if changed
        if (displayName !== currentUser?.displayName) {
          const profileRes = await apiUpdateProfile({ displayName });
          updatedUser = profileRes.user;
        }
      } else if (removedAvatar) {
        const res = await apiUpdateProfile({ displayName, avatarUrl: '' });
        updatedUser = res.user;
      } else {
        // Just update display name
        const res = await apiUpdateProfile({ displayName });
        updatedUser = res.user;
      }

      setCurrentUser(updatedUser);
      onSaved(updatedUser);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="ep-overlay" onClick={onClose}>
      <div className="ep-card" onClick={e => e.stopPropagation()}>
        <div className="ep-header">
          <h2 className="ep-title">Edit Profile</h2>
          <button className="ep-close" onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Avatar picker */}
        <div className="ep-avatar-wrap" onClick={() => fileInputRef.current?.click()} title="Click to change photo">
          <img
            className="ep-avatar-preview"
            src={previewSrc || fallbackAvatar}
            alt="Avatar preview"
            onError={e => { (e.target as HTMLImageElement).src = fallbackAvatar; }}
          />
          <div className="ep-avatar-ring" />
          <div className="ep-avatar-overlay">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
        </div>
        <div className="ep-avatar-actions">
          <p className="ep-avatar-hint">Click photo to change</p>
          {previewSrc && (
            <button
              className="ep-btn--remove-dp"
              onClick={() => {
                setRemovedAvatar(true);
                setSelectedFile(null);
                setPreviewSrc('');
              }}
            >
              Remove photo
            </button>
          )}
        </div>

        <div className="ep-fields">
          <div className="ep-field">
            <label className="ep-label">Display Name</label>
            <input
              className="ep-input"
              type="text"
              placeholder="Your name"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              maxLength={40}
            />
          </div>
        </div>

        {error && <p className="ep-error">{error}</p>}

        <div className="ep-actions">
          <button className="ep-btn ep-btn--cancel" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button className="ep-btn ep-btn--save" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditProfileModal;
