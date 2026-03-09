import { TrendingUp, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

function MonteCarloPanel({ data }) {
    if (!data || data.error) return null;

    // Safely format percentage or return N/A if null/undefined
    const formatPct = (val) => val === null || val === undefined ? "N/A" : `${val}%`;

    // Convert data to a format suitable for rendering metrics and a chart
    const mcMetrics = [
        { label: "Expected Annual Return", value: formatPct(data.expected_return_annual), color: "#4ade80" },
        { label: "Annual Volatility", value: formatPct(data.expected_vol_annual), color: "#a78bfa" },
        { label: "Prob. of Loss", value: formatPct(data.prob_loss_next_year), color: "#f472b6" },
        { label: "VaR (95%)", value: formatPct(data.var_95_annual), color: "#ef4444" }
    ];

    const hasValidData = data.expected_return_annual !== null && data.expected_return_annual !== undefined;
    let chartData = [];

    if (hasValidData) {
        const expected = parseFloat(data.expected_return_annual);
        const vol = parseFloat(data.expected_vol_annual);

        // Create 7 bins for a rough bell curve
        chartData = [
            { name: "-3σ", value: 1, return: (expected - 3 * vol).toFixed(1) + "%" },
            { name: "-2σ", value: 5, return: (expected - 2 * vol).toFixed(1) + "%" },
            { name: "-1σ", value: 20, return: (expected - 1 * vol).toFixed(1) + "%" },
            { name: "Mean", value: 48, return: expected.toFixed(1) + "%" },
            { name: "+1σ", value: 20, return: (expected + 1 * vol).toFixed(1) + "%" },
            { name: "+2σ", value: 5, return: (expected + 2 * vol).toFixed(1) + "%" },
            { name: "+3σ", value: 1, return: (expected + 3 * vol).toFixed(1) + "%" }
        ];
    }

    return (
        <div className="portfolio-panel monte-carlo-panel">
            <h3>
                <TrendingUp size={16} style={{ marginRight: '6px', verticalAlign: 'middle', color: '#60a5fa' }} />
                Monte Carlo Simulation
            </h3>
            <p className="portfolio-subtitle">10,000 Paths (1-Year Horizon)</p>

            {data.error && data.error !== "Skipped simulation due to optimization failure." && (
                <div className="risk-warning" style={{ color: "#ef4444", backgroundColor: "rgba(239,68,68,0.1)", borderColor: "rgba(239,68,68,0.3)", marginBottom: "16px" }}>
                    <AlertTriangle size={14} style={{ marginRight: 6 }} />
                    {data.error}
                </div>
            )}

            <div className="mc-metrics-grid">
                {mcMetrics.map((m, i) => (
                    <div key={i} className="mc-metric-card">
                        <span className="mc-metric-label">{m.label}</span>
                        <span className="mc-metric-value" style={{ color: m.color }}>{m.value}</span>
                    </div>
                ))}
            </div>

            {hasValidData ? (
                <>
                    <div style={{ width: '100%', height: 160, marginTop: '20px' }}>
                        <ResponsiveContainer>
                            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                                <XAxis dataKey="return" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis tick={false} axisLine={false} tickLine={false} />
                                <Tooltip
                                    cursor={{ fill: '#334155' }}
                                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                    labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                                    formatter={(value, name, props) => [`Frequency: ${value}`, `Scenario`]}
                                />
                                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={index < 3 ? '#ef4444' : index === 3 ? '#60a5fa' : '#4ade80'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    {data.prob_loss_next_year && parseFloat(data.prob_loss_next_year) > 20 && (
                        <div className="risk-warning">
                            <AlertTriangle size={14} color="#f59e0b" style={{ marginRight: 6 }} />
                            Elevated tail risk detected in simulations.
                        </div>
                    )}
                </>
            ) : (
                <div style={{ marginTop: '20px', padding: '20px', textAlign: 'center', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '8px' }}>
                    <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Simulation skipped due to prior optimization failure.</p>
                </div>
            )}
        </div>
    );
}

export default MonteCarloPanel;
