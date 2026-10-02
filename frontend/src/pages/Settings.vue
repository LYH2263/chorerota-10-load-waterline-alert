<template>
  <div>
    <h1 class="brand">设置</h1>
    <label>家庭名 <input v-model="household" /></label>
    <label>
      负荷水位（成员周权重之和超过它即告警，须为正数）
      <input type="number" step="any" v-model="waterline" placeholder="未设置" />
    </label>
    <button @click="save">保存</button>
    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="okMsg" class="muted" style="margin-top:8px">{{ okMsg }}</p>
    <p class="muted" style="margin-top:16px">健康检查：{{ health }}</p>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const household = ref('')
const waterline = ref('')
const health = ref('')
const err = ref('')
const okMsg = ref('')
async function load() {
  const s = await api('/settings'); household.value = s.household || ''
  waterline.value = s.load_waterline ?? ''
  const h = await api('/health'); health.value = JSON.stringify(h)
}
async function save() {
  err.value = ''; okMsg.value = ''
  const w = String(waterline.value).trim()
  if (w !== '' && (!Number.isFinite(Number(w)) || Number(w) <= 0)) {
    err.value = '水位必须是大于 0 的数字'
    return
  }
  const body = { household: household.value }
  if (w !== '') body.load_waterline = w
  try {
    await api('/settings', { method: 'PUT', body: JSON.stringify(body) })
    okMsg.value = '已保存；水位只影响之后生成的周表，不会改动已出的告警单。'
    await load()
  } catch (e) { err.value = e.message }
}
onMounted(load)
</script>
