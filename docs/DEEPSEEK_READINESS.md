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
