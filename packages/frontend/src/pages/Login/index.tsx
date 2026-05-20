import { Card, Form, Input, Button, Typography } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Title } = Typography;

function LoginPage() {
  const navigate = useNavigate();

  const onFinish = (_values: { username: string; password: string }) => {
    // TODO: Implement actual authentication in Issue #29
    navigate("/home");
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "#f0f2f5",
      }}
    >
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: "center" }}>
          OKBox Login
        </Title>
        <Form name="login" onFinish={onFinish} autoComplete="off">
          <Form.Item name="username" rules={[{ required: true, message: "Please enter username" }]}>
            <Input prefix={<UserOutlined />} placeholder="Username" size="large" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "Please enter password" }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              Login
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

export default LoginPage;
