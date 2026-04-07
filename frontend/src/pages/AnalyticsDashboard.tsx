import React, { useState, useEffect } from 'react';
import AnalyticsCharts from '../components/AnalyticsCharts';
import { apiGetAnalytics, getCurrentUser } from '../services/api';
import './AnalyticsDashboard.css';

interface AnalyticsDashboardProps {
  onBack: () => void;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ onBack }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const user = getCurrentUser();

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        if (!user?.username) return;
        const res = await apiGetAnalytics(user.username);
        setData(res);
      } catch (err) {
        console.error('Analytics Fetch Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [user?.username]);

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="loader"></div>
        <p>Crunching the numbers...</p>
      </div>
    );
  }

  return (
    <div className="analytics-root">
      <header className="analytics-header">
        <div className="analytics-nav">
          <button className="analytics-back-btn" onClick={onBack}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
            </svg>
            Back to Dashboard
          </button>
        </div>
        <h2 className="analytics-title">Performance <span className="accent">Insights</span></h2>
        <p className="analytics-subtitle">Detailed breakdown of your Instagram activity and audience engagement.</p>
      </header>
      <AnalyticsCharts data={data} />
    </div>
  );
};

export default AnalyticsDashboard;
