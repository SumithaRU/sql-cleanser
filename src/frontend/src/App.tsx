import React, { useState, useEffect } from "react";
import { compareFilesWithProgress } from "./lib/api";
import Dropzone from "./components/Dropzone";
import ProgressBar from "./components/ProgressBar";
import ComparisonNameInput from "./components/ComparisonNameInput";

const App: React.FC = () => {
  const [baseFiles, setBaseFiles] = useState<File[]>([]);
  const [oracleFiles, setOracleFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>("");
  const [comparisonName, setComparisonName] = useState<string>("");
  const [currentStep, setCurrentStep] = useState<string>("");
  const [resetCountdown, setResetCountdown] = useState<number>(0);

  // Enhanced comparison state logic
  const hasBaseFiles = baseFiles.length > 0;
  const hasOracleFiles = oracleFiles.length > 0;
  const fileCountMismatch =
    hasBaseFiles && hasOracleFiles && baseFiles.length !== oracleFiles.length;
  const canCompare =
    hasBaseFiles &&
    hasOracleFiles &&
    !fileCountMismatch &&
    status !== "comparing";
  const isInProgress = status === "comparing";

  const handleReset = () => {
    setBaseFiles([]);
    setOracleFiles([]);
    setProgress(0);
    setStatus("");
    setComparisonName("");
    setCurrentStep("");
    setResetCountdown(0);
  };

  // Generate filename with timestamp and optional name
  const generateFilename = () => {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[:.]/g, "-").split(".")[0]; // YYYY-MM-DDTHH-MM-SS
    const baseName = comparisonName.trim() || "SQL_Comparison";
    return `${baseName}_${timestamp}.zip`;
  };

  // Auto-reset when comparison completes successfully
  useEffect(() => {
    if (status === "complete") {
      setResetCountdown(3);

      const countdownInterval = setInterval(() => {
        setResetCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            handleReset();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(countdownInterval);
    }
  }, [status]);

  const handleCompare = async () => {
    if (!canCompare) return;
    setStatus("comparing");
    setProgress(0);
    setCurrentStep("📤 Starting comparison...");

    try {
      // Convert FileList to File[]
      const baseFileList = Array.from(baseFiles) as unknown as FileList;
      const oracleFileList = Array.from(oracleFiles) as unknown as FileList;

      // Use real progress tracking
      const { blob, filename } = await compareFilesWithProgress(
        baseFileList,
        oracleFileList,
        comparisonName,
        (progressPercent: number, step: string) => {
          setProgress(progressPercent);
          setCurrentStep(step);
        }
      );

      // Final progress update
      setProgress(100);
      setCurrentStep("📦 Finalizing download...");

      // Use custom filename or fallback to server-provided filename
      const customFilename = generateFilename();
      const downloadName = customFilename || filename;

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", downloadName);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      setCurrentStep("✅ Download complete!");
      setStatus("complete");
    } catch (err) {
      console.error(err);
      setCurrentStep("❌ Comparison failed");
      setStatus("error");
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: "1200px", margin: "0 auto" }}>
      <h1
        style={{
          color: "#fff",
          textAlign: "center",
          marginBottom: "40px",
          fontSize: "32px",
          fontWeight: "600",
        }}
      >
        🔄 SQL Cleanser
      </h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "30px",
          marginBottom: "30px",
        }}
      >
        <div>
          <h3
            style={{
              color: "#fff",
              textAlign: "center",
              marginBottom: "15px",
              fontSize: "18px",
              fontWeight: "500",
            }}
          >
            📊 PostgreSQL Scripts (Base Files)
          </h3>
          <Dropzone
            files={baseFiles}
            setFiles={setBaseFiles}
            label="Base Files"
            otherFiles={oracleFiles}
            otherLabel="Oracle Files"
          />
        </div>
        <div>
          <h3
            style={{
              color: "#fff",
              textAlign: "center",
              marginBottom: "15px",
              fontSize: "18px",
              fontWeight: "500",
            }}
          >
            🎯 Oracle Scripts
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

      {/* Comparison Name Input */}
      {status !== "complete" && (
        <div style={{ maxWidth: "600px", margin: "0 auto" }}>
          <ComparisonNameInput
            value={comparisonName}
            onChange={setComparisonName}
            placeholder="Enter a name for this comparison (optional)"
            showPreview={true}
          />
        </div>
      )}

      {/* Enhanced Compare Button with Smart State Management */}
      <div style={{ textAlign: "center" }}>
        <button
          onClick={handleCompare}
          disabled={!canCompare}
          style={{
            backgroundColor: canCompare
              ? "#007bff"
              : fileCountMismatch
              ? "#BF1414"
              : isInProgress
              ? "#FF9800"
              : "#555",
            color: "#fff",
            padding: "15px 30px",
            borderRadius: "99px",
            border: "none",
            cursor: canCompare ? "pointer" : "not-allowed",
            fontSize: "16px",
            fontWeight: "600",
            transition: "all 0.3s ease",
            fontFamily: "Montserrat",
            boxShadow: canCompare
              ? "0 4px 12px rgba(76, 175, 80, 0.3)"
              : fileCountMismatch
              ? "0 4px 12px rgba(229, 115, 115, 0.25)"
              : "none",
            minWidth: "250px",
          }}
        >
          {isInProgress
            ? `🔄 Processing... (${progress}%)`
            : canCompare
            ? `✅ Compare & Migrate (${baseFiles.length} files each)`
            : fileCountMismatch
            ? `File count mismatch (${baseFiles.length} vs ${oracleFiles.length})`
            : hasBaseFiles && !hasOracleFiles
            ? "⏳ Add Oracle files to continue"
            : !hasBaseFiles && hasOracleFiles
            ? "⏳ Add Base files to continue"
            : "📁 Upload files to both sections"}
        </button>

        {/* Reset Button */}
        {(hasBaseFiles || hasOracleFiles) && !isInProgress && (
          <button
            onClick={handleReset}
            style={{
              backgroundColor: "transparent",
              color: "#888",
              padding: "8px 16px",
              borderRadius: "99px",
              border: "1px solid #555",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: "500",
              fontFamily: "Montserrat",
              marginLeft: "15px",
              transition: "all 0.3s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "#aaa";
              e.currentTarget.style.color = "#aaa";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "#555";
              e.currentTarget.style.color = "#888";
            }}
          >
            🗑️ Clear All
          </button>
        )}

        {/* Status Messages */}
        <div style={{ marginTop: "20px" }}>
          {!hasBaseFiles && !hasOracleFiles && status !== "complete" && (
            <p style={{ color: "#888", fontSize: "14px" }}>
              Upload SQL files to both sections to start comparison
            </p>
          )}
          {hasBaseFiles && !hasOracleFiles && status !== "complete" && (
            <p style={{ color: "#FF9800", fontSize: "14px" }}>
              ⚠️ Base files uploaded. Add Oracle files to enable comparison.
            </p>
          )}
          {!hasBaseFiles && hasOracleFiles && status !== "complete" && (
            <p style={{ color: "#FF9800", fontSize: "14px" }}>
              ⚠️ Oracle files uploaded. Add Base files to enable comparison.
            </p>
          )}
          {fileCountMismatch && status !== "complete" && (
            <p
              style={{ color: "#E57373", fontSize: "14px", fontWeight: "500" }}
            >
              ❌ File count mismatch! Both sides must have the same number of
              files for accurate comparison.
            </p>
          )}
          {canCompare && !isInProgress && status !== "complete" && (
            <p style={{ color: "#4CAF50", fontSize: "14px" }}>
              ✅ Ready to compare! Both file sets are uploaded and counts match.
            </p>
          )}
          {status === "complete" && (
            <div style={{ textAlign: "center" }}>
              <p
                style={{
                  color: "#4CAF50",
                  fontSize: "14px",
                  fontWeight: "500",
                }}
              >
                🎉 Comparison complete! Check your downloads folder.
              </p>
              <p
                style={{
                  color: "#888",
                  fontSize: "12px",
                  marginTop: "5px",
                  fontFamily: "monospace",
                  backgroundColor: "#333",
                  padding: "6px 10px",
                  borderRadius: "4px",
                  display: "inline-block",
                }}
              >
                📁 {generateFilename()}
              </p>
              {resetCountdown > 0 && (
                <div style={{ marginTop: "15px" }}>
                  <p
                    style={{
                      color: "#888",
                      fontSize: "12px",
                      marginBottom: "10px",
                      fontStyle: "italic",
                    }}
                  >
                    🔄 Auto-resetting in {resetCountdown} second
                    {resetCountdown !== 1 ? "s" : ""}...
                  </p>
                  <button
                    onClick={handleReset}
                    style={{
                      backgroundColor: "#007bff",
                      color: "#fff",
                      border: "none",
                      borderRadius: "99px",
                      padding: "8px 16px",
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
                    🆕 Start New Comparison
                  </button>
                </div>
              )}
            </div>
          )}
          {status === "error" && (
            <p
              style={{ color: "#E57373", fontSize: "14px", fontWeight: "500" }}
            >
              ❌ Error during comparison. Please try again.
            </p>
          )}
        </div>
      </div>

      {/* Enhanced Progress Bar for Processing State */}
      {isInProgress && (
        <div
          style={{
            marginTop: "20px",
            maxWidth: "600px",
            margin: "20px auto 0",
          }}
        >
          <ProgressBar
            progress={progress}
            label={currentStep || "Processing..."}
            showPercentage={true}
            color="#007bff"
            height={14}
          />
        </div>
      )}
    </div>
  );
};

export default App;
