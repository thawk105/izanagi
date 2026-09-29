単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md — 段 2 plan (攻撃対象)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md — 親の段 1 brief (これも攻撃対象。(P1)〜(P7) は親の provisional 裁定)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/ の T-2273-origin.md・D2253.md・D2271.md・D512-D513.md — 依頼と既裁定の逐語。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md、pin-closure.md — 親の実測と pin 閉包。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/output/insights/2026-09-27/t2273-shard0-precopy-impl/README.md — 前 wave ((a)) の実装・計測・事前登録の形。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py (417〜700 行)、orchestrator/tests/test_s8b_holdout_freeze.py (380〜1200 行)、orchestrator/tests/test_s8b_oracle_driver.py (921〜1076 `_T080SharedBases` と `_t080_stub_free_e2e_repo`、1546〜1830 builder と発行 child)。必要な範囲だけ引く。

書込可能な tmp は無い。静的検査だけでよい (test の実走は親が行う)。予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。

## レンズ B — 過剰・削除・効果・計測設計

plan を守らず検査せよ。親 brief 自身も検査対象である。特に:
1. 過剰: plan の追加物 (test・helper・fallback・定数) のうち、依頼 (本題の実装だけ、仮想リスク向けの gate・検査・台帳・一般化は scope 外) を超えるもの、削れるもの。より小さい差分で同じ効果が出る形 (例: 局所化をやめて共通 literal の hoist だけにした場合の効果、逆に局所化だけの場合)。
2. 効果の見込み: profile (1 回の単独走、fixture は計算ノード /tmp) から shard-0 の W_0 短縮をどこまで言えるか。発行 child は共有発行 key の builder ごとに走り、key は複数ある (`_t080_stub_free_e2e_repo` の key 5 要素)。どの builder が shard-0 の L node の待ちに乗るか、builder 同士が並列に走るかを読み、W_0 に効く上限を見積もれ。走査の短縮が受入の他の test (実 repo を走査する test、shard-1 / 2) にも効くかどうか。
3. 計測設計: land 条件を前 wave (a) と同じ隣接 3 対 (A = 測定準備時の local main、B = A + 実装、順序 A,B / B,A / A,B、shard-0 W_0 の対差 3 対すべて正 ∧ 対率中央値 ≥ 10 %) で事前登録することの妥当性。10 % 閾値は (b) の見込み効果に対して適切か (前 wave B の W_0 296〜337 秒)。W_1・pre を補助量としてどう報告するか。計算量の見積り (前 wave 実績: 受入 1 走 ≈ 879 node 秒、焦点走 ≈ 347、変異 ≈ 668、温め 111) の妥当性。
4. 事前登録の前に安く確かめるべきこと (例: 実装後に同じ単独走 profile を 1 回取り直して child の短縮を確かめてから系列を投げる) と、その費用。

## 出力形式

見出し「## 過剰と削れるもの」「## 効果の見込み」「## 計測設計」「## 先に確かめること」「## 判定」(GO / 修正後 GO / NO-GO と理由)「## 総括」。各所見は file:line と「放置すると成果物 (land 判定・記録・受入時間) がどう変わるか」を 1 行で付けよ。「## 総括」は 5 行以内。
