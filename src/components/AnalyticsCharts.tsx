import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, 
  AreaChart, Area, 
  Legend
} from 'recharts';

const COLORS = ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe'];

interface AnalyticsChartsProps {
  data: {
    hashtags: any[];
    mentions: any[];
    trends: any[];
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
      {/* HASHTAGS BAR CHART */}
      <div className="analytics-card glass">
        <h3>Top Hashtags</h3>
        <p className="card-desc">Most frequent tags used in your recent posts.</p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.hashtags} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="rgba(255,255,255,0.1)" />
              <XAxis type="number" hide />
              <YAxis 
                dataKey="name" 
                type="category" 
                stroke="var(--clr-text-muted)" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                width={80}
              />
              <Tooltip 
                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }}
              />
              <Bar dataKey="value" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={20} animationDuration={1500} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* MENTIONS PIE CHART */}
      <div className="analytics-card glass">
        <h3>Top Mentions</h3>
        <p className="card-desc">Accounts you tag most frequently.</p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data.mentions}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={85}
                paddingAngle={5}
                dataKey="value"
                animationDuration={1500}
              >
                {data.mentions.map((_entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                 contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ENGAGEMENT TREND LINE CHART */}
      <div className="analytics-card glass wide">
        <h3>Engagement Trends</h3>
        <p className="card-desc">Your average engagement (Likes + Comments) over your recent posts.</p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data.trends}>
              <defs>
                <linearGradient id="colorEng" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="date" stroke="var(--clr-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--clr-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                 contentStyle={{ background: 'var(--clr-surface)', border: '1px solid var(--clr-border)', borderRadius: '8px' }}
              />
              <Area 
                type="monotone" 
                dataKey="engagement" 
                stroke="#8b5cf6" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorEng)" 
                animationDuration={2000}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsCharts;
