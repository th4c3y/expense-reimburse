<template>
  <div class="page-container">
    <el-card>
      <div class="toolbar">
        <el-button type="success" @click="openCreate">新增部门</el-button>
      </div>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="部门名称" width="160" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="manager_id" label="负责人ID" width="100" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑部门' : '新增部门'" width="420px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="form.code" :disabled="!!form.id" /></el-form-item>
        <el-form-item label="负责人ID"><el-input-number v-model="form.manager_id" :min="0" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
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
import { listDepartments, createDepartment, updateDepartment, deleteDepartment } from '../api'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({})

async function load() {
  loading.value = true
  try {
    const res = await listDepartments()
    list.value = res.data
  } finally {
    loading.value = false
  }
}
function openCreate() {
  form.value = { manager_id: 0 }
  dialogVisible.value = true
}
function openEdit(row) {
  form.value = { ...row }
  dialogVisible.value = true
}
async function submit() {
  if (form.value.id) {
    await updateDepartment(form.value.id, form.value)
    ElMessage.success('更新成功')
  } else {
    await createDepartment(form.value)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}
async function remove(id) {
  await ElMessageBox.confirm('确认删除该部门？', '提示', { type: 'warning' })
  await deleteDepartment(id)
  ElMessage.success('删除成功')
  load()
}
onMounted(load)
</script>

<style scoped>
.toolbar { margin-bottom: 16px; }
</style>
