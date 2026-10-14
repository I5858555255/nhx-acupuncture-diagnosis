# 阶段 1 任务说明 — 5 提取器并行/串行提取

在 `vendor/cangjie-skill/extractors/` 下有 5 个提取器 prompt：

- `case-extractor.md`（读取该 prompt 并执行）
- `counter-example-extractor.md`（读取该 prompt 并执行）
- `framework-extractor.md`（读取该 prompt 并执行）
- `glossary-extractor.md`（读取该 prompt 并执行）
- `principle-extractor.md`（读取该 prompt 并执行）

执行要求（来自 cangjie-skill SKILL.md 阶段 1）：
1. **并行优先**：Agent 工具一次调用发起 5 个子任务；环境不支持时**串行**执行，产物格式不变。
2. 每个提取器独立输出到 `candidates/<type>.md`（本目录已建骨架）。
3. 长文本按 `vendor/cangjie-skill/methodology/02-stage1-parallel-extract.md` 分块；
   已建内容索引时检索式 extractor 按索引取块。
4. 覆盖率硬门：通过三重验证的候选相对全量扫描基线漏检数必须为 0。
