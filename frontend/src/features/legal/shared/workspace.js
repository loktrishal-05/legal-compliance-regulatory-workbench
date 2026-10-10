// Selected legal workspace: a per-viewer convenience only. The server re-authorizes every request.
import { createContext, useContext } from 'react'

const KEY = 'legal.workspace'

export const WorkspaceContext = createContext({ workspaces: [], workspace: null, select: () => {}, status: 'loading',
  error: null, reload: () => {} })
export const useWorkspace = () => useContext(WorkspaceContext)

export function rememberedWorkspace(storage = globalThis.localStorage) {
  try { return storage?.getItem(KEY) || null } catch { return null }
}

export function rememberWorkspace(id, storage = globalThis.localStorage) {
  try { if (id) storage?.setItem(KEY, id); else storage?.removeItem(KEY) } catch { /* private mode: keep in memory */ }
}

// Only a workspace the server just listed for this user can be selected; a stale remembered id is ignored.
export function chooseWorkspace(items, remembered) {
  if (!items?.length) return null
  return items.find(item => item.workspace_id === remembered) || items[0]
}
