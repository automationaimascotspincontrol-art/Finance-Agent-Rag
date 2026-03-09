import { Link } from "lucide-react";

function CorrelationMatrix({ data }) {
    if (!data) return null;

    // We need to extract the correlation matrices for the tickers
    // The structure depends on how RiskEngine sends it, but let's assume it's nested
    // Form: { "AAPL": { "correlation": { "NVDA": 0.45, "BTC-USD": 0.12, ... } }, ... }

    const tickers = Object.keys(data);
    if (tickers.length < 2) return null; // Can't show correlation of < 2 items

    const getCorrelationColor = (val) => {
        if (val >= 0.8) return 'rgba(34, 197, 94, 0.8)'; // Strong positive (Green)
        if (val >= 0.5) return 'rgba(74, 222, 128, 0.6)';
        if (val >= 0.2) return 'rgba(134, 239, 172, 0.4)';
        if (val > -0.2 && val < 0.2) return 'rgba(148, 163, 184, 0.1)'; // Neutral
        if (val <= -0.8) return 'rgba(239, 68, 68, 0.8)'; // Strong negative (Red - good for diversification!)
        if (val <= -0.5) return 'rgba(248, 113, 113, 0.6)';
        if (val <= -0.2) return 'rgba(252, 165, 165, 0.4)';
        return 'rgba(148, 163, 184, 0.2)';
    };

    return (
        <div className="portfolio-panel correlation-panel">
            <h3>
                <Link size={16} style={{ marginRight: '6px', verticalAlign: 'middle', color: '#a78bfa' }} />
                Correlation Network
            </h3>
            <p className="portfolio-subtitle">Cross-asset correlation matrix</p>

            <div className="matrix-container">
                <table className="correlation-table">
                    <thead>
                        <tr>
                            <th></th>
                            {tickers.map(t => (
                                <th key={`th-${t}`} title={t}>
                                    {t.split('-')[0].substring(0, 4)}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {tickers.map(rowTicker => {
                            const rowCorrelations = data[rowTicker]?.correlation || {};
                            return (
                                <tr key={`tr-${rowTicker}`}>
                                    <td className="row-header" title={rowTicker}>
                                        {rowTicker.split('-')[0].substring(0, 4)}
                                    </td>
                                    {tickers.map(colTicker => {
                                        // Diagonal is always 1
                                        let val = 1.0;
                                        if (rowTicker !== colTicker) {
                                            val = rowCorrelations[colTicker] ?? 0;
                                        }
                                        val = parseFloat(val);

                                        return (
                                            <td
                                                key={`td-${rowTicker}-${colTicker}`}
                                                style={{ backgroundColor: getCorrelationColor(val) }}
                                                title={`${rowTicker} vs ${colTicker}: ${val.toFixed(2)}`}
                                            >
                                                {val.toFixed(2)}
                                            </td>
                                        );
                                    })}
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default CorrelationMatrix;
