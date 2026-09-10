## 結論

親の暫定裁定は部分的に反証される。

今日の production code で選択規則を強制しない実在経路は、C06 だけでなく `gate-check` の再読込 fallback を含む **2 群**である。したがって (P1-1) と (P1-2) は refuted、(P1-3) と、補正付きの (P1-4) は real と判定する。

## 母集合の定義と権威

独立 AST 走査の母集合は次のとおり。

- `orchestrator/**/*.py` と `tools/**/*.py` の計 764 file を全て `ast.parse`。
- production inventory は、path component に `tests` または `__pycache__` を含むものを除いた 399 file。
- test fixture、docs/output、定義・docstring・annotation、`load_legacy_freeze`、loader 自身の構築を除外。
- module alias、direct-import alias、単純代入 alias を解決した。production 内に対象 API の代入 alias、`__all__` re-export、定数名による `getattr` / `__import__` 呼出しは無かった。

`load_ratified_freeze` の production caller 集合を exact 一致で固定する repo 内メタテストは実在しない。したがって、この 9 callsite の正本は今回の AST 走査である。補助的には、loader 外の `RatifiedFreeze(...)` 構築が無いことを [test_s8b_ratified_freeze.py:2501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_ratified_freeze.py:2501) が固定している。

一方、残件 (c) の `verify_manifest` caller には権威ある閉包がある。[test_s8b_oracle_manifest_contract.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_manifest_contract.py:31) の exact set と [同:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_manifest_contract.py:99) の equality assertion を正本とする。集合は driver / report / judge / verdict の4 fileである。同テスト自身も動的 import / `getattr` は射程外と明記しているが、今回の追加 AST 走査ではその形の実 caller は無かった。

## 直接 loader callsite の全閉包

| production callsite | enclosing function | 分類 |
|---|---|---|
| [s8b_oracle_manifest.py:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:1205) | `build_approved_manifest` | `:1206` の狭い API で強制済み |
| [s8b_oracle_report.py:2547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_report.py:2547) | `main` | `:2548` で強制済み |
| [s8b_oracle_judge.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_judge.py:749) | `main` | `:750` で強制済み |
| [s8b_verdict.py:828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_verdict.py:828) | `main` | `:829` で強制済み |
| [s8c_result_judge.py:2076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8c_result_judge.py:2076) | `_load_selection_checked_ratified_floor` | `:2078` で強制済み |
| [s8b_oracle_driver.py:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:644) | `gate_check` | `:664` の `launch_validate` で強制済み |
| [s8b_oracle_driver.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:1335) | `run_block` | `:1351` の `launch_validate` で強制済み |
| [p3_autonomous_workload_trial.py:4957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:4957) | `run_trial` | **未強制、C06 群** |
| [s8b_oracle_driver.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:496) | `_gate_check_core` | **未強制、production fallback 群** |

従って、9 callsite / 9 function / 7 module の内訳は、狭い API 強制済み 5、`launch_validate` 強制済み 2、未強制 2 である。

## `_gate_check_core:496` は除外できない

これは単なる private self-load ではなく、公開 CLI から到達する。

1. production CLI は [s8b_oracle_driver.py:2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:2055) で `gate_check` を呼ぶ。
2. 最初の raw freeze load は `gate_check:615`。失敗すると `:619` から、`verified` も `launch_validated` も無い `_gate_check_core` へ入る。
3. core は [同:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:459) で同じ freeze を再読込する。
4. 初回失敗後にこの再読込が v2 として成功すると、`:487` の v2 branch から `:496` の `load_ratified_freeze` へ進む。
5. その後は `:503` の SHA equality だけで、`assert_g1_floor_selection_identity` も `launch_validate` も呼ばず、`:589` で `GateDecision` を返す。CLI は `:2058-2059` でその判定を外部へ出す。

したがって「private だから production entry ではない」は成立しない。これは初回失敗→再読成功という具体的な production CFG であり、仮想 caller ではない。

`gate_check(ratified=...)` の通常 v2 経路は、`:641` で注入値を candidate にしても必ず `:664` へ渡すため強制済みである。ただし上記 fallback に入ると、core は `:490-491` で注入値を raw active として採用でき、やはり launch token を要求しない。repo 内唯一の production caller `main:2055` は `ratified=` を渡さないので、注入 variant 単独は新たな production 群には数えないが、seam が全経路で安全という (P1-2) の根拠にはできない。

## 間接 consumer の扱い

間接経路は捨てず、取得元と最終作用へ畳み込んだ。

- `_build_manifest_from_ratified` は [s8b_oracle_manifest.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:842) で `RatifiedFreeze` を受け、manifest を生成する。唯一の production call は `build_approved_manifest:1245` で、その前に `:1206` の強制がある。writer は `:1260`。
- `_prepare_s8c_budget_inputs` は [p3_autonomous_workload_trial.py:2082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:2082) で document/hash/holdouts を使い、`run_trial:4958` から `reserve_all_cells:4964` へ渡す。これは C06 未強制群に含める。
- `_ratified_floor_binding` は [s8c_result_judge.py:2045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8c_result_judge.py:2045) で値を読むが、production 経路は `:2076-2081` の強制済み helper から `verify_floor_bytes:2129` へ進むため、強制済み群へ畳む。
- `read_floor_source_blob` は verdict の [s8b_verdict.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_verdict.py:849) で使われるが、同じ `main` の `:828-830` が先に選択強制と reverify を通す。
- direct-import alias は [p3_autonomous_workload_trial.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:108) と [s8c_result_judge.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8c_result_judge.py:26) にあるが、上表の callsite そのものであり別群を増やさない。

「値として使うだけだから」と production consumer を除外した箇所はない。cross-module consumer は全て実際の gate/publish chainへ畳み、ratified module 内部の validator は独立入口ではなく API 実装として扱った。

## (P1) 判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| (P1-1) | **refuted** | 未強制は C06 だけでなく driver fallback `:496` もある。C06 は D1371 の不実装裁定対象だが、driver は実在 CLI gate。 |
| (P1-2) | **refuted** | `gate_check` の通常 v2 path は `:664` で強制する一方、初回 load 失敗→core 再読成功では `:496` または注入値 `:490-491` を launch token 無しで gate に使う。 |
| (P1-3) | **real** | genuine 正負4 node が現存し、実 loader と launch / 狭い API を通す。 |
| (P1-4) | **real（数え方の補正あり）** | raw `verify_manifest` caller は権威ある閉包上4 file。だが official artifact を先へ生成する production chain は report / judge / verdict の3 CLIだけで、全て選択強制済み。直接 library 呼出しには repo 内 caller がない。 |

C06 は [D1371:43690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/decisions.md:43690) のとおり現時点では実装しない。現コードでも schedule authority は [p3_autonomous_workload_trial.py:2074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:2074) で無条件に失敗し、budget ledger へ到達しない。

## (c) と (d) の現況

(c) について、1236 が閉じた狭い内容は今日も成立している。

- 旧 public 名 `build_manifest` / `build_manifest_from_ratified` / `write_manifest` は無く、現定義は `_build_manifest`、`_build_manifest_from_ratified`、`_write_manifest` の private 名である。[s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:818)
- exact 負例 `test_ungated_manifest_apis_are_not_public` も [test_s8b_oracle_manifest.py:1248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_manifest.py:1248) に残る。
- `verify_manifest` が選択 token を要求しない非対称は [s8b_oracle_manifest.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:1019) に残るが、これは1236自身が既に「閉じていない範囲」と記録した事項であり、回帰ではない。[worklog 1236:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/archive/worklog-phase3-0903-1236.md:26)
- artifact-producing production call は report `:2561`、judge `:761`、verdict `:857/:864` に閉じ、各 main は先に選択強制する。従って直接 library 呼出し向けの新規 gate は禁止された仮想リスク対応になる。

(d) も今日なお閉じている。genuine 4 node は [test_s8b_ratified_verify.py:1031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_ratified_verify.py:1031)、`:1046`、`:1060`、`:1075` に存在し、実 loader はそれぞれ `:1038/:1053/:1067/:1082`、launch / consumer callee は `:1041/:1055/:1070/:1084` で発火する。実導出本体も [s8b_holdout_freeze.py:1851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_holdout_freeze.py:1851) から `_derive_floor_selection_eligibility:1867` へ接続されたままである。

従って [1345 carry:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/docs/archive/worklog-phase3-0908-1345-1347.md:311) の「(c)(d) が残件」と「3 群」は古い。1236 の「(c)(d) 完了」は維持されるが、同 entry の `driver:496` 除外だけは今回の独立検算で破れた。

## 推奨プラン

実装面ゼロは妥当でない。driver の実在 production fallback だけを閉じる最小差分を推奨する。

- [s8b_oracle_driver.py:402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:402): `_gate_check_core` の v2 authority を exact `LaunchValidatedFreeze` に限定する。raw `RatifiedFreeze` 注入と core self-load を v2 gate authority にしない。
- 同 `:487-507`: `ratified_error` は従来どおり refusal にする。それ以外の v2 で `launch_validated` が無ければ fail-closed とし、`:496` の self-load を除去する。SHA 比較対象も `launch_validated.ratified` のみにする。
- 同 `:619-683`: core 呼出し引数を整理する。通常 v2 は既存どおり `:664` で validation を行い `:677-683` から token を渡す。初回 loader failure は二度目の snapshot で許可へ反転させない。
- `orchestrator/tests/test_s8b_oracle_driver.py` の `test_gate_check_core_rejects_reverified_freeze_token` 付近 (`:2462`) に、v2 raw freeze／token 欠落拒否を追加する。
- 同 file の `test_v2_standalone_gate_check_requires_full_floor_validation` 付近 (`:5436`) に、初回 raw load 失敗→次回成功を模した regression を追加し、core の再読で allow へ反転しないことを固定する。通常 self-load／`ratified=` 注入が `launch_validate` を通る既存正負例は維持する。
- (c)(d) の code/test は変更しない。C06 にも触れない。
- insight に 9 callsite、2未強制群、権威ある `verify_manifest` closure、1345 carry の訂正を記録し、worklog/decisions は archive 直接編集ではなく spool fragment で更新する。

この差分は `s8b_oracle_report.py` と `s8b_oracle_judge.py` を触らない。`_GENERATOR_SOURCES` は [s8b_oracle_manifest.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:65) の5 fileで、driver は含まれない。したがって凍結成果物の再発行は不要である。

D1241 / D1313 の advisory・non-certifying 上限は一切変更しない。

## 非実走

この段では書き込み、commit、branch操作、pytest実走を行っていない。上記は AST と静的 CFG の検査結果であり、テストを緑とは申告しない。

## 総括

母集合は production loader callsite 9件。内訳は狭い API 強制済み5、`launch_validate` 強制済み2、未強制2（C06 1、driver fallback 1）。

(P1-1) refuted、(P1-2) refuted、(P1-3) real、(P1-4) real。ただし `verify_manifest` の直接 caller は3ではなく権威ある閉包上4 fileで、artifact-producing continuation が3 CLIである。

この wave は実装面あり。`s8b_oracle_driver.py` の core self-load/raw authority を exact launch token 要求へ縮め、driver testと記録だけを更新する。report/judge、(c)(d)、C06には触れず、凍結成果物の再発行も不要。