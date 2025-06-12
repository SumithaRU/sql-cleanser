import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface Props {
  files: File[];
  setFiles: (files: File[]) => void;
  label?: string;
  otherFiles?: File[];
  otherLabel?: string;
}

const Dropzone: React.FC<Props> = ({
  files,
  setFiles,
  label = "SQL Files",
  otherFiles = [],
  otherLabel = "Other Files",
}) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setFiles([...files, ...acceptedFiles]);
    },
    [files, setFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/sql": [".sql", ".txt"] },
  });

  const removeFile = (indexToRemove: number) => {
    setFiles(files.filter((_, index) => index !== indexToRemove));
  };

  // Check comparison readiness
  const hasFiles = files.length > 0;
  const hasOtherFiles = otherFiles.length > 0;
  const needsBothForComparison =
    label &&
    otherLabel &&
    (label.includes("Base") ||
      label.includes("Oracle") ||
      otherLabel.includes("Base") ||
      otherLabel.includes("Oracle"));
  const fileCountMismatch =
    hasFiles &&
    hasOtherFiles &&
    files.length !== otherFiles.length &&
    needsBothForComparison;
  const isComparisonReady = hasFiles && hasOtherFiles && !fileCountMismatch;
  const needsOtherFiles = hasFiles && !hasOtherFiles && needsBothForComparison;

  return (
    <div
      {...getRootProps()}
      style={{
        backgroundColor: "#303030",
        border: `2px dashed ${
          isDragActive
            ? "#4CAF50"
            : fileCountMismatch
            ? "#E57373"
            : isComparisonReady
            ? "#4CAF50"
            : needsOtherFiles
            ? "#FF9800"
            : hasOtherFiles && !hasFiles && needsBothForComparison
            ? "#FFA726"
            : "#555"
        }`,
        padding: "40px 20px",
        textAlign: "center",
        cursor: "pointer",
        marginBottom: 20,
        borderRadius: 19,
        transition: "all 0.3s ease",
        ...(isDragActive && {
          backgroundColor: "#404040",
        }),
        ...(fileCountMismatch && {
          boxShadow:
            "0 0 0 1px #E5737320, 0 4px 12px rgba(229, 115, 115, 0.15)",
        }),
        ...(isComparisonReady && {
          boxShadow: "0 0 0 1px #4CAF5020, 0 4px 12px rgba(76, 175, 80, 0.15)",
        }),
        ...(needsOtherFiles && {
          boxShadow: "0 0 0 1px #FF980020, 0 4px 12px rgba(255, 152, 0, 0.15)",
        }),
      }}
    >
      <input {...getInputProps()} />

      {/* Main Action Text */}
      {isDragActive ? (
        <p
          style={{
            color: "#4CAF50",
            fontSize: "18px",
            margin: "0 0 20px 0",
            fontWeight: "600",
          }}
        >
          📂 Drop the files here...
        </p>
      ) : files.length === 0 ? (
        <div>
          <p
            style={{
              color: "#aaa",
              fontSize: "18px",
              margin: "0 0 10px 0",
              fontWeight: "500",
            }}
          >
            📄 Add {label.toLowerCase()} here
          </p>
          <p style={{ color: "#888", fontSize: "14px", margin: "0" }}>
            Drag 'n' drop SQL files or click to select • Supports .sql and .txt
            files
          </p>
          {hasOtherFiles && needsBothForComparison && (
            <p
              style={{
                color: "#FFA726",
                fontSize: "13px",
                margin: "8px 0 0 0",
                fontWeight: "500",
                backgroundColor: "#FFA72620",
                padding: "8px 12px",
                borderRadius: "6px",
                border: "1px solid #FFA72640",
              }}
            >
              ⚠️ {otherLabel} uploaded! Add {label.toLowerCase()} to enable
              comparison
            </p>
          )}
        </div>
      ) : needsOtherFiles ? (
        <div>
          <p
            style={{
              color: "#FF9800",
              fontSize: "16px",
              margin: "0 0 10px 0",
              fontWeight: "500",
            }}
          >
            🔄 Now add {otherLabel.toLowerCase()} to compare
          </p>
          <p style={{ color: "#888", fontSize: "14px", margin: "0" }}>
            Comparison requires both file sets • You can also add more{" "}
            {label.toLowerCase()}
          </p>
        </div>
      ) : fileCountMismatch ? (
        <div>
          <p
            style={{
              color: "#E57373",
              fontSize: "16px",
              margin: "0 0 10px 0",
              fontWeight: "500",
            }}
          >
            ⚠️ File count mismatch detected
          </p>
          <p style={{ color: "#888", fontSize: "14px", margin: "0" }}>
            {files.length} {label.toLowerCase()} • {otherFiles.length}{" "}
            {otherLabel.toLowerCase()} • Add or remove files to match counts
          </p>
          <p
            style={{
              color: "#E57373",
              fontSize: "13px",
              margin: "8px 0 0 0",
              fontWeight: "500",
              backgroundColor: "#E5737320",
              padding: "8px 12px",
              borderRadius: "6px",
              border: "1px solid #E5737340",
            }}
          >
            🔢 For accurate comparison, both sides should have the same number
            of files
          </p>
        </div>
      ) : isComparisonReady ? (
        <div>
          <p
            style={{
              color: "#4CAF50",
              fontSize: "16px",
              margin: "0 0 10px 0",
              fontWeight: "500",
            }}
          >
            ✅ Ready to compare! Add more files if needed
          </p>
          <p style={{ color: "#888", fontSize: "14px", margin: "0" }}>
            {files.length} {label.toLowerCase()} • {otherFiles.length}{" "}
            {otherLabel.toLowerCase()} • Click to add more
          </p>
        </div>
      ) : files.length === 1 ? (
        <div>
          <p
            style={{
              color: "#4CAF50",
              fontSize: "16px",
              margin: "0 0 10px 0",
              fontWeight: "500",
            }}
          >
            ✨ You can add even more files now
          </p>
          <p style={{ color: "#888", fontSize: "14px", margin: "0" }}>
            Click or drag to add additional SQL files
          </p>
        </div>
      ) : (
        <div>
          <p
            style={{
              color: "#4CAF50",
              fontSize: "16px",
              margin: "0 0 10px 0",
              fontWeight: "500",
            }}
          >
            🎯 Add more files or manage your selection
          </p>
          <p style={{ color: "#888", fontSize: "14px", margin: "0" }}>
            {files.length} files selected • Click to add more
          </p>
        </div>
      )}

      {/* Files Display */}
      {files.length > 0 && (
        <div style={{ marginTop: "30px", textAlign: "left" }}>
          {files.length === 1 ? (
            // Single file - Professional card style
            <div
              style={{
                backgroundColor: "#404040",
                border: "1px solid #555",
                borderRadius: "12px",
                padding: "16px 20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                margin: "0 auto",
                maxWidth: "500px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "12px" }}
              >
                <span style={{ fontSize: "24px" }}>📄</span>
                <div>
                  <p
                    style={{
                      color: "#fff",
                      margin: "0",
                      fontSize: "16px",
                      fontWeight: "500",
                      wordBreak: "break-word",
                    }}
                  >
                    {files[0].name}
                  </p>
                  <p
                    style={{
                      color: "#aaa",
                      margin: "0",
                      fontSize: "12px",
                      marginTop: "4px",
                    }}
                  >
                    {(files[0].size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(0);
                }}
                style={{
                  backgroundColor: "transparent",
                  border: "none",
                  color: "#ff6b6b",
                  cursor: "pointer",
                  fontSize: "18px",
                  padding: "8px",
                  borderRadius: "6px",
                  transition: "background-color 0.2s ease",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#ff6b6b20")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                ✕
              </button>
            </div>
          ) : (
            // Multiple files - Grid/List style
            <div
              style={{
                display: "grid",
                gap: "12px",
                maxHeight: "200px",
                overflowY: "auto",
              }}
            >
              {files.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  style={{
                    backgroundColor: "#404040",
                    border: "1px solid #555",
                    borderRadius: "8px",
                    padding: "12px 16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    transition: "background-color 0.2s ease",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor = "#454545")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = "#404040")
                  }
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <span style={{ fontSize: "16px" }}>📄</span>
                    <div>
                      <p
                        style={{
                          color: "#fff",
                          margin: "0",
                          fontSize: "14px",
                          fontWeight: "500",
                          wordBreak: "break-word",
                        }}
                      >
                        {file.name}
                      </p>
                      <p
                        style={{
                          color: "#aaa",
                          margin: "0",
                          fontSize: "11px",
                          marginTop: "2px",
                        }}
                      >
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    style={{
                      backgroundColor: "transparent",
                      border: "none",
                      color: "#ff6b6b",
                      cursor: "pointer",
                      fontSize: "14px",
                      padding: "6px",
                      borderRadius: "4px",
                      transition: "background-color 0.2s ease",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.backgroundColor = "#ff6b6b20")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.backgroundColor = "transparent")
                    }
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dropzone;
