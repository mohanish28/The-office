# AI Office — Chunk 4: Frontend Dashboard

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React owner dashboard — login, task creation, live approval timeline with WebSocket updates, agent output viewer, and the org chart visual of the AI office hierarchy.

**Architecture:** Vite + React 18 + TypeScript. Zustand for auth state (token persisted in localStorage). React Query for server data. Axios instance with JWT header + silent refresh. WebSocket hook for real-time pipeline updates. TailwindCSS for styling.

**Tech Stack:** React 18, TypeScript, Vite, TailwindCSS, Zustand, @tanstack/react-query, Axios, react-router-dom v6, react-markdown, vitest + @testing-library/react

**Prerequisites:** Chunk 1 backend running on port 8000

---

## File Map

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── src/
│   ├── main.tsx                        # React root, providers
│   ├── App.tsx                         # Routes
│   ├── api/
│   │   ├── client.ts                   # Axios: base URL, auth header, 401 refresh
│   │   ├── auth.ts                     # login(), register()
│   │   ├── tasks.ts                    # createTask(), listTasks(), getTask()
│   │   └── approvals.ts                # getApprovals()
│   ├── store/
│   │   └── auth.ts                     # Zustand: token, user, login(), logout()
│   ├── hooks/
│   │   ├── useAuth.ts                  # login/logout actions + redirect
│   │   └── useTaskWS.ts               # WebSocket → live step updates
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx               # task list + stats
│   │   ├── TaskCreate.tsx              # new task form
│   │   └── TaskDetail.tsx              # approval timeline + agent outputs
│   └── components/
│       ├── ProtectedRoute.tsx          # redirect if no token
│       ├── OrgChart.tsx                # static AI office hierarchy visual
│       ├── ApprovalTimeline.tsx        # step-by-step pipeline status
│       ├── AgentOutputCard.tsx         # rendered markdown output per step
│       └── SafetyBadge.tsx             # color badge for safety score
├── tests/
│   ├── setup.ts
│   ├── Login.test.tsx
│   ├── Dashboard.test.tsx
│   └── ApprovalTimeline.test.tsx
└── Dockerfile
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/index.html`

- [ ] **Step 1: Scaffold with Vite**

```bash
cd "C:/Users/DELL/Desktop/working/The office"
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

- [ ] **Step 2: Install deps**

```bash
npm install axios zustand @tanstack/react-query react-router-dom react-markdown
npm install -D tailwindcss postcss autoprefixer @tailwindcss/typography vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react
npx tailwindcss init -p
```

- [ ] **Step 3: Update tailwind.config.js**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        nvidia: { green: "#76b900", dark: "#1a1a2e" }
      }
    }
  },
  plugins: [require("@tailwindcss/typography")]
}
```

- [ ] **Step 4: Update vite.config.ts**

```ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true }
    }
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"]
  }
})
```

- [ ] **Step 5: Write src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 6: Verify dev server starts**

```bash
npm run dev
# Expected: Local: http://localhost:5173/ — Vite default React page visible
```

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "chore: bootstrap React+TS+Vite+Tailwind frontend"
```

---

## Task 2: Auth Store + API Client

**Files:**
- Create: `frontend/src/store/auth.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/auth.ts`
- Test: `frontend/tests/setup.ts`

- [ ] **Step 1: Write tests/setup.ts**

```ts
import "@testing-library/jest-dom"
```

- [ ] **Step 2: Write src/store/auth.ts**

```ts
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface AuthState {
  token: string | null
  email: string | null
  isOwner: boolean
  setAuth: (token: string, email: string, isOwner: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      isOwner: false,
      setAuth: (token, email, isOwner) => set({ token, email, isOwner }),
      logout: () => set({ token: null, email: null, isOwner: false }),
    }),
    { name: "ai-office-auth" }
  )
)
```

- [ ] **Step 3: Write src/api/client.ts**

```ts
import axios from "axios"
import { useAuthStore } from "../store/auth"

const client = axios.create({ baseURL: "/api" })

client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = "/login"
    }
    return Promise.reject(error)
  }
)

export default client
```

- [ ] **Step 4: Write src/api/auth.ts**

```ts
import client from "./client"

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const res = await client.post<{ access_token: string }>("/auth/login", { email, password })
  return res.data
}

export async function register(email: string, password: string): Promise<{ id: string; email: string; is_owner: boolean }> {
  const res = await client.post("/auth/register", { email, password })
  return res.data
}
```

- [ ] **Step 5: Write src/hooks/useAuth.ts**

```ts
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "../store/auth"
import { login as apiLogin } from "../api/auth"

export function useAuth() {
  const { token, email, isOwner, setAuth, logout: storeLogout } = useAuthStore()
  const navigate = useNavigate()

  async function login(email: string, password: string) {
    const data = await apiLogin(email, password)
    // Decode is_owner from JWT payload
    const payload = JSON.parse(atob(data.access_token.split(".")[1]))
    setAuth(data.access_token, email, payload.is_owner ?? false)
    navigate("/")
  }

  function logout() {
    storeLogout()
    navigate("/login")
  }

  return { token, email, isOwner, login, logout }
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/store/ frontend/src/api/ frontend/src/hooks/useAuth.ts frontend/tests/setup.ts
git commit -m "feat: auth store (Zustand persist), API client with JWT interceptor"
```

---

## Task 3: Login Page

**Files:**
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Test: `frontend/tests/Login.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// frontend/tests/Login.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { vi } from "vitest"
import Login from "../src/pages/Login"
import * as authHook from "../src/hooks/useAuth"

test("shows email and password inputs", () => {
  vi.spyOn(authHook, "useAuth").mockReturnValue({
    token: null, email: null, isOwner: false,
    login: vi.fn(), logout: vi.fn()
  })
  render(<MemoryRouter><Login /></MemoryRouter>)
  expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument()
  expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument()
})

test("calls login on submit", async () => {
  const mockLogin = vi.fn()
  vi.spyOn(authHook, "useAuth").mockReturnValue({
    token: null, email: null, isOwner: false,
    login: mockLogin, logout: vi.fn()
  })
  render(<MemoryRouter><Login /></MemoryRouter>)
  fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: "owner@test.com" } })
  fireEvent.change(screen.getByPlaceholderText(/password/i), { target: { value: "secret" } })
  fireEvent.click(screen.getByRole("button", { name: /sign in/i }))
  await waitFor(() => expect(mockLogin).toHaveBeenCalledWith("owner@test.com", "secret"))
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd frontend && npx vitest run tests/Login.test.tsx
# Expected: Cannot find module '../src/pages/Login'
```

- [ ] **Step 3: Write src/pages/Login.tsx**

```tsx
import { useState } from "react"
import { useAuth } from "../hooks/useAuth"

export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password)
    } catch {
      setError("Invalid email or password")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-nvidia-dark flex items-center justify-center">
      <div className="bg-gray-900 p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-nvidia-green mb-2">⚡ AI Office</h1>
        <p className="text-gray-400 mb-6">Owner login — NVIDIA NIM powered</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-nvidia-green outline-none"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-nvidia-green outline-none"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-nvidia-green text-black font-bold py-3 rounded-lg hover:bg-green-500 disabled:opacity-50 transition"
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Write src/components/ProtectedRoute.tsx**

```tsx
import { Navigate } from "react-router-dom"
import { useAuthStore } from "../store/auth"

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}
```

- [ ] **Step 5: Run — expect PASS**

```bash
npx vitest run tests/Login.test.tsx
# Expected: 2 PASSED
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Login.tsx frontend/src/components/ProtectedRoute.tsx frontend/tests/Login.test.tsx
git commit -m "feat: Login page + ProtectedRoute guard"
```

---

## Task 4: Task API + Dashboard Page

**Files:**
- Create: `frontend/src/api/tasks.ts`
- Create: `frontend/src/api/approvals.ts`
- Create: `frontend/src/pages/Dashboard.tsx`
- Test: `frontend/tests/Dashboard.test.tsx`

- [ ] **Step 1: Write src/api/tasks.ts**

```ts
import client from "./client"

export interface Task {
  id: string
  title: string
  description: string
  task_type: string
  status: string
  created_by: string
  created_at: string
  celery_task_id: string | null
}

export async function listTasks(): Promise<Task[]> {
  const res = await client.get<Task[]>("/tasks")
  return res.data
}

export async function getTask(id: string): Promise<Task> {
  const res = await client.get<Task>(`/tasks/${id}`)
  return res.data
}

export async function createTask(body: { title: string; description: string; task_type: string }): Promise<Task> {
  const res = await client.post<Task>("/tasks", body)
  return res.data
}
```

- [ ] **Step 2: Write src/api/approvals.ts**

```ts
import client from "./client"

export interface ApprovalStep {
  id: string
  task_id: string
  step_number: number
  agent_role: string
  status: string
  output: string | null
  verdict: string | null
  started_at: string | null
  finished_at: string | null
}

export async function getApprovals(taskId: string): Promise<ApprovalStep[]> {
  const res = await client.get<ApprovalStep[]>(`/tasks/${taskId}/approvals`)
  return res.data
}
```

- [ ] **Step 3: Write failing test**

```tsx
// frontend/tests/Dashboard.test.tsx
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { vi } from "vitest"
import Dashboard from "../src/pages/Dashboard"
import * as tasksApi from "../src/api/tasks"

test("shows 'No tasks yet' when list is empty", async () => {
  vi.spyOn(tasksApi, "listTasks").mockResolvedValue([])
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><Dashboard /></MemoryRouter>
    </QueryClientProvider>
  )
  expect(await screen.findByText(/no tasks yet/i)).toBeInTheDocument()
})

test("shows task titles when loaded", async () => {
  vi.spyOn(tasksApi, "listTasks").mockResolvedValue([
    { id: "1", title: "Build login page", description: "", task_type: "frontend",
      status: "approved", created_by: "u1", created_at: new Date().toISOString(), celery_task_id: null }
  ])
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><Dashboard /></MemoryRouter>
    </QueryClientProvider>
  )
  expect(await screen.findByText("Build login page")).toBeInTheDocument()
})
```

- [ ] **Step 4: Run — expect FAIL**

```bash
npx vitest run tests/Dashboard.test.tsx
# Expected: Cannot find module '../src/pages/Dashboard'
```

- [ ] **Step 5: Write src/pages/Dashboard.tsx**

```tsx
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { listTasks, Task } from "../api/tasks"
import { useAuth } from "../hooks/useAuth"

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-gray-600",
  in_progress: "bg-blue-600 animate-pulse",
  awaiting_approval: "bg-yellow-600",
  approved: "bg-nvidia-green text-black",
  rejected: "bg-red-600",
}

function TaskRow({ task }: { task: Task }) {
  return (
    <Link to={`/tasks/${task.id}`} className="block bg-gray-800 hover:bg-gray-750 rounded-xl p-4 border border-gray-700 hover:border-nvidia-green transition">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-white font-semibold">{task.title}</h3>
          <p className="text-gray-400 text-sm mt-1">{task.task_type} · {new Date(task.created_at).toLocaleString()}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${STATUS_COLOR[task.status] ?? "bg-gray-600"}`}>
          {task.status.replace("_", " ")}
        </span>
      </div>
    </Link>
  )
}

export default function Dashboard() {
  const { email, logout } = useAuth()
  const { data: tasks, isLoading } = useQuery({ queryKey: ["tasks"], queryFn: listTasks, refetchInterval: 5000 })

  return (
    <div className="min-h-screen bg-nvidia-dark text-white">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-nvidia-green">⚡ AI Office</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{email}</span>
          <Link to="/tasks/new" className="bg-nvidia-green text-black px-4 py-2 rounded-lg font-bold hover:bg-green-500 transition">
            + New Task
          </Link>
          <button onClick={logout} className="text-gray-400 hover:text-white text-sm">Logout</button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6">
        <h2 className="text-xl font-semibold mb-4">Your Tasks</h2>
        {isLoading && <p className="text-gray-400">Loading…</p>}
        {!isLoading && (!tasks || tasks.length === 0) && (
          <div className="text-center py-16 text-gray-500">
            <p className="text-4xl mb-4">📋</p>
            <p className="text-lg">No tasks yet</p>
            <p className="text-sm mt-2">Create your first task to get the AI office working</p>
          </div>
        )}
        <div className="space-y-3">
          {tasks?.map((t) => <TaskRow key={t.id} task={t} />)}
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 6: Run — expect PASS**

```bash
npx vitest run tests/Dashboard.test.tsx
# Expected: 2 PASSED
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/ frontend/src/pages/Dashboard.tsx frontend/tests/Dashboard.test.tsx
git commit -m "feat: Dashboard page — task list with status badges, 5s auto-refresh"
```

---

## Task 5: Task Create Page

**Files:**
- Create: `frontend/src/pages/TaskCreate.tsx`

- [ ] **Step 1: Write src/pages/TaskCreate.tsx**

```tsx
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { createTask } from "../api/tasks"

const TASK_TYPES = [
  { value: "full", label: "Full Stack", icon: "🏗️", desc: "Frontend + Backend + API + DevOps" },
  { value: "frontend", label: "Frontend", icon: "🖥️", desc: "React components, UI, UX" },
  { value: "backend", label: "Backend", icon: "🗄️", desc: "API, database, business logic" },
  { value: "devops", label: "DevOps", icon: "☁️", desc: "Docker, CI/CD, infrastructure" },
  { value: "data", label: "Data", icon: "📊", desc: "Extraction, search, RAG" },
]

export default function TaskCreate() {
  const navigate = useNavigate()
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [taskType, setTaskType] = useState("full")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    try {
      const task = await createTask({ title, description, task_type: taskType })
      navigate(`/tasks/${task.id}`)
    } catch {
      setError("Failed to create task. Check your connection.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-nvidia-dark text-white">
      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-2xl font-bold text-nvidia-green">⚡ New Task</h1>
      </header>
      <main className="max-w-2xl mx-auto p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Task Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Build a user authentication system"
              required
              className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-nvidia-green outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what you need built in detail…"
              required
              rows={5}
              className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-nvidia-green outline-none resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Pipeline Type</label>
            <div className="grid grid-cols-1 gap-3">
              {TASK_TYPES.map((t) => (
                <label key={t.value} className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition ${taskType === t.value ? "border-nvidia-green bg-gray-800" : "border-gray-700 hover:border-gray-500"}`}>
                  <input type="radio" value={t.value} checked={taskType === t.value} onChange={() => setTaskType(t.value)} className="hidden" />
                  <span className="text-2xl">{t.icon}</span>
                  <div>
                    <p className="font-semibold">{t.label}</p>
                    <p className="text-sm text-gray-400">{t.desc}</p>
                  </div>
                  {taskType === t.value && <span className="ml-auto text-nvidia-green">✓</span>}
                </label>
              ))}
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-3">
            <button type="button" onClick={() => navigate("/")} className="flex-1 border border-gray-600 py-3 rounded-lg hover:border-gray-400 transition">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="flex-1 bg-nvidia-green text-black font-bold py-3 rounded-lg hover:bg-green-500 disabled:opacity-50 transition">
              {loading ? "Submitting to AI Office…" : "Submit Task"}
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/TaskCreate.tsx
git commit -m "feat: TaskCreate page — pipeline type selector, form submit"
```

---

## Task 6: WebSocket Hook + Approval Timeline

**Files:**
- Create: `frontend/src/hooks/useTaskWS.ts`
- Create: `frontend/src/components/ApprovalTimeline.tsx`
- Create: `frontend/src/components/AgentOutputCard.tsx`
- Create: `frontend/src/components/SafetyBadge.tsx`
- Test: `frontend/tests/ApprovalTimeline.test.tsx`

- [ ] **Step 1: Write src/hooks/useTaskWS.ts**

```ts
import { useEffect, useState } from "react"

export interface LiveStep {
  step: number
  role: string
  status: string
  verdict: string | null
}

export interface WSMessage {
  type: "state" | "step_update" | "ping"
  task_status?: string
  steps?: LiveStep[]
  step?: LiveStep
}

export function useTaskWS(taskId: string) {
  const [steps, setSteps] = useState<LiveStep[]>([])
  const [taskStatus, setTaskStatus] = useState<string | null>(null)

  useEffect(() => {
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/tasks/${taskId}`)

    ws.onmessage = (e) => {
      const msg: WSMessage = JSON.parse(e.data)
      if (msg.type === "state") {
        setTaskStatus(msg.task_status ?? null)
        setSteps(msg.steps ?? [])
      } else if (msg.type === "step_update" && msg.step) {
        setSteps((prev) => {
          const idx = prev.findIndex((s) => s.step === msg.step!.step)
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = msg.step!
            return next
          }
          return [...prev, msg.step!]
        })
      }
    }

    return () => ws.close()
  }, [taskId])

  return { steps, taskStatus }
}
```

- [ ] **Step 2: Write src/components/SafetyBadge.tsx**

```tsx
interface Props { score: number | null }

export default function SafetyBadge({ score }: Props) {
  if (score === null) return null
  const pct = Math.round(score * 100)
  const color = score >= 0.8 ? "bg-nvidia-green text-black" : score >= 0.5 ? "bg-yellow-500 text-black" : "bg-red-500 text-white"
  return <span className={`text-xs font-bold px-2 py-1 rounded-full ${color}`}>Safety {pct}%</span>
}
```

- [ ] **Step 3: Write src/components/AgentOutputCard.tsx**

```tsx
import ReactMarkdown from "react-markdown"
import SafetyBadge from "./SafetyBadge"

interface Props {
  role: string
  output: string | null
  verdict: string | null
}

const ROLE_ICON: Record<string, string> = {
  cto: "🧠", senior_lead: "⚡", product_manager: "📋",
  frontend_dev: "🖥️", backend_dev: "🗄️", api_engineer: "🔗",
  devops: "☁️", qa_engineer: "🧪", safety_reviewer: "🛡️",
  data_extractor: "🔍", rag_search: "📈",
}

const VERDICT_COLOR: Record<string, string> = {
  APPROVE: "text-nvidia-green", APPROVED: "text-nvidia-green",
  REJECT: "text-red-400", REJECTED: "text-red-400",
  REVISE: "text-yellow-400", REVISED: "text-yellow-400",
  PASS: "text-nvidia-green", FAIL: "text-red-400",
}

export default function AgentOutputCard({ role, output, verdict }: Props) {
  let parsed: Record<string, unknown> | null = null
  try { if (output) parsed = JSON.parse(output) } catch {}

  const safetyScore = parsed && "safety_score" in parsed ? Number(parsed.safety_score) : null
  const displayText = parsed
    ? (parsed.reasoning as string) || (parsed.summary as string) || (parsed.synthesized_answer as string)
      || (parsed.component_code as string) || (parsed.implementation_code as string)
      || JSON.stringify(parsed, null, 2)
    : output

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{ROLE_ICON[role] ?? "🤖"}</span>
          <span className="font-semibold text-white capitalize">{role.replace(/_/g, " ")}</span>
        </div>
        <div className="flex items-center gap-2">
          {safetyScore !== null && <SafetyBadge score={safetyScore} />}
          {verdict && <span className={`text-sm font-bold ${VERDICT_COLOR[verdict] ?? "text-gray-400"}`}>{verdict}</span>}
        </div>
      </div>
      {displayText && (
        <div className="prose prose-invert prose-sm max-w-none bg-gray-900 rounded-lg p-3 max-h-64 overflow-y-auto">
          <ReactMarkdown>{displayText.slice(0, 2000)}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Write failing test**

```tsx
// frontend/tests/ApprovalTimeline.test.tsx
import { render, screen } from "@testing-library/react"
import ApprovalTimeline from "../src/components/ApprovalTimeline"

const steps = [
  { step: 1, role: "product_manager", status: "approved", verdict: "APPROVE" },
  { step: 2, role: "frontend_dev", status: "running", verdict: null },
  { step: 3, role: "cto", status: "pending", verdict: null },
]

test("renders all step roles", () => {
  render(<ApprovalTimeline steps={steps} />)
  expect(screen.getByText(/product manager/i)).toBeInTheDocument()
  expect(screen.getByText(/frontend dev/i)).toBeInTheDocument()
  expect(screen.getByText(/cto/i)).toBeInTheDocument()
})

test("shows approved verdict for completed step", () => {
  render(<ApprovalTimeline steps={steps} />)
  expect(screen.getByText("APPROVE")).toBeInTheDocument()
})
```

- [ ] **Step 5: Run — expect FAIL**

```bash
npx vitest run tests/ApprovalTimeline.test.tsx
# Expected: Cannot find module '../src/components/ApprovalTimeline'
```

- [ ] **Step 6: Write src/components/ApprovalTimeline.tsx**

```tsx
import { LiveStep } from "../hooks/useTaskWS"

const STATUS_ICON: Record<string, string> = {
  pending: "⏳", running: "⚙️", approved: "✅", rejected: "❌", revised: "🔄",
}
const STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-500", running: "text-blue-400 animate-pulse",
  approved: "text-nvidia-green", rejected: "text-red-400", revised: "text-yellow-400",
}

interface Props { steps: LiveStep[] }

export default function ApprovalTimeline({ steps }: Props) {
  return (
    <div className="space-y-2">
      {steps.map((s) => (
        <div key={s.step} className="flex items-center gap-4 p-3 bg-gray-800 rounded-lg border border-gray-700">
          <span className="text-xl">{STATUS_ICON[s.status] ?? "⏳"}</span>
          <div className="flex-1">
            <p className={`font-medium capitalize ${STATUS_COLOR[s.status] ?? "text-gray-400"}`}>
              {s.role.replace(/_/g, " ")}
            </p>
            <p className="text-gray-500 text-xs capitalize">{s.status.replace(/_/g, " ")}</p>
          </div>
          {s.verdict && (
            <span className={`text-sm font-bold ${STATUS_COLOR[s.status] ?? "text-gray-400"}`}>
              {s.verdict}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 7: Run — expect PASS**

```bash
npx vitest run tests/ApprovalTimeline.test.tsx
# Expected: 2 PASSED
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/hooks/useTaskWS.ts frontend/src/components/ frontend/tests/ApprovalTimeline.test.tsx
git commit -m "feat: WebSocket hook, ApprovalTimeline, AgentOutputCard, SafetyBadge"
```

---

## Task 7: Task Detail Page

**Files:**
- Create: `frontend/src/pages/TaskDetail.tsx`

- [ ] **Step 1: Write src/pages/TaskDetail.tsx**

```tsx
import { useParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { getTask } from "../api/tasks"
import { getApprovals } from "../api/approvals"
import { useTaskWS } from "../hooks/useTaskWS"
import ApprovalTimeline from "../components/ApprovalTimeline"
import AgentOutputCard from "../components/AgentOutputCard"

const STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-400", in_progress: "text-blue-400",
  approved: "text-nvidia-green", rejected: "text-red-400",
}

export default function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const { data: task } = useQuery({ queryKey: ["task", taskId], queryFn: () => getTask(taskId!), refetchInterval: 3000 })
  const { data: approvals } = useQuery({ queryKey: ["approvals", taskId], queryFn: () => getApprovals(taskId!), refetchInterval: 3000 })
  const { steps: liveSteps } = useTaskWS(taskId!)

  // Merge DB approvals with live WebSocket steps
  const displaySteps = liveSteps.length > 0 ? liveSteps : (approvals ?? []).map((a) => ({
    step: a.step_number, role: a.agent_role, status: a.status, verdict: a.verdict
  }))

  return (
    <div className="min-h-screen bg-nvidia-dark text-white">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <Link to="/" className="text-gray-400 hover:text-white">← Dashboard</Link>
        <h1 className="text-xl font-bold text-nvidia-green">⚡ AI Office</h1>
      </header>

      <main className="max-w-5xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: task info + timeline */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <h2 className="font-bold text-lg">{task?.title}</h2>
            <p className="text-gray-400 text-sm mt-1">{task?.description}</p>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-xs text-gray-500 capitalize">{task?.task_type} pipeline</span>
              <span className={`text-sm font-bold uppercase ${STATUS_COLOR[task?.status ?? ""] ?? "text-gray-400"}`}>
                {task?.status?.replace(/_/g, " ")}
              </span>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wide">Pipeline Steps</h3>
            {displaySteps.length > 0
              ? <ApprovalTimeline steps={displaySteps} />
              : <p className="text-gray-500 text-sm">Pipeline starting…</p>
            }
          </div>
        </div>

        {/* Right: agent outputs */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Agent Outputs</h3>
          {(approvals ?? []).filter((a) => a.output).map((a) => (
            <AgentOutputCard key={a.id} role={a.agent_role} output={a.output} verdict={a.verdict} />
          ))}
          {(!approvals || approvals.filter((a) => a.output).length === 0) && (
            <p className="text-gray-500 text-sm">Waiting for agents to start…</p>
          )}
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/TaskDetail.tsx
git commit -m "feat: TaskDetail page — split view, live timeline + agent outputs"
```

---

## Task 8: OrgChart + App Router + Main

**Files:**
- Create: `frontend/src/components/OrgChart.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write src/components/OrgChart.tsx**

```tsx
const LEVELS = [
  { level: 0, nodes: [{ icon: "👑", title: "Owner — You", sub: "Final Authority", color: "border-yellow-400" }] },
  { level: 1, nodes: [{ icon: "🧠", title: "CTO Agent", sub: "nemotron-3-super-120b", color: "border-purple-400" }] },
  { level: 2, nodes: [
    { icon: "⚡", title: "Senior Lead", sub: "kimi-k2.6", color: "border-blue-400" },
    { icon: "📋", title: "Product Manager", sub: "minimax-m2.7", color: "border-blue-400" },
  ]},
  { level: 3, nodes: [
    { icon: "🖥️", title: "Frontend Dev", sub: "deepseek-v4-flash", color: "border-nvidia-green" },
    { icon: "🗄️", title: "Backend Dev", sub: "deepseek-v4-pro", color: "border-nvidia-green" },
    { icon: "🔗", title: "API Engineer", sub: "glm-5.1", color: "border-nvidia-green" },
    { icon: "☁️", title: "DevOps", sub: "mistral-medium-3.5", color: "border-nvidia-green" },
  ]},
  { level: 4, nodes: [
    { icon: "🧪", title: "QA Engineer", sub: "mistral-small-4-119b", color: "border-orange-400" },
    { icon: "🛡️", title: "Safety Reviewer", sub: "nemotron-content-safety", color: "border-orange-400" },
    { icon: "🔍", title: "Data Extractor", sub: "nemotron-ocr-v1", color: "border-orange-400" },
    { icon: "📈", title: "RAG Search", sub: "llama-nemotron-rerank", color: "border-orange-400" },
  ]},
]

export default function OrgChart() {
  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h3 className="text-center font-bold text-nvidia-green mb-6">🏢 AI Office Hierarchy</h3>
      <div className="space-y-4">
        {LEVELS.map(({ level, nodes }) => (
          <div key={level}>
            <p className="text-xs text-gray-500 text-center mb-2">Level {level}</p>
            <div className="flex flex-wrap justify-center gap-3">
              {nodes.map((n) => (
                <div key={n.title} className={`bg-gray-800 border ${n.color} rounded-xl p-3 text-center min-w-[120px]`}>
                  <p className="text-2xl">{n.icon}</p>
                  <p className="text-white text-xs font-semibold mt-1">{n.title}</p>
                  <p className="text-gray-500 text-xs mt-0.5">{n.sub}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Write src/App.tsx**

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom"
import ProtectedRoute from "./components/ProtectedRoute"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import TaskCreate from "./pages/TaskCreate"
import TaskDetail from "./pages/TaskDetail"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/tasks/new" element={<ProtectedRoute><TaskCreate /></ProtectedRoute>} />
        <Route path="/tasks/:taskId" element={<ProtectedRoute><TaskDetail /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 3: Write src/main.tsx**

```tsx
import React from "react"
import ReactDOM from "react-dom/client"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import App from "./App"
import "./index.css"

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 10_000, retry: 1 } }
})

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
)
```

- [ ] **Step 4: Run full test suite**

```bash
npx vitest run
# Expected: all PASSED
```

- [ ] **Step 5: Build for production**

```bash
npm run build
# Expected: dist/ folder created, no TS errors
```

- [ ] **Step 6: Write Dockerfile**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 7: Write nginx-spa.conf (SPA fallback)**

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;
  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: OrgChart, App router, React root, production Dockerfile"
```

---

## Chunk 4 Complete

All tasks done when:
- `npx vitest run` → all green
- `npm run build` → no TS errors, dist/ created
- Login → Dashboard → New Task → TaskDetail flow works end-to-end
- WebSocket timeline updates live as pipeline runs

**Next:** Chunk 5 — Infrastructure (Docker Compose, Nginx, CI/CD, monitoring)
