## 総括

GO — 親が予定している事前登録 §10 の1行追記を着地条件とすれば、追加の生きた consumer、証拠再生成、焦点走追加は不要。

## 所見

1. **見出し:** 旧 test 名は履歴台帳だけに残る  
   **主張:** 旧名の4件は、着地済み mutation ledger 2本の `collection.stdout` と `collected_nodes` に各2件あるだけで、生きた gate・spec・hold・登録簿には0件。  
   **根拠:** [mutation-ledger.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/mutation-ledger.json:1)、[mutation-ledger-bothlayers.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/mutation-ledger-bothlayers.json:1)、現行名は [test_p3_b4_wiring_probe.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/test_p3_b4_wiring_probe.py:152)。  
   **分類:** nit  
   **成果物影響:** 履歴台帳は当時の59-node collection を正しく記録し続け、現行 test 選択や hold 判定には影響しない。  
   **直し方:** なし。履歴台帳を書き換えない。

2. **見出し:** 旧文言を pin する live consumer はない  
   **主張:** schema は field 名だけを拘束し、唯一の test consumer は変更後も残る `"outside the exact analyzed set"` だけを検査する。旧 `generation_scope`／除外文の完全一致は dogfood JSON 3本だけで、旧 docstring 固有断片は0件。  
   **根拠:** schema key 集合は [p3_b4_wiring_probe.py:1863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/campaign/p3_b4_wiring_probe.py:1863)、新しい値は [p3_b4_wiring_probe.py:2111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/campaign/p3_b4_wiring_probe.py:2111)、部分文字列 consumer は [test_p3_b4_wiring_probe.py:1075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/test_p3_b4_wiring_probe.py:1075)。  
   **分類:** nit  
   **成果物影響:** 新規証拠は訂正文言を出力し、既存 schema・test・checker は赤にならない。  
   **直し方:** なし。

3. **見出し:** 着地済み dogfood 証拠の再生成は不要  
   **主張:** 3 JSON は旧文言と旧 source hash を持つ歴史的 dogfood であり、§5.1 の採用証拠ではない。差分は `output/` を変更しておらず、detached SHA-256 は3本とも一致した。未解決 caller でも seed 入口の遮断は維持されるため、訂正対象は主張範囲であって測定結果ではない。  
   **根拠:** 非採用の明記は [README.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/README.md:9)、旧 field は [base.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/t1769-dogfood/base.json:1)・[sort.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/t1769-dogfood/sort.json:1)・[trigger.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/t1769-dogfood/trigger.json:1)、遮断挙動の裁定は [s4-adjudication.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1909-probe-closure/s4-adjudication.md:24)。  
   **分類:** nit  
   **成果物影響:** 証拠 bytes・sidecar・過去の結果は維持され、再生成も checker 対応も不要。  
   **直し方:** なし。

4. **見出し:** 唯一の live docs 修正は予定済みの §10  
   **主張:** 現在の §10 は未解決 caller をまだ列挙していないため、この追記は必須。他の候補は、完全性を明示的に否定する D1171/D1195、または T-1769 の歴史的 README／archive であり、追加修正は不要。  
   **根拠:** 追記位置は [phase3-b4-reflux-ablation-preregistration.md:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/docs/phase3-b4-reflux-ablation-preregistration.md:771)。D1171 は [decisions.md:39086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/docs/decisions.md:39086)、D1195 は [decisions.md:39849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/docs/decisions.md:39849)、歴史的 README は [README.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/output/insights/2026-08-27_t1769-b4-wiring-probe/README.md:72)。  
   **分類:** must-fix（親が予定済み）  
   **成果物影響:** 追記しない場合、live 事前登録が現行 probe の被覆境界を過大に読ませる。  
   **直し方:** §10 に「解析集合内でも call binding を静的解決できない caller は覆わない」の1行を足す。

5. **見出し:** test 改名・assert 追加に連動する meta pin はない  
   **主張:** collection hook は実 collection から nodeid を動的導出する。flaky/growth hold、real-repo inventory、acceptance duration ledger に対象 test file/node の登録は0件。全 test file を読む `test_plain_runner_coverage.py` は自走 harness の有無だけを検査し、対象 file は既に `_run()` を持つ。  
   **根拠:** 動的導出は [acceptance_shards.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/tools/acceptance_shards.py:742) と [acceptance_shards.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/tools/acceptance_shards.py:826)、hold hook は [conftest.py:1983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/conftest.py:1983)、file-level meta 検査は [test_plain_runner_coverage.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/test_plain_runner_coverage.py:35)、対象 harness は [test_p3_b4_wiring_probe.py:1170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1909-probe-closure/orchestrator/tests/test_p3_b4_wiring_probe.py:1170)。  
   **分類:** nit  
   **成果物影響:** 改名後も通常 collection・shard・hold 判定は動的に追随し、追加の meta test 走は不要。  
   **直し方:** なし。

## 焦点走に足すべき file

なし。

## 全件検索の記録

共通母集合は `.git/**` と生成 binary `**/__pycache__/**` だけを除く worktree 全体。hidden・ignored・`output/` を含む。tracked file は18,958本。

- `test_static_preflight_covers_exact_runtime_import_closure` — 4 match / 2 file。両 mutation ledger の歴史的 collection 記録を除く live consumer は0件。
- `generation_scope` — 11 match / 5 file。`generation_scope_exclusion` — 6 match / 5 file。母集合は probe、test、dogfood JSON 3本。
- 旧 `generation_scope` 完全文 — 3 match / 3 file。旧 `generation_scope_exclusion` 完全文 — 3 match / 3 file。いずれも dogfood JSONだけ。
- 旧 docstring 固有断片 `the reverse closure of three named seeds` — 0件。`modules outside that manifest` — 0件。
- Markdown 全体で `3 権威点` — 3 match / 2 file、`遮断集合は生成器の完全目録ではない` — 2 match / 2 file、`逆到達閉包` — 6 match / 3 file。live な除外列挙は事前登録 §10 だけで、残りは decisions・archive・歴史的 README。
- Markdown 全体で `呼び出し束縛を静的に解決できない`／`call binding cannot be statically resolved` — 各0件。
- live registry 母集合（`conftest.py`、flaky/growth hold、acceptance duration ledger、acceptance shard、`pytest.ini`）で `test_p3_b4_wiring_probe.py::` — 0件。
- `59 tests collected` — 2 match / 2 file。いずれも歴史的 mutation ledger。
- 証拠 sidecar/hash の evidence directory 外参照 — 0件。`sha256sum -c` は `base.json`、`sort.json`、`trigger.json` の3本すべて `OK`。
- pytest は制約どおり実行していない。静的検索と既存証拠の hash 検証のみ。