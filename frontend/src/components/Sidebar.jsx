import { useContext } from "react";
import ThemeToggle from "./ThemeToggle";

function Sidebar() {
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <h2>AI Financial Agent</h2>
                <ThemeToggle />
            </div>
            <div className="sidebar-content">
                <button className="new-chat-btn">+ New Chat</button>
                <div className="history-list">
                    <p className="history-title">History</p>
                    <button className="history-item">Analyze Nvidia</button>
                    <button className="history-item">Portfolio Opt</button>
                </div>
            </div>
            <div className="sidebar-footer">
                <button className="footer-btn">Saved Reports</button>
                <button className="footer-btn">Portfolio</button>
                <button className="footer-btn">Settings</button>
            </div>
        </aside>
    );
}
export default Sidebar;
