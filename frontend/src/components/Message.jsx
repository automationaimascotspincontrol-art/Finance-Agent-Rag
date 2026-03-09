import ReactMarkdown from "react-markdown";

function Message({ role, content }) {
    return (
        <div className={`message ${role}`}>
            <div className="message-avatar">
                {role === "user" ? "U" : "AI"}
            </div>
            <div className="message-content">
                <ReactMarkdown>{content}</ReactMarkdown>
            </div>
        </div>
    );
}
export default Message;
