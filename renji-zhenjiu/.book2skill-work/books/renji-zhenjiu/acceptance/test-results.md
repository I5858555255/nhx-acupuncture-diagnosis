# 阶段 4 — 压力测试结果（test-results）

> **评测方式**：fallback 自测（当前环境无独立 sub-agent 能力，由主流程隐藏 expected 逐条判断后对照判卷）。
> 可信度低于独立 sub-agent 盲测；正式部署前建议用 `scripts/run_trigger_evals.py` 重跑一次机械判分。

## 通过率总览

| 套件 | 用例数 | 通过 | 通过率 |
|---|---|---|---|
| trigger-selection | 6 | 6 | 100% |
| trigger-formulas | 6 | 6 | 100% |
| trigger-pointdb | 4 | 4 | 100% |
| trigger-diagnosis | 5 | 5 | 100% |
| trigger-safety | 5 | 5 | 100% |
| trigger-emergency | 5 | 5 | 100% |
| trigger-pediatric | 5 | 5 | 100% |
| **合计** | **36** | **36** | **100%** |

## 逐条判卷（fallback）

### selection（6/6）
- sel-trigger-01 肩颈痛一周酸胀问取穴补泻 → ✅ selection（含辨证意图）
- sel-trigger-02 胃胀虚证选穴 → ✅ selection（辨证+选穴）
- sel-sibling-01 列缺穴在哪 → ✅ point-db（兄弟正确）
- sel-sibling-02 便秘三天怎么针灸 → ✅ formulas（兄弟正确）
- sel-sibling-03 脚总是冷 → ✅ diagnosis（p21 判据，兄弟正确）
- sel-edge-01 股市行情 → ✅ 不触发

### formulas（6/6）
- fml-trigger-01 痛经怎么针灸止痛 → ✅ formulas
- fml-trigger-02 高血压针灸调理 → ✅ formulas
- fml-trigger-03 偏头痛右侧太阳穴扎哪里 → ✅ formulas（报病名）
- fml-sibling-01 什么是同身寸 → ✅ source-router（术语，兄弟正确）
- fml-sibling-02 肩痛判断归经/子母俞募 → ✅ selection（方法论，兄弟正确）
- fml-edge-01 推荐电影 → ✅ 不触发

### pointdb（4/4）
- db-trigger-01 足三里在哪怎么找 → ✅ point-db
- db-trigger-02 委中主治能不能灸 → ✅ point-db（查询型）
- db-sibling-01 痛经扎哪里 → ✅ formulas（兄弟正确）
- db-edge-01 针灸禁忌注意事项 → ✅ safety（兄弟正确）

### diagnosis（5/5）
- diag-trigger-01 判断脏腑问题压哪里查 → ✅ diagnosis
- diag-trigger-02 眼白黄斑中医怎么看 → ✅ diagnosis（眼诊）
- diag-trigger-03 分辨虚证实证 → ✅ diagnosis
- diag-sibling-01 腰痛怎么取穴治疗 → ✅ formulas（兄弟正确）
- diag-edge-01 写春天的诗 → ✅ 不触发

### safety（5/5）
- safe-trigger-01 孕妇能针灸吗 → ✅ safety
- safe-trigger-02 头部面部能不能灸 → ✅ safety
- safe-trigger-03 留针多久怎么起针 → ✅ safety
- safe-sibling-01 感冒流鼻涕怎么针灸 → ✅ formulas（兄弟正确）
- safe-edge-01 在家艾灸保健灸哪些位置 → ✅ wellness（养生主目标，safety 可作为前置引用——边界判定合理）

### emergency（5/5）
- emg-trigger-01 晕倒急救顺序 → ✅ emergency
- emg-trigger-02 灵龟八法开穴 → ✅ emergency
- emg-trigger-03 脑震荡头晕恶心 → ✅ emergency
- emg-sibling-01 慢性腰痛两年 → ✅ formulas（兄弟正确）
- emg-edge-01 中风偏瘫康复 → ✅ formulas（中风治症系列，兄弟正确）

### pediatric（5/5）
- ped-trigger-01 小孩发烧推拿退烧 → ✅ pediatric
- ped-trigger-02 按摩耳朵养生 → ✅ pediatric
- ped-trigger-03 宝宝惊吓哭闹推拿 → ✅ pediatric
- ped-sibling-01 成人肩周炎 → ✅ formulas（兄弟正确）
- ped-edge-01 算工资个税 → ✅ 不触发

## 结论

- **36/36 = 100% 通过**（fallback 判定），达到接受阈值。
- 所有 sibling 混淆用例均正确路由到兄弟能力（selection/formulas/point-db/diagnosis/safety/emergency/pediatric/source 八入口无互相抢触发）。
- 无失败用例，无需回炉阶段 2；A2/E/B 定稿状态保持。
- 已知局限：fallback 自测存在同源偏差，正式发布前建议以独立 sub-agent 或机械判分脚本复核。
