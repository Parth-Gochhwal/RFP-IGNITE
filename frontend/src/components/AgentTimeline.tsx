interface AgentTimelineProps {
  completed: boolean;
}

export function AgentTimeline({ completed }: AgentTimelineProps) {
  const agents = [
    { name: 'Sales Agent', description: 'RFP Selection' },
    { name: 'Main Agent', description: 'Orchestration' },
    { name: 'Technical Agent', description: 'SKU Matching' },
    { name: 'Pricing Agent', description: 'Cost Calculation' },
  ];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Agent Pipeline</h2>
      <div className="flex items-center gap-4 overflow-x-auto pb-2">
        {agents.map((agent, index) => (
          <div key={agent.name} className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold text-sm ${
                  completed
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-2 border-green-500 dark:border-green-600'
                    : 'bg-slate-100 dark:bg-slate-800/40 text-slate-400 dark:text-slate-400 border-2 border-slate-300 dark:border-slate-700'
                }`}
              >
                {index + 1}
              </div>
              <p className="text-xs font-medium text-slate-700 dark:text-slate-200 mt-2">{agent.name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">{agent.description}</p>
              {completed && (
                <span className="text-xs text-green-600 dark:text-green-400 font-medium mt-1">✓ Completed</span>
              )}
            </div>
            {index < agents.length - 1 && (
              <div
                className={`w-16 h-0.5 mx-2 ${
                  completed ? 'bg-green-500 dark:bg-green-600' : 'bg-slate-300 dark:bg-slate-700'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

