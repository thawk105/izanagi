# Unit 1 実装報告

## 1. 変更した file と要点

- [holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:1)
  - freeze の `holdouts` map から保護 signature を導出。
  - neutral 集合との exact 一致を発行時に要求。
  - direct gflags の正規化、last-wins、間接入力拒否を実装。
  - token 本体を closure 内の `id(token) -> state` に強参照保持し、`state.token is token` で検査。
  - Unit 2 用 issuer hook と admission assert API を公開。
- [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/runner.py:397)
  - `run_once` に keyword-only admission を追加し、tempdir 作成前に gate を実行。
  - subprocess 環境から親・追加環境双方の `FLAGS_*` を除去。
  - `measure_point` は admission が非 `None` の場合だけ下流へ転送。
- [test_holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_holdout_observation.py:1)
  - freeze drift、gflags、identity 攻撃、gateway、環境除去、P1、既存 call shape を網羅。
  - 実 freeze と `trial_registry.HOLDOUT_BINDINGS` の exact 一致も固定。
- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_ccbench_spawn_sites.py:1)
  - AST で binary subprocess 候補を列挙。
  - gateway、4 本の定数 flags allowlist、非観測診断 site を閉集合化。
  - allowlist 各項目に根拠コメントを付与。

docs、Unit 2 所有 file、`trial_registry.py` は未編集です。commit もしていません。

## 2. 現行の受理・拒否挙動 → 変更後の受理・拒否挙動

現行は任意の gflags が admission 無しで `run_once` の subprocess へ到達し、親の `FLAGS_*` 環境も継承していました。

変更後は次のとおりです。

- effective rr20 / rr80: issued identity admission 必須。
- rr5 / rr50 / rr95: admission 未指定なら従来の call shape、3-tuple、spawn を維持。
- `--flagfile`、`--fromenv`、`--tryfromenv`: ratio に関係なく tempdir 前に拒否。
- `-ycsb_rratio=` と `--ycsb_rratio=`: 同一扱い、重複時は最終値を採用。
- caller 構築、copy、`dataclasses.replace`、pickle、dict 復元 token: 拒否。
- freeze の追加・欠落・binding drift: neutral 集合との不一致として発行前に拒否。
- admission を指定しない `measure_point` caller: 新 kwarg を `run_once` へ送りません。

## 3. 実走したテスト / 実走できなかったもの

テスト本体まで到達した nodeid は 0 件です。緑は主張しません。

次の 2 範囲を `tools/run_tests.py` で投入しましたが、いずれも collection 前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。

- 新規 2 file。
- 新規 2 file、`test_calibrator.py`、`test_plain_runner_coverage.py`。

静的診断のみ、以下を確認しました。

- 4 file の AST parse 成功。
- `git diff --check` 成功。
- spawn inventory 11 site が期待閉集合と一致。
- copy、replace、pickle、dict 復元がすべて原 token と別 identity。
- 編集 4 file は NFC で、U+0300〜U+036F なし。

## 4. 事前登録変異の前後層確認

変異本走は未実走です。コード上の帰属は次のように固定しました。

- M1: `test_tokenless_rr80_gate_is_only_barrier_before_accepting_subprocess`
  - direct `run_once` 入力で前層なし。導出が空なら classifier は非保護となり、成功する subprocess spy まで到達します。
- M2: 同 node
  - `measure_point` を通さず直接 `run_once`。gate 削除後に拒否する後層はありません。
- M3: `test_flagfile_gate_is_only_barrier_before_accepting_subprocess`
  - flagfile だけを direct `run_once` へ渡します。拒否を外すと ratio 未指定扱いで、成功 spy まで到達します。
- M6: `test_unknown_freeze_holdout_is_rejected_instead_of_classified_unprotected`
  - H3 追加 document を純関数へ直接渡します。前後に別 gate はなく、exact 検査だけが拒否理由です。
- M7: `test_caller_constructed_token_cannot_reach_subprocess`
  - 正規 token と同じ field の caller token を使用。`isinstance` だけなら protected classifier を通過し、成功 spy へ到達します。
- P1: `test_non_holdout_ratios_keep_tokenless_spawn_and_return_shape`
  - rr5 / rr50 / rr95 は token 無しで spy が各 1 回呼ばれ、有効 metrics と既存 3-tuple を受理する設計です。

## 5. 所有外への波及可能性

- `measure_point` caller:
  - `calibrator/sweep.py`
  - `campaign/pipeline.py`
  - `pegasus_floor_scoping.py`
  - `between_run_floor.py`
  - Unit 2 所有の `s8b_floor_campaign.py`
- direct `run_once` caller:
  - `backoff_overthrottle.py`
- 共有 fixture / consumer test:
  - `test_calibrator.py`
  - `test_calibrator_certify.py`
  - `test_campaign.py`
  - `test_between_run_floor.py`
  - `test_s8b_floor_campaign.py`
  - `test_trial_registry.py`
  - `test_plain_runner_coverage.py`
- Unit 2 結線前は、`s8b_floor_campaign` の既定 `measure_point` 経路が rr20 / rr80 admission を渡さないため、該当 consumer test は意図的に赤になりえます。xfail 化や期待値変更はしていません。

## 6. 未完・申し送り

- Pegasus の headroom／queue 状態により pytest は未実走です。
- Unit 2 は、検証済み freeze document を issuer hook に渡し、発行 token を `measure_point` まで転送する必要があります。
- 親 D・worklog は未 land です。D96 記録不足は親段の既知未完ですが、実際の docs checker finding は未観測です。
- 既存テスト期待値は変更していません。
- 最終 `git status` は所有範囲の 4 file のみ変更・新規です。

## 総括

Unit 1 の中立 leaf、identity capability、gflags gateway、構造 meta-test を実装しました。  
非 holdout の既存 call shape と戻り値は維持し、rr20 / rr80 と間接 gflags だけを fail-closed にしました。  
変異の前後層帰属はテスト構造で固定しましたが、変異本走と pytest は未実走です。  
runner は 2 回とも collection 前に Pegasus infrastructure rc=16 で停止しました。  
docs 編集・commit・所有外 file の変更は行っていません。