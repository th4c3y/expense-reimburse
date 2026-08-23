<template>
  <div class="page-container">
    <el-card>
      <div class="toolbar">
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:140px" @change="load">
          <el-option label="草稿" value="draft" />
          <el-option label="审批中" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
          <el-option label="已付款" value="paid" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="标题关键字" style="width:200px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="$router.push('/expense-create')">新建报销</el-button>
      </div>

      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="sheet_no" label="单号" width="150" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="total_amount" label="金额(¥)" width="120">
          <template #default="{ row }">{{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.id)">查看</el-button>
            <el-button
              v-if="['draft', 'rejected'].includes(row.status)"
              link type="warning"
              @click="$router.push(`/expense-edit/${row.id}`)"
            >编辑</el-button>
            <el-button
              v-if="['draft', 'rejected'].includes(row.status)"
              link type="success"
              @click="submit(row.id)"
            >提交</el-button>
            <el-button
              v-if="['draft', 'rejected'].includes(row.status)"
              link type="danger"
              @click="remove(row.id)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="prev, pager, next, total"
        :total="total"
        :current-page="page"
        @current-change="(p) => { page = p; load() }"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listExpenses, deleteExpense, submitExpense } from '../api'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filters = ref({ status: '', keyword: '' })

const statusMap = {
  draft: { label: '草稿', type: 'info' },
  pending: { label: '审批中', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  paid: { label: '已付款', type: 'primary' }
}
const statusLabel = (s) => statusMap[s]?.label || s
const statusType = (s) => statusMap[s]?.type || 'info'

async function load() {
  loading.value = true
  try {
    const res = await listExpenses({
      page: page.value,
      per_page: 15,
      status: filters.value.status,
      keyword: filters.value.keyword
    })
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function goDetail(id) {
  router.push(`/expense-detail/${id}`)
}

async function submit(id) {
  await ElMessageBox.confirm('确认提交该报销单进入审批流程？', '提示', { type: 'warning' })
  await submitExpense(id)
  ElMessage.success('提交成功')
  load()
}

async function remove(id) {
  await ElMessageBox.confirm('确认删除该报销单？', '提示', { type: 'warning' })
  await deleteExpense(id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.pager { margin-top: 16px; justify-content: flex-end; display: flex; }
</style>
