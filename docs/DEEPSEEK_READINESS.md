# DeepSeek 受控接入检查

## 已落实的代码约束

- 正式池67家，正式硕士专业工业催化。保留jobs.db、历史分析和投递记录。
- Flash默认及配置为 `deepseek-flash`。深度模型保留 `deepseek-v4-pro`；未调用API验证账号是否支持此型号，需在受控测试中核验，不声称所有模型已可用。
- main.py共享20个岗位的筛选队列预算（新增+历史合计），未处理岗位不写假筛选缓存。
- 深度分析硬上限5个/轮，日上限10；0表示禁用；取消ALLOW_FULL_PRO_ANALYSIS绕过途径。JD补全也先限制到5个候选。
- 日常API错误重试最多3次，因此岗位预算不等于HTTP请求次数。专用预检每请求只尝试一次，最多1次Flash批次+5次深度请求，总计6次。

## 安全运行方式

优先在GitHub Actions选择 `Controlled DeepSeek preflight`，分支选main，`execute=false`：只检查密钥是否存在及选取20条岗位，0次API请求。

确认干跑输出和模型支持后，再手动同一工作流选择 `execute=true`：最多20个岗位Flash粗筛、5个岗位深度分析；不抓取、不补全JD、不通知、只在临时SQLite副本分析。结果JSON在Actions artifact，不回写生产库。没有足够合格岗位或已有当前分析时实际请求会更少。

本地等价命令：

```bash
python scripts/deepseek_preflight.py             # 默认0次API
python scripts/deepseek_preflight.py --execute   # 明确允许受控付费测试
```

不要用 `python main.py` 做首次API连通测试：它仍是67家正式采集与报告任务。日常任务虽有20/5硬限制，仍会采集招聘页面并更新生产状态。

## 验证结果与限制

- 本地干跑：20条岗位、0次API；当前进程/.env未检测到DEEPSEEK_API_KEY。此结果不能推断GitHub Secrets。
- GitHub密钥名称查询与Actions运行记录接口均返回Forbidden，未读取或输出任何密钥值。
- 配置GitHub Secret：Settings → Secrets and variables → Actions → New repository secret，名称DEEPSEEK_API_KEY；已有则无需重建。
- 远端工作流是否真正执行最新SHA、密钥是否存在、账号余额/模型权限/实际响应仍须通过上述云端预检核实。干跑不证明余额或模型可用。
- CI日志新增HEAD SHA、企业数及预算日志，以供核对执行版本。

## 部署追踪

- 8154565已快进同步main，含67家企业池和工业催化画像；推送触发Tests和无AI报告同步，均确认使用8154565。
- 首次CI失败：Python3.11不允许旧HTML f-string表达式中的反斜杠。已改为普通字符串拼接；在独立Python3.11环境下333项测试通过，企业池报告及API零调用干跑通过。
- GitHub Actions REST接口Forbidden，但公开Actions网页可读，可用网页确认最新提交的运行状态。Secret存在性仍需云端干跑确认。

## 云端最终结果

- 应用提交3bb3c9f已同步main。Tests成功（含4e1eb2b及553d65a）；无AI报告同步40646915509成功，Pages发布40646958440成功。
- 自动零API预检40646987765使用3bb3c9f，runner的Secret存在性检查明确失败：DEEPSEEK_API_KEY is not configured for this workflow。因此当前尚不具备实际付费调用条件；本轮没有调用DeepSeek。
- 手动在仓库Settings → Secrets and variables → Actions添加/修正仓库级DEEPSEEK_API_KEY。若使用组织级Secret，需授权该仓库；当前预检无environment绑定，环境级Secret不会自动提供。
- 配好后手动运行Controlled DeepSeek preflight，main，execute=false；确认通过后再execute=true。深度模型deepseek-v4-pro是否对账号可用仍未经API验证；若返回不支持模型，先依据官方模型文档修正analysis_model，再复测，不要用全量任务验证。
- 运行链接：https://github.com/jaxes210/career-agent/actions/runs/40646987765
