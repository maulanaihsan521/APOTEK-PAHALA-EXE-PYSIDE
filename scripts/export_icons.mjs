// Salin ikon Lucide (dari mobile-web/node_modules) menjadi berkas SVG.
// Jalankan dari akar proyek:
//     node scripts/export_icons.mjs
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const sourceDir = path.join(root, 'mobile-web', 'node_modules', 'lucide-react', 'dist', 'esm', 'icons')
const targetDir = path.join(root, 'desktop', 'app', 'assets', 'icons')

const names = [
  'house', 'trending-up', 'receipt-text', 'cloud-rain', 'package', 'clipboard-list',
  'file-bar-chart', 'settings', 'bell', 'sun', 'moon', 'log-out', 'user-round',
  'calendar-days', 'calendar-range', 'chevron-down', 'chevron-right', 'chevron-left',
  'search', 'download', 'upload', 'file-spreadsheet', 'file-text', 'refresh-cw', 'plus',
  'check', 'circle-check', 'triangle-alert', 'circle-x', 'info', 'sparkles', 'target',
  'wallet', 'pill', 'shopping-bag', 'database', 'hard-drive-download', 'hard-drive-upload',
  'play', 'sliders-horizontal', 'history', 'badge-check', 'pencil-line', 'trash-2',
  'eye', 'eye-off', 'lock-keyhole', 'activity', 'gauge', 'arrow-up-right',
  'arrow-down-right', 'arrow-right', 'filter', 'printer', 'cpu', 'cloud', 'droplets',
  'thermometer', 'shield-check', 'building-2', 'circle-alert', 'external-link', 'x',
  'book-open', 'circle-help', 'wand-sparkles', 'maximize', 'rotate-ccw', 'server',
  'plug-zap', 'leaf', 'chart-column', 'clipboard-check', 'clock', 'badge-info',
  'monitor', 'chevrons-up-down', 'ellipsis', 'circle-user-round', 'save', 'undo-2',
  'flask-conical', 'brain', 'file-down', 'list-filter', 'boxes', 'layout-grid',
  'calendar-clock', 'database-backup', 'scan-line', 'key-round', 'loading', 'circle-dot'
]

function resolveFile(name) {
  const direct = path.join(sourceDir, `${name}.js`)
  if (fs.existsSync(direct)) return direct
  const aliases = { home: 'house', 'chart-column': 'chart-no-axes-column-increasing' }
  const alias = aliases[name]
  if (alias) {
    const file = path.join(sourceDir, `${alias}.js`)
    if (fs.existsSync(file)) return file
  }
  return null
}

function readNode(file, depth = 0) {
  if (depth > 5) return null
  const text = fs.readFileSync(file, 'utf8')
  const alias = text.match(/export \{ default \} from '\.\/([^']+)\.js'/)
  if (alias) return readNode(path.join(sourceDir, `${alias[1]}.js`), depth + 1)
  const match = text.match(/const __iconNode = ([\s\S]*?);\nconst /)
  if (!match) return null
  return Function(`"use strict"; return ${match[1]}`)()
}

const attrs = (object = {}) =>
  Object.entries(object)
    .filter(([key]) => !['key'].includes(key))
    .map(([key, value]) => `${key}="${String(value).replaceAll('&', '&amp;').replaceAll('"', '&quot;')}"`)
    .join(' ')

fs.mkdirSync(targetDir, { recursive: true })
let written = 0
const missing = []
for (const name of names) {
  const file = resolveFile(name)
  if (!file) {
    missing.push(name)
    continue
  }
  const node = readNode(file)
  if (!node) {
    missing.push(name)
    continue
  }
  const children = node
    .map(([tag, properties]) => `  <${tag} ${attrs(properties)} />`)
    .join('\n')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n${children}\n</svg>\n`
  fs.writeFileSync(path.join(targetDir, `${name}.svg`), svg, 'utf8')
  written += 1
}

console.log(`icons written: ${written}`)
if (missing.length) console.log(`missing: ${missing.join(', ')}`)
