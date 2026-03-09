import { useState } from "react";
import { Send } from "lucide-react";

function ChatInput({ onSendMessage, isLoading }) {
    const [message, setMessage] = useState("");

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (message.trim() && !isLoading) {
                onSendMessage(message);
                setMessage("");
            }
        }
    };

    return (
        <div className="chat-input-wrapper">
            <textarea
                className="chat-input"
                placeholder="Send a message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                rows={1}
            />
            <button
                className="send-btn"
                onClick={() => {
                    if (message.trim() && !isLoading) {
                        onSendMessage(message);
                        setMessage("");
                    }
                }}
                disabled={isLoading || !message.trim()}
            >
                <Send size={18} />
            </button>
        </div>
    );
}
export default ChatInput;
