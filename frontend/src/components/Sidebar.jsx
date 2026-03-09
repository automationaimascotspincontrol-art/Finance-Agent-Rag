import { useContext } from "react";
import ThemeToggle from "./ThemeToggle";
import { MessageSquarePlus, BookOpen, PieChart, Settings, TrendingUp } from "lucide-react";

function Sidebar() {
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <h2>⚡ QuantTerminal</h2>
                <ThemeToggle />
            </div>
            <div className="sidebar-content">
                <button className="new-chat-btn">
                    <MessageSquarePlus size={16} />
                    New Analysis
                </button>
                <div className="history-list">
                    <p className="history-title">Recent</p>
                    <button className="history-item">
                        <TrendingUp size={14} style={{ marginRight: '8px', opacity: 0.5 }} />
                        Analyze Nvidia
                    </button>
                    <button className="history-item">
                        <PieChart size={14} style={{ marginRight: '8px', opacity: 0.5 }} />
                        Portfolio Opt
                    </button>
                </div>
            </div>
            <div className="sidebar-footer">
                <button className="footer-btn">
                    <BookOpen size={15} />
                    Saved Reports
                </button>
                <button className="footer-btn">
                    <PieChart size={15} />
                    Portfolio
                </button>
                <button className="footer-btn">
                    <Settings size={15} />
                    Settings
                </button>
            </div>
        </aside>
    );
}
export default Sidebar;
