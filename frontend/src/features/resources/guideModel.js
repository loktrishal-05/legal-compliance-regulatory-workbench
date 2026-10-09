export const sectionSlug = title => title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

// Static repository Markdown only; React text nodes keep HTML and document instructions inert.
export function guideBlocks(text) {
  const blocks = []
  for (const paragraph of text.split(/\n\s*\n/)) {
    const lines = paragraph.trim().split('\n').filter(line => line.trim() && line.trim() !== '---')
    if (!lines.length) continue
    for (let i = 0; i < lines.length;) {
      const heading = /^(#{1,4}) (.+)$/.exec(lines[i])
      if (heading) { blocks.push({ kind: 'heading', level: heading[1].length, text: heading[2] }); i++; continue }
      if (lines[i].startsWith('|')) {
        const rows = []
        while (lines[i]?.startsWith('|')) {
          const cells = lines[i++].split('|').slice(1, -1).map(cell => cell.trim())
          if (!cells.every(cell => /^:?-+:?$/.test(cell))) rows.push(cells)
        }
        blocks.push({ kind: 'table', rows }); continue
      }
      const list = /^(?:- |\d+\. )/.exec(lines[i])
      if (list) {
        const items = []; const ordered = !lines[i].startsWith('- ')
        while (/^(?:- |\d+\. )/.test(lines[i] || '')) items.push(lines[i++].replace(/^(?:- |\d+\. )/, ''))
        blocks.push({ kind: 'list', ordered, lines: items }); continue
      }
      blocks.push({ kind: 'paragraph', text: lines[i++].replace(/^> /, '') })
    }
  }
  return blocks
}
