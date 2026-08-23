<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon><Money /></el-icon>
        <span>费用报销系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon><span>概览看板</span>
        </el-menu-item>
        <el-menu-item index="/my-expenses">
          <el-icon><Tickets /></el-icon><span>我的报销</span>
        </el-menu-item>
        <el-menu-item index="/expense-create">
          <el-icon><DocumentAdd /></el-icon><span>新建报销</span>
        </el-menu-item>
        <el-menu-item
          v-if="canApprove"
          index="/approval-center"
        >
          <el-icon><Stamp /></el-icon><span>审批中心</span>
        </el-menu-item>
        <el-menu-item
          v-if="canManage"
          index="/users"
        >
          <el-icon><User /></el-icon><span>用户管理</span>
        </el-menu-item>
        <el-menu-item
          v-if="canManage"
          index="/departments"
        >
          <el-icon><OfficeBuilding /></el-icon><span>部门管理</span>
        </el-menu-item>
        <el-menu-item
          v-if="isAdminOrFinance"
          index="/categories"
        >
          <el-icon><Files /></el-icon><span>报销类别</span>
        </el-menu-item>
        <el-menu-item
          v-if="userStore.role === 'admin'"
          index="/flows"
        >
          <el-icon><Switch /></el-icon><span>审批流配置</span>
        </el-menu-item>
        <el-menu-item
          v-if="canReport"
          index="/reports"
        >
          <el-icon><DataLine /></el-icon><span>统计报表</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">公司费用报销管理平台</div>
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            {{ userStore.user?.real_name }}
            <el-tag size="small" style="margin-left:6px">{{ roleLabel }}</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="changePwd">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="pwdVisible" title="修改密码" width="400px">
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPwd">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/user'
import { changePassword } from '../api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const roleMap = { admin: '管理员', manager: '部门经理', finance: '财务', employee: '员工' }
const roleLabel = computed(() => roleMap[userStore.role] || '')
const activeMenu = computed(() => route.path)

const canApprove = computed(() => ['manager', 'finance', 'admin'].includes(userStore.role))
const canManage = computed(() => userStore.role === 'admin')
const canReport = computed(() => ['admin', 'finance', 'manager'].includes(userStore.role))
const isAdminOrFinance = computed(() => ['admin', 'finance'].includes(userStore.role))

const pwdVisible = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '' })

function handleCommand(cmd) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
      .then(() => {
        userStore.logout()
        router.push('/login')
      })
      .catch(() => {})
  } else if (cmd === 'changePwd') {
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdVisible.value = true
  }
}

async function submitPwd() {
  await changePassword(pwdForm)
  ElMessage.success('密码修改成功')
  pwdVisible.value = false
}
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #1f2d3d;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-weight: 600;
  font-size: 16px;
  padding: 0 18px;
  background: #18222e;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}
.header-title {
  font-size: 18px;
  font-weight: 600;
}
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #303133;
}
.main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
