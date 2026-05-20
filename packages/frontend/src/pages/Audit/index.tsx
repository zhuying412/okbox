import { useState, useEffect, useCallback } from "react";
import { Table, Card, Typography, DatePicker, Select, Input, Space, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import apiClient from "../../services/api";

const { Title } = Typography;
const { RangePicker } = DatePicker;

interface AuditLogEntry {
  id: string;
  user_id: string | null;
  username: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  path: string;
  ip_address: string | null;
  status_code: number | null;
  created_at: string;
}

const actionColors: Record<string, string> = {
  POST: "green",
  PUT: "blue",
  PATCH: "orange",
  DELETE: "red",
};

const columns: ColumnsType<AuditLogEntry> = [
  {
    title: "Time",
    dataIndex: "created_at",
    key: "created_at",
    width: 180,
    render: (val: string) => dayjs(val).format("YYYY-MM-DD HH:mm:ss"),
  },
  {
    title: "User",
    dataIndex: "username",
    key: "username",
    width: 120,
    render: (val: string | null) => val || "anonymous",
  },
  {
    title: "Action",
    dataIndex: "action",
    key: "action",
    width: 80,
    render: (val: string) => <Tag color={actionColors[val] || "default"}>{val}</Tag>,
  },
  {
    title: "Resource",
    dataIndex: "resource_type",
    key: "resource_type",
    width: 120,
  },
  {
    title: "Path",
    dataIndex: "path",
    key: "path",
    ellipsis: true,
  },
  {
    title: "Status",
    dataIndex: "status_code",
    key: "status_code",
    width: 80,
  },
  {
    title: "IP",
    dataIndex: "ip_address",
    key: "ip_address",
    width: 130,
  },
];

function AuditPage() {
  const [data, setData] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{
    action?: string;
    resource_type?: string;
    start_time?: string;
    end_time?: string;
  }>({});

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 50, ...filters };
      const response = await apiClient.get("/audit/logs", { params });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch {
      // error handled by interceptor
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div>
      <Title level={4}>Audit Logs</Title>
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="Action"
            allowClear
            style={{ width: 120 }}
            onChange={(val) => setFilters((f) => ({ ...f, action: val }))}
            options={[
              { label: "POST", value: "POST" },
              { label: "PUT", value: "PUT" },
              { label: "PATCH", value: "PATCH" },
              { label: "DELETE", value: "DELETE" },
            ]}
          />
          <Input
            placeholder="Resource Type"
            style={{ width: 150 }}
            onChange={(e) => setFilters((f) => ({ ...f, resource_type: e.target.value || undefined }))}
          />
          <RangePicker
            showTime
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setFilters((f) => ({
                  ...f,
                  start_time: dates[0]!.toISOString(),
                  end_time: dates[1]!.toISOString(),
                }));
              } else {
                setFilters((f) => ({ ...f, start_time: undefined, end_time: undefined }));
              }
            }}
          />
        </Space>
      </Card>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 50,
          onChange: setPage,
          showTotal: (t) => `Total ${t} records`,
        }}
      />
    </div>
  );
}

export default AuditPage;
