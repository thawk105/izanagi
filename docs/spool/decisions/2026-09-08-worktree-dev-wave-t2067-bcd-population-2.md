---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: worktree-dev-wave-t2067-bcd-population
seq: 2
---

## {{D:floor-selection-unenforced-population}}. 床値選択の未強制母集合は到達条件を併記した 2 群とし、二読 fallback は実装せず裁定へ返す

**決定:** 床値選択規則を強制していない入口の母集合について、次を確定する。

1. **母集合の単位は「批准床値 (`RatifiedFreeze`) を静的 loader で得る production callsite」**とする。
   2026-09-08 の main での値は 9 callsite / 9 関数 / 7 module で、内訳は強制済み 7
   (狭い選択 API 5 + full launch validation 2) と未強制 2 である。
2. **未強制 2 群は C06 予算群と、standalone gate の二読 fallback
   (`orchestrator/campaign/s8b_oracle_driver.py` の `_gate_check_core` 内 self-load) とする。**
   後者を母集合へ載せるにあたり、**到達条件を併記する** — 発火には「初回 read が失敗し、
   直後の再 read が成功する」外部要因の状態変化が要り、`sha256` 完全一致の要求により受理されうる
   freeze は active 世代そのものに限られる。先行 wave の「private core の self-load だから
   public wrapper はこの形で到達させない」という除外は採らない。
3. **件数の出所は AST 走査であると明記し、権威ある閉包に由来するとは書かない。** loader の caller を
   exact 一致で固定するメタテストは repo に実在しない。隣接する `build_observations` /
   `_gate_check_validated` / `verify_manifest` には caller 閉包テストが実在するため、
   対象を取り違えると在るものを無いと書くことになる。
4. **二読 fallback を閉じる実装は本課題では行わない。** 択一 (現状維持で記録する / exact
   `LaunchValidatedFreeze` 必須へ縮める) をユーザー裁定へ返す。
5. **library 経路 (`verify_manifest` が選択 token を要求しない、`build_observations` の
   optional 引数、`_write_approved_manifest`) にも選択強制を課さない。** production の到達経路が
   0 件であり、閉じていない範囲として記録に留める。

D1241 / D1313 の advisory / non-certifying 上限は解除しない。

**理由:**

- 除外の根拠だった「public wrapper はこの形で到達させない」は、公開 CLI からの具体経路で破れる。
  最初の freeze load が失敗すると core へ入り、core は同じ path を自分でもう一度読む。
  二読目が v2 として成功すると、launch validation を通さないまま gate 判定へ進む。
- 一方で DW-G04 は「発火条件を満たす既存 artifact path か計測 ID を書けない条件付き機能は
  設計メモに留める」と定め、DW-G05 は「成果物への影響を示せない must-fix は nit / backlog」と定める。
  この fallback は安定した同一 filesystem 状態では発火せず、どちらの基準も満たさない。
- 放置時の被害は限定される。受理されうるのは active 世代そのものであり、別の freeze が
  混入する経路ではない。欠けるのは active 世代自身の選択 identity 検査である。
- ただし D65 決定 (5) が「public gate_check は v2 で必ず自己検証」と定めており、この分岐では
  その不変条件が成立していない。**承認済み裁定に対する新事実**なので、親が不採用で閉じず
  裁定へ返す。
- 件数の出所を偽らないことは、後続が「権威ある閉包で数えた」と誤読して再検算を省くのを防ぐ。

**却下した選択肢:**

- 先行 wave の除外を維持する — 公開 CLI からの到達経路が示された以上、事実に反する母集合の上で
  残余を数えることになる。
- 二読 fallback を今すぐ token 必須へ縮める — DW-G04 / DW-G05 に反し、依頼の scope 制約
  (仮想リスク向けの gate・検査の追加は scope 外) にも反する。regression の固定には
  「初回失敗→二回目成功」を mock で作る node が要り、既存入力の回帰ではなく仮想遷移の新設になる。
- library 経路へ選択 token を課す — production 到達経路が 0 件であり、同じ理由で仮想リスク対応になる。
- 母集合の件数を「権威ある閉包に由来する」と書く — そのメタテストは実在しない。
- 到達条件を書かずに未強制 2 群とだけ記録する — 2 群の到達可能性が同じだと誤読され、
  C06 (裁定済みで機構的に到達しない) と fallback (race でのみ到達) の差が消える。
