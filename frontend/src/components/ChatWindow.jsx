import { useEffect, useRef } from "react";
import Message from "./Message";
import ChatInput from "./ChatInput";
import { Bot, Sparkles, TrendingUp, Shield, BarChart3 } from "lucide-react";

function ChatWindow({ messages, onSendMessage, isLoading }) {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const quickActions = [
        "Analyze NVDA, TSLA, BTC",
        "Build a hedge-fund portfolio",
        "Compare Tesla vs Apple risk",
        "Show VaR for my portfolio",
    ];

    return (
        <main className="chat-window">
            <div className="messages-container" ref={scrollRef}>
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">
                            <Bot size={32} color="white" />
                        </div>
                        <h1>AI Quant Research Terminal</h1>
                        <p>
                            Institutional-grade analysis powered by 50+ quantitative factors,
                            Monte Carlo simulations, and real-time market data.
                        </p>
                        <div className="quick-actions">
                            {quickActions.map((action, idx) => (
                                <button
                                    key={idx}
                                    className="quick-action-btn"
                                    onClick={() => onSendMessage(action)}
                                >
                                    {idx === 0 && <TrendingUp size={13} style={{ marginRight: 4 }} />}
                                    {idx === 1 && <BarChart3 size={13} style={{ marginRight: 4 }} />}
                                    {idx === 2 && <Shield size={13} style={{ marginRight: 4 }} />}
                                    {idx === 3 && <Sparkles size={13} style={{ marginRight: 4 }} />}
                                    {action}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <Message key={idx} role={msg.role} content={msg.content} />
                    ))
                )}
                {isLoading && (
                    <div className="message ai loading">
                        <div className="message-avatar">
                            <Bot size={16} />
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div className="loading-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <span className="loading-text">Computing factors...</span>
                        </div>
                    </div>
                )}
            </div>
            <div className="input-container">
                <ChatInput onSendMessage={onSendMessage} isLoading={isLoading} />
                <div className="input-hint">
                    <span>Powered by 50+ quantitative signals • Real-time data • Zero hallucinations</span>
                </div>
            </div>
        </main>
    );
}
export default ChatWindow;
