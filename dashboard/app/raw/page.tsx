"use client"

import { useEffect, useState, useMemo } from "react"
import Link from "next/link"
import { ArrowLeft, Search } from "lucide-react"

export default function RawPage() {
  const [rows, setRows] = useState<Record<string, string>[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [rowFilter, setRowFilter] = useState("ALL")

  useEffect(() => {
    fetch("/api/data").then(r => r.json()).then(data => { setRows(data); setLoading(false) })
  }, [])

  const columns = useMemo(() => rows.length ? Object.keys(rows[0]) : [], [rows])

  const filtered = useMemo(() => rows.filter(r => {
    if (rowFilter !== "ALL" && r["Row"] !== rowFilter) return false
    if (!search) return true
    return Object.values(r).some(v => v.toLowerCase().includes(search.toLowerCase()))
  }), [rows, search, rowFilter])

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-20 bg-gray-900/80 backdrop-blur border-b border-gray-800 px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-gray-400 hover:text-white transition-colors"><ArrowLeft size={18} /></Link>
        <h1 className="text-white font-bold text-sm flex-1">Dati Grezzi</h1>
        <div className="flex items-center gap-2">
          <select value={rowFilter} onChange={e => setRowFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-300 text-xs rounded-lg px-3 py-1.5">
            <option value="ALL">Tutte le righe</option>
            <option value="OFFENSE">Offense</option>
            <option value="DEFENSE">Defense</option>
          </select>
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Cerca..."
              className="bg-gray-800 border border-gray-700 text-gray-300 text-xs rounded-lg pl-8 pr-3 py-1.5 w-48" />
          </div>
          <span className="text-gray-500 text-xs">{filtered.length} righe</span>
        </div>
      </header>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-gray-400">Caricamento...</div>
      ) : (
        <div className="overflow-auto flex-1">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="sticky top-0 bg-gray-900 z-10">
              <tr>
                {columns.map(col => (
                  <th key={col} className="px-3 py-2 text-gray-400 font-semibold uppercase tracking-wider whitespace-nowrap border-b border-gray-800 bg-gray-900">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => (
                <tr key={i} className={`border-b border-gray-900 ${i % 2 === 1 ? "bg-gray-900/40" : ""} hover:bg-gray-800/60 transition-colors`}>
                  {columns.map(col => (
                    <td key={col} className={`px-3 py-1.5 whitespace-nowrap max-w-[200px] truncate
                      ${row[col] === "OFFENSE" ? "text-red-400 font-semibold" :
                        row[col] === "DEFENSE" ? "text-blue-400 font-semibold" :
                        "text-gray-300"}`}>
                      {row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
