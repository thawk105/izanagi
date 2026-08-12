# 段 1 brief — 実行場所分類の台帳反映 + wave 使用量 collector の 2 バグ修正

- wave: dev-wave-exec-loc-and-usage-fixes / branch `worktree-dev-wave-exec-loc-and-usage-fixes`
- 一次資料: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings8-batch.md` (裁定控え) と
  `/work/SFC/tanab/dev-wave-jobs/rulings8-measure/` (実測 raw、README + 3 job dir)
- 実測環境: 本 wave の受入は Pegasus login から `tools/run_tests.py` (自動 dispatch) で行う。
  分類の再測定は行わない (既測、下記 P1)。

## scope (3 点) と成果物影響 (DW-G05)

1. **`tools/claude_session_ledger.py` の実行場所分類を台帳へ反映する。**
   放置すると同 tool と `collect_wave_usage.py` が login で hook に拒否され続け、段 9 後の
   使用量収集が恒久 blocked になり、**wave 工数台帳 (`dev-wave-jobs/**/usage artifact`) が全 wave 欠測**する。
2. **`tools/collect_wave_usage.py` の slug-dash バグと fail-open を直す。**
   放置すると先頭 `-` の project slug (= 本 repo の実 slug `-work-1-SFC-tanab-izanagi`) で
   内側 parser が `SystemExit(2)` になり、`ledger_report=null` の artifact を rc=0 で保存する。
   **呼び手は成功と誤認し、台帳の欠測が検出されない。**
3. **`tools/claude_session_ledger.py` の `message_id_collision` 誤判定を解消する。**
   放置すると並列 subagent を使った全 wave で rc=2 となり、**使用量が 1 件も記録されない。**
   ただし修正方向を誤ると同一 model call を 4 重計上し、**台帳の token 値そのものが壊れる。**

scope 外 (明示): `tools/mutation_worktree.py` の分類 (軽量化実装後)、branch 削除・push
(ユーザー手番)、分類の新規実測。

## 確定済みユーザー裁定 (authority: user、第 7 束)

- 実行場所分類の**選択**は AI へ明示委任された (「あなたが適切なところを選んでください」)。
- 分類の**実測**は既に別 job が計算ノードで実施済み。本 wave は反映のみで、再測定しない。
- 論文用生成物は git 管理 (本 wave の insights は tracked)。

## 実測した前提 (DW-S01)

- 一次資料 README の判定: ledger 既定 argv (`--json`) = local-ok 相当。有効 5 走の charged delta
  最大 20.6 MiB、certified peak = 20.6 + 128 = 約 149 MiB < 規範値 512 MiB。入力 1.40 GB / 1,045 jsonl。
- 方法論の差 (evidence へ明記が必須): 計算ノードには per-job cgroup も delegation も無く
  (`/proc/self/cgroup` = `0::/system.slice/nqs-jsv.service` の 1 行、2 ノードで確認)、§7.0 の
  専有 scope 手順は非 root で実行できない。採ったのは共有 service cgroup の `memory.current`
  delta sampling で、同居 job の充当変動が混入する (実際 1 走が負 delta で無効化)。
- collect_wave_usage の欠陥は raw で再現済み: `run3-0_908401.nqsv/usage-1.stderr` =
  `argument --project: expected one argument`、同 `usage-1.rc` = `0`。等号形を外側へ渡しても
  内側で同じ欠陥が出ることを確認済み。
- ledger の rc=2 実体: `run-0:908392.nqsv/ledger-1.stderr` の
  `fatal: message_id_collision: msg_011Cd9iV517nAAoCVuTwcsjt: <4 つの subagents/agent-*.jsonl>`。
  当該 record を実機で確認したところ、**4 ファイルとも `parentUuid` と `message.id` が同一で
  `agentId` だけが異なり、いずれも `usage` を持つ**。= 並列 subagent の共有親文脈が各 transcript へ
  複製されたもので、同一 model call である。
- ledger の入力は hard cap 済み (`DEFAULT_MAX_FILES=25` / `MAX_TOTAL_BYTES=512 MiB` /
  `MAX_RECORDS` 他)。registry の現 `reason`「input caps ... are incomplete」は実装と食い違う。

## 不変条件 (緩めない)

- **規律 2**: 正しさ/受理ゲートを緩める方向の変異を採らない。既存の negative test を反転・削除して
  目的を達する形は不採用。
- 台帳の token 値は過大計上しない。dedup は「同一 model call を 1 回」であって「issue を握り潰す」ではない。
- hook / loader の fail-closed 縮退 (registry 異常時に `tools/pegasus/` を全拒否) を壊さない。
- 分類の実測を本 wave が自分で行わない (§7.0 手番、F159)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) `class` を `local-ok` へ変えることは、現行の構造的防壁の撤去を伴う。**
  `tools/pegasus_admission_registry.py:105-107` と `hooks/guard_bash.py:270-272` が
  非 `tools/pegasus/` の `local-ok` を禁止し、専用 negative test 2 本
  (`test_pegasus_registry_loader_rejects_non_pegasus_local_ok`,
  `test_bash_pegasus_entry_lookup_rejects_registry_keys_outside_subtree`) と
  `test_bash_registered_non_pegasus_unknown_site_matrix` が張られている。この禁止は
  「適用 path を広げても受理集合は単調に縮むだけ」(D175 決定 6) を成立させている当の機構である。
  **provisional: class は `unknown` 据置とし、`reason` / `evidence` へ実測結果と方法論差を反映する。
  class flip は裁定パッケージでユーザーへ返す。**
- **(P2) 実測表 (§7.0) へ行を足さない。** `tools/check_docs.py:3004` の実測表 parser は
  `tools/pegasus/` path しか受理せず、期待集合は evidence が `runbook §7.0 実測` に**完全一致**する
  entry である。**provisional: evidence 文字列を完全一致させず、方法論差を含む別文字列にする**
  (実測表の受理集合を触らずに済む)。
- **(P3) ledger の collision 修正方向は dedup。** 同一 `message.id` は同一 model call なので
  **1 回だけ計上**する。`message_id_collision` を FATAL から外すだけの降格は 4 重計上を招くので不採用。
  usage が食い違う複製が来た場合は従来どおり anomaly として扱う。
- **(P4) collect_wave_usage の rc は状態で分ける。** provisional: `complete`=0、
  `blocked`=既知の正常停止として 0 以外の専用値、`error`/`missing`/`incomplete`=非 0。
  **`blocked` を一律に非 0 にすると login での段 9 手順が必ず失敗する**ため、呼び手が区別できる形にする。
- **(P5) slug 渡しは `--project=<slug>` の等号 1 token 形にする。** 先頭 `-` を値として渡せる。
  同型の穴がある `--since` / `--until` / `--max-files` / path 系も等号形へ揃える。

## 成果物の形

- 実装面: `tools/collect_wave_usage.py`、`tools/claude_session_ledger.py`、対応テスト
  (`orchestrator/tests/test_collect_wave_usage.py`, `test_claude_session_ledger.py`)。
  P1 の裁定次第で `tools/pegasus/admission_registry.json` の非 class field。
- docs: `docs/pegasus-runbook.md` §7.0 投影表 (class 不変なら evidence 列のみ)、
  worklog / decisions fragment (spool)、insights 一式、裁定パッケージ。

## 並列分割方針

本 wave は受理集合と防壁に触るため**軽量版にしない** (DW-C00)。段 2 プラン 1 本、段 3 敵対 2 レンズ、
段 5 実装は所有を 2 分割 (A: collect_wave_usage + registry/docs 反映、B: claude_session_ledger の dedup)、
段 6 は敵対レビュー 2 本 + fix + 変異 matrix + 受入再走。
