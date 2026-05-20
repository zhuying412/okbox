import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Input,
  Select,
  Modal,
  Form,
  DatePicker,
  Upload,
  message,
} from "antd";
import { PlusOutlined, UploadOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import apiClient from "../../services/api";

const { Title } = Typography;

interface Sample {
  id: string;
  sample_no: string;
  patient_name: string | null;
  sample_type: string;
  panel_type: string;
  status: string;
  received_date: string;
  created_at: string;
}

const statusColors: Record<string, string> = {
  registered: "default",
  analyzing: "processing",
  interpreted: "warning",
  reported: "success",
  signed: "purple",
};

function SamplesPage() {
  const [data, setData] = useState<Sample[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchSamples = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const response = await apiClient.get("/samples", { params });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    fetchSamples();
  }, [fetchSamples]);

  const handleCreate = async (values: Record<string, unknown>) => {
    try {
      const payload = {
        ...values,
        received_date: (values.received_date as dayjs.Dayjs).format("YYYY-MM-DD"),
      };
      await apiClient.post("/samples", payload);
      message.success("Sample registered successfully");
      setModalOpen(false);
      form.resetFields();
      fetchSamples();
    } catch {
      message.error("Failed to register sample");
    }
  };

  const columns: ColumnsType<Sample> = [
    { title: "Sample No", dataIndex: "sample_no", key: "sample_no", width: 150 },
    { title: "Patient", dataIndex: "patient_name", key: "patient_name", width: 120, render: (v) => v || "-" },
    { title: "Type", dataIndex: "sample_type", key: "sample_type", width: 100 },
    { title: "Panel", dataIndex: "panel_type", key: "panel_type", width: 120 },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (val: string) => <Tag color={statusColors[val]}>{val}</Tag>,
    },
    {
      title: "Received",
      dataIndex: "received_date",
      key: "received_date",
      width: 120,
    },
    {
      title: "Created",
      dataIndex: "created_at",
      key: "created_at",
      width: 160,
      render: (val: string) => dayjs(val).format("YYYY-MM-DD HH:mm"),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Samples</Title>
        <Space>
          <Upload
            accept=".csv"
            showUploadList={false}
            customRequest={async ({ file, onSuccess, onError }) => {
              const formData = new FormData();
              formData.append("file", file as Blob);
              try {
                const res = await apiClient.post("/samples/import", formData);
                message.success(`Imported ${res.data.success_count} samples`);
                fetchSamples();
                onSuccess?.(res.data);
              } catch (e) {
                onError?.(e as Error);
              }
            }}
          >
            <Button icon={<UploadOutlined />}>Import CSV</Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            Register Sample
          </Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Input
            placeholder="Search sample no / patient"
            prefix={<SearchOutlined />}
            style={{ width: 250 }}
            onChange={(e) => setSearch(e.target.value)}
            onPressEnter={() => fetchSamples()}
          />
          <Select
            placeholder="Status"
            allowClear
            style={{ width: 150 }}
            onChange={setStatusFilter}
            options={[
              { label: "Registered", value: "registered" },
              { label: "Analyzing", value: "analyzing" },
              { label: "Interpreted", value: "interpreted" },
              { label: "Reported", value: "reported" },
              { label: "Signed", value: "signed" },
            ]}
          />
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />

      <Modal
        title="Register Sample"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="sample_no" label="Sample No" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="patient_name" label="Patient Name">
            <Input />
          </Form.Item>
          <Form.Item name="sample_type" label="Sample Type" rules={[{ required: true }]}>
            <Select
              options={[
                { label: "Blood", value: "blood" },
                { label: "Tissue", value: "tissue" },
                { label: "FFPE", value: "ffpe" },
                { label: "ctDNA", value: "ctDNA" },
                { label: "Bone Marrow", value: "bone_marrow" },
                { label: "Other", value: "other" },
              ]}
            />
          </Form.Item>
          <Form.Item name="panel_type" label="Panel Type" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="received_date" label="Received Date" rules={[{ required: true }]}>
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default SamplesPage;
