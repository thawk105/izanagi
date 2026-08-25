---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1434-price-version-binding
seq: 2
---

## {{D:frozen-price-binding-trust-root}}. price version の信頼の起点はコード側の凍結 literal に置き、schedule の自己申告を authority にしない

**決定:** schedule slot の非 null `price_version` を受理する条件を、次の 1 形だけにする。
信頼の起点 (trust root) は **review 済み commit の中の凍結 literal** — snapshot の path、
その bytes の SHA-256、`price_table_version`、repo 内抜粋の path と SHA-256 — であり、
schedule が宣言する値ではない。

1. `schema_version` が `int` 型の 3 であること (値が等しいだけの `3.0` は受理しない)。
2. schedule 直下の `price_snapshot` が `{"path", "sha256"}` **ちょうど**の object で、
   凍結 literal と完全一致すること。余剰 key・欠落 key・非 object を拒否する。
3. その path の実 bytes を読み、SHA-256 が凍結値と一致すること。
4. 読んだ bytes を `tools/t189_price_snapshot.py` の `validate_price_snapshot` が受理し、
   `price_table_version` が凍結値と一致すること。
5. snapshot が指す抜粋 (repo 内) の path・SHA-256・byte 長が一致すること。実 bytes まで読む。
6. schedule の全 slot の `price_version` が一様であること。集合は `{null}` か
   `{凍結 version}` のどちらかだけを許し、混在を拒否する。

`cache_condition` の受理集合は変えない。非 null を従来どおりすべて拒否する。

**理由:**
- schedule が snapshot の path と SHA を宣言できるだけでは、schedule を書く側が snapshot も
  差し替えられる。それは「自分で書いた値を自分で照合する」自己追認であって認証にならない。
  敵対相談が指摘し、親が独立 probe で「呼び手が別の値を期待値だと自称しても通らない」ことを
  実測して確認した。
- 検証器 `validate_price_snapshot` は closed schema と byte 範囲の算術は検査するが、
  **repo 内抜粋の実体を開かない**。したがって抜粋の実 bytes 照合を別に足さなければ、
  抜粋の差し替えが通る。
- 全 slot 一様性は事前登録 §10 が明文で要求していたが実装に存在せず、全 slot が null なので
  恒真に成立していただけだった。非 null を受理可能にすると「謳うだけで発火しない保証」へ変わる。
  受理集合を広げるなら同じ commit で塞がなければならない。
- repo 外に保存した取得時の生データは gate の必須入力にしない。装置が証明できるのは
  「review 済みのローカル snapshot と抜粋を用いたこと」までであり、公表原表そのものの
  真正性ではない。この限界は文書へ明記する。

**却下した選択肢:**
- 非 null なら通す / 正規表現に合えば通す — 受理条件を緩める変更であり絶対規律 2 に反する。
- schedule が宣言した path と SHA だけで束縛する — 上記の自己追認になる。
- repo 外の生データを gate の必須入力にする — 実験装置が repo 外の可搬でない path に依存し、
  粗い provenance で足りるという既定方針にも反する。

## {{D:bind-path-only-hardening}}. 新しい受理形の中でだけ検査を強くする経路を使い、共通経路は触らない

**決定:** 既存の受理集合 `A0` に属さない**新しい受理形の中でだけ**発火する検査は、
`A0` を縮める危険なしにいくらでも強くしてよい。逆に、その穴が共通経路にもあるからといって
共通経路の検査を強くしてはならない。実装では新規検査を「束縛が発行されたときだけ」を表す
条件の内側に置き、それが実際に条件付きであることを親が確認する。

**理由:**
- 本件では非 null の `price_version` が変更前は必ず拒否されていた。したがって
  **`A0` には束縛済み schedule が 1 つも存在しない。** 束縛経路の中で課す要求は、
  定義上いかなる既存要素も落とさない。
- 同じ穴 (Python の数値型混同) は共通経路にもあった。共通経路を直すと、`block_order` が
  `true` や `2.0` である**全 slot が null の既存 schedule が新たに拒否され `A0` が縮む**。
  受理集合の縮小は拡大と同じく承認を要する変更であり、副作用として起こしてはならない。
- この非対称性を先に言語化したことで、同型の穴を 1 巡でまとめて閉じられた。
  穴を 1 つずつ追いかけると、レビューの巡回上限に当たるまでもぐら叩きが続く。

**却下した選択肢:**
- 共通経路をまとめて直す — `A0` が縮む。縮小が妥当だとしても、それは別の裁定である。
- 見つかった穴だけを 1 件ずつ直す — 同型が残り、次の巡回で同じ議論を繰り返す。
- 型混同を repo 全体の lint で塞ぐ — 制度一般化には異なる producer / consumer での
  独立 2 例が要る。本件は同じ consumer 内の 3 箇所であり、条件を満たさない。
