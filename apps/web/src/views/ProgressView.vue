<script setup lang="ts">
import { useResearchStore } from '@/stores/research'

const store = useResearchStore()

interface Step {
  name: string
  label: string
  icon: string
}

const steps: Step[] = [
  { name: 'CREATING', label: '理解需求', icon: '📝' },
  { name: 'PLANNING', label: '生成研究方向', icon: '🧭' },
  { name: 'COLLECTING', label: '收集候选对象', icon: '🔍' },
  { name: 'FILTERING', label: '数据清洗', icon: '🧹' },
  { name: 'SCORING', label: 'Buyer Score', icon: '📊' },
  { name: 'COMPLETED', label: 'Ranking', icon: '🏆' },
]

const statusOrder = ['IDLE', 'CREATING', 'PLANNING', 'COLLECTING', 'FILTERING', 'SCORING', 'COMPLETED', 'FAILED']

function getStepStatus(stepName: Step['name']): 'done' | 'active' | 'pending' {
  const currentIdx = statusOrder.indexOf(store.taskStatus)
  const stepIdx = statusOrder.indexOf(stepName)

  if (store.taskStatus === 'FAILED') return 'pending'
  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) return 'active'
  return 'pending'
}
</script>

<template>
  <div class="progress-page">
    <div class="progress-card">
      <h2>Agent 执行进度</h2>

      <div v-if="store.taskStatus === 'IDLE'" class="empty-state">
        <p>还没有正在执行的研究任务</p>
        <router-link to="/">前往研究页面开始 →</router-link>
      </div>

      <div v-else class="steps">
        <div
          v-for="step in steps"
          :key="step.name"
          class="step-item"
          :class="getStepStatus(step.name)"
        >
          <div class="step-icon">
            <span v-if="getStepStatus(step.name) === 'done'">✓</span>
            <span v-else-if="getStepStatus(step.name) === 'active'" class="pulse">●</span>
            <span v-else>{{ step.icon }}</span>
          </div>
          <div class="step-label">{{ step.label }}</div>
        </div>
      </div>

      <div v-if="store.taskStatus === 'COMPLETED'" class="completed-banner">
        ✅ 研究完成！共发现 {{ store.stats.scored_count }} 个候选，
        <router-link to="/board">查看潜客看板 →</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progress-page {
  display: flex;
  justify-content: center;
}

.progress-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.progress-card h2 {
  text-align: center;
  margin-bottom: 32px;
}

.empty-state {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  transition: all 0.3s;
}

.step-item.done {
  background: #f0f9eb;
  color: #67c23a;
}

.step-item.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}

.step-item.pending {
  color: #c0c4cc;
}

.step-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 16px;
  flex-shrink: 0;
}

.done .step-icon {
  background: #67c23a;
  color: white;
}

.active .step-icon {
  background: #409eff;
  color: white;
}

.pending .step-icon {
  background: #ebeef5;
}

.pulse {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.step-label {
  font-size: 15px;
}

.completed-banner {
  margin-top: 24px;
  padding: 16px;
  background: #f0f9eb;
  border-radius: 8px;
  text-align: center;
  color: #67c23a;
}
</style>
