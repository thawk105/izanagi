単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief.md (親の段 1 brief。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan.md (段 2 の plan。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (対象 test。2579〜2593 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜920 行の `_job_name` / `_job_script`。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 3 敵対相談役 (レンズ A、read-only)。plan を守る側に立たず、**親 brief と plan の両方**を
攻撃せよ。レンズ A = **正しさ境界 (規律 2: 検査を甘くしない) と検出力**。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。変異事前登録 = (a) repo path に release を含む fixture で緑、(b) handshake 行を注入した
script で赤。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

## 攻撃点 (少なくとも次を検査し、各所見に real / refuted と根拠 file:line を付ける)

1. **検出力の後退:** 現行 `"release" not in script.lower()` が赤にする入力集合 (template 由来の行) のうち、plan の新検査が
   緑にしてしまう入力を具体的に構成せよ (例: `RELEASE=1` 単独行、`# release` comment、`trap ... release`、`until` 待ち)。
   その入力が FA-4 の言う「親→job の release handshake」に該当するか、該当しないなら検出力後退は実害か nit かを判定せよ。
2. **除去の過剰:** path 文字列の除去が template 本文の行を誤って消す・壊す可能性。`str(path)` の部分一致で `REPO=` の変数名や
   `$REPO` の展開行、`DISPATCHER` 行の `tools/pegasus/dispatch_compute.py` の部分が消えるか。除去後の本文に handshake 行が
   残ることを保証する除去の形 (置換 token を残す、行単位で除く等) を評価せよ。
3. **除去の不足:** `_job_script` が埋め込む環境依存文字列を全部列挙し (repo_root、result/probe/request/marker の 4 path、
   dispatcher、job_name = `izdw-` + submission_dir.name[:10])、plan の除去対象から漏れるものがあれば示せ。pytest の
   `tmp_path` の名前は test 関数名から作られる (`test_compute_marker_is_cross_n0` のように 30 字で切られる) — この名前が
   `release` を含む条件があるか実測 (pytest の basetemp 命名規則を code で確認) せよ。
4. **親 brief の実測値の一般化:** brief が「template 由来の残りは定数 (SFC / gen_S / candidates / env 名 / INFRA_RC) と shell 本文」と
   書くのは正しいか。`_INTERPRETER_CANDIDATES` (dispatch_compute.py:408 付近) の中身に `release` や path を含む要素が無いか確認せよ。
5. **狭い定義の是非:** 「release と marker 参照の同一行共起」を採ると、複数行に分かれた handshake (`RELEASE_FILE="$MARKER.release"` +
   `until [[ -f "$RELEASE_FILE" ]]`) をどう扱うか。広い定義 (release 行の全件) と狭い定義の、規律 2 の観点からの優劣を判定せよ。
6. **変異の帰属:** plan の負例 (b) が「handshake 行を注入」で赤になる理由が単一か (他の assert — `while` 不在や `mv` の順序 —
   が先に赤にしないか)。`until` を使う注入なら `while` 不在 assert は反応しないことを確認せよ。
7. **規律 2 の射程:** この test は CC 変異の正しさ gate ではないが、dispatcher の設計不変条件 (FA-4) を守る防壁である。
   置換が「検査を甘くして通す」に該当する経路 (例: 除去対象を広げすぎて handshake 行自体が消える) が無いか。

## 制約

- pytest は走らせられない。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。
- 所見は real / refuted、must-fix / nit、scope 内 / 外を各 1 語で明示。scope 外の real 所見は「裁定パッケージ候補」として
  書き、実装したふりをしない。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)
## 検出力の比較表 (入力 × 現行 / 広い定義 / 狭い定義)
## 推奨する検査の形 (1 つ、通る正例 1 つと落ちる負例 1 つ)
## 変異登録への修正案
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
