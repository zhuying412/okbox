import { useState, useEffect, useRef } from "react";
import { Spin, Typography } from "antd";
import apiClient from "../../services/api";

const { Text } = Typography;

interface TaskLogViewerProps {
  taskId: string;
}

function TaskLogViewer({ taskId }: TaskLogViewerProps) {
  const [logContent, setLogContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    let active = true;

    const fetchLog = async () => {
      try {
        const response = await apiClient.get(`/tasks/${taskId}/log`);
        if (active) {
          setLogContent(response.data.log_content);
          setLoading(false);
          // Auto-scroll to bottom
          if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
          }
        }
      } catch {
        if (active) {
          setLogContent("Failed to load log");
          setLoading(false);
        }
      }
    };

    fetchLog();

    // Poll for log updates every 3 seconds
    const interval = setInterval(fetchLog, 3000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [taskId]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 40 }}>
        <Spin tip="Loading log..." />
      </div>
    );
  }

  return (
    <pre
      ref={containerRef}
      style={{
        background: "#1e1e1e",
        color: "#d4d4d4",
        padding: 16,
        borderRadius: 8,
        maxHeight: 500,
        overflow: "auto",
        fontSize: 12,
        fontFamily: "'Courier New', monospace",
        whiteSpace: "pre-wrap",
        wordBreak: "break-all",
      }}
    >
      {logContent || <Text type="secondary">No log output available</Text>}
    </pre>
  );
}

export default TaskLogViewer;
