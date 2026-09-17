単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief.md (親の段 1 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (対象 test。2579〜2593 行の `test_compute_marker_is_cross_namespace_evidence_without_release_handshake` と、24 行の `_REPO`、1054〜1130 行・2290〜2312 行の `_job_script` を使う既存 test。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜920 行の `_job_name` / `_job_script`。変更禁止、読むだけ。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 2 プラン起草役 (read-only)。brief の scope 内で、file:line 粒度の実装プランを書け。
コードは書かず、変更する行・追加する helper・test の形・変異 matrix の anchor を特定せよ。pytest は走らせられない
(書込可能 tmp が無い)。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。

**ユーザー依頼 (逐語):** 「`orchestrator/tests/test_pegasus_dispatch_compute.py:2592` の
`test_compute_marker_is_cross_namespace_evidence_without_release_handshake` が script 本文へ掛ける
`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する release 行) の
不在検査へ変える。Codex author (D95)。変異事前登録 = (a) repo path に release を含む fixture で緑、(b) handshake 行を
注入した script で赤。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

## 答えるべきこと

1. **検査の形 (brief の P1):** 「path を除いた本文の行で `release` (大小無視) を含む行の全件列挙が空」(広い定義) と
   「`release` と marker 参照 (`MARKER` / `marker_tmp` / marker file 名) の同一行共起」(狭い定義) のどちらを採るか。
   現行 `"release" not in script.lower()` が赤にする template 由来の行を、各定義がどこまで赤にするかを表で示せ。
   検出力が現行より落ちる定義は規律 2 (検査を甘くしない) に抵触するので理由なしに採るな。
2. **除く文字列 (P2):** `_job_script` が埋め込む環境依存文字列を全部列挙し (repo_root、submission_dir 配下 4 path、
   dispatcher、job_name)、どれを除去対象にするか、`str(path)` と `shlex.quote(str(path))` のどちらの形で除くか、
   除去の実装 (置換か行除外か) を file:line で書け。除去が template 本文の行を誤って消す可能性 (例: `REPO=` 行の
   変数名まで消えるか) を検討せよ。
3. **正例対照を test 自身に持たせるか (P3):** `repo_root` を `[_REPO, release を含む合成 path]` で parametrize する案の
   是非。parametrize id、合成 path の形 (実在不要か — `_job_script` は path を埋めるだけで存在を検査しない)、
   既存の他 test への影響 (node id の変化で pin されている test が無いか grep で確認せよ)。
4. **`"while" not in script` (P4):** 触らない (scope 外) で正しいか。path 除去後の本文に掛け直すべき理由が
   scope 内にあるなら示せ。無ければ「触らない」と書け。
5. **変異 matrix の anchor (file:line):** (a) 正例: parametrize の release-path node が baseline で緑、かつ
   「path 除去を外す = 旧検査へ戻す」変異で同 node が赤。(b) 負例: `_job_script` の template へ handshake 行
   (例: `until [[ -f "${MARKER}.release" ]]; do sleep 1; done` を `mv "$marker_tmp" "$MARKER"` の直前) を注入して赤。
   等価 M0: comment 行だけ追加で SURVIVED。各変異の anchor 行を 1 箇所に定まる複数行 anchor で書け。
   期待赤 node は既存 node 名 (parametrize 後の id を含む) で書け。
6. **既存 test への波及:** `_job_script` を呼ぶ他 test (1054〜1130、2290〜2312、5937 付近) は production を変えないので不変のはず。
   確認せよ。
7. **変更しない一覧:** production (`tools/pegasus/dispatch_compute.py`)、他 test、docs。

## 制約

- brief の不変条件 (i)〜(iv) を守る。特に (ii) 検出力は現行以上。
- 追加 gate・helper の一般化 (他 test への共通化)・docs 編集はプランに入れるな。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 変更面 (file:line 表)
## P1〜P4 の判断と根拠
## 変異 matrix 事前登録案 (anchor・期待 node)
## 波及と変更しない一覧
## 未確定事項
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
