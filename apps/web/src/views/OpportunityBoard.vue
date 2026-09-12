<script setup lang="ts">
import { useResearchStore } from '@/stores/research'

const store = useResearchStore()

const levelColor = (level: string) => {
  switch (level) {
    case 'S': return '#f56c6c'
    case 'A': return '#e6a23c'
    case 'B': return '#409eff'
    default: return '#909399'
  }
}
</script>

<template>
  <div class="board-page">
    <div v-if="store.opportunities.length === 0" class="empty-board">
      <div class="empty-card">
        <p>还没有研究结果</p>
        <router-link to="/">前往研究页面开始 →</router-link>
      </div>
    </div>

    <div v-else>
      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-label">研究方向</span>
          <span class="stat-value">{{ store.stats.query_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">原始候选</span>
          <span class="stat-value">{{ store.stats.candidate_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">去重后</span>
          <span class="stat-value">{{ store.stats.scored_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">高潜客户</span>
          <span class="stat-value">{{ store.opportunities.length }}</span>
        </div>
      </div>

      <!-- Opportunity Cards -->
      <div class="opportunities-list">
        <div
          v-for="(opp, idx) in store.opportunities"
          :key="opp.id"
          class="opportunity-card"
        >
          <div class="card-header">
            <div class="rank">#{{ idx + 1 }}</div>
            <div class="company-info">
              <h3>{{ opp.account_name }}</h3>
              <a :href="opp.profile_url" target="_blank" class="profile-link">
                {{ opp.profile_url }}
              </a>
            </div>
            <div class="score-badge" :style="{ backgroundColor: levelColor(opp.level) }">
              <span class="total-score">{{ opp.total_score }}</span>
              <span class="level">Lvl {{ opp.level }}</span>
            </div>
          </div>

          <div class="card-body">
            <div class="score-reason">
              <strong>为什么推荐：</strong>{{ opp.buyer_score.score_reason }}
            </div>

            <div class="score-dimensions">
              <div class="dim">
                <span class="dim-label">ICP</span>
                <span class="dim-value">{{ opp.buyer_score.icp_fit }}/25</span>
              </div>
              <div class="dim">
                <span class="dim-label">痛点</span>
                <span class="dim-value">{{ opp.buyer_score.pain_intensity }}/20</span>
              </div>
              <div class="dim">
                <span class="dim-label">频次</span>
                <span class="dim-value">{{ opp.buyer_score.usage_frequency }}/15</span>
              </div>
              <div class="dim">
                <span class="dim-label">投入</span>
                <span class="dim-value">{{ opp.buyer_score.existing_spend }}/15</span>
              </div>
            </div>

            <div class="hypothesis">
              <strong>价值假设：</strong>{{ opp.value_hypothesis }}
            </div>

            <div v-if="opp.evidence.length > 0" class="evidence-section">
              <strong>主要证据：</strong>
              <ul>
                <li v-for="(ev, i) in opp.evidence" :key="i">
                  {{ ev.evidence_text }}
                </li>
              </ul>
            </div>

            <div class="risk-section">
              <strong>主要风险：</strong>{{ opp.buyer_score.risk }}
            </div>

            <div class="action-section">
              <el-tag type="primary" size="small">{{ opp.recommended_action }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-board {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.empty-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.empty-card p {
  color: #909399;
  margin-bottom: 12px;
}

.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.opportunities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.opportunity-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}

.opportunity-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  gap: 16px;
}

.rank {
  font-size: 20px;
  font-weight: 700;
  color: #c0c4cc;
  width: 40px;
  text-align: center;
}

.company-info {
  flex: 1;
}

.company-info h3 {
  font-size: 16px;
  margin-bottom: 4px;
}

.profile-link {
  font-size: 12px;
  color: #909399;
  word-break: break-all;
}

.score-badge {
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  text-align: center;
  min-width: 70px;
}

.total-score {
  display: block;
  font-size: 22px;
  font-weight: 700;
}

.level {
  font-size: 11px;
  opacity: 0.9;
}

.card-body {
  padding: 20px;
}

.score-reason,
.hypothesis,
.risk-section {
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.6;
}

.score-dimensions {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.dim {
  background: #f5f7fa;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.dim-label {
  color: #909399;
  margin-right: 4px;
}

.dim-value {
  font-weight: 600;
}

.evidence-section {
  margin-bottom: 12px;
}

.evidence-section ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.evidence-section li {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.5;
}

.action-section {
  margin-top: 12px;
}
</style>
