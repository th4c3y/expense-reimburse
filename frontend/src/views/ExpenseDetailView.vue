<template>
  <div class="page-container" v-loading="loading">
    <el-card v-if="sheet">
      <div class="card-title">
        报销单详情
        <el-tag :type="statusType(sheet.status)" style="margin-left:10px">{{ statusLabel(sheet.status) }}</el-tag>
      </div>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="单据编号">{{ sheet.sheet_no }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ sheet.applicant_name }}</el-descriptions-item>
        <el-descriptions-item label="所属部门">{{ sheet.department_name }}</el-descriptions-item>
        <el-descriptions-item label="报销标题">{{ sheet.title }}</el-descriptions-item>
        <el-descriptions-item label="总金额">¥{{ Number(sheet.total_amount).toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ sheet.created_at }}</el-descriptions-item>
        <el-descriptions-item label="报销事由" :span="2">{{ sheet.reason || '—' }}</el-descriptions-item>
        <el-descriptions-item v-if="sheet.reject_reason" label="驳回原因" :span="2">
          <span style="color:#f56c6c">{{ sheet.reject_reason }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>报销明细</el-divider>
      <el-table :data="sheet.items" border>
        <el-table-column prop="category_name" label="类别" width="140" />
        <el-table-column label="金额(¥)" width="120">
          <template #default="{ row }">¥{{ Number(row.amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="occur_date" label="发生日期" width="130" />
        <el-table-column prop="description" label="说明" />
        <el-table-column prop="invoice_no" label="发票号" width="150" />
      </el-table>

      <el-divider>审批流程</el-divider>
      <el-timeline>
        <el-timeline-item
          v-for="r in records"
          :key="r.id"
          :timestamp="r.created_at"
          :type="actionType(r.action)"
        >
          <b>{{ r.approver_name }}</b> · {{ actionLabel(r.action) }}
          <span v-if="r.comment" style="color:#606266">（{{ r.comment }}）</span>
        </el-timeline-item>
        <el-timeline-item v-if="!records.length" timestamp="—">暂无审批记录</el-timeline-item>
      </el-timeline>

      <div style="margin-top:20px">
        <el-button @click="$router.back()">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getExpense, approvalRecords } from '../api'

const route = useRoute()
const sheet = ref(null)
const records = ref([])
const loading = ref(false)

const statusMap = {
  draft: { label: '草稿', type: 'info' },
  pending: { label: '审批中', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  paid: { label: '已付款', type: 'primary' }
}
const statusLabel = (s) => statusMap[s]?.label || s
const statusType = (s) => statusMap[s]?.type || 'info'

const actionMap = {
  submit: { label: '提交', type: 'primary' },
  approve: { label: '审批通过', type: 'success' },
  reject: { label: '驳回', type: 'danger' },
  transfer: { label: '转交', type: 'warning' },
  comment: { label: '评论', type: 'info' }
}
const actionLabel = (a) => actionMap[a]?.label || a
const actionType = (a) => actionMap[a]?.type || 'info'

async function load() {
  loading.value = true
  try {
    const res = await getExpense(route.params.id)
    sheet.value = res.data
    const recRes = await approvalRecords(route.params.id)
    records.value = recRes.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
