単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md (親の段 1 brief v2。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md (段 2 plan v2。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (対象 test。2579〜2593 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜916 行。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 3 敵対相談役 (レンズ A、read-only)。plan を守る側に立たず、**親 brief v2 と plan v2 の両方**を
攻撃せよ。レンズ A = **正しさ境界 (規律 2: 検査を甘くしない) と検出力、正規化境界**。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。変異事前登録 = (a) repo path に release を含む fixture で緑、(b) handshake 行を注入した
script で赤。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

## 攻撃点 (少なくとも次を検査し、各所見に real / refuted と根拠 file:line を付ける)

1. **検出力の後退の構成:** 現行 `"release" not in script.lower()` が赤にする template 由来の入力のうち、plan v2 の正規化 + 広い検査が
   緑にする入力を具体的に構成せよ。特に (i) 6 つの置換文字列に production 定数を残す設計で、production のどの変更が隠れうるか
   (`result.json` の basename、`tools/pegasus/dispatch_compute.py` の suffix、`DC._COMPUTE_MARKER_NAME`)、(ii) 検索が「改行 + 代入名=」で
   始まる形なら、代入名の改名で検索が外れたとき何が起きるか (P5 の出現数 assert が赤にするか)。
2. **除去の過剰:** 検索の完全表現置換が、値の直後に足された構文 (`; until …`) や別行の handshake を消す経路が無いか。
   合成 path `/__t2761__/repo release's checkout` の `'` が `shlex.quote` で `'"'"'` になるとき、検索式と script 内表現が
   byte 一致するか (Python 式で確認せよ)。
3. **P5 の性格:** 出現数 1 の assert が「追加 gate」に当たるか。当たるなら理由を、当たらないなら理由を書け。当たらない場合でも、
   これが赤になる production の変更 (変数名改名など) を列挙し、それが「検査を甘くしない」方向に働くことを確認せよ。
4. **狭い定義との比較:** brief v2 の alias 3 行の例が、狭い同一行共起検査を本当に通す (緑になる) か、`RELEASE_FILE` を
   「marker 参照」と数える解釈で赤になるか。広い定義の採用理由として十分か。
5. **変異 B/B2/B3 の即抜け設計:** 注入行が実行時に即抜ける根拠 (`$marker_tmp` の実在、`set -u` 下の変数定義順) を
   `_job_script` の行番号で検証せよ。即抜けが失敗する経路 (printf 失敗、`-f` の判定、`||` の評価順) があれば示せ。
   また即抜け条件を足すことが「handshake 行の注入」の実証として弱いか (test は静的検査なので実行時挙動は無関係、という
   親の主張を攻撃せよ)。
6. **変異の帰属:** B/B2/B3 が赤になる理由が単一か (`while` 不在 assert、`mv` 順序 assert、marker 名 assert のいずれかが先に赤にしないか)。
   A の期待 `{R}` が完全集合である環境条件 (container path・basetemp に `release` 無し) の妥当性。
7. **規律 2 の射程:** 置換が「検査を甘くして通す」に該当する経路が残るか。残るなら must-fix、無いなら refuted と書け。

## 制約

- pytest は走らせられない。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。
- 所見は real / refuted、must-fix / nit、scope 内 / 外を各 1 語で明示。scope 外の real 所見は「裁定パッケージ候補」として
  書き、実装したふりをしない。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)
## 検出力の比較表 (入力 × 現行 / plan v2)
## 推奨する修正 (あれば。通る正例 1 つと落ちる負例 1 つ)
## 変異登録への修正案
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
