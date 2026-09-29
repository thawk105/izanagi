## 反例と正しさの所見

- **提案どおりの窓式には、指定資料から反例を構成できない。** `_derive_required_literal` は key の正規表現記号を拒否し、値側も `.` 以外の記号を拒否するため、非 `None` の式には anchor・lookaround・`\b` が入らない。各 match は導出された `L` を含む。最大幅 `W` が実際の上界なら、`lo=p+len(L)-W`、`hi=p+W` は左右とも十分で、`endpos=hi` は終了位置が `hi` ちょうどの一致を許す。`.` は改行に一致しないが、この包含と幅の論証は変わらない。放置すると、幅の上界を保証せずに局所化した場合、hit を落として report と受理集合を変える。[s8b_holdout_freeze.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:423)、[同:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:447)、[plan:等価性の論証](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md)
- **境界と重なりは個別に殺せる。** `(?:k=v)`、text `k=v` では `hi=p+W-1` が hit を落とす。`(?:aa=b)`、text `aaa=b` では `aa` の位置 0 は不一致、位置 1 は一致するため、次の探索を `p+len(L)` にすると hit を落とす。`(?:\"k\":\"v\")` では key の出現位置より前から match が始まり、`lo=p` が hit を落とす。いずれも単軸で確かめないと report の conjunction に隠れうる。放置すると per-axis count、hash、場合によって受理集合が変わる。[s8b_holdout_freeze.py:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:417)、[plan:test と変異候補](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md)
- **右端の変異 fixture は明示的な単一 alternative が必要。** 現行の三形式を含む式では最大幅が JSON 形式由来になり、plain 形式の hit は `p+W-1` でも窓内に収まりうる。「最長長さの plain 形式」という記述だけでは kill を保証しない。放置すると右端の off-by-one が生存し、将来の式で hit を落としうる。[test_s8b_holdout_freeze.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_holdout_freeze.py:550)、[plan:変異表](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md)
- **幅の数値仕様は plan の断定を根拠にしない。** 射影資料だけでは Python 3.10 の `getwidth()` の飽和值を検証できない。`MAXREPEAT` 以上と解析失敗を全文 search に倒す方針は保守的だが、幅は最大値だけを使い、最小値を窓幅に使ってはならない。放置すると過小な `W` により report の hit が欠落する。[plan:等価性の論証](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md)、[s8b_holdout_freeze.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:564)

## 既裁定との整合

- 同一 `expression_snapshot` から compile・literal・幅を導き、非 exact `str` を従来経路に戻す案は D350 と整合する。stdlib の `sre_parse.getwidth()` を使うこと自体は新しい正規表現文法の自作 parser ではない。放置すると snapshot の食い違いで正しい hit を捨て、受理集合が変わる。[s8b_holdout_freeze.py:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:525)、[D350-D351.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D350-D351.md)
- 列挙・読取・decode・免除を維持し、memo を一呼出しの `texts` identity に束縛する案は D512 に沿う。ただし新しい局所化 helper が **`L` 導出失敗、幅解析失敗、非 exact `str` の全経路で全文 search に戻る**ことを実装と単軸 test で固定する必要がある。放置すると report bytes と受理集合、または例外契約が変わる。[s8b_holdout_freeze.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:543)、[同:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:608)、[D512-D513.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D512-D513.md)

## 番人と変異

- 候補 helper の回数 0/5/9 と、bounded/full の実呼出しを別々に固定する方向は D513 に適う。候補回数だけでは局所化を外す変異が等価に生存する。reference `_scan_one` の三回呼出しと全 report bytes 一致も残す必要がある。放置すると結果等価な性能退行を見逃す。[test_s8b_holdout_freeze.py:985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_holdout_freeze.py:985)、[同:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_holdout_freeze.py:1064)、[D512-D513.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D512-D513.md)
- **`MAXREPEAT` fallback を外す変異と注入 test の組は、現案では等価変異になりやすい。** 短い text に巨大な幅を注入すると窓が全文に広がり、fallback の有無で真偽も search 範囲も同じになる。helper が反復式を拒否するため自然入力にも該当しない。この変異を必須 kill とせず、fallback 分岐の選択を直接観測する test にするか、変異表から外すべき。放置すると変異監査の赤緑を誤解するが、通常入力の report は変わらない。[s8b_holdout_freeze.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:449)、[plan:変異表](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md)
- 共通 literal の `in` 自体を外す変異は、`ycsb_unrelated` の候補回数では殺せない。軸 literal の `find` が引き続き 0 候補へ落とすためである。共通判定の実発火回数を独立に測る番人が必要。放置すると共通 prefilter の性能退行だけが生存し、report は同じままになる。[s8b_holdout_freeze.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:559)、[test_s8b_holdout_freeze.py:1011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_holdout_freeze.py:1011)
- `rel` だけで共通判定を cache する変異には、第一走で literal A が**不在**、第二走で別の literal B が**存在**する同一 rel を使う。逆順の「A あり→B なし」は軸 `find` が誤った cache hit を覆い隠しうる。単軸 test を使えば F264 の多軸 mask も避けられる。放置すると第二走の hit を落とし、report と受理集合が変わる。[s8b_holdout_freeze.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:550)、[F264.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/F264.md)

## 親の実測の読み

- 4,313 sample は 50 Hz 換算で約 86 秒、regex 行 2,311 は約 46 秒、共通 `in` 行 806 は約 16 秒という読みは算術上正しい。ただし行帰属は節約可能時間の上限ではない。窓ごとの regex search と `find` が新たに発火し、literal の出現数次第で総走査量が増える。放置すると 50〜60 秒削減を既測定の効果として誤認する。[profile-summary.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md)、[plan:効果の見込み](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md)
- `search_repository` 約 13 回と一回約 6.6 秒は call graph と総時間からの**見込み**であり、profile に実呼出し回数の計数はない。fixture は計算ノード `/tmp` 上で、実 repo の共有 filesystem と text 分布も異なる。放置すると child の短縮を shard-0 の短縮へ過大に一般化する。[profile-summary.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md)、[s1-brief.md](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md)

## 判定

**修正後 GO。** 窓探索の等価性論証は現 helper の受理文法では成立する。右端と重なりを確実に殺す単軸 fixture、共通判定の独立回数番人、等価になりやすい `MAXREPEAT` 変異の扱いを修正してから実装・計測へ進むべき。

## 総括

正しさの主な危険は窓式そのものより、境界 test と発火回数番人の縮退にある。
`getwidth()` の上界と fallback を実装上で保守的に扱い、全 report bytes を独立 reference と比較する。
50〜60 秒削減と 13 回走査は予測であり、実受入の計測で判定する。