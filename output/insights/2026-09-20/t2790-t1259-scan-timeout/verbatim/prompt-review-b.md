単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/adjudication.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/brief.md (段 1 brief と親の前提実測。**親自身の実測値とその一般化が本レンズの主対象**。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/adjudication.md (段 4 裁定と plan v2、§1 の P1〜P3、§3 変異事前登録。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/rulings-verbatim.md (D2148 項 12・D1877・D1936 項 43・F945 冒頭と末尾の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/survey-1.md (Codex 作の集計器 `junit_scan_survey.py` が受入 shard junit 33+ 走から作った層別分布表。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/junit_scan_survey.py (集計器の実装。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/scan_sampler.py (login 側 sampler の実装。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/sampler-smoke.jsonl (sampler の試走 2 sample。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/f945-supersede-draft.md (F945 追補 1 行の草案。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/author-u1.patch (実装差分 = commit 4208bf332、base 8fd1eecf9。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/author-u1-out.md (実装子の最終報告。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout/orchestrator/tests/conftest.py の 660〜710 行と 2161〜2177 行 (real-repo memo work unit と接尾除去 = P1 の機序の根拠。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py の 73〜97 行 (module fixture が走査結果の一部を上書きして捨てる箇所。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2790-t1259-scan-timeout (HEAD 4208bf332)。read-only。
受入 shard の原本は /work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/shard-*/junit.xml (読取り可。任意の session を開いて集計器の主張を検算してよい)。
git の履歴も読める: `git log -1 252e24b4f`、`git show 252e24b4f --first-parent -- orchestrator/tests/conftest.py`。

# 依頼 — 段 6 敵対レビュー B: 過剰・削除 + 親の実測値とその一般化

親が実行済み: 焦点走 54 passed (計算ノード)、全史 provenance 緑、consumer 焦点走 223 passed / 1 failed (差分到達不能の p3_s4_loop identity 赤、単独再走中)。
受入全走・変異・sampler 本走 (受入と並走) は未実施。sandbox は read-only で pytest を走らせられない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## 攻撃してほしいこと (プランを守らず検査する。親の brief・裁定・実測が主対象)
1. **P1 (機序) の一般化**: 「非 group 化 → worker ごとの module fixture 再実行 → 同一 worktree を 42〜46 本同時走査 → F945」は、
   junit の前後比較 (接尾の有無 ↔ 2 秒超 test 数 43〜46 ↔ 1) から言えるか。反証候補を探せ: (a) pytest の module fixture の例外 cache と
   「1 shard で error 1 件」の整合、(b) 前 regime の高い所要が「同時走査」でなく時刻帯の負荷で説明できる可能性 (survey の重なり数別の表と
   前 regime 内のばらつきを使う)、(c) 252e24b4f の差分が本当に t1259 の grouping を変えたか (conftest 2161〜2177 の接尾除去と
   `REAL_REPO_PROCESS_MEMO_NODES` の関係を読んで確認)、(d) 「2 秒超 test 数 = fixture 実行回数」という代理の妥当性 (test 本体が
   2 秒以上かかる test が t1259 にあるか)。
2. **分布の読み方**: junit time は 4 git 呼び出し + sha256 の合計で、timeout は呼び出しごと。前 regime で 30 秒超でも error でない sample が
   102 件ある事実と「30 秒 timeout」の関係を整理し、brief / 草案の表現に誤りがないか。右打ち切り 59 件を除いた p99 の意味。
   後 regime n=23 で p99 を語る限界。集計器の overlap 定義 (窓の和集合の交差、ピーク同時数でない) が結論に与える影響。
3. **P3 (採用値の決め方)**: 「max ≤ 60 秒なら 120 秒を採用」は根拠があるか。候補 120 に対し 60 / 90 / 180 などの代替と、
   その費用 (真の hang の検出遅延、real-repo lock deadline 245 秒との関係、受入 5 分上限) を比較して、親の規則が恣意的なら指摘せよ。
   D2148 項 12 の「実測で確かめるまで確定値にしない」を満たす最小の記録は何か。
4. **過剰・削除**: helper module + 新 test file + 計測 script 2 本は D2148 項 12 の「局所的に見直す設計」に対して過剰か。削れる物・
   統合すべき物・逆に足りない物 (例: 採用値を将来変えるときの手順が無い、fixture の走査時間を junit に残す記録が無い) を挙げよ。
   ただし新 gate・自動再投入・production 変更・untracked 走査削減は scope 外 (裁定) なので提案しない。
5. **F945 追補草案**: 事実と一致しない表現、断定しすぎ (「主因を分離した」「構造的に無い」)、欠けている限界 (時刻・負荷との交絡、
   計算ノード側の未計測、n の小ささ) を指摘し、書き直し案を 1 行で示せ (1 物理行の制約)。
6. **fixture が走査結果を捨てている事実**: module fixture は `tracked_status` / `untracked_paths` を上書きするので、fixture の実走査で
   検査力を持つのは `head` と `source_sha256` だけ。この事実を wave はどう記録すべきか。「走査対象を維持した」という主張は成立するか。
7. **sampler の妥当性**: login で測る sampler は、計算ノード上の shard から lustre を走査する fixture の代理になるか。何を主張でき、何を
   主張できないか。sampler 自身が測定対象の負荷を変える (自分の走査で共有 FS を叩く) 程度は無視できるか。

## 出力形式 (H2 見出し、最後の `## 総括` は必須)
- `## 所見` — 番号付き。各所見に `real | refuted | 不明`、`must-fix | should | nit`、根拠 (file:line または survey の行)、
  放置時に成果物 (F945 台帳の主張・insight の結論・採用値) がどう変わるかを 1 行 (DW-G05)。
- `## 親の実測値への反証・限界` — P1〜P3 それぞれに対し、支持する証拠・反証する証拠・書くべき限界を分けて。
- `## 削除・縮約の提案` — 削れる物と理由。
- `## F945 追補の書き直し案` — 1 物理行。
- `## 総括` (5 行以内、GO / NO-GO とその条件)
