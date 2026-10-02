<template>
  <div>
    <h1 class="brand">告警详情</h1>
    <p v-if="err" class="err">{{ err }}</p>
    <article v-if="a" class="week-card" style="max-width:480px">
      <header>告警单 #{{ a.id }}</header>
      <ul class="list">
        <li>成员：<b>{{ a.member_name }}</b>（#{{ a.member_id }}）</li>
        <li>周编号：{{ a.week_label || '第#' + a.week_id + '周' }}（week_id {{ a.week_id }}）</li>
        <li>周权重负荷：<b class="err">{{ a.load }}</b></li>
        <li>当时水位：{{ a.waterline }}</li>
        <li>超出量：{{ a.load - a.waterline }}</li>
        <li>建单时间：{{ a.created_at }}</li>
      </ul>
    </article>
    <p style="margin-top:16px">
      <router-link to="/alerts"><button class="ghost">← 返回告警列表</button></router-link>
    </p>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
const route = useRoute()
const a = ref(null)
const err = ref('')
onMounted(async () => {
  try { a.value = await api('/load-alerts/' + route.params.id) }
  catch (e) { err.value = e.message }
})
</script>
