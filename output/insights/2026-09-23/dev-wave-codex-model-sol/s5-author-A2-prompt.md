単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-model-sol/s4-adjudication.md — **段 4 裁定とプラン v2 (本作業の正本)**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-codex-model-sol/brief.md — 親 brief (scope 表・scope 外・不変条件)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/docs/dev-wave/operations.md — 参照のみ。DW-O01 の `<model>` 行は親が既に `gpt-6-sol` へ改訂済み (base commit e39e43c9c)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/tools/dev_waves/launch_authority.py — 参照のみ (`_MODEL_LINE_V2_RE`、`snapshot_authority`、`derive_launch`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/tools/check_docs.py — 所有 file。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/orchestrator/tests/test_check_docs.py — 所有 file。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/orchestrator/tests/test_dev_wave_launch_authority.py — 所有 file。読めなければ即停止

## 作業 (プラン v2 の実装単位 A)

**編集してよい file は次の 3 つだけ:** `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`、`orchestrator/tests/test_dev_wave_launch_authority.py`。

1. `tools/check_docs.py` の `DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL` の slug `gpt-6-astra` を `gpt-6-sol` へ替える (他の文字は 1 byte も変えない)。
2. `orchestrator/tests/test_check_docs.py`:
   - `test_dev_wave_model_pin_rejects_dw_o01_authority_drift` の `text.replace("gpt-6-astra", "gpt-5.6-terra", 1)` の置換元を `"gpt-6-sol"` へ (置換先 `gpt-5.6-terra` と `assert changed != text` は据え置き)。
   - `test_dev_wave_model_pin_contract_is_time_invariant` の期待 literal の slug を `gpt-6-sol` へ。
3. `orchestrator/tests/test_dev_wave_launch_authority.py` の期待 model 2 か所 (`test_snapshot_and_derive_current_authority_positive` の集合、`test_all_stage_models_match_independent_docs_cross_check` のリスト) を `"gpt-6-sol"` へ。
4. 上記 3 file の中に他の `gpt-6-astra` が残っていないか確かめ、残っていれば報告する (勝手に変えない)。

既存テストの期待値変更は、ユーザー裁定 (model 移行) の直接の帰結として段 4 裁定が許可した上記 4 か所だけ。他の期待値・assert・parametrize は変えない。

**着手前に次の現行挙動を読んで報告に明記する:** (a) check_docs が DW-O01 の model 行を検査する関数と、literal 不一致・権威行外の `gpt-` slug をどう finding にするか。(b) launch_authority が V2 行から model を導出する経路。(c) base commit の docs と現行 literal (astra) の組で、check_docs と上記 test がどの結果になるはずか (期待赤の finding 集合)。

## 制約 (すべて守る)

- **非 NFC 行を表示しない (F223)。** `orchestrator/tests/test_check_docs.py` の 5740〜5800 行には Unicode NFC でない文字が意図的に含まれ、その表示が 1 行でも実行記録に載ると本 job 全体が不受理になる。**このファイルを `cat` 等で全体表示しない。** 読むときは `sed -n '<開始>,<終了>p'` で必要な行範囲だけを表示し、5740〜5800 行を含む範囲は表示しない (編集対象は 9120〜9130 行と 9405〜9415 行付近だけ)。`grep` で検索するときは `grep -n -c` で件数を見るか、表示する語を `gpt-6-` のように ASCII で絞る。
- 前回の attempt (commit 311bbb50c、branch dev-wave-sol-unit-a) は上記の理由で起動器に不受理とされた。その差分は参考にしてよいが、所有 3 file を自分で読み直して同じ変更を作り直すこと。
- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/` 配下、`output/` を含む)。所有 3 file 以外の file を作成・編集しない。`orchestrator/tests/test_s8b_ratified_freeze.py` と `orchestrator/tests/acceptance_duration_ledger.json` は触らない (段 1 で scope 外と判定済み)。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、`pytest.main` の埋め込み、test file の自走 harness のいずれも使わない)。親が計算ノードで焦点走を行う。報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile <file>`) は行ってよい。
- `gpt-` slug を検査する既存の制約 meta-test (例: workers.md / operations.md の DW-O01 外に slug が無いことを見る test、`DEV_WAVE_MODEL_SLUG_RE` の test) に変更が触れないかを**自分で洗い出して静的に確認する** (親の名指しを網羅と見なさない)。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値を焼き込まない。
- 指示外の受理集合を変えない。規律 2 (正しさゲート) に触れない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 着手前の現行挙動 (上記 (a)〜(c))
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と、それぞれが変更で影響を受けるか
5. 段 4 の変異 m0〜m2 と、それぞれを落とすはずの test node 名 (変更箇所を通る根拠)
6. 所有外の caller・共有 fixture・consumer test への波及の静的列挙
7. 未実走であることの明記と、親が走らせるべき nodeid / file の候補
最後に `## 総括` を置く。
