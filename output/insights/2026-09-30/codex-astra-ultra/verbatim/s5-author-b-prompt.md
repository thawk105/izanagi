単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (正本、「中心裁定」「plan v2」の単位 B と変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s4-ruling.md
- 段 2 plan (起動器の行番号の地図。「単位 B」節は P1 前提なので P1' の実装には使える部分だけ使う): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s2-plan.md
- 実物の委任 rollout (root、read-only で参照だけ): /home/SFC/tanab/.codex/sessions/2026/09/30/rollout-2026-09-30T15-38-48-01a0f109-8530-7910-8c0e-e99685287eb1.jsonl

作業する worktree (cwd、書込みはここだけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/astra-ultra-unit-b (base 3cb51f201)。

# 役割と所有

あなたは dev-wave 段 5 の実装子 (Codex role=author、単位 B) である。**sub-agent を spawn しない (collaboration tool を使わない)。**
編集してよい path はこれだけ: tools/codex_worker_launch.py、orchestrator/tests/test_codex_worker_launch.py。docs は編集しない。commit しない。

# やること (s4-ruling.md「plan v2」単位 B の 1〜5)

背景: effort=ultra の Codex は委任 (collaboration namespace の `spawn_agent` function_call) を自動で試みる。委任先は別 rollout file に記録され
(`session_meta.session_id` = root の id、`id` = 子の id)、`--json` stdout には root の `thread.started` しか出ないため、現行の起動器は子の
model call・token・model/effort/cwd を見ずに attempt を受理してしまう。裁定は「委任した attempt は受理しない」。

1. root rollout の `response_item` で `payload.type == "function_call"` かつ `payload.name == "spawn_agent"` の行 (実物の形は上の rollout を見よ。
   `namespace` は `collaboration`) を検出したら、新しい致命 evidence reason (既存命名に合わせて決め、報告) を記録し、attempt を accepted にしない。
   `wait_agent` など spawn 以外の collaboration 呼び出しだけでは拒否しない (spawn が無ければ委任は生じない)。
   online (`_consume_rollout_event` 1468 行付近) と sealed 再検証 (4384・4499・4700 行付近) で**同じ判定関数**を共有する。
2. reason 集合が閉じている箇所 (150 行付近ほか) へ追加し、既存 receipt (V1〜V5) の読取互換を確認して報告する。schema 世代は上げない方針。
   上げないと互換が壊れるなら実装せず報告して止まる。
3. `orchestrator/tests/test_codex_worker_launch.py:3667` 付近の許可語彙 parametrize に "ultra" を追加 (語彙自体は単位 A が
   `tools/dev_waves/effort_levels.py` に足す。この木にはまだ無いので、その正例は期待赤として報告してよい)。
4. テスト: 正例 (spawn_agent 無し、wait_agent だけの空振りを含む) accepted、負例 (spawn_agent 1 件) が新 reason で rejected、sealed 再検証でも同じ拒否。
   fixture は実 rollout の function_call 行の形 (type/name/namespace/arguments/call_id) を写す。account id 等の識別子は写さない。
5. 早期停止は既存機構で schema を変えずにできる場合だけ。できなければ終了時拒否でよい (どちらにしたか報告)。

# 検査と報告 (必須)

- 緑には実走 nodeid・範囲を併記。実走不能なら「実装済み・未実走」と書き、`closed` と書かない。
- テスト新設・改名は親の名指しを網羅と見なさず、制約 meta-test (test file 列挙・所要台帳・hold 契約など) を自ら洗い出し走らせる。
- テストを甘くして緑にしない。機構の正例・負例は実体を名指しし依存先を stub しない (検出関数を monkeypatch で差し替えない)。
- 期待値へ揮発 payload を焼き込まない。
- 報告に、所有外 caller・共有 fixture・consumer (`tools/codex_worker_ledger.py`、`tools/t1434_t1222_science_slice.py`、receipt を読むテスト) への波及を静的列挙。
- 指示外の受理集合変更をしない。変更前の受理・拒否挙動を明記 (現行: spawn_agent があっても他が緑なら accepted)。
- 既存テストの期待値を変えない (反転・skip・削除禁止)。

# 出力形式

markdown。「## 変更 file と要旨」「## 受理・拒否の含意 (2 文ずつ、通る正例つき)」「## 実走したテスト (nodeid・結果)」「## 期待赤と回帰」「## 波及の静的列挙」
「## 変異事前登録 m4〜m6 の位置と単一理由性」「## 総括」。
