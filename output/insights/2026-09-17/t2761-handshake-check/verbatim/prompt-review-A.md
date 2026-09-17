単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s4-adjudication.md (親の段 4 裁定 = 実装の正本。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md (親の brief v2。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s5-author-snapshot.patch (実装差分の snapshot。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s5-author.md (実装子の最終報告。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/focus-run-1-request4017.o.txt (親の焦点走 log: 計算ノードで対象 2 node が 2 passed。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/login-probe-b4-b5.txt (親の login probe B4/B5 の結果。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (実装後の対象 test。2580〜2637 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜916 行。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 6 敵対レビュー役 (レンズ A、read-only)。実装 (snapshot patch = 作業ツリーの現物) を、
**規律 2 (検査を甘くしない) と検出力、正規化境界、裁定との一致** のレンズで攻撃せよ。実装子の報告を鵜呑みにせず現物で確認する。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

親が実測済み (静的レビューが見られない部分): 焦点走 (計算ノード、request 4017) で C/R 2 node が 2 passed。login probe B4 (marker 定数を
`compute-visible.release` へ差替え) は行リストに `MARKER=<SUBMISSION>/compute-visible.release` を含む赤、B5 (`/__t2761__/rele` +
REPO 値直後に `ase` 連結) は P5 の word 終端で赤。変異 matrix は未走 (レビュー後に probe → 本走)。

## 攻撃点

1. **裁定 (プラン v2.1) との一致:** P1〜P5 の各項目が現物と一致するか。6 値の needle / replacement が裁定の表と byte 一致するか。
   置換文字列に固定部分 (basename、`tools/pegasus/dispatch_compute.py`、`DC._COMPUTE_MARKER_NAME`) が残っているか。
   既存 3 assert が文言・位置とも維持されているか。job name を置換していないか。
2. **検出力の後退の構成 (再挑戦):** 現行 (旧) が拒否する template 由来の入力で、新実装が受理する具体入力を構成せよ。
   word 終端集合 `"\n \t;&|"` の妥当性 (`)`、`` ` ``、`>` などが続く連結を考えよ。終端文字集合の外なら P5 が赤にするので後退ではない —
   その主張を検証せよ)。`script.count(needle) == 1` と `script.index(needle)` の組合せの穴 (needle が別の値の接尾辞として現れる、
   例: `MARKER` needle が `REQUEST` needle の一部になる等) を考えよ。
3. **P5 の副作用:** 正規化の前提検査が赤にする production 変更を列挙し、それらがすべて「厳しくする方向」であることを確認せよ。
   もし「新しい偽赤」(環境依存の入力で P5 が赤になる経路) があれば must-fix。例: tmp_path や repo_root に改行・`;`・`&`・`|` を含む path、
   `shlex.quote` が空文字を `''` にする場合、`Path` の正規化 (末尾 `/` の除去、`..`) で needle と script の表現がずれる場合。
4. **parametrize の合成 path:** `/__t2761__/repo release's checkout` は実在せず `_job_script` は文字列化するだけ — 例外や warning を
   出す経路 (Path.resolve 等) が無いことを確認。node id `[repo-release-path]` が既存の pin・allowlist に当たらないか。
5. **規律 2 の射程:** 「検査を甘くして通す」に該当する経路が残るか。残るなら must-fix、無いなら refuted と書け。
6. **scope:** 差分に本題以外の変更 (`import shlex` 以外の import、他 test への影響、helper 化) が無いか。

## 制約

- pytest は走らせられない。静的検査だけでよく、緑を主張するな。
- 所見は real / refuted、must-fix / nit、scope 内 / 外を各 1 語で明示し、must-fix には放置時の成果物影響 (受理集合・偽赤・偽緑) を 1 行で書く
  (書けないものは nit)。scope 外の real 所見は「裁定パッケージ候補」として書く。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・成果物影響・根拠 file:line)
## 裁定との一致表 (P1〜P5 × 現物)
## 検出力の比較 (旧 / 新、構成した入力)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
