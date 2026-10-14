# 阶段 2 任务说明 — RIA++ 能力卡

按 `vendor/cangjie-skill/methodology/04-stage2-ria-plus.md` 为每个通过单元构造
R / I / A1 / A2 / E / B 六段能力卡：
- 卡片正文 → `.cangjie/capabilities/cards/<slug>.md`（不带 frontmatter）
- 在 `.cangjie/capabilities/verified.yaml` 登记：capability_id、intents、keywords、
  one_liner、importance（附依据）、frontmatter.description（A2 浓缩版）

`verified.yaml` 是唯一编译事实源（schema 见 vendor/cangjie-skill/schemas/）。
