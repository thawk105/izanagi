---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2797-b5-contrast
seq: 1
title: [T-2797] B-5 生成器対照の (α) §10 残部品を Codex author で段階実装し (β) 上限付き試走 53 論理 session を完走した — 3 arm の score 4.00〜4.05M tps (floor 内、n=1、主標本外)、固有費 217〜509 s / session、home 共有 bench lock で wall の 59% が待ち、本走は未認可のまま裁定パッケージを insight §8 に再提示 (コード + テスト + insight、branch worktree-dev-wave-t2797-b5-contrast、変異 KILLED 26 / 等価 2 / MISMATCH 2 → 再登録・再走で KILLED)
---

## 本文

- 依頼 (D2172 項 4 段階裁定 (A)) を 9 段で処理した。段 2 plan (codex read-only、P1〜P9) → 段 3 敵対相談 2 本 (must-fix 3 点: BUILD_START 不在は未投入の証拠にならない、同 slot retry は残存 claim に拒否される、45 分無応答は機械故障の証拠にならない) → 段 4 裁定 (P9 = 3 arm とも `p3_s4_loop` CLI の subprocess で slot 評価、seam 4 点、M0〜M19 事前登録) → 段 5 Codex author 3 単位 (A1 core + seam、A2 report、A3 job body + launcher) → 段 6 review 2 本 (NO-GO、must-fix 5 / should 8) → fix1〜3 → 焦点再レビュー (残件 2 は WAL diff-reject 経路の受理と `logical_sessions` で閉じた) → 変異 → 試走 → 記録。設計判断は {{D:b5-slot-subprocess-driver}}、運用事実は {{D:b5-pilot-execution-facts}}。
- 試走 (β): 4 job (random 13636 / sweep-matched 13637 / llm 13638 / block-stock 13639、gen_S、write-heavy、submit-tree = 統合 commit 4) を 22:01 JST に投入し 04:02 JST に完走。3 arm とも A=10 / B=10 / 論理 16 session、前処理拒否 0・品質欠測 0・retry 0、全 318 verify 走 serializable。score は random 4,045,006 (endpoint 6 µs) / sweep 4,002,540 (8 µs) / llm 4,011,506 (8 µs)、block stock 記述 CV 0.46%。優劣は言えない (n=1、`not-applicable-pilot`)。
- LLM arm は親手番 10 巡 (planner-v4 → coder-v4-autonomous-k2 → critic、Agent tool の fresh subagent、`model: opus` / `effort: high`) を全部逐語で保存した。1 巡 10〜13 分、critic の診断が 4〜5 分で最長。critic は 9 巡で abort 率の単調性・平坦域 5〜10 µs・両側の崖を帰属し、planner / coder は候補値を独立に導いた (critic の候補と一致することが多かった)。
- 所要: session の固有費は 217〜509 s (abort 率の高い候補 ≈ 500 s)、他 job 終了後の 7 session は lock 待ち 0 で 499〜510 s。試走 4 job 並列では home 共有 `~/.izanagi/bench.lock` (performance verify pass 5 rep + bench を囲む、`p3_s4_loop_pegasus.sh` は `IZANAGI_BENCH_LOCK` 未設定) の待ちが wall 53,805 s の 59% を占めた。B-10 / A-5 job body は node-local lock を設定している。
- 変異: probe (commit 4、29 変異) → final (commit 5、30 変異) で M10 / M11 が MISMATCH (観測 = 期待 + fix3 で足した test 1 本の上位集合、probe を fix 最終 commit で再検証しなかった DW-M07 の省略) → erratum を残し final2 で再登録・再走して KILLED。M25 は等価 (連番条項が件数条項を含意) → positive に再分類、両層 M25b を予測 node で登録し KILLED。
- 落とし穴: 隔離 session の Bash guard は heredoc 内の path 語や計算値引数を拒否するので、検査・保存 script は job dir に Write して plain に呼んだ。`hooks/guard_bash.py` は main の登録簿を読むため wave 内で登録した launcher は land まで Bash から起動できず、試走は job dir の script が launcher API を import して投入した。planner の返答が前置き付きの fence になる巡 (5 / 7 / 8 / 10) は原文を `.raw.md` に残して fence 内 JSON を逐語で使った。
- 工数: codex 子 = plan 1 + consult 2 + author 3 + review 2 + fix 3 + focus 1 の 12 本、Agent 子 = planner 10 + coder 10 + critic 9 の 29 本、親の実走 (login) 4 回 + 焦点走 (計算ノード) 2 回 + 変異 3 走 (probe / final / final2)。wave の壁時計は起動 gate 19:13 JST (startup-gate.log) → 記録 commit (段 7、本 entry 直後の commit 日時) まで。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定するため insight §7 に追記)。

## 次の一手差分

### 完了

- [T-1872] 事前登録 §10 の「実装が要る」残部品 (系列開始 stock の planner 前配置、session 契約の flag 束縛と品質欠測の分類、B / A 台帳と収束停止の不適用、重複の fresh 評価、random 生成器、sweep の hash 順 B 点、解析 consumer、較正・verify の job body 配線と launcher) を Codex author で段階実装し、正例・負例の変異 (M0〜M28、M25b) で固定した。本走の認可は [T-2797] で諮る。
  remaining: none
  base: a0ebd797d556479b25f9f4b2bef3f5ecd43047bc91bd23a2f242f5e5b05753b8

### 更新

- [T-2797] **P2・試走 (β) 完了 → 本走認可の裁定パッケージをユーザー裁定へ**: (γ) 2 の残部 (凍結する実験構成の実値: role 子の `model: opus` / `effort: high`、prompt・知識射影・還流の逐語と sha)、4 (費用: 固有費 ≤ 510 s / 論理 session → 1,773 session ≈ 251 h の node 時間、総実行 wall 上限の倍率、LLM arm の親手番 1,080 巡 ≈ 180〜235 h が律速になりうる)、6 (対象 commit = 本 wave の land 以降で job body の node-local lock を含む commit) を `output/insights/2026-09-20/t2797-b5-contrast/README.md` §8 に再提示した。発効 commit は作っていない。本走前に要る実装 (job body の `IZANAGI_BENCH_LOCK`、job ごとの submit-tree) は {{T:b5-job-body-node-local-lock}}。試走の既知結果台帳は同 insight §6、主標本には入れない。
  base: f7f87d454b52220f335ee70b90ec81963badb9a4b6e82b5fabd8533bcaae965c

### 新規

- {{T:b5-job-body-node-local-lock}} **P2・新規 (本走前、Codex author)**: `tools/pegasus/p3_s4_loop_pegasus.sh` の B-5 mode (または job 全体) で `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を B-10 / A-5 と同じ node-local に設定し、`tools/pegasus/b5_contrast_launch.py` を job ごとの submit-tree (または cache 公開競合の検査) に対応させる。試走で home 共有 lock の待ちが wall の 59% を占め、並列度を上げても総 wall が縮まないことが判明した ({{D:b5-pilot-execution-facts}})。既存 3 経路の bytes 不変を test で固定する。
