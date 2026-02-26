# EvoMap 赏金审核状态监控日志

## 2026-02-22 21:04 CST

### 查询任务
- 任务ID: `cmltory6a0014j679xmmro2gf`
- 提交ID: `cmlucdlud0rqlqj29w6en97ff`
- 节点ID: `hub_0f978bbe1fb5`
- 任务名称: AI 推理管道 + 模型缓存

### 检查结果
**状态**: ❌ 无法查询 - 缺少 API 凭证

### 详情
尝试通过以下方式查询 EvoMap API：
1. `https://evomap.ai/api/v1/tasks/{taskId}` - 404
2. `https://evomap.ai/api/tasks/{taskId}` - 404
3. `https://evomap.ai/hub/{hubId}/task/{taskId}` - 404
4. `https://evomap.ai/submission/{submissionId}` - 404

EvoMap 的 API 需要认证令牌才能访问。当前无法获取任务状态。

### 建议
1. 在 `TOOLS.md` 中添加 EvoMap API Token 配置
2. 或使用浏览器自动化登录 EvoMap 后查看任务状态
3. 手动检查 EvoMap 网站确认审核状态

---
