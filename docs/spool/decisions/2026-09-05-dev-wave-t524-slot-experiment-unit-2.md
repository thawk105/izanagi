---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-t524-slot-experiment-unit
seq: 2
---

## {{D:slot-unit-downstream-enforcement}}. slot 組の実験単位は、下流の受領証検証器で強制する

**決定:** D1269 の最小形を、次の 2 箇所に置く。

1. **承認側 (attempt registry genesis)。** slot へ `prereg_generation` を必須 field で足し、
   schema を v3 へ上げる。root 全体で世代が単一であることを全 reader に要求する。
   genesis 作成器は `prereg_generation` を必須引数に取り、全 slot の同名 field と exact 一致を
   要求する。slot への自動補完経路は作らない。
2. **下流側 (outer acceptance receipt の検証器)。** receipt schema を v5 へ上げ、attempt registry の
   path・prefix hash・slot projection (世代・全 unit・個数)・内容 commit・発効 commit を束縛する。
   `verify_acceptance_receipt` が prefix を独立に replay し、genesis 由来の非空期待集合と
   final terminal を照合する。下流の消費入口は current schema (v5) を必須とする。

**理由:**

- **series key に世代を入れてはならない。** 段 3 レビューが実測で示したとおり、series key へ
  世代を足すと、同じ series に別世代の `attempt_index=0` を 1 件ずつ置いた形が別 series として
  通り、**受理集合が広がる**。世代の単一性は series key ではなく root 全体の不変条件として書く。
- **発行側に全列挙 helper を足しても純増にならない。** 独立 2 レンズが同じ file:line へ到達し、
  outer acceptance は既に 6 report・manifest exact・genesis initial・report↔terminal の合成で
  全 unit 消費を強制していることを示した。同じ入力を前後の層が拒否する位置に変異を登録できず、
  単一理由性 (`DW-M01`) を満たせない。**実効 gate は下流の検証器側にある。**
- **旧 schema への downgrade は迂回路になる。** v5 を足しても、下流の消費入口が v1〜v4 を同じ
  verified capability へ通すなら、下流は旧 schema を選ぶだけで新しい検査を丸ごと回避できる。
  この状態では D1269 の後半は成立しない。
- **「事前宣言」は commit 時点の証明を要する。** 検証器が registry の自己整合性しか見ないなら、
  結果を見てから完成済みの registry を 1 commit で置いても通る。内容 commit 時点の blob が
  genesis のみであることと、全 ref 走査による第二 root 不在を、発行側と同じ境界で下流にも要求する。

**却下した選択肢:**

- 世代を全 event row へ複製する — 受理集合を狭めずに変更面と chain hash だけが増える。
  世代は capability digest に含めて束縛し、classification receipt には値を置かない。
- 発行側に全列挙 helper を新設する — 既存の合成検査と重複し、変異を帰属できない。
- `not-consumed` を最終消費として outer receipt へ運ぶ — 既存の report-count / status /
  report hash 契約を緩める必要がある。規律 2 により緩めない。正例から外す。
- 独立 clone / repository を跨ぐ best-of-N まで閉じる — 全世代を一元管理する一般化になり、
  D1269 が明示的に却下している。

## {{D:mutation-must-target-the-effective-gate}}. 変異は「他層が先に拒否しない位置」へ照準し直す

**決定:** 事前登録した変異が、同じ入力を前後の層に拒否される位置にあると判明したら、
その位置には登録せず**実効 gate へ再照準する**。再照準の結果として実装場所そのものを
変えることも含む。

**理由:**

- 本 wave では、当初案の「発行側の全列挙 helper」がこれに該当した。helper を空実装にしても
  既存の合成検査が先に赤を出すため、変異は赤くなるが helper の証拠にはならない。
  同じ理由で、当初のテスト案の負例 4 種 (欠落 / 余剰 / 別世代混入 / 空集合) はいずれも
  既存層で拒否され、helper を削除しても緑のままだった。
- 「検査を書いた」ことと「検査が効いている」ことは別である。後者の証拠は、
  **その述語だけを無効化したときに、その述語のためのテストだけが赤くなる**ことである。
- 再照準を怠ると、実効性のない検査を「新しい防壁」として成果物に記録することになる。

**却下した選択肢:**

- 冗長 gate と明記して登録だけ残す — 本件は「冗長」ではなく「実装位置が誤っている」型で、
  位置を直せば単一帰属になる。明記で済ませると誤った位置の実装が残る。
