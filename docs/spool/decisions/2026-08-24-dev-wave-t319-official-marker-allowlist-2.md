---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t319-official-marker-allowlist
seq: 2
---

## {{D:official-root-marker-allowlist}}. official report の output root は exact official marker の allowlist でだけ受理する

**決定:** D65 P-A1(a) Stage 1 を実装し、official report の consumer 側 root 判定を
blocklist から allowlist へ狭める。判定は次の 5 点で閉じる。

1. root 自身が `{"namespace":"official"}` + LF の exact bytes を持つ marker file を必須とする。
   欠落・exploration・unknown・malformed のいずれも拒否する (従来は欠落を受理していた)。
2. root より上の**全祖先**の marker を走査し、official exact 以外が 1 つでもあれば拒否する。
   最初の 1 件で打ち切らず、非 official 祖先の下に局所 official root を置く迂回を許さない。
3. marker leaf は `O_NOFOLLOW|O_NONBLOCK` の guarded open、`fstat` で regular file 確認、
   exact 25 bytes の有界 read で読む。symlink・FIFO・device を通常 file として read/parse しない。
   input root の既存 symlink component も lexical に拒否する。
4. repository-local の read 例外は canonical な repo output root **ちょうど 1 件**に限る。
   sibling・foreign repository・worktree container へ広げない。外部 root は従来の
   external admission を維持したうえで、さらに exact official marker を要求する。
5. 観測を構築する直前と直後に root と marker を再検査し、走査後の差し替えを拒否する。

read consumer から producer 用の campaign layout 依存を外し、判定を read-only に閉じる。

**限定:** marker は runtime の役割表明であって provenance の証明ではない。正式測定の認可、
holdout の解禁、freeze・proof chain の保証をこの marker へ昇格させない。producer 側の
marker-first 化 (生成時に create-only/exact-check する形) は本決定に含めず、未実装のまま残す。

**migration:** 歴史的 official campaign 集合の migration 単位は canonical root 1 件である。
既存 campaign・report・freeze の bytes を移動も再生成もせず、tracked な marker file を
1 件だけ追加する。この marker は repository の clean enumeration と digest に入り、
freeze allowlist を増やさずに既存の clean scan を通る。

**理由:**
- 欠落を受理する blocklist が残る限り、marker を持たない任意の root と、非 official 祖先を
  隠す子 root が official report の受理集合へ入る。official の観測と verdict が参照する集合が
  暗黙に広がり、防壁として機能しない。
- 祖先走査を「最初の 1 件で停止」にすると、非 official 祖先の直下へ official marker を置く
  一手で迂回できる。全走査でなければ性質を主張できない。
- 対象となる実祖先の marker を先に実測し 0 件であることを確認したため、fail-closed 側へ
  倒した過剰拒否のコストを受容できる。

**却下した選択肢:**
- producer 側の自動 marker 生成まで同時に実装する — 変更面が producer 全型へ広がり、
  本決定の受理境界の検証と分離できない。別タスクの所有とする。
- repository-local root なら marker なしで読む一般例外 — canonical 1 件を超えて広げると、
  sibling repository や worktree container が無条件に official へ入る。
- 相対 path の一般受理 — canonical な相対形だけを exact 例外として絶対化し、その他の相対と
  生の親参照は従来どおり拒否する。
- 全 WAL / store read の openat 化による race の完全封鎖 — 既存の一般 race であり本決定の
  外。marker 経路の TOCTOU だけを閉じ、完全閉鎖とは記録しない。
