R-1 は **closed** です。変更は [test_pegasus_policy_registry.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:96) のみです。commit は作成していません。

### 変更内容

- nested `with` の bind 名だけで shadowing を判定せず、`context_expr` と bind 先の provenance を確認。
- `with handle as handle` は同一 shared handle として走査を継続。
- `with open(sys.argv[2]) as handle` は別 object への再束縛として従来どおり走査を打ち切り。
- R-1 の攻撃形を positive control として追加しました。[positive control](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:473)

| 形 | 修正前 | 修正後 |
|---|---|---|
| R-1 `with handle as handle` | finding `[]` | `[(5, "certify_walltime_s")]` |
| 直接 shared read | 検出 | `[(3, "certify_walltime_s")]` |
| nested task-policy shadowing | finding `[]` | finding `[]` |

### 検査

- `python3 -m py_compile ...`: rc 0
- helper 直接評価: R-1、直接形、shadowing control とも期待値どおり
- consumer test function 直接評価: PASS
- plain-runner harness 静的検査: PASS
  - 初回の単独 import は `skiputil` の検索パス不足で失敗しましたが、テストディレクトリを import path に設定した静的再評価は PASS。pytest の失敗ではありません。
- `git diff --check`: rc 0
- `python3 tools/check_codex_agents.py`: rc 0
- `python3 tools/check_docs.py`: rc 0

指定 wrapper による対象テストと meta-test は dispatch 前に停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
wrapper rc=16
```

pytest node は一件も実行されておらず、緑は主張しません。

### 所見対応

| 所見 | 判定 | 確認 |
|---|---|---|
| R-1 / F7 | closed | 攻撃形を検出し、既存 task-policy shadowing control は非検出を維持 |
| F1 | closed・非回帰 | walltime／reserve assertions は変更なし |
| F2 | closed・非回帰 | `_tracked_paths()` の exact membership は変更なし |
| F3 | closed・非回帰 | flat-layout 検査は変更なし |
| F4 | closed・非回帰 | symlink component／containment 検査は変更なし |
| F5 | closed・非回帰 | certify shell の symlink 拒否は変更なし |
| F6 | partial・裁定どおり | scanner の限定 docstring、検出範囲とも変更なし |

### 静的な波及範囲

- helper の caller は同じテストファイル内の `_moved_reads()` のみ。production caller はありません。
- 共有 pytest fixture は使用しておらず、fixture 波及はありません。
- tracked `.py`／`.sh` consumer scan のうち、同一 handle の nested 再束縛だけが新たに検出対象になります。
- 他の test file、shell、policy、docs への編集はありません。

### 最終差分

`git status --short`:

```text
M  orchestrator/tests/test_pegasus_floor_tools.py
AM orchestrator/tests/test_pegasus_policy_registry.py
M  orchestrator/tests/test_pegasus_tools.py
M  tools/pegasus/certify_calibration.sh
M  tools/pegasus/floor_campaign.sh
A  tools/pegasus/policies/calibration_v1.json
A  tools/pegasus/policies/floor_v1.json
A  tools/pegasus/policies/registry_v1.json
M  tools/pegasus/submit_certify.sh
M  tools/pegasus/submit_floor.sh
```

R-1 の unstaged 差分は対象ファイルだけです。

```text
orchestrator/tests/test_pegasus_policy_registry.py | 33 +++++++++++++++++-----
1 file changed, 26 insertions(+), 7 deletions(-)
```

base `7b24f81` からの全差分は 10 files、657 insertions、36 deletions です。

```text
git diff --exit-code 7b24f81 -- tools/pegasus/policy.json \
  output/env/pegasus \
  orchestrator/qualification/t126_reservation_policy_v1.json
rc=0
```

## 総括

- R-1 は **closed**。
- 同一 shared handle の nested 再束縛を provenance に基づき検出します。
- 正当な nested task-policy read の非検出は維持しました。
- 既存の直接 shared read positive control も検出を維持しています。
- F1〜F5・F7 に回帰はなく、F6 は裁定どおり partial のままです。
- pytest は dispatch 障害で未実行のため、親による計算ノード実測が必要です。
- protected path は base 比 rc 0、commit は作成していません。