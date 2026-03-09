import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const sendChatQuery = async (query) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat/`, { query });
        return response.data.response;
    } catch (error) {
        console.error("Chat API Error:", error);
        return "Error connecting to AI Financial Agent.";
    }
};

export const optimizePortfolio = async (tickers) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/portfolio/optimize`, { tickers });
        return response.data.allocation;
    } catch (error) {
        console.error("Portfolio API Error:", error);
        return null;
    }
};
