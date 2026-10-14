# 阶段 1 候选 — Glossary（关键概念词典）

> 来源：全书通读，按 glossary-extractor 职责提取。只收核心术语（作者的特定用法）。

- id: g01
  term: 同身寸
  type: term
  source_chapter: 第二章·针灸穴位丈量方法
  author_definition: |
    "把中指头弯起来，这两个横纹头，点跟这个点之间我们定义为一寸……你看的时候要看病人的手，不能看你的手。"
  key_distinction: |
    ≠ 绝对长度单位 — 以病人自身手指为尺，因人而异
    ≠ 只看医生自己手 — 必须用病人的手
    = 三指=两寸、四指=三寸；四肢与经络间取穴用
  why_it_matters: |
    所有穴位定位的基础度量；忽略同身寸会找错穴。
  tags: [term, measurement, core-concept]

- id: g02
  term: 井荣俞原经合（五俞穴）
  type: term
  source_chapter: 第三章·十二正经之井荣俞原经合穴
  author_definition: |
    "所出为井，所溜为荣，所注为俞，所行为经，所入为合。"
  key_distinction: |
    ≠ 单纯的穴位分类 — 是按经气在四肢流注五个阶段（出→溜→注→行→入）的属性序列
    = 阴经木火土金水、阳经金水木火土排列
    = 每个穴的属性决定其在本经中是母穴/子穴/本穴
  why_it_matters: |
    子母补泻、本穴治疗的语法基础；不知道属性就无法选补泻穴。
  tags: [term, five-shu-points, core-concept]

- id: g03
  term: 本穴
  type: term
  source_chapter: 第三章、第四章（各经）
  author_definition: |
    "当这个穴道跟该经属性相同的时候，我们就称之为本穴。"
  key_distinction: |
    ≠ 字典义"本经穴位" — 专指属性与该经五行相同的穴
    = 例：少府（火）是心经（火）本穴、阴谷（水）是肾经（水）本穴
    = 本穴无补泻之分，用于调五行循环
  why_it_matters: |
    本穴治疗法则（调木火土金水循环）与"属性相同"判断的核心。
  tags: [term, five-elements, core-concept]

- id: g04
  term: 母穴 / 子穴
  type: term
  source_chapter: 第三章、第四章（各经）
  author_definition: |
    "虚则补其母，实则泻其子。"
  key_distinction: |
    ≠ 固定穴名 — 按五行生克动态确定：生本经者为母、本经所生者为子
    = 虚症补母穴、实症泻子穴（经络四肢痛）
    = 心包/三焦经的子母随夏至冬至属性切换
  why_it_matters: |
    子母补泻是经络痛取穴的第一法则。
  tags: [term, five-elements, core-concept]

- id: g05
  term: 原穴
  type: term
  source_chapter: 第三章、第四章（各经）
  author_definition: |
    "阳经都有原穴，阴经没有原穴。"
  key_distinction: |
    ≠ 阴经也有独立原穴（现代教材） — 作者：阴经以输为原（无独立原穴）
    = 原穴无虚实之分，虚实皆可治、平补平泻
    = 原络治疗中用原穴（病经）+络穴（表里经）
  why_it_matters: |
    阳经取穴（如大肠原合谷、膀胱原京骨）与虚实皆可治的选穴依据。
  tags: [term, yuan-point, core-concept]

- id: g06
  term: 络穴
  type: term
  source_chapter: 第四章（各经）
  author_definition: |
    "络穴跟原穴一样，虚实都可以治疗。"
  key_distinction: |
    ≠ 只用于表里联络 — 络穴与原穴一样无虚实之分
    = 十五络穴（十二经各一+任督脾大络），表里经沟通点
    = 原络治疗：病经原穴+表里经络穴
  why_it_matters: |
    原络治疗与"虚实皆可"选穴的核心。
  tags: [term, luo-point, core-concept]

- id: g07
  term: 郄穴
  type: term
  source_chapter: 第四章（大杼、梁丘、孔最等）
  author_definition: |
    "郄穴就是消炎，清热，止痛。郄穴是麻醉穴。"
  key_distinction: |
    ≠ 普通穴位 — 专用于急性病、止痛、消炎、止血的"急症要穴"
    = 十六郄穴（十二经+阴跷阳跷阴维阳维）
    = 会郄治疗（八会+郄）主骨伤急症
  why_it_matters: |
    急性痛/出血/骨伤的即时选穴（孔最止痔血、梁丘止胃痛、郄门镇心痛）。
  tags: [term, xi-point, core-concept]

- id: g08
  term: 募穴
  type: term
  source_chapter: 第四章·任脉经穴（各脏腑募）
  author_definition: |
    "任何脏腑都有募穴与俞穴。"
  key_distinction: |
    ≠ 只在背部 — 募穴在胸腹部正面（肺募中府、心募巨阙、胃募中脘、膀胱募中极等）
    = 俞募治疗：正面募穴+背面俞穴同下（内科脏腑病）
  why_it_matters: |
    俞募治疗的一半（正面取穴）与内科病选穴基础。
  tags: [term, mu-point, core-concept]

- id: g09
  term: 俞穴（背俞穴）
  type: term
  source_chapter: 第四章·膀胱经（俞穴各节）
  author_definition: |
    "俞，念输、念俞也可以……原来它的意思是输，在这运输气血。"
  key_distinction: |
    ≠ 五俞穴之"俞" — 专指督脉旁开一寸半/三寸的脏腑背俞穴
    = 肺俞（三椎）、心俞（五椎）、肝俞（九椎）……肾俞（十四椎）
    = 可诊断（压痛点）可治疗（不分虚实寒热），俞募治疗的一半
  why_it_matters: |
    压痛点诊断图谱与俞募治疗的基础。
  tags: [term, back-shu, core-concept]

- id: g10
  term: 八会穴
  type: term
  source_chapter: 第四章·八会穴介绍
  author_definition: |
    "脏会章门，腑会中脘，气会膻中，血会膈俞，骨会大杼，筋会阳陵泉，脉会太渊，髓会绝骨（悬钟）。"
  key_distinction: |
    ≠ 普通穴位 — 八类组织精气汇聚处，按类治之
    = 骨病治大杼、血病治膈俞、腑病治中脘……
  why_it_matters: |
    会郄治疗与按组织类型（骨/血/气/筋）选穴的基础。
  tags: [term, eight-confluent, core-concept]

- id: g11
  term: 天应穴（阿是穴）
  type: term
  source_chapter: 全书贯穿
  author_definition: |
    "阿是穴真正的精神，并不是'啊啊啊！是是是!'，而在这下针的意思。"
  key_distinction: |
    ≠ "哪里痛扎哪里" — 沿经络走行按压找最痛点（压痛点）下针
    = 用于耳针选点、结石痛点、局部硬块灸
    = 压痛点在=病在，消失=病愈（诊断与治疗合一）
  why_it_matters: |
    全书最常用的定位与诊断手段；误读为乱扎会背离辨证。
  tags: [term, ashi-point, core-concept]

- id: g12
  term: 近取穴 / 远取穴
  type: term
  source_chapter: 第四、六章
  author_definition: |
    "在这个器官的周围，选择穴道就是近取穴。在四肢上找就是远取穴。"
  key_distinction: |
    ≠ 只按距离 — 近取治局部（急性/实证/近取无补泻），远取循经调脏腑
    = 近取+远取可配合（腰痛=肾俞近取+委中远取）
  why_it_matters: |
    取穴空间决策的基本二分。
  tags: [term, spatial, core-concept]

- id: g13
  term: 俞募治疗
  type: term
  source_chapter: 第五章·俞募治疗与会郄治疗
  author_definition: |
    "俞募治疗法，大部分都用在内科的……如果是肺经痛，比如痛一个星期，就用子穴……内科病用俞募治疗法。"
  key_distinction: |
    ≠ 通用取穴法 — 专用于内科脏腑病（咳喘、心脏病、胃病、肝病等）
    = 背面俞穴+正面募穴同下（先正面或背面皆可）
  why_it_matters: |
    内科病取穴的第一法则。
  tags: [term, treatment-rule, core-concept]

- id: g14
  term: 会郄治疗
  type: term
  source_chapter: 第四章·大杼穴、第五章
  author_definition: |
    "若有人跑来说，我是五十肩，手抬不起来，它这是病在经络上面，下大杼干嘛?……骨伤……用会郄比较多。"
  key_distinction: |
    ≠ 俞募治疗 — 专用于骨伤/急症/局部痛
    = 八会穴（按组织）+郄穴（止痛消炎）组合
  why_it_matters: |
    骨伤、急性痛、血症的取穴法则。
  tags: [term, treatment-rule, core-concept]

- id: g15
  term: 子母补泻
  type: term
  source_chapter: 第三、四章
  author_definition: |
    "虚则补其母，实则泻其子。"
  key_distinction: |
    ≠ 简单补泻 — 按五行属性定补泻穴（经络四肢痛用）
    = 补井当补合、泻井当泻荣两条特殊规则
  why_it_matters: |
    经络痛取穴第一法则，与俞募/会郄/原络分工。
  tags: [term, treatment-rule, core-concept]

- id: g16
  term: 导引
  type: term
  source_chapter: 第四、五章
  author_definition: |
    "导引就是一个目标，你一下到第十一椎，就等于是告诉身体，我要气血集中在这个点上……"
  key_distinction: |
    ≠ 气功概念 — 针灸选穴法：目标针（引气血到病位）+引导针（子穴/母穴引气血回流）
    = 手麻等症：对侧补泻针+同侧导引针
  why_it_matters: |
    "指哪打哪"的选穴思考法，提高单椎/局部痛疗效。
  tags: [term, qi-guidance, technique]

- id: g17
  term: 病进 / 病退
  type: term
  source_chapter: 第一章·针灸的使用时机
  author_definition: |
    "当病进时，是由四肢末梢往身上走……病退时，就会由身上往四肢走。"
  key_distinction: |
    ≠ 病情轻重 — 专指病势走向（末梢↔躯干）
    = 病进=方案错需改；病退=维持原方案至愈
  why_it_matters: |
    疗效监控与是否改方的第一判据。
  tags: [term, prognosis, core-concept]

- id: g18
  term: 灵龟八法
  type: term
  source_chapter: 第六章·灵龟八法
  author_definition: |
    "从计算干支、时间，知道它的属性以后可决定现在的时辰是开什么穴，这就是灵龟八法。"
  key_distinction: |
    ≠ 子午流注（只看干） — 灵龟八法看干支+时辰
    = 8 穴 4 组（后溪申脉、公孙内关、外关临泣、列缺照海），开组先主后配
    = 应急开穴，任何病先开穴再辨证，一天一次
  why_it_matters: |
    急救/急症/争取问诊时间的特殊开穴法。
  tags: [term, chronobiology, eight-methods]

- id: g19
  term: 指针
  type: term
  source_chapter: 第六章·三关、指针术
  author_definition: |
    "指针就是不用真的下针。"
  key_distinction: |
    ≠ 针刺 — 手指代针（儿科），不破皮
    = 三关辨证（风关→气关→命关）、开/散天河水、耳轮调整眼珠
    = 按寒热方向操作（寒往身推、热往末梢推，男女相反）
  why_it_matters: |
    小儿唯一安全的"针刺"替代手段。
  tags: [term, pediatrics, technique]

- id: g20
  term: 气化（水-火模型）
  type: term
  source_chapter: 第四章·膀胱经、小肠经等
  author_definition: |
    "水一气化起来，膀胱就膨胀……气化则能出焉……所以中医在讲气就是这样子。"
  key_distinction: |
    ≠ 物理气化 — 人体水液被小肠火加热蒸腾为气，供脏腑利用
    = 气化正常=水为身体所用（脚热）；气化不足=寒水（脚冷）滋养病邪
    = "行阳/让水气化"是治肿瘤与养生的总纲
  why_it_matters: |
    全书生理模型核心：治水=治病、脚热=健康。
  tags: [term, physiology, core-concept]

- id: g21
  term: 阴阳（作者用法）
  type: term
  source_chapter: 全书贯穿
  author_definition: |
    "阳就是气，而这个气其实就是水蒸气。……阴就是看得到的东西。像血就是阴，但西医看到血没有看到气。"
  key_distinction: |
    ≠ 抽象哲学概念 — 阳=气/水蒸气/功能（可观察到运动），阴=血/有形营养
    = 阳走六寸阴始走；阴阳平衡=头面凉脚热
    = 阴阳分隔（化疗）=下冷上热、不受针药
  why_it_matters: |
    所有诊断（寒热虚实）与治则（行阳）的理论底座。
  tags: [term, yin-yang, core-concept]

- id: g22
  term: 奇穴（经外奇穴）
  type: term
  source_chapter: 第四、六章（各奇穴）
  author_definition: |
    "有个穴道，叫做痞根穴。顾名思义就是痞块之根。"
  key_distinction: |
    ≠ 正经穴 — 不属十二正经/任督，多为专病专穴
    = 如安眠（失眠）、消渴（糖尿病）、消积（肿瘤诊断）、阑尾（盲肠炎）、
      定喘（气喘）、肝关肠关心关（止痛）、胆石点（胆结石）、眉棱点（眉棱骨痛）
    = 需在正经基础上使用（"学奇穴时正经不能忘"）
  why_it_matters: |
    各治症方案中的特效补充穴。
  tags: [term, extra-point, core-concept]

- id: g23
  term: 回阳九针
  type: term
  source_chapter: 第六章·回阳九针
  author_definition: |
    "'哑门劳宫三阴交，涌泉太溪中脘接，环跳三里合谷并。此是回阳九针穴'……用在过去病人虽死掉，但心口还有温度。"
  key_distinction: |
    ≠ 常规治疗 — 濒死（心口尚温）回阳的最后一搏
    = 九穴按序下针，约第六针可呼吸讲话，可争取半小时交待遗言
  why_it_matters: |
    极端急救手段，需精确取穴；Boundary 注明仅限专业场景。
  tags: [term, emergency, extreme]

- id: g24
  term: 十三鬼穴
  type: term
  source_chapter: 第六章·十三鬼穴
  author_definition: |
    "孙思邈传下来的十三鬼穴，这个十三鬼穴是用在治疗癫症、痫症、狂症用的……要按照顺序下。"
  key_distinction: |
    ≠ 迷信 — 治癫狂痫（痰涎壅塞）的特定序列针法
    = 必须按顺序（人中→少商→隐白……），男左女右、先左后右
    = 正取穴（鸠尾百会+灸申脉照海）无效时使用
  why_it_matters: |
    精神类急症的补充方案；需严谨按序操作。
  tags: [term, psychiatry, sequence]
