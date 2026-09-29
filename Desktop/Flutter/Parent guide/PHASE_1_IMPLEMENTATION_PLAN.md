# Phase 1 — Foundation: Implementation Plan

## Objective
Establish a stable monorepo development environment with all apps running locally, backend health endpoint operational, MongoDB and Redis connected, and CI pipeline passing.

---

## Milestone 1 — Project Foundation

### Task Breakdown

#### 1.1 Repository & Monorepo Setup
- [ ] Initialize Git repository
- [ ] Create monorepo structure per project spec:
  ```
  parentguide/
  ├── apps/
  │   ├── mobile/
  │   ├── web/
  │   └── api/
  ├── packages/
  │   ├── shared/
  │   ├── types/
  │   ├── validation/
  │   └── config/
  ├── infrastructure/
  │   └── docker/
  ├── docs/
  ├── .github/
  │   └── workflows/
  ├── docker-compose.yml
  ├── package.json
  └── README.md
  ```
- [ ] Configure root `package.json` with workspaces

#### 1.2 TypeScript Configuration
- [ ] Create `tsconfig.base.json` with shared compiler options
- [ ] Configure `tsconfig.json` for each app (mobile, web, api)
- [ ] Set up strict type-checking rules
- [ ] Configure path aliases for shared packages

#### 1.3 Code Quality Tools
- [ ] Install and configure ESLint
  - Base config in root
  - Extend configs for TypeScript
  - App-specific overrides
- [ ] Install and configure Prettier
  - Shared formatting rules
  - ESLint integration (no conflicts)
- [ ] Add lint scripts to package.json

#### 1.4 Git Hooks
- [ ] Install Husky + lint-staged
- [ ] Configure pre-commit hook:
  - ESLint check
  - Prettier format check
  - TypeScript type check (staged files)

#### 1.5 Docker Compose Infrastructure
- [ ] Create `docker-compose.yml` with:
  - MongoDB service (with persistent volume)
  - Redis service
  - Admin UI (optional: MongoDB Express, Redis Commander)
- [ ] Configure environment-specific compose files:
  - `docker-compose.dev.yml`
  - `docker-compose.prod.yml`
- [ ] Add startup/shutdown scripts

#### 1.6 Database Connections
- [ ] MongoDB connection utility in `packages/config/`
  - Connection pooling configuration
  - Error handling
  - Health check endpoint
- [ ] Redis connection utility in `packages/config/`
  - Retry logic
  - Health check endpoint

#### 1.7 Express API Server
- [ ] Create `apps/api/` project structure
- [ ] Basic Express server setup:
  - TypeScript compilation
  - Middleware (JSON parser, CORS, Helmet)
  - Error handling
- [ ] Health endpoint: `GET /health`
  - Returns MongoDB connection status
  - Returns Redis connection status
  - Returns server uptime
- [ ] Basic route structure:
  ```
  /api/v1/auth/*
  /api/v1/families/*
  /api/v1/location/*
  ```

#### 1.8 React Native Mobile App
- [ ] Initialize React Native project in `apps/mobile/`
- [ ] TypeScript configuration
- [ ] Navigation setup (React Navigation)
- [ ] State management (Zustand)
- [ ] API client (Axios)
- [ ] Socket.IO client setup
- [ ] Secure storage configuration
- [ ] Verify app runs on emulator/device

#### 1.9 React Web App
- [ ] Initialize React project in `apps/web/` (Vite)
- [ ] TypeScript configuration
- [ ] Router setup (React Router)
- [ ] State management (Zustand)
- [ ] API client (Axios)
- [ ] Tailwind CSS configuration
- [ ] Verify app runs locally

#### 1.10 Environment Configuration
- [ ] Create `.env.example` with all required variables:
  ```
  NODE_ENV=
  PORT=
  MONGODB_URI=
  REDIS_URL=
  JWT_ACCESS_SECRET=
  JWT_REFRESH_SECRET=
  FIREBASE_PROJECT_ID=
  MAPS_API_KEY=
  ```
- [ ] Create config loading utility with validation (Zod)
- [ ] Ensure `.env` is in `.gitignore`

#### 1.11 CI Pipeline
- [ ] Create GitHub Actions workflow `.github/workflows/ci.yml`:
  - Triggers: push to main, PRs
  - Steps:
    1. Checkout code
    2. Setup Node.js
    3. Install dependencies
    4. Lint check
    5. Type check
    6. Run tests (placeholder)
    7. Build all apps
- [ ] Configure GitHub Actions secrets template

---

## Definition of Done Checklist

- [ ] All apps run locally:
  - [ ] `npm run dev` starts API server
  - [ ] Mobile app launches on emulator
  - [ ] Web app launches in browser
- [ ] Backend health endpoint works: `GET /api/v1/health` returns 200
- [ ] MongoDB connects: health endpoint shows "mongo: connected"
- [ ] Redis connects: health endpoint shows "redis: connected"
- [ ] CI passes: GitHub Actions workflow completes successfully

---

## Implementation Order

1. **Repository & Monorepo** (prerequisite for everything)
2. **TypeScript + ESLint + Prettier** (code quality foundation)
3. **Docker Compose** (infrastructure for DBs)
4. **Database Connections** (MongoDB + Redis utilities)
5. **Express API Server** (backend with health endpoint)
6. **Environment Configuration** (dotenv + validation)
7. **React Native Mobile App** (initialize + basic structure)
8. **React Web App** (initialize + basic structure)
9. **Git Hooks** (last — after code quality tools are stable)
10. **CI Pipeline** (final — validates entire setup)

---

## Estimated Effort

| Task | Duration |
|------|----------|
| Repository & Monorepo | 2-3 hours |
| TypeScript + Linting + Prettier | 2-3 hours |
| Docker Compose | 1-2 hours |
| Database Connections | 2-3 hours |
| Express API Server | 3-4 hours |
| Environment Configuration | 1-2 hours |
| React Native Mobile App | 3-4 hours |
| React Web App | 3-4 hours |
| Git Hooks | 1 hour |
| CI Pipeline | 2-3 hours |
| **Total** | **20-28 hours** |

---

## Risk Factors

- **Mobile emulator issues**: Verify Android Studio/Xcode setup before starting
- **MongoDB/Redis connection**: Test Docker Compose independently first
- **TypeScript strict mode**: May require gradual adoption if existing code has issues
- **Port conflicts**: Standardize ports in `.env.example`

---

## Success Criteria

Phase 1 is complete when:
1. New developer can clone repo and run `docker-compose up && npm install && npm run dev`
2. All three apps (API, mobile, web) start without errors
3. Health endpoint confirms all services connected
4. CI pipeline passes on clean commit
5. Pre-commit hooks prevent lint/type errors from being committed
