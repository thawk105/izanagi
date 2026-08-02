# 段 4 裁定 — [T-139] 正例 artifact (親、2026-08-02)

段 3 の敵対レンズ 2 本がいずれも **NO-GO**。親はこれを受諾する。

## 両レンズが独立に一致した点 (real、採用)

1. **回復候補 X (2 stripe gate) の性能順序が未実測。** `degraded < X < stock` が成り立つ保証は
   どこにもない。A・B とも (d) で「確認できなかった前提」の筆頭に挙げた。
   → **`DW-G01` (生死実験先行) 違反。これは親 brief の欠陥である。**
   親は恒久実装と 240 run 本走を、最安の生死確認より前に置いていた。
2. **manifest の自己宣言による admission 拡張。** 新 manifest が自分で
   `recovery_measurement_eligibility: true` を名乗る形は、D120 決定 2 の**直接の**禁止対象
   (旧宣言の別 policy による上書き) ではないが、**未裁定の権威境界を親が独断で新設する**点で
   同じ穴の別入口である。A-B1 と B-P2 が独立に同じ判定を返した。
   → **不採用。権威境界の設計はユーザー裁定へ返す。**

## 親が real と裁定した個別所見 (実装時の要件として持ち越す)

- **A-B2** activation witness と実行 executable の SHA が終端で結合されていない。
  *成果物影響:* 結合しないと、別 binary の測定値を正例として台帳へ入れられる。
- **A-B3** measurement checkout が独立取得でなく複写でも通る。
  *成果物影響:* 測定 checkout の記録が偽装可能なら F41 の恒久義務が恒真になる。
- **B-1** arm ごとの between-session CV を **paired 差**の floor に使うのは統計的に誤り。
  paired session 差で取るべき。
  *成果物影響:* floor を誤ると「識別可能」判定が甘くなり、分母が noise と区別できないまま
  正例を名乗る。
- **B-5** 消費側 (材料レポート / Layer3 / 選択) に RF の consumer も producer も無く、
  触るのは 9 層中 5 層。*成果物影響:* gate を作っても誰も呼ばない構造になる。
- **A の brief 訂正** 要求は **7 件** (3 arm + 6 性質)、充足 3・不足 4。親 brief の表は
  between-run floor を落として「6 件」と書いていた。**訂正する。**

## 裁定 (`DW-S04`)

### 不採用 — 段 2 プランの恒久実装部分すべて

新 patch の恒久登録、qualification manifest、新 contract、新 producer、新 artifact、
8 allocation × 240 run の本走は**本 wave では実装しない**。理由は上記 1・2 の両方。
特に 2 は親の権限外である (`DW-S04`: scope 外の real 所見は実装せず裁定パッケージで返す)。

### 採用 — `DW-G01` の生死確認 probe **だけ**を実装して走らせる

両レンズが「許容できる次の一手」として一致して挙げたもの。これは:

- **使い捨て**である (恒久 patch 登録も台帳登録もしない)。
- **受理集合を変えない** (artifact を発行せず、qualification manifest を作らない)。
- **未裁定の権威境界に触れない。**
- そして**これ無しには plan v2 が書けない** — X が成立しないなら設計全体が無意味になる。

先例は本 task 自身の生死確認 (設計台帳 §3、job 873583) であり、その扱い —
「trace-disabled・t48 の局所観測による**方向シグナル**であって性能主張ではない」— を継承する。

**probe の受理条件 (事前固定):**

- trace-disabled、t48、2 workload (W-cal / W-hw)、3 arm (stock / mode1 / mode2)。
- 単独性を確認してから計測する (F3 恒久対応)。確認できなければ計測しない。
- 判定は「**両 workload で `mode1 < mode2 < stock` の順序が全標本で成り立つか**」の
  方向シグナルのみ。RF 値・p 値・区間・CV による識別可能性判定は**行わない**
  (未裁定 scope、B-1 の指摘どおり現案の floor は誤っている)。
- 順序が成り立たなければ **X は不成立**と記録し、代替 X の設計を次 wave へ返す。
  成り立っても「正例 artifact ができた」とは名乗らない。

### 変異事前登録 (`DW-M01`)

probe は gate を新設せず受理集合を変えないため、**変異 matrix は対象外**とする。
worklog にこの射程を明記する。

## 段 5 以降の重量

probe は受理集合不変・正しさ防壁非接触・設計択一なしのため **軽量版**とする
(`DW-C00`)。実装面 (probe patch と driver) は Codex `role=author` が書き、親は直接編集しない。
段 6 の敵対レビュー 2 本は省く。実測は親が行う。

## ユーザー裁定へ返すもの (裁定パッケージ)

1. **新しい正例 artifact の適格性を、誰の権威で宣言するか。** 凍結 ledger は exact-one contract で
   閉じており追記できない。manifest の自己宣言は両レンズが拒否した。
   択 = (a) 新 D で権威境界を定義し `artifact_role=qualification` を [T-318] 準拠で置く、
   (b) ledger の exact-one contract 自体を改訂する、(c) 正例を artifact として発行せず
   計測記録のみに留める。
2. **paired 差の floor をどう定義するか** — これは未裁定の「RF 規範の統計設計 5 点」の一部であり、
   正例 artifact の受理条件がそこに依存することが本 wave で判明した。
   正例と統計規範のどちらを先に決めるかの順序裁定が要る。
3. **消費側の不在** — RF を消費する producer / consumer が実在しない。
   正例 artifact を作っても呼ぶ者がいない状態を許すか、consumer とセットで設計するか。
