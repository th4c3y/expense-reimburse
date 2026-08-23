<template>
  <div class="page-container">
    <el-row :gutter="16">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ c.label }}</div>
          <div class="stat-value" :style="{ color: c.color }">{{ c.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card>
          <div class="card-title">近 6 个月报销趋势</div>
          <div ref="trendRef" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <div class="card-title">报销类别分布</div>
          <div ref="catRef" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top:16px">
      <el-col :span="24">
        <el-card>
          <div class="card-title">部门报销金额</div>
          <div ref="deptRef" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { statsOverview, statsTrend, statsByCategory, statsByDepartment } from '../api'

const cards = ref([])
const trendRef = ref(null)
const catRef = ref(null)
const deptRef = ref(null)

async function loadOverview() {
  const res = await statsOverview()
  const d = res.data
  cards.value = [
    { label: '报销单总数', value: d.total_sheets, color: '#2d6cdf' },
    { label: '待审批', value: d.pending, color: '#e6a23c' },
    { label: '已通过', value: d.approved, color: '#67c23a' },
    { label: '已付款金额(¥)', value: d.paid_amount.toFixed(2), color: '#f56c6c' }
  ]
}

function renderTrend() {
  statsTrend().then((res) => {
    const data = res.data
    const chart = echarts.init(trendRef.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: data.map((i) => i.month) },
      yAxis: { type: 'value' },
      series: [{ name: '金额', type: 'line', smooth: true, data: data.map((i) => i.amount), areaStyle: {} }]
    })
  })
}

function renderCategory() {
  statsByCategory().then((res) => {
    const data = res.data
    const chart = echarts.init(catRef.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        name: '类别分布', type: 'pie', radius: ['40%', '70%'],
        data: data.map((i) => ({ name: i.name, value: i.amount }))
      }]
    })
  })
}

function renderDept() {
  statsByDepartment().then((res) => {
    const data = res.data
    const chart = echarts.init(deptRef.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: data.map((i) => i.name) },
      yAxis: { type: 'value' },
      series: [{ name: '金额', type: 'bar', data: data.map((i) => i.amount), itemStyle: { color: '#2d6cdf' } }]
    })
  })
}

onMounted(async () => {
  await loadOverview()
  await nextTick()
  renderTrend()
  renderCategory()
  renderDept()
})
</script>

<style scoped>
.stat-card { text-align: center; }
.stat-label { color: #909399; font-size: 14px; }
.stat-value { font-size: 28px; font-weight: 700; margin-top: 8px; }
</style>
