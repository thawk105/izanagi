---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: worktree-dev-wave-b8-longrun-verify-prereg
seq: 1
title: B-8 (種を変えた長時間実行による最終候補の検証) の事前登録 v1 を作った — 対象は 2 案 (S-1 最終候補 g_rl / g_rt を推奨)、種は独立 process の自己シード、長時間は 3 s より長い extime を校正で決める (docs のみ、branch worktree-dev-wave-b8-longrun-verify-prereg)
---

## 本文

- 依頼の範囲だけで 1 wave: B-8 の事前登録 v1 を docs-only で起草し land まで。発効・試走・本走・runner 実装は含めず、行っていない。
  台帳 ID 未起票 (出所 = 論文ストーリー 2026-09-20 §8 B-8「未取得」と D2160 の仕分け)。着手時 local main `947fd160a` から
  fresh worktree、記録前に `d4af98f15` (T-2610 docs wave の land) を ff-only で取り込み。実装面差分ゼロ。
- 成果物 = `docs/b8-final-candidate-longrun-verify-preregistration.md` (v1、未発効) と `docs/README.md` の 1 bullet。設計判断は
  {{D:b8-longrun-verify-prereg-v1}}。一次資料の逐語・裁定・Codex 逐語は `output/insights/2026-09-20/b8-longrun-verify-prereg/README.md`。
- 段 1 実測: S-1 (iv 付属) の対象 = g_rl (balanced / read-heavy) / g_rt (write-heavy)、gate 述語は `known_axes_freeze.json` の逐語、
  S-1 の 24 verify 本走は S-1 直接比較 report の記述と検索範囲では未実施。S-1 freeze は pin 前進で `IZANAGI_FREEZE_HOLD` 中だが
  variant の build は凍結の照合を経由しない。現行 pin への trigger-gating template patch は `patch -F0 --dry-run` で transaction.cc の
  全 hunk が当たる (厳密適用・build・identity は未実測)。CCBench の乱数は `Xoroshiro128Plus::init()` が `std::random_device` の 32 bit
  値 1 つから作り、`YcsbWorkload` は worker thread ごとに構築 (member 既定 constructor と自身の constructor で二重 init、後者が上書き)、
  seed の CLI flag は無い。D2160 の校正で 6 s は 3 workload とも完走 (read-heavy 808〜864 s / 80〜86 GiB)、10 s は balanced SIGKILL・
  write-heavy hard timeout。並行 wave `dev-wave-verifier-capacity` (13:16 開始) とは編集面が交差せず、本書は同 wave の成果を前提条件に
  せず校正規則で吸収する。
- 軽量版 (段 2・3 省略、DW-C00)。段 4 で brief の P1〜P5 をそのまま採用: 対象は案 A 推奨・案 B 代替で択一は発効時、種は S-1 層 2 の
  登録定義、長時間は extime ≥ 6 s を校正 {6, 10} s で決め 3 s へ丸めない、費用は案 B 6 s の算術のみ、判定は D2160 項 3・5 を継承。
  統計文 4 つ (1−εⁿ、長さ 2 倍 = 露出 2 倍、累計 = 単走、自己シードは全部異なる) は反例を作って書かず、仮定として登録した。
- 段 6 独立レビュー 1 本 (gpt-6-astra / medium、12 call、288 秒): must 2 (失格と pass の排他性、発効束と校正の循環)、should 4
  (保全容量の母集団 = 3 s 54 走 + 6 s 6 走 + 10 s 4 走、統計文の反例と確率表現、不在断定の確認範囲、予算段下げと適格集合の接続)、
  nit 1 (件数内訳・参照・per-verify 値)。全件 real・採用、親が docs を直した (`rulings-stage6.md`)。焦点再レビュー 2 巡 (6 call・152 秒、5 call・76 秒): 1 巡目は closed 2 / partial 5 で新規 must 1 (失格条件と
  失格時に書く事実の不一致)・should 5 (ε の意味の反転、§0 の指示語、段下げ後の記録、無限定の断定、(3d) の効能否定)・nit 1、
  2 巡目は closed 6 / partial 1 で新規 must 1 (追記文言が verdict を固定)。いずれも real・採用で親が直し、最後の 1 点は
  観測値 (anomaly を検出した verify i 件・serializable でない verdict j 件) をそのまま書く形へ閉じて 3 巡目を起動しなかった
  (`rulings-stage6.md`)。親の統計文 (ε の定義) は 2 巡続けて倒された。
- 検査: `check_docs` 違反なし、`git diff --check` 空、新規 file の末尾空白 0、NFC (結合文字 U+0302 は平文へ)、holdout 語走査は本 wave の
  file に hit なし (既存 4 file の hit は別物)。変異 matrix は実装面ゼロで免除。受入全走は記録 commit の tip に対して投入し、結果は
  専用 handoff と land の receipt に残す。
- 専用 handoff は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b8-longrun-verify-prereg/handoff.md`。dev-wave 改善候補は
  ゼロ。次 wave・push は行わない。

## 次の一手差分

### 新規

- {{T:b8-prereg-activation}} **P2・ユーザー裁定待ち**: B-8 事前登録 v1 (`docs/b8-final-candidate-longrun-verify-preregistration.md`) §12 の
  発効前確認事項 7 点 — 対象の択 (案 A g_rl / g_rt 推奨、案 B fixed-5 / fixed-10)、「種」「長時間」の定義が論文ストーリー §8 B-8 の
  仕分けを満たすか、B-8 の書き方、費用 (≤ 4 h / 対象)、runner 改版 (Codex author、repo 外) と案 A の試走 (現行 pin での build・identity)、
  verifier の版 — を裁定し、発効 commit と D 番号で記録する。発効前に本走を始めない。
