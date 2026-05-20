import { Result, Button } from "antd";
import { useNavigate } from "react-router-dom";

function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Result
      status="404"
      title="404"
      subTitle="Page not found"
      extra={
        <Button type="primary" onClick={() => navigate("/home")}>
          Back Home
        </Button>
      }
    />
  );
}

export default NotFoundPage;
