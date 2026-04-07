import React, { useState, useEffect } from 'react';
import { apiGetCampaigns, apiCreateCampaign, getCurrentUser, apiGetCollaborations } from '../services/api';
import './CampaignDashboard.css';

interface CampaignDashboardProps {
  onNavigate: (page: string, params?: any) => void;
  onBack: () => void;
}

const CampaignDashboard: React.FC<CampaignDashboardProps> = ({ onNavigate, onBack }) => {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [activeDashboardTab, setActiveDashboardTab] = useState<'active' | 'completed'>('active');
  const [showCreate, setShowCreate] = useState(false);
  const user = getCurrentUser();

  const [form, setForm] = useState({ title: '', goal: '', budget: '', niche: '', timeline: '' });

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      if (user?.userType === 'Brand') {
        const [camps, collabs] = await Promise.all([apiGetCampaigns(), apiGetCollaborations()]);
        
        const formatted = camps.map((campaign: any) => {
          const relatedCollabs = collabs.filter((c: any) => c.campaignId?._id === campaign._id || c.campaignId === campaign._id);
          const spentAmount = relatedCollabs.reduce((acc: number, c: any) => acc + (c.paymentDetails?.amount || 0), 0);
          return { ...campaign, spentAmount };
        });
        
        setCampaigns(formatted);
      } else {
        const collabs = await apiGetCollaborations();
        const formatted = collabs.map((c: any) => ({
          ...(c.campaignId || {}),
          collabStatus: c.status,
          brandName: c.brandId?.displayName || c.brandId?.username || 'Sponsor',
          collabAmount: c.paymentDetails?.amount
        }));
        setCampaigns(formatted);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiCreateCampaign({ ...form, budget: Number(form.budget) });
      setShowCreate(false);
      setForm({ title: '', goal: '', budget: '', niche: '', timeline: '' });
      loadCampaigns();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="campaign-dash-root">
      <div className="campaign-dash">
        <button className="cd-back-btn" onClick={onBack}>
          <span className="icon">&larr;</span> Back to Dashboard
        </button>
        <div className="campaign-dash-header">
          <h1 className="campaign-dash-title">{user?.userType === 'Brand' ? 'My Campaigns' : 'My Collaborations'}</h1>
          {user?.userType === 'Brand' && (
            <button className="btn-primary" onClick={() => setShowCreate(true)}>+ Create Campaign</button>
          )}
        </div>

        <div className="campaign-tabs">
          <button 
            className={`campaign-tab-btn ${activeDashboardTab === 'active' ? 'active' : ''}`}
            onClick={() => setActiveDashboardTab('active')}
          >
            Active
          </button>
          <button 
            className={`campaign-tab-btn ${activeDashboardTab === 'completed' ? 'active' : ''}`}
            onClick={() => setActiveDashboardTab('completed')}
          >
            Completed
          </button>
        </div>

        <div className="campaign-list">
          {campaigns.filter(c => {
            const isCompleted = (c.collabStatus || c.status) === 'Completed';
            return activeDashboardTab === 'completed' ? isCompleted : !isCompleted;
          }).map(c => (
            <div key={c._id} className="campaign-card" onClick={() => onNavigate('campaign-details', { campaignId: c._id })}>
              <h3>{c.title}</h3>
              {user?.userType !== 'Brand' && c.brandName && (
                <span style={{ fontSize: '0.8rem', color: 'var(--clr-primary)', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
                  by {c.brandName}
                </span>
              )}
              <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', marginBottom: '0.5rem' }}>
                Started: {c.startDate ? new Date(c.startDate).toLocaleDateString() : 'N/A'}
              </div>
              <p>{c.goal}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className={`campaign-status ${(c.collabStatus || c.status || 'draft').toLowerCase().replace(' ', '-')}`}>
                  {c.collabStatus || c.status}
                </span>
                {user?.userType !== 'Brand' && (
                  <span style={{ fontWeight: 600 }}>
                    PKR {(c.collabAmount || 0).toLocaleString()}
                  </span>
                )}
              </div>

              {user?.userType === 'Brand' && (
                <div className="campaign-card-financials" onClick={e => e.stopPropagation()}>
                  <div className="campaign-card-budget-row">
                    <span className="spent">PKR {(c.spentAmount || 0).toLocaleString()} spent</span>
                    <span className="total">of PKR {(c.budget || 0).toLocaleString()}</span>
                  </div>
                  {(() => {
                    const percent = Math.min(100, Math.round(((c.spentAmount || 0) / (c.budget || 1)) * 100));
                    return (
                      <div className="mini-progress-bar">
                        <div className="mini-progress-fill" style={{ width: `${percent}%`, background: percent > 90 ? '#ef4444' : 'var(--clr-primary)' }}></div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          ))}
          {campaigns.filter(c => {
            const isCompleted = (c.collabStatus || c.status) === 'Completed';
            return activeDashboardTab === 'completed' ? isCompleted : !isCompleted;
          }).length === 0 && (
            <p style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--clr-text-muted)', marginTop: '2rem' }}>
              No {activeDashboardTab} {user?.userType === 'Brand' ? 'campaigns' : 'collaborations'} found.
            </p>
          )}
        </div>

        {showCreate && (
          <div className="modal-overlay">
            <form className="modal-content" onClick={(e) => e.stopPropagation()} onSubmit={handleCreate}>
              <h2>Create New Campaign</h2>
              <div className="form-group">
                <label>Title</label>
                <input required value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Goal</label>
                <input required value={form.goal} onChange={e => setForm({...form, goal: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Budget (PKR)</label>
                <input type="number" required value={form.budget} onChange={e => setForm({...form, budget: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Niche</label>
                <input value={form.niche} onChange={e => setForm({...form, niche: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Timeline</label>
                <input placeholder="e.g. 2 weeks" value={form.timeline} onChange={e => setForm({...form, timeline: e.target.value})} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignDashboard;
