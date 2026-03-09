import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import { ThemeProvider } from "./context/ThemeContext";
import { sendChatQueryStreaming } from "./api/chatApi";
import TraceIndicator from "./components/TraceIndicator";
import "./index.css";
import "./styles/light.css";
import "./styles/dark.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [traceStatus, setTraceStatus] = useState("");
  const [allocation, setAllocation] = useState(null);

  const handleSendMessage = async (query) => {
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsLoading(true);
    setTraceStatus("Planner Agent starting...");

    await sendChatQueryStreaming(
      query,
      (status) => {
        setTraceStatus(status);
      },
      (data) => {
        if (data.type === "final") {
          setMessages((prev) => [...prev, { role: "ai", content: data.content }]);
          if (data.portfolio_data) {
            setAllocation(data.portfolio_data);
          }
          setIsLoading(false);
          setTraceStatus("");
        }
      }
    );
  };

  return (
    <ThemeProvider>
      <div className="app-layout">
        <Sidebar />
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
        <TraceIndicator status={traceStatus} />
        {allocation && (
          <div className="right-panel">
            <PortfolioPanel allocation={allocation} />
          </div>
        )}
      </div>
    </ThemeProvider>
  );
}

export default App;
