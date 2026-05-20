import { Typography, Card, Row, Col, Statistic } from "antd";
import { ExperimentOutlined, FileTextOutlined, CheckCircleOutlined } from "@ant-design/icons";

const { Title } = Typography;

function HomePage() {
  return (
    <div>
      <Title level={4}>Dashboard</Title>
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic title="Samples" value={0} prefix={<ExperimentOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Reports" value={0} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Completed Tasks" value={0} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default HomePage;
