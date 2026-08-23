import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
      { path: 'my-expenses', name: 'MyExpenses', component: () => import('../views/MyExpensesView.vue') },
      { path: 'expense-create', name: 'ExpenseCreate', component: () => import('../views/ExpenseFormView.vue') },
      { path: 'expense-edit/:id', name: 'ExpenseEdit', component: () => import('../views/ExpenseFormView.vue') },
      { path: 'expense-detail/:id', name: 'ExpenseDetail', component: () => import('../views/ExpenseDetailView.vue') },
      { path: 'approval-center', name: 'ApprovalCenter', component: () => import('../views/ApprovalCenterView.vue'), meta: { roles: ['manager', 'finance', 'admin'] } },
      { path: 'users', name: 'Users', component: () => import('../views/UserManageView.vue'), meta: { roles: ['admin'] } },
      { path: 'departments', name: 'Departments', component: () => import('../views/DepartmentView.vue'), meta: { roles: ['admin'] } },
      { path: 'categories', name: 'Categories', component: () => import('../views/CategoryView.vue'), meta: { roles: ['admin', 'finance'] } },
      { path: 'flows', name: 'Flows', component: () => import('../views/FlowManageView.vue'), meta: { roles: ['admin'] } },
      { path: 'reports', name: 'Reports', component: () => import('../views/ReportView.vue'), meta: { roles: ['admin', 'finance', 'manager'] } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.public) {
    if (to.path === '/login' && userStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
    return
  }
  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }
  if (to.meta.roles && !to.meta.roles.includes(userStore.role)) {
    ElMessage?.error('无权限访问该页面')
    next('/dashboard')
    return
  }
  next()
})

export default router
