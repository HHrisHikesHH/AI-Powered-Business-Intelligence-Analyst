import { Card, CardContent } from './ui/card';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface VisualizationConfig {
  chart_type: string;
  data_key?: string;
  category_key?: string;
  title?: string;
  description?: string;
  x_axis_label?: string;
  y_axis_label?: string;
  colors?: string[];
  config?: any;
}

interface VisualizationProps {
  config: VisualizationConfig;
  results: any[];
}

const COLORS = [
  '#8884d8',
  '#82ca9d',
  '#ffc658',
  '#ff7300',
  '#0088fe',
  '#00c49f',
  '#ffbb28',
  '#ff8042',
];

export default function Visualization({ config, results }: VisualizationProps) {
  const data = results || [];

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-muted-foreground">
          No data available for visualization
        </CardContent>
      </Card>
    );
  }

  const renderChart = () => {
    const chartType = config.chart_type?.toLowerCase?.() || 'bar';
    const xKey = config.category_key || 'name';
    const yKey = config.data_key || 'value';
    const colors = config.colors && config.colors.length > 0 ? config.colors : COLORS;

    switch (chartType) {
      case 'line':
      case 'linechart':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey={yKey}
                stroke={colors[0]}
                name={yKey}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
      case 'barchart':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey={yKey}
                fill={colors[0]}
                name={yKey}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'pie':
      case 'piechart':
        const pieData = data.map((item, i) => ({
          name: item[xKey] || `Item ${i + 1}`,
          value: item[yKey] || 0,
        }));
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        // Default to bar chart if type is unknown
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey={yKey}
                fill={colors[0]}
              />
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold capitalize">
            {config.title || config.chart_type}
          </h3>
        </div>
        {renderChart()}
      </CardContent>
    </Card>
  );
}

