単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief.md (親の段 1 brief。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan.md (段 2 の plan。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (対象 test。2579〜2593 行と、`_job_script` を呼ぶ 1054〜1130・2290〜2312・5937 付近。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜920 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/docs/dev-wave/mutation.md (変異契約 DW-M01〜M08。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 3 敵対相談役 (レンズ B、read-only)。plan を守る側に立たず、**親 brief と plan の両方**を
攻撃せよ。レンズ B = **整合・実効性・再発面・変異の帰属**。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。変異事前登録 = (a) repo path に release を含む fixture で緑、(b) handshake 行を注入した
script で赤。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

## 攻撃点 (少なくとも次を検査し、各所見に real / refuted と根拠 file:line を付ける)

1. **F1022 型の再発面:** path 除去後も残る環境依存文字列は何か。`tmp_path` (pytest basetemp: `/tmp/pytest-of-<user>/pytest-N/<testname[:30]>N`)、
   `job_name`、hostname、環境変数、`shlex.quote` が path に `'` を付ける条件 (空白や特殊文字を含む path で `'...'` になる) —
   quote 形と素の `str(path)` の両方を除かないと何が残るか。ユーザー名や basetemp が `release` を含む場合を含めて判定せよ。
2. **正例対照 (P3) の実装:** `repo_root` の parametrize が「本題の検査置換だけ」の scope 内か。合成 path の形
   (例: `_REPO.parent / "scope-release" / _REPO.name`、実在不要) が `_job_script` で例外なく通るか。parametrize による node id
   変化が、この test の node id を pin する他の test・docs・mutation ledger・allowlist に当たらないか grep で確認せよ
   (`test_compute_marker_is_cross_namespace_evidence_without_release_handshake` を repo 全体で検索)。
3. **変異の帰属 (DW-M01/M03/M04):** plan の各変異について (i) anchor が 1 箇所に定まるか、(ii) 赤理由が単一か (他 assert が
   先に赤にしないか)、(iii) 期待赤 node が parametrize 後の id を含む完全集合になっているか、(iv) 「path 除去を外す」変異は
   test file 側の変異 (テスト強化の wave なので DW-M08 の新旧両走) として登録すべきか。
4. **`"while" not in script` (P4):** scope 外として触らないのは一貫しているか。path に `while` を含む worktree 名で同型の
   偽赤が起きる (F1022 と同じ穴) のに release だけ直すことの是非を、依頼の逐語 (「本題の検査置換だけ」) との整合で判定せよ。
   触るべきと考えるなら「裁定パッケージ候補」として書き、実装に含めろとは書くな。
5. **plan の file:line の正確さ:** plan が引く行番号・関数名・定数名が現物と一致するか全部確認せよ。
6. **親の provisional 裁定 P1/P2 の前提:** brief が言う「狭い定義は `RELEASE=...` 単独行を見逃す」は現行 assert の挙動と
   比べて正しいか。「除く文字列を広げる」が「検査を甘くする」方向に働く経路が無いか (除去が template 行を消す等)。
7. **暫定防壁の撤去条件:** 着地後に memory の「wave 名に release を含めない」防壁が本当に不要になるか。他に `release` 語の
   不在を script や path に掛ける test が repo に残っていないか grep で確認せよ (`not in script` / `not in .*lower()` を全 test で)。
   残るなら着地後も防壁が要る旨を「裁定パッケージ候補」に書け。

## 制約

- pytest は走らせられない。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。
- 所見は real / refuted、must-fix / nit、scope 内 / 外を各 1 語で明示。scope 外の real 所見は「裁定パッケージ候補」として
  書き、実装したふりをしない。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)
## 残る環境依存文字列の表
## 変異登録への修正案 (anchor・期待 node・単一理由性)
## 裁定パッケージ候補
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
