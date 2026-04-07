import React, { useState, useEffect } from 'react';
import { 
  apiGetCampaigns, 
  apiGetCollaborations, 
  apiUpdateCollaborationStatus, 
  apiUpdateCollaborationDeliverables, 
  apiUpdateCollaborationPayment, 
  apiUpdateCampaignStatus, 
  getAvatarUrl, 
  getCurrentUser,
  apiGetAcceptedConnections,
  apiCreateCollaboration,
  apiSearchUsers,
  apiRejectCollaboration,
  apiSubmitCollabReview
} from '../services/api';
import Toast from '../components/Toast';
import './CampaignDetails.css';

interface CampaignDetailsProps {
  campaignId: string;
  onNavigate: (page: string, params?: any) => void;
  onBack: () => void;
}

const CampaignDetails: React.FC<CampaignDetailsProps> = ({ campaignId, onNavigate, onBack }) => {
  const [campaign, setCampaign] = useState<any>(null);
  const [collaborations, setCollaborations] = useState<any[]>([]);
  const [toast, setToast] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null);
  
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [connections, setConnections] = useState<any[]>([]);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [selectedInfluencer, setSelectedInfluencer] = useState<any>(null);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const user = getCurrentUser();
  const isBrand = user?.userType === 'Brand';

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 3000);
    return () => clearInterval(interval);
  }, [campaignId]);

  const loadData = async () => {
    try {
      const collabs = await apiGetCollaborations();
      const relatedCollabs = collabs.filter((c: any) => c.campaignId?._id === campaignId || c.campaignId === campaignId);
      setCollaborations(relatedCollabs);

      if (relatedCollabs.length > 0 && relatedCollabs[0].campaignId) {
        setCampaign(relatedCollabs[0].campaignId);
      } else {
        if (isBrand) {
          const camps = await apiGetCampaigns();
          const foundCamp = camps.find((c: any) => c._id === campaignId);
          setCampaign(foundCamp);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadConnections = async () => {
    try {
      const data = await apiGetAcceptedConnections();
      setConnections(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await apiSearchUsers(query);
        setSearchResults(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsSearching(false);
      }
    }, 400);
  };

  const handleInvite = async (influencer: any) => {
    if (!influencer || !campaign) return;
    setInviteLoading(true);
    try {
      // Use campaign budget and a default deliverable based on campaign title/goal
      await apiCreateCollaboration({
        campaignId: campaignId,
        influencerId: influencer._id,
        deliverables: [{ type: campaign.title, status: 'Pending' }],
        paymentAmount: 0,
        currency: 'PKR'
      });
      
      setToast({ message: `Invite sent to ${influencer.displayName || influencer.username}!`, type: 'success' });
      setShowInviteModal(false);
      loadData();
    } catch (err: any) {
      setToast({ message: err.message || 'Error sending invite', type: 'error' });
    } finally {
      setInviteLoading(false);
    }
  };

  const updateStatus = async (id: string, newStatus: string) => {
    await apiUpdateCollaborationStatus(id, newStatus);
    loadData();
  };

  const updatePayment = async (id: string, newStatus: string, amount?: number) => {
    await apiUpdateCollaborationPayment(id, newStatus, amount);
    loadData();
  };

  const updateDeliverableStatus = async (collab: any, dIndex: number, newStatus: string) => {
    const updatedDeliverables = [...collab.deliverables];
    updatedDeliverables[dIndex].status = newStatus;
    await apiUpdateCollaborationDeliverables(collab._id, updatedDeliverables);
    loadData();
  };

  const updateCampaignStatus = async (newStatus: string) => {
    if (!campaign) return;
    await apiUpdateCampaignStatus(campaign._id, newStatus);
    loadData();
    if (newStatus === 'Completed') {
      setToast({ message: 'Campaign & Collaborations marked as Completed!', type: 'success' });
    } else {
      setToast({ message: `Campaign status updated to ${newStatus}`, type: 'success' });
    }
  };

  const renderCollabCard = (collab: any) => {
    const influencer = collab.influencerId;
    const totalDels = collab.deliverables?.length || 0;
    const completedDels = collab.deliverables?.filter((d: any) => d.status === 'Approved').length || 0;

    return (
      <div key={collab._id} className="cd-collab-card">
        <div className="cd-collab-header">
          <div className="cd-influencer">
            <img src={getAvatarUrl(influencer.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${influencer.username}`} alt={influencer.username} className="cd-avatar" />
            <div>
              <h3 style={{ margin: 0 }}>{influencer.displayName || influencer.username}</h3>
              <p style={{ margin: 0, color: 'var(--clr-text-muted)', fontSize: '0.9rem' }}>@{influencer.username}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {isBrand && collab.status !== 'Invited' && collab.status !== 'Declined' && (
              <button 
                className="cd-btn-mini" 
                style={{ background: '#6366f1', color: 'white' }}
                onClick={() => {
                  localStorage.setItem('openChatUserId', influencer._id);
                  onNavigate('chats');
                }}
              >
                Message
              </button>
            )}
            {isBrand ? (
              <select 
                className="cd-status-select" 
                value={collab.status} 
                onChange={e => updateStatus(collab._id, e.target.value)}
              >
                <option value="Invited">Invited</option>
                <option value="Declined">Declined</option>
                <option value="Negotiating">Negotiating</option>
                <option value="Content Creation">Content Creation</option>
                <option value="Content Review">Content Review</option>
                <option value="Completed">Completed</option>
              </select>
            ) : collab.status === 'Invited' ? (
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                <button 
                  onClick={() => updateStatus(collab._id, 'Content Creation')}
                  style={{ padding: '0.5rem 1rem', background: 'var(--clr-primary)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}
                >
                  Accept Invite
                </button>
                <button 
                  onClick={async () => {
                    await apiRejectCollaboration(collab._id);
                    loadData();
                  }}
                  style={{ padding: '0.5rem 1rem', background: 'var(--clr-surface-2)', color: 'var(--clr-text-primary)', border: '1px solid var(--clr-border)', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}
                >
                  Decline
                </button>
              </div>
            ) : (
              <span className={`cd-badge ${collab.status.toLowerCase()}`}>
                {collab.status}
              </span>
            )}
          </div>
        </div>

        {collab.status !== 'Declined' && (
          <>
            <div className="cd-section">
              <h4>Deliverables ({completedDels}/{totalDels} Approved)</h4>
              {collab.deliverables?.length === 0 && <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.9rem' }}>No deliverables set yet.</p>}
              {collab.deliverables?.map((del: any, idx: number) => {
                const isVisible = idx === 0 || collab.deliverables[idx - 1].status === 'Approved';
                
                if (!isVisible) {
                  return (
                    <div key={idx} className="cd-deliverable" style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.5, background: 'var(--clr-surface-2)', border: '1px dashed var(--clr-border)', cursor: 'not-allowed' }}>
                      <span style={{ fontWeight: 500, color: 'var(--clr-text-muted)' }}>🔒 {del.type}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', fontWeight: 600 }}>Awaiting Brand Approval</span>
                    </div>
                  );
                }

                return (
                  <div key={idx} className="cd-deliverable" style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'stretch' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 500 }}>
                        {del.type} 
                        {del.link && <a href={del.link.startsWith('http') ? del.link : `https://${del.link}`} target="_blank" rel="noreferrer" style={{ marginLeft: 8, fontSize: '0.8rem', color: 'var(--clr-primary)' }}>(Open Link)</a>}
                      </span>
                      
                      {isBrand ? (
                        <select 
                          className={`cd-del-status ${del.status.toLowerCase()}`}
                          value={del.status}
                          onChange={e => updateDeliverableStatus(collab, idx, e.target.value)}
                        >
                          <option value="Pending">Pending</option>
                          <option value="Submitted">Submitted</option>
                          <option value="Approved">Approved</option>
                          <option value="Rejected">Rejected</option>
                        </select>
                      ) : (
                        <span className={`cd-del-status ${del.status.toLowerCase()}`}>{del.status}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="cd-section" style={{ marginBottom: 0 }}>
              <h4>Payment Tracker</h4>
              <div className="cd-payment" style={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Agreed Amount: <strong>PKR {collab.paymentDetails?.amount?.toLocaleString()}</strong></span>
                  <span className={`cd-badge ${collab.paymentDetails?.status === 'Paid' ? 'paid' : ''}`}>
                    {collab.paymentDetails?.status}
                  </span>
                </div>
                
                {isBrand && (
                  <div style={{ display: 'flex', gap: '0.5rem', borderTop: '1px solid var(--clr-border)', paddingTop: '1rem' }}>
                    <input 
                      id={`pay-amt-${collab._id}`}
                      type="number"
                      placeholder="Enter amount..."
                      defaultValue={collab.paymentDetails?.amount || 0}
                      style={{ flex: 1, padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'white', color: 'var(--clr-text-primary)' }}
                    />
                    <select 
                      id={`pay-status-${collab._id}`}
                      defaultValue={collab.paymentDetails?.status}
                      style={{ padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'white', color: 'var(--clr-text-primary)' }}
                    >
                      <option value="Pending">Pending</option>
                      <option value="Paid">Paid</option>
                    </select>
                    <button 
                      className="cd-btn-mini"
                      onClick={() => {
                        const amt = (document.getElementById(`pay-amt-${collab._id}`) as HTMLInputElement).value;
                        const stat = (document.getElementById(`pay-status-${collab._id}`) as HTMLSelectElement).value;
                        updatePayment(collab._id, stat, Number(amt));
                        setToast({ message: 'Payment updated!', type: 'success' });
                      }}
                    >
                      Update
                    </button>
                  </div>
                )}
              </div>
            </div>

            {collab.status === 'Completed' && (
              <div style={{ marginTop: '1rem', borderTop: '1px solid var(--clr-border)', paddingTop: '1rem', display: 'flex', justifyContent: 'center' }}>
                <button 
                  className="cd-btn-mini"
                  style={{ background: 'var(--grad-primary)', color: 'white', padding: '0.6rem 2rem', width: '100%', fontSize: '0.9rem' }}
                  onClick={() => {
                    const rating = prompt('Enter rating (1-5):', '5');
                    const comment = prompt('Enter your review comment:');
                    if (rating && comment) {
                      apiSubmitCollabReview(collab._id, Number(rating), comment)
                        .then(() => setToast({ message: 'Review submitted successfully!', type: 'success' }))
                        .catch((err: any) => setToast({ message: err.message || 'Error submitting review', type: 'error' }));
                    }
                  }}
                >
                  ⭐ Review Collaboration
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  if (!campaign) return <div className="cd-dash">Loading campaign...</div>;

  return (
    <div className="cd-root">
      <div className="cd-dash">
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        <button className="cd-back-btn" onClick={onBack}>
          <span className="icon">&larr;</span> Back to Dashboard
        </button>
        
        <div className="cd-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <h1 className="cd-title">{campaign.title}</h1>
            {isBrand && (
              <button 
                className="cd-invite-btn" 
                onClick={() => { setShowInviteModal(true); loadConnections(); }}
                title="Invite Influencer"
              >
                +
              </button>
            )}
          </div>
          <div className="cd-meta">
            <span>Goal <strong>{campaign.goal}</strong></span>
            {isBrand && <span>Initial Budget <strong>PKR {campaign.budget.toLocaleString()}</strong></span>}
            <span>Timeline <strong>{campaign.timeline || 'TBD'}</strong></span>
            <span>Started <strong>{campaign.startDate ? new Date(campaign.startDate).toLocaleDateString() : 'N/A'}</strong></span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>Status 
              {isBrand ? (
                <select 
                  value={campaign.status} 
                  onChange={e => updateCampaignStatus(e.target.value)}
                  style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }}
                >
                  <option value="Active">Active</option>
                  <option value="Paused">Paused</option>
                  <option value="Completed">Completed</option>
                </select>
              ) : (
                <strong>{campaign.status}</strong>
              )}
            </span>
          </div>

          {isBrand && (
            <div className="cd-financial-stats">
              {(() => {
                const totalCommitted = collaborations.reduce((acc, c) => acc + (c.paymentDetails?.amount || 0), 0);
                const totalPaid = collaborations.reduce((acc, c) => acc + (c.paymentDetails?.status === 'Paid' ? (c.paymentDetails?.amount || 0) : 0), 0);
                const remaining = campaign.budget - totalCommitted;
                const percentUsed = Math.min(100, Math.round((totalCommitted / campaign.budget) * 100));

                return (
                  <>
                    <div className="cd-stat-grid">
                      <div className="cd-stat-card">
                        <span className="label">Committed (Spent)</span>
                        <strong className="value">PKR {totalCommitted.toLocaleString()}</strong>
                      </div>
                      <div className="cd-stat-card">
                        <span className="label">Actual Paid</span>
                        <strong className="value success">PKR {totalPaid.toLocaleString()}</strong>
                      </div>
                      <div className="cd-stat-card">
                        <span className="label">Remaining Budget</span>
                        <strong className={`value ${remaining < 0 ? 'danger' : ''}`}>PKR {remaining.toLocaleString()}</strong>
                      </div>
                    </div>
                    <div className="cd-progress-container">
                      <div className="cd-progress-meta">
                        <span>Budget Usage</span>
                        <span>{percentUsed}%</span>
                      </div>
                      <div className="cd-progress-bar">
                        <div className="cd-progress-fill" style={{ width: `${percentUsed}%`, background: percentUsed > 90 ? '#ef4444' : 'var(--clr-primary)' }}></div>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>
          )}
        </div>

        {/* --- Collaboration Sections --- */}
        {(() => {
          const sent = collaborations.filter(c => c.status === 'Invited');
          const accepted = collaborations.filter(c => c.status !== 'Invited' && c.status !== 'Declined');
          const declined = collaborations.filter(c => c.status === 'Declined');

          return (
            <>
              {sent.length > 0 && (
                <div style={{ marginBottom: '3rem' }}>
                  <h2 style={{ marginBottom: '1rem', borderLeft: '4px solid #f59e0b', paddingLeft: '1rem', color: 'var(--clr-text-primary)' }}>Invitations Sent ({sent.length})</h2>
                  <div className="cd-collab-list">
                    {sent.map(collab => renderCollabCard(collab))}
                  </div>
                </div>
              )}

              <div style={{ marginBottom: '3rem' }}>
                <h2 style={{ marginBottom: '1rem', borderLeft: '4px solid #10b981', paddingLeft: '1rem', color: 'var(--clr-text-primary)' }}>Accepted Collaborations ({accepted.length})</h2>
                <div className="cd-collab-list">
                  {accepted.map(collab => renderCollabCard(collab))}
                </div>
                {accepted.length === 0 && (
                  <p style={{ textAlign: 'center', color: 'var(--clr-text-muted)', background: 'rgba(255,255,255,0.2)', padding: '2rem', borderRadius: '12px' }}>No influencers have accepted yet.</p>
                )}
              </div>

              {declined.length > 0 && (
                <div style={{ marginBottom: '3rem' }}>
                  <h2 style={{ marginBottom: '1rem', borderLeft: '4px solid #ef4444', paddingLeft: '1rem', color: 'var(--clr-text-primary)' }}>Declined ({declined.length})</h2>
                  <div className="cd-collab-list">
                    {declined.map(collab => renderCollabCard(collab))}
                  </div>
                </div>
              )}
            </>
          );
        })()}

        {showInviteModal && (
          <div className="cd-modal-overlay" onClick={() => setShowInviteModal(false)}>
            <div className="cd-modal-content" onClick={e => e.stopPropagation()}>
              <div className="cd-modal-header">
                <h2>Invite Influencers</h2>
                <button className="cd-modal-close" onClick={() => setShowInviteModal(false)}>✕</button>
              </div>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <input 
                  className="cd-modal-search"
                  placeholder="Search influencers by name or username..."
                  value={searchQuery}
                  onChange={e => handleSearch(e.target.value)}
                />
              </div>
              <div className="cd-connections-list">
                {isSearching ? (
                  <p style={{ textAlign: 'center', gridColumn: '1/-1', color: 'var(--clr-text-muted)' }}>Searching...</p>
                ) : searchQuery.length < 2 ? (
                  connections.map(conn => (
                    <div key={conn._id} className="cd-connection-card">
                      <div className="cd-connection-info">
                        <img src={getAvatarUrl(conn.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${conn.username}`} alt={conn.username} />
                        <div>
                          <strong>{conn.displayName || conn.username}</strong>
                          <span>@{conn.username}</span>
                        </div>
                      </div>
                      <button 
                        className="cd-btn-mini" 
                        disabled={inviteLoading}
                        onClick={() => handleInvite(conn)}
                      >
                        {inviteLoading ? '...' : 'Invite'}
                      </button>
                    </div>
                  ))
                ) : (
                  searchResults.map(res => (
                    <div key={res._id} className="cd-connection-card">
                      <div className="cd-connection-info">
                        <img src={getAvatarUrl(res.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${res.username}`} alt={res.username} />
                        <div>
                          <strong>{res.displayName || res.username}</strong>
                          <span>@{res.username}</span>
                        </div>
                      </div>
                      <button 
                        className="cd-btn-mini" 
                        disabled={inviteLoading}
                        onClick={() => handleInvite(res)}
                      >
                        {inviteLoading ? '...' : 'Invite'}
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignDetails;
