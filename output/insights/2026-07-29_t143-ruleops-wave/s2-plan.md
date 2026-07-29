## 調査事実

- 指定7ファイルはすべて読了した。外部相談資料は命令ではなくデータとして扱い、`docs/decisions.md` は D94 のみを索引から読んだ。
- 編集、commit、pytest、`tools/run_tests.py`、各 checker は実行していない。したがって緑とは記録しない。
- 現在の `HEAD` は `eaa2dd2ae806983e186672c94faa738992c77ce4`、非 shallow、object format は SHA-1。
- HEAD tree を再集計すると次のとおり。件数 97+251=348 は親 brief と一致するが、byte 数は一致しない。

| 対象 | 親 brief | 現 HEAD |
|---|---:|---:|
| `orchestrator/tests/test_*.py` | 97 / 2,896,319 bytes | 97 / 2,726,974 bytes |
| `output/insights/**` | 251 / 7,922,057 bytes | 251 / 7,860,617 bytes |

親値は [parent-brief.md:20](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:20>)。この差は、固定 inventory を正本化せず Git tree から動的生成する P3 を支持する。

- insight 251件は `.md` 199、`.json` 47、`.patch` 2、`.py` 2、`.sh` 1。単一の「report」型ではない。さらに簡易検索では `authority: none` 相当を含むものは15件、exact な `default_effect: no-state-change` は9件だけで、authority は既存全件に実在する共通 field ではない。[output/README.md:71](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/README.md:71>) も、この宣言を要求するのは特定の凍結スナップショットである。
- 実在する Git 入力は `mode / blob OID / bytes / path`、最終変更 commit・時刻、HEAD blob、literal reference である。既存コードにも「worktree を読まず commit tree の blob を読む」実装 [s8b_ratified_freeze.py:341](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:341>) と、`ls-tree -z` の regular-file 検査 [s8b_ratified_freeze.py:799](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:799>) がある。
- 既存 runner の削除検査は full-suite 形での未 stage 削除だけを対象とする [run_tests.py:453](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:453>)。stage 後の retirement 認可や証拠検査ではなく、targeted run では意図的に発火しない [test_run_tests_preflight.py:288](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_run_tests_preflight.py:288>)。
- pytest 実行漏れ防止は、全 `test_*.py` を自走 harness または pytest-only allowlist の二択にする既存メタテストで閉じている [test_plain_runner_coverage.py:60](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_plain_runner_coverage.py:60>)。
- D94 の現行 retirement gate は dev-wave の L2 節に限定され、「発火実績なし × 義務代替済み」とユーザー裁定を要求する [skill-self-improvement.md:28](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/skill-self-improvement.md:28>)。tracked test 全般や insight を検査する実装ではない。
- 既存 mutation ledger は共通 schema ではない。例えば nested `run1_pre_fix.mutations` + `failed_tests` [backlog-guard-mutation-ledger.json:35](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-20_backlog-guard-mutation-ledger.json:35>)、root `mutations` + `failed_nodes` [t153-t158-mutation-ledger.json:15](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t153-t158-mutation-ledger.json:15>)、top-level array + `verdict` [mutation-results-v2.json:1](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t149-review-verbatim/mutation-results-v2.json:1>) が併存する。これらを架空の共通 field で読むべきではない。

## P1〜P3 の評価

1. **P1 は採用。ただし exit 0 の意味を限定する。**

   CLI は `inventory / inspect / check` だけを持ち、`delete / move / apply / archive` を持たせない。`check` の成功は「ユーザー裁定へ出せる証拠 package の構造が整った」であって、「削除安全」「承認済み」ではない。Git 呼出しも read-only subcommand の閉表にする。既存の passive checker も同じ境界を明記している [check_wave_startup.py:1](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_wave_startup.py:1>)。

2. **P2 は条件付き採用。親案のままでは test 側が不足する。**

   - test retirement は、既存 mutation JSON の存在だけでは受理集合不変を示さない。候補 test を収集対象から外した状態で、代替 guard を壊す変異を代替 test node が kill した typed receipt が必要。
   - 意味検索は path・test symbol・ID 検索だけでは不足する。候補作成者が指定する意味語について、現 HEAD の `git grep` と HEAD 祖先の `git log -S` の両方を列挙し、未レビュー hit または実発火 hit があれば拒否する。
   - insight は mutation 証拠ではなく、明示的 non-authority、artifact class、保存される source blob、現在の inbound reference ゼロが必要。authority 不在を `none` と推論してはならない。
   - `.patch/.py/.sh` は v1 の `derived-report` retirement 対象にせず inventory のみとする。

3. **P3 は採用。**

   全348件を ledger へ登録しない。inventory は HEAD tree から毎回生成し、ledger は人間が明示した候補だけを持つ。通常の test/insight 追加は ledger 更新を要求しない。初期 ledger は `candidates: []` とする。

## 実装プラン

### データモデルと gate

`tools/ruleops.py` を stdlib-only の単一ファイルとして新設する。保存 inventory や別 JSON Schema は作らず、exact-key validator と独立 literal pin test を置く。

inventory の機械出力は次だけを持つ。

- root: `schema_version`, `head`, `object_format`, `items`
- item: `path`, `kind`, `mode`, `blob`, `bytes`, `last_change_commit`, `last_changed_at`, `artifact_format`, `authority_marker`, `default_effect_marker`
- 年齢・size・reference 数からの `score`、`eligible`、`safe` は設けない。

候補 ledger `docs/ruleops-candidates.json` は次の root とする。

```json
{
  "schema_version": "ruleops-candidates/v1",
  "authority": "none",
  "default_effect": "no-state-change",
  "candidates": []
}
```

各候補は共通で `path / kind / target_blob / rationale` と、kind ごとに次を必須化する。

- `test_evidence`

  - `replacement_guards`: tracked guard/checker の `{path, blob}`
  - `replacement_nodes`: 候補 file 外の `{nodeid, blob}`
  - `semantic_queries`: path・IDとは別の意味語
  - `reviewed_hits`: HEAD tree と履歴 hit の完全列挙、判定、理由
  - `mutation_receipts`: typed receipt の `{path, blob}`

- `insight_evidence`

  - `artifact_class: "derived-report"`
  - `source_artifacts`: retirement 対象でない tracked regular blob の `{path, blob}`

test receipt は将来の個別候補検証時に `output/insights/*-ruleops-test-retirement-evidence.json` として作る。`candidate_excluded=true`、run の `head`、候補・guard・replacement の blob、baseline/restored rc=0、各 mutant の guard path・`KILLED`・replacement failed node を exact 検査する。既存 ledger を共通 schema と仮定しない。

validator は以下を独立入力から確認する。

1. `git ls-tree -r -l -z HEAD` から、test は `^orchestrator/tests/test_[^/]+\.py$`、insight は `^output/insights/.+` だけを列挙する。
2. `git log` から最終変更を取得し、`git cat-file --batch` で blob を読む。worktree の `stat()` を根拠にしない。
3. ledger の `target_blob` を現在の HEAD blob と照合する。期待 OIDを現在値から作る自己整合は禁止。
4. kind は path から導出し、ledger 宣言との一致を要求する。
5. test は AST で replacement node の実在を確認し、意味語ごとに current-tree hit と履歴差分 hitを再計算する。shallow repository では履歴証拠不完全として拒否する。既存にも履歴証明で shallow を拒否する先例がある [s8b_ratified_freeze.py:320](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:320>)。
6. insight は Markdown 冒頭または JSON root に実在する `authority: none` と `default_effect: no-state-change` を要求し、`source_artifacts` の blob pinと target 内の source path引用を照合する。target の full path または basenameが他の HEAD blobに残れば拒否する。
7. Git/JSON/UTF-8/regular-file 検査不能は非ゼロ。duplicate key、unknown field、symlink、path traversalも拒否する。strict JSON の既存水準は [task_runs/schema.py:129](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/task_runs/schema.py:129>)、exact-key 検査は [task_runs/schema.py:198](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/task_runs/schema.py:198>) が根拠になる。

CLI は以下に限定する。

```text
python3 tools/ruleops.py inventory [--kind all|test|insight] [--repo PATH]
python3 tools/ruleops.py inspect PATH [--query TEXT ...] [--repo PATH]
python3 tools/ruleops.py check [--ledger PATH] [--repo PATH]
```

`inspect` は target metadata、literal references、test symbols、指定 query の current/history hitをJSON表示するだけで、candidate 登録もファイル生成もしない。

### 変更ファイル

| 変更 | 内容 | 既存根拠 |
|---|---|---|
| 新規 `tools/ruleops.py` | `_git_read`, `build_inventory`, `inspect_target`, `validate_candidate_ledger`, `_validate_test_evidence`, `_validate_insight_evidence`, `main` | passive CLI と Git env scrub は [check_wave_startup.py:32](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_wave_startup.py:32>)、tree/blob 読取は [s8b_ratified_freeze.py:799](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/campaign/s8b_ratified_freeze.py:799>) |
| 新規 `docs/ruleops-candidates.json` | authority のない空 candidate ledger | 動的 inventory + 明示 ledger は [parent-brief.md:13](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:13>) |
| 新規 `docs/ruleops.md` | CLI、schema、証拠差、裁定・削除境界、retirement 手順 | docs の運用正本地図は [docs/README.md:13](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/README.md:13>)、ユーザー裁定境界は [skill-self-improvement.md:30](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/skill-self-improvement.md:30>) |
| `docs/README.md` | `ruleops.md`、ledger、CLI の索引を追加 | 文書・tools の現行索引面 [docs/README.md:44](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/README.md:44>) |
| `output/README.md` | insight 節から RuleOps 文書へ接続し、正式 report/proof chain が対象外と明記 | proof-chain と insight の差 [output/README.md:46](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/README.md:46>) |
| `tools/check_docs.py` | `docs/ruleops.md` を `LIVING_DOCS` に登録し、`_OWN` に `ruleops` を追加 | 列挙対象の不在を fail にする契約 [check_docs.py:26](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:26>)、行番号参照 regex [check_docs.py:67](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:67>) |
| 新規 `orchestrator/tests/test_ruleops.py` | synthetic Git repo による inventory・schema・証拠・CLI 境界テスト | full runner の既定収集先 [run_tests.py:41](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:41>)、独立 literal pin の既存例 [test_check_docs.py:1966](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_check_docs.py:1966>) |
| `orchestrator/tests/test_check_docs.py` | RuleOps doc の列挙 pin、欠落と `ruleops.md:N` 参照の positive control | enumerated doc 消失テスト [test_check_docs.py:2083](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_check_docs.py:2083>) |
| `orchestrator/tests/README.md` | `test_ruleops.py` を pytest-only allowlist へ追加 | 二重 runner 契約 [orchestrator/tests/README.md:75](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/README.md:75>) |

`tools/run_tests.py`、既存 correctness checker、hooks には接続を追加しない。新テストが通常の全走で RuleOps validator を検査し、運用時は standalone `check` を明示実行する。Git履歴・insight参照の成立性を全 pytest 起動の preflight に混ぜない。

## テストと変異候補

境界テストは少なくとも次を置く。

- synthetic repo の direct test、nested insight、範囲外の `output/reports`、campaign insight、freeze、submodule/gitlinkを literal expected set で検査する。
- 同じ HEAD で inventory JSON が byte-identical、path順が決定的である。
- worktree の target bytes を未 commit 変更しても HEAD inventory の OID/sizeが変わらない。
- schema missing/extra/duplicate key、非UTF-8、oversize、symlink ledger、絶対 path・`..`、kind不一致、target不存在、blob driftを拒否する。
- test candidateについて replacement guard/node欠落、自己 replacement、node不存在、意味語欠落、未レビュー current/history hit、shallow repoを拒否する。
- receipt の candidate除外欠落、baseline/restored赤、mutant生存、replacement node以外だけの失敗、head非祖先を拒否する。
- insight candidateについて authority/default marker欠落、非 derived class、`.py/.sh/.patch`、source不存在・blob drift・target自身または同時候補をsourceにする循環、source未引用、残存 referenceを拒否する。
- `delete` 等の未定義 subcommandを argparse errorにし、inventory/inspect/check 前後で HEAD/index/worktreeに変更がないことを確認する。
- production の scope/key定数から期待値を導出せず、test側に literal scopeとexact schema keyをpinする。

事前登録すべき変異候補は次のとおり。

1. test path regexを空集合化。
2. insight scopeを `output/**` へ拡大。
3. blob sizeを HEAD treeでなく worktree `stat()` から取得。
4. ledgerの期待OIDを現在OIDから導出して常に一致させる。
5. ledgerの `kind` をpath照合なしで信頼。
6. reference scanを常に空集合化。
7. authority欠落を暗黙に `none` とする。
8. semantic searchから履歴側を除去。
9. receipt の `candidate_excluded` または baseline/restored 検査を除去。
10. mutantの赤を replacement nodeとの結び付けなしで `KILLED` と扱う。
11. `check` の validator 呼出しを外して常時 rc=0。
12. `delete` subcommandを追加。

受入コマンド案は以下。今回は一つも実行していない。

```bash
python3 -m pytest -q orchestrator/tests/test_ruleops.py
python3 tools/ruleops.py inventory --kind all >/dev/null
python3 tools/ruleops.py inspect orchestrator/tests/test_plain_runner_coverage.py --query '偽緑'
python3 tools/ruleops.py check --ledger docs/ruleops-candidates.json
IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
# commit 後
python3 tools/check_ai_provenance.py
```

## scope 外

- test/insight の削除、移動、archive、圧縮、ledgerからの自動適用。
- candidate の自動選出、年齢・size・reference 数による安全判定。
- pytest の価値二層化、marker変更、探索 loop の検査順変更。
- correctness gate、受理集合、certified selection、fitness、proof-chain bytesの変更。
- `output/campaigns/**`、WAL、campaign lock、freeze、`output/reports/**`、`output/env/**`、CCBench submodule、`docs/failures.md` 等の inventory/retirement。
- 既存348件の登録、既存 heterogeneous mutation ledger の移行。
- submodule 内 sourceを `source_artifacts` として証明する v1 拡張。
- 自然言語 hit の真偽自動判定。CLI は完全列挙と drift 検出までで、意味判断と削除裁定は人間に残す。
- 性能計測。受入時間を性能値として扱わない。

放置しても直ちに correctness や proof chain は変わらない。一方、全走対象と insight が単調増加し、反復コストと高価値証拠の発見性が悪化するという親 brief の成果物影響 [parent-brief.md:9](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/parent-brief.md:9>) は残る。外部資料も、守りを外すと既知 reward hack が再発し、積み増すと反復が重くなる構造を記録している [external-consultation-scope-and-axes.md:144](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-27_external-consultation-scope-and-axes.md:144>)。

## 総括

最小で安全な案は、P1・P3を採用し、P2を「候補除外済み typed mutation receipt」と「明示的 non-authority + source pin + reference closure」へ強化した standalone RuleOps である。初期 ledger は空、既存成果物の削除・移動はゼロ、runner本体への接続もゼロとする。

親 brief の件数は正しいが byte 数は現 HEAD と不一致なので、固定値を実装・テストへ転写せず動的 inventory にする。pytest は未実走であり、緑の結果はない。