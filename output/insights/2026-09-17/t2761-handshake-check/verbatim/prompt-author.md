単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s4-adjudication.md (親の段 4 裁定 = 実装の正本。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md (段 2 plan v2。検索/置換表と parametrize の形はここ。裁定と食い違う箇所は裁定が優先。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (編集対象。2579〜2593 行の対象 test だけを変える。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜920 行の `_job_name` / `_job_script`。読むだけ、変更禁止。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 5 実装子 (Codex `role=author`、D95)。裁定 (s4-adjudication.md) の「プラン v2 の修正 (= プラン v2.1)」を
そのまま実装せよ (plan v2 の検索/置換表 + 裁定の P5 二段検査 + parametrize)。編集対象は `orchestrator/tests/test_pegasus_dispatch_compute.py` の
`test_compute_marker_is_cross_namespace_evidence_without_release_handshake` (とその parametrize decorator) だけ。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

## 現行の受理・拒否挙動 (scope 前)

- 受理: `_job_script` の出力に `release` (大小無視) が全く含まれず、`while` が含まれず、marker 名があり、`mv "$marker_tmp" "$MARKER"` が
  `selected=""` より前にある script。
- 拒否: 上のどれかが破れた script。**repo_root / submission_dir の path に `release` を含むだけでも拒否する (F1022 の偽赤)。**

## 実装後の受理・拒否挙動 (裁定どおり)

- 受理: 6 つの埋込み値 (plan v2 の表) を placeholder へ置換した本文に `release` 行が無く、既存 3 assert が成立する script。
  path に `release` を含んでも受理する (parametrize `[repo-release-path]` が緑)。
- 拒否: (1) 置換後の本文に `release` (大小無視) を含む行が 1 行でもある script (assert のメッセージに該当行の一覧を出す)。
  (2) 正規化の前提が崩れた script: needle の出現数が 1 でない、または needle の直後が word 終端 (`\n`、空白、tab、`;`、`&`、`|`、末尾) でない
  (裁定 P5 の二段検査。メッセージに needle を含める)。(3) 既存 3 assert (`DC._COMPUTE_MARKER_NAME in script`、`mv` の順序、`"while" not in script`) の破れ。

## 禁止事項 (各 1 項目ずつ守れ)

- `tools/pegasus/dispatch_compute.py` を含む production を編集しない。
- 対象 test 以外の test・共有 helper・`_REPO` の定義・conftest を編集しない。
- docs (`docs/` 配下すべて、`docs/handoff/` への file 作成を含む)・`output/`・memory・handoff を編集・作成しない。
- 絶対に `git add` / `git commit` / `git stash` / `git checkout` / `git reset` を実行しない。commit は親が行う。
- 既存 test の期待値を変えない (反転・緩和・skip・xfail・削除を禁ずる)。既存 3 assert は文言も含めそのまま残す。
- 検査を甘くしない: placeholder 置換は plan v2 の表の 6 値だけを、その埋込み位置 (改行 + `RESULT=` 等の直後、`shlex.quote(str(path))` の完全表現) で
  各 1 回だけ置換し、置換文字列には固定部分 (basename、`tools/pegasus/dispatch_compute.py`、`DC._COMPUTE_MARKER_NAME`) を残す。
  `str(path)` の無限定な全域置換や、行ごと削除はしない。job name (`#PBS -N`) は置換しない。
- 追加 gate・helper の一般化・他 test への共通化をしない。
- 計算ノードへの dispatch (`tools/run_tests.py` の自動 dispatch を含む) をしない。pytest は login node で対象 file を直接
  `python3 -m pytest orchestrator/tests/test_pegasus_dispatch_compute.py -k compute_marker_is_cross_namespace -p no:cacheprovider -q`
  の形で走らせてよい (file 全体は走らせなくてよい。親が焦点走と受入を行う)。

## 完了報告に必ず含めること

- 差分の要約 (変更行の file:line)。
- 実走した pytest の nodeid・結果 (実走できなければ「実装済み・未実走」と書く。緑を主張しない)。
- 実装後の anchor 逐語 (裁定の変異 a-old-check の old = 新検査ブロック全体 (normalizations の定義から release_lines の assert まで、`while` assert を含む)。file 内で出現数 1 であることの確認)。
- 所有外 caller・共有 fixture・consumer test への波及可能性の静的列挙 (`_job_script` を呼ぶ他 test は production を変えないので不変のはず)。
- 甘くしていないことの自己申告: 現行が拒否する template 由来の `release` 行を新検査も拒否する根拠。

## 出力形式 (見出しは全部 `##`)

## 差分要約
## 実走結果
## anchor 逐語
## 波及
## 総括

出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
