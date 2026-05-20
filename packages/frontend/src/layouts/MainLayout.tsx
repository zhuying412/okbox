import { Layout, Menu } from "antd";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  HomeOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  UserOutlined,
} from "@ant-design/icons";

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: "/home", icon: <HomeOutlined />, label: "Home" },
  { key: "/samples", icon: <ExperimentOutlined />, label: "Samples" },
  { key: "/reports", icon: <FileTextOutlined />, label: "Reports" },
  { key: "/patients", icon: <UserOutlined />, label: "Patients" },
];

function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible>
        <div
          style={{
            height: 32,
            margin: 16,
            color: "#fff",
            fontSize: 18,
            fontWeight: "bold",
            textAlign: "center",
          }}
        >
          OKBox
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: "0 16px", background: "#fff" }}>
          <span style={{ fontSize: 16 }}>NGS Data Analysis Platform</span>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: "#fff", borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default MainLayout;
