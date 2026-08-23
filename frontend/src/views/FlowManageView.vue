<template>
  <div class="page-container">
    <el-card>
      <div class="toolbar">
        <el-button type="success" @click="openCreate">新增审批流</el-button>
        <el-tag type="info">审批流按"金额区间 + 部门范围"自动匹配报销单，优先级高者优先</el-tag>
      </div>

      <el-collapse v-model="activeNames">
        <el-collapse-item v-for="f in list" :key="f.id" :name="f.id">
          <template #title>
            <span style="font-weight:600">{{ f.name }}</span>
            <el-tag size="small" style="margin-left:8px" :type="f.is_default ? 'success' : 'info'">
              {{ f.is_default ? '默认流' : '条件流' }}
            </el-tag>
            <span style="margin-left:8px;color:#909399">
              金额 {{ f.min_amount }} ~ {{ f.max_amount || '∞' }} / 优先级 {{ f.priority }}
            </span>
          </template>

          <el-table :data="f.nodes" border size="small">
            <el-table-column label="顺序" width="60" prop="order_no" />
            <el-table-column label="节点名称" prop="name" />
            <el-table-column label="审批人类型" width="140">
              <template #default="{ row }">{{ typeLabel(row.approver_type) }}</template>
            </el-table-column>
            <el-table-column label="审批人值" prop="approver_value" />
          </el-table>

          <div class="node-actions">
            <el-button link type="primary" @click="openEdit(f)">编辑</el-button>
            <el-button link type="danger" @click="remove(f.id)">删除</el-button>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 审批流编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑审批流' : '新增审批流'" width="680px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="优先级"><el-input-number v-model="form.priority" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="最低金额"><el-input-number v-model="form.min_amount" :min="0" :precision="2" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="最高金额"><el-input-number v-model="form.max_amount" :min="0" :precision="2" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="部门范围"><el-input v-model="form.department_scope" placeholder="逗号分隔部门ID,留空为全部" /></el-form-item>
        <el-form-item label="设为默认"><el-switch v-model="form.is_default" :active-value="1" :inactive-value="0" /></el-form-item>

        <el-divider>审批节点</el-divider>
        <div v-for="(n, idx) in form.nodes" :key="idx" class="node-row">
          <span class="node-idx">{{ idx + 1 }}.</span>
          <el-input v-model="n.name" placeholder="节点名" style="width:140px" />
          <el-select v-model="n.approver_type" style="width:150px">
            <el-option label="按角色" value="role" />
            <el-option label="部门经理" value="dept_manager" />
            <el-option label="指定用户" value="user" />
            <el-option label="财务总监" value="finance_director" />
          </el-select>
          <el-input v-model="n.approver_value" placeholder="角色名/用户ID" style="width:140px" />
          <el-button link type="danger" @click="form.nodes.splice(idx, 1)">移除</el-button>
        </div>
        <el-button type="dashed" @click="addNode">+ 添加节点</el-button>
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
import { listFlows, createFlow, updateFlow, deleteFlow } from '../api'

const list = ref([])
const activeNames = ref([])
const dialogVisible = ref(false)
const form = ref({ nodes: [] })

const typeMap = {
  role: '按角色', dept_manager: '部门经理', user: '指定用户', finance_director: '财务总监'
}
const typeLabel = (t) => typeMap[t] || t

async function load() {
  const res = await listFlows()
  list.value = res.data
  activeNames.value = list.value.map((f) => f.id)
}

function openCreate() {
  form.value = {
    name: '', priority: 0, min_amount: 0, max_amount: null,
    department_scope: '', is_default: 0, nodes: [
      { name: '节点1', approver_type: 'dept_manager', approver_value: null },
      { name: '节点2', approver_type: 'role', approver_value: 'finance' }
    ]
  }
  dialogVisible.value = true
}
function openEdit(f) {
  form.value = JSON.parse(JSON.stringify(f))
  dialogVisible.value = true
}
function addNode() {
  form.value.nodes.push({
    name: `节点${form.value.nodes.length + 1}`,
    approver_type: 'role', approver_value: null
  })
}
async function submit() {
  if (!form.value.name) {
    ElMessage.warning('请填写审批流名称')
    return
  }
  if (form.value.id) {
    await updateFlow(form.value.id, form.value)
    ElMessage.success('更新成功')
  } else {
    await createFlow(form.value)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}
async function remove(id) {
  await ElMessageBox.confirm('确认删除该审批流？', '提示', { type: 'warning' })
  await deleteFlow(id)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; flex-wrap: wrap; }
.node-actions { margin-top: 10px; }
.node-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.node-idx { width: 20px; color: #909399; }
</style>
