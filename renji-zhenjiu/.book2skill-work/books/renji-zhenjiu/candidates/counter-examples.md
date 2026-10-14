# 阶段 1 候选 — Counter-examples（失败模式/反例/陷阱）

> 来源：全书通读，按 counter-example-extractor 职责提取。每条含 failure_mode/mechanism/warning_signs，不做筛选。

- id: ce01
  title: "哪里痛扎哪里"的取穴错误
  type: counter-example
  source_chapter: 第一、四、五章（多处）
  source_quote: |
    "过去呢，针就是针，灸就是灸……但从文化大革命以后，变成哪里痛针哪里。要真是如此简单，就不用读针灸啦!而且效果又不好，手法又变得开始花哨了。"
  failure_mode: |
    病人说哪痛就在哪下针，不辨经络、不辨虚实，效果差且易误伤。
  mechanism: |
    把"局部症状"误当"病位所在"：痛是经络或脏腑失衡的表象，须归经辨证；
    不学经络走向就无法选对穴，只能乱枪打鸟（如书上写治肩就下三十几针仍痛）。
  warning_signs:
    - 取穴前不问"痛在哪条经/哪个位置"
    - 一次下几十针覆盖式治疗
    - 只记"某穴治某病"清单而不理解机制
  bound_to:
    - "辨证选穴决策框架"
    - "子母补泻取穴法"
  tags: [counter-example, wrong-approach, acupuncture]

- id: ce02
  title: 针上放艾绒（针灸混杂）
  type: counter-example
  source_chapter: 第一章·针灸的使用时机
  source_quote: |
    "古有名训，针就是针，炙就是灸，我们要分开使用。……变成针上头放个艾绒，让病人更痛苦。"
  failure_mode: |
    在同一针上叠加艾灸（温针灸滥用），违背"针而勿灸灸勿针"。
  mechanism: |
    针与灸机制不同：针调气、灸补阳（久火），混用既失精度又徒增痛苦；
    花哨手法常为掩盖辨证能力不足。
  warning_signs:
    - 针上挂艾绒当卖点
    - 不分寒热虚实一律针+灸
  bound_to:
    - "针而勿灸灸勿针"
    - "灸法边界"
  tags: [counter-example, wrong-approach, safety]

- id: ce03
  title: 乱枪打鸟式取穴
  type: counter-example
  source_chapter: 第四章·天宗穴、养老穴等
  source_quote: |
    "看到书上写治肩而下了三十几针，病人起来后还是痛，因为没有扎到小海，知道我的意思吧。"
  failure_mode: |
    不辨经络归属，把书上所有"治肩"的穴全扎一遍，病人仍痛。
  mechanism: |
    肩痛可能属大肠经/小肠经/三焦经/胆经，须先归经再选该经子母穴；
    覆盖式下针掩盖的是辨证缺失。
  warning_signs:
    - 治肩痛不区分前/后/侧/中
    - 一次下针数量远超该病所需（一针可解偏下几十针）
  bound_to:
    - "辨证选穴决策框架"
    - "近取穴/远取穴"
  tags: [counter-example, wrong-approach, shoulder-pain]

- id: ce04
  title: 攒竹透睛明的炫技针法
  type: counter-example
  source_chapter: 第四章·睛明穴与攒竹穴
  source_quote: |
    "过去有人用攒竹透到睛明，这是想表现自己，但一点用都没有。因为这个睛明穴在这里，我们要把眼球拨开才扎得过去，怎么可能从攒竹透到睛明。"
  failure_mode: |
    为炫技做解剖上不可能的透针（攒竹透睛明），无效且易出血伤眼。
  mechanism: |
    穴位之间有解剖屏障（睛明须拨眼球下针），透针须符合解剖可行性与治疗逻辑，
    不能为表现而违反结构。
  warning_signs:
    - 透针路径跨越关键器官（眼球等）
    - 手法以"看起来厉害"而非疗效为目的
  bound_to:
    - "对称治疗法/透穴正确使用"
    - "安全边界"
  tags: [counter-example, wrong-approach, eye-safety]

- id: ce05
  title: 吃钙片反致肾结石
  type: counter-example
  source_chapter: 第四章·太溪穴与肾结石诊治、水泉穴
  source_quote: |
    "钙跟钙片是两回事哦！两个是不等同的。……吃了半天，骨头还是烂，照样一点用都没有，最后还得到肾结石。"
  failure_mode: |
    用钙片补骨（美国常规 1500mg/日）反而骨松+肾结石，患者不知情。
  mechanism: |
    作者主张：天然钙（骨头汤等）与合成钙片代谢路径不同，钙片沉积成结石；
    骨病（骨质疏松）应从肾/骨会大杼/饮食调治。（此为作者个人观点，与主流共识冲突）
  warning_signs:
    - 把"需要钙"等同于"要吃钙片"
    - 骨病只补钙不辨肾虚/脾虚
  bound_to:
    - "八会穴归属（骨会大杼）"
    - "批判边界（钙片断言）"
  tags: [counter-example, nutrition, kidney-stone]

- id: ce06
  title: 化疗致阴阳分隔
  type: counter-example
  source_chapter: 第六章·灵龟八法与子午流注
  source_quote: |
    "一化学治疗就阴阳分隔。这化疗好像把病毒包起来，我们要去解它时，还要通过化疗这一关，才能进去，在治疗上面就会倍增困扰，效果非常不好。"
  failure_mode: |
    经化疗的患者针药效差，治疗难度倍增。
  mechanism: |
    作者模型：化疗造成阴阳分隔（下冷上热、病人不受针力药力），
    需先解化疗屏障才能治本。（此为作者立场性观点，非循证结论）
  warning_signs:
    - 患者已行化疗（治疗需调整预期）
    - 下针/用药后无反应
  bound_to:
    - "阴阳平衡模型"
    - "治疗预期管理"
  tags: [counter-example, chemo, boundary]

- id: ce07
  title: 疫苗/破伤风针无用论
  type: counter-example
  source_chapter: 第一章·隔蒜灸
  source_quote: |
    "如果说，你觉得打破伤风针很好，打疫苗很好，那就去打吧，实际上没什么大帮助，破伤风时，连药也不用吃针也不用下，用灸就可以好。"
  failure_mode: |
    作者断言疫苗/破伤风针帮助有限、灸即可愈——与现代医学共识冲突的立场声明。
  mechanism: |
    作者以个案经验外推否定预防医学；作为 skill 必须标记为"作者观点"，不得作为医疗建议。
  warning_signs:
    - 将作者断言当循证结论
    - 读者据此放弃现代预防措施
  bound_to:
    - "批判边界（疫苗断言）"
    - "灸法适应证"
  tags: [counter-example, vaccine, boundary]

- id: ce08
  title: 肿瘤开刀后复发
  type: counter-example
  source_chapter: 第一章·针灸的使用时机
  source_quote: |
    "即使宣称手术很成功，但这个刀开下去后的结果如何，你需要慢慢去体会它！若去开刀，还是会长回来的。"
  failure_mode: |
    手术切除肿瘤后复发，患者承受手术创伤仍不治本。
  mechanism: |
    作者模型：肿瘤有"根"（痞根、消积），切瘤不除根则复生；
    治疗应行阳（让气机流畅）+断根（灸痞根/消积）。（作者立场，肿瘤治疗须以现代医学为主）
  warning_signs:
    - 把手术当作唯一方案而不处理病因
    - 忽略肿块"根"的持续存在
  bound_to:
    - "痞根穴/消积穴（断根）"
    - "批判边界"
  tags: [counter-example, tumor, boundary]

- id: ce09
  title: 头部/背部深针误伤
  type: counter-example
  source_chapter: 第二章·针刺的深浅讨论、第四章·肩井穴
  source_quote: |
    "背上扎针，就不可以深针，否则会扎到内脏。扎到肺会引起肺气肿……肩井穴……下太深会伤到肺造成肺气肿，要特别注意。"
  failure_mode: |
    背薄处/肩井深刺伤肺致气肿；头部误以为可深刺入颅。
  mechanism: |
    针刺深度须按解剖（腹深似井、背薄似饼）与部位（头皮头骨之间）控制，
    忽略解剖即造成内脏损伤。
  warning_signs:
    - 背部/胸部深刺
    - 头部穴位试图刺入颅骨以下
  bound_to:
    - "腹深似井背薄似饼"
    - "安全边界"
  tags: [counter-example, depth, safety]

- id: ce10
  title: 进针后乱动致弯针
  type: counter-example
  source_chapter: 第六章·三种背痛诊治（外关穴）
  source_quote: |
    "针下去以后叫他不要动手指头，一动就牵扯到这个针了。若那你告诉他了，他还动，这是他自找的痛。"
  failure_mode: |
    下针后病人活动肢体致针弯（如外关进针后握拳）。
  mechanism: |
    针留于肌肉间，肌肉收缩会弯针；须提前告知患者留针期间保持体位。
  warning_signs:
    - 下针前未嘱患者固定体位
    - 针弯后强行抽拉
  bound_to:
    - "进针与留针管理"
  tags: [counter-example, technique, needle-bending]

- id: ce11
  title: 灸后水泡撕皮留疤
  type: counter-example
  source_chapter: 第一章·隔姜灸
  source_quote: |
    "若灸后起了水泡，就从皮肤旁边用消毒过的针刺一个小洞，把水慢按排出来。不要把皮肤撕掉免得造成疤痕。"
  failure_mode: |
    灸出水泡后直接撕皮，感染留疤。
  mechanism: |
    正确处置：消毒针从旁刺小孔缓慢排水，撒硫磺粉+大黄粉；
    撕皮破坏新生组织并引入感染。
  warning_signs:
    - 灸后水泡直接挑破撕皮
  bound_to:
    - "灸法操作规范"
  tags: [counter-example, moxibustion, wound-care]

- id: ce12
  title: 留针过久/不当留针
  type: counter-example
  source_chapter: 第四章·听宫穴
  source_quote: |
    "这三个穴道不要留针很久，留很久那不是整人吗。起针后，耳朵的耳鸣就好了，但是牙关会开始痛，因为牙开太久了。"
  failure_mode: |
    张口取穴（听宫等）留针过久致牙关酸痛。
  mechanism: |
    留针时长须按部位与姿势适配（开口位久留则下颌疲劳），
    新病短留、久病长留的原则也要结合部位。
  warning_signs:
    - 开口/特殊体位穴道久留
    - 不分新久病一律留 20 分钟以上
  bound_to:
    - "留针时长决策"
  tags: [counter-example, retention, jaw-pain]

- id: ce13
  title: 孕妇乱扎腹部与合谷三阴交
  type: counter-example
  source_chapter: 第六章·怀孕忌针、安胎堕胎与胎位不正
  source_quote: |
    "女人在怀孕的时候，腹部有些穴道是不针的，因为怕有问题。合谷、三阴交也不针。"
  failure_mode: |
    孕期下腹部穴或合谷/三阴交，导致流产风险。
  mechanism: |
    孕期针灸有严格禁忌（补合谷泻三阴交=堕胎、泻合谷补三阴交=安胎），
    不明补泻手法不得触碰；腹部针禁以护胎儿。
  warning_signs:
    - 孕期下针于腹/腰/合谷/三阴交
    - 操作者不明确补泻方向
  bound_to:
    - "孕妇禁针与安胎/堕胎"
  tags: [counter-example, pregnancy, safety]

- id: ce14
  title: 担法滥用（神阙/乳房）
  type: counter-example
  source_chapter: 第四章·担法与截法
  source_quote: |
    "那担法也不能乱用，例如有个太太跑来，我两个乳房痛，不要用担法。……不能担到神阙，神阙是禁针的。"
  failure_mode: |
    把担法（两点中点下针）用于乳房痛、腹腹痛等，触及禁针区（神阙）。
  mechanism: |
    担法只适用于对称性经痛（如背两点痛），须避开禁针/危险区，
    不能机械套用。
  warning_signs:
    - 在两乳/神阙等禁区用担法
  bound_to:
    - "担法与截法"
  tags: [counter-example, technique, contraindication]

- id: ce15
  title: 单针依赖（子午流注滥用）
  type: counter-example
  source_chapter: 第六章·灵龟八法与子午流注
  source_quote: |
    "有的中医呢，想表现很厉害，什么病人来，这个时辰通通扎这个穴道……有的有效，有的没效，没效怎么不讲，对不对?"
  failure_mode: |
    以子午流注单针包治一切（一针走天下），十个病人九个无效。
  mechanism: |
    时间开穴是应急/辅助手段，须配合辨证取穴体系；
    依赖单针=用最简手段掩盖辨证体系缺失，且无效病例不透明。
  warning_signs:
    - 不问病证只按时辰开穴
    - 宣称"一针治百病"
  bound_to:
    - "灵龟八法与子午流注"
    - "辨证选穴决策框架"
  tags: [counter-example, chronobiology, over-reliance]

- id: ce16
  title: 不辨寒热用灸/下针
  type: counter-example
  source_chapter: 第一、六章（灸法、便秘等）
  source_quote: |
    "便秘……寒就是没有蠕动，病人一个星期不上厕所，也不难过。热实呢，一两天不上厕所就很难过。所以寒热看他难不难过，可以知道。"
  failure_mode: |
    不辨寒热虚实即选灸/针/补泻（如热症用灸、寒实症只针不灸）。
  mechanism: |
    灸偏温补、针可清可补；寒实便秘宜灸（天枢关元中脘四花灸），
    热实便秘只针不灸；不辨寒热则方向相反。
  warning_signs:
    - 便秘等症不问寒热直接下针/灸
  bound_to:
    - "不灸的时机清单"
    - "便秘治症方案"
  tags: [counter-example, cold-heat, decision]
