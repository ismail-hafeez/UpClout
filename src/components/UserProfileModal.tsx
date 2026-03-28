import React, { useEffect, useState } from 'react';
import { apiGetUserProfile, apiGetReviews, apiSubmitReview, getAvatarUrl, getCurrentUser, apiGetConnectionStatus, apiSendConnectionRequest, apiAcceptConnectionRequest, apiUnaddConnection, apiGetPublicCollaborations, apiGetCampaigns, apiCreateCollaboration } from '../services/api';
import Toast from './Toast';
import StarRating from './StarRating';
import './UserProfileModal.css';

interface UserProfileModalProps {
  userId: string;
  onClose: () => void;
  onMessageClick?: () => void;
}

const UserProfileModal: React.FC<UserProfileModalProps> = ({ userId, onClose, onMessageClick }) => {
  const [profile, setProfile] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [publicCollabs, setPublicCollabs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'reviews' | 'active_collabs' | 'past_collabs'>('reviews');
  const [loading, setLoading] = useState(true);
  
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  
  const [connStatus, setConnStatus] = useState<'none' | 'pending' | 'accepted' | 'self' | null>(null);
  const [isRequester, setIsRequester] = useState(false);
  const [connId, setConnId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [myCampaigns, setMyCampaigns] = useState<any[]>([]);
  const [inviteForm, setInviteForm] = useState({ campaignId: '', deliverablesText: '', deliverableCount: 1, paymentAmount: '' });
  const [inviteLoading, setInviteLoading] = useState(false);
  const [toast, setToast] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null);

  const currentUser = getCurrentUser();

  useEffect(() => {
    if (showInviteForm && myCampaigns.length === 0) {
      apiGetCampaigns().then(setMyCampaigns).catch(console.error);
    }
  }, [showInviteForm]);

  const handleSendInvite = async () => {
    if (!inviteForm.campaignId || !inviteForm.deliverablesText || !inviteForm.paymentAmount || inviteForm.deliverableCount < 1) return;
    setInviteLoading(true);
    try {
      const dels = [];
      const count = inviteForm.deliverableCount;
      for (let i = 0; i < count; i++) {
        dels.push({ type: count > 1 ? `${inviteForm.deliverablesText} ${i + 1}` : inviteForm.deliverablesText, status: 'Pending' });
      }

      await apiCreateCollaboration({
        campaignId: inviteForm.campaignId,
        influencerId: userId,
        deliverables: dels,
        paymentAmount: Number(inviteForm.paymentAmount),
        currency: 'PKR'
      });
      setShowInviteForm(false);
      setInviteForm({ campaignId: '', deliverablesText: '', deliverableCount: 1, paymentAmount: '' });
      setToast({ message: 'Invite sent successfully!', type: 'success' });
    } catch(err: any) {
      setToast({ message: err.response?.data?.message || 'Error sending invite', type: 'error' });
    } finally {
      setInviteLoading(false);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [profData, revData, connData, collabsData] = await Promise.all([
        apiGetUserProfile(userId),
        apiGetReviews(userId),
        apiGetConnectionStatus(userId),
        (currentUser?.id === userId || currentUser?._id === userId) ? apiGetPublicCollaborations(userId) : Promise.resolve([])
      ]);
      setProfile(profData);
      setReviews(revData.reviews || []);
      setPublicCollabs(collabsData || []);
      
      setConnStatus(connData.status);
      setIsRequester(connData.isRequester || false);
      setConnId(connData.connectionId || null);

      const myReview = (revData.reviews || []).find((r: any) => 
        r.reviewer?._id === currentUser?.id || 
        r.reviewer?._id === currentUser?._id ||
        r.reviewer?.id === currentUser?.id
      );
      if (myReview) {
        setRating(myReview.rating);
        setComment(myReview.comment || '');
        setHasReviewed(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [userId]);

  const handleSubmitReview = async () => {
    if (!rating) return;
    setSubmitting(true);
    try {
      await apiSubmitReview(userId, { rating, comment });
      setHasReviewed(true);
      await loadData(); // Fresh reload captures new cloutScore/reviews
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleConnect = async () => {
    setActionLoading(true);
    try {
      const res = await apiSendConnectionRequest(userId);
      setConnStatus(res.status);
      setConnId(res.connectionId || connId);
      setIsRequester(true);
    } catch(err) { console.error(err); }
    finally { setActionLoading(false); }
  };

  const handleAccept = async () => {
    if (!connId) return;
    setActionLoading(true);
    try {
      await apiAcceptConnectionRequest(connId);
      setConnStatus('accepted');
    } catch(err) { console.error(err); }
    finally { setActionLoading(false); }
  };

  const handleRemoveConnection = async () => {
    if (!connId) return;
    setActionLoading(true);
    try {
      await apiUnaddConnection(connId);
      setConnStatus('none');
      setConnId(null);
    } catch(err) { console.error(err); }
    finally { setActionLoading(false); }
  };

  if (loading || !profile) {
    return (
      <div className="up-modal-overlay">
        <div className="up-modal-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--clr-text-muted)' }}>
          <span className="spinner" style={{ display: 'inline-block', marginBottom: '1rem', width: '24px', height: '24px', borderTopColor: 'var(--clr-primary-light)' }} />
          <div>Loading profile...</div>
        </div>
      </div>
    );
  }

  const isSelf = currentUser?.id === userId || currentUser?._id === userId;

  return (
    <div className="up-modal-overlay" onClick={onClose}>
      <div className="up-modal-card" onClick={e => e.stopPropagation()}>
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        <header className="up-header">
          <button className="up-close" onClick={onClose} aria-label="Close">✕</button>
          
          <img 
            src={getAvatarUrl(profile.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${profile.username}`} 
            alt={profile.username} 
            className="up-avatar"
          />
          <div className="up-info">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', paddingRight: '3rem', flexWrap: 'wrap' }}>
              <h2>{profile.displayName || profile.username}</h2>
              {!isSelf && (
                connStatus === 'accepted' ? (
                  <>
                  <div style={{ display: 'flex', gap: '0.8rem' }}>
                    {onMessageClick && (
                      <button 
                        onClick={onMessageClick}
                        style={{
                          padding: '0.6rem 1.4rem', background: 'linear-gradient(135deg, var(--clr-primary-light), var(--clr-accent))', 
                          color: 'white', border: 'none', borderRadius: '24px', fontSize: '0.9rem', fontWeight: 600, 
                          cursor: 'pointer', transition: 'transform 0.15s, box-shadow 0.15s', boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)'
                        }}
                        onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 16px rgba(37, 99, 235, 0.3)'; }}
                        onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(37, 99, 235, 0.2)'; }}
                      >
                        Message
                      </button>
                    )}
                    <button 
                      onClick={handleRemoveConnection} disabled={actionLoading}
                      style={{
                        padding: '0.6rem 1.4rem', background: '#fee2e2', 
                        color: '#ef4444', border: 'none', borderRadius: '24px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s'
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = '#fecaca'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = '#fee2e2'; }}
                    >
                      {actionLoading ? '...' : 'Unadd'}
                    </button>
                    {currentUser?.userType === 'Brand' && (
                      <button 
                        onClick={() => setShowInviteForm(!showInviteForm)}
                        style={{
                          padding: '0.6rem 1.4rem', background: 'var(--clr-primary)', 
                          color: 'white', border: 'none', borderRadius: '24px', fontSize: '0.9rem', fontWeight: 600, 
                          cursor: 'pointer', transition: 'opacity 0.15s'
                        }}
                        onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
                        onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                      >
                        {showInviteForm ? 'Cancel Invite' : 'Invite to Campaign'}
                      </button>
                    )}
                  </div>
                  {showInviteForm && (
                    <div style={{ flexBasis: '100%', marginTop: '1rem', background: 'var(--clr-surface-2)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--clr-border)', width: '100%' }}>
                      <h4 style={{ margin: '0 0 1rem 0', color: 'var(--clr-text-primary)' }}>Invite to Campaign</h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                        <select value={inviteForm.campaignId} onChange={e => setInviteForm({...inviteForm, campaignId: e.target.value})} style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }}>
                          <option value="">Select a Campaign...</option>
                          {myCampaigns.map(c => <option key={c._id} value={c._id}>{c.title}</option>)}
                        </select>
                        <div style={{ display: 'flex', gap: '0.8rem' }}>
                          <input type="number" min="1" max="20" placeholder="Qty" value={inviteForm.deliverableCount} onChange={e => setInviteForm({...inviteForm, deliverableCount: Number(e.target.value) || 1})} style={{ width: '70px', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }} title="Number of deliverables (e.g. 2)" />
                          <input placeholder="Deliverable Type (e.g. Reel)" value={inviteForm.deliverablesText} onChange={e => setInviteForm({...inviteForm, deliverablesText: e.target.value})} style={{ flex: 1, padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }} />
                        </div>
                        <input type="number" placeholder="Payment Amount (PKR)" value={inviteForm.paymentAmount} onChange={e => setInviteForm({...inviteForm, paymentAmount: e.target.value})} style={{ padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }} />
                        <button disabled={inviteLoading || !inviteForm.campaignId || !inviteForm.deliverablesText || !inviteForm.paymentAmount} onClick={handleSendInvite} style={{ padding: '0.6rem', background: 'var(--clr-primary)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', opacity: (inviteLoading || !inviteForm.campaignId || !inviteForm.deliverablesText || !inviteForm.paymentAmount) ? 0.5 : 1 }}>
                          {inviteLoading ? 'Sending...' : 'Send Invite'}
                        </button>
                      </div>
                    </div>
                  )}
                </>
                ) : connStatus === 'none' ? (
                  <button 
                    onClick={handleConnect} disabled={actionLoading}
                    style={{
                      padding: '0.6rem 1.4rem', background: 'linear-gradient(135deg, #34d399, #10b981)', 
                      color: 'white', border: 'none', borderRadius: '24px', fontSize: '0.9rem', fontWeight: 600, 
                      cursor: 'pointer', transition: 'transform 0.15s, box-shadow 0.15s', boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)'
                    }}
                    onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 16px rgba(16, 185, 129, 0.3)'; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.2)'; }}
                  >
                    {actionLoading ? '...' : '+ Add'}
                  </button>
                ) : connStatus === 'pending' ? (
                  isRequester ? (
                    <button disabled style={{ padding: '0.6rem 1.4rem', background: 'var(--clr-surface-2)', color: 'var(--clr-text-muted)', border: '1.5px solid var(--clr-border)', borderRadius: '24px', fontSize: '0.9rem', fontWeight: 600 }}>
                      Request Sent
                    </button>
                  ) : (
                    <button onClick={handleAccept} disabled={actionLoading} style={{ padding: '0.6rem 1.4rem', background: 'var(--clr-secondary)', color: 'white', border: 'none', borderRadius: '24px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer' }}>
                      {actionLoading ? '...' : 'Accept Request'}
                    </button>
                  )
                ) : null
              )}
            </div>
            <p>@{profile.username}</p>
            <div className="up-stats">
              <StarRating value={profile.cloutScore} readOnly size={18} />
              <span style={{ color: 'var(--clr-text-primary)' }}>{profile.cloutScore > 0 ? profile.cloutScore.toFixed(1) : 'New'}</span>
              <span style={{ opacity: 0.4 }}>•</span>
              <span>{profile.reviewCount} Reviews</span>
            </div>
          </div>
        </header>

        <div className="up-body">
          {isSelf && (
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--clr-border)', overflowX: 'auto', whiteSpace: 'nowrap' }}>
              <h3 
                style={{ margin: 0, paddingBottom: '0.8rem', cursor: 'pointer', fontSize: '1.1rem', fontWeight: 600, borderBottom: activeTab === 'reviews' ? '2px solid var(--clr-primary)' : '2px solid transparent', color: activeTab === 'reviews' ? 'var(--clr-text-primary)' : 'var(--clr-text-muted)', transition: 'all 0.2s' }} 
                onClick={() => setActiveTab('reviews')}
              >
                Recent Reviews
              </h3>
              <h3 
                style={{ margin: 0, paddingBottom: '0.8rem', cursor: 'pointer', fontSize: '1.1rem', fontWeight: 600, borderBottom: activeTab === 'active_collabs' ? '2px solid var(--clr-primary)' : '2px solid transparent', color: activeTab === 'active_collabs' ? 'var(--clr-text-primary)' : 'var(--clr-text-muted)', transition: 'all 0.2s' }} 
                onClick={() => setActiveTab('active_collabs')}
              >
                Active Collaborations
              </h3>
              <h3 
                style={{ margin: 0, paddingBottom: '0.8rem', cursor: 'pointer', fontSize: '1.1rem', fontWeight: 600, borderBottom: activeTab === 'past_collabs' ? '2px solid var(--clr-primary)' : '2px solid transparent', color: activeTab === 'past_collabs' ? 'var(--clr-text-primary)' : 'var(--clr-text-muted)', transition: 'all 0.2s' }} 
                onClick={() => setActiveTab('past_collabs')}
              >
                Past Collaborations
              </h3>
            </div>
          )}

          {!isSelf && <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--clr-text-primary)' }}>Recent Reviews</h3>}

          {activeTab === 'active_collabs' && (
            <div className="up-collabs-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
              {publicCollabs.filter((c: any) => c.status !== 'Completed').length === 0 ? (
                <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.95rem' }}>No active collaborations.</p>
              ) : (
                publicCollabs.filter((c: any) => c.status !== 'Completed').map((collab: any) => (
                  <div key={collab._id} style={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '12px', padding: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--clr-text-primary)' }}>{collab.campaignId?.title || 'Unknown Campaign'}</h4>
                      <span style={{ padding: '0.2rem 0.6rem', background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>{collab.status}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--clr-text-muted)' }}>
                      <span><strong>{collab.deliverables?.length || 0}</strong> Deliverables</span>
                      <span><strong>${collab.paymentDetails?.amount}</strong> {collab.paymentDetails?.currency}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'past_collabs' && (
            <div className="up-collabs-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
              {publicCollabs.filter((c: any) => c.status === 'Completed').length === 0 ? (
                <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.95rem' }}>No past collaborations found.</p>
              ) : (
                publicCollabs.filter((c: any) => c.status === 'Completed').map((collab: any) => (
                  <div key={collab._id} style={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '12px', padding: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h4 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--clr-text-primary)' }}>{collab.campaignId?.title || 'Unknown Campaign'}</h4>
                      <span style={{ padding: '0.2rem 0.6rem', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>Completed</span>
                    </div>
                    <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--clr-text-muted)' }}>
                      <span><strong>{collab.deliverables?.length || 0}</strong> Deliverables</span>
                      <span><strong>${collab.paymentDetails?.amount}</strong> {collab.paymentDetails?.currency}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'reviews' && (
            <>
              {reviews.length === 0 ? (
                <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.95rem' }}>No reviews yet.</p>
              ) : (
                reviews.map((rev) => (
                  <div key={rev._id} className="up-review-card">
                    <div className="up-review-header">
                      <img 
                        src={getAvatarUrl(rev.reviewer?.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${rev.reviewer?.username}`} 
                        alt={rev.reviewer?.username} 
                        className="up-review-avatar"
                      />
                      <span className="up-review-author">{rev.reviewer?.displayName || rev.reviewer?.username}</span>
                      <StarRating value={rev.rating} readOnly size={15} />
                      <span className="up-review-date">{new Date(rev.createdAt).toLocaleDateString()}</span>
                    </div>
                    {rev.comment && <p className="up-review-comment">{rev.comment}</p>}
                  </div>
                ))
              )}

              {!isSelf && connStatus === 'accepted' ? (
            <div className="up-leave-review">
              <h3 className="up-section-title">
                {hasReviewed ? 'Edit Your Review' : 'Leave a Review'}
              </h3>
              {hasReviewed && (
                <p style={{ fontSize: '0.85rem', color: 'var(--clr-primary-light)', marginBottom: '0.8rem', background: 'rgba(56, 189, 248, 0.1)', padding: '0.6rem 0.8rem', borderRadius: '8px' }}>
                  You have already reviewed this creator. You can update your rating and comment below.
                </p>
              )}
              <div style={{ marginBottom: '0.5rem' }}>
                <StarRating value={rating} onChange={setRating} size={30} />
              </div>
              <textarea 
                className="up-textarea"
                placeholder={hasReviewed ? "Update your experience..." : "Share your experience working with this creator..."}
                value={comment}
                onChange={e => setComment(e.target.value)}
                maxLength={500}
              />
              <button 
                className="up-submit-btn" 
                disabled={submitting || rating === 0}
                onClick={handleSubmitReview}
              >
                {submitting ? 'Saving...' : hasReviewed ? 'Update Review' : 'Submit Review'}
              </button>
            </div>
          ) : !isSelf && (
            <div className="up-leave-review" style={{ userSelect: 'none', opacity: 0.7, paddingBottom: '2rem' }}>
              <p style={{ textAlign: 'center', color: 'var(--clr-text-muted)', fontSize: '1rem', background: 'var(--clr-surface-2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--clr-border)' }}>
                🔒 You must be connected to interact and leave a review.
              </p>
            </div>
          )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfileModal;
