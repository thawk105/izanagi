---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t657-permanent-bundle-design
seq: 2
---

## {{D:calibration-freeze-authority-bundle}}. 較正と凍結の世代交代を上位の権限束として設計する

**決定:** 環境契約の活性化 (較正) と ratified freeze の世代を、**上位層の権限束**として 1 つの
identity のもとで解決する。正本は `docs/calibration-freeze-authority-bundle-design.md` (第 1 設計段、
裁定待ち)。freeze 族**内部**の設計正本は改訂せず、適用範囲と precedence の注記だけを追記する。
precedence は状態文でなく「上位 namespace の pointer record が上位 resolver の検証をちょうど 1 つ
通って解決できる HEAD か」で判定する。

**理由:**
- 較正の世代交代は凍結の世代交代なしに完了しない。環境だけ進めると live admission の契約 hash が
  食い違い、固定 path の凍結成果物を上書きすると履歴不変条件と盲検封印の紐付けが同時に壊れる。
- 凍結側の bundle digest は成分数固定・配列長強制・domain separator 固定として既にユーザー承認済みの
  exact 契約である。環境成分をそこへ足すと承認済み契約の改訂になる。上位に別 domain の束を置けば
  凍結側を 1 byte も変えずに済む。
- 上位束は下位と同じ形 (承認 record が成分一覧と digest を持ち、pointer が承認 record を指す) に
  する。独立した束 record を別に置くと、その hash を digest の原像へ入れれば自己参照になり、
  入れなければ差し替えても identity が変わらない。

**却下した選択肢:**
- 凍結側 digest への環境成分の追加 — 承認済み exact 契約の改訂を要する。
- 下位 pointer をそのまま production authority として使い続ける — 環境と凍結を別々に解決すると、
  上位が承認していない直積が再生成される。敵対レビュー 2 本が独立にこの経路を構成した。
- 環境の有効 head を literal から record へ移すことを前提にする — literal を残したまま成立する
  topology の反例が構成されたため、必要条件ではない。解決方式は択一として開く。

## {{D:design-completion-criteria-need-positive-fixture}}. 設計の完了判定は陽性 fixture を実体として固定する

**決定:** 段階分割の各段の完了判定は、陰性条件 (不正入力が落ちる) だけでなく**陽性条件
(正常入力がちょうど受理される)** を持つ。さらに陽性・陰性 fixture は、閉じた manifest、
不変条件の各行との全単射、実際に走らせる検査 node の名前まで固定して初めて完了判定になる。
「未定義」と書かれた段は完了と宣言できない。

**理由:**
- 陰性条件だけを完了判定にすると、**何も受理しない実装 (reject-all) が全段で緑になる**。
  敵対レビューが独立に 3 段でこの構成を作った。
- 「正常な入力が通る」と書くだけでは、任意の 1 ケースを通して完了と主張できる。
- fixture を置くだけでは、検査を一度も呼ばずに完了と主張できる。

**却下した選択肢:**
- 各段の完了判定を設計文書の時点で exact に書く — 陽性 fixture の実体が裁定に依存するため、
  書けば恒真になる。書けないものを書けたことにしない。
