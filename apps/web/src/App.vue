<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-inner">
        <h1 class="logo">🔭 OpportunityRadar</h1>
        <nav class="nav-links">
          <RouterLink to="/">研究</RouterLink>
          <RouterLink to="/progress">进度</RouterLink>
          <RouterLink to="/board">潜客看板</RouterLink>
        </nav>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.app-header {
  background: #1a1a2e;
  color: white;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #409eff;
}

.app-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
</style>
