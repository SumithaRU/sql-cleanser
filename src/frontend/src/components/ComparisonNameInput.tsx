import React, { useState } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  showPreview?: boolean;
}

const ComparisonNameInput: React.FC<Props> = ({
  value,
  onChange,
  placeholder = "Enter comparison name (optional)",
  showPreview = true,
}) => {
  const [focused, setFocused] = useState(false);

  const generateDefaultName = () => {
    const now = new Date();
    const dateStr = now.toISOString().split("T")[0]; // YYYY-MM-DD
    const timeStr = now.toTimeString().split(" ")[0].replace(/:/g, ""); // HHMMSS
    return `SQL_Comparison_${dateStr}_${timeStr}`;
  };

  const handleGenerateDefault = () => {
    onChange(generateDefaultName());
  };

  const generatePreviewFilename = () => {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, "-").split(".")[0];
    const baseName = value.trim() || "SQL_Comparison";
    return `${baseName}_${timestamp}.zip`;
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <label
        style={{
          display: "block",
          color: "#fff",
          fontSize: "14px",
          fontWeight: "500",
          marginBottom: "8px",
        }}
      >
        📝 Comparison Name
      </label>

      <div style={{ position: "relative" }}>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          style={{
            width: "100%",
            padding: "12px 16px",
            paddingRight: "120px", // Space for button
            backgroundColor: "#303030",
            border: `2px solid ${focused ? "#007bff" : "#555"}`,
            borderRadius: "8px",
            color: "#fff",
            fontSize: "14px",
            fontFamily: "Montserrat",
            outline: "none",
            transition: "border-color 0.3s ease",
            boxSizing: "border-box",
          }}
        />

        <button
          onClick={handleGenerateDefault}
          style={{
            position: "absolute",
            right: "8px",
            top: "50%",
            transform: "translateY(-50%)",
            backgroundColor: "#007bff",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            padding: "6px 10px",
            fontSize: "12px",
            fontWeight: "500",
            cursor: "pointer",
            transition: "background-color 0.3s ease",
            fontFamily: "Montserrat",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = "#0056b3")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = "#007bff")
          }
        >
          🕒 Auto
        </button>
      </div>

      <p
        style={{
          color: "#888",
          fontSize: "8px",
          margin: "6px 0 0 0",
          lineHeight: "1.4",
        }}
      >
        Results will be saved with timestamp. Leave empty for automatic naming.
      </p>

      {showPreview && value && (
        <div
          style={{
            marginTop: "8px",
            padding: "8px 12px",
            backgroundColor: "#404040",
            borderRadius: "6px",
            border: "1px solid #555",
          }}
        >
          <p
            style={{
              color: "#aaa",
              fontSize: "8px",
              margin: "0 0 4px 0",
              fontWeight: "500",
            }}
          >
            📁 Preview filename:
          </p>
          <p
            style={{
              color: "#fff",
              fontSize: "8px",
              margin: "0",
              fontFamily: "monospace",
              wordBreak: "break-all",
            }}
          >
            {generatePreviewFilename()}
          </p>
        </div>
      )}
    </div>
  );
};

export default ComparisonNameInput;
