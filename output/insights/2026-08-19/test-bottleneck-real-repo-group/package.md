# 受入テストのボトルネック実測 — real-repo group 部分除外は NO-GO (T-989 継続、2026-08-19)

## 経緯

ユーザー依頼「テスト全走のボトルネック解析と、アーキテクチャを効果的に活用するとか並列改善で
早くしてほしい」を受け、[T-989] の残件 (「受入 wall への real-repo group 帰属が未確定」) を
継続調査する dev-wave として実施した。branch `worktree-dev-wave-test-bottleneck`。

## 段1〜2 — 前提事実と codex plan

- 受入全走 (pytest) の直近実走は 2026-08-19 時点で 183〜274 秒 (2026-08-15 実測 128〜149 秒から
  増加傾向、テスト数も 11,159→13,228+ に増加)。
- `orchestrator/tests/conftest.py:287-378` の `REAL_REPO_SERIAL_NODES` (66 node) が
  `--dist loadgroup` により単一 xdist worker へ直列集約される。
- 段2 codex plan (`stage2-plan.md`) は「P3 loop 系 4 node は temporary repo + `nullcontext` により
  静的に real-repo 排他が不要」という改善候補を提示した。

## 段2.5 — 親の追加実測 (方法論に欠陥あり、下記段3で是正)

`python3 tools/run_tests.py --junitxml=... --force-dispatch` を1回計算ノードへ投入し
(`measure-run1-junit.xml`、wall=186.66秒、13,250 passed/95 skipped)、66 canonical node の
duration 単純合計を「T_group」として 114.92 秒 (wall の61.6%) と算出した。
**この算出は誤りだった (下記段3参照)。**

## 段3 — 敵対相談 (2レンズ、いずれも NO-GO)

- **レンズB (実効性、`stage3-lensB-retry.md`)**: 親の「T_group=114.92s」は実は
  各テストの duration 単純合計 (S_group) であり、xdist worker の実際の実行区間ではない。
  「wall-T_group=71.74s が他worker側」という解釈だと makespan=max(T_group,T_other) の定義から
  wall は114.92sになるはずだが実測186.66s — **論理的矛盾**。真の critical path 計測には
  worker_id/nodeid/start/finish を記録する診断が別途必要。また P3 4node の合計を
  親は29.73s (3件) と誤集計しており、正しくは33.055s (4件、同名関数が2ファイルに存在するのを
  見落とした)。n=1測定は統計的にも不足 (paired比較で最低10〜12ペア必要という見積もり)。
- **レンズA (正しさ境界、`stage3-lensA-retry.md`)**: 段2 plan の前提
  「P3 4nodeはtemporary repo+nullcontextで実repoに触れない」自体が refuted。
  `conftest.py:148` の `capture_contract_loader_binding()` が一時repo差し替え(`conftest.py:180`)
  より前に実worktree rootへのGit検証・25 blob読み出しを行う。歴史的には D63導入時 (2026-07-19)
  この4nodeは「実ccbench writer」として分類されており、除外は既存裁定の単純適用ではなく
  新規の resource-closure 再分類にあたる。`--dist loadgroup` は同一group内の同一worker集約は
  保証するが、除外後のitemがreal-repo groupと同時実行しない保証はない。独立oracle
  (`test_real_repo_serialization.py`) の複数箇所が66node固定literalを持ち追随更新が必要。

## 過去との整合 — D258 (2026-08-10, T-692) と D358 (2026-08-13) が同じ路線を既に閉じていた

- **D358「real-repo の排他は単一 worker 直列化のまま維持する」**が、排他機構を丸ごと無効化した
  診断走行 (`--dist load`) でも wall=116.63秒 (予測約80秒に遠く及ばず)、worker数 24/32/48 の差も
  run間変動に埋もれる、と実測済みで**「排他機構の変更で受入を速くする路線を閉じる」**と裁定済み。
- **D258 (T-692)** は 2026-08-10 時点 (7,746 test) で real-repo group 直列和が critical path 下界
  であることを実測確定した一方、恒久策は「分配側に無い」(真因は T-080 receipt 解決の
  O(commit数) コストで、1走に構造的に2回払う) と結論していた。

今回の調査 (2026-08-19、13,228+ test) は、方法論の欠陥はあったが、**独立に同じ方向の結論
(real-repo group の部分的な組み替えでは wall は動かせない) へ収束した。**

## 結論・次の一手

- **P3 4node除外は実装しない (NO-GO、両レンズ一致)。**
- 真の critical path (worker span) を測るには `conftest.py:669-677` 相当の位置に一時診断
  (worker_id/nodeid/start/finish の記録) を追加する必要がある。D358/D258の実測density を踏まえると、
  このコストをかけてもなお「分配側に恒久策は無い」という同じ結論に戻る可能性が高い。
  **本 wave ではこの診断の実装を推奨しない** (投資対効果が不明かつ D358 が同種の実験で
  否定的な結果を既に得ている)。
- テスト全走時間そのものの伸び (128〜149s→183〜274s、2026-08-15→2026-08-19) は本 wave の
  scope外。テスト数増加との交絡が未分離であり、[[test-time-regression-rule]] の監視対象として
  別途フォローが要る。

## 一次資料

- brief/handoff: `/work/SFC/tanab/dev-wave-jobs/dev-wave-test-bottleneck/{brief.md,handoff.md}`
- 段2 plan: `/work/SFC/tanab/dev-wave-jobs/dev-wave-test-bottleneck/stage2-plan.md`
- 段3: `/work/SFC/tanab/dev-wave-jobs/dev-wave-test-bottleneck/stage3-lensA-retry.md`,
  `stage3-lensB-retry.md`
- 実測 junit: `/work/SFC/tanab/dev-wave-jobs/dev-wave-test-bottleneck/measure-run1-junit.xml`
- D258: `docs/decisions.md:11855`、D358: `docs/decisions.md:15613`
