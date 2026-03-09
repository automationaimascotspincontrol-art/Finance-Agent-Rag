import { PieChart as PieChartIcon } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ['#4ade80', '#60a5fa', '#f472b6', '#a78bfa', '#fbbf24', '#2dd4bf', '#fb923c'];

function PortfolioPanel({ allocation }) {
    if (!allocation) return null;

    // Convert allocation dict into array for Recharts
    const data = Object.entries(allocation)
        .filter(([_, pct]) => pct > 0 && pct !== "error")
        .map(([ticker, pct]) => ({
            name: ticker,
            value: pct,
        }));

    const isError = allocation.error;

    return (
        <div className="portfolio-panel">
            <h3>
                <PieChartIcon size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                Optimized Portfolio
            </h3>
            {isError ? (
                <div className="error-state">
                    <p style={{ color: '#ef4444', fontSize: '0.9rem', marginTop: '8px' }}>
                        {allocation.error}
                    </p>
                </div>
            ) : (
                <>
                    <p className="portfolio-subtitle">Black-Litterman Max-Sharpe Allocation</p>

                    <div style={{ width: '100%', height: 200, margin: '16px 0' }}>
                        <ResponsiveContainer>
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    formatter={(value) => `${value}%`}
                                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                    itemStyle={{ color: '#e2e8f0' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="allocation-list">
                        {data.map((item, index) => (
                            <div key={item.name} className="allocation-item">
                                <div className="allocation-header">
                                    <span className="ticker" style={{ borderLeft: `3px solid ${COLORS[index % COLORS.length]}`, paddingLeft: '6px' }}>
                                        {item.name}
                                    </span>
                                    <span className="percentage">{item.value}%</span>
                                </div>
                                <div className="progress-bar-bg">
                                    <div className="progress-bar-fill" style={{ width: `${item.value}%`, backgroundColor: COLORS[index % COLORS.length] }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

export default PortfolioPanel;
