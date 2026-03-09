import ReactMarkdown from "react-markdown";
import { User, Bot } from "lucide-react";

function Message({ role, content }) {
    return (
        <div className={`message ${role}`}>
            <div className="message-avatar">
                {role === "user" ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className="message-content">
                <ReactMarkdown>{content}</ReactMarkdown>
            </div>
        </div>
    );
}
export default Message;
