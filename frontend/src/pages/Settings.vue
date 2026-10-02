<template>
  <div>
    <h1 class="brand">设置</h1>
    <label>家庭名 <input v-model="household" /></label>
    <label>负荷水位（&gt; 0 的整数）<input type="number" v-model.number="waterline" /></label>
    <button @click="save">保存</button>
    <p v-if="err" class="err">{{ err }}</p>
    <p class="muted" style="margin-top:16px">健康检查：{{ health }}</p>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const household = ref('')
const waterline = ref(null)
const health = ref('')
const err = ref('')
async function load() {
  const s = await api('/settings')
  household.value = s.household || ''
  waterline.value = s.load_waterline != null ? Number(s.load_waterline) : null
  const h = await api('/health'); health.value = JSON.stringify(h)
}
async function save() {
  err.value = ''
  const body = { household: household.value }
  if (waterline.value != null && waterline.value !== '') body.load_waterline = waterline.value
  try {
    await api('/settings', { method: 'PUT', body: JSON.stringify(body) })
  } catch (e) { err.value = e.message }
}
onMounted(load)
</script>
