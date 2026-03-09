function TraceIndicator({ status }) {
    if (!status) return null;

    return (
        <div className="trace-indicator">
            <div className="spinner-small"></div>
            <span className="status-text">{status}</span>
        </div>
    );
}

export default TraceIndicator;
