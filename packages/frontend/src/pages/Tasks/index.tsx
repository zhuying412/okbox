import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Select,
  Modal,
  Descriptions,
  message,
} from "antd";
import {
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  FileTextOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import apiClient from "../../services/api";
import TaskLogViewer from "./TaskLogViewer";

const { Title } = Typography;

interface Task {
  id: string;
  status: string;
  pipeline_name: string;
  pipeline_version: string;
  sample_id: string | null;
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  error_message: string | null;
  retry_count: number;
  max_retries: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

const statusColors: Record<string, string> = {
  pending: "default",
  running: "processing",
  completed: "success",
  failed: "error",
  cancelled: "warning",
  retrying: "orange",
};

function TasksPage() {
  const [data, setData] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(false);
  const [logTaskId, setLogTaskId] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      const response = await apiClient.get("/tasks", { params });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    fetchTasks();
    // Poll every 10s for real-time status updates
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  const handleCancel = async (taskId: string) => {
    try {
      await apiClient.post(`/tasks/${taskId}/cancel`);
      message.success("Task cancelled");
      fetchTasks();
    } catch {
      message.error("Failed to cancel task");
    }
  };

  const handleRetry = async (taskId: string) => {
    try {
      await apiClient.post(`/tasks/${taskId}/retry`);
      message.success("Task resubmitted");
      fetchTasks();
    } catch {
      message.error("Failed to retry task");
    }
  };

  const getDuration = (task: Task) => {
    if (!task.started_at) return "-";
    const end = task.completed_at || new Date().toISOString();
    const diff = dayjs(end).diff(dayjs(task.started_at), "second");
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
  };

  const columns: ColumnsType<Task> = [
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (val: string) => <Tag color={statusColors[val]}>{val.toUpperCase()}</Tag>,
    },
    { title: "Pipeline", dataIndex: "pipeline_name", key: "pipeline_name", width: 140 },
    { title: "Version", dataIndex: "pipeline_version", key: "pipeline_version", width: 80 },
    {
      title: "Duration",
      key: "duration",
      width: 100,
      render: (_: unknown, record: Task) => getDuration(record),
    },
    {
      title: "Created",
      dataIndex: "created_at",
      key: "created_at",
      width: 160,
      render: (val: string) => dayjs(val).format("YYYY-MM-DD HH:mm"),
    },
    {
      title: "Retries",
      key: "retries",
      width: 80,
      render: (_: unknown, r: Task) => `${r.retry_count}/${r.max_retries}`,
    },
    {
      title: "Actions",
      key: "actions",
      width: 200,
      render: (_: unknown, record: Task) => (
        <Space size="small">
          <Button
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => {
              setLogTaskId(record.id);
              setLogOpen(true);
            }}
          >
            Log
          </Button>
          {(record.status === "pending" || record.status === "running") && (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancel(record.id)}
            >
              Cancel
            </Button>
          )}
          {record.status === "failed" && (
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleRetry(record.id)}
            >
              Retry
            </Button>
          )}
          <Button
            size="small"
            onClick={() => {
              setSelectedTask(record);
              setDetailOpen(true);
            }}
          >
            Detail
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Pipeline Tasks</Title>
        <Space>
          <Select
            placeholder="Status filter"
            allowClear
            style={{ width: 150 }}
            onChange={setStatusFilter}
            options={[
              { label: "Pending", value: "pending" },
              { label: "Running", value: "running" },
              { label: "Completed", value: "completed" },
              { label: "Failed", value: "failed" },
              { label: "Cancelled", value: "cancelled" },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchTasks}>
            Refresh
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />

      {/* Task Detail Modal */}
      <Modal
        title="Task Details"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={700}
      >
        {selectedTask && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="ID">{selectedTask.id}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={statusColors[selectedTask.status]}>
                {selectedTask.status.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Pipeline">{selectedTask.pipeline_name}</Descriptions.Item>
            <Descriptions.Item label="Version">{selectedTask.pipeline_version}</Descriptions.Item>
            <Descriptions.Item label="Created">
              {dayjs(selectedTask.created_at).format("YYYY-MM-DD HH:mm:ss")}
            </Descriptions.Item>
            <Descriptions.Item label="Duration">{getDuration(selectedTask)}</Descriptions.Item>
            <Descriptions.Item label="Retries" span={2}>
              {selectedTask.retry_count} / {selectedTask.max_retries}
            </Descriptions.Item>
            {selectedTask.error_message && (
              <Descriptions.Item label="Error" span={2}>
                <pre style={{ whiteSpace: "pre-wrap", margin: 0, color: "red" }}>
                  {selectedTask.error_message}
                </pre>
              </Descriptions.Item>
            )}
            {selectedTask.inputs && (
              <Descriptions.Item label="Inputs" span={2}>
                <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 12 }}>
                  {JSON.stringify(selectedTask.inputs, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
            {selectedTask.outputs && (
              <Descriptions.Item label="Outputs" span={2}>
                <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 12 }}>
                  {JSON.stringify(selectedTask.outputs, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* Log Viewer Modal */}
      <Modal
        title="Task Log"
        open={logOpen}
        onCancel={() => setLogOpen(false)}
        footer={null}
        width={800}
      >
        {logTaskId && <TaskLogViewer taskId={logTaskId} />}
      </Modal>
    </div>
  );
}

export default TasksPage;
