function PortfolioPanel({ allocation }) {
    if (!allocation) return null;

    return (
        <div className="portfolio-panel">
            <h3>Optimized Portfolio</h3>
            <div className="allocation-list">
                {Object.entries(allocation).map(([ticker, pct]) => (
                    <div key={ticker} className="allocation-item">
                        <span className="ticker">{ticker}</span>
                        <span className="percentage">{pct}%</span>
                        <div className="progress-bar-bg">
                            <div className="progress-bar-fill" style={{ width: `${pct}%` }}></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default PortfolioPanel;
