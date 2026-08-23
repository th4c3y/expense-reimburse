<template>
  <div class="page-container">
    <el-card>
      <div class="card-title">审批中心 - 待我审批</div>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="sheet_no" label="单号" width="150" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="applicant_name" label="申请人" width="100" />
        <el-table-column label="金额(¥)" width="120">
          <template #default="{ row }">¥{{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="当前节点" width="110">
          <template #default="{ row }">
            <el-tag>{{ row.current_node === 1 ? '经理审批' : '财务审批' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.id)">查看</el-button>
            <el-button link type="success" @click="approve(row.id)">通过</el-button>
            <el-button link type="danger" @click="reject(row.id)">驳回</el-button>
            <el-button
              v-if="userStore.role === 'finance' && row.current_node === 2"
              link type="warning"
              @click="pay(row.id)"
            >付款</el-button>
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

    <!-- 审批意见对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogAction === 'approve' ? '审批通过' : '驳回'" width="420px">
      <el-input v-model="comment" type="textarea" :rows="3" :placeholder="dialogAction === 'reject' ? '请填写驳回原因（必填）' : '审批意见（选填）'" />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :type="dialogAction === 'approve' ? 'success' : 'danger'" @click="confirmAction">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { pendingList, approveExpense, rejectExpense, payExpense } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

const dialogVisible = ref(false)
const dialogAction = ref('approve')
const currentId = ref(null)
const comment = ref('')

async function load() {
  loading.value = true
  try {
    const res = await pendingList({ page: page.value, per_page: 15 })
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function goDetail(id) {
  router.push(`/expense-detail/${id}`)
}

function approve(id) {
  currentId.value = id
  dialogAction.value = 'approve'
  comment.value = ''
  dialogVisible.value = true
}

function reject(id) {
  currentId.value = id
  dialogAction.value = 'reject'
  comment.value = ''
  dialogVisible.value = true
}

async function confirmAction() {
  if (dialogAction.value === 'reject' && !comment.value.trim()) {
    ElMessage.warning('驳回必须填写原因')
    return
  }
  if (dialogAction.value === 'approve') {
    await approveExpense(currentId.value, { comment: comment.value })
    ElMessage.success('审批通过')
  } else {
    await rejectExpense(currentId.value, { comment: comment.value })
    ElMessage.success('已驳回')
  }
  dialogVisible.value = false
  load()
}

async function pay(id) {
  await ElMessageBox.confirm('确认将该单据标记为已付款？', '提示', { type: 'warning' })
  await payExpense(id)
  ElMessage.success('付款成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
