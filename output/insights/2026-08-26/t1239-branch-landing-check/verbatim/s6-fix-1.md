指定された 2 ファイルだけを修正しました。commit、add、stash 等は実行していません。

- [check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py)
- [test_check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py)

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | merge の証明 path を全 parent 差分の積集合へ変更。parent edge provenance は維持 |
| F2 | closed | 取得済み候補をすべて照合後、一致ゼロの場合だけ `truncated` |
| F3 | closed | 既定候補数を 64 から 1024 へ変更 |
| F4 | closed | legacy/v2 receipt の field、型、日付、identity、allocation、重複 JSON key、重複 receipt を検証 |
| F5 | closed | spool deletion の旧 blob を hash 化し、exact receipt と identity で証明 |
| F6 | closed | graft、標準 replace ref、`GIT_REPLACE_REF_BASE` namespace を検出。Git child は最小環境で起動 |
| F7 | closed | corpus を receipt miss/task 検索時だけ構築し、`git cat-file --batch` で一括読込。Python loop に deadline 検査を追加 |
| F8 | closed | merge-base の呼出しと一意性要求を除去 |
| F9 | closed | corpus、ledger、task、patch-id の失敗を observation 内へ隔離 |
| F10 | closed | closure/history/receipt blob 打ち切りの outcome、観測数、limit、elapsed を保持 |
| F11 | closed | matched unit 数、全一致、単一 file 最大被覆数を追加。単一 file 過半数だけ `matched` |
| F12 | closed | `unresolved_fragment_candidates` に path、hash、receipt、unit 数、hit 先を出力 |
| F13 | closed | `files` を unique path の連言集約へ変更。`proof_units` に edge provenance を分離。tip net 数も別 field 化 |
| F14 | closed | 全履歴走査を closed-world 負証明時だけ実行 |
| F15 | closed | hash 例外を evidence へ伝播。非 UTF-8 corpus を `error` 化し、完全性・読取量を出力 |
| F16 | closed | deletion guard 5 field を追加 |
| F17 | closed | `refs_stable` を廃止。開始 snapshot 束縛、終了時一致、連続安定未証明を分離 |
| M2' | closed | ledger probe の verdict 反映を単一の無効 gate に再照準 |
| M4' | closed | 全 parent 積集合を単一式にし、第 1 parent 差への変異を検出する fixture を追加 |
| M8' | closed | 別 path blob を拒む実効 decision へ再照準 |

`partial`、`regressed` はありません。

F3 の 1024 は、親が実 repo で `landed` を確認済みの候補上限です。F2 後は 33 番目の一致を 64 でも拾えますが、頻繁に更新される path に対して実測済みの余裕を残し、履歴全走査上限は F14 により positive proof の gate から外しました。

## 実データ smoke

現 checkout に残っていた対象 ref は `worktree-cleanup-branches-20260825` だけでした。既定 60 秒で実走した結果:

- verdict: `indeterminate`、裁定 A3 どおり
- total: 0.523 秒
- Git child: 21
- corpus: 754 files、19,846,833 bytes、0.202 秒、完全
- 2 fragment とも 5 単位中 1 単位だけ一致し、`not-matched` / weak coverage
- 両 fragment を path、whole-file SHA、body SHA、hit 先付きで列挙

旧診断の約 1,500 Git child、57 秒に対し、F7 の実データ経路が既定予算内で完走することを確認しました。

## pytest と静的検査

pytest は実装済み・未実走です。正規 runner を対象ファイルで 2 回、collect-only で 1 回、consumer test で 1 回起動しましたが、すべて以下で pytest child 起動前に終了しました。

```text
qstat -Q preflight rc=1
child_started=false
dispatch infrastructure rc=16
```

したがって緑と申告できる pytest nodeid はありません。対象は静的に 46 test function、parametrize 展開後 47 node です。

未実走範囲:

```text
orchestrator/tests/test_check_branch_landed.py
orchestrator/tests/test_plain_runner_coverage.py
orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests
```

確認済み:

- `python3 -m py_compile` — rc=0
- whitespace check — 指摘なし
- U+0300〜U+036F — 検出なし
- `git status --short` — 指定 2 ファイルだけ
- 実 repo cleanup smoke — 期待 verdict、JSON schema、deadline 内完走

assertion failure として観測された赤はありません。ただし 47 node と consumer test は未起動なので、緑ではありません。

## 変異点

| 変異 | 実装位置 | masking がない理由 |
|---|---|---|
| M1 | `tools/check_branch_landed.py:1041` | receipt miss unit は ledger が非決定なので、変異 verdict がそのまま branch 合成へ届く |
| M2' | `tools/check_branch_landed.py:1277` | strong ledger hit の receipt-miss fixture で、この gate を有効化すると conjunction より前に `landed` になる |
| M3 | `tools/check_branch_landed.py:461` | 中間 secret の fixture は tip state が exact。closure を tip-only にすると他層は受理する |
| M4' | `tools/check_branch_landed.py:547` | fixture の第 1 parent 固有差は main exact。変異後も証拠層は受理し、proof-unit 集合 assertion だけが落ちる |
| M5 | `tools/check_branch_landed.py:595` | mode と content を別 commit から合成した場合だけ mode fixture が `landed` になる |
| M6 | `tools/check_branch_landed.py:1052` | 候補打ち切り fixture に他の positive evidence はなく、変異した打ち切り verdict が直接伝播する |
| M7 | `tools/check_branch_landed.py:325` | scope contract を単一 dict expansion で出力し、schema test が欠落を直接検出する |
| M8' | `tools/check_branch_landed.py:1060` | 同一 blob 別 path fixture はこの decision まで到達し、変異時はそのまま `landed` になる |
| M9 | `tools/check_branch_landed.py:1260` | ref movement fixture で他層は conclusive。snapshot 比較だけが `indeterminate` にする |
| M10 | `tools/check_branch_landed.py:1281` | landed sibling と indeterminate sibling の fixture で、優先順位変異が直接 branch verdict を変える |

## 波及と受理集合

静的波及:

- 所有外 caller: なし
- 共有 fixture: 変更なし。新テストは `tmp_path`、`monkeypatch` と file 内 helper のみ
- consumer test:
  - `test_plain_runner_coverage.py`
  - `test_pytest_collection_config.py`
  - 通常の全 pytest collection
- docs、README、設定、既存テスト期待値: 変更なし

受理集合の方向:

- `landed` が増える: merge 積集合、候補先行照合、receipt 済み deletion、merge-base 不要化、positive proof の履歴 gate 除去
- 偽の `landed` が減る: 不正 receipt、identity 不一致、graft、標準外 replace namespace
- A3 は維持: receipt 不在は `indeterminate`。ledger probe は verdict を動かさない
- `not-landed` は完全な closed-world 負証明の場合だけで、緩和していない

## 総括

F1〜F17 と M2'/M4'/M8' は実装上すべて閉じました。閉じなかった所見はありません。

残る不確実性は、正規 runner の infrastructure failure により 47 node と consumer test が未実走であること、および親の 9 ref のうちこの checkout では cleanup 以外を再実測できなかったことです。

親は runner 回復後に対象 47 node と consumer test を実走し、続いて指定 9 branch の verdict を確認してください。特に `t1484`、agent、`t1458`、second が `landed`、cleanup、roadmap、floor、unitB/C が `indeterminate` になることが最終確認点です。