import { useState, useEffect, useCallback } from "react";
import {
  Table,
  Card,
  Typography,
  Input,
  Select,
  Space,
  InputNumber,
  Tag,
  Drawer,
  Descriptions,
  Button,
} from "antd";
import { SearchOutlined, FilterOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import apiClient from "../../services/api";

const { Title, Text } = Typography;

interface Variant {
  id: string;
  chromosome: string;
  position: number;
  ref_allele: string;
  alt_allele: string;
  variant_type: string;
  gene: string | null;
  hgvs_c: string | null;
  hgvs_p: string | null;
  quality: number | null;
  depth: number | null;
  vaf: number | null;
  filter_status: string | null;
  functional_impact: string | null;
  population_frequency: number | null;
  clinical_significance: string | null;
  dbsnp_id: string | null;
  annotations: Record<string, unknown> | null;
}

const clinSigColors: Record<string, string> = {
  pathogenic: "red",
  likely_pathogenic: "volcano",
  vus: "orange",
  likely_benign: "cyan",
  benign: "green",
};

function VariantsPage() {
  const [data, setData] = useState<Variant[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [sampleId, setSampleId] = useState("");
  const [filters, setFilters] = useState<Record<string, unknown>>({});
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const fetchVariants = useCallback(async () => {
    if (!sampleId) return;
    setLoading(true);
    try {
      const params = { sample_id: sampleId, page, page_size: 50, ...filters };
      const response = await apiClient.get("/variants", { params });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }, [sampleId, page, filters]);

  useEffect(() => {
    fetchVariants();
  }, [fetchVariants]);

  const columns: ColumnsType<Variant> = [
    { title: "Chr", dataIndex: "chromosome", key: "chr", width: 60 },
    { title: "Position", dataIndex: "position", key: "pos", width: 100 },
    { title: "Gene", dataIndex: "gene", key: "gene", width: 80 },
    {
      title: "Change",
      key: "change",
      width: 120,
      render: (_: unknown, r: Variant) => `${r.ref_allele}>${r.alt_allele}`,
    },
    { title: "Type", dataIndex: "variant_type", key: "type", width: 70 },
    { title: "HGVSp", dataIndex: "hgvs_p", key: "hgvsp", width: 150, ellipsis: true },
    {
      title: "VAF",
      dataIndex: "vaf",
      key: "vaf",
      width: 70,
      render: (v: number | null) => (v != null ? (v * 100).toFixed(1) + "%" : "-"),
    },
    { title: "Depth", dataIndex: "depth", key: "depth", width: 65 },
    {
      title: "Pop Freq",
      dataIndex: "population_frequency",
      key: "pop_freq",
      width: 85,
      render: (v: number | null) => (v != null ? v.toExponential(2) : "-"),
    },
    { title: "Impact", dataIndex: "functional_impact", key: "impact", width: 120, ellipsis: true },
    {
      title: "Significance",
      dataIndex: "clinical_significance",
      key: "clin_sig",
      width: 130,
      render: (val: string | null) =>
        val ? (
          <Tag color={clinSigColors[val] || "default"}>{val.replace("_", " ")}</Tag>
        ) : (
          "-"
        ),
    },
    {
      title: "",
      key: "actions",
      width: 60,
      render: (_: unknown, record: Variant) => (
        <Button
          size="small"
          type="link"
          onClick={() => {
            setSelectedVariant(record);
            setDrawerOpen(true);
          }}
        >
          Detail
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>Variant Browser</Title>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="Sample ID"
            style={{ width: 300 }}
            value={sampleId}
            onChange={(e) => setSampleId(e.target.value)}
            onPressEnter={() => fetchVariants()}
            prefix={<SearchOutlined />}
          />
          <Input
            placeholder="Gene"
            style={{ width: 120 }}
            onChange={(e) => setFilters((f) => ({ ...f, gene: e.target.value || undefined }))}
          />
          <Select
            placeholder="Variant Type"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setFilters((f) => ({ ...f, variant_type: v }))}
            options={[
              { label: "SNV", value: "snv" },
              { label: "InDel", value: "indel" },
              { label: "CNV", value: "cnv" },
              { label: "Fusion", value: "fusion" },
            ]}
          />
          <InputNumber
            placeholder="Min VAF"
            style={{ width: 100 }}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) => setFilters((f) => ({ ...f, min_vaf: v ?? undefined }))}
          />
          <InputNumber
            placeholder="Min Depth"
            style={{ width: 110 }}
            min={0}
            onChange={(v) => setFilters((f) => ({ ...f, min_depth: v ?? undefined }))}
          />
          <InputNumber
            placeholder="Max Pop Freq"
            style={{ width: 130 }}
            min={0}
            max={1}
            step={0.001}
            onChange={(v) =>
              setFilters((f) => ({ ...f, max_population_frequency: v ?? undefined }))
            }
          />
          <Select
            placeholder="Significance"
            allowClear
            style={{ width: 150 }}
            onChange={(v) => setFilters((f) => ({ ...f, clinical_significance: v }))}
            options={[
              { label: "Pathogenic", value: "pathogenic" },
              { label: "Likely Pathogenic", value: "likely_pathogenic" },
              { label: "VUS", value: "vus" },
              { label: "Likely Benign", value: "likely_benign" },
              { label: "Benign", value: "benign" },
            ]}
          />
          <Button icon={<FilterOutlined />} type="primary" onClick={fetchVariants}>
            Filter
          </Button>
        </Space>
      </Card>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        size="small"
        scroll={{ x: 1200 }}
        pagination={{
          current: page,
          total,
          pageSize: 50,
          onChange: setPage,
          showTotal: (t) => `${t} variants`,
        }}
      />

      <Drawer
        title="Variant Details"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={600}
      >
        {selectedVariant && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Chromosome">{selectedVariant.chromosome}</Descriptions.Item>
            <Descriptions.Item label="Position">{selectedVariant.position}</Descriptions.Item>
            <Descriptions.Item label="REF / ALT">
              {selectedVariant.ref_allele} / {selectedVariant.alt_allele}
            </Descriptions.Item>
            <Descriptions.Item label="Gene">{selectedVariant.gene || "-"}</Descriptions.Item>
            <Descriptions.Item label="HGVSc">{selectedVariant.hgvs_c || "-"}</Descriptions.Item>
            <Descriptions.Item label="HGVSp">{selectedVariant.hgvs_p || "-"}</Descriptions.Item>
            <Descriptions.Item label="Type">{selectedVariant.variant_type}</Descriptions.Item>
            <Descriptions.Item label="VAF">
              {selectedVariant.vaf != null ? (selectedVariant.vaf * 100).toFixed(2) + "%" : "-"}
            </Descriptions.Item>
            <Descriptions.Item label="Depth">{selectedVariant.depth ?? "-"}</Descriptions.Item>
            <Descriptions.Item label="Quality">{selectedVariant.quality ?? "-"}</Descriptions.Item>
            <Descriptions.Item label="Filter">{selectedVariant.filter_status || "-"}</Descriptions.Item>
            <Descriptions.Item label="Population Freq">
              {selectedVariant.population_frequency != null
                ? selectedVariant.population_frequency.toExponential(3)
                : "-"}
            </Descriptions.Item>
            <Descriptions.Item label="Functional Impact">
              {selectedVariant.functional_impact || "-"}
            </Descriptions.Item>
            <Descriptions.Item label="Clinical Significance">
              {selectedVariant.clinical_significance ? (
                <Tag color={clinSigColors[selectedVariant.clinical_significance]}>
                  {selectedVariant.clinical_significance.replace("_", " ")}
                </Tag>
              ) : (
                "-"
              )}
            </Descriptions.Item>
            <Descriptions.Item label="dbSNP">{selectedVariant.dbsnp_id || "-"}</Descriptions.Item>
            {selectedVariant.annotations && (
              <Descriptions.Item label="Annotations">
                <pre style={{ fontSize: 11, whiteSpace: "pre-wrap", maxHeight: 300, overflow: "auto" }}>
                  {JSON.stringify(selectedVariant.annotations, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
}

export default VariantsPage;
