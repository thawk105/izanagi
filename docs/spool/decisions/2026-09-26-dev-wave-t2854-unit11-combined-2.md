---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: dev-wave-t2854-unit11-combined
seq: 2
---

## {{D:tpcc-v3-combined-candidate}}. TPC-C 段 1 の CCBench 候補は C → C1' → C3 → C2' の別名 branch に 1 系列で並べ、結合確認は silo・mocc の両方を C 基点で取り、D297 の header 差分の受理方式は既裁定の変更を要するので 4 択にしてユーザーへ諮る

**決定:**
1. **系列:** CCBench の新しい local branch `izanagi-tpcc-v3-silo-mocc` = C `68106660` (現 pin) → C1' `6aa7a58f` → C3 `53f6b097` → C2' `40a7f4acb174ca43cb590f40d13847216a1564bc`。C2' は C2 (`a6f2c741`、silo の v3 emitter) の `cherry-pick -x` で、C1' と C3 は OID のまま使う。公開済みの `izanagi-tpcc-v3-trace` は残し (D2235 項 1)、同名への force push はしない。push・gitlink・承認定数・pin は動かさない。
2. **結合確認の命題と範囲:** 「C2' の単一 source tree から作る各 protocol の binary が、共有 header と各 emitter を正しく使う」。C を基点に、silo・mocc の TPC-C の v3 構造・witness・内容、YCSB の v2 と現行 verifier の certified、変更 header を読む 21 compile entry の TRACE=0 完全展開・include 活性、4 binary (tpcc / ycsb × silo / mocc) の nm・strings・正規化逆アセンブル、TRACE=1 の構文検査を計算ノード 1 走で取る (request 29455.nqsv で全段合格)。
3. **変異:** 結合に固有の層だけを登録する。共有 header の取引種別 setter の削除 (両 protocol が先頭理由 schema)、共有 header の `#line` 削除 (TPC-C 9 entry だけ完全展開が不一致)、protocol 側の代表として silo の表 6 → 5 (content-table だけ) と mocc の種別 1 ↔ 2 (content-txtype だけ)。単位 1〜3 で済んだ計数順序・各 protocol の `#line` は再演しない。影響しない側の再 build・再走行は kill 条件にしない。4 件とも KILLED。
4. **D297 の扱い:** 現行の D297 検査器は C → C2' を `include/tpcc.hh` の header 差分で拒否する (rc=1、前処理に入る前の差分検査)。本決定は C2' を pin に入れず、検査器を変えず、D297 の合格も TPC-C の certified も名乗らない (D2225 決定 6 と同じ)。
5. **受理方式:** 既裁定の変更 (D297 の受理規則の改訂か C2' 限定の例外) か作り直しを要するので、AI の判断では採らず 4 択でユーザーへ諮る — 択 1 D297 の header 受理規則の設計審査 (推奨。審査の承認と実装の委任は別の裁定)、択 2 C2' に限る代替証拠での受理、択 3 header を変えない別候補 (D2225 決定 2・3・5 と D2230 の再裁定が要る)、択 4 当面は何もしない。各択の不足する保証と費用は `output/insights/2026-09-26/t2854-unit11-combined/README.md` §5。

**理由:**
- C3 と C2 は変更 path が重ならず、C3 の silo の blob は C1 の silo と同じ (`054a7e5f`) なので、C2 は C3 の上にそのまま当たり C2' の blob は C2 と一致する。C1' と C3 を作り直さなければ単位 3 の証拠がそのまま効く。
- 単位 1・2 (e9e477ca 系列) と単位 3 (silo を含まない) の証拠では、共有 header が 2 protocol の v3 切替を同時に担うこと、C (mocc の X/P 計装) の上で silo の emitter が働くことを取れない。結合でしか取れないのはこの 2 点と、同じ tree での TRACE=0 同一性である。
- 検査器の 16 文脈は silo の有効 genome 8 × `GLOBAL_VALUE_DEFINE` の有無で、実 TPC-C build の 16 構成ではない。header 拒否の残る本質は「header 単体の前処理は consumer TU の展開を代表しない」ことで、`-dD` で「#define を残さない」は部分的に解消している。したがって受理方式の論点は consumer TU の列挙と TU ごとの文脈であり、その規則は段 2 の header 変更にも効く。
- 依頼は検査器の拡張と代替証拠での受理を委任していない。段 1 の v3 と witness は header を変える形で決まっている (D2225 決定 2・3) ので、D297 を変えずに C2' を通す道は無い。

**却下した選択肢:**
- C1 / C2 / C3 を C の上へすべて作り直す — C1' と C3 の OID と単位 3 の証拠が失われ、結果の tree は同じ。
- 単位 1〜3 の変異 (計数順序の D1 / M2、各 protocol の `#line`) を全量再演する — header の blob は同一で、結合固有の情報を増やさない (段 3 相談 B)。
- 本 wave で検査器に consumer TU の解析を足して合格させる、または本 wave の証拠で C2' を受理する — 委任外で、D297 の受理規則を候補に合わせて変えることになる。
- 択 1 を「実装まで含めて別 wave で進める」形で推奨する — 未設計で費用の上限が無く、設計審査と実装の委任を 1 つの選択に束ねる (段 3 相談 A)。
