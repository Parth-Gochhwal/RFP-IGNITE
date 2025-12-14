import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  LabelList,
} from "recharts";
import { useTheme } from "../theme/ThemeContext";

export type MatchItem = {
  line_id: string;
  description: string;
  best_match_score: number;
};

type Props = {
  items: MatchItem[] | null;
};

const SpecMatchBarChart = ({ items }: Props) => {
  const { isDark } = useTheme();
  const data = items || [];
  const height = Math.max(200, data.length * 36);

  if (!data.length) {
    return (
      <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">
          Spec Match Scores
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">No match data available.</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
          Spec Match Scores
        </h3>
        <span className="text-xs text-slate-500 dark:text-slate-300">Best match per line</span>
      </div>
      <div style={{ height }}>
        <ResponsiveContainer>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#334155" : "#e2e8f0"} />
            <XAxis
              type="number"
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tick={{ fontSize: 11, fill: isDark ? "#cbd5e1" : "#475569" }}
            />
            <YAxis
              dataKey="line_id"
              type="category"
              tick={{ fontSize: 11, fill: isDark ? "#cbd5e1" : "#475569" }}
              width={90}
            />
            <Tooltip
              formatter={(value: number) => `${value}%`}
              labelFormatter={(label) => `Line: ${label}`}
            />
            <Bar dataKey="best_match_score" fill="#2563eb" radius={[0, 4, 4, 0]}>
              <LabelList
                dataKey="best_match_score"
                position="right"
                formatter={(value: number) => `${value}%`}
                style={{ fontSize: 11, fill: isDark ? "#e2e8f0" : "#0f172a" }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 text-xs text-slate-500 dark:text-slate-300">
        Lower percentages indicate potential mismatches requiring review.
      </div>
    </div>
  );
};

export default SpecMatchBarChart;

