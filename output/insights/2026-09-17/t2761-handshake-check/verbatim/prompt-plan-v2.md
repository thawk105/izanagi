単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md (親の段 1 brief v2。DW-O13 の分析と親の provisional 裁定 P1〜P5、変異案を含む。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (対象 test。2579〜2593 行と 24 行の `_REPO`。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜916 行。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/docs/dev-wave/mutation.md (変異契約 DW-M01〜M08。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 2 プラン起草役 (read-only)。brief v2 の scope と provisional 裁定 P1〜P5 に沿って、
file:line 粒度の実装プランを書け。コードは書かず、変更する行・test の形・正規化の検索/置換表・変異 matrix の anchor を
特定せよ。pytest は走らせられない (書込可能 tmp が無い)。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。

ユーザー依頼 (逐語): 「`orchestrator/tests/test_pegasus_dispatch_compute.py:2592` の
`test_compute_marker_is_cross_namespace_evidence_without_release_handshake` が script 本文へ掛ける `"release" not in script.lower()` を、
repo path を除いた本文に対する handshake 構文 (marker を操作する release 行) の不在検査へ変える。Codex author (D95)。
変異事前登録 = (a) repo path に release を含む fixture で緑、(b) handshake 行を注入した script で赤。規律 2 を緩めない。
本題の検査置換だけ。追加 gate は scope 外。」

## 答えるべきこと

1. **正規化の検索/置換表 (P2):** 6 値それぞれについて、検索文字列の組み立て式 (Python 式で、`shlex.quote(str(...))` を含む) と
   置換文字列を書け。`MARKER` の置換は `"<SUBMISSION>/" + DC._COMPUTE_MARKER_NAME` のように production 定数を残すこと。
   `DISPATCHER` の置換は固定 suffix `tools/pegasus/dispatch_compute.py` を残すこと。検索が改行 + 代入名から始まる形
   (例: `"\nREPO=" + shlex.quote(str(repo_root))`) にして誤爆を避けるか判断せよ。
2. **P5 (出現数 1 の assert):** 置換前に `script.count(needle) == 1` を assert する形の是非。assert 文言に needle を含める。
   これが「追加 gate」に当たらない理由 (正規化の前提検査で production の受理集合に触れない) を書け。
3. **検査本体 (P1):** `release_lines = [line for line in normalized.splitlines() if "release" in line.lower()]` /
   `assert not release_lines, release_lines` の形。docstring / comment に「環境値を除いた本文の release 候補行を保守的に拒否する
   (FA-4 の release handshake 不在の代理検査)」と書く案。既存 3 assert は文言も位置も変えず、`"while" not in script` は元の
   `script` に掛けたまま。
4. **P3 parametrize:** `@pytest.mark.parametrize("repo_root", [_REPO, Path("/__t2761__/repo release's checkout")], ids=[...])` の
   形と、test 関数 signature (`tmp_path, repo_root`)。合成 path の `'` が `shlex.quote` で `'"'"'` になることを検索式が扱えるか確認。
5. **変異 matrix (brief v2 の表) の anchor を実装後の形で書け:** 各変異の `old` (複数行 anchor、出現数 1) と `new` を逐語で。
   production 側 (M0 / B / B2 / B3) は `_job_script` の f-string 内なので `{{`/`}}` の escape に注意 (`${{MARKER}}` 形)。
   test 側 (A) は実装後の新検査ブロックを anchor にし、旧 2 行へ戻す `new` を書け。AB は A と B の replacements を 1 変異に並べる。
   期待 node (C / R) と、B/B2/B3 の注入行が実行時に即抜ける根拠 (`$marker_tmp` は `printf … >"$marker_tmp"` 直後で実在、
   `$MARKER` は `set -u` 下でも代入済み) を示せ。
6. **B4 (marker 定数改名) の login probe 手順:** `DC._COMPUTE_MARKER_NAME` を process 内で `compute-visible.release` へ差し替えて
   対象 test 関数を直接呼ぶ (dispatch しない) probe の形を 10 行程度の Python で示せ (親が job dir で実行する。repo へは入れない)。
7. **波及と変更しない一覧:** `_job_script` を呼ぶ他 test (1054〜1130、2290〜2312、4080、4142、5055、5340、5937 付近、6119、6616) は
   production を変えないので不変。production・他 test・docs・`_REPO`・duration ledger は変更しない。

## 制約

- brief v2 の不変条件 (i)〜(iv) を守る。特に (ii) 検出力は現行以上。
- 追加 gate・helper の一般化 (他 test への共通化)・docs 編集はプランに入れるな。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 変更面 (file:line 表)
## 正規化の検索/置換表
## 検査本体と parametrize の形
## 変異 matrix 事前登録 (anchor 逐語・期待 node・即抜けの根拠)
## B4 login probe
## 波及と変更しない一覧
## 未確定事項
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
