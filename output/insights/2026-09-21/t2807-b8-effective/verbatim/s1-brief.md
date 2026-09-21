# 段 1 brief — [T-2807] B-8 事前登録 v1 の発効 → 校正 3 job → 本走 6 job → 3 値判定 (2026-09-21、起点 local main 5efd69367 → 段 3 前に ff-only で 21641fee7)

- 研究前進: 論文ストーリー §8 B-8 (種を変えた長時間実行による最終候補の検証、現状「未取得」) を事前登録 v1 の規則で判定する。完了判定 = runner v5 `summarize` の 3 値判定 (pass / 失格 / 未確定) が出て、results 稿と story の腐らない入口 (README stale 注記) に §8 / §6.3 の書き方で載ること。「B-8 を取得した」は pass (要件 3 要素 = 対象 案 A・種 = 独立 process の自己シード・長時間 = extime ≥ 6 s が揃い本走 24 が全て pass 条件を満たす) の場合だけ書く。校正で本走不可 (∩ 空・予算超過・bench 失敗・失格) なら、その結末を書いて閉じる。
- 確定済みユーザー裁定: D2194 項 1 (択 (a) 承認、発効束 = insight §7.1、校正 3 job walltime 03:30:00、本走 6 job 24 verify ≤ 4 h / 対象、verifier hard timeout 本走 1800 s)、D2186 項 1 (対象 案 A・種 §3.2・長時間 §4.1・pass なら「取得」/ 失格なら §6.3 追記・verifier 版固定・発効束は発効 commit の tree に束縛し固定 checkout で走らせる)、D2190 (runner v5 の規則解釈 P1〜P11)。
- 実測済み前提 (親、2026-09-21): 事前登録 v1 raw sha256 = 6ccb18c7…f7c5 (51,974 bytes、不変)、runner v5 (prerun job dir probe/verify_phase_runner.py) sha256 = 4ff6652a…3430 (v5 複製と一致)。D2194 の記録 = rulings commit 3016f22ee (01:03 JST) → fold 2afb39768 (01:20 JST、D 番号付与)、提示時点 main 285477c00。runner の `validate_bundle` は schema / target / pin / identity 形 / known_results だけを検査し `status` を見ない (bundle sha256 は全 record に束縛)。
- scope (純増、全て docs / repo 外):
  (a) 発効 commit: 新 insight `output/insights/2026-09-21/t2807-b8-effective/` = README (発効の記録) + `verbatim/b8-effective-bundle.json` (draft の全値を不変で写し、`status`=`effective`、`decision`=D2194 項 1、`effective_date`=2026-09-21、承認 commit 群を足す)。`docs/paper-story/README.md` の stale 注記へ 1 項 (D2194 項 1 に基づく発効と、仕分け (2) を「独立 process の自己シード」へ改める限定、D2186 項 1 (2))。
  (b) 校正: 発効 commit の detached submit-tree 3 本 (同 SHA、同一 worktree の dispatch は直列なので別木) から calibrate 3 job を並行投入 (workload 別、{6,10} s、walltime 03:30:00)。
  (c) summarize → extime・B(E)・stage_B_allowed。決定記録 (fragment) と insight に置く (発効束ではない、§12)。
  (d) stage_B_allowed なら本走 6 job (workload × job-index 1/2、各 4 rep)、walltime は校正実測の最大所要 × 倍率 + 上限式の検査。未完走は §6.4 の reverify 1 回。
  (e) summarize の 3 値判定 → results 稿 `docs/paper-story/results/2026-09-2x-b8-final-candidate-longrun-verify.md` + results 表 1 行 + README stale 注記の更新。失格なら §6.2 の構造化記録を insight に逐語。
- 不変条件: 事前登録 v1 本文・patch・verifier module・pin は 1 byte も変えない。runner は再 author しない (投入直前に sha256 を照合)。発効前に校正・本走を始めない。校正で bench 失敗の cohort は本走を投入しない。anomaly の枠は再検証しない (規律 2)。性能値を取らない・書かない (規律 1)。story 日付版・既存 results 稿・既存 insight は凍結物として編集しない。cygnus は使わない。
- scope 外: 仮想リスク向けの gate・検査・台帳・一般化、runner の改修、verifier の改修、S-1 hold 解除、phase doc 編集、story 新版の作成 (D1858)。
- 受入・実測環境: 測定は Pegasus gen_S 計算ノード (runbook §7.5 並行投入、単独性は runner が bench・verifier 直前に検査)、trace 保全は job dir `run/` (/work lustre)。docs 検査は `python3 tools/check_docs.py`、受入全走は `tools/dev_wave_wait.py acceptance`。
- 変更面 (実アンカー): 新規 3〜4 file (insight README / bundle JSON / results 稿) + `docs/paper-story/README.md` の「積んでいる項目」節と results 系列表 (末尾に 1 行)。DW-O09: コード・テストからの pin 0 件 (`git grep` 実測)。
- 分割: 実装面ゼロ → 段 5 なし。段 3 の read-only 相談 1 本 (brief と投入手順を 2 レンズで攻撃) + 段 6 の read-only レビュー 1 本 (結果稿・insight を一次 record と照合) を残す (計算ノード job を投げ数値を書く wave、記憶の 3 例)。

## 親の provisional 裁定 (攻撃対象)

- (P1) 仕分け (2) の限定の置き場 = `docs/paper-story/README.md` の stale 注記 (日付版は凍結物で「書いた後は更新しない」、項目を積んでも新版は要らない D1858)。日付版の §8 は編集しない。
- (P2) 「承認 commit」= D2194 を記録した rulings commit `3016f22ee` を主とし、D 番号を振った fold `2afb39768` と提示時点 main `285477c00` を別 field で併記。発効 commit 自身の hash は bundle に書かない (自己参照禁止、§0)。発効 commit の hash は後続 commit の insight / 決定記録に書く。
- (P3) bundle の値は draft から 1 値も変えない (identity・sha・known_results)。足すのは status / decision / 日付 / 承認 commit / 発効束の保存先 path だけ。runner `--bundle` は固定 checkout 内の tracked copy を指す。
- (P4) run root = 本 wave の job dir `run/` (`calib/<workload>`、`verify/<workload>-j<n>`)。runner は prerun job dir の v5 をその path のまま使う (複製すると `runner_sha256` は同じだが同定の path が 2 つになる)。
- (P5) 校正 3 job の submit-tree は発効 commit から 3 本、本走 6 job はさらに 3 本 (計 6 本) 足すか校正後の 3 本を再利用するか — 同 SHA なので校正終了後の再利用で可 (同一木の dispatch 直列だけ守る)。本走 6 本を同時に出すには 6 木要る → 3 本追加。
- (P6) 本走 walltime = 本書の校正実測の最大 job 所要 (4 rep 換算) × 倍率。上限式 = F 上限 2400 + 4 × (bench 120 + count + preserve + verifier hard 1800) + 終了余裕 300 を予約以下にする (§7)。値は校正後に親が決め insight に書く (発効束ではない)。
- (P7) 本走の未完走は `reverify` を同 trace に 1 回だけ (§6.4、hard timeout 3600)。reverify も未完走なら未確定のまま。
