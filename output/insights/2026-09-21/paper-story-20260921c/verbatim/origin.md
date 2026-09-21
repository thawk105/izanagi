# 依頼の逐語 (2026-09-21、ユーザー直接起動の `/dev-wave` の引数)

dev-wave command の展開に埋め込まれた引数を写した。展開時に入った行の折返しは除いた (文字は不変)。

> 論文ストーリー 2026-09-21c 版 (同日 3 版目) と claim-evidence の次版を正典全体から再導出し、同じ wave で状態図 (Fig 3b の後継) を 21c 版の §0 / §8 から作る。主な差分は B-8 の 3 値判定 pass (entry 1791、D2202、結果稿 docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md、insight output/insights/2026-09-21/t2807-b8-effective/README.md) を §8 B-8 へ反映することと、入口 README の stale 注記の吸収。30 枠の pass を未観測の条件への保証へ広げず、限定は結果稿から逐語で運ぶ。状態図は tools/plotting/plot_arc_status.py を使い (状態は人が 21c 版から JSON に写し、生成器は描くだけ)、21c 版を参照できない場合に限って最小修正する。作図は計測機の外で tools/plotting/FIGURE_CONVENTIONS.md に従う。先例は entry 1793 (21b 版)。起草前に当日の worklog entry の見出しを全部読む。着手直前の local main から fresh worktree。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
