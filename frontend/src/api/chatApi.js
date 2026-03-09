const API_BASE_URL = "http://localhost:8000";

export const sendChatQueryStreaming = async (query, onStatus, onFinal) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (line.trim()) {
                    const data = JSON.parse(line);
                    if (data.type === "status") {
                        onStatus(data.content);
                    } else if (data.type === "final") {
                        onFinal(data);
                    } else if (data.type === "error") {
                        console.error("Stream Error:", data.content);
                    }
                }
            }
        }
    } catch (error) {
        console.error("Chat API Error:", error);
        onFinal({ type: "final", content: "Error connecting to AI Financial Agent." });
    }
};

export const optimizePortfolio = async (tickers) => {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/optimize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tickers })
        });
        const data = await response.json();
        return data.allocation;
    } catch (error) {
        console.error("Portfolio API Error:", error);
        return null;
    }
};
