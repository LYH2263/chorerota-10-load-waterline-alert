import { createRouter, createWebHistory } from 'vue-router'
import Board from './pages/Board.vue'
import Members from './pages/Members.vue'
import Tasks from './pages/Tasks.vue'
import Swaps from './pages/Swaps.vue'
import Alerts from './pages/Alerts.vue'
import AlertDetail from './pages/AlertDetail.vue'
import Settings from './pages/Settings.vue'
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Board },
    { path: '/members', component: Members },
    { path: '/tasks', component: Tasks },
    { path: '/swaps', component: Swaps },
    { path: '/alerts', component: Alerts },
    { path: '/alerts/:id', component: AlertDetail },
    { path: '/settings', component: Settings },
  ],
})
