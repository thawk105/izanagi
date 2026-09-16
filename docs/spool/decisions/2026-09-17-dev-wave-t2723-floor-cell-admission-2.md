---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2723-floor-cell-admission
seq: 2
---

## {{D:floor-cell-reads-through-section5-admission-parser}}. B-4 floor セルの読取は事前登録 §5 の admission 固定表解析と責任者行述語を共有し、他欄の充足は検査しない

**決定:** 材料レポート → floor artifact issuer の floor セル読取 (`resolve_preregistered_authoritative_floor`) は、
文書全体の exact prefix 走査をやめ、`p3_b4_admission_record.py` の既存 §5 検査から切り出した 2 つの helper
(固定表の解析 = `## 5.`〜`### 5.1` の一意な見出し境界・fence / HTML comment の除外・12 非空行・exact header・
label 集合・cell の strip + NFKC + default-ignorable 拒否、および 1 セルの受理述語 = D2079 の責任者行 1 形 +
一般 sentinel 規則) を通して、§5 固定表の floor セル 1 つだけを読む。読取は次の順で決まる。

1. 共有 parser が文書を受理しない (境界・形状・label 集合・不可視文字) → 拒否 (`preregistration_floor_row_error`、
   不正 UTF-8 だけ `preregistration_encoding_error`)。
2. floor 行の strip 前 label が定数と exact 一致しない → 拒否。
3. 責任者行 `実行責任者・開始時刻` の normalized value が admission の 1 セル述語に違反する → 拒否
   (sentinel による absence 判定より先に検査する)。
4. floor セルの strip 後 raw が `未記入` と一致 → floor 不在 (None、材料レポートの legacy 経路)。NFKC は掛けない。
5. それ以外は strip 後 raw を既存の pin grammar (`artifact_path=…; sha256=…`) で解き、path / hash を raw のまま
   `load_authoritative_floor` へ渡す。

**決定 2:** 他欄の sentinel と expectation 行は floor 経路で検査しない。現行の実文書は floor を含む 6 欄が `未記入`
であり、これらを検査すると正例 (現行文書で floor=None) が落ちる。他欄が `未記入` のまま有効 pin を置けば floor が
present になる既存挙動は本決定で変えない。完了主張は「floor セルの読取を §5 固定表 + 責任者行述語へ接続した」に
限り、事前登録の発効条件への完全接続は主張しない。

**決定 3:** 受理集合の変化は列挙で契約する。拒否→受理は (a) floor 値セルの外周空白の strip (admission と同一)、
(b) 真正 §5 の外にある同 prefix 行の無視、の 2 系統だけ。受理→拒否は共有 parser の全条件・floor label の exact
一致・責任者行述語・path 中の ASCII `|`。admission 関数自身の受理集合・例外 message・検査順は不変。

**決定 4:** 実文書を直読して None を確かめる回帰 test は conftest の real-repo 分類へ登録しない。

**理由:**

- 起票 (worklog 1571 の T-2723 項) と同型の失敗型は F423 (文書全体の string search で「本物の箇所」を決める設計は decoy に欺ける)。
  既存の admission parser は見出し境界・fence / comment 除外・label 集合・不可視文字拒否を既に持つので、
  新しい validator を設計せず接続するのが最小差分である。
- 親の対照 probe (実文書 bytes の最小改変、変更前後の module で同一入力): 責任者を `未記入` にした文書は変更前 None
  (受理) → 変更後 row error。§5 の floor 行を消して外側に pin を置いた文書は変更前 path_error (外側 pin を読んで
  loader へ進んだ) → 変更後 row error。§5 外に pin 行を足しただけの文書は変更前「exact 1 件」で生成停止 →
  変更後 None (無視)。
- sentinel を NFKC 後に比べる案 (段 2 plan) は、`未記⼊` (末尾 U+2F0A) のような異体を拒否から None へ変える追加緩和
  になる (段 3 レンズ A の実測)。strip 後 raw に限れば拡大は strip だけに収まる。
- floor label を strip 前 exact 一致に保つのは、新経路が選ぶ行が常に旧経路の prefix 候補でもあることを保ち、両版で
  成功する入力の floor 値・参照先が変わらないためである。
- 決定 4 の根拠: 実文書を直読する既存 test (`test_p3_b4_analysis_prereg_consumer.py`) は未登録・marker 無しの先例で、
  access map の親 working tree への access は全 node が read (writer 不在) なので登録は shared lock と xdist group の
  付与だけで正しさに効かない。分類監査は TMPDIR literal の AST 走査だけで実 repo 読取を機械検出しない。依頼が
  「仮想リスク向けの台帳追加は scope 外」と定める。

**却下した選択肢:**

- 他欄の sentinel 検査を floor 経路へ持ち込む — 現行文書で正例が落ち、依頼の scope 外。
- NFKC 後の値で sentinel を判定する — 拒否→None の追加緩和 (規律 2)。
- admission 関数を丸ごと呼ぶ — expectation 行の grammar と model / prompt 照合まで要求し、現行文書を受理できない。
- floor label にも admission の strip + NFKC 一致を許す — 旧経路が読まなかった行を新経路が読みうる。
- 実文書 test を real-repo 分類へ登録し conftest と golden 2 file を触る — 正しさに効かず、依頼の scope 外の台帳追加。

**残存限界 (記録のみ、本 wave では触らない):**

- 両見出し (`## 5.` / `### 5.1`) を軽微に壊して別所へ canonical な §5 完全表を置く F423 型は admission parser 自身の
  既知限界 (見出し探索は raw exact 一致の文書全体走査) として残る。
- 実文書 → None の回帰 test は現在の未登録状態の写しであり、floor が正式登録される wave で更新する。
