import { useState, useEffect } from "react";
import { Card, Typography, Row, Col, Statistic, Table, Button, message } from "antd";
import {
  BarChartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  ExportOutlined,
} from "@ant-design/icons";
import apiClient from "../../services/api";

const { Title } = Typography;

function StatisticsPage() {
  const [tat, setTat] = useState<{ average_days: number; sample_count: number }>({
    average_days: 0,
    sample_count: 0,
  });
  const [pipelineRate, setPipelineRate] = useState<{
    total: number;
    success_rate: number;
  }>({ total: 0, success_rate: 0 });
  const [monthlyData, setMonthlyData] = useState<
    { year: number; month: number; count: number }[]
  >([]);
  const [variantDist, setVariantDist] = useState<{ type: string; count: number }[]>([]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [tatRes, pipeRes, monthRes, varRes] = await Promise.all([
          apiClient.get("/statistics/tat"),
          apiClient.get("/statistics/pipeline/success-rate"),
          apiClient.get("/statistics/samples/monthly"),
          apiClient.get("/statistics/variants/distribution"),
        ]);
        setTat(tatRes.data);
        setPipelineRate(pipeRes.data);
        setMonthlyData(monthRes.data.data);
        setVariantDist(varRes.data.data);
      } catch {
        // handled
      }
    };
    fetchStats();
  }, []);

  const handleExport = async () => {
    try {
      const response = await apiClient.get("/statistics/export");
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: "application/json",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "statistics_report.json");
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success("Statistics exported");
    } catch {
      message.error("Export failed");
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Statistics Dashboard
        </Title>
        <Button icon={<ExportOutlined />} onClick={handleExport}>
          Export Report
        </Button>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg TAT (days)"
              value={tat.average_days}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Pipeline Success Rate"
              value={pipelineRate.success_rate}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: pipelineRate.success_rate > 90 ? "#3f8600" : "#cf1322" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Pipelines"
              value={pipelineRate.total}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Samples with TAT"
              value={tat.sample_count}
              prefix={<ExperimentOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="Monthly Sample Count">
            <Table
              dataSource={monthlyData}
              rowKey={(r) => `${r.year}-${r.month}`}
              columns={[
                { title: "Year", dataIndex: "year", key: "year" },
                { title: "Month", dataIndex: "month", key: "month" },
                { title: "Count", dataIndex: "count", key: "count" },
              ]}
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Variant Type Distribution">
            <Table
              dataSource={variantDist}
              rowKey="type"
              columns={[
                { title: "Type", dataIndex: "type", key: "type" },
                { title: "Count", dataIndex: "count", key: "count" },
              ]}
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default StatisticsPage;
