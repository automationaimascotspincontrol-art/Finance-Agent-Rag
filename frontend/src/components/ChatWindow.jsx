import { useEffect, useRef } from "react";
import Message from "./Message";
import ChatInput from "./ChatInput";

function ChatWindow({ messages, onSendMessage, isLoading }) {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    return (
        <main className="chat-window">
            <div className="messages-container" ref={scrollRef}>
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <h1>How can I help you invest today?</h1>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <Message key={idx} role={msg.role} content={msg.content} />
                    ))
                )}
                {isLoading && (
                    <div className="message ai loading">
                        <div className="loading-spinner"></div>
                        <p>Analyzing...</p>
                    </div>
                )}
            </div>
            <div className="input-container">
                <ChatInput onSendMessage={onSendMessage} isLoading={isLoading} />
            </div>
        </main>
    );
}
export default ChatWindow;
