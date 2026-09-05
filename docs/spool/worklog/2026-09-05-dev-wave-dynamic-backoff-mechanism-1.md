---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-dynamic-backoff-mechanism
seq: 1
title: Cicada 型 adaptive backoff の 3 定数を動的化して Pegasus で実測した — 計数窓は調整済みと等価、適応刻みは多コアで損、動的上限は発火せず、認証は cw-as-dyn 24 request (コード + docs + insight、branch worktree-dev-wave-dynamic-backoff-mechanism、変異 12/12 KILLED + 等価 1 SURVIVED)
---

## 本文

- ユーザー依頼は「Cicada adaptive backoff の 3 定数を動的化し、同じ wave で Pegasus 実測まで行う。計数窓・適応刻み・
  動的上限 (「効果なし」を事前登録する腕)・BACKOFF_TRACE 診断計器 (D14、perf build に symbol 0)。patch A は変えず新 patch を
  重ねる。probe は新設せず登録済み path に cell 書式を足す。事前登録を段 4 で凍結。複数ノードへ同時投入。基準線は
  D1506 の 2 本。認証は T-2189 の機構で動的版にも通す。本題だけ」。
- **結果 (未認証):** 事前登録 v1.1 の判定は H1 rejected (write-heavy 36〜48 スレッドで −4〜−6%)、H2 accepted、
  H3 rejected だが 24 点すべて ±3% 等価 (計数窓は tuned に何も足さない)、H4 rejected (適応刻みは多コアで −2.5〜−6%)、
  H5 accepted (等価だが動的上限は一度も発火していない)、H6 accepted (stock −65〜−77%)、H7 accepted。
  診断 build の方向的中率は 48 スレッドで 0.50 (偶然と同じ)、24 スレッドで 0.1 前後、read-heavy で 0。
  一次資料は `output/insights/2026-09-05_dynamic-backoff-mechanism/README.md`、設計判断は
  {{D:dynamic-backoff-count-window-design}} と {{D:dynamic-backoff-measurement-protocol}}。
- **brief 前の実測で覆した前提:** D1576 (更新窓は一定でない) を織り込んで計数窓を「最小間隔で間引く」形にした。
  `patches/ledger.json` は D18 第 4 類 ability probe 専用 (`silo_ladder_rung1_contract.py` が entry 数 1 を exact 要求) で
  A も未登録 → B は登録しない。`patchharness.applied` は 1 patch 専用 → `applied(A)` 内で B を `apply_patch`。
- **段 3 相談 2 本 (must-fix 13 + 12) の real 所見で裁定を変えた:** patch B は `#include` を足せない (`source_digest` の include 行
  gate に `include/backoff.hh` が入っている。親が現物で確認)、刻みは整数 µs (sub-µs は `uint64_t last_backoff_` で偽ゼロ勾配)、
  cap 10240 (40960 は悪化点)、上限 floor 50、時間のみ 10240 µs の対照腕を追加、方向的中を「次窓の throughput 差」で定義、
  腕の実行順を巡回、journal、schema v2 + patch stack。不採用: 認証を H1 通過の条件付きにする案 (ユーザー引数が同 wave を明示)。
- **段 5 は 3 単位並列 (Codex author)。fix 3 回:** (1) 遷移 test の driver が compile 不能 — 同一 bytes の variant file を
  GCC の `#pragma once` が同一視して 3 つ目の include を捨てた。(2) **生死確認 1 回目 (login node で pin+A+B を CCBench の
  CMake で実 build) が `-Werror=unused-parameter` で既定 build の compile error を捕まえた** — 遷移 test は警告フラグ無しで
  compile していた。fix 後は `-Wall -Wextra -Werror` で 5 構成を検査。(3) probe の trace parser が語 (`count|cap|time`) を、
  patch は整数 (0/1/2) を出す不一致、ccbench を CMake build する unit test の差し替え、sink golden 21→28。
  生死確認 2〜3 回目: perf build は nm/strings 0 件、診断は symbol 4 / 文字列 2、**A 単独と A+B 既定の `ycsb_silo.exe` は
  アドレス注記を除いた命令列 60,242 行が完全一致**。
- **段 6 レビュー 2 本 (NO-GO、must-fix 7 + 8) → fix 3 単位:** 計数窓の時刻を counter 走査の後に取る (stock と同じ端点)、
  診断 JSON の producer/consumer schema 不一致 (`trace_events` vs `events` 等) を producer 正本で統一し fixture を producer
  round-trip に、診断 exact (rep 0、event ≥1)、driver/PBS sha・argv・repo clean flag・full pin を全 JSON に、動的認証の
  namespace 閉包、6〜7 block と点欠落の欠測規則、hostname 一意要求の撤去、forest に複合判定、abort の対内 pp 差、
  static_assert の関係制約。不採用: 既発行 group receipt の再検証と trace 削除 (T-2189 既存機構、裁定パッケージへ)、
  perf mode の exact 7 cell 束縛。事前登録は v1.1 へ (性能値を見る前、腕・値・判定式は不変)。
- **main 取り込み:** 両親接触の実装面は `test_ccbench_spawn_sites.py` 1 file (main 側は行番号 1 行)。Codex fix 子の合成監査
  「変更不要」で merge commit dcdcf9bd4 (integrator + codex author scope=merge-synthesis)。
- **計測:** canary 2 job (perf/診断) は patch B の修正前の実行体だったので生死確認に格下げ (値は判定に使わず)。正式は固定 SHA の
  detached worktree (`submit-tree`) から perf 7 block (978014〜978020、各 12.1〜12.5 分、7 host 重複なし、CPU/経過 19.6〜20.3)
  + 診断 1 (978021、136 s) を同時投入、gen_S 混雑 (全 354 request) でも 30 分で完走。認証 24 request は pilot (978024、
  read-heavy slot 0、Elapse 520 s、verify 451 s) → 残り 23 (978044〜978066)。**24/24 certified** (group receipt complete、
  commit 1.463 億 / abort 2.171 億、anomaly 0、verify 79〜465 s、6 ノード)。認証したのは正しさだけで、機構の各枝の被覆と
  性能値は未認証。
- **変異:** probe → 本走の 2 段。probe 1 回目は harness の collection 段が queue-wait-timeout (914 s、D612 上書きが届かない
  既知型) で orphan-hold (978013) → 不在確認して hold 2 file + 停止記録を削除し、perf/diag が捌けた後に再投入。probe で M5 (floor 0) は `-Werror` の符号無し比較で compile が落ちる別理由 kill
  → floor 25 へ再照準、**M11a/M11b (図生成器の等価域と % 変換) が SURVIVED** → test を足す fix (dc0aa0bbd) → 本走
  **12/12 KILLED (期待 node 完全一致 13/13、M1 は 2 層・M10 は 3 層の冗長 gate) + 等価 1 SURVIVED**。
- **段 8 の改善候補:** (a) `qstat` の job 名列は 8 文字で切れる (待ち手の grep が空振り)、(b) GCC の `#pragma once` は同一 bytes の
  別 path file を同一視する、(c) sandbox の子は `python -m pytest` を guard に拒否され自走 harness だけ使える、
  (d) harness の collection 段の D612 上書き (T-2228 (c) と同じ)。いずれも memory へ。
- **受入全走 1 回目 (tested tip 54940301f): 20,626 緑 / 68 skip / 赤 1 件** — `test_p3_s4_loop.py::
  test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted` (B-3 在庫検査)。patch B の `#if BACKOFF_TRACE` 内の
  診断 stdout marker `IZANAGI_BACKOFF_TRACE*` (文字列 literal) が `\bIZANAGI_[A-Z0-9_]+\b` に一致し、ledger 未登録の
  「裸マクロ patch」と数えられた。全走でしか発火しない在庫検査の型 (T-2187 の (d) と同型)。Codex fix 子が
  `known_non_variant_patches` へ B を理由 comment 付きで足し (検査の regex と意味は不変)、受入 2 回目を投入した。
- 計算ノード: perf 7 + 診断 1 + canary 2 + 認証 24 + 変異 dispatch 約 30 (probe 2 回 + 本走) + provenance 監査 7 +
  受入全走 2 + 焦点走 dispatch 若干。詳細は insight §4。

## 次の一手差分

### 新規

- {{T:dynamic-backoff-ceiling-regime}} **P3・新規**: 動的上限は今回の regime (`Backoff_` ≤ 21 µs) で一度も発火しなかった。
  「効果なし」を検証するには上限に当たる regime が要るが、D1505 の後ではその regime 自体が候補にならない。
  方向的中 0.50 の反実仮想 (同じ状態で逆の一歩を取る対照) も未測定。着手するなら診断 build の対照設計から。
- {{T:t2189-group-receipt-revalidation}} **P2・ユーザー裁定待ち**: 段 6 レビュー A の所見 — `--mode certify` の既発行 group
  receipt 再検証が row 内容を再照合せず、`trace_dir` を専用 namespace に束縛しないまま `shutil.rmtree` する。T-2189 が main に
  置いた既存機構で本 wave は触っていない。閉じるなら「新規発行と既存検証を別戻り値にし、削除は canonical root の子・
  非 symlink・result JSON の `trace_directory` 一致に限定」を Codex author で。
