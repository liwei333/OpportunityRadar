<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useResearchStore } from '@/stores/research'

const router = useRouter()
const store = useResearchStore()

const goal = ref('帮我寻找最可能购买 OpportunityRadar 的客户，优先寻找服务 B2B、制造业、工业品企业的短视频代运营和企业获客公司。')

async function handleStart() {
  if (goal.value.trim().length < 5) {
    ElMessage.warning('请输入至少5个字符的研究目标')
    return
  }

  try {
    await store.startResearch(goal.value.trim())
    ElMessage.success('研究完成！')
    router.push('/board')
  } catch (error: any) {
    ElMessage.error(`研究失败：${error.message || '未知错误'}`)
  }
}
</script>

<template>
  <div class="research-page">
    <div class="hero-card">
      <h2>今天想研究什么？</h2>
      <p class="subtitle">输入你的商业目标，AI 研究 Agent 将自动完成市场研究、候选筛选和潜客评分。</p>

      <el-input
        v-model="goal"
        type="textarea"
        :rows="4"
        placeholder="例如：帮我寻找最可能购买 OpportunityRadar 的客户……"
        class="goal-input"
      />

      <el-button
        type="primary"
        size="large"
        :loading="store.isRunning"
        @click="handleStart"
        class="start-btn"
      >
        {{ store.isRunning ? '研究中...' : '开始研究' }}
      </el-button>
    </div>

    <div class="info-cards">
      <div class="info-card">
        <div class="info-icon">🎯</div>
        <h3>智能规划</h3>
        <p>Agent 自动识别 ICP，生成多个研究方向和搜索策略</p>
      </div>
      <div class="info-card">
        <div class="info-icon">📊</div>
        <h3>Buyer Score</h3>
        <p>七维评分模型，100分制量化每个客户的购买可能性</p>
      </div>
      <div class="info-card">
        <div class="info-icon">🔍</div>
        <h3>证据驱动</h3>
        <p>每个评分都有可追溯的证据，拒绝黑盒判断</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.research-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.hero-card h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.subtitle {
  color: #909399;
  margin-bottom: 24px;
}

.goal-input {
  margin-bottom: 20px;
  font-size: 14px;
}

.start-btn {
  min-width: 200px;
  height: 44px;
  font-size: 16px;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.info-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.info-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.info-card p {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .info-cards {
    grid-template-columns: 1fr;
  }
}
</style>
