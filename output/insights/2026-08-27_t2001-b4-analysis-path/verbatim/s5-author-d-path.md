## 前提の確認

指定資料と A/B/C 実装、`reflux_formal_consumer.py` の bytes 対応 idiom を確認しました。Web 検索、commit、既存 file の編集は行っていません。

## 実装したもの

指定された 2 file のみ作成しました。

- [p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:170)

  - registry → manifest →実 bytes hash → exact 再生成 →全 registry violation 集計 → slot 遵守導出 → adapter → `evaluate_analysis()` の順序を固定。
  - `registry_violation_count` と `assignment_followed` を公開 signature から排除。
  - 各 arm の申告 `source_artifact_sha256` と実 source bytes を多重集合で一対一照合し、余分な bytes も拒否。
  - loader、parser、adapter の失敗を12理由 enumの `analysis_invalid` へ写し、例外を外へ出さない全域経路を実装。
  - caller の binding を実 registry/manifest から再構築した binding と完全比較。
  - 固定5 module、事前登録 §5.1.1 exact bytes、schema versionを canonical receipt化。consumer 不在時は省略せず拒否。

- [test_p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py:288)

  - 指定された負例、hash 再計算、slot 遵守導出、余分な source artifact 拒否を実体 API で固定。
  - manifest の申告 hashを変異 bytesに合わせても、追加・削除・並べ替えを exact regeneration が拒否する構成。
  - closure receipt の再生成安定性と member 不在時の fail-closed を固定。
  - 末尾に指定 self-runnerを配置。

## 実走結果

実行要求:

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_path.py -q
```

結果は `rc=16` でした。

```text
qstat -Q preflight rc=1
child_started=false
kind=infra
```

dispatch child は起動せず、実走 nodeid は 0 件です。緑とは扱っていません。runner が生成した一時 receipt 4 file とディレクトリは除去しました。

静的検査は成功しました。

- 両 file の AST parse
- 禁止 import、API、literal、`perf` 条件の走査
- 公開 signature の自己申告引数不在確認
- `git diff --no-index --check` 警告なし
- U+0300〜U+036F 不在
- production に `__main__` なし、test self-runner あり

## 受理集合

`evaluate_b4_artifacts()` は次だけを受理します。

- strict canonical registry bytes
- strict canonical manifest bytes
- raw analysis JSON bytes
- 各 arm に一対一対応する実 source artifact bytes
- 実 ledger bytesと完全一致する `B4ContractBinding`
- exactな `floor`

申告 hashだけの整合、manifest mutation、余分・不足 source bytes、malformed loader入力は protocol violationの `analysis_invalid` になります。

## 波及可能性

- 現在の所有外 caller: なし。
- 共有 fixture: なし。fixture は新 test file 内に閉じています。
- 将来 consumer: 単位 E の preregistration consumer。
- 将来 caller: authority producer、sanctioned CLI、永続 writer、全件 report generator、certified selector。
- repository 全体を走査する import、build authority、spawn census、plain runner、collection coverage等の既存検査へ影響し得ます。今回は dispatch障害により未実走です。

## 未了と限界

- pytestは全 nodeid未実走です。
- `p3_b4_analysis_prereg_consumer.py` は現在不在なので、実 repositoryに対する closure receipt生成は意図どおり fail-closedです。
- authority producer、sanctioned CLI、永続 writer、全件 report、certified selection配線は未実装です。
- 権威 producerが不在のため、事前登録 §6 前提条件9や全件性の問題が解消したとは扱えません。

## 総括

単位 D の artifact bytes から verdict までの統合経路と closure receipt生成器を、指定2 fileだけに実装しました。静的閉包は確認済みですが、正式なテスト実走は Pegasus dispatch障害により未確認です。