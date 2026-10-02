<template>
  <div>
    <h1 class="brand">本周看板</h1>
    <p class="muted">周卡片网格 · round-robin 落位后可去「对调」申请交换</p>
    <div style="display:flex;gap:8px;margin:12px 0">
      <button @click="generate">生成周表</button>
      <button class="ghost" @click="load">刷新</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="alerts.length" style="margin:0 0 8px">
      <router-link class="chip coral" :to="'/alerts?week_id=' + weekId">负荷告警 {{ alerts.length }} 单 →</router-link>
    </p>
    <div class="week-grid">
      <article v-for="d in days" :key="d" class="week-card">
        <header>Day {{ d }}</header>
        <div v-for="a in byDay(d)" :key="a.id">
          <span class="chip">{{ a.task_title }}</span>
          <span class="chip coral">{{ a.member_name }}</span>
        </div>
        <p v-if="!byDay(d).length" class="muted">空</p>
      </article>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const assigns = ref([])
const alerts = ref([])
const days = [0,1,2,3,4,5,6]
const err = ref('')
const weekId = 1
function byDay(d) { return assigns.value.filter(a => a.day === d) }
async function load() {
  err.value = ''
  try {
    const b = await api('/weeks/' + weekId + '/board')
    assigns.value = b.assignments || []
    alerts.value = await api('/load-alerts?week_id=' + weekId)
  } catch (e) { err.value = e.message }
}
async function generate() {
  err.value = ''
  try { await api('/weeks/' + weekId + '/generate', { method: 'POST', body: '{}' }); await load() }
  catch (e) { err.value = e.message }
}
onMounted(load)
</script>
