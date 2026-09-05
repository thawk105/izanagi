D1-a、D1-c、D1-d を所有 4 file 内で実装しました。commit と docs 編集は行っていません。

### 実装内容

- [s8b_floor_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit2/orchestrator/campaign/s8b_floor_contract.py:35)
  - v4 legacy、v5、readable schema 集合を追加。
  - `_RESULT_KEYS` を v4 alias のまま維持。
  - schema 別 exact key 集合と `schema` kw-only 引数を追加。
  - `RESULT_SCHEMA` と既存呼出しの default は v4 のまま。

- [s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit2/orchestrator/campaign/s8b_floor_stats.py:683)
  - v5 proof の shape、artifact header、独立 proof の順で検証。
  - v4 で expected proof を拒否し、v3 の既存拒否文字列を保存。
  - live wrapper は v5 のみ registry inspector を局所 import。
  - binding は外部 freeze、canonical protocol、canonical schedule だけから導出。
  - unit 1 API への fallback は追加していません。

### テスト追加

[s8b_floor_stats のテスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit2/orchestrator/tests/test_s8b_floor_stats.py:722)へ 11 function、parametrize 展開後 13 node を追加しました。M11〜M16、v4 extra key、v4/v5 expected proof 契約、header 2 digest、binding 3 field、live v4 tripwire、live v5 の外部 binding と独立 proof 利用を直接検査します。

### 検査結果

- `check_docs`: 違反なし。
- `check_codex_agents.py`: OK。
- 4 file の AST compile と test module import: 成功。
- `git diff --check`: 成功。
- pytest focus 走と collect-only は、ともに runner の Pegasus dispatch が `qstat -Q` preflight で `rc=16`。child は起動されず、pytest node は 0 件実行です。
- login admission ledger も sandbox 内から安全確認不能だったため、規律に反する直接 pytest は行っていません。
- `test_official_perf_surface_inventory_is_exact` は静的確認上 signature を pin していませんが、実走は同じ理由で未実施です。
- runner が生成した所有外 receipt directory 2 件は除去済みです。

### 所有外への波及

現時点では v4 default のため既存挙動は不変です。将来の v5 切替時には `s8b_holdout_freeze.py:1429,1620`、`s8b_ratified_freeze.py:2360,3281`、`s8b_floor_campaign.py:6684` と、`s8b_v2_freeze_fixture.py:340`、`test_s8b_ratified_verify.py:460`、`test_s8b_floor_campaign.py:6552` の追従確認が必要です。

## 総括

- 変更: contract `+27/-6`、stats `+94/-5`、contract test `+59/-0`、stats test `+348/-0`。
- 合計: 4 file、`+528/-11`。所有外の残存変更なし。
- 新設 test: 11 function、13 node。既存 contract 2 node は assertion を保持して拡張。
- 実走: pytest 0 passed / 0 failed、対象 2 file 全 node 未実走、runner infrastructure `rc=16`。
- unit 1 待ち node: 0。新設 v5 node は fake API 注入済みだが、統合後の実 API 実走は親作業。
- 不変: v4 artifact の受理集合、producer schema、v3 拒否文字列。
- 波及: 所有外 caller 5 箇所と共有 fixture 3 箇所を上記に列挙。
- 未実装: 所有 scope 内なし。実台帳二世代 M14、coverage、producer、D2 は裁定どおり後続。