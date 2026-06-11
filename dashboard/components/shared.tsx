// ── Tipi e componenti condivisi tra le pagine della dashboard ──────────────────

export interface PPPStats {
  points: number
  possessions: number
  ppp: number | null
}

export const PERIODS = ["ALL", "1 Q", "2 Q", "3 Q", "4 Q", "CT"]
export const PERIOD_LABEL: Record<string, string> = { "ALL": "Full Game", "1 Q": "Q1", "2 Q": "Q2", "3 Q": "Q3", "4 Q": "Q4", "CT": "CT" }

export function Card({ title, children, className = "" }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-2xl p-5 ${className}`}>
      <p className="text-xs text-gray-400 uppercase tracking-widest mb-4 font-semibold">{title}</p>
      {children}
    </div>
  )
}

// ── Dist table: valore → conteggio + % ──────────────────────────────────────────

export function DistTable({ data, total }: { data: Record<string, number>; total: number }) {
  const vals = Object.entries(data).sort((a, b) => b[1] - a[1])
  if (!vals.length) return <p className="text-gray-600 text-xs">No data</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left text-gray-400 py-2 pr-4 font-semibold min-w-[120px]">Value</th>
            <th className="text-center text-gray-400 py-2 px-2 font-semibold">N</th>
            <th className="text-center text-yellow-600 py-2 px-2 font-semibold">%</th>
          </tr>
        </thead>
        <tbody>
          {vals.map(([val, n], i) => (
            <tr key={val} className={i % 2 === 1 ? "bg-gray-800/30" : ""}>
              <td className="py-1.5 pr-4 text-gray-300 font-medium">{val}</td>
              <td className="py-1.5 px-2 text-center text-white font-bold">{n}</td>
              <td className="py-1.5 px-2 text-center text-yellow-500">{total ? Math.round(n / total * 100) : 0}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
