## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| A-1 claim literal | closed | 4 つの既存軸を現行 literal へ exact mapping。[probe.py:416](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:416)、[test:2102](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_t2187_adaptive_const_probe.py:2102) |
| A-2 binary/cache singleton | closed | F2 に従い row group と published の singleton 条件を撤回。各 row の型・形式検査は維持。[probe.py:2517](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:2517)、[probe.py:2749](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:2749)、[probe.py:3079](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:3079) |
| A-3 CLI 正規形 | closed | canonical seed、raw thread 先行検査、option 重複拒否を実装。[probe.py:755](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:755)、[probe.py:1564](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:1564)、[probe.py:3237](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:3237) |
| A-4 generic legacy 分岐 | closed | `_legacy_published_claim` を削除し、published も同じ閉写像だけで検証。[probe.py:2994](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:2994)、[test:2146](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_t2187_adaptive_const_probe.py:2146) |
| B-1 performance 投入 script | 親担当 | repo 外投入 script の修正事項。[review-b:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage6-review-b.md:3) |
| B-2 singleton blocker | closed | F2 による二層撤回。[probe.py:2749](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:2749) |
| B-3 group 失敗診断 | closed | 24 path 完備後の reject を create-only failure JSON へ記録。書込み失敗は握り、終了コードは変更しない。[probe.py:3112](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:3112)、[test:1234](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_t2187_adaptive_const_probe.py:1234) |
| B-4 再投入分類 | 親担当 | repo 外投入 script の修正事項。[review-b:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage6-review-b.md:33) |
| B-5 pilot 引数 | 親担当 | repo 外投入 script の修正事項。[review-b:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage6-review-b.md:43) |
| B-6 stale artifact | 親担当 | repo 外投入 script の修正事項。[review-b:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert/out/stage6-review-b.md:53) |
| B-7 claim consumer | closed | producer・group・published を同じ exact mapping に統一。[probe.py:420](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:420)、[probe.py:2994](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:2994) |

## 変更ファイル

- [t2187_adaptive_const_probe.py:416](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/tools/pegasus/probes/t2187_adaptive_const_probe.py:416)
  - claim の exact 閉写像化
  - generic legacy 分岐削除
  - binary/cache singleton 撤回
  - failure receipt の best-effort create-only 発行
  - canonical seed、raw thread、重複 option 拒否

- [test_t2187_adaptive_const_probe.py:989](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265cert-unit-a/orchestrator/tests/test_t2187_adaptive_const_probe.py:989)
  - F2 の binary/cache singleton 正負期待を削除
  - failure receipt、claim 閉写像、canonical seed、重複 option、raw 検査順の負例を追加

- `t2187_adaptive_const_probe.pbs` は変更なし。
- docs 編集・commit は実施していない。

## 変更・追加した nodeid

- 変更:
  - `test_group_receipt_requires_exact_24_terminal_request_set`
  - `test_step_policy_seed_rejects_non_decimal_or_out_of_uint64`
  - `test_published_claim_compatibility_is_exact_for_the_four_old_literals`
  - `test_published_cohort2_receipts_reaccept_exact_old_claim_identities`
- 追加:
  - `test_certification_axis_options_reject_duplicates[threads]`
  - `test_certification_axis_options_reject_duplicates[step-policy-seed]`
  - `test_certification_raw_thread_literal_rejects_before_thread_parser`

## 実走結果

- 対象ファイル全体: wrapper rc=16。
- 上記 nodeid と親実測赤 2 件の選択実行: wrapper rc=16。
- いずれも `qstat -Q preflight rc=1` の dispatch infrastructure failure で `child_started=false`。したがって実装済み・未実走であり、緑とは申告しない。
- `git diff --check` は rc=0。

## 変えた既存挙動

- 4 つの既存 48-thread 軸は既存 literal をそのまま返す。
- その他の有効軸だけが実 thread、実 seed、非診断 build 条件を含む生成 claim になる。
- group 間で binary/cache が異なっても受理可能になったが、各 row の両 field の実在・形式検査は維持。
- 24 path 完備後の group reject は failure JSON を残す。certified request の終了コードは従来どおり 0。
- 重複 option とゼロ埋め seed を新たに拒否する。F2 以外の既存拒否は削除していない。

## 総括

F1〜F4 と対応テストを許可された 2 ファイルへ反映した。  
親実測赤 2 件の直接原因はコード上で解消した。  
テストは dispatch 障害により未実走。  
docs・PBS・commit は変更していない。