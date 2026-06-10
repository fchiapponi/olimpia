import { NextResponse } from "next/server"
import fs from "fs"
import path from "path"

export async function GET() {
  const jsonPath = path.join(process.cwd(), "..", "output", "analisi_playcalls.json")

  if (!fs.existsSync(jsonPath)) {
    return NextResponse.json({ error: "analisi_playcalls.json non trovato" }, { status: 404 })
  }

  const data = JSON.parse(fs.readFileSync(jsonPath, "utf-8"))
  return NextResponse.json(data)
}
