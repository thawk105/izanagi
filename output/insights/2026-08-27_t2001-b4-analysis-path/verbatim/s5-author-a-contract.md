## 前提の確認

指定された4資料をすべて末尾まで読了した。

- `s4-ruling.md`
- `ref-prereg-b4.md`
- `s2-plan.md`
- `ref-decisions.md`

裁定を優先し、Web検索、他ファイル編集、commit は行っていない。

## 実装したもの

- [p3_b4_analysis_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:1)

  - A1: `B4AnalysisInvalidReason` を逐語どおり12 member化。
  - A2: `Fraction`、整数、整数比だけを受理。float は domain error。
  - A4: `B4ThetaRootOutwardEnclosure` として、exact 根を挟む80回二分法の外向き有理数包囲を保持。
  - A7: 全型を `B4` 接頭辞化し、全 wire dataclass で schema version を必須化。
  - B3: block id・件数・reference 3項・違反件数を純関数内で照合。観測値がない ledger hash は domain 検査だけ行う境界を docstring に明記。
  - `block_score()`、exact 符号検定、Clopper-Pearson 根包囲、7分岐の全域 `evaluate_analysis()` を実装。
  - `A_MIN` は `effect_below_a_min` 注記だけに使用。

- [test_p3_b4_analysis_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_contract.py:1)

  - 12理由を単独発火させる12 fixture。
  - 境界込み tie、float 拒否、missing の非除外と順位を固定。
  - protocol violation、汚染、treatment 不足の優先順を固定。
  - `m=6, W=6, ties=195` による A10/M7 変異検査。
  - exact p値、根包囲、`m=0`、全域性を検査。
  - 末尾に self-runner を配置。

A3・A5・A6・A8・A11は後続単位の所有範囲。A9の追加 meta-test 範囲は実走対象へ含めたが、下記インフラ障害で起動していない。

## 実走結果

専用テスト:

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_contract.py -q
```

補強前2回、現行 bytes 1回とも `rc=16`。`qstat -Q preflight rc=1` により dispatch child が起動せず、実走 nodeid は0件。テストの赤ではなく、緑とも扱っていない。

meta-test は次を一括指定した。

```text
python3 tools/run_tests.py \
  orchestrator/tests/test_campaign_import_invariant.py \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_pytest_collection_config.py \
  <一覧検査の閉包にある29 exact nodeid> -q
```

同じく `rc=16`、実走 nodeid 0件。

非 pytest 検査は `rc=0`:

- 両ファイルの AST parse
- `git diff --check`
- 禁止 import・API・literal・`perf` 条件・結合文字の静的走査
- production import smoke
- `12 reasons`、`p_on=1/64`、根包囲の短い算術 smoke

runner が生成した4件の ignored dispatch receipt は、2ファイル限定を保つため削除した。再生成可能である。

## 受理集合

従来はこの module が存在せず、B-4 分析入力の受理・拒否経路も存在しなかった。既存 caller の挙動は変更していない。

新APIは次を受理する。

- schema versionが一致するB4型
- 201個の一意な既知 block
- `Fraction`、整数、または明示的整数比
- exact なreference束縛、正しいthroughput/status契約、真偽値
- lowercase SHA-256形式のhash

float、件数違反、未知・重複id、束縛不一致、型・domain違反は全行を残したまま `analysis_invalid` とし、protocol violationへ写す。manifest・registry hashの実bytes照合は受理せず推定もせず、単位Dへ残している。

## 波及可能性

- 現在の所有外 caller: なし。
- 将来 caller:
  - 単位B adapterがB4 observation型を構築する。
  - 単位C ledgersがbindingとscheduleを構築する。
  - 単位Dがartifact bytesからhashを再計算して本APIへ渡す。
  - 単位E consumerが定数・enum・挙動を凍結文面と照合する。
- 共有 fixture: なし。新テストのhelperとfixtureは当該ファイル内だけ。
- consumer test: 一覧検査の閉包26件、追加4 node、将来のadapter・ledger・path・consumer各テスト。
- sanctioned CLI、artifact writer、producer、report generator、certified selectorへの配線はない。

## 未了と限界

- 実装済みだが、pytest nodeはすべて未実走。
- 制約 meta-testも未実走。
- `qstat -Q` が利用可能になった計算経路で、親が専用テストとmeta-testを再実走する必要がある。
- 単位Aだけでは事前登録 §6 前提条件9を充足しない。
- authority producer、永続writer、file-drawer閉包、ledger bytes照合は未実装。
- ファイルはuntrackedで、commitしていない。

## 総括

指定された2ファイルだけを作成した。  
12理由、exact有理数、外向き根包囲、B4型、内部束縛照合を実装した。  
順位規則と7分岐順、`A_MIN`非閾値化を独立fixtureで固定した。  
静的検査とimport smokeは成功した。  
pytestはPegasus dispatch infrastructure failureにより未実走であり、closedとは扱わない。