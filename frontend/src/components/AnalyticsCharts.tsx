import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
  AreaChart, Area,
  Legend
} from 'recharts';
import { getAvatarUrl } from '../services/api';

const COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#06B6D4', '#F59E0B'];

interface AnalyticsChartsProps {
  data: {
    hashtags: any[];
    mentions: any[];
    trends: any[];
    post_types: any[];
    hourly: any[];
    keywords: any[];
    benchmark: any;
    reviews: any[];
  };
}

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ data }) => {
  if (!data || (!data.hashtags.length && !data.mentions.length && !data.trends.length)) {
    return (
      <div className="analytics-empty">
        <h3>No Data Yet</h3>
        <p>Start posting or wait for your profile to be indexed by Owly to see your stats!</p>
      </div>
    );
  }

  return (
    <div className="analytics-grid">
      {/* 1. HASHTAGS */}
      <div className="analytics-card glass">
        <h3>Top Hashtags</h3>
        <p className="card-desc">Most frequent tags used in your recent posts.</p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.hashtags} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="rgba(255,255,255,0.1)" />
              <XAxis type="number" hide />
              <YAxis
                dataKey="name"
                type="category"
                stroke="var(--clr-text-muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={80}
              />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }}
              />
              <Bar dataKey="value" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. POST TYPES */}
      <div className="analytics-card glass">
        <h3>Post Distribution</h3>
        <p className="card-desc">Breakdown of formats (Reels vs. Images).</p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={data.post_types}
                cx="50%" cy="50%" innerRadius={50} outerRadius={75}
                paddingAngle={5} dataKey="value" animationDuration={1000}
              >
                {data.post_types.map((_entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }} />
              <Legend verticalAlign="bottom" align="center" iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. PRIME TIME */}
      <div className="analytics-card glass">
        <h3>Prime Time</h3>
        <p className="card-desc">Average engagement by hour of day.</p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.hourly}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="hour" stroke="var(--clr-text-muted)" fontSize={10} tickFormatter={(h) => `${h}h`} />
              <YAxis hide />
              <Tooltip contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }} />
              <Bar dataKey="engagement" fill="#6366f1" radius={[2, 2, 0, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. KEYWORDS */}
      <div className="analytics-card glass">
        <h3>Topic Highlights</h3>
        <p className="card-desc">Most used keywords in your captions.</p>
        <div className="keyword-cloud" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', marginTop: '1rem' }}>
          {data.keywords.map((kw, i) => (
            <span key={i} className="keyword-tag">
              {kw.name}
            </span>
          ))}
        </div>
      </div>

      {/* 5. FREQUENT COLLABORATORS (MENTIONS) */}
      <div className="analytics-card glass">
        <h3>Frequent Collaborators</h3>
        <p className="card-desc">Accounts you tag and work with most.</p>
        <div className="collaborator-list">
          {data.mentions.map((m, i) => (
            <div key={i} className="collaborator-item">
              <div className="collab-avatar-wrapper">
                <img
                  src={getAvatarUrl(m.pic) || `https://api.dicebear.com/7.x/avataaars/svg?seed=${m.name}`}
                  alt={m.name}
                  className="collab-avatar"
                />
                <span className="collab-count">{m.value}</span>
              </div>
              <span className="collab-name">@{m.name}</span>
            </div>
          ))}
          {data.mentions.length === 0 && <p className="no-data-msg">No collaborators found.</p>}
        </div>
      </div>

      {/* 6. REVIEWS SECTION */}
      <div className="analytics-card glass">
        <h3>Recent Reviews</h3>
        <p className="card-desc">What others say about working with you.</p>
        <div className="reviews-list">
          {data.reviews.map((r, i) => (
            <div key={i} className="review-item" style={{ marginBottom: '1rem', paddingBottom: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{r.reviewer}</span>
                <span style={{ color: '#f59e0b', fontSize: '0.8rem' }}>{'★'.repeat(r.rating)}</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', margin: 0, fontStyle: 'italic' }}>"{r.comment}"</p>
              <div style={{ textAlign: 'right', fontSize: '0.7rem', opacity: 0.5, marginTop: '0.2rem' }}>{r.date}</div>
            </div>
          ))}
          {data.reviews.length === 0 && (
            <div style={{ textAlign: 'center', padding: '1rem', opacity: 0.5 }}>
              <p style={{ fontSize: '0.9rem' }}>No reviews yet.</p>
              <p style={{ fontSize: '0.75rem' }}>Complete collaborations to earn reviews!</p>
            </div>
          )}
        </div>
      </div>

      {/* 7. TRENDS (WIDE) */}
      <div className="analytics-card glass wide">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3>Engagement Trends</h3>
            <p className="card-desc">Timeline of average interaction per post.</p>
          </div>
          <div className="benchmark-badge" style={{
            background: data.benchmark?.status === 'Above Average' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(59, 130, 246, 0.1)',
            color: data.benchmark?.status === 'Above Average' ? '#22c55e' : '#3b82f6',
            padding: '0.4rem 0.8rem',
            borderRadius: '12px',
            fontSize: '0.8rem',
            fontWeight: 700,
            border: '1px solid currentColor'
          }}>
            {data.benchmark?.user_rate}% ER <span style={{ opacity: 0.6, fontWeight: 500, marginLeft: 6 }}>vs {data.benchmark?.avg_rate}% Avg</span>
          </div>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.trends}>
              <defs>
                <linearGradient id="colorEng" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="date" stroke="var(--clr-text-muted)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--clr-text-muted)" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }} />
              <Area type="monotone" dataKey="engagement" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorEng)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsCharts;
