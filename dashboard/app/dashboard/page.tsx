"use client"

import { useEffect, useState, useMemo } from "react"
import Link from "next/link"
import { ArrowLeft, Download } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts"

// ── types ────────────────────────────────────────────────────────────────────

interface PPPStats {
  points: number
  possessions: number
  ppp: number | null
}

interface EntryData {
  play_call?: string
  situation?: string
  total: number
  by_quarter: Record<string, number>
  ppp: PPPStats
  ppp_by_quarter: Record<string, PPPStats>
  results: Record<string, number>
  situations: Record<string, number>
  shot_locations: Record<string, number>
  o_coverages: Record<string, number>
  pressing: Record<string, number>
  paint_touches: Record<string, number>
  quality: Record<string, number>
  broken_play: number
  quality_avg: number | null
  paint_touch_n: number
  pivot_results: Record<string, Record<string, number>>
  pivot_situations: Record<string, Record<string, number>>
  pivot_coverages: Record<string, Record<string, number>>
  pivot_shot_loc: Record<string, Record<string, number>>
  pivot_quality: Record<string, Record<string, number>>
  pivot_pressing: Record<string, Record<string, number>>
  pivot_paint: Record<string, Record<string, number>>
  pivot_broken: Record<string, Record<string, number>>
  sit_x_results: Record<string, Record<string, number>>
  sit_x_paint: Record<string, Record<string, number>>
  sit_x_quality: Record<string, Record<string, number>>
  cov_x_results: Record<string, Record<string, number>>
  paint_x_results: Record<string, Record<string, number>>
}

// ── constants ─────────────────────────────────────────────────────────────────

const RED = "#dc2626"
const QUARTERS = ["1 Q","2 Q","3 Q","4 Q","CT"]
const Q_LABEL: Record<string,string> = {"1 Q":"Q1","2 Q":"Q2","3 Q":"Q3","4 Q":"Q4","CT":"CT"}

const MODES = {
  playcalls:  { url: "/api/playcalls",  field: "play_call" as const,  label: "Play Call",  title: "Play Call — clicca per analizzare" },
  situations: { url: "/api/situations", field: "situation" as const, label: "Situation", title: "Situation — clicca per analizzare" },
}
type Mode = keyof typeof MODES

function entryName(d: EntryData, mode: Mode): string {
  return d[MODES[mode].field] ?? ""
}

// ── UI helpers ────────────────────────────────────────────────────────────────

const TT = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-3 text-xs shadow-xl">
      <p className="text-gray-300 font-semibold mb-1">{label}</p>
      {payload.map((p: any) => <p key={p.dataKey} style={{color:p.color}}>{p.name}: <b>{p.value}</b></p>)}
    </div>
  )
}

function Card({ title, children, className="" }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-2xl p-5 ${className}`}>
      <p className="text-xs text-gray-400 uppercase tracking-widest mb-4 font-semibold">{title}</p>
      {children}
    </div>
  )
}

// ── Pivot table: valore × quarto ──────────────────────────────────────────────

function PivotTable({ pivot, total }: { pivot: Record<string, Record<string, number>>; total: number }) {
  const vals = Object.entries(pivot).sort((a, b) => {
    const sa = Object.values(a[1]).reduce((s,v)=>s+v,0)
    const sb = Object.values(b[1]).reduce((s,v)=>s+v,0)
    return sb - sa
  })
  if (!vals.length) return <p className="text-gray-600 text-xs">Nessun dato</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left text-gray-400 py-2 pr-4 font-semibold min-w-[120px]">Valore</th>
            <th className="text-center text-gray-400 py-2 px-2 font-semibold">Tot</th>
            <th className="text-center text-yellow-600 py-2 px-2 font-semibold">%</th>
            {QUARTERS.map(q => (
              <th key={q} className="text-center text-gray-500 py-2 px-2 font-semibold">{Q_LABEL[q]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {vals.map(([val, qMap], i) => {
            const n = Object.values(qMap).reduce((s,v)=>s+v,0)
            return (
              <tr key={val} className={i%2===1 ? "bg-gray-800/30" : ""}>
                <td className="py-1.5 pr-4 text-gray-300 font-medium">{val}</td>
                <td className="py-1.5 px-2 text-center text-white font-bold">{n}</td>
                <td className="py-1.5 px-2 text-center text-yellow-500">{total ? Math.round(n/total*100) : 0}%</td>
                {QUARTERS.map(q => (
                  <td key={q} className="py-1.5 px-2 text-center text-gray-400">{qMap[q]||""}</td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── PPP table: PPP / Punti / Possessi per quarto ─────────────────────────────

function PPPTable({ ppp, byQuarter }: { ppp: PPPStats; byQuarter: Record<string, PPPStats> }) {
  const lines: { label: string; total: number | string; get: (s: PPPStats) => number | string }[] = [
    { label: "PPP",      total: ppp.ppp ?? "—", get: s => s.ppp ?? "—" },
    { label: "Punti",    total: ppp.points,      get: s => s.points },
    { label: "Possessi", total: ppp.possessions, get: s => s.possessions },
  ]

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="text-left text-gray-400 py-2 pr-4 font-semibold min-w-[80px]"></th>
            <th className="text-center text-yellow-600 py-2 px-2 font-semibold">Tot</th>
            {QUARTERS.map(q => (
              <th key={q} className="text-center text-gray-500 py-2 px-2 font-semibold">{Q_LABEL[q]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {lines.map(({ label, total, get }, i) => (
            <tr key={label} className={i%2===1 ? "bg-gray-800/30" : ""}>
              <td className="py-1.5 pr-4 text-gray-300 font-medium">{label}</td>
              <td className="py-1.5 px-2 text-center text-white font-bold">{total}</td>
              {QUARTERS.map(q => (
                <td key={q} className="py-1.5 px-2 text-center text-gray-400">{byQuarter[q] ? get(byQuarter[q]) : "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Cross table ───────────────────────────────────────────────────────────────

function CrossTable({ data }: { data: Record<string, Record<string, number>> }) {
  const entries = Object.entries(data).sort((a,b) =>
    Object.values(b[1]).reduce((s,v)=>s+v,0) - Object.values(a[1]).reduce((s,v)=>s+v,0)
  )
  if (!entries.length) return <p className="text-gray-600 text-xs">Nessun dato</p>

  return (
    <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
      {entries.map(([a, bs]) => {
        const tot = Object.values(bs).reduce((s,v)=>s+v,0)
        return (
          <div key={a}>
            <p className="text-white text-xs font-bold mb-1">{a} <span className="text-gray-500 font-normal">({tot})</span></p>
            <div className="ml-3 space-y-0.5">
              {Object.entries(bs).sort((x,y)=>y[1]-x[1]).map(([b, n]) => (
                <div key={b} className="flex items-center gap-2 text-xs">
                  <span className="text-gray-400 w-28 truncate">{b}</span>
                  <div className="flex-1 bg-gray-800 rounded-full h-1">
                    <div className="bg-red-600 h-1 rounded-full" style={{width:`${Math.round(n/tot*100)}%`}} />
                  </div>
                  <span className="text-white font-bold w-5 text-right">{n}</span>
                  <span className="text-gray-500 w-8 text-right">{Math.round(n/tot*100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const [mode, setMode] = useState<Mode>("playcalls")
  const [data, setData] = useState<EntryData[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setSelected(null)
    fetch(MODES[mode].url).then(r => r.json()).then(d => { setData(d); setLoading(false) })
  }, [mode])

  const pc = useMemo(() => selected ? data.find(d => entryName(d, mode) === selected) ?? null : null, [data, selected, mode])

  const overview = useMemo(() =>
    data.map(d => ({ name: entryName(d, mode), value: d.total })).sort((a,b) => b.value - a.value),
    [data, mode]
  )

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">Caricamento...</div>
  )

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 bg-gray-900/90 backdrop-blur border-b border-gray-800 px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-gray-400 hover:text-white"><ArrowLeft size={18} /></Link>
        <div className="flex items-center gap-3 flex-1">
          <div className="w-7 h-7 rounded-full bg-red-600 flex items-center justify-center">
            <span className="text-white font-black text-xs">EA7</span>
          </div>
          <span className="text-white font-bold text-sm">Olimpia Analytics</span>
          {pc && <span className="bg-red-600/20 text-red-400 text-xs font-semibold px-2.5 py-1 rounded-lg">{entryName(pc, mode)} — {pc.total} azioni</span>}
        </div>
        {!pc && (
          <div className="flex bg-gray-800 rounded-lg p-1 print:hidden">
            {(Object.keys(MODES) as Mode[]).map(m => (
              <button key={m} onClick={() => setMode(m)}
                className={`text-xs font-semibold px-3 py-1 rounded-md transition-colors ${mode === m ? "bg-red-600 text-white" : "text-gray-400 hover:text-white"}`}>
                {MODES[m].label}
              </button>
            ))}
          </div>
        )}
        {pc && (
          <button onClick={() => setSelected(null)}
            className="text-xs text-gray-400 hover:text-white bg-gray-800 px-3 py-1.5 rounded-lg">
            ← Tutte
          </button>
        )}
        <button onClick={() => window.print()}
          className="flex items-center gap-1.5 text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors print:hidden">
          <Download size={13} /> PDF
        </button>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Overview — sempre visibile */}
        <Card title={MODES[mode].title}>
          <ResponsiveContainer width="100%" height={Math.max(280, overview.length * 26)}>
            <BarChart data={overview} layout="vertical"
              onClick={e => e?.activeLabel && setSelected(String(e.activeLabel) === selected ? null : String(e.activeLabel))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
              <XAxis type="number" tick={{fill:"#6b7280",fontSize:11}} />
              <YAxis type="category" dataKey="name" width={155} tick={{fill:"#9ca3af",fontSize:11}} />
              <Tooltip content={<TT />} />
              <Bar dataKey="value" name="Azioni" radius={[0,4,4,0]} className="cursor-pointer">
                {overview.map((d,i) => (
                  <Cell key={i} fill={d.name === selected ? "#fff" : RED}
                    opacity={selected && d.name !== selected ? 0.25 : 1} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Dettaglio play call selezionata */}
        {pc && (
          <>
            {/* KPI */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { l: "Azioni totali",   v: pc.total, sub: "" },
                { l: "PPP",             v: pc.ppp.ppp ?? "—", sub: pc.ppp.possessions ? `${pc.ppp.points} pt / ${pc.ppp.possessions} poss` : "" },
                { l: "Paint Touch",     v: `${pc.paint_touch_n} (${pc.total ? Math.round(pc.paint_touch_n/pc.total*100) : 0}%)`, sub: "" },
                { l: "Quality media",   v: pc.quality_avg ?? "—", sub: "" },
                { l: "Broken Play",     v: `${pc.broken_play} (${pc.total ? Math.round(pc.broken_play/pc.total*100) : 0}%)`, sub: "" },
              ].map(({l,v,sub}) => (
                <div key={l} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
                  <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">{l}</p>
                  <p className="text-white font-black text-2xl">{v}</p>
                  {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
                </div>
              ))}
            </div>

            {/* Pivot tables */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <Card title="PPP per quarto"><PPPTable ppp={pc.ppp} byQuarter={pc.ppp_by_quarter} /></Card>
              <Card title="Results"><PivotTable pivot={pc.pivot_results} total={pc.total} /></Card>
              <Card title="Situation"><PivotTable pivot={pc.pivot_situations} total={pc.total} /></Card>
              <Card title="Shot Location"><PivotTable pivot={pc.pivot_shot_loc} total={pc.total} /></Card>
              <Card title="O Coverages"><PivotTable pivot={pc.pivot_coverages} total={pc.total} /></Card>
              <Card title="Quality Shot"><PivotTable pivot={pc.pivot_quality} total={pc.total} /></Card>
              <Card title="Paint Touches"><PivotTable pivot={pc.pivot_paint} total={pc.total} /></Card>
              <Card title="Pressing"><PivotTable pivot={pc.pivot_pressing} total={pc.total} /></Card>
              <Card title="Broken Play"><PivotTable pivot={pc.pivot_broken} total={pc.total} /></Card>
            </div>

            {/* Legami */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card title="Situation × Results"><CrossTable data={pc.sit_x_results} /></Card>
              <Card title="O Coverages × Results"><CrossTable data={pc.cov_x_results} /></Card>
              <Card title="Situation × Paint Touches"><CrossTable data={pc.sit_x_paint} /></Card>
              <Card title="Situation × Quality Shot"><CrossTable data={pc.sit_x_quality} /></Card>
              <Card title="Paint Touches × Results" className="lg:col-span-2"><CrossTable data={pc.paint_x_results} /></Card>
            </div>
          </>
        )}

      </div>
    </div>
  )
}
