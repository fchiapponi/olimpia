"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, Download } from "lucide-react"
import { PPPStats, PERIODS, PERIOD_LABEL, Card } from "@/components/shared"

// ── types ────────────────────────────────────────────────────────────────────

interface BreakdownEntry {
  total: number
  pct: number
  ppp: PPPStats
  quality_avg: number | null
  paint_touch_n: number
  shot_locations: Record<string, number>
}

interface PRPeriodStats {
  total: number
  ppp: PPPStats
  ppp_paint: PPPStats
  ppp_no_paint: PPPStats
  ppp_broken: PPPStats
  ppp_no_broken: PPPStats
  quality_avg: number | null
  paint_touch_n: number
  broken_play: number
  by_situation: Record<string, BreakdownEntry>
  by_coverage: Record<string, BreakdownEntry>
  by_screener_pos: Record<string, BreakdownEntry>
  by_kind_of_screen: Record<string, BreakdownEntry>
  by_roll: Record<string, BreakdownEntry>
  by_screen_location: Record<string, BreakdownEntry>
  gravity_handler: Record<string, BreakdownEntry>
  gravity_screener: Record<string, BreakdownEntry>
}

// ── breakdown table: valore → N, %, PPP, Quality, Shot Location top ────────────

function BreakdownTable({ data, valueLabel = "Value" }: { data: Record<string, BreakdownEntry>; valueLabel?: string }) {
  const entries = Object.entries(data).sort((a, b) => b[1].total - a[1].total)
  if (!entries.length) return <p className="text-gray-600 text-xs">No data</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left text-gray-400 py-2 pr-4 font-semibold min-w-[160px]">{valueLabel}</th>
            <th className="text-center text-gray-400 py-2 px-2 font-semibold">N</th>
            <th className="text-center text-yellow-600 py-2 px-2 font-semibold">%</th>
            <th className="text-center text-gray-400 py-2 px-2 font-semibold">PPP</th>
            <th className="text-center text-gray-400 py-2 px-2 font-semibold">Quality</th>
            <th className="text-center text-gray-400 py-2 px-2 font-semibold">Paint Touch</th>
            <th className="text-left text-gray-400 py-2 px-2 font-semibold min-w-[140px]">Top Shot Location</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([val, e], i) => {
            const topShot = Object.entries(e.shot_locations).sort((a, b) => b[1] - a[1])[0]
            return (
              <tr key={val} className={i % 2 === 1 ? "bg-gray-800/30" : ""}>
                <td className="py-1.5 pr-4 text-gray-200 font-medium">{val}</td>
                <td className="py-1.5 px-2 text-center text-white font-bold">{e.total}</td>
                <td className="py-1.5 px-2 text-center text-yellow-500">{e.pct}%</td>
                <td className="py-1.5 px-2 text-center text-gray-300 font-bold">{e.ppp.ppp ?? "—"}</td>
                <td className="py-1.5 px-2 text-center text-gray-300">{e.quality_avg ?? "—"}</td>
                <td className="py-1.5 px-2 text-center text-gray-300">{e.paint_touch_n} <span className="text-gray-500">({e.total ? Math.round(e.paint_touch_n / e.total * 100) : 0}%)</span></td>
                <td className="py-1.5 px-2 text-gray-400">{topShot ? `${topShot[0]} (${Math.round(topShot[1] / e.total * 100)}%)` : "—"}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════

export default function PRPage() {
  const [period, setPeriod] = useState("ALL")
  const [periods, setPeriods] = useState<Record<string, PRPeriodStats> | null>(null)

  useEffect(() => {
    fetch("/api/pr").then(r => r.json()).then(d => setPeriods(d.periods))
  }, [])

  if (!periods) return (
    <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">Loading...</div>
  )

  const s = periods[period]

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 bg-gray-900/90 backdrop-blur border-b border-gray-800 px-6 py-3 flex items-center gap-4">
        <Link href="/dashboard" className="text-gray-400 hover:text-white"><ArrowLeft size={18} /></Link>
        <div className="flex items-center gap-3 flex-1">
          <div className="w-7 h-7 rounded-full bg-red-600 flex items-center justify-center">
            <span className="text-white font-black text-xs">EA7</span>
          </div>
          <span className="text-white font-bold text-sm">P&R — Pick & Roll</span>
        </div>
        <button onClick={() => window.print()}
          className="flex items-center gap-1.5 text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors print:hidden">
          <Download size={13} /> PDF
        </button>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Selettore periodo */}
        <div className="flex flex-wrap gap-2">
          {PERIODS.map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${period === p ? "bg-red-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
              {PERIOD_LABEL[p]}
            </button>
          ))}
        </div>

        {/* KPI principali */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { l: "P&R Actions", v: s.total, sub: "" },
            { l: "PPP", v: s.ppp.ppp ?? "—", sub: s.ppp.possessions ? `${s.ppp.points} pt / ${s.ppp.possessions} poss` : "" },
            { l: "Avg Quality", v: s.quality_avg ?? "—", sub: "" },
            { l: "Paint Touch", v: `${s.paint_touch_n} (${s.total ? Math.round(s.paint_touch_n / s.total * 100) : 0}%)`, sub: "" },
            { l: "Broken Play", v: `${s.broken_play} (${s.total ? Math.round(s.broken_play / s.total * 100) : 0}%)`, sub: "" },
          ].map(({ l, v, sub }) => (
            <div key={l} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
              <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">{l}</p>
              <p className="text-2xl font-black text-white">{v}</p>
              {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
            </div>
          ))}
        </div>

        {/* PPP con/senza paint touch e broken play */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { l: "PPP with Paint Touch", v: s.ppp_paint },
            { l: "PPP without Paint Touch", v: s.ppp_no_paint },
            { l: "PPP with Broken Play", v: s.ppp_broken },
            { l: "PPP without Broken Play", v: s.ppp_no_broken },
          ].map(({ l, v }) => (
            <div key={l} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
              <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">{l}</p>
              <p className="text-2xl font-black text-white">{v.ppp ?? "—"}</p>
              <p className="text-gray-500 text-xs mt-1">{v.possessions} poss</p>
            </div>
          ))}
        </div>

        {/* Tipologia P&R */}
        <Card title="P&R Type"><BreakdownTable data={s.by_situation} valueLabel="Situation" /></Card>

        {/* Breakdown per categoria */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Card title="Coverage"><BreakdownTable data={s.by_coverage} valueLabel="Coverage" /></Card>
          <Card title="Screener (position)"><BreakdownTable data={s.by_screener_pos} valueLabel="Position" /></Card>
          <Card title="Kind of Screen"><BreakdownTable data={s.by_kind_of_screen} valueLabel="Type" /></Card>
          <Card title="Roll"><BreakdownTable data={s.by_roll} valueLabel="Roll" /></Card>
          <Card title="Screen Location" className="xl:col-span-2"><BreakdownTable data={s.by_screen_location} valueLabel="Location" /></Card>
        </div>

        {/* Gravity */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Card title="Gravity — Handler"><BreakdownTable data={s.gravity_handler} valueLabel="Handler" /></Card>
          <Card title="Gravity — Screener"><BreakdownTable data={s.gravity_screener} valueLabel="Screener" /></Card>
        </div>
      </div>
    </div>
  )
}
