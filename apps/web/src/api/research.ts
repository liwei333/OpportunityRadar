import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export interface CreateTaskResponse {
  task_id: string
  status: string
}

export interface TaskRunResponse {
  task_id: string
  status: string
  queries_generated: number
  candidates_collected: number
  candidates_after_dedup: number
  opportunities_found: number
  top_score: number
}

export interface Evidence {
  evidence_type: string
  evidence_text: string
  source_url: string
  confidence: number
}

export interface BuyerScore {
  icp_fit: number
  pain_intensity: number
  usage_frequency: number
  existing_spend: number
  customer_value: number
  buy_vs_build: number
  reachability: number
  total: number
  score_reason: string
  risk: string
  confidence: number
}

export interface Opportunity {
  id: string
  candidate_id: string
  account_name: string
  profile_url: string
  level: string
  total_score: number
  buyer_score: BuyerScore
  value_hypothesis: string
  recommended_action: string
  evidence: Evidence[]
}

export interface OpportunitiesResponse {
  task_id: string
  total: number
  opportunities: Opportunity[]
}

export async function createTask(goal: string): Promise<CreateTaskResponse> {
  const res = await http.post('/research/tasks', { goal })
  return res.data
}

export async function runTask(taskId: string): Promise<TaskRunResponse> {
  const res = await http.post(`/research/tasks/${taskId}/run`)
  return res.data
}

export async function getOpportunities(taskId: string): Promise<OpportunitiesResponse> {
  const res = await http.get(`/research/tasks/${taskId}/opportunities`)
  return res.data
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await http.get('/health')
  return res.data
}
