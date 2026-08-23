-- =========================================================
-- 公司费用报销系统 - MariaDB 建表脚本（备用 / 手动执行）
-- 通常不需要手动执行，init_db.py 会通过 SQLAlchemy 自动建表。
-- 本文件仅作为数据库结构参考与备份。
-- =========================================================

CREATE TABLE IF NOT EXISTS `department` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(64)  NOT NULL COMMENT '部门名称',
  `code`        VARCHAR(32)  NOT NULL COMMENT '部门编码',
  `manager_id`  INT          NULL COMMENT '部门负责人',
  `description` VARCHAR(255) NULL,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_department_name` (`name`),
  UNIQUE KEY `uq_department_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表';

CREATE TABLE IF NOT EXISTS `user` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`        VARCHAR(64)  NOT NULL COMMENT '登录名',
  `password_hash`   VARCHAR(255) NOT NULL,
  `real_name`       VARCHAR(64)  NOT NULL COMMENT '真实姓名',
  `email`           VARCHAR(128) NULL,
  `phone`           VARCHAR(32)  NULL,
  `department_id`   INT          NULL,
  `role`            VARCHAR(32)  NOT NULL DEFAULT 'employee' COMMENT 'admin/manager/finance/employee',
  `status`          TINYINT      NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
  `approval_limit`  DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '审批额度上限',
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_username` (`username`),
  KEY `idx_user_department` (`department_id`),
  CONSTRAINT `fk_user_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE IF NOT EXISTS `expense_category` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(64)  NOT NULL COMMENT '类别名称',
  `code`        VARCHAR(32)  NOT NULL,
  `description` VARCHAR(255) NULL,
  `status`      TINYINT      NOT NULL DEFAULT 1,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_category_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报销类别表';

CREATE TABLE IF NOT EXISTS `expense_sheet` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `sheet_no`       VARCHAR(32)  NOT NULL COMMENT '单据编号',
  `applicant_id`   INT          NOT NULL COMMENT '申请人',
  `department_id`  INT          NULL,
  `title`          VARCHAR(128) NOT NULL COMMENT '报销标题',
  `reason`         TEXT         NULL COMMENT '报销事由',
  `total_amount`   DECIMAL(12,2) NOT NULL DEFAULT 0,
  `status`         VARCHAR(32)  NOT NULL DEFAULT 'draft' COMMENT 'draft/pending/approved/rejected/paid',
  `flow_id`        INT          NULL COMMENT '匹配的审批流ID',
  `current_node`   INT          NOT NULL DEFAULT 1 COMMENT '当前审批节点序号(order_no)',
  `reject_reason`  TEXT         NULL,
  `paid_at`        DATETIME     NULL,
  `approved_at`    DATETIME     NULL,
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sheet_no` (`sheet_no`),
  KEY `idx_sheet_applicant` (`applicant_id`),
  KEY `idx_sheet_status` (`status`),
  KEY `idx_sheet_department` (`department_id`),
  KEY `idx_sheet_flow` (`flow_id`),
  CONSTRAINT `fk_sheet_applicant` FOREIGN KEY (`applicant_id`) REFERENCES `user` (`id`),
  CONSTRAINT `fk_sheet_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`),
  CONSTRAINT `fk_sheet_flow` FOREIGN KEY (`flow_id`) REFERENCES `approval_flow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报销单主表';

CREATE TABLE IF NOT EXISTS `expense_item` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `sheet_id`    INT          NOT NULL,
  `category_id` INT          NOT NULL,
  `amount`      DECIMAL(12,2) NOT NULL COMMENT '金额',
  `occur_date`  DATE         NOT NULL COMMENT '发生日期',
  `description` VARCHAR(255) NULL,
  `invoice_no`  VARCHAR(64)  NULL COMMENT '发票号',
  `remark`      VARCHAR(255) NULL,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_item_sheet` (`sheet_id`),
  KEY `idx_item_category` (`category_id`),
  CONSTRAINT `fk_item_sheet` FOREIGN KEY (`sheet_id`) REFERENCES `expense_sheet` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_item_category` FOREIGN KEY (`category_id`) REFERENCES `expense_category` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报销明细表';

CREATE TABLE IF NOT EXISTS `approval_record` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `sheet_id`      INT          NOT NULL,
  `approver_id`   INT          NOT NULL COMMENT '审批人',
  `node`          INT          NOT NULL DEFAULT 1 COMMENT '审批节点',
  `action`        VARCHAR(32)  NOT NULL COMMENT 'submit/approve/reject/transfer/comment',
  `comment`       TEXT         NULL COMMENT '审批意见',
  `before_status` VARCHAR(32)  NULL,
  `after_status`  VARCHAR(32)  NULL,
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_approval_sheet` (`sheet_id`),
  KEY `idx_approval_approver` (`approver_id`),
  CONSTRAINT `fk_approval_sheet` FOREIGN KEY (`sheet_id`) REFERENCES `expense_sheet` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_approval_approver` FOREIGN KEY (`approver_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批记录表';

-- =========================================================
-- 审批流配置（可配置多级审批）
-- =========================================================

CREATE TABLE IF NOT EXISTS `approval_flow` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`             VARCHAR(64)  NOT NULL COMMENT '审批流名称',
  `description`      VARCHAR(255) NULL,
  `priority`         INT          NOT NULL DEFAULT 0 COMMENT '优先级,越大越优先匹配',
  `min_amount`       DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '适用最低金额(含)',
  `max_amount`       DECIMAL(12,2) NULL COMMENT '适用最高金额(不含),NULL为无上限',
  `department_scope` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '适用部门ID,逗号分隔,空为全部',
  `is_default`       TINYINT      NOT NULL DEFAULT 0 COMMENT '是否默认流',
  `status`           TINYINT      NOT NULL DEFAULT 1,
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_flow_default` (`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批流模板表';

CREATE TABLE IF NOT EXISTS `approval_node` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `flow_id`         INT          NOT NULL,
  `order_no`        INT          NOT NULL COMMENT '节点顺序',
  `name`            VARCHAR(64)  NOT NULL COMMENT '节点名称',
  `approver_type`   VARCHAR(32)  NOT NULL DEFAULT 'role' COMMENT 'role/dept_manager/user/finance_director',
  `approver_value`  VARCHAR(64)  NULL COMMENT '角色名/用户ID',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_node_flow` (`flow_id`),
  CONSTRAINT `fk_node_flow` FOREIGN KEY (`flow_id`) REFERENCES `approval_flow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批流节点表';

CREATE TABLE IF NOT EXISTS `attachment` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `item_id`        INT          NULL,
  `sheet_id`       INT          NULL,
  `original_name`  VARCHAR(255) NULL,
  `stored_name`    VARCHAR(255) NULL,
  `file_path`      VARCHAR(512) NULL,
  `file_size`      INT          NOT NULL DEFAULT 0,
  `mime_type`      VARCHAR(64)  NULL,
  `ocr_text`       TEXT         NULL COMMENT 'OCR识别全文',
  `ocr_amount`     DECIMAL(12,2) NULL COMMENT 'OCR识别金额',
  `ocr_invoice_no` VARCHAR(64)  NULL COMMENT 'OCR识别发票号',
  `ocr_status`     TINYINT      NOT NULL DEFAULT 0 COMMENT '0未识别 1已识别 2失败',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_attach_item` (`item_id`),
  KEY `idx_attach_sheet` (`sheet_id`),
  CONSTRAINT `fk_attach_item` FOREIGN KEY (`item_id`) REFERENCES `expense_item` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_attach_sheet` FOREIGN KEY (`sheet_id`) REFERENCES `expense_sheet` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='附件表';
