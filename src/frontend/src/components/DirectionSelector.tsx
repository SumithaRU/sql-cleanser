import React, { useEffect } from "react";

export type Direction = "pg2ora" | "ora2pg";

interface DirectionOption {
  value: Direction;
  label: string;
  description: string;
  emoji: string;
}

interface Props {
  value: Direction;
  onChange: (direction: Direction) => void;
  disabled?: boolean;
}

const DIRECTION_OPTIONS: DirectionOption[] = [
  {
    value: "pg2ora",
    label: "PostgreSQL → Oracle",
    description: "Convert PostgreSQL scripts to Oracle-compatible SQL",
    emoji: "🐘➡️🔶",
  },
  {
    value: "ora2pg",
    label: "Oracle → PostgreSQL",
    description: "Convert Oracle scripts to PostgreSQL-compatible SQL",
    emoji: "🔶➡️🐘",
  },
];

const STORAGE_KEY = "sql-cleanser-direction";

const DirectionSelector: React.FC<Props> = ({
  value,
  onChange,
  disabled = false,
}) => {
  // Load direction from localStorage on mount
  useEffect(() => {
    const savedDirection = localStorage.getItem(STORAGE_KEY) as Direction;
    if (
      savedDirection &&
      (savedDirection === "pg2ora" || savedDirection === "ora2pg")
    ) {
      onChange(savedDirection);
    }
  }, [onChange]);

  // Save direction to localStorage when changed
  const handleChange = (newDirection: Direction) => {
    localStorage.setItem(STORAGE_KEY, newDirection);
    onChange(newDirection);
  };

  const selectedOption =
    DIRECTION_OPTIONS.find((opt) => opt.value === value) ||
    DIRECTION_OPTIONS[0];

  return (
    <div style={{ marginBottom: "30px" }}>
      <h3
        style={{
          color: "#fff",
          textAlign: "center",
          marginBottom: "15px",
          fontSize: "18px",
          fontWeight: "500",
        }}
      >
        🔄 Conversion Direction
      </h3>

      <div
        style={{
          maxWidth: "500px",
          margin: "0 auto",
          backgroundColor: "#303030",
          borderRadius: "12px",
          padding: "20px",
          border: "1px solid #555",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "10px",
          }}
        >
          {DIRECTION_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => handleChange(option.value)}
              disabled={disabled}
              style={{
                backgroundColor: value === option.value ? "#007bff" : "#404040",
                color: "#fff",
                border: `2px solid ${
                  value === option.value ? "#007bff" : "#555"
                }`,
                borderRadius: "8px",
                padding: "15px 12px",
                cursor: disabled ? "not-allowed" : "pointer",
                fontSize: "14px",
                fontWeight: "500",
                transition: "all 0.3s ease",
                textAlign: "left",
                opacity: disabled ? 0.6 : 1,
                boxShadow:
                  value === option.value
                    ? "0 4px 12px rgba(0, 123, 255, 0.3)"
                    : "none",
              }}
              onMouseEnter={(e) => {
                if (!disabled && value !== option.value) {
                  e.currentTarget.style.backgroundColor = "#505050";
                  e.currentTarget.style.borderColor = "#777";
                }
              }}
              onMouseLeave={(e) => {
                if (!disabled && value !== option.value) {
                  e.currentTarget.style.backgroundColor = "#404040";
                  e.currentTarget.style.borderColor = "#555";
                }
              }}
            >
              <div style={{ fontSize: "16px", marginBottom: "5px" }}>
                {option.emoji}
              </div>
              <div style={{ fontWeight: "600", marginBottom: "3px" }}>
                {option.label}
              </div>
              <div
                style={{ fontSize: "12px", color: "#ccc", lineHeight: "1.3" }}
              >
                {option.description}
              </div>
            </button>
          ))}
        </div>

        <div
          style={{
            marginTop: "15px",
            padding: "12px",
            backgroundColor: "#2a2a2a",
            borderRadius: "6px",
            textAlign: "center",
          }}
        >
          <div
            style={{ color: "#4CAF50", fontSize: "14px", fontWeight: "500" }}
          >
            📍 Selected: {selectedOption.emoji} {selectedOption.label}
          </div>
          <div style={{ color: "#aaa", fontSize: "12px", marginTop: "3px" }}>
            {selectedOption.description}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DirectionSelector;
export { DIRECTION_OPTIONS };
