import test from 'node:test'
import assert from 'node:assert/strict'
import { guideBlocks, sectionSlug } from './guideModel.js'

test('guide rendering preserves content, table headers and citation anchors without interpreting HTML', () => {
  const blocks = guideBlocks('## 4.1 Upload *(MVP)*\n\n- Never bypass quarantine\n- <script>unsafe()</script>\n\n| Role | Access |\n|---|---|\n| Auditor | Read only |')
  assert.equal(sectionSlug(blocks[0].text), '4-1-upload-mvp')
  assert.equal(blocks[1].lines[1], '<script>unsafe()</script>')
  assert.deepEqual(blocks[2].rows, [['Role', 'Access'], ['Auditor', 'Read only']])
})
