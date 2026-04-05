import React, { useState, useEffect } from 'react';
import AnalyticsCharts from '../components/AnalyticsCharts';
import { apiGetAnalytics, getCurrentUser } from '../services/api';
import './AnalyticsDashboard.css';

const AnalyticsDashboard: React.FC = () => {
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
        <h2 className="analytics-title">Performance <span className="accent">Insights</span></h2>
        <p className="analytics-subtitle">Detailed breakdown of your Instagram activity and audience engagement.</p>
      </header>
      <AnalyticsCharts data={data} />
    </div>
  );
};

export default AnalyticsDashboard;
