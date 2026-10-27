import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { delimiter, resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const python = process.platform === 'win32' ? 'python' : 'python3'
const dependencyDir = resolve(root, '.python_deps')
let vite
let shuttingDown = false

function ensurePythonDependencies() {
  if (existsSync(resolve(dependencyDir, 'flask')) && existsSync(resolve(dependencyDir, 'sqlalchemy'))) return
  console.log('[setup] 正在安装 Flask 后端依赖…')
  const result = spawnSync(python, [
    '-m', 'pip', 'install', '--target', dependencyDir,
    '-r', 'requirements-dev.txt', '--disable-pip-version-check',
  ], { cwd: root, stdio: 'inherit' })
  if (result.status !== 0) process.exit(result.status || 1)
}

function startVite() {
  vite = spawn(process.execPath, [
    'node_modules/vite/bin/vite.js', '--host', '0.0.0.0', '--port', '3000',
  ], { cwd: root, stdio: 'inherit' })
  vite.on('exit', (code) => {
    if (!shuttingDown) shutdown(code || 0)
  })
}

async function waitForBackend() {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (flask.exitCode !== null) throw new Error('Flask 启动失败，请检查上方日志。')
    try {
      const response = await fetch('http://127.0.0.1:5000/api/health', { signal: AbortSignal.timeout(1500) })
      if (response.ok) {
        const health = await response.json()
        console.log(`[backend] 数据库 ${health.database}，新闻 ${health.news} 条，接口已就绪。`)
        return
      }
    } catch (_) { /* 数据库首次导入期间继续等待 */ }
    await new Promise(resolvePromise => setTimeout(resolvePromise, 1000))
  }
  throw new Error('等待 Flask 接口超时。')
}

function shutdown(code = 0) {
  if (shuttingDown) return
  shuttingDown = true
  flask?.kill()
  vite?.kill()
  process.exit(code)
}

ensurePythonDependencies()
const flask = spawn(python, ['backend/app.py'], {
  cwd: root,
  stdio: 'inherit',
  env: {
    ...process.env,
    PYTHONPATH: [dependencyDir, process.env.PYTHONPATH].filter(Boolean).join(delimiter),
    PYTHONUNBUFFERED: '1',
    PORT: '5000',
  },
})
flask.on('error', error => { console.error('[backend]', error); shutdown(1) })
process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

try {
  await waitForBackend()
  startVite()
} catch (error) {
  console.error('[startup]', error)
  shutdown(1)
}
