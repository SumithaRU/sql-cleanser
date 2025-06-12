import React, { useState, useEffect } from "react";
import { compareFilesWithProgress } from "./lib/api";
import Dropzone from "./components/Dropzone";
import ProgressBar from "./components/ProgressBar";
import ComparisonNameInput from "./components/ComparisonNameInput";
import DirectionSelector, {
  Direction,
  DIRECTION_OPTIONS,
} from "./components/DirectionSelector";
import Toast from "./components/Toast";

const App: React.FC = () => {
  const [sourceFiles, setSourceFiles] = useState<File[]>([]);
  const [targetFiles, setTargetFiles] = useState<File[]>([]);
  const [direction, setDirection] = useState<Direction>("pg2ora");
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>("");
  const [comparisonName, setComparisonName] = useState<string>("");
  const [currentStep, setCurrentStep] = useState<string>("");
  const [resetCountdown, setResetCountdown] = useState<number>(0);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  // Enhanced comparison state logic
  const hasSourceFiles = sourceFiles.length > 0;
  const hasTargetFiles = targetFiles.length > 0;
  const fileCountMismatch =
    hasSourceFiles &&
    hasTargetFiles &&
    sourceFiles.length !== targetFiles.length;
  const canCompare =
    hasSourceFiles &&
    hasTargetFiles &&
    !fileCountMismatch &&
    status !== "comparing";
  const isInProgress = status === "comparing";

  const handleReset = () => {
    setSourceFiles([]);
    setTargetFiles([]);
    setProgress(0);
    setStatus("");
    setComparisonName("");
    setCurrentStep("");
    setResetCountdown(0);
    setToast(null);
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
      const sourceFileList = Array.from(sourceFiles) as unknown as FileList;
      const targetFileList = Array.from(targetFiles) as unknown as FileList;

      // Use real progress tracking
      const { blob, filename } = await compareFilesWithProgress(
        sourceFileList,
        targetFileList,
        direction,
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
      setToast({
        message: "Conversion ready – download your ZIP.",
        type: "success",
      });
    } catch (err) {
      console.error(err);
      setCurrentStep("❌ Comparison failed");
      setStatus("error");
      setToast({
        message:
          err instanceof Error
            ? err.message
            : "Conversion failed. Please try again.",
        type: "error",
      });
    }
  };

  // Get dynamic labels based on direction
  const getLabels = () => {
    const selectedOption =
      DIRECTION_OPTIONS.find((opt) => opt.value === direction) ||
      DIRECTION_OPTIONS[0];
    if (direction === "pg2ora") {
      return {
        sourceLabel: "📊 PostgreSQL Scripts (Source Files)",
        targetLabel: "🎯 Oracle Scripts (Target Files)",
        sourceShort: "PostgreSQL Files",
        targetShort: "Oracle Files",
      };
    } else {
      return {
        sourceLabel: "🔶 Oracle Scripts (Source Files)",
        targetLabel: "🐘 PostgreSQL Scripts (Target Files)",
        sourceShort: "Oracle Files",
        targetShort: "PostgreSQL Files",
      };
    }
  };

  const labels = getLabels();

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

      {/* Direction Selector */}
      <DirectionSelector
        value={direction}
        onChange={setDirection}
        disabled={isInProgress}
      />

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
            {labels.sourceLabel}
          </h3>
          <Dropzone
            files={sourceFiles}
            setFiles={setSourceFiles}
            label={labels.sourceShort}
            otherFiles={targetFiles}
            otherLabel={labels.targetShort}
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
            {labels.targetLabel}
          </h3>
          <Dropzone
            files={targetFiles}
            setFiles={setTargetFiles}
            label={labels.targetShort}
            otherFiles={sourceFiles}
            otherLabel={labels.sourceShort}
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
            ? `✅ Convert & Migrate (${sourceFiles.length} files each)`
            : fileCountMismatch
            ? `File count mismatch (${sourceFiles.length} vs ${targetFiles.length})`
            : hasSourceFiles && !hasTargetFiles
            ? `⏳ Add ${labels.targetShort} to continue`
            : !hasSourceFiles && hasTargetFiles
            ? `⏳ Add ${labels.sourceShort} to continue`
            : "📁 Upload files to both sections"}
        </button>

        {/* Reset Button */}
        {(hasSourceFiles || hasTargetFiles) && !isInProgress && (
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
          {!hasSourceFiles && !hasTargetFiles && status !== "complete" && (
            <p style={{ color: "#888", fontSize: "14px" }}>
              Upload SQL files to both sections to start conversion
            </p>
          )}
          {hasSourceFiles && !hasTargetFiles && status !== "complete" && (
            <p style={{ color: "#FF9800", fontSize: "14px" }}>
              ⚠️ {labels.sourceShort} uploaded. Add {labels.targetShort} to
              enable conversion.
            </p>
          )}
          {!hasSourceFiles && hasTargetFiles && status !== "complete" && (
            <p style={{ color: "#FF9800", fontSize: "14px" }}>
              ⚠️ {labels.targetShort} uploaded. Add {labels.sourceShort} to
              enable conversion.
            </p>
          )}
          {fileCountMismatch && status !== "complete" && (
            <p
              style={{ color: "#E57373", fontSize: "14px", fontWeight: "500" }}
            >
              ❌ File count mismatch! Both sides must have the same number of
              files for accurate conversion.
            </p>
          )}
          {canCompare && !isInProgress && status !== "complete" && (
            <p style={{ color: "#4CAF50", fontSize: "14px" }}>
              ✅ Ready to convert! Both file sets are uploaded and counts match.
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
                🎉 Conversion complete! Check your downloads folder.
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
                    🆕 Start New Conversion
                  </button>
                </div>
              )}
            </div>
          )}
          {status === "error" && (
            <p
              style={{ color: "#E57373", fontSize: "14px", fontWeight: "500" }}
            >
              ❌ Error during conversion. Please try again.
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

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default App;
