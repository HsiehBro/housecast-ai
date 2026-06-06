# 房价预测系统

基于 XGBoost 的房价预测全栈 Web 应用，涵盖数据采集、机器学习预测与交互式可视化。数据来源为**西安市高陵区**房源。

## 技术栈

**后端:** Django 4.2, DRF, PostgreSQL 14, XGBoost, Scikit-learn, SHAP
**前端:** Vue 3, Vite 8, TypeScript, Element Plus, ECharts 6, Pinia 3, 高德地图
**部署:** Docker, Nginx, Gunicorn

## 项目结构

```
backend/
├── config/          # Django 配置 (dev/prod 分离)
├── users/           # 用户模型 + JWT 认证
├── houses/          # 房源模型 + CRUD API
├── prediction/      # 预测 API, SHAP, 版本管理
├── ml/              # 特征工程, 训练, 模型持久化
├── crawler/         # 数据爬虫
└── data/            # CSV 数据文件

frontend/
├── src/
│   ├── api/         # Axios 封装 + API 方法
│   ├── views/       # 页面视图 (Home, Predict, Charts, Map, Houses 等)
│   ├── store/       # Pinia 状态管理
│   └── utils/       # AMap 初始化, Axios 实例
├── nginx.conf       # Nginx 配置 (含 API 反向代理)
└── Dockerfile
```

## 开发环境

### 环境要求

- Python 3.12+
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) — Python 包管理工具
- PostgreSQL 14+ (生产环境)
- Git

### 1. 克隆项目

```bash
git clone <repository-url>
cd housecast-ai
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写以下必填项：

```ini
# 必填
DJANGO_SECRET_KEY=<your-secret-key>
DB_PASSWORD=<your-db-password>

# 地图功能必需
VITE_AMAP_KEY=<高德地图 JS API Key>
AMAP_SECURITY_KEY=<高德地图安全密钥>

# 可选
DJANGO_ADMIN_PASSWORD=admin123
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

> 前端环境变量需在 `frontend/` 下也创建 `.env` 文件，变量名需以 `VITE_` 开头。

### 3. 后端启动

```bash
cd backend

# 安装 Python 依赖 (使用 uv，不要用 pip)
uv sync

# 数据库迁移 (开发环境默认使用 SQLite)
uv run python manage.py migrate

# 创建管理员账户
uv run python manage.py createsuperuser

# 启动开发服务器
uv run python manage.py runserver
```

后端运行在 `http://localhost:8000`。

### 4. 导入数据与训练模型

```bash
cd backend

# 导入 CSV 房源数据到数据库
uv run python manage.py import_houses data/houses.csv

# 训练 XGBoost 模型 (输出至 ml/models/)
uv run python ml/train.py
```

> 首次启动预测功能前必须先训练模型，否则预测 API 不可用。

### 5. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (HMR)
npm run dev
```

前端运行在 `http://localhost:5173`，Vite 自动代理 API 请求到后端。

### 6. 验证

- 前端页面: http://localhost:5173
- 后端 API: http://localhost:8000/api/houses/
- 管理后台: http://localhost:8000/admin/
- 预测接口: `POST http://localhost:8000/api/prediction/predict/`

## Docker 部署

> **注意：** Docker 运行在远程机器上，请在远程环境执行以下命令。

### 1. 准备远程环境

确保远程机器已安装 Docker 和 Docker Compose，并将项目代码上传至远程机器。

### 2. 配置环境变量

在远程项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑填写实际值
```

### 3. 启动服务

```bash
docker-compose up -d
```

启动后自动执行：
- PostgreSQL 数据库初始化
- 数据库迁移
- 创建管理员账户 (用户名: admin, 密码: `DJANGO_ADMIN_PASSWORD`)
- 检测并自动导入 CSV 数据 (如有 `data/houses.csv`)
- 检测 ML 模型文件
- 静态文件收集

### 4. 查看状态与日志

```bash
docker-compose ps                # 查看服务状态
docker-compose logs -f           # 查看全部日志
docker-compose logs -f backend   # 查看后端日志
```

### 5. 训练模型 (容器内)

```bash
docker-compose exec backend python ml/train.py
```

### 6. 导入数据 (容器内)

```bash
docker-compose exec backend python manage.py import_houses /app/data/houses.csv
```

### 服务架构

```
                    ┌──────────────┐
                    │   Nginx :80  │ ← 前端静态资源 + API 反向代理
                    │  (frontend)  │
                    └──────┬───────┘
                           │ /api/
                    ┌──────▼───────┐
                    │  Gunicorn     │ ← Django 后端
                    │  :8000        │
                    │  (backend)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  PostgreSQL   │ ← 数据持久化
                    │  :5432        │
                    └──────────────┘
```

部署后访问: `http://<host>` (Nginx 统一入口)

## API 接口

| 分类 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/auth/register/` | 注册 |
| 认证 | POST | `/api/auth/login/` | 登录 |
| 认证 | POST | `/api/auth/logout/` | 登出 |
| 认证 | POST | `/api/auth/refresh/` | 刷新 Token |
| 认证 | GET | `/api/auth/me/` | 当前用户 |
| 房源 | GET | `/api/houses/` | 列表 (分页) |
| 房源 | POST | `/api/houses/` | 创建 |
| 房源 | GET | `/api/houses/{id}/` | 详情 |
| 房源 | PUT | `/api/houses/{id}/` | 更新 |
| 房源 | DELETE | `/api/houses/{id}/` | 删除 |
| 预测 | POST | `/api/prediction/predict/` | 房价预测 |
| 预测 | GET | `/api/prediction/model-info/` | 模型信息 |
| 预测 | POST | `/api/prediction/explain/` | SHAP 解释 |
| 预测 | GET | `/api/prediction/versions/` | 模型版本列表 |
| 预测 | GET | `/api/prediction/versions/current/` | 当前版本 |
| 预测 | POST | `/api/prediction/versions/rollback/` | 回滚版本 |

## ML 流水线

```
CSV 数据 → import_data.py (导入 DB)
         → features.py   (特征工程: 清洗/编码/标准化)
         → train.py      (XGBoost + 交叉验证)
         → joblib 持久化  → ml/models/house_price_model.pkl
         → service.py    (启动加载, 在线推理)
         → explainability.py (SHAP 可解释性)
         → versioning.py (模型版本管理 + 回滚)
```

## 常用命令速查

```bash
# === 后端 ===
cd backend
uv sync                                        # 安装依赖
uv run python manage.py migrate                # 迁移
uv run python manage.py createsuperuser        # 管理员
uv run python manage.py runserver              # 开发服务器
uv run python manage.py test                   # 测试
uv run python manage.py import_houses <csv>    # 导入数据
uv run python ml/train.py                      # 训练模型

# === 前端 ===
cd frontend
npm install                                    # 安装依赖
npm run dev                                    # 开发服务器
npm run build                                  # 生产构建
npx vue-tsc --noEmit                           # 类型检查
npm run test                                   # 测试

# === Docker ===
docker-compose up -d                           # 启动
docker-compose logs -f                         # 日志
docker-compose exec backend python ml/train.py # 容器内训练
```

## 许可证

MIT
