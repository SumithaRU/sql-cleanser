// Example usage of the enhanced Dropzone for comparison
import React, { useState } from "react";
import Dropzone from "./Dropzone";

const ComparisonExample: React.FC = () => {
  const [baseFiles, setBaseFiles] = useState<File[]>([]);
  const [oracleFiles, setOracleFiles] = useState<File[]>([]);

  const canCompare =
    baseFiles.length > 0 &&
    oracleFiles.length > 0 &&
    baseFiles.length === oracleFiles.length;
  const hasFileCountMismatch =
    baseFiles.length > 0 &&
    oracleFiles.length > 0 &&
    baseFiles.length !== oracleFiles.length;

  return (
    <div style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ color: "#fff", textAlign: "center", marginBottom: "40px" }}>
        SQL Files Comparison
      </h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "30px",
          marginBottom: "30px",
        }}
      >
        {/* Base Files Dropzone */}
        <div>
          <h3
            style={{
              color: "#fff",
              marginBottom: "15px",
              textAlign: "center",
              fontSize: "18px",
            }}
          >
            📊 Base Files (PostgreSQL)
          </h3>
          <Dropzone
            files={baseFiles}
            setFiles={setBaseFiles}
            label="Base Files"
            otherFiles={oracleFiles}
            otherLabel="Oracle Files"
          />
        </div>

        {/* Oracle Files Dropzone */}
        <div>
          <h3
            style={{
              color: "#fff",
              marginBottom: "15px",
              textAlign: "center",
              fontSize: "18px",
            }}
          >
            🎯 Oracle Files
          </h3>
          <Dropzone
            files={oracleFiles}
            setFiles={setOracleFiles}
            label="Oracle Files"
            otherFiles={baseFiles}
            otherLabel="Base Files"
          />
        </div>
      </div>

      {/* Compare Button */}
      <div style={{ textAlign: "center" }}>
        <button
          disabled={!canCompare}
          style={{
            backgroundColor: canCompare
              ? "#4CAF50"
              : hasFileCountMismatch
              ? "#E57373"
              : "#555",
            color: canCompare ? "#fff" : hasFileCountMismatch ? "#fff" : "#aaa",
            border: "none",
            padding: "15px 30px",
            borderRadius: "8px",
            fontSize: "16px",
            fontWeight: "600",
            cursor: canCompare ? "pointer" : "not-allowed",
            transition: "all 0.3s ease",
            boxShadow: canCompare
              ? "0 4px 12px rgba(76, 175, 80, 0.3)"
              : hasFileCountMismatch
              ? "0 4px 12px rgba(229, 115, 115, 0.25)"
              : "none",
          }}
          onClick={() => {
            if (canCompare) {
              console.log("Starting comparison...", { baseFiles, oracleFiles });
              // Your comparison logic here
            }
          }}
        >
          {canCompare
            ? `🔄 Compare Files (${baseFiles.length} base • ${oracleFiles.length} oracle)`
            : hasFileCountMismatch
            ? `❌ File count mismatch (${baseFiles.length} base • ${oracleFiles.length} oracle)`
            : "⏳ Upload files to both sections to compare"}
        </button>

        {/* Status Messages */}
        {baseFiles.length === 0 && oracleFiles.length === 0 && (
          <p style={{ color: "#888", marginTop: "15px", fontSize: "14px" }}>
            Upload SQL files to both sections to start comparison
          </p>
        )}

        {baseFiles.length > 0 && oracleFiles.length === 0 && (
          <p style={{ color: "#FF9800", marginTop: "15px", fontSize: "14px" }}>
            ⚠️ Base files uploaded. Add Oracle files to enable comparison.
          </p>
        )}

        {baseFiles.length === 0 && oracleFiles.length > 0 && (
          <p style={{ color: "#FF9800", marginTop: "15px", fontSize: "14px" }}>
            ⚠️ Oracle files uploaded. Add Base files to enable comparison.
          </p>
        )}

        {hasFileCountMismatch && (
          <p style={{ color: "#E57373", marginTop: "15px", fontSize: "14px" }}>
            ❌ File count mismatch! Add or remove files to match counts for
            accurate comparison.
          </p>
        )}

        {canCompare && (
          <p style={{ color: "#4CAF50", marginTop: "15px", fontSize: "14px" }}>
            ✅ Ready to compare! Both file sets are uploaded.
          </p>
        )}
      </div>
    </div>
  );
};

export default ComparisonExample;
