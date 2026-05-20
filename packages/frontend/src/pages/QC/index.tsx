import { useState, useEffect } from "react";
import { Card, Typography, Table, Tag, Statistic, Row, Col, Alert } from "antd";
import { WarningOutlined, CheckCircleOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import apiClient from "../../services/api";

const { Title } = Typography;

interface QCMetric {
  id: string;
  sample_id: string;
  total_reads: number | null;
  mean_depth: number | null;
  coverage_30x: number | null;
  q30_rate: number | null;
  duplication_rate: number | null;
  on_target_rate: number | null;
  mapping_rate: number | null;
  status: string;
  is_alert: boolean;
  created_at: string;
}

const statusColors: Record<string, string> = {
  pass: "success",
  warn: "warning",
  fail: "error",
};

function QCPage() {
  const [alerts, setAlerts] = useState<QCMetric[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        const response = await apiClient.get("/qc/alerts");
        setAlerts(response.data);
      } catch {
        // handled
      } finally {
        setLoading(false);
      }
    };
    fetchAlerts();
  }, []);

  const columns: ColumnsType<QCMetric> = [
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 80,
      render: (val: string) => (
        <Tag color={statusColors[val]}>{val.toUpperCase()}</Tag>
      ),
    },
    { title: "Sample", dataIndex: "sample_id", key: "sample_id", width: 200, ellipsis: true },
    {
      title: "Total Reads",
      dataIndex: "total_reads",
      key: "total_reads",
      width: 120,
      render: (v: number | null) => (v ? (v / 1_000_000).toFixed(2) + "M" : "-"),
    },
    {
      title: "Mean Depth",
      dataIndex: "mean_depth",
      key: "mean_depth",
      width: 100,
      render: (v: number | null) => (v ? v.toFixed(1) + "x" : "-"),
    },
    {
      title: "Coverage 30x",
      dataIndex: "coverage_30x",
      key: "coverage_30x",
      width: 110,
      render: (v: number | null) => (v ? (v * 100).toFixed(1) + "%" : "-"),
    },
    {
      title: "Q30",
      dataIndex: "q30_rate",
      key: "q30_rate",
      width: 80,
      render: (v: number | null) => (v ? (v * 100).toFixed(1) + "%" : "-"),
    },
    {
      title: "Dup Rate",
      dataIndex: "duplication_rate",
      key: "duplication_rate",
      width: 90,
      render: (v: number | null) => (v ? (v * 100).toFixed(1) + "%" : "-"),
    },
    {
      title: "Mapping",
      dataIndex: "mapping_rate",
      key: "mapping_rate",
      width: 90,
      render: (v: number | null) => (v ? (v * 100).toFixed(1) + "%" : "-"),
    },
  ];

  const failCount = alerts.filter((a) => a.status === "fail").length;
  const warnCount = alerts.filter((a) => a.status === "warn").length;

  return (
    <div>
      <Title level={4}>Quality Control Dashboard</Title>

      {failCount > 0 && (
        <Alert
          message={`${failCount} sample(s) failed QC thresholds`}
          type="error"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="QC Alerts"
              value={failCount}
              prefix={<WarningOutlined />}
              valueStyle={{ color: failCount > 0 ? "#cf1322" : "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Warnings"
              value={warnCount}
              valueStyle={{ color: warnCount > 0 ? "#faad14" : "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Checked"
              value={alerts.length}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="QC Alert Samples">
        <Table
          columns={columns}
          dataSource={alerts}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>
    </div>
  );
}

export default QCPage;
