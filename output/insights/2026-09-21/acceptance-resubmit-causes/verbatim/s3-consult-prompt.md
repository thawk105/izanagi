単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes

必読事項の射影 (読めなければ即停止):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/verbatim/origin.md — 依頼の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/s1-brief.md — 親の段 1 brief ((P1)〜(P3) は親の provisional 裁定・攻撃対象)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/s1-prevention-draft.md — 親の草稿「防げた分類ごとの守られなかった既存手順」(攻撃対象)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/verbatim/classification.md — 親が作った投入ごとの分類表・wave ごとの追加 wall・分類ごとの件数。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/verbatim/timelines-all.txt — 20 wave の job dir から機械抽出した時系列 (chain log / attempt log / child log / receipt / land 記録)。分類表の根拠。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/verbatim/extract.py.txt、classify.py.txt — 上を出した抽出・集計 script の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/waves.txt — 対象 20 wave (worklog entry 番号と job dir 名)。
- 一次資料 (job dir、必要な投入だけ直接読んでよい): /work/1/SFC/tanab/dev-wave-jobs/<job dir 名>/acceptance-*.chain.log、acceptance-<label>-<n>.log、acceptance-child-<label>-<n>.log、acceptance-receipt-*.json、acceptance-<label>-<n>.started.txt / .finished.txt、land*.json / land*.log。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/tools/dev_wave_wait.py — 受入待ち手。`_behind_count` と `_StageFailure("postcheck")` の位置 (3905 行付近) と、その検査が child 起動の前か後かを grep で確かめる。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/tools/dev_wave_land.py — land。`_forward_main_merge_topology` (2120 行付近) の「landing tip ≠ tested tip なら間は main 前方 merge だけ」の検査 (rc=23 = RC_AUDIT)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/docs/dev-wave/operations.md — `DW-O18` (137 行付近、非帰属赤と hold 登録の契約)、`DW-O20` (156 行付近、取り込みは post-claim merge)、`DW-O26` (185 行付近、inventory 4 群)、94 行付近 (記録 commit が tested tip から漏れると rc=23)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/docs/failures.md — `### F1013` (27735 行付近)、`### F902` (24960 行付近、terminal-merge と merge-composition-audit)、`### F524`、`### F1000`、`### F474` は見出しを grep して該当節だけ読む。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/output/insights/2026-09-21/dev-wave-wall-decomp/README.md — 前 wave (entry 1774) の受入再走の記述 (51 行付近・87 行付近)。親の (P3) はこれを訂正する。

## 目的

これは自分たちの開発 wave の受入手順の診断レビューである。診断 wave の段 3 相談 (read-only、reasoning=medium) として、
**親の brief・分類表・草稿自身を検査対象**とし、一次資料 (job dir の log / receipt) と実装 (dev_wave_wait.py / dev_wave_land.py) と正本 (docs) に照らして、
insight を書く前に直すべき欠陥だけを根拠 (file:line、job dir の file 名と行、分類表の行) 付きで指摘せよ。
親を守る側に立つな。見つからなければ「見つからない」と書け。改善策の実装は本 wave の範囲外 (依頼: 診断だけ、gate・台帳・一般化の追加は scope 外、受入の受理集合・門番・hold の意味論は変えない、規律 2 を緩めない) なので、
実装案の良否ではなく「分類と会計と『守られなかった手順』の名指しが一次資料で閉じるか」を点検せよ。

## レンズ (この順で、各レンズは必ず結論を書く)

1. **分類の正しさ (正しさ境界):** 分類表の 15 件の再投入 (最終緑を除く投入) について、親が付けた分類が一次資料の本文 (attempt log の `classification` / `reason`、child log の FAILED 行、chain log の停止行、land 記録の `reason`) と一致するか。とくに (a) 「自分起因 / 非帰属」の帰属は当該 wave の worklog entry / handoff の記録を採るという brief の方針が、記録の無い件 (1759 の赤は worklog に無く handoff だけ) で成立しているか、(b) postcheck を「merge 中に main が前進」と読む (P3) が `dev_wave_wait.py` の順序と 4 件の attempt wall (0.8〜2.6 分、child log 無し) で裏付くか、(c) T-2803 の 3 投入 (緑 → rc=92 → preflight 赤 → 緑) の切り分けが正しいか、(d) T-2817 の ref 走を「再投入ではない」と除外するのは妥当か、(e) 6 分類に入れず「分類外」にした G / H は本当に 6 分類のどれにも当たらないか。
2. **会計の整合 (整合):** (P2) の追加 wall の定義 (最終緑の finished − 最初の投入開始 − 最終緑 1 走) と「再投入分の走 / 親の処理間隙」の分解が、classify.py の計算と timelines-all.txt の時刻で再現できるか (少なくとも 3 wave を手で検算)。門番待ちと走 wall を分ける表示が依頼の「追加 wall (受入 1 走 + lease 待ち)」に答えているか。「lease 待ち = 0 (D662 で待ち行列廃止、待ちは門番だけ)」の主張は receipt / land stderr の lease 行で裏付くか。
3. **『守られなかった手順』の名指し (実効性):** 草稿の表の各行について、名指しした正本 (DW-O18 / DW-O20 / DW-O26 / operations.md:94 / F902 / F524 / F474 / F1000) が本当にその行の事象を扱っているか、「手順違反なし」と書いた行に実は正本の命令があって守られていないものが無いか、逆に「守られなかった」と書いた行が正本に無い慣行 (job dir の chain script など) を手順と呼んでいないか。
4. **過剰と削除 (過剰):** 診断 wave として書きすぎている項目 (実装提案・一般化・gate 新設の匂い) と、依頼に対して欠けている項目 (依頼が列挙する 3 つの既存手順「受入前の main 取り込み位置 / DW-O18 の hold 登録 / 三軸語走査の出力を insight に写さない」それぞれについて、守られたか・守られなかったか・該当事象なしのどれかが明記されているか)。
5. **親自身の実測値とその一般化:** 「20 wave のうち 11 wave が 2 回以上投入、追加 wall 合計 333.3 分」の母集合の取り方 (rulings wave の除外、T-2501 の job dir 消失による繰り入れ) が結論を歪めないか。9 wave が 1 走で済んだ根拠 (timeline に attempt 1 本) は十分か。

## 出力形式

- 各レンズごとに「所見 N: <要旨> / 根拠: <file:line or job dir file 名> / 影響: <分類・件数・wall・名指しのどれがどう変わるか> / 提案: <insight の書き換え内容 (実装ではない)>」。
- 最後に `## 総括` を必ず置き、must-fix (insight を書く前に直す) / should (書き方の是正) / nit を分けて列挙し、must-fix 0 なら「must-fix なし」と明記する。
- 書込可能 tmp は無い。静的検査 (読取り + grep) でよい。test の実走は不要。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。
