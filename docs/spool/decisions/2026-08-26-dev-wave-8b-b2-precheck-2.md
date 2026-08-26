---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-8b-b2-precheck
seq: 2
---

## {{D:b2-precheck-blockers}}. B-2 の閉塞は独立な複数本ではなく層であり、最上流は完了証明層の不在である

**決定:** 論文 §8 の B-2 (descriptor を条件にした合成の因果証拠) を投入できない理由を、
独立した blocker の列挙としてではなく**依存の層**として記録する。上流から順に、
(a) 発効判定に充足を返す終端が存在しない、(b) 事前登録 §5 の数値欄 7 件が未記入、
(c) 正式 profile の hard stop、(d) 6 cell manifest・二段束縛 record・trial registry の不在、
(e) schedule authority の無条件 raise、(f) 共有 8b ratified freeze が active でない。
**(b)〜(e) は (a) に従属する下流症状であり、順序を入れ替えて先に解除してはならない。**

**理由:**
- 発効は「条件契約の妥当性 ∧ 判定器版一致 ∧ §5 全記入 ∧ 12 条件すべて充足」の連言である。
  評価器には充足を返す site が 1 つも無く、加えて `SATISFIABLE_CONDITION_IDS` が空であるため、
  仮に充足を返しても ERROR へ倒される。**したがって (a) を解かない限り (b)〜(e) を
  すべて解いても発効しない。**
- これは実装漏れではない。理想的な合成入力に対しても終端が
  `completion-proof-not-machine-checkable` であることを既存テストが期待値として固定しており、
  8c 事前登録 §6 条件 2 の「充足を返す経路は無い」という記述と一致する。意図された
  fail-closed である。
- §5 の欄を先に埋める順序は、事前登録自身が禁じている。判定パラメータ欄は型・単位・向きを
  機械検証する consumer が実在するときにしか記入してはならず、6 cell manifest 欄は
  arm binding と registry と二段束縛を実際に消費する配線が揃うまで記入してはならない。
  **順序を守らない記入は、検証されない値で発効を通す。**
- 閉塞を「独立 3 本」と記録すると、どれか 1 本を外せば前進すると読める。実際には最上流を
  外さない限り 1 mm も動かない。逆に (f) だけは (a) と独立に進められる別線である。

**却下した選択肢:**
- **閉塞を独立な blocker の列挙として書く** — 並列に解除できるという誤読を生む。
  段 3 の 2 レンズが独立に同じ点を指摘した。
- **正式 profile の hard stop を外して先へ進む** — (a) が閉じていない状態で
  受理集合を広げる変更であり、絶対規律 2 に反する。
- **§5 の欄を先に埋めて発効判定を通す** — 事前登録が明示的に禁じる順序違反である。

## {{D:noncertifying-canary-not-b2-evidence}}. 非認証の登録経路で走らせた対照は B-2 の証拠に数えない

**決定:** `registered-formal-non-certifying` の登録モードで正式 workload の
on/off/swapped を走らせても、**それを B-2 の因果証拠として算入しない。** 配線の検査
(canary) としてのみ用い、成果物には非認証であることを明示する。
またこの経路を使う canary は、6 cell manifest・二段束縛 record・trial registry を
authoring する実装 wave の成果物であり、precheck の scope では取らない。

**理由:**
- 当該モードは `certifying=False` を返し、role payload も `scientific_claim=False` である。
  発効判定を呼ばずに条件契約 freeze の妥当性だけを検査する経路であり、
  「認証しない代わりに走る」という設計意図が型に現れている。
- 8b 設計 §10.6 の epoch 境界が、追随実装の発効前に走った run を legacy・exploratory と定め、
  後から formal へ昇格・再解釈・混合しないと明記している。
- この経路の manifest loader は**ちょうど 6 試行**と**世代数 = 整数 2 固定**を要求するため、
  「軽い 1 セル canary」という中間物は存在しない。canary を取る判断は、6 セル分の
  事前登録 artifact を authoring する判断と不可分である。

**却下した選択肢:**
- **非認証 canary を「配線 demo」として B-2 の補助証拠に添える** — 既知結果の追試を
  新発見へ数え替える経路であり、8b 設計 §1 が名指しで禁じる形と同型である。
- **canary を precheck の中で取る** — artifact の authoring は実装面であり、
  親が直接書けない。取るなら Codex 実装子を持つ別 wave になる。
