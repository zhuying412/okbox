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
  message,
} from "antd";
import {
  EyeOutlined,
  DownloadOutlined,
  FileTextOutlined,
  ExportOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import apiClient from "../../services/api";

const { Title } = Typography;

interface ReportItem {
  id: string;
  sample_id: string;
  title: string;
  status: string;
  version: number;
  pdf_path: string | null;
  created_at: string;
  generated_at: string | null;
}

const statusColors: Record<string, string> = {
  draft: "default",
  generating: "processing",
  generated: "success",
  failed: "error",
};

function ReportsPage() {
  const [data, setData] = useState<ReportItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      const response = await apiClient.get("/reports", { params });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handlePreview = (reportId: string) => {
    setPreviewUrl(`/api/v1/reports/${reportId}/preview`);
    setPreviewOpen(true);
  };

  const handleDownloadPdf = async (reportId: string) => {
    try {
      const response = await apiClient.get(`/reports/${reportId}/download/pdf`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      message.error("Failed to download PDF");
    }
  };

  const handleExportJson = async (reportId: string) => {
    try {
      const response = await apiClient.get(`/reports/${reportId}/export/json`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: "application/json",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report_${reportId}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      message.error("Failed to export JSON");
    }
  };

  const columns: ColumnsType<ReportItem> = [
    { title: "Title", dataIndex: "title", key: "title", width: 200, ellipsis: true },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (val: string) => <Tag color={statusColors[val]}>{val.toUpperCase()}</Tag>,
    },
    { title: "Version", dataIndex: "version", key: "version", width: 80 },
    {
      title: "Generated",
      dataIndex: "generated_at",
      key: "generated_at",
      width: 160,
      render: (val: string | null) => (val ? dayjs(val).format("YYYY-MM-DD HH:mm") : "-"),
    },
    {
      title: "Actions",
      key: "actions",
      width: 280,
      render: (_: unknown, record: ReportItem) => (
        <Space size="small">
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record.id)}
            disabled={record.status !== "generated"}
          >
            Preview
          </Button>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadPdf(record.id)}
            disabled={!record.pdf_path}
          >
            PDF
          </Button>
          <Button
            size="small"
            icon={<ExportOutlined />}
            onClick={() => handleExportJson(record.id)}
          >
            JSON
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Reports
        </Title>
        <Select
          placeholder="Status"
          allowClear
          style={{ width: 150 }}
          onChange={setStatusFilter}
          options={[
            { label: "Draft", value: "draft" },
            { label: "Generating", value: "generating" },
            { label: "Generated", value: "generated" },
            { label: "Failed", value: "failed" },
          ]}
        />
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />

      <Modal
        title="Report Preview"
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={null}
        width={900}
      >
        {previewUrl && (
          <iframe
            src={previewUrl}
            style={{ width: "100%", height: 600, border: "1px solid #d9d9d9", borderRadius: 4 }}
            title="Report Preview"
          />
        )}
      </Modal>
    </div>
  );
}

export default ReportsPage;
