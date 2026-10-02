<template>
  <div>
    <!-- 列表 -->
    <template v-if="!alertId">
      <h1 class="brand">负荷告警</h1>
      <p class="muted">周表生成时按成员汇总任务权重，负荷 &gt; 水位即建单；单据数字为出单时快照，不随后续修改回刷。</p>
      <p v-if="err" class="err">{{ err }}</p>
      <p v-if="!rows.length && !err" class="muted">暂无告警单</p>
      <ul class="list">
        <li v-for="a in rows" :key="a.id" class="alert-row" @click="open(a.id)">
          <span class="chip">第{{ a.week_id }}周<template v-if="a.week_label">（{{ a.week_label }}）</template></span>
          <span class="chip">{{ a.member_name }}</span>
          <span class="chip coral">负荷 {{ a.load }} / 水位 {{ a.waterline }}</span>
        </li>
      </ul>
    </template>

    <!-- 详情 -->
    <template v-else>
      <h1 class="brand">告警详情 #{{ alertId }}</h1>
      <p v-if="err" class="err">{{ err }}</p>
      <div v-if="detail" class="week-card">
        <p><span class="muted">周编号：</span>第{{ detail.week_id }} 周<template v-if="detail.week_label">（{{ detail.week_label }}）</template></p>
        <p><span class="muted">成员：</span>{{ detail.member_name }}（#{{ detail.member_id }}）</p>
        <p><span class="chip coral">负荷 {{ detail.load }}</span> 超出水位 <span class="chip">{{ detail.waterline }}</span></p>
      </div>
      <p style="margin-top:12px"><router-link class="chip" to="/alerts">← 返回告警列表</router-link></p>
    </template>
  </div>
</template>
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
const route = useRoute()
const router = useRouter()
const rows = ref([])
const detail = ref(null)
const err = ref('')
const alertId = computed(() => (route.params.id ? Number(route.params.id) : null))
function open(id) { router.push('/alerts/' + id) }
async function load() {
  err.value = ''
  detail.value = null
  rows.value = []
  try {
    if (alertId.value) {
      detail.value = await api('/load-alerts/' + alertId.value)
    } else {
      const q = route.query.week_id ? '?week_id=' + encodeURIComponent(route.query.week_id) : ''
      rows.value = await api('/load-alerts' + q)
    }
  } catch (e) { err.value = e.message }
}
watch(alertId, load)
onMounted(load)
</script>
<style scoped>
.alert-row { cursor: pointer; }
</style>
