import Link from "next/link"
import { BarChart2 } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-8 px-6">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 rounded-full bg-red-600 flex items-center justify-center shadow-lg shadow-red-900/40">
          <span className="text-white font-black text-sm">EA7</span>
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-tight">Olimpia Milano</h1>
          <p className="text-gray-400 text-sm">Analytics Platform</p>
        </div>
      </div>

      <div className="w-full max-w-sm">
        <Link href="/dashboard"
          className="bg-red-600 hover:bg-red-700 rounded-2xl p-6 flex flex-col gap-3 transition-colors group">
          <div className="w-10 h-10 rounded-xl bg-red-500 group-hover:bg-red-600 flex items-center justify-center transition-colors">
            <BarChart2 size={20} className="text-white" />
          </div>
          <div>
            <p className="text-white font-bold">Dashboard</p>
            <p className="text-red-200 text-sm mt-0.5">Analisi per Play Call</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
