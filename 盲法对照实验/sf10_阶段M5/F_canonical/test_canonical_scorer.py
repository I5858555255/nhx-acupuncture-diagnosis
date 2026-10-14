# -*- coding: utf-8 -*-
"""test_canonical_scorer.py — canonical_scorer 单元测试（M5 阶段F）。

覆盖：
  1. 点级指标公式（TP/FP/FN、R/P/F1/Jac 的边界值）
  2. 宏平均 / 微平均口径
  3. 复合穴展开（膝五针 / 三皇穴 / 开四关）
  4. 透刺端点（X透Y 两端都计、两端都命中时精确率=1）
  5. 别名归并（耳穴等）
  6. gold 去重
  7. 空预测 / 空 gold
  8. 路径解析（脚本位置推导 + 显式 root）
运行：python -m unittest test_canonical_scorer -v
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # 盲法对照实验目录
sys.path.insert(0, str(ROOT / "benchmark_v2"))

import canonical_scorer as cs  # noqa: E402


class TestPerCaseMetrics(unittest.TestCase):
    """点级指标公式：TP/FP/FN 与 R/P/F1/Jac。"""

    def test_tp_fp_fn_counts(self):
        G = {"合谷", "太冲", "足三里"}
        P = {"合谷", "太冲", "内关", "列缺"}
        m = cs.per_case_metrics(G, P)
        self.assertEqual(m["tp"], 2)   # 合谷、太冲
        self.assertEqual(m["fp"], 2)    # 内关、列缺
        self.assertEqual(m["fn"], 1)   # 足三里漏
        self.assertAlmostEqual(m["recall"], 2 / 3)
        self.assertAlmostEqual(m["prec"], 2 / 4)
        expect_f1 = 2 * (2 / 3) * (2 / 4) / ((2 / 3) + (2 / 4))
        self.assertAlmostEqual(m["f1"], expect_f1)
        self.assertAlmostEqual(m["jac"], 2 / (2 + 2 + 1))

    def test_perfect_hit(self):
        G = {"A", "B"}
        m = cs.per_case_metrics(G, {"A", "B"})
        self.assertEqual((m["tp"], m["fp"], m["fn"]), (2, 0, 0))
        self.assertEqual(m["recall"], 1.0)
        self.assertEqual(m["prec"], 1.0)
        self.assertEqual(m["f1"], 1.0)
        self.assertEqual(m["jac"], 1.0)

    def test_zero_tp_f1_is_zero(self):
        """tp=0：F1=0.0（不是 None），recall=0，prec=0，jac=0。"""
        G = {"A", "B"}
        P = {"C", "D"}
        m = cs.per_case_metrics(G, P)
        self.assertEqual((m["tp"], m["fp"], m["fn"]), (0, 2, 2))
        self.assertEqual(m["recall"], 0.0)
        self.assertEqual(m["prec"], 0.0)
        self.assertEqual(m["f1"], 0.0)
        self.assertEqual(m["jac"], 0.0)

    def test_empty_prediction(self):
        """空预测：G 非空。prec=None，recall=0，F1=0.0，jac=0.0。"""
        m = cs.per_case_metrics({"A", "B"}, set())
        self.assertEqual((m["tp"], m["fp"], m["fn"]), (0, 0, 2))
        self.assertEqual(m["recall"], 0.0)
        self.assertIsNone(m["prec"])
        self.assertEqual(m["f1"], 0.0)
        self.assertEqual(m["jac"], 0.0)

    def test_empty_gold(self):
        """空 gold：G 空。recall=None；P 非空时 prec=0、F1=0.0、jac=0.0。"""
        m = cs.per_case_metrics(set(), {"A", "B"})
        self.assertIsNone(m["recall"])
        self.assertEqual(m["prec"], 0.0)
        self.assertEqual(m["f1"], 0.0)
        self.assertEqual(m["jac"], 0.0)

    def test_both_empty(self):
        m = cs.per_case_metrics(set(), set())
        self.assertIsNone(m["recall"])
        self.assertIsNone(m["prec"])
        self.assertEqual(m["f1"], 0.0)
        self.assertEqual(m["jac"], 0.0)


class TestCompositeExpansion(unittest.TestCase):
    """复合穴展开：组穴只展开成组成穴，不保留父级组名。"""

    def test_kiwu_zhen(self):
        self.assertEqual(
            cs.normalize_units(["膝五针"]),
            {"鹤顶", "内膝眼", "外膝眼", "阴陵泉"},
        )

    def test_sanhuang(self):
        self.assertEqual(
            cs.normalize_units(["三皇穴"]),
            {"阴陵泉", "地机", "三阴交"},
        )

    def test_kai_siguan(self):
        self.assertEqual(cs.normalize_units(["开四关"]), {"合谷", "太冲"})

    def test_x_plus_y(self):
        self.assertEqual(cs.normalize_units(["公孙+内关"]), {"公孙", "内关"})

    def test_group_not_kept_as_point(self):
        """组穴名本身不进入规范集。"""
        self.assertNotIn("膝五针", cs.normalize_units(["膝五针"]))
        self.assertNotIn("开四关", cs.normalize_units(["开四关"]))


class TestTransmissionNeedling(unittest.TestCase):
    """透刺：X透Y 两端都计；两端都命中时精确率=1（不超 100% 契约）。"""

    def test_ends_counted(self):
        self.assertEqual(cs.normalize_units(["合谷透后溪"]), {"合谷", "后溪"})

    def test_both_ends_hit_precision_one(self):
        P = cs.normalize_units(["合谷透后溪"])
        G = {"合谷", "后溪"}
        m = cs.per_case_metrics(G, P)
        self.assertEqual(len(P), 2)
        self.assertEqual(m["tp"], 2)
        self.assertEqual(m["prec"], 1.0)
        self.assertEqual(m["f1"], 1.0)

    def test_only_one_end_hit(self):
        P = cs.normalize_units(["合谷透后溪"])
        m = cs.per_case_metrics({"合谷"}, P)
        self.assertEqual(m["tp"], 1)
        self.assertEqual(m["fn"], 0)   # gold={合谷} 全中
        self.assertEqual(m["fp"], 1)   # 后溪是误报


class TestAliasNormalization(unittest.TestCase):
    """别名归并：耳穴等。"""

    def test_ear_aliases(self):
        self.assertEqual(cs.normalize_units(["耳胆石点"]), {"耳胆点"})
        self.assertEqual(cs.normalize_units(["耳针胆点"]), {"耳胆点"})
        self.assertEqual(cs.normalize_units(["埋耳针<胆>"]), {"耳胆点"})
        self.assertEqual(cs.normalize_units(["心脏点"]), {"耳心点"})
        self.assertEqual(cs.normalize_units(["耳针埋心的压痛点"]), {"耳心点"})
        self.assertEqual(cs.normalize_units(["耳针肾膀胱区压痛点"]), {"耳肾点"})

    def test_point_aliases(self):
        self.assertEqual(cs.normalize_units(["肩禺"]), {"肩髃"})
        self.assertEqual(cs.normalize_units(["肩臑"]), {"肩髃"})
        self.assertEqual(cs.normalize_units(["三里"]), {"足三里"})
        self.assertEqual(cs.normalize_units(["膀胱募"]), {"中极"})

    def test_procedure_note(self):
        self.assertEqual(cs.normalize_units(["灸关元"]), {"关元"})
        self.assertEqual(cs.normalize_units(["委中放血"]), {"委中"})
        self.assertEqual(cs.normalize_units(["天应隔姜灸"]), {"天应"})


class TestGoldDedup(unittest.TestCase):
    """gold/预测去重：同一穴多次出现只计一次。"""

    def test_duplicate_units_collapse(self):
        P = cs.normalize_units(["合谷", "合谷", "开四关", "太冲"])
        # 合谷 x2 + 开四关(合谷,太冲) + 太冲 -> {合谷,太冲}
        self.assertEqual(P, {"合谷", "太冲"})

    def test_gold_set_dedup_in_metrics(self):
        G = {"合谷", "太冲", "合谷"}          # 入参 set 已去重
        m = cs.per_case_metrics(G, {"合谷"})
        self.assertEqual(len(G), 2)
        self.assertEqual(m["recall"], 0.5)


class TestMacroMicro(unittest.TestCase):
    """宏平均 / 微平均口径。"""

    @staticmethod
    def _make_per():
        """造两案：案1 全中、案2 半中。"""
        per = {}
        per["c1"] = {"new": {"v": cs.score_prediction({"A", "B"}, ["A", "B"])}}
        per["c2"] = {"new": {"v": cs.score_prediction({"A", "B", "C"}, ["A"])}}
        return per

    def test_macro_recall(self):
        per = self._make_per()
        r = cs.macro_metric(per, "v", "main", "recall", ["c1", "c2"])
        self.assertAlmostEqual(r, (1.0 + (1 / 3)) / 2)

    def test_macro_skips_none(self):
        per = self._make_per()
        # 案1 prec=1.0；案2 pred={A} 非空 prec=1/1=1.0；宏=1.0
        p = cs.macro_metric(per, "v", "main", "prec", ["c1", "c2"])
        self.assertEqual(p, 1.0)

    def test_micro_recall(self):
        per = self._make_per()
        r = cs.micro_metric(per, "v", "main", "recall", ["c1", "c2"])
        # TP=2+1=3；FN=0+2=2；3/5
        self.assertAlmostEqual(r, 3 / 5)

    def test_micro_prec(self):
        per = self._make_per()
        p = cs.micro_metric(per, "v", "main", "prec", ["c1", "c2"])
        # TP=3；FP=0；3/3=1.0
        self.assertEqual(p, 1.0)

    def test_micro_jac(self):
        per = self._make_per()
        j = cs.micro_metric(per, "v", "main", "jac", ["c1", "c2"])
        # TP=3,FP=0,FN=2 -> 3/5
        self.assertAlmostEqual(j, 3 / 5)

    def test_macro_average_empty(self):
        self.assertIsNone(cs.macro_average([]))
        self.assertIsNone(cs.macro_average([None, None]))

    def test_micro_all_none_when_no_hits(self):
        per = {"c1": {"new": {"v": cs.score_prediction({"A"}, ["B"])}}}
        self.assertEqual(cs.micro_metric(per, "v", "main", "f1", ["c1"]), 0.0)


class TestPathResolution(unittest.TestCase):
    """路径解析：默认从脚本位置推导；显式 root 覆盖；gold 文件可读。"""

    def test_default_root_points_to_project(self):
        self.assertEqual(cs.DEFAULT_ROOT.name, "盲法对照实验")
        self.assertTrue(cs.DEFAULT_ROOT.is_dir())
        self.assertTrue((cs.DEFAULT_ROOT / "benchmark_v2" / "normalize_acupoints.py").is_file())

    def test_gold_pkl_exists(self):
        self.assertTrue(cs.gold_pkl_path().is_file())

    def test_explicit_root(self):
        r = cs.resolve_root(str(ROOT))
        self.assertEqual(r, ROOT)

    def test_load_gold_roundtrip(self):
        results, case_ids, summary = cs.load_gold()
        self.assertEqual(len(case_ids), 93)
        self.assertIn("chain_map", summary)
        self.assertIn("gold_members", results[case_ids[0]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
