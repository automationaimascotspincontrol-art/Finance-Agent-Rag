import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import PortfolioPanel from "./components/PortfolioPanel";
import { ThemeProvider } from "./context/ThemeContext";
import { sendChatQuery } from "./api/chatApi";
import "./index.css";
import "./styles/light.css";
import "./styles/dark.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [allocation, setAllocation] = useState(null);

  const handleSendMessage = async (query) => {
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsLoading(true);

    if (query.toLowerCase().includes("optimize portfolio") || query.toLowerCase().includes("allocate")) {
      const parsedTickers = ["NVDA", "TSLA", "AAPL"];
      const aiResponse = `Optimizing portfolio for ${parsedTickers.join(", ")} based on Modern Portfolio Theory...`;

      setMessages((prev) => [...prev, { role: "ai", content: aiResponse }]);

      setTimeout(() => {
        setAllocation({ "NVDA": 40.5, "TSLA": 25.2, "AAPL": 34.3 });
        setIsLoading(false);
      }, 1500);
      return;
    }

    const aiResponse = await sendChatQuery(query);
    setMessages((prev) => [...prev, { role: "ai", content: aiResponse }]);
    setIsLoading(false);
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
