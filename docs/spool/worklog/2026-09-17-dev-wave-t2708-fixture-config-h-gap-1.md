---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2708-fixture-config-h-gap
seq: 1
title: [T-2708] t080 fixture の config.h 取り込み漏れの影響を計算ノードで実測した — 取り込むと fixture の可視集合は期待集合と完全一致 (差 1 → 0)・判定不変・path 名指しの取り込みは 29 ms・実 repo の ignore 一致集合を写す一般解は列挙 4.8 秒で不採用・scan 増分は分離不能 (対差中央値 −70 ms、統計上限 +157 ms/scan)、採否はユーザー裁定へ (docs + 計測成果物、branch worktree-dev-wave-t2708-fixture-config-h-gap、実装差分ゼロのため変異 matrix 免除)
---

## 本文

- ユーザー依頼は「t080 fixture が実 repo の tracked file `orchestrator/tests/fixtures/sort_swo_masstree/config.h` を
  取り込めていない (同 dir の `.gitignore` の `/config.h` が `git init` からの `git add -A` で優先される) 件の影響を測る。
  取り込んだ場合の忠実性の増分と所要の増加を実測し、採否を裁定パッケージで返す。着手直前の local main から fresh worktree
  を作る。実装差分は原則ゼロ (計測 probe は repo へ入れない)。T-2710 と同時に投げるなら起動時に編集面重複検査を行う。
  規律 2 を緩めない。本題の影響測定だけ」。**本 wave では実装しない。** 一次資料は
  `output/insights/2026-09-17/t2708-fixture-config-h-gap/` (段 1 brief・段 2 plan・段 3 の 2 レンズ・段 4 裁定・
  段 5/6 の子報告・probe 逐語・本走 2 回の JSON)。設計判断は {{D:t080-fixture-config-h-force-add}}、
  run1 の失敗は F351 の再発として追記した。
- **同型の穴は config.h の 1 件だけ (静的 + 動的)。** 実 repo で tracked かつ ignore 一致は 419 件、うち 418 件は root
  `.gitignore:25` 由来で fixture は root `.gitignore` を複製しないので一致側。計算ノードの実測でも、構築規則で射影した期待集合
  E (25,182 件) と現行 fixture の index (25,181 件) の差はちょうど config.h で、取り込み後の index は E と完全一致した。
- **判定は不変。** config.h に三軸 key は 0 件、`_live_scan_sha256` は `search` を含まず、`file_count` は受理集合外
  (production 注記)。動的にも 22 対すべてで A/B の semantic report と live scan sha256 が一致し、`file_count` だけ 25,568 → 25,569。
- **所要 (計算ノード bnode028、request 4055.nqsv、Elapse 1,105 秒)。** path 名指しの `add -f` は 28.7 ms (反復中央値)。
  実 repo の `ls-files -ci` 集合 419 path を写す一般解は一連 5.0 秒で、うち実 repo 側の列挙が 4.8 秒 (Lustre 上で tracked
  27,022 件に ignore 規則を照合する)。scan 1 回は 18.4 秒 (fixture 25,568 file)、A/B 対差の中央値は −70 ms、IQR 558 ms、
  順序別中央値は AB −325 / BA +150 ms (2 走目が速い順序効果が支配的) で、1 file の増分は分離できなかった。
  統計上限 +157 ms/scan (13 scan で約 2.0 秒)、per-file 換算の期待値 0.72 ms/scan (13 scan で約 9 ms)。
- **裁定パッケージ (ユーザー裁定へ)。** (a) path 名指しの `add -f` 1 行 + membership 検査 1 本 (親の推奨、費用 29 ms +
  scan 増分、効果は E と完全一致)、(b) 現状維持 (成果物影響なし)、(c) 一般解は列挙費用と非コピー対象の扱いから不採用
  (親裁定)。費用許容値は既存裁定に無く、レンズ B の「critical path +1 秒以内」を提案値として置いた。
- **段 3 (2 レンズ、23 所見) が親 brief を 5 点訂正した。** 実測環境 login node → 計算ノード (runbook §7.0.0)、「ms 級」は
  未測定、「一般解は 1 手・件数非依存」は過大、DW-G05 の「レポート・台帳は変わらない」は実 repo の既存成果物に限る
  (fixture の `file_count`・basis OID・receipt は変わる)、「untracked 0 件」は非 ignored に限る。棄却した所見は無い。
- **run1 (request 4025.nqsv、6 秒 rc=1) は growth hold の import 拒否で空費した。** held module
  `test_s8b_oracle_driver.py` は pytest 外の import を `GrowthTestHoldBypassRefused` で必ず拒否する (F351 と同型)。解除 env は
  使わず、probe の内側で `pytest.main([held module, "--collect-only", "-k", 不一致名])` を呼び `pytest_sessionstart` で
  完全修飾名を import する形へ fix 子が直した。段 2 plan と段 3 の 2 レンズはこの制約を見落とした。
- scope 外で残る (裁定パッケージ候補、insight §5): copytree の名前除外・basis 上書き・submodule の known pin・receipt/draft
  除外が fixture と実 repo の scan 集合を別方向にずらす構造 (現在の欠落は反証なし / 判定不能)、発行経路 (13 scan) の e2e wall の
  A/B。
- 段 8 (自己改善): 候補 2 件を契約で裁定。(a) 「held test module の helper を pytest 外の probe から使うと import が
  拒否される」は F351 の再発追記で顕在化させ、親の memory に held module の項を足す。(b) 段 2 plan / 段 3 レンズの prompt に
  「module 末尾の guard binding (`enforce_held_functions`) の有無を確認せよ」を入れる手順は親の memory へ。いずれも
  `docs/dev-wave/` へは足さない (予算満杯で、同型の docs 側発火実績は F351 と本件の 2 例、機械代替なし → D271 の新規 L2 節の
  条件は満たすが本 wave は実装差分ゼロの調査 wave なので裁定パッケージ候補に留める)。
- 工数: codex 子 5 本 (plan 1、consult 2、author 1、fix 1、全段 `gpt-6-astra`)。親の実走: selftest 1 (login)、本走 2 回
  (計算ノード generic dispatch)。probe は repo に残さず `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2708-fixture-config-h-gap/`
  へ保全 (sha256 `8c8731cd2b9a4974…`、415 行)。

## 次の一手差分

### 更新

- [T-2708] **P2・ユーザー裁定待ち**: 影響を計算ノードで実測し裁定パッケージを返した
  (`output/insights/2026-09-17/t2708-fixture-config-h-gap/README.md` §4)。取り込むと fixture の可視集合は期待集合と完全一致
  (差 1 → 0)、判定不変、path 名指しの取り込み費用 29 ms、scan 増分は分離不能 (統計上限 13 scan で約 2 秒、per-file 換算 9 ms)。
  一般解 (列挙 4.8 秒) は不採用。残るのは (a) path 名指しの `add -f` 1 行 + membership 検査 1 本を別 wave (Codex author、
  変異事前登録 = 取り込み行削除で新規 test 赤) で入れるか、(b) 現状維持か、のユーザー裁定。親の推奨は (a) だが成果物影響は
  ゼロで優先度 P3 相当。
  base: 1dcb019251642587c515c60654b9e15135317b9b2fe1ad9eae3f846c369e80c5
