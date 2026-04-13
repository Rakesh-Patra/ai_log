# InsForge CLI Skill

Use the `insforge` CLI (via the `shell` tool) to manage the backend infrastructure.

## 🗄️ Database (`insforge db`)
- **Query**: `insforge db query "SELECT ..."`
- **Delete**: `insforge db query "DELETE FROM table WHERE ..."`
- **Tables**: `insforge db tables`
- **RPC**: `insforge db rpc <function_name>`

## 🔐 Secrets (`insforge secrets`)
- **List**: `insforge secrets list`
- **Add**: `insforge secrets add <key> <value>`
- **Get**: `insforge secrets get <key>`
- **Delete**: `insforge secrets delete <key>` (Soft delete; restoration possible)

## 👤 Auth (`insforge current`)
- **Verify**: `insforge current` (Check project and region)
- **Metadata**: `insforge metadata` (View overall project infrastructure)
- **Logs**: `insforge logs <source> [--limit <n>]` (Source: `insforge.logs`, `postgres.logs`, `function.logs`)

## 🚀 Functions & Schedules
- **Functions**: `insforge functions list`
- **Invoke**: `insforge functions invoke <slug> [--data <json>]`
- **Schedules**: `insforge schedules list`
- **Create Task**: `insforge schedules create --name --cron --url --method`

## 📦 Deployments & Storage
- **Deployments**: `insforge deployments status <id>`
- **Storage**: `insforge storage buckets`
- **List Files**: `insforge storage list-objects <bucket>`

---

## 💡 Usage Examples

### 1. Check for recent errors
`insforge logs postgrest.logs --limit 10`

### 2. Add a new configuration secret
`insforge secrets add NEW_FEATURE_ENABLED "true"`

### 3. Orchestrated Task: Deployment & Cleanup
- `kubectl delete deployment my-app`
- `insforge db query "DELETE FROM logs WHERE app = 'my-app';"`
