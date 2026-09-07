## 実装結果

静的 backoff 上限拡張を実装しました。

- 物理値 `0..9999` と raw 値を相互変換する単一 codec を追加しました。[backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/orchestrator/campaign/backoff_extended_sweep.py:60)
- C++ hole の最終 fallback だけを `BACKOFF_FIXED - 2000ULL` に変更しました。[silo-backoff-fixed.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/patches/silo-backoff-fixed.patch:70)
- `exact_model` を raw `11999` 上限と `encoded - 2000` 復号へ更新しました。[b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/orchestrator/campaign/b10_backoff_shape_sweep.py:722)
- hole の逐語 pin、B-10 schema v5、space/trial 次版を反映しました。
- extended/T-2266 genome は raw 3000、label/report は物理 1000 になりました。T-2266 realized tail は 1000、unrealized は空です。
- extended と T-2266 の campaign identity、T-2266 report schema、overthrottle rep/manifest schema を次版へ分離しました。
- overthrottle の label、row、resume 検証、manifest summary を物理値へ統一しました。
- `backoff_requested_us` は現行 `genomes()` 依存を外し、D1106 の旧 raw 格子・base flags・seed を局所固定しました。
- condition meaning gate の既存 fixture を更新し、raw 3000 → 実測 1000.0 の正例を追加しました。raw 1000 → 0 の F718 負例は維持しています。

新しいハッシュは次のとおりです。

- patch SHA-256: `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a`
- formula SHA-256: `1205b1ffb4fa6740873f1aa1ecf50bfc484239fb74aa28464dcb2e3a19fbe8df`

## 受理・拒否範囲

| 面 | 変更前 | 変更後 |
|---|---|---|
| 静的物理値 | 意味上 `0..999` | exact integer `0..9999` |
| 静的 encode | 物理値を raw として直接使用 | `0..999 → 同値`、`1000..9999 → µ+2000` |
| 静的 decode | 集中 API なし | raw `0..999` と `3000..11999` を受理。`1000..2999`、負値、`12000+`、非整数を拒否 |
| `exact_model` | 非負整数を上限なしで受理 | raw `0..11999` を受理、負値と `12000+` を拒否 |
| raw `0..999` | 定数として恒等 | 数値不変 |
| raw `1000..1999` | symmetric-modulo | 旧閉形式のまま |
| raw `2000..2999` | binary | 旧閉形式のまま |
| raw `3000..11999` | `% 1000` | `raw - 2000` |
| `BACKOFF_FIXED=-1` | stock 枝 | 不変 |

静的値の入力言語は `0..999` から `0..9999` へ拡張しています。正しさゲートや B-10 shape の閉集合、R1〜R5は変更していません。

## 検査状況

成功した検査:

- 変更対象11 Pythonファイルの `py_compile`
- `git diff --check`
- codec 全 `0..9999` 往復、11999/12000境界、raw3000→1000、T-2266 raw集合、旧D1106固定を確認する静的 smoke
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- test file列挙・test名重複・self-runner/allowlist・既存duration-ledger node名の静的監査

pytest は実装済み・未実走です。対象6ファイルと `test_plain_runner_coverage.py` を `tools/run_tests.py` 経由で起動しましたが、いずれもテスト子を起動する前に rc=16 で停止しました。

- login側: 予約台帳を安全に更新できず dispatch 判定
- queue側: `qstat -Q` が `EACCTAUTH Unknown user-id` で失敗
- 実走 nodeid: なし

親 docs 未着地による想定赤は次の1 nodeだけです。

- `orchestrator/tests/test_b10_backoff_shape_sweep.py::test_p06_canonical_v4_machine_spec_and_runtime_residual_are_accepted`

現行 Markdown が v4・旧patch/formula hashのためで、それ以外の赤は回帰扱いです。

## 所有外への波及

- 親担当の B-10事前登録 Markdown は schema v5、新patch/formula hashへの更新が必要です。
- `patches/README.md`、`src/coder-spec.md`、worklog、decisionsも親担当のまま未編集です。
- `tools/t2216_backoff_walk_model.py` とそのconsumer testは旧v1・999 tailの歴史系列なので変更していません。
- 旧 plotting、figure provenance、campaign digest、F718、旧成果物は変更していません。
- stock の preprocess digest、`src_token`、`variant_id` は不変ですが、admission receipt経由のcache keyは安全側にmissします。
- 非負 variantはhole bytes変更により新しいsource identityになります。
- 投入scriptは8点を透過するため変更不要です。

## 総括

裁定どおりの実装と静的検査は完了し、Markdown/RST・既存成果物・旧digestには触れていません。commit・pushも行っていません。ただしpytest本体はPegasus実行基盤の認証失敗で未実走のため、状態は「実装済み・未実走」です。