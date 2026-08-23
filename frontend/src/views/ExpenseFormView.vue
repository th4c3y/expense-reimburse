<template>
  <div class="page-container">
    <el-card>
      <div class="card-title">{{ isEdit ? '编辑报销单' : '新建报销单' }}</div>
      <el-form :model="form" label-width="90px" style="max-width:900px">
        <el-form-item label="报销标题" required>
          <el-input v-model="form.title" placeholder="如：2026年8月出差报销" />
        </el-form-item>
        <el-form-item label="报销事由">
          <el-input v-model="form.reason" type="textarea" :rows="2" />
        </el-form-item>

        <el-divider>报销明细</el-divider>

        <el-table :data="form.items" border>
          <el-table-column label="费用类别" width="160">
            <template #default="{ row }">
              <el-select v-model="row.category_id" placeholder="选择类别">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="金额(¥)" width="140">
            <template #default="{ row }">
              <el-input-number v-model="row.amount" :min="0" :precision="2" :step="10" style="width:120px" />
            </template>
          </el-table-column>
          <el-table-column label="发生日期" width="160">
            <template #default="{ row }">
              <el-date-picker v-model="row.occur_date" type="date" value-format="YYYY-MM-DD" />
            </template>
          </el-table-column>
          <el-table-column label="说明">
            <template #default="{ row }">
              <el-input v-model="row.description" placeholder="费用说明" />
            </template>
          </el-table-column>
          <el-table-column label="发票号" width="150">
            <template #default="{ row }">
              <el-input v-model="row.invoice_no" placeholder="选填" />
            </template>
          </el-table-column>
          <el-table-column label="发票" width="100">
            <template #default="{ row, $index }">
              <el-upload
                :show-file-list="false"
                :before-upload="(f) => beforeInvoiceUpload(f, $index)"
                :http-request="(opt) => doInvoiceUpload(opt, $index)"
                accept=".jpg,.jpeg,.png,.bmp,.pdf,.webp"
              >
                <el-button link type="primary" size="small">上传发票</el-button>
              </el-upload>
              <div v-if="row.attachment" class="att-tip">
                <el-icon><Paperclip /></el-icon>
                <span @click="previewAtt(row.attachment)" class="att-link">已识别</span>
                <el-button link type="danger" size="small" @click="removeAtt($index)">删</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ $index }">
              <el-button link type="danger" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div style="margin-top:10px">
          <el-button type="dashed" @click="addItem">+ 添加明细</el-button>
          <span style="margin-left:16px;color:#909399">
            合计：<b style="color:#f56c6c">¥{{ totalAmount.toFixed(2) }}</b>
          </span>
        </div>

        <el-form-item style="margin-top:24px">
          <el-button type="primary" @click="save('draft')">保存草稿</el-button>
          <el-button type="success" @click="save('submit')">保存并提交</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Paperclip } from '@element-plus/icons-vue'
import { listCategories, createExpense, updateExpense, getExpense, submitExpense, uploadFile } from '../api'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const categories = ref([])
const today = new Date().toISOString().slice(0, 10)

const form = reactive({
  title: '',
  reason: '',
  items: []
})

const totalAmount = computed(() =>
  form.items.reduce((sum, i) => sum + (Number(i.amount) || 0), 0)
)

function addItem() {
  form.items.push({
    category_id: categories.value[0]?.id || null,
    amount: 0,
    occur_date: today,
    description: '',
    invoice_no: ''
  })
}
function removeItem(idx) {
  form.items.splice(idx, 1)
}

// ===== 发票上传 + OCR =====
function beforeInvoiceUpload(file) {
  const ok = file.size / 1024 / 1024 < 10
  if (!ok) {
    ElMessage.error('发票图片不能超过 10MB')
    return false
  }
  return true
}

async function doInvoiceUpload(opt, idx) {
  const formData = new FormData()
  formData.append('file', opt.file)
  try {
    const res = await uploadFile(formData)
    const att = res.data
    const item = form.items[idx]
    item.attachment = att
    // OCR 回填金额与发票号
    if (att.ocr_amount != null) item.amount = Number(att.ocr_amount)
    if (att.ocr_invoice_no) item.invoice_no = att.ocr_invoice_no
    ElMessage.success('发票已上传，OCR 自动回填成功')
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    opt.onSuccess && opt.onSuccess()
  }
}

function removeAtt(idx) {
  form.items[idx].attachment = null
}

function previewAtt(att) {
  if (att.file_path) {
    window.open(import.meta.env.VITE_API_BASE + att.file_path, '_blank')
  } else if (att.ocr_text) {
    ElMessage.info(att.ocr_text)
  }
}

async function loadCategories() {
  const res = await listCategories()
  categories.value = res.data
  if (!form.items.length) addItem()
}

async function loadEdit() {
  const res = await getExpense(route.params.id)
  const d = res.data
  form.title = d.title
  form.reason = d.reason || ''
  form.items = d.items.map((i) => ({
    category_id: i.category_id,
    amount: i.amount,
    occur_date: i.occur_date,
    description: i.description,
    invoice_no: i.invoice_no
  }))
}

async function save(action) {
  if (!form.title) {
    ElMessage.warning('请填写报销标题')
    return
  }
  if (!form.items.length || form.items.some((i) => !i.category_id)) {
    ElMessage.warning('请完善每条明细的费用类别')
    return
  }
  const payload = {
    title: form.title,
    reason: form.reason,
    items: form.items.map((i) => ({
      category_id: i.category_id,
      amount: i.amount,
      occur_date: i.occur_date,
      description: i.description,
      invoice_no: i.invoice_no
    }))
  }

  let savedId = route.params.id
  if (isEdit.value) {
    await updateExpense(savedId, payload)
    ElMessage.success('更新成功')
  } else {
    const res = await createExpense(payload)
    savedId = res.data.id
    ElMessage.success('保存成功')
  }

  if (action === 'submit') {
    await submitExpense(savedId)
    ElMessage.success('提交成功')
  }
  router.push('/my-expenses')
}

onMounted(async () => {
  await loadCategories()
  if (isEdit.value) await loadEdit()
})
</script>

<style scoped>
.el-button--dashed {
  border-style: dashed;
}
.att-tip {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  color: #67c23a;
  margin-top: 2px;
}
.att-link {
  color: #2d6cdf;
  cursor: pointer;
  text-decoration: underline;
}
</style>
