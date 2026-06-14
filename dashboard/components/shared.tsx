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
