import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'research',
      component: () => import('@/views/ResearchView.vue'),
    },
    {
      path: '/progress',
      name: 'progress',
      component: () => import('@/views/ProgressView.vue'),
    },
    {
      path: '/board',
      name: 'board',
      component: () => import('@/views/OpportunityBoard.vue'),
    },
  ],
})

export default router
