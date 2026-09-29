# 段 6 fix 裁定 2 — smoke1 (計算ノード) の条件 gate 拒否

2026-09-30 00:55 JST / 親。smoke1 = 36580.nqsv (bnode005、tip 297ad1dee、Elapse 101 s、rc 1)。

## 事実 (完全な stderr: vhb-m0/output/pegasus-dispatch/acd18b3eecc5db9b05325e3b37ce8da9/izdw-acd18b3eec.e36580)
- perf 5 binary (K0/1/2/4/8、WL=1) は gate を通り build できた。build 秒 8.8〜12.5、dependency 17.0。sizeof(Tuple) = K0 256、K1 256、K2 320、K4 320、K8 384 byte。
- COUNT の build で gate が拒否: `CICADA_VHASH_COUNT` の runtime-meaning が red、reason `compile-time-branch-selection-mismatch`、expected `requested=(20,20),default=(0,20)`、observed `requested=(8, 8),default=(0, 8)`。

## 裁定
- real・本 wave 帰属。COUNT の `#if CICADA_VHASH_COUNT` 20 site のうち 12 が `#if CICADA_VHASH_K` の内側にあり、gate の probe は K 未定義で owner TU を前処理するので見えない (記憶: 非活性 #if の内側は観測できない、F139 型の再発)。
- 直し方: md_6 の先例 (CICADA_FWD_COUNT の companion `CICADA_FWD_ENABLE=1`) と同じく、`CICADA_VHASH_COUNT` の DefineSpec に `companion_defines=(("CICADA_VHASH_K", "1"),)` を付ける。gate の companion は spec 固定で probe だけに効く (condition_meaning_gate.py の `_effective_companions`)。patch は変えない。test_condition_meaning_gate.py の該当 DefineSpec の pin を合わせる。
- 限界 (一次資料に書く): COUNT の意味の証拠は K=1 の文脈で取ったもの。K=0 (stock) の COUNT build と K=2/4/8 は、同じ分岐の選択を別の文脈で使う (K=2/4/8 の meaning は U3 報告どおり未確立)。COUNT は診断計器で性能値に使わない。
- 同じ型の見落としが他に無いか: WL と K は smoke1 で gate を通った。trace / broken build は smoke1 で未到達 (COUNT の後)。
- 変異: M10 = COUNT の companion を外す → gate の登録 test (companion の pin) が赤。
- fix 単位: F3 (作業木 vhb-u1、F1 の後に続けて): orchestrator/campaign/condition_meaning_gate.py、orchestrator/tests/test_condition_meaning_gate.py。
