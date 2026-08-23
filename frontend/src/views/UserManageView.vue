<template>
  <div class="page-container">
    <el-card>
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="用户名/姓名" style="width:200px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">新增用户</el-button>
      </div>

      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="username" label="登录名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag>{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_id" label="部门ID" width="90" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="pager" background layout="prev, pager, next, total"
        :total="total" :current-page="page"
        @current-change="(p) => { page = p; load() }" />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新增用户'" width="460px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="登录名"><el-input v-model="form.username" :disabled="!!form.id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" /></el-form-item>
        <el-form-item label="密码" v-if="!form.id"><el-input v-model="form.password" placeholder="默认123456" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="部门经理" value="manager" />
            <el-option label="财务" value="finance" />
            <el-option label="员工" value="employee" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门ID"><el-input-number v-model="form.department_id" :min="0" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="审批额度"><el-input-number v-model="form.approval_limit" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser } from '../api'

const list = ref([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({})

const roleMap = { admin: '管理员', manager: '部门经理', finance: '财务', employee: '员工' }
const roleLabel = (r) => roleMap[r] || r

async function load() {
  loading.value = true
  try {
    const res = await listUsers({ page: page.value, per_page: 20, keyword: keyword.value })
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { role: 'employee', status: 1, department_id: 0, approval_limit: 0, password: '123456' }
  dialogVisible.value = true
}
function openEdit(row) {
  form.value = { ...row }
  dialogVisible.value = true
}
async function submit() {
  if (form.value.id) {
    await updateUser(form.value.id, form.value)
    ElMessage.success('更新成功')
  } else {
    await createUser(form.value)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}
async function remove(id) {
  await ElMessageBox.confirm('确认删除该用户？', '提示', { type: 'warning' })
  await deleteUser(id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
