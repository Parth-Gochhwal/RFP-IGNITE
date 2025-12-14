import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { useTheme } from "../theme/ThemeContext";

type PriceBreakdownProps = {
  totals:
    | {
        material_total: number;
        tests_total: number;
        overall_total?: number;
        other_total?: number;
      }
    | null;
};

const COLORS = ["#2563eb", "#0ea5e9", "#94a3b8"];

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

const PriceBreakdownChart = ({ totals }: PriceBreakdownProps) => {
  const { isDark } = useTheme();
  if (!totals) {
    return (
      <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">
          Price Breakdown
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">No price data available.</p>
      </div>
    );
  }

  const material = totals.material_total || 0;
  const tests = totals.tests_total || 0;
  const overall =
    totals.overall_total !== undefined
      ? totals.overall_total
      : material + tests;
  const otherRaw =
    totals.other_total !== undefined
      ? totals.other_total
      : Math.max(0, overall - (material + tests));
  const other = otherRaw < 0 ? 0 : otherRaw;

  const data = [
    { name: "Material", value: material },
    { name: "Tests/Services", value: tests },
    { name: "Other", value: other },
  ].filter((d) => d.value > 0);

  const totalValue = material + tests + other;

  return (
    <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
          Price Breakdown
        </h3>
        <span className="text-xs text-slate-500 dark:text-slate-300">
          Total: {formatCurrency(totalValue)}
        </span>
      </div>
      <div className="h-64">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${entry.name}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [
                formatCurrency(value),
                name,
              ]}
            />
            <Legend
              formatter={(value) => (
                <span className={`text-xs ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 text-xs text-slate-500 dark:text-slate-300">
        Shows proportion of Material vs Tests/Services vs Other costs.
      </div>
    </div>
  );
};

export default PriceBreakdownChart;

