単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md (親の段 1 brief v2。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md (段 2 plan v2。攻撃対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/F1022.md (失敗の型 F1022 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md (由来の裁定 FA-4 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py (対象 test。2579〜2593 行と `_job_script` を呼ぶ他 test。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py (production。828〜916 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/docs/dev-wave/mutation.md (変異契約 DW-M01〜M08。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/mutation_harness.py (変異 harness。`_runner_identity` 775〜850 行と spec の schema。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2761] の段 3 敵対相談役 (レンズ B、read-only)。plan を守る側に立たず、**親 brief v2 と plan v2 の両方**を
攻撃せよ。レンズ B = **整合・実効性・再発面・変異 matrix の実行可能性と帰属**。

ユーザー依頼 (逐語): 「`"release" not in script.lower()` を、repo path を除いた本文に対する handshake 構文 (marker を操作する
release 行) の不在検査へ変える。変異事前登録 = (a) repo path に release を含む fixture で緑、(b) handshake 行を注入した
script で赤。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。」

## 攻撃点 (少なくとも次を検査し、各所見に real / refuted と根拠 file:line を付ける)

1. **runner 経路の自壊 (DW-M07):** 変異 harness は container tree の `tools/run_tests.py --force-dispatch` → 同 tree の
   `tools/pegasus/dispatch_compute.py` で計算ノードへ投入する。B/B2/B3/M0 は `_job_script` (dispatch の job script 生成) を変異するので、
   投入される job script 自体が変異後の形になる。(i) `_runner_identity` (mutation_harness.py:775〜850) の dispatch 入口 blob 検査は
   起動時 1 回か、変異ごとか。変異ごとなら production 変異は全部 rc 非 0 で走れない。(ii) 変異後の job script が bash 構文として
   正しく、実行時に即抜けるか (`set -u`、変数定義順、`printf … >"$marker_tmp"` の直後性)。(iii) 変異が dispatch の marker 収集・
   会計照合 (`compute-visible.json` の実在、job name、`.o` 収集) を壊さないか。壊す経路があれば must-fix。
2. **A の期待 node 完全集合:** container path `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2761-handshake-check/mutation-tree` と
   計算ノードの basetemp (`run_tests.py` が `--basetemp` を渡すか、pytest 既定 `/tmp/pytest-of-tanab/` か) に `release` が無いことの
   確認方法。C が緑のまま R だけ赤になる条件が成り立つか。
3. **新旧両走 (DW-M08 末尾):** 「テスト強化だけの wave は新テストと変更前 HEAD 版の双方へ変異を走らせ、新テストだけが検出する差分を示す」
   を、A (旧検査復元) / AB (旧検査 + handshake) で代替する親の案の妥当性。旧 HEAD の検査 2 行と A の復元 bytes が同一か
   (`git show 38353207f:orchestrator/tests/test_pegasus_dispatch_compute.py` の 2592〜2593 行を確認)。代替が不十分なら、
   旧 HEAD の container で B を走らせる追加走 (spec 別) を裁定候補として書け。
4. **spec の schema 適合:** plan v2 の anchor (`old`) が `izanagi-dev-wave-mutation-spec/v1` の `replacements` に必要な形
   (file 相対 path、`old` 逐語、出現数 1) を満たすか。f-string 内の `{{`/`}}` escape が `old`/`new` に正しく入っているか。
   test 側 anchor (A) は実装前なので実装後に一意性を確認する旨が書かれているか。`expected_nodes` の書式 (完全 nodeid、parametrize id 込み)。
5. **B4 login probe の実行可能性:** `DC._COMPUTE_MARKER_NAME` を process 内で差し替えて対象 test 関数を直接呼ぶ probe が、
   `_job_script` の marker 名参照経路 (module global の読み方) で本当に効くか。effective でなければ別の形を示せ。
6. **plan v2 の file:line の正確さ:** plan が引く行番号・関数名・定数名が現物と一致するか全部確認せよ。
7. **暫定防壁の撤去条件:** 着地後に「wave 名に release を含めない」防壁が不要になるか。他 test に `release` の語不在を script / path に
   掛ける検査が無いか grep で確認 (`not in script` / `not in .*lower()`)。`while` の同型偽赤が残る事実は scope 外の裁定候補。

## 制約

- pytest は走らせられない。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。
- 所見は real / refuted、must-fix / nit、scope 内 / 外を各 1 語で明示。scope 外の real 所見は「裁定パッケージ候補」として
  書き、実装したふりをしない。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)
## 変異 matrix の実行可能性表 (変異 × runner 経路への影響 × 期待 node)
## 変異登録への修正案
## 裁定パッケージ候補
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
