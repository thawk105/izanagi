---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2344-closure-stage
seq: 1
title: [T-2344] enforcement source closure を 63 → 85 path へ 1 段進めた — 現行 63 の直接 import 先 22 本を収載し、exact-63 を歴史閲覧 grammar として収載、scope 文言と独立 literal を同 commit で追随 (コード + test、branch worktree-dev-wave-t2344-closure-stage、Codex author 3 commit、変異 11/11 KILLED + 対照 1 SURVIVED、受入 attempt 1 赤 1 件 → fix 2 → 最終 tip に再投入)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight 冒頭) の範囲で 1 wave。裁定 = D1075 / D1884 (段階実装の次段、範囲は wave が決める)、
  D1653 / D1770 (旧 grammar は歴史閲覧限定)、D2081 (文言の形式)。一次資料は `output/insights/2026-09-20/t2344-closure-stage1/README.md`
  (brief・実測・plan・相談 2 本・裁定・実装子 2 本・レビュー 2 本・fix・変異台帳・probe の逐語)。専用 handoff は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/HANDOFF.md`。
- 起点 local main `f94b61fc8` (着手直前、fresh worktree)。全段構成 (受理集合が変わり正しさ防壁に触るため DW-C00 の独立敵対検証子): 段 2 plan 1、
  段 3 2 レンズ (real 9 / refuted 8)、段 5 author (v1 は親 prompt の編集許可が plan より狭く即停止・変更 0、v2 が 8 file)、段 6 レビュー 2 + fix 1。
- **段 1 の実測で引数の前提を更新した:** 着手時は収載 63 / 発見 163 / 未収載 100、発行器起点を含む和 173 / 未収載 110 (引数の 165 / 102 は 09-09 の値)。
  記録済み exact-63 campaign.lock は走査 19 root で 20 本 (B-10 formal 6・A-2 2・A-6 1・B-7 3 ほか)、20 本の wire key 列と記録 commit 9 件の宣言順を exact 照合。
- **段の選択 (裁定 {{D:closure-stage-by-import-layer}}):** 現行 63 起点の 1 段目 22 本を末尾に sorted 順で足し exact 85。exact-63 の歴史 grammar を同 commit で収載
  (T-2483 と同型)。scope 文言は「curated exact 85 path; 2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 163 module、うち収載 85 / 未収載 78」。
  「推移閉包」「source-bound」は名乗らない。
- 段 3 の主な real: (A) subset 変異は `KeyError` 赤で単一理由でない → 登録から外す、「63 を現行分岐へ流すと拒否 test が赤」は逆 (歴史正例が赤)、
  「bytes が変わる commit は受理を変えない」は条件不足 (D1163 は記録 E1 と現在 E1 の差だけ)。(B) 85 / 163 / 78 を着手 commit の実測と書くと偽 (must-fix → 85 seed で再測し文言を訂正)、
  発行器の穴は残る ((P1) の却下理由を訂正)、「63 key 20 本」≠ exact grammar (→ exact 照合)、最新 checkout での certified 再解析運用 (T-1998 再検証の実例) は
  「記録 commit か HISTORICAL_RAW」では救えない (→ 開示 + 裁定パッケージ)、受入増分「約 3 秒」は 63 件分だけ。
- 段 6 レビュー A / B は独立に同じ唯一の real (test_t671 の git timeout 期待値 630 = 10 秒 × 63 の追随漏れ 5 か所) を出し NO-GO → fix 1 で 850 → 焦点走 f2 3115 passed / 0 failed。
  production 差分の裁定違反・certified への流入・過剰・名乗り拡大はいずれも refuted。
- **受理集合の変化 (開示):** tuple 前進後の checkout では記録済み exact-63 campaign (20 本) が certified の decode 段で拒否され (実 lock 代表 4 件で実測: 通常 decoder と
  CERTIFIED_ACCEPTANCE の epoch API が exact key 集合で拒否)、HISTORICAL_RAW では 20 / 20 が歴史型・旧 63 scope・E1 で読める (bytes 不変)。最新 consumer での certified
  再解析は失われる。新 22 本は capture の clean committed 要求の対象 (K2 launcher・受入は既に tracked dirty を拒否するので本走は不変)。
- 変異 (DW-M01〜M08): 事前登録 4 群 (収載追加の回帰 / 歴史可読性 / 未知 grammar 拒否 / certified 隔離) の 11 変異 + comment だけの対照 M0。probe 走 (runner 5 file) で **M0 が `test_layer3_report.py` の accepted report 系 5 node を落とし drift 核と判明** (実 repo の live binding を capture、F358 の型) → final 走は runner から layer3 を外し (layer3 の追随は焦点走 f2 の緑が担保)、期待 node = 観測 − drift 核 − layer3 で登録。**final: 11/11 KILLED (期待 node 完全一致、M1 271 / M2 182 / M3 2 / M5 65 / M7 67 / M8 4 / M9 63 / M10 (両層) 4 / M11 2 / M12 1 / M13 2)、M0 SURVIVED**。
- 受入・検査: 焦点走 f1 (3112 passed / 3 failed = 上の追随漏れ) / f2 (3115 passed)、全史 provenance 監査 12061 件違反なし、実 lock probe A 20/20・B 4/4・C 4/4、
  受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir (`acceptance-receipt-*.json`) と land の記録が持つ (件数は本文へ書かない)。
- 裁定パッケージ候補 (insight §8): (1) 次段の順序 — 発行器 6 本 + 発行器起点 10 本を先にするか、tuple 起点の 2 段目 23 本か。(2) 記録済み exact-63 成果物の最新 consumer での
  certified 再解析を続けるか — (a) 修正済み exact-63 解析 checkout の保存、(b) 新 grammar で再測定、(c) 現状維持。
- 言わないこと: 推移閉包が閉じた・certified 経路が source-bound (未収載 78、和で 88 が残る)・20 本すべてで certified 拒否を実走した (代表 4 件)。
- 事故: 段 5 author v1 の即停止 (親 prompt の編集許可の括弧書きが plan §4 より狭かった。2 分の損失、変更 0)。
- **受入全走 attempt 1 (tip 43c32588b) は赤 1 件で停止**: `test_b10_backoff_static_tail_formal.py::test_formal_loader_rejects_real_exploration` が実在の exploration campaign (exact-63) を certified 経路に渡し `not formal` を期待 → decode 段 (exact key 集合不正) で拒否されて不一致。本 wave 起因 (受理集合の変化そのもの、production は D1653 どおり)。fix 2 で主張を「実 exact-63 は decode 段拒否」と「not formal は現行 grammar の合成 campaign で検査」の 2 node に分けて残し、単独走緑。段 6 レビュー 2 本と焦点走 3 本が取り逃したのは、この test が変更 symbol を参照せず実 外部 root の記録済み campaign を読むため (F474 の再発として記録、対処は memory)。受入は最終 tip へ再投入。
- 工数: codex 9 本 (plan 1・consult 2・author 2・review 2・fix 2、gpt-6-astra / medium)、計算ノード job = 焦点走 4 (f1 fix 前・f2 fix 後・f3 merge 後 + DW-O26 改訂版の inventory 4 群・f4 fix 2 後の単独走) + 変異 probe 13 + final 13 + 受入 2 回。

## 次の一手差分

### 更新

- [T-2344] **P2・裁定済み (D1884) → 段階実装 1 段完了 (63 → 85、{{D:closure-stage-by-import-layer}})、次段と再解析の扱いは裁定待ち**: 現行 63 起点の
  1 段目 22 本を収載し exact 85 にした。exact-63 は歴史閲覧 grammar として収載済み。着手時 (2026-09-20、f94b61fc8) の発見集合 163 に対し未収載 78、
  発行器起点を含む和 173 に対し 88 が残り、「certified 経路が source-bound である」は推移閉包の意味では引き続き名乗らない。裁定待ち 2 件
  (一次資料 `output/insights/2026-09-20/t2344-closure-stage1/README.md` §8): (1) 次段の順序 = 発行器 6 本 (+ 発行器起点にだけ居る 10 本) を
  先に収載するか、tuple 起点の 2 段目 23 本か。推奨は発行器先行 (D1884 が名指しした穴に直接効く)。(2) 記録済み exact-63 成果物 20 本の
  「最新 consumer での certified 再解析」を続けるか — (a) 修正済み exact-63 解析 checkout の保存、(b) 新 grammar で再測定、(c) 現状維持
  (HISTORICAL_RAW と記録 commit)。推奨は (c) を既定に (a) を B-10 formal / A-2 / B-7 に限って用意する。tuple を動かす変更単位には直前 grammar の
  歴史収載を同 commit で含める。
  base: 4b37cf0443d771fd8fd23ce130e3c34c68de0a73431f64abba91f66b75580adc
