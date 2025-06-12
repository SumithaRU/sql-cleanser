import React from "react";

interface Props {
  progress: number;
  label?: string;
  showPercentage?: boolean;
  color?: string;
  height?: number;
}

const ProgressBar: React.FC<Props> = ({
  progress,
  label = "Processing...",
  showPercentage = true,
  color = "#007bff",
  height = 12,
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div style={{ width: "100%", margin: "15px 0" }}>
      {/* Label and Percentage */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "8px",
          fontSize: "14px",
          fontWeight: "500",
        }}
      >
        <span style={{ color: "#fff" }}>{label}</span>
        {showPercentage && (
          <span
            style={{
              color: "#aaa",
              fontSize: "13px",
              fontFamily: "monospace",
            }}
          >
            {clampedProgress.toFixed(0)}%
          </span>
        )}
      </div>

      {/* Progress Bar Container */}
      <div
        style={{
          width: "100%",
          background: "#333",
          borderRadius: "8px",
          overflow: "hidden",
          boxShadow: "inset 0 2px 4px rgba(0,0,0,0.3)",
          border: "1px solid #555",
        }}
      >
        {/* Progress Fill */}
        <div
          style={{
            width: `${clampedProgress}%`,
            background: `linear-gradient(90deg, ${color}, ${color}dd)`,
            height: `${height}px`,
            transition: "width 0.3s ease",
            borderRadius: "7px",
            boxShadow: clampedProgress > 0 ? `0 0 8px ${color}40` : "none",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* Animated Stripe Effect */}
          {clampedProgress > 0 && clampedProgress < 100 && (
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundImage: `linear-gradient(45deg, 
                transparent 25%, 
                rgba(255,255,255,0.1) 25%, 
                rgba(255,255,255,0.1) 50%, 
                transparent 50%, 
                transparent 75%, 
                rgba(255,255,255,0.1) 75%)`,
                backgroundSize: "20px 20px",
                animation: "progressStripes 1s linear infinite",
              }}
            />
          )}
        </div>
      </div>

      {/* Add CSS Animation */}
      <style>{`
        @keyframes progressStripes {
          0% { background-position: 0 0; }
          100% { background-position: 20px 0; }
        }
      `}</style>
    </div>
  );
};

export default ProgressBar;
