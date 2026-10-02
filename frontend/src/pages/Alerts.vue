<template>
  <div>
    <h1 class="brand">负荷告警</h1>
    <p class="muted">
      告警单在周表生成时定格：成员、周权重负荷、当时水位、周编号。
      之后改水位或任务权重不回刷旧单；重新生成同一周则整周覆盖。
    </p>
    <div style="display:flex;gap:8px;margin:12px 0">
      <button class="ghost" :class="{ active: scope === 'all' }" @click="setScope('all')">全部周</button>
      <button v-if="weekFilter" class="ghost" :class="{ active: scope === 'week' }" @click="setScope('week')">
        仅本周（#{{ weekFilter }}）
      </button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <ul class="list">
      <li v-for="a in rows" :key="a.id">
        <router-link :to="'/alerts/' + a.id" class="alert-row">
          <span class="chip coral">{{ a.member_name }}</span>
          <span>负荷 <b>{{ a.load }}</b> / 水位 {{ a.waterline }}</span>
          <span class="chip">{{ a.week_label || ('第#' + a.week_id + '周') }}</span>
        </router-link>
      </li>
    </ul>
    <p v-if="!rows.length && !err" class="muted">暂无超线告警单。</p>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
const route = useRoute()
const router = useRouter()
const rows = ref([])
const err = ref('')
const weekFilter = ref(route.query.week ? Number(route.query.week) : null)
const scope = ref(weekFilter.value ? 'week' : 'all')
async function load() {
  err.value = ''
  try {
    const q = scope.value === 'week' && weekFilter.value ? '?week_id=' + weekFilter.value : ''
    rows.value = await api('/load-alerts' + q)
  } catch (e) { err.value = e.message }
}
function setScope(s) {
  scope.value = s
  router.replace({ query: s === 'week' ? { week: weekFilter.value } : {} })
  load()
}
onMounted(load)
</script>
