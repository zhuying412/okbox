import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Card,
  Typography,
  Button,
  Input,
  Space,
  Modal,
  Form,
  Select,
  DatePicker,
  message,
} from "antd";
import { PlusOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import apiClient from "../../services/api";

const { Title } = Typography;

interface Patient {
  id: string;
  patient_no: string;
  name: string | null;
  gender: string;
  birth_date: string | null;
  id_number: string | null;
  diagnosis: string | null;
  department: string | null;
  attending_doctor: string | null;
  created_at: string;
}

function PatientsPage() {
  const [data, setData] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      const response = await apiClient.get("/patients", { params });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const handleCreate = async (values: Record<string, unknown>) => {
    try {
      const payload = {
        ...values,
        birth_date: values.birth_date
          ? (values.birth_date as dayjs.Dayjs).format("YYYY-MM-DD")
          : undefined,
      };
      await apiClient.post("/patients", payload);
      message.success("Patient created");
      setModalOpen(false);
      form.resetFields();
      fetchPatients();
    } catch {
      message.error("Failed to create patient");
    }
  };

  const columns: ColumnsType<Patient> = [
    { title: "Patient No", dataIndex: "patient_no", key: "patient_no", width: 130 },
    { title: "Name", dataIndex: "name", key: "name", width: 100 },
    { title: "Gender", dataIndex: "gender", key: "gender", width: 80 },
    {
      title: "Birth Date",
      dataIndex: "birth_date",
      key: "birth_date",
      width: 110,
      render: (v: string | null) => v || "-",
    },
    { title: "ID Number", dataIndex: "id_number", key: "id_number", width: 150 },
    { title: "Diagnosis", dataIndex: "diagnosis", key: "diagnosis", width: 150, ellipsis: true },
    { title: "Department", dataIndex: "department", key: "department", width: 120 },
    { title: "Doctor", dataIndex: "attending_doctor", key: "doctor", width: 100 },
    {
      title: "Created",
      dataIndex: "created_at",
      key: "created_at",
      width: 150,
      render: (val: string) => dayjs(val).format("YYYY-MM-DD HH:mm"),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          Patients
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          Add Patient
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Input
          placeholder="Search by patient no or name"
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onPressEnter={() => fetchPatients()}
        />
      </Card>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />

      <Modal
        title="Add Patient"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="patient_no" label="Patient No" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="gender" label="Gender">
            <Select
              options={[
                { label: "Male", value: "male" },
                { label: "Female", value: "female" },
                { label: "Unknown", value: "unknown" },
              ]}
            />
          </Form.Item>
          <Form.Item name="birth_date" label="Birth Date">
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="id_number" label="ID Number">
            <Input />
          </Form.Item>
          <Form.Item name="diagnosis" label="Diagnosis">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="department" label="Department">
            <Input />
          </Form.Item>
          <Form.Item name="attending_doctor" label="Attending Doctor">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default PatientsPage;
