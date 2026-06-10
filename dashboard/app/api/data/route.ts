import { NextResponse } from "next/server"
import fs from "fs"
import path from "path"
import Papa from "papaparse"

export async function GET() {
  const csvPath = path.join(process.cwd(), "..", "output", "input_enriched.csv")

  if (!fs.existsSync(csvPath)) {
    return NextResponse.json({ error: "input_enriched.csv non trovato" }, { status: 404 })
  }

  const text = fs.readFileSync(csvPath, "utf-8")
  const { data } = Papa.parse(text, { header: true, skipEmptyLines: true })

  return NextResponse.json(data)
}
