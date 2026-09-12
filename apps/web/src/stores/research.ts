import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createTask, runTask, getOpportunities } from '@/api/research'

export interface Opportunity {
  id: string
  account_name: string
  profile_url: string
  level: string
  total_score: number
  buyer_score: {
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
  value_hypothesis: string
  recommended_action: string
  evidence: Array<{
    evidence_type: string
    evidence_text: string
    source_url: string
    confidence: number
  }>
}

export interface TaskStats {
  query_count: number
  candidate_count: number
  scored_count: number
  top_score: number
}

export const useResearchStore = defineStore('research', () => {
  const taskId = ref<string | null>(null)
  const taskStatus = ref<string>('IDLE')
  const opportunities = ref<Opportunity[]>([])
  const stats = ref<TaskStats>({
    query_count: 0,
    candidate_count: 0,
    scored_count: 0,
    top_score: 0,
  })
  const isRunning = ref(false)

  async function startResearch(goal: string) {
    isRunning.value = true
    taskStatus.value = 'CREATING'

    try {
      // Create task
      const createRes = await createTask(goal)
      taskId.value = createRes.task_id
      taskStatus.value = 'PLANNING'

      // Run task
      const runRes = await runTask(createRes.task_id)
      taskStatus.value = 'COMPLETED'

      // Update stats
      stats.value = {
        query_count: runRes.queries_generated,
        candidate_count: runRes.candidates_collected,
        scored_count: runRes.candidates_after_dedup,
        top_score: runRes.top_score,
      }

      // Get opportunities
      await fetchOpportunities()
    } catch (error) {
      taskStatus.value = 'FAILED'
      throw error
    } finally {
      isRunning.value = false
    }
  }

  async function fetchOpportunities() {
    if (!taskId.value) return
    const res = await getOpportunities(taskId.value)
    opportunities.value = res.opportunities
  }

  function reset() {
    taskId.value = null
    taskStatus.value = 'IDLE'
    opportunities.value = []
    stats.value = { query_count: 0, candidate_count: 0, scored_count: 0, top_score: 0 }
    isRunning.value = false
  }

  return {
    taskId,
    taskStatus,
    opportunities,
    stats,
    isRunning,
    startResearch,
    fetchOpportunities,
    reset,
  }
})
