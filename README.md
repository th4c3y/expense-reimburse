# 公司费用报销系统 (Internal Expense Reimbursement)

一套功能齐全的公司内部费用报销 Web 应用。

- **前端**：Vue 3 + Vite + Vue Router + Pinia + Axios + Element Plus + ECharts
- **后端**：Python Flask + Flask-SQLAlchemy + Flask-JWT-Extended + Flask-CORS
- **数据库**：外部已存在的 MariaDB（通过 PyMySQL 连接）

---

## 功能清单

| 模块 | 功能 |
| --- | --- |
| 认证 | 登录、获取当前用户、修改密码（JWT） |
| 报销单 | 新建 / 编辑 / 删除 / 提交 / 查看详情，明细动态增删 |
| 审批流 | 两级审批（部门经理 → 财务），通过 / 驳回 / 付款 |
| 审批中心 | 按角色展示待我审批列表 + 审批记录时间线 |
| 用户管理 | 用户增删改查（管理员） |
| 部门管理 | 部门增删改查（管理员） |
| 报销类别 | 类别增删改查（管理员 / 财务） |
| 统计报表 | 概览卡片、类别分布、部门金额、月度趋势（ECharts） |

**角色**：`admin`（管理员）、`manager`（部门经理）、`finance`（财务）、`employee`（员工）

**审批流程**：草稿 → 提交 → 审批中（经理节点）→ 审批中（财务节点）→ 已通过 → 已付款 / 驳回

---

## 目录结构

```
web/
├── backend/                 # Flask 后端
│   ├── app/
│   │   ├── api/             # 各业务蓝图（auth/user/department/category/expense/approval/statistics）
│   │   ├── models.py        # SQLAlchemy 模型
│   │   └── utils/           # 响应工具、鉴权装饰器
│   ├── config.py            # 数据库 / JWT / CORS 配置
│   ├── init_db.py           # 建表 + 种子数据脚本
│   ├── run.py               # 启动入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Vue3 前端
│   └── src/
│       ├── api/             # 接口封装
│       ├── layouts/         # 主布局
│       ├── router/          # 路由 + 权限守卫
│       ├── stores/          # Pinia
│       ├── utils/           # Axios 封装
│       └── views/           # 页面
├── database/
│   └── schema.sql           # MariaDB 建表脚本（备用 / 参考）
└── README.md
```

---

## 快速开始

### 1. 准备 MariaDB

系统使用**外部已存在的空白 MariaDB 数据库**。请先创建数据库（例如 `expense_db`）：

```sql
CREATE DATABASE expense_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端

```bash
cd backend

# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

# 配置数据库连接（复制并修改）
cp .env.example .env            # 修改 DB_USER / DB_PASSWORD / DB_HOST / DB_PORT / DB_NAME

# 初始化数据库（建表 + 写入示例数据）
python init_db.py

# 启动服务（默认 5000 端口）
python run.py
```

> 也可以通过环境变量直接传入，无需 `.env` 文件。

### 3. 前端

```bash
cd frontend
npm install
npm run dev          # 默认 http://localhost:5173
```

前端开发服务器已配置代理，将 `/api` 请求转发到 `http://127.0.0.1:5000`。

### 4. 登录

打开 `http://localhost:5173`，使用演示账号登录（默认密码均为 `123456`）：

| 用户名 | 角色 | 说明 |
| --- | --- | --- |
| `admin` | 管理员 | 用户 / 部门 / 类别管理，全部审批 |
| `manager` | 部门经理 | 经理节点审批 |
| `finance` | 财务 | 财务节点审批、付款 |
| `employee` | 员工 | 提交报销单 |

---

## 默认审批流程说明

1. 员工新建报销单并**提交** → 状态变为「审批中（节点 1）」。
2. **部门经理**在审批中心通过 → 进入「审批中（节点 2）」。
3. **财务**通过 → 状态「已通过」；财务可标记为「已付款」。
4. 任一节点**驳回** → 状态「已驳回」，员工可编辑后重新提交。

> 当前为两级审批（经理 → 财务）的固定流程。如需更灵活的多级 / 自定义审批流，可在 `approval.py` 与 `ExpenseSheet.current_node` 基础上扩展。

---

## 接口一览

所有接口前缀为 `/api`，统一返回格式：`{ code, message, data }`。

- `POST /auth/login` 登录
- `GET /auth/me` 当前用户
- `GET /users`、`POST /users`、`PUT /users/<id>`、`DELETE /users/<id>` 用户管理
- `GET /departments` ... 部门管理
- `GET /categories` ... 报销类别
- `GET /expenses`、`POST /expenses`、`PUT /expenses/<id>`、`DELETE /expenses/<id>`、`POST /expenses/<id>/submit` 报销单
- `GET /approvals/pending`、`POST /approvals/<id>/approve|reject|pay`、`GET /approvals/<id>/records` 审批
- `GET /stats/overview|by-category|by-department|trend` 统计
