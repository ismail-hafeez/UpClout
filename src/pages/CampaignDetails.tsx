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
  apiCreateCollaboration
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
  const [inviteForm, setInviteForm] = useState({ deliverablesText: '', deliverableCount: 1, paymentAmount: '' });

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

  const handleInvite = async () => {
    if (!selectedInfluencer || !inviteForm.deliverablesText || !inviteForm.paymentAmount) return;
    setInviteLoading(true);
    try {
      const dels = [];
      const count = inviteForm.deliverableCount;
      for (let i = 0; i < count; i++) {
        dels.push({ 
          type: count > 1 ? `${inviteForm.deliverablesText} ${i + 1}` : inviteForm.deliverablesText, 
          status: 'Pending' 
        });
      }

      await apiCreateCollaboration({
        campaignId: campaignId,
        influencerId: selectedInfluencer._id,
        deliverables: dels,
        paymentAmount: Number(inviteForm.paymentAmount),
        currency: 'PKR'
      });
      
      setToast({ message: `Invite sent to ${selectedInfluencer.displayName || selectedInfluencer.username}!`, type: 'success' });
      setShowInviteModal(false);
      setSelectedInfluencer(null);
      setInviteForm({ deliverablesText: '', deliverableCount: 1, paymentAmount: '' });
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

  const updatePayment = async (id: string, newStatus: string) => {
    await apiUpdateCollaborationPayment(id, newStatus);
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

  if (!campaign) return <div className="cd-dash">Loading campaign...</div>;

  return (
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
          {campaign.status === 'Completed' && (
            <span>Completed <strong>{campaign.completionDate ? new Date(campaign.completionDate).toLocaleDateString() : 'N/A'}</strong></span>
          )}
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>Status 
            {isBrand ? (
              <select 
                value={campaign.status} 
                onChange={e => updateCampaignStatus(e.target.value)}
                style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)', fontWeight: 600 }}
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

      <h2>Collaborations ({collaborations.length})</h2>
      <div className="cd-collab-list">
        {collaborations.map(collab => {
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
                <div>
                  {isBrand ? (
                    <select 
                      className="cd-status-select" 
                      value={collab.status} 
                      onChange={e => updateStatus(collab._id, e.target.value)}
                    >
                      <option value="Negotiating">Negotiating</option>
                      <option value="Content Creation">Content Creation</option>
                      <option value="Content Review">Content Review</option>
                      <option value="Completed">Completed</option>
                    </select>
                  ) : collab.status === 'Negotiating' ? (
                    <button 
                      onClick={() => updateStatus(collab._id, 'Content Creation')}
                      style={{ padding: '0.5rem 1rem', background: 'var(--clr-primary)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', transition: 'opacity 0.2s' }}
                      onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
                      onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                    >
                      Accept Invite &rarr;
                    </button>
                  ) : (
                    <span style={{ padding: '0.4rem 0.8rem', background: 'var(--clr-surface-2)', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 600, border: '1px solid var(--clr-border)', color: 'var(--clr-text-primary)' }}>
                      {collab.status}
                    </span>
                  )}
                </div>
              </div>

              <div className="cd-section">
                <h4>Deliverables ({completedDels}/{totalDels} Approved)</h4>
                {collab.deliverables?.length === 0 && <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.9rem' }}>No deliverables set yet.</p>}
                {collab.deliverables?.map((del: any, idx: number) => {
                  const isVisible = idx === 0 || collab.deliverables[idx - 1].status === 'Approved';
                  
                  if (!isVisible) {
                    return (
                      <div key={idx} className="cd-deliverable" style={{ display: 'flex', justifyContent: 'space-between', opacity: 0.5, background: 'var(--clr-surface-2)', border: '1px dashed var(--clr-border)', cursor: 'not-allowed' }}>
                        <span style={{ fontWeight: 500, color: 'var(--clr-text-muted)' }}>🔒 {del.type}</span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', fontWeight: 600 }}>Awaiting Brand Approval on previous item</span>
                      </div>
                    );
                  }

                  return (
                    <div key={idx} className="cd-deliverable" style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'stretch' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 500 }}>
                          {del.type} 
                          {del.link && <a href={del.link.startsWith('http') ? del.link : `https://${del.link}`} target="_blank" rel="noreferrer" style={{ marginLeft: 8, fontSize: '0.8rem', color: 'var(--clr-primary)' }}>(Open Link)</a>}
                          {del.status === 'Rejected' && <span style={{ marginLeft: 8, fontSize: '0.75rem', color: '#ef4444', fontWeight: 600, background: 'rgba(239, 68, 68, 0.1)', padding: '0.2rem 0.5rem', borderRadius: '12px' }}>Needs Revision</span>}
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
                      
                      {(!isBrand && del.status !== 'Approved') && (
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.2rem' }}>
                          <input 
                            id={`del-input-${idx}`}
                            placeholder="Add your content link here..."
                            defaultValue={del.link || ''}
                            onKeyDown={e => {
                              if (e.key === 'Enter') {
                                const btn = document.getElementById(`del-btn-${idx}`);
                                if (btn) btn.click();
                              }
                            }}
                            style={{ flex: 1, padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-surface)', color: 'var(--clr-text-primary)', fontSize: '0.9rem' }}
                          />
                          <button 
                            id={`del-btn-${idx}`}
                            onClick={() => {
                              const inputEl = document.getElementById(`del-input-${idx}`) as HTMLInputElement;
                              if (inputEl) {
                                const updatedDeliverables = [...collab.deliverables];
                                updatedDeliverables[idx].link = inputEl.value;
                                if (updatedDeliverables[idx].status === 'Pending' || updatedDeliverables[idx].status === 'Rejected') {
                                  updatedDeliverables[idx].status = 'Submitted';
                                }
                                apiUpdateCollaborationDeliverables(collab._id, updatedDeliverables);
                                setToast({ message: 'Link saved and submitted to Brand!', type: 'success' });
                                setTimeout(loadData, 500);
                              }
                            }}
                            style={{ padding: '0.6rem 1rem', background: 'var(--clr-primary)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', transition: 'opacity 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
                            onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                          >
                            Submit Link
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="cd-section" style={{ marginBottom: 0 }}>
                <h4>Payment Tracker</h4>
                <div className="cd-payment">
                  <span>Agreed Amount: <strong>PKR {collab.paymentDetails?.amount}</strong></span>
                  {isBrand ? (
                    <select 
                      className={`cd-badge ${collab.paymentDetails?.status === 'Paid' ? 'paid' : ''}`}
                      value={collab.paymentDetails?.status}
                      onChange={e => updatePayment(collab._id, e.target.value)}
                    >
                      <option value="Pending">Pending</option>
                      <option value="Paid">Paid</option>
                    </select>
                  ) : (
                    <span className={`cd-badge ${collab.paymentDetails?.status === 'Paid' ? 'paid' : ''}`}>
                      {collab.paymentDetails?.status}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        {collaborations.length === 0 && (
          <p style={{ textAlign: 'center', color: 'var(--clr-text-muted)' }}>No influencers have joined this campaign yet.</p>
        )}
      </div>

      {showInviteModal && (
        <div className="cd-modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="cd-modal-content" onClick={e => e.stopPropagation()}>
            <div className="cd-modal-header">
              <h2>Invite Influencers</h2>
              <button className="cd-modal-close" onClick={() => setShowInviteModal(false)}>✕</button>
            </div>
            
            {!selectedInfluencer ? (
              <>
                <div style={{ marginBottom: '1.5rem' }}>
                  <input 
                    className="cd-modal-search"
                    placeholder="Search connected influencers..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                  />
                </div>
                <div className="cd-connections-list">
                  {connections
                    .filter(c => (c.displayName || c.username).toLowerCase().includes(searchQuery.toLowerCase()))
                    .map(conn => (
                      <div key={conn._id} className="cd-connection-card">
                        <div className="cd-connection-info">
                          <img src={getAvatarUrl(conn.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${conn.username}`} alt={conn.username} />
                          <div>
                            <strong>{conn.displayName || conn.username}</strong>
                            <span>@{conn.username}</span>
                          </div>
                        </div>
                        <button className="cd-btn-mini" onClick={() => setSelectedInfluencer(conn)}>Select</button>
                      </div>
                    ))}
                  {connections.length === 0 && <p style={{ textAlign: 'center', gridColumn: '1/-1', color: 'var(--clr-text-muted)' }}>No connected influencers found.</p>}
                </div>
              </>
            ) : (
              <div className="cd-invite-form">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem', background: 'var(--clr-surface-2)', padding: '1rem', borderRadius: '12px' }}>
                  <img src={getAvatarUrl(selectedInfluencer.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${selectedInfluencer.username}`} alt={selectedInfluencer.username} style={{ width: 40, height: 40, borderRadius: '50%' }} />
                  <div>
                    <h4 style={{ margin: 0 }}>Inviting {selectedInfluencer.displayName || selectedInfluencer.username}</h4>
                    <button className="cd-btn-link" onClick={() => setSelectedInfluencer(null)}>Change Influencer</button>
                  </div>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                  <div className="form-group">
                    <label>Deliverables (e.g. 1 Instagram Reel)</label>
                    <div style={{ display: 'flex', gap: '0.8rem' }}>
                      <input 
                        type="number" min="1" max="20" 
                        value={inviteForm.deliverableCount} 
                        onChange={e => setInviteForm({...inviteForm, deliverableCount: Number(e.target.value) || 1})} 
                        style={{ width: '70px', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }} 
                      />
                      <input 
                        placeholder="Deliverable Type (e.g. Reel)" 
                        value={inviteForm.deliverablesText} 
                        onChange={e => setInviteForm({...inviteForm, deliverablesText: e.target.value})} 
                        style={{ flex: 1, padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)' }} 
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Payment Amount (PKR)</label>
                    <input 
                      type="number" 
                      placeholder="e.g. 5000" 
                      value={inviteForm.paymentAmount} 
                      onChange={e => setInviteForm({...inviteForm, paymentAmount: e.target.value})} 
                      style={{ padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--clr-border)', background: 'var(--clr-bg)', color: 'var(--clr-text-primary)', width: '100%' }} 
                    />
                  </div>
                  <button 
                    className="cd-btn-primary" 
                    disabled={inviteLoading || !inviteForm.deliverablesText || !inviteForm.paymentAmount} 
                    onClick={handleInvite}
                  >
                    {inviteLoading ? 'Sending...' : 'Send Invitation'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignDetails;
