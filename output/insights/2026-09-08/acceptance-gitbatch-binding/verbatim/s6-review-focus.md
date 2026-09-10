## 検査前提

read-only の静的検査のみを実施した。pytest は実走しておらず、`fix1.md` の passed／緑という主張は独立確認していない。

## 対応表

| 旧所見 | 状態 | 静的判定 |
|---|---|---|
| D-01 | **partial** | `ls-tree -r -z <40hex> -- <literal...>` と exact `cat-file --batch` は許可され、旧 `cat-file blob` は削除された。ただし `-C` より前の argv が exact 検査されず、余分な global option を受理する |
| D-02 | **closed** | expected と走査対象の双方に `p3_b4_wiring_probe.py` が追加された。第三 caller を消すと `actual != expected` になる |
| C-05 | **closed** | 指定7負例が raw bytes literal で追加された。最終 NUL 負例は「valid expected entry + 未終端 unexpected entry」で、NUL検査削除変異を殺せる |
| C-06 | **closed** | 2 fake とも call marker が追加され、対象分岐の発火、回数、exact argvを検査する。既存の `match` は緩められていない |

## E-01 — Git argv prelude が exact でなく、別 repository 指定を許可する

- **severity:** blocker
- **自己判定:** **real**。[ドリフト] [恒真ゲート]
- **根拠:** `_allow_read_only_git` は `argv[0]` を確認した後、`words.index("-C")` で最初の `-C` を探すだけで、`words[1:separator]` を production の harden prelude と照合していない。その後は `-C` の引数と operation のみを検査する（[`p3_b4_wiring_probe.py:431-468`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/p3_b4_wiring_probe.py:431)）。
- required env、caller stack、`-C` の path 検査自体は残っている（[`p3_b4_wiring_probe.py:470-503`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/p3_b4_wiring_probe.py:470)）。しかし、例えば次の非 production argv はそれらを満たしたまま許可される。

```python
[
    "/usr/bin/git",
    "--git-dir=/tmp/foreign.git",
    "-C", str(_REPO_ROOT),
    "cat-file", "--batch",
]
```

`--git-dir` により object source を別 repository へ向けられるため、`-C == _REPO_ROOT` は意味的な repo root 制約にならない。これは「余分な語を受理しない」という検査条件、および fix 報告の「exact のみ」「repo root 制約維持」という説明（[`fix1.md:3-7`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/artifacts/dev-wave-acceptance-gitbatch-20260908/fix1.md:3)）と一致しない。
- 新テスト helper は prelude を常に固定し、引数として operation しか受け取らない（[`test_p3_b4_wiring_probe.py:58-88`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_p3_b4_wiring_probe.py:58)）。したがって既存の負例群は `-C` 前への余分な語を表現できず、この次元では恒真である。
- **修正案:** production の `/usr/bin/git --no-pager -c ... --no-replace-objects -C` prelude を定数化して prefix 全体を exact 比較し、`-C` の位置も固定する。テスト helper は full argv または prelude override を受けられる形にし、少なくとも `--git-dir=/tmp/foreign.git`、余分な `-c`、harden option の欠落・重複を拒否する負例を追加する。

## D-01 詳細

production `_iter_blobs` の operation は [`contract_loader_binding.py:383-390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:383) と [`contract_loader_binding.py:448-453`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:448) の形であり、新 allowlist の operation grammar とは一致する。

literal prefix、不在 pathspec、重複、絶対 path、空／`.`／`..` segment、NUL、非40桁小文字hex commit、`cat-file --batch` の余分な語は静的に拒否される（[`p3_b4_wiring_probe.py:451-468`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/p3_b4_wiring_probe.py:451)）。旧3語形は allowlist から削除され、負例にも入っている（[`test_p3_b4_wiring_probe.py:108-163`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_p3_b4_wiring_probe.py:108)）。

ただし E-01 により full argv の exactness と repo root の意味的制約が閉じていないため、D-01 全体は partial とする。

## D-02 詳細

expected に `("p3_b4_wiring_probe.py", "_load_runtime", "capture_contract_loader_binding"): 1` が追加され、同ファイルも AST 走査対象になった（[`test_t671_source_binding.py:786-824`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:786)）。

第三 caller を削除すると expected の1件が actual に現れず、末尾の `assert actual == expected` が失敗する。D-02 は closed。

## C-05 詳細

追加された7 fixtureは実装 helperで応答を生成せず、raw bytes literal で構成されている（[`test_t671_source_binding.py:981-1018`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_t671_source_binding.py:981)）。

- 最終 NUL不在: `valid expected entry + unterminated unexpected entry`
- TAB不在
- field数2／4
- 空 raw path
- 空 mode
- malformed OID

これらはそれぞれ parser の NUL、entry framing、mode、OID 分岐（[`contract_loader_binding.py:393-434`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/campaign/contract_loader_binding.py:393)）へ到達する。最終 NUL 検査だけを削除すると `entries.pop()` が未終端 unexpected entry を捨て、正常 batch 応答へ進むため、当該負例は変異を殺せる。C-05 は closed。

## C-06 詳細

`redirected_git_view` は全 call を記録し、exact `rev-parse --show-toplevel` 1回を要求する（[`test_artifact_admission.py:2329-2344`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_artifact_admission.py:2329)）。

`missing_blob` も全 call を記録し、注入条件と同じ prefixを使って ls-tree branch のexact 1回、全 literal pathspec、対象 pathを含む例外を検査する（[`test_artifact_admission.py:2392-2418`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-gitbatch-20260908/orchestrator/tests/test_artifact_admission.py:2392)）。既存の `match="Git top-level"` と `match="git command"` は維持されている。C-06 は closed。

## 回帰・失敗型

| 検査 | 判定 | 根拠 |
|---|---|---|
| 所有 path | refuted | patch の変更は p3 production/test、t671 test、artifact test、ledger の5 pathのみ |
| `contract_loader_binding.py` 変更 | refuted | `fix1.patch` に同ファイルの diff headerなし。変異spec anchorは未変更 |
| 台帳 add-only | refuted | 13 node追加と `19935 -> 19948` のみで、既存entryの削除・値変更なし（[`fix1.patch:41-71`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-gitbatch-20260908/fix1.patch:41)） |
| 既存期待値の弱化 | refuted | artifact test の既存例外 `match` は維持され、marker/assertだけを追加 |
| [恒真ゲート] | **real、限定的** | E-01。D-02/C-05/C-06 は実装分岐を通るが、D-01負例 helperは argv preludeを固定し、prefixへの余分な語を検査できない |
| [ドリフト] | **real** | E-01。報告の「exact のみ」「repo root制約維持」と実装の受理集合が不一致 |
| [権限逸脱] | refuted | 提示patch上は所有5 pathのみ。commit有無は射影資料だけでは独立検証不能 |

## 総括

blocker **1件**、should-fix **0件**。  
D-02、C-05、C-06 は closed、D-01 は partial。  
full Git argv が exact でなく、余分な `--git-dir` で repo root 制約を迂回できる。  
判定: **NO-GO**。