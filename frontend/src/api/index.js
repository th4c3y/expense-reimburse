import request from '../utils/request'

// ===== 认证 =====
export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')
export const changePassword = (data) => request.post('/auth/change-password', data)

// ===== 用户 =====
export const listUsers = (params) => request.get('/users', { params })
export const createUser = (data) => request.post('/users', data)
export const updateUser = (id, data) => request.put(`/users/${id}`, data)
export const deleteUser = (id) => request.delete(`/users/${id}`)
export const simpleUsers = () => request.get('/users/simple')

// ===== 部门 =====
export const listDepartments = () => request.get('/departments')
export const createDepartment = (data) => request.post('/departments', data)
export const updateDepartment = (id, data) => request.put(`/departments/${id}`, data)
export const deleteDepartment = (id) => request.delete(`/departments/${id}`)

// ===== 报销类别 =====
export const listCategories = () => request.get('/categories')
export const createCategory = (data) => request.post('/categories', data)
export const updateCategory = (id, data) => request.put(`/categories/${id}`, data)
export const deleteCategory = (id) => request.delete(`/categories/${id}`)

// ===== 报销单 =====
export const listExpenses = (params) => request.get('/expenses', { params })
export const getExpense = (id) => request.get(`/expenses/${id}`)
export const createExpense = (data) => request.post('/expenses', data)
export const updateExpense = (id, data) => request.put(`/expenses/${id}`, data)
export const deleteExpense = (id) => request.delete(`/expenses/${id}`)
export const submitExpense = (id) => request.post(`/expenses/${id}/submit`)

// ===== 审批 =====
export const pendingList = (params) => request.get('/approvals/pending', { params })
export const approveExpense = (id, data) => request.post(`/approvals/${id}/approve`, data)
export const rejectExpense = (id, data) => request.post(`/approvals/${id}/reject`, data)
export const payExpense = (id) => request.post(`/approvals/${id}/pay`)
export const approvalRecords = (id) => request.get(`/approvals/${id}/records`)

// ===== 统计 =====
export const statsOverview = () => request.get('/stats/overview')
export const statsByCategory = () => request.get('/stats/by-category')
export const statsByDepartment = () => request.get('/stats/by-department')
export const statsTrend = () => request.get('/stats/trend')

// ===== 审批流配置 =====
export const listFlows = () => request.get('/flows')
export const createFlow = (data) => request.post('/flows', data)
export const updateFlow = (id, data) => request.put(`/flows/${id}`, data)
export const deleteFlow = (id) => request.delete(`/flows/${id}`)

// ===== 附件上传 / OCR =====
export const uploadFile = (formData) =>
  request.post('/upload/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
export const listAttachments = (params) => request.get('/upload/list', { params })
export const deleteAttachment = (id) => request.delete(`/upload/${id}`)
