---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t922-measure-happypath
seq: 2
---

## {{D:t810-shipped-anchor}}. 測定装置の authority は import 解決でなく設置場所から導く

**決定:** T-810 測定装置が caller の申告値を検証するとき、比較の相手 (authority) は
**coordinator 自身の設置場所からパスで導く**。具体的には staged wrapper の bytes は
`Path(t810_coordinator.__file__).resolve().parent / "t810_pbs_wrapper.py"` の実 bytes と、
repository roots は `resolve_git_identity(Path(t810_coordinator.__file__).resolve().parents[2])` の
live git identity と比較する。**import 済み module の `__file__` を authority にしない。**
caller が別途 roots を渡す経路は残すが、authority との**和集合**とし、caller は roots を
増やせるが減らせない。

**理由:**
- `tools` と `tools/pegasus` は `__init__.py` を持たない namespace package である。
  `PYTHONPATH` に別の `tools/pegasus/` を先置きすれば、official な coordinator を repo から
  読みながら wrapper だけを差し替えられる。import 解決を authority にすると、
  攻撃者は「authority 自身」を用意できてしまう。設置場所からパスで導けばこの経路は塞がる。
- 測定装置には launch intent / config を書く production producer が存在しない。
  producer が無い以上、caller config の外に置ける根は「今まさに動いている実装の所在」しかない。
  凍結 pin 台帳や署名連鎖を新設せずに済むため、凍結チェーン検証の保留 (D328) とも衝突しない。
  D328 の保留対象は実装↔測定の同一性検証であり、実行認可 (admission) と信頼境界は対象外である。
- caller roots を捨てず和集合にするのは、authority が一時的に不完全でも受理集合が広がらない
  ようにするためである。共有 repo では並行 wave が worktree を絶えず追加・撤去するため、
  live な registry は一瞬だけ解決不能になりうる。解決できない登録は**捨てず**、
  その登録が主張する root を非 strict 解決で保持する。roots への操作を追加のみに保てば、
  外乱は過剰拒否にも受理拡大にも化けない。

**却下した選択肢:**
- import 済み module の `__file__` を authority にする — namespace package の shadowing で
  authority ごと差し替えられる。
- 解決不能な worktree 登録を skip する — 並行 churn は消えるが、main tree の外にある
  linked worktree が roots から落ち、そこへの書き込みが repository-external として受理される。
- 解決不能な登録で fail-closed のまま止める — 他 session の worktree 操作という無関係な外乱で
  測定準備が失敗する。安全側ではあるが正当な運用を殺す。
- 検査を最上位の入口にだけ置く — 内側の adapter を直接呼べば迂回できる。private 名は
  能力境界ではない (D331)。検査は最内の effect adapter に置く。
