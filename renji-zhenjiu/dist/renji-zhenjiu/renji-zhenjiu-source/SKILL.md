---
name: renji-zhenjiu-source
description: |
  人纪针灸全书来源路由入口。当用户询问书中任意术语定义（同身寸、井荣俞原经合、天应穴、
  灵龟八法、回阳九针等）、经络穴位索引、书中案例细节、作者观点原文，或不确定该用哪个
  子能力时，由此入口路由到对应能力卡或共享词典；也承载未晋级为独立 Skill 的术语与案例素材。
metadata:
  cangjie.generated-by: cangjie-tools v2.5.0
  cangjie.variant: router
  cangjie.bundle-id: bundle.renji-zhenjiu
  cangjie.capability-count: 7
  cangjie.entrypoint-count: 8
---
# 人纪系列·针灸篇（倪海厦针灸课程转录） — 来源路由入口（compact pack）

## 触发与不触发

**适用**：与本书能力域相关的咨询与任务（见下方路由表的意图列）。
**不适用**：
- 西医诊断与用药建议（本书对现代医学的批评属作者立场，非循证结论，不得作为医疗建议）。
- 治癌/治AIDS 等超出循证范围的声称（仅作为历史观点引用，不提供治疗方案）。
- 真人示范类操作细节（进针手势、放血手法）——文字无法替代临床指导。
- 繁体/简体的古籍原文考据与版本校勘。

## 核心原则（常驻速览，概览类问题读到这里即可回答）

1. 辨证选穴先归经：必须知道痛在哪条经、病在哪个脏腑，绝不"哪里痛扎哪里"。
2. 五行生克是决策文法：虚则补其母、实则泻其子；先强将被克之脏阻断传变。
3. 按病性分派法则：内科病用俞募、经络四肢痛用子母、骨伤急症用会郄、表里同病用原络。
4. 诊断靠压痛点+望闻问：背俞穴压痛定脏腑、耳针压痛定病位、眼诊五色定五脏；脚热=健康。
5. 安全第一：针而勿灸灸勿针、大虚/汗/酒后不针、热/汗处/眼/阴不灸、孕妇禁针合谷三阴交。
6. 疗效立竿见影：正确取穴下针即效；病退不改方，病进必改穴。
7. 操作须专业：放血、深刺、灸百壮等属专业医疗行为，禁止非专业人士自行施治。

## 能力路由（先读本表，按意图加载 1 张能力卡）

| 用户意图 | 先读 | 补读/备注 |
|---|---|---|
| 帮我看这个肩痛/腰痛/头痛应该怎么取穴；这种痛是新病还是久病，该补还是泻；内科病（胃病/心脏病/肝病）怎么选穴；怎么判断该用哪个治疗法则（子母/俞募/会郄）；某个穴位怎么找到具体位置 | references/capabilities/renji-acupuncture-selection.md | 已晋级为独立 Skill `renji-acupuncture-selection`（已安装时优先直接使用；本卡仅作原文与背景补充） |
| 痛经/便秘/头痛/腰痛/失眠/咳嗽怎么针灸；某某病（乳癌/痔疮/盲肠炎/扁桃腺…）怎么治；高血压/糖尿病/心脏病有什么针灸方案；这个症状（眼干/耳鸣/牙痛/喉痛）扎哪里 | references/capabilities/renji-acupuncture-formulas.md | 已晋级为独立 Skill `renji-acupuncture-formulas`（已安装时优先直接使用；本卡仅作原文与背景补充） |
| 列缺/足三里/委中/太冲…穴在哪里、怎么找；某某穴主治什么、针多深、能不能灸；某条经络（肺经/胃经/胆经…）的循行和穴位；井荣俞原经合属性、原穴络穴郄穴在哪 | references/capabilities/renji-meridian-point-db.md | 已晋级为独立 Skill `renji-meridian-point-db`（已安装时优先直接使用；本卡仅作原文与背景补充） |
| 怎么判断病人哪里有问题（压哪个椎/耳部哪个点）；帮我看看这个症状属于哪个脏腑/哪条经；眼诊/耳针/望诊怎么辨病；如何判断虚实寒热（喜按拒按、脚冷脚热） | references/capabilities/renji-diagnosis.md | 已晋级为独立 Skill `renji-diagnosis`（已安装时优先直接使用；本卡仅作原文与背景补充） |
| 这个穴/部位能不能灸、能不能针；孕妇/生理期能不能针灸；针灸有什么禁忌和注意事项；留针多久、怎么起针、灸后怎么办 | references/capabilities/renji-safety-contraindications.md | 已晋级为独立 Skill `renji-safety-contraindications`（已安装时优先直接使用；本卡仅作原文与背景补充） |
| 昏迷/晕倒怎么急救；脑震荡/中风的针灸处理；灵龟八法/子午流注怎么开穴；放血（十宣/委中/然谷）怎么做 | references/capabilities/renji-emergency-special-needling.md | 已晋级为独立 Skill `renji-emergency-special-needling`（已安装时优先直接使用；本卡仅作原文与背景补充） |
| 小儿发烧/惊风/黄疸怎么推拿；三关怎么辨证、天河水怎么开；日常怎么养生（耳朵按摩/五脏逼毒）；家里怎么艾灸保健（关元/足三里） | references/capabilities/renji-pediatric-tuina-wellness.md | 已晋级为独立 Skill `renji-pediatric-tuina-wellness`（已安装时优先直接使用；本卡仅作原文与背景补充） |

**非能力类查询**：
- 书名/作者/章节/整书概览 → references/overview.md
- 术语解释 → references/glossary.md
- 决策规则速查（不需要原文依据时） → references/cheatsheet.md
- 完整意图与关键词索引（本表未覆盖的意图先查这里） → references/capability-index.md

## 加载规则

- 每次任务先读本文件，再按路由表加载 **1** 张能力卡；任务明确跨域时最多加载 2 张。
- 概览/书名类问题不加载能力卡，用「核心原则」与 overview.md 回答。
- 路由表与 capability-index.md 都无法命中的意图，明确告知超出本书范围，不要硬套。

## 边界与判停

- 用户描述的是急症/危重症（昏迷、大出血、剧烈胸痛等）时，停止给出针灸方案，提示立即就医。
- 用户明确是孕妇、婴幼儿（非指针术场景）或体质极度虚弱者时，仅给禁忌提示，不给针刺方案。
- 用户表明自己非医疗专业人员且准备自行施针时，停止输出具体操作，提示必须由执业医师操作。
- 涉及"治愈癌症/肿瘤/艾滋病"等重大疾病承诺时，拒绝并按边界处理。
