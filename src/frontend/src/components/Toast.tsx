import React, { useEffect, useState } from "react";

interface Props {
  message: string;
  type: "success" | "error" | "info";
  duration?: number;
  onClose: () => void;
}

const Toast: React.FC<Props> = ({
  message,
  type,
  duration = 4000,
  onClose,
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // Wait for fade-out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getBackgroundColor = () => {
    switch (type) {
      case "success":
        return "#4CAF50";
      case "error":
        return "#f44336";
      case "info":
        return "#2196F3";
      default:
        return "#333";
    }
  };

  const getIcon = () => {
    switch (type) {
      case "success":
        return "✅";
      case "error":
        return "❌";
      case "info":
        return "ℹ️";
      default:
        return "📢";
    }
  };

  if (!isVisible) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: "20px",
        right: "20px",
        backgroundColor: getBackgroundColor(),
        color: "#fff",
        padding: "15px 20px",
        borderRadius: "8px",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
        zIndex: 1000,
        maxWidth: "400px",
        fontSize: "14px",
        fontWeight: "500",
        opacity: isVisible ? 1 : 0,
        transform: `translateX(${isVisible ? 0 : 100}%)`,
        transition: "all 0.3s ease",
        cursor: "pointer",
      }}
      onClick={() => {
        setIsVisible(false);
        setTimeout(onClose, 300);
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span style={{ fontSize: "16px" }}>{getIcon()}</span>
        <span>{message}</span>
      </div>
    </div>
  );
};

export default Toast;
