import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import PortfolioPanel from "./components/PortfolioPanel";
import MonteCarloPanel from "./components/MonteCarloPanel";
import CorrelationMatrix from "./components/CorrelationMatrix";
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
  const [monteCarlo, setMonteCarlo] = useState(null);
  const [riskData, setRiskData] = useState(null);

  const handleSendMessage = async (query) => {
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsLoading(true);
    setTraceStatus("Planner Agent starting...");
    setAllocation(null);
    setMonteCarlo(null);
    setRiskData(null);

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
          if (data.monte_carlo_results) {
            setMonteCarlo(data.monte_carlo_results);
          }
          if (data.risk_data) {
            setRiskData(data.risk_data);
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
        {(allocation || monteCarlo || riskData) && (
          <div className="right-panel">
            {allocation && <PortfolioPanel allocation={allocation} />}
            {monteCarlo && <MonteCarloPanel data={monteCarlo} />}
            {riskData && <CorrelationMatrix data={riskData} />}
          </div>
        )}
      </div>
    </ThemeProvider>
  );
}

export default App;
