"use client"

import { useEffect, useState, useMemo } from "react"
import Link from "next/link"
import { ArrowLeft, Download, Repeat2 } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts"
import { PPPStats, PERIODS, PERIOD_LABEL, Card, DistTable } from "@/components/shared"

// ── types ────────────────────────────────────────────────────────────────────

interface PeriodStats {
  total: number
  ppp: PPPStats
  ppp_paint: PPPStats
  ppp_no_paint: PPPStats
  ppp_broken: PPPStats
  ppp_no_broken: PPPStats
  results: Record<string, number>
  situations: Record<string, number>
  shot_locations: Record<string, number>
  o_coverages: Record<string, number>
  pressing: Record<string, number>
  paint_touches: Record<string, number>
  quality: Record<string, number>
  broken_play: number
  broken_play_dist: Record<string, number>
  quality_avg: number | null
  paint_touch_n: number
  sit_x_results: Record<string, Record<string, number>>
  sit_x_paint: Record<string, Record<string, number>>
  sit_x_quality: Record<string, Record<string, number>>
  cov_x_results: Record<string, Record<string, number>>
  paint_x_results: Record<string, Record<string, number>>
}

interface EntryData {
  play_call?: string
  situation?: string
  player?: string
  periods: Record<string, PeriodStats>
}

// ── constants ─────────────────────────────────────────────────────────────────

const RED = "#dc2626"

const MODES = {
  playcalls:      { url: "/api/playcalls",       field: "play_call" as const, label: "Play Call",       title: "Play Call — click to analyze" },
  situations:     { url: "/api/situations",      field: "situation" as const, label: "Situation",       title: "Situation — click to analyze" },
  players:        { url: "/api/players",         field: "player" as const,    label: "Oncourt",         title: "Oncourt — click to analyze" },
  difesa:         { url: "/api/difesa",          field: "play_call" as const, label: "Defense",         title: "Defense — Opponent Play Calls, click to analyze" },
  players_difesa: { url: "/api/players-difesa",  field: "player" as const,    label: "Defense Oncourt", title: "Defense Oncourt — click to analyze" },
}
type Mode = keyof typeof MODES
const isDefense = (mode: Mode) => mode === "difesa" || mode === "players_difesa"

function entryName(d: EntryData, mode: Mode): string {
  return d[MODES[mode].field] ?? ""
}

function stats(d: EntryData, period: string): PeriodStats {
  return d.periods[period] ?? d.periods["ALL"]
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

// ── Cross table ───────────────────────────────────────────────────────────────

function CrossTable({ data }: { data: Record<string, Record<string, number>> }) {
  const entries = Object.entries(data).sort((a,b) =>
    Object.values(b[1]).reduce((s,v)=>s+v,0) - Object.values(a[1]).reduce((s,v)=>s+v,0)
  )
  if (!entries.length) return <p className="text-gray-600 text-xs">No data</p>

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

// ── Summary table: una riga per play call / situation / giocatore ────────────

type SortKey = "name" | "total" | "points" | "possessions" | "ppp" | "quality" | "paint" | "broken" | "ppp_paint" | "ppp_no_paint" | "ppp_broken" | "ppp_no_broken"

function sortValue(r: { name: string; s: PeriodStats }, key: SortKey): number | string {
  switch (key) {
    case "name":         return r.name
    case "total":        return r.s.total
    case "points":       return r.s.ppp.points
    case "possessions":  return r.s.ppp.possessions
    case "ppp":          return r.s.ppp.ppp ?? -Infinity
    case "quality":      return r.s.quality_avg ?? -Infinity
    case "paint":        return r.s.paint_touch_n
    case "broken":       return r.s.broken_play
    case "ppp_paint":    return r.s.ppp_paint.ppp ?? -Infinity
    case "ppp_no_paint": return r.s.ppp_no_paint.ppp ?? -Infinity
    case "ppp_broken":   return r.s.ppp_broken.ppp ?? -Infinity
    case "ppp_no_broken":return r.s.ppp_no_broken.ppp ?? -Infinity
  }
}

function SummaryTable({ data, mode, period, selected, onSelect }: { data: EntryData[]; mode: Mode; period: string; selected: string | null; onSelect: (name: string) => void }) {
  const [sortKey, setSortKey] = useState<SortKey>("total")
  const [sortDir, setSortDir] = useState<1 | -1>(-1)

  const allRows = data
    .map(d => ({ name: entryName(d, mode), s: stats(d, period) }))
    .filter(({ s }) => s.total > 0)

  if (!allRows.length) return <p className="text-gray-600 text-xs">No data</p>

  const totalAll = allRows.reduce((sum, { s }) => sum + s.total, 0)

  const pppValues = allRows.map(({ s }) => s.ppp.ppp).filter((v): v is number => v != null)
  const pppAvg = pppValues.length ? pppValues.reduce((a, b) => a + b, 0) / pppValues.length : null

  const qualityValues = allRows.map(({ s }) => s.quality_avg).filter((v): v is number => v != null)
  const qualityAvg = qualityValues.length ? qualityValues.reduce((a, b) => a + b, 0) / qualityValues.length : null

  const rows = [...allRows].sort((a, b) => {
    const va = sortValue(a, sortKey), vb = sortValue(b, sortKey)
    if (typeof va === "string" || typeof vb === "string") return String(va).localeCompare(String(vb)) * sortDir
    return (va - vb) * sortDir
  })

  function toggleSort(key: SortKey) {
    if (key === sortKey) setSortDir(d => (d === 1 ? -1 : 1))
    else { setSortKey(key); setSortDir(key === "name" ? 1 : -1) }
  }

  const Th = ({ label, k, align="center", color="text-gray-400" }: { label: string; k: SortKey; align?: "left"|"center"; color?: string }) => (
    <th onClick={() => toggleSort(k)}
      className={`${align === "left" ? "text-left pr-4 min-w-[140px]" : "text-center px-2"} ${color} py-2 font-semibold cursor-pointer select-none hover:text-white transition-colors whitespace-nowrap`}>
      {label}{sortKey === k && (sortDir === 1 ? " ▲" : " ▼")}
    </th>
  )

  const defense = isDefense(mode)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <Th label={MODES[mode].label} k="name" align="left" />
            <Th label="Plays" k="total" />
            <Th label="Frequency" k="total" color="text-yellow-600" />
            <Th label="Points" k="points" />
            <Th label="Shots/Possessions" k="possessions" />
            <Th label={defense ? "PPP Allowed" : "PPP"} k="ppp" />
            <Th label="Quality Shot" k="quality" />
            <Th label="Paint Touch" k="paint" />
            {!defense && <Th label="Broken Play" k="broken" />}
            <Th label="PPP Paint" k="ppp_paint" />
            <Th label="PPP No Paint" k="ppp_no_paint" />
            {!defense && <Th label="PPP Broken" k="ppp_broken" />}
            {!defense && <Th label="PPP No Broken" k="ppp_no_broken" />}
          </tr>
        </thead>
        <tbody>
          {rows.map(({ name, s }, i) => {
            const isSelected = name === selected
            const pppBetter = s.ppp.ppp != null && pppAvg != null && (defense ? s.ppp.ppp < pppAvg : s.ppp.ppp > pppAvg)
            const pppWorse  = s.ppp.ppp != null && pppAvg != null && (defense ? s.ppp.ppp > pppAvg : s.ppp.ppp < pppAvg)
            const pppColor = pppBetter ? "text-green-500" : pppWorse ? "text-red-500" : "text-gray-300"
            const qualityBetter = s.quality_avg != null && qualityAvg != null && (defense ? s.quality_avg < qualityAvg : s.quality_avg > qualityAvg)
            const qualityWorse  = s.quality_avg != null && qualityAvg != null && (defense ? s.quality_avg > qualityAvg : s.quality_avg < qualityAvg)
            const qualityColor = qualityBetter ? "text-green-500" : qualityWorse ? "text-red-500" : "text-gray-300"
            return (
              <tr key={i} onClick={() => onSelect(name === selected ? "" : name)}
                className={`cursor-pointer hover:bg-gray-800/60 transition-colors ${i % 2 === 1 ? "bg-gray-800/30" : ""} ${isSelected ? "bg-red-600/20" : ""}`}>
                <td className="py-1.5 pr-4 text-gray-200 font-medium">{name}</td>
                <td className="py-1.5 px-2 text-center text-white font-bold">{s.total}</td>
                <td className="py-1.5 px-2 text-center text-yellow-500">{totalAll ? Math.round(s.total / totalAll * 100) : 0}%</td>
                <td className="py-1.5 px-2 text-center text-gray-300">{s.ppp.points}</td>
                <td className="py-1.5 px-2 text-center text-gray-300">{s.ppp.possessions}</td>
                <td className={`py-1.5 px-2 text-center font-bold ${pppColor}`}>{s.ppp.ppp ?? "—"}</td>
                <td className={`py-1.5 px-2 text-center font-bold ${qualityColor}`}>{s.quality_avg ?? "—"}</td>
                <td className="py-1.5 px-2 text-center text-gray-300">{s.paint_touch_n} <span className="text-gray-500">({s.total ? Math.round(s.paint_touch_n / s.total * 100) : 0}%)</span></td>
                {!defense && <td className="py-1.5 px-2 text-center text-gray-300">{s.broken_play} <span className="text-gray-500">({s.total ? Math.round(s.broken_play / s.total * 100) : 0}%)</span></td>}
                <td className="py-1.5 px-2 text-center text-gray-300">{s.ppp_paint.ppp ?? "—"} <span className="text-gray-500">({s.ppp_paint.possessions})</span></td>
                <td className="py-1.5 px-2 text-center text-gray-300">{s.ppp_no_paint.ppp ?? "—"} <span className="text-gray-500">({s.ppp_no_paint.possessions})</span></td>
                {!defense && <td className="py-1.5 px-2 text-center text-gray-300">{s.ppp_broken.ppp ?? "—"} <span className="text-gray-500">({s.ppp_broken.possessions})</span></td>}
                {!defense && <td className="py-1.5 px-2 text-center text-gray-300">{s.ppp_no_broken.ppp ?? "—"} <span className="text-gray-500">({s.ppp_no_broken.possessions})</span></td>}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const [mode, setMode] = useState<Mode>("playcalls")
  const [period, setPeriod] = useState<string>("ALL")
  const [data, setData] = useState<EntryData[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<string | null>(null)
  const [search, setSearch] = useState("")

  useEffect(() => {
    setLoading(true)
    setSelected(null)
    setSearch("")
    fetch(MODES[mode].url).then(r => r.json()).then(d => { setData(d); setLoading(false) })
  }, [mode])

  const pc = useMemo(() => selected ? data.find(d => entryName(d, mode) === selected) ?? null : null, [data, selected, mode])
  const pcStats = pc ? stats(pc, period) : null
  const defense = isDefense(mode)

  const filteredData = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return data
    return data.filter(d => entryName(d, mode).toLowerCase().includes(q))
  }, [data, mode, search])

  const overview = useMemo(() =>
    filteredData.map(d => ({ name: entryName(d, mode), value: stats(d, period).total }))
        .filter(d => d.value > 0)
        .sort((a,b) => b.value - a.value),
    [filteredData, mode, period]
  )

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">Loading...</div>
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
          {pc && pcStats && <span className="bg-red-600/20 text-red-400 text-xs font-semibold px-2.5 py-1 rounded-lg">{entryName(pc, mode)} — {pcStats.total} actions</span>}
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
            ← All
          </button>
        )}
        <Link href="/dashboard/pr"
          className="flex items-center gap-1.5 text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors print:hidden">
          <Repeat2 size={13} /> P&R
        </Link>
        <button onClick={() => window.print()}
          className="flex items-center gap-1.5 text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors print:hidden">
          <Download size={13} /> PDF
        </button>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Selettore periodo + ricerca — sempre visibile */}
        <div className="flex flex-wrap items-center justify-between gap-2 print:hidden">
          <div className="flex flex-wrap gap-2">
            {PERIODS.map(p => (
              <button key={p} onClick={() => setPeriod(p)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${period === p ? "bg-red-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                {PERIOD_LABEL[p]}
              </button>
            ))}
          </div>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder={`Search ${MODES[mode].label.toLowerCase()}...`}
            className="bg-gray-800 text-white text-xs placeholder-gray-500 rounded-lg px-3 py-1.5 outline-none focus:ring-1 focus:ring-red-600 w-48" />
        </div>

        {/* Overview — sempre visibile */}
        <Card title={MODES[mode].title}>
          <ResponsiveContainer width="100%" height={Math.max(280, overview.length * 26)}>
            <BarChart data={overview} layout="vertical"
              onClick={e => e?.activeLabel && setSelected(String(e.activeLabel) === selected ? null : String(e.activeLabel))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
              <XAxis type="number" tick={{fill:"#6b7280",fontSize:11}} />
              <YAxis type="category" dataKey="name" width={155} tick={{fill:"#9ca3af",fontSize:11}} />
              <Tooltip content={<TT />} />
              <Bar dataKey="value" name="Actions" radius={[0,4,4,0]} className="cursor-pointer">
                {overview.map((d,i) => (
                  <Cell key={i} fill={d.name === selected ? "#fff" : RED}
                    opacity={selected && d.name !== selected ? 0.25 : 1} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Riepilogo — sempre visibile */}
        <Card title="Summary">
          <SummaryTable data={filteredData} mode={mode} period={period} selected={selected} onSelect={name => setSelected(name || null)} />
        </Card>

        {/* Dettaglio play call selezionata */}
        {pc && pcStats && (
          <>
            {/* KPI */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { l: "Total Actions",   v: pcStats.total, sub: "" },
                { l: defense ? "PPP Allowed" : "PPP", v: pcStats.ppp.ppp ?? "—", sub: pcStats.ppp.possessions ? `${pcStats.ppp.points} pt / ${pcStats.ppp.possessions} poss` : "" },
                { l: "Paint Touch",     v: `${pcStats.paint_touch_n} (${pcStats.total ? Math.round(pcStats.paint_touch_n/pcStats.total*100) : 0}%)`, sub: "" },
                { l: defense ? "Opponent Quality" : "Avg Quality", v: pcStats.quality_avg ?? "—", sub: "" },
                ...(defense ? [] : [{ l: "Broken Play", v: `${pcStats.broken_play} (${pcStats.total ? Math.round(pcStats.broken_play/pcStats.total*100) : 0}%)`, sub: "" }]),
              ].map(({l,v,sub}) => (
                <div key={l} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
                  <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">{l}</p>
                  <p className="text-white font-black text-2xl">{v}</p>
                  {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
                </div>
              ))}
            </div>

            {/* Distribuzioni */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <Card title="Results"><DistTable data={pcStats.results} total={pcStats.total} /></Card>
              <Card title={defense ? "D Situation" : "Situation"}><DistTable data={pcStats.situations} total={pcStats.total} /></Card>
              <Card title="Shot Location"><DistTable data={pcStats.shot_locations} total={pcStats.total} /></Card>
              <Card title={defense ? "D Coverages" : "O Coverages"}><DistTable data={pcStats.o_coverages} total={pcStats.total} /></Card>
              <Card title="Quality Shot"><DistTable data={pcStats.quality} total={pcStats.total} /></Card>
              <Card title="Paint Touches"><DistTable data={pcStats.paint_touches} total={pcStats.total} /></Card>
              {!defense && <Card title="Pressing"><DistTable data={pcStats.pressing} total={pcStats.total} /></Card>}
              {!defense && <Card title="Broken Play"><DistTable data={pcStats.broken_play_dist} total={pcStats.total} /></Card>}
            </div>

            {/* Legami */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card title={defense ? "D Situation × Results" : "Situation × Results"}><CrossTable data={pcStats.sit_x_results} /></Card>
              <Card title={defense ? "D Coverages × Results" : "O Coverages × Results"}><CrossTable data={pcStats.cov_x_results} /></Card>
              {!defense && <Card title="Situation × Paint Touches"><CrossTable data={pcStats.sit_x_paint} /></Card>}
              {!defense && <Card title="Situation × Quality Shot"><CrossTable data={pcStats.sit_x_quality} /></Card>}
              <Card title="Paint Touches × Results" className="lg:col-span-2"><CrossTable data={pcStats.paint_x_results} /></Card>
            </div>
          </>
        )}

      </div>
    </div>
  )
}
