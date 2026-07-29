# [T-179] 段 1 brief — worker 資源台帳の正本化

## 対象と wave path

- 対象: `docs/phase3.md`「Codex dev-wave 資源効率化」の [T-179] (P1・最優先)。
- wave path: **軽量版 + 段 6 敵対レビュー 2 本を保持**。段 2 (codex plan 起草) と段 3 (敵対相談) は省く。
  - 省く理由: 設計択一は親が**実ログの直接実測で閉じた** — 台帳が再現すべき全数値
    (10 session / 434 turn / 2,757,982 / stage 別 6 値 / focus2 単独 498,984) が
    完全一致で再現済み。plan を紙で攻撃するより、実コードを段 6 で 2 レンズ攻撃する方が検出力が高い。
  - 保持する理由: 本成果物の価値は「数値の帰属が正しいこと」そのもので、静かな誤帰属が
    T-180〜T-184 の全比較を汚染する。よって `DW-S06-A` の 2 本並列レビューは省かない。
- 実装面は `DW-C00` の凍結境界どおり Codex `role=author` が書く。親は brief・裁定・統合・変異・受入・記録・commit のみ。

## scope (実装する)

1. `tools/codex_worker_ledger.py` — codex rollout JSONL を読み、worker 資源台帳を決定的に集計する
   **read-only** CLI。ファイルを一切書かず stdout に表 / JSON を出す。
2. `orchestrator/tests/test_codex_worker_ledger.py` + `orchestrator/tests/fixtures/codex_ledger/`
   の合成 rollout fixture — live inference なしで全受入が回ること。
3. worklog 突合 gate — `docs/worklog.md` の `エージェント工数: Codex N job (...)` 行を解析し、
   台帳の実測 session 数・bucket 内訳と突き合わせ、不一致を非 0 rc で返す。

## scope 外 (実装しない)

- resource envelope / 上限停止 (T-180)、reasoning・model の A/B (T-181, T-182)、
  retry 上限と fail-closed 回復の**強制** (T-183)、policy 採用 (T-184)。本 wave は**観測だけ**。
- `DW-O01` や worker 契約の既定値変更。model/reasoning は一切変えない。
- 他 wave への一般化。stage 規則表は T-153(e)/T-154 の実 prompt から導いた**この族のみ**の主張とし、
  未分類は `unclassified` として必ず表に出す (`DW-G03`: 独立 2 例が無いので族一般化しない)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) データ源**: `$CODEX_HOME/sessions/**/rollout-*.jsonl` (既定 `~/.codex/sessions`)。
  root は CLI 引数 / 環境変数で受け、**マシン固有パスを docs へ書かない**。
- **(P2) session 同一性**: 完全 `session_meta.session_id`。先頭 8 hex は時刻順で衝突する
  (019fac54 が 2 件、019fac79 が 2 件) ため短縮 ID を key にしない。rollout パスも併記する。
- **(P3) token の正本**: 各 session の**最終** `token_count.info.total_token_usage` に対する
  `input_tokens - cached_input_tokens + output_tokens` (= CLI reported)。
  per-turn `last_token_usage` の和は `context_compacted` を挟むと 7,571 ずれるので**使わない**。
  両方を出力し差分列 (`compaction_delta`) を明示する。`total_tokens` 生値も別列で持つ。
- **(P4) stage 分類**: 最初の `event_msg.user_message` (親 prompt 全文) に対する**明示的な規則表**
  (パターン → stage) + 任意の override map。どちらにも当たらなければ `unclassified` とし、
  黙って捨てない。`--strict` で unclassified があれば非 0。
- **(P5) 終了分類**: rollout から導ける値だけを名乗る — `completed` (task_complete あり) /
  `incomplete` (task_complete なし = F45 型候補、repo 全体 626 file 中 18 file) /
  `aborted_turn` (`turn_aborted` あり)。**CLI exit code と `.done` は rollout に存在しない**ため
  `exit_code=unknown` と明示し、偽の権威を与えない。
- **(P6) validator**: 新規実装せず `tools/check_codex_output.py` の述語 (最小 byte + fence 外
  `## 総括`) を最終 `agent_message` へ再利用する。不合格 = F43 型 (`fragment`)。
- **(P7) retry 検出**: 同一 wave 内で正規化 prompt hash が一致する複数 session を retry group とする。
- **(P8) worklog 突合**: (59) の「Codex 9 job (planner 1 / consult 2 / author・fix 3 / review 3)」を
  実測 10 session (planner 1 / consult 2 / author+fix 3 / review+focus 4) と比較する。
  **不一致の実体 = review bucket の 3 対 4** (focus2 の 1 件が落ちている)。

## 不変条件 (破れば停止)

- **read-only**: 台帳ツールは repo にもログにも書き込まない。
- **決定的**: 同一入力 → 同一 bytes 出力。時刻・乱数・辞書順非決定に依存しない。
- **fail-closed**: 壊れた JSON 行、`session_meta` 欠落、unclassified stage、突合不一致を
  黙殺せず、`--strict` で非 0 rc にする。
- **live inference 不要**: 受入は fixture と凍結ログの再集計だけで完結する。
- 受理集合の恣意的な拡大・縮小をしない (指示にない session を wave へ入れない / 落とさない)。

## 成果物影響 (`DW-G05`)

実装しない場合、T-180〜T-184 の比較はすべて worklog (59) 型の**手作業集計**に依存し続ける。
その手作業は既に review bucket で 3 対 4 の誤りを出しており、T-184 の policy 採用は
検証不能な stage 別 token 値を根拠に dev-wave の worker 契約 (model/reasoning/retry の受理集合) を
書き換えることになる。台帳があれば、その根拠値は fixture test で固定され再現可能になる。

## 発火した条件 (`DW-Oxx`)

O01 (codex 起動)、O02 (job artifact = job tmp の `t179-wave/`)、O05 (read-only レビュー子)、
O13 (gate 新設 — 入力 field の実在は上記のとおり実ログで全数確認済み)、O17 (commit trailer)、
O18 (親テスト cwd = repo root)、O19 (変異本走は統合 commit 後)、O20 (背景 job + worktree、gate 緑)。
O08/O09/O10 (freeze・凍結 bytes・producer write-path) は**不成立** — 本 wave は read-only ツールで
`output/campaigns` にも `external/ccbench` にも触れず、凍結成果物の bytes を変えない。

## 並列分割方針

実装単位は 1 つ (ツール + テスト + fixture は相互依存が強く所有を割ると patch 競合する)。
Codex author 1 子に `tools/codex_worker_ledger.py`、`orchestrator/tests/test_codex_worker_ledger.py`、
`orchestrator/tests/fixtures/codex_ledger/**` の 3 パスを排他所有させる。docs は親のみ。

## 実行環境

本 worktree (`.claude/worktrees/dev-wave-t179-worker-ledger`)・ログインノード。
計測ジョブ無し。受入全走もここで行う。
