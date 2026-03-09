import { useContext } from "react";
import { ThemeContext } from "../context/ThemeContext";

function ThemeToggle() {
    const { theme, toggleTheme } = useContext(ThemeContext);

    return (
        <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle Theme">
            {theme === "light" ? "🌙" : "☀️"}
        </button>
    );
}

export default ThemeToggle;
