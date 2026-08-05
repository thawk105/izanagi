# 段 4 裁定 — [T-244] P3 (1)(2)(3) 設計起草

wave: dev-wave-t244-p3-design / branch: `worktree-dev-wave-t244-p3-design`
起点 main: `3075a8fd`

## 裁定

**実装しない。** 段 5・6 を飛ばし `4→7→8→9` とする。実装差分が無いため、変異 matrix と
実装後の受入全走は対象外である。

本 wave の依頼は「(1)(2)(3) の**設計起草**」であり、実装は最初から scope 外である。したがって
この「実装しない」は前 wave (D163) の「試みたが不能と判明した」とは性質が異なる — **成果物は
推奨付き裁定パッケージそのもの**である。ただし段 3 の敵対 2 レンズが独立に NO-GO を返し、
**設計案をそのまま実装 wave として起票してはならない**理由を 15 件挙げた。その裁定を以下に置く。

判断材料は 4 つの独立な情報源である — 親の段 1 前提実測 (N1〜N14)、段 2 プラン (codex read-only)、
段 3 レンズ A (正しさ境界・恒真化)、段 3 レンズ B (実効性・会計・段取り)。

## 実装 wave として起票できない理由 (段 3 の合意点)

1. **DW-G04 の発火 gate を満たせない (レンズ B 所見 3、real)。** 受理側 (候補を受理し予算を消費し
   seal する) が発火する既存 production artifact path も計測 ID も書けない。authority registry は
   空 (`reflux_origin_authority_v2.json`)、production 初期化は明示禁止 (N13)。設計案が挙げた
   「現行 baseline で発火する検査」10 件のうち、正例は将来形の 1 件だけで、残りは現在系を拒否する
   検査である。**「実装後に正例を作る」は G04 の先行条件の代替にならない。**
2. **DW-G01 の生死実験が先行していない (レンズ B 所見 4、real)。** 設計案は authority schema・
   provisioning・epoch router・reservation FSM・8c 改修・report v3・sidecar を一括してから正例を
   作る順序であり、「最安の生死確認を先に」という要求に反する。
3. **1 wave で安全に閉じない (レンズ B 所見 11、real)。** 受理集合の変更が 4 面 (production 初期化・
   authority generation schema・reservation event・report v3 / completeness) 同時に発生し、
   いずれも D96 の同一変更単位を要する。
4. **予算 root の同一性が閉じない (レンズ A 所見 2、real)。** 後述 (2-b)。これは設計の穴ではなく
   **repo 内の検査だけでは原理的に閉じない**面であり、ユーザー裁定を要する。

## 所見の裁定表

区分: `採用` = 本裁定と推奨に採る / `パッケージ` = ユーザー裁定へ返す / `訂正` = 親の記述を直す。
**実装差分が無いため、全所見の成果物影響は一律に「certified 選択・材料レポート・試行台帳・
proof chain の現在値と受理集合は不変」である。**

| # | 判定 | 区分 | 要旨 |
|---|---|---|---|
| plan | real | 採用 | (1)(2)(3) の設計案は方向として妥当。ただし下記の訂正を要する |
| A-1 | real | 採用 + パッケージ | `cardinality` は member row 数であり候補数ではない。単一候補 × R を「候補 batch」と記録すると P4 consumer が候補 1 点を 2 点以上と誤認する。散文の断りでは足りず、`distinct_candidate_count` を別 field にし 1 の記録を P4 証拠として受理不能にする必要がある |
| A-2 | real | パッケージ | git-common-dir 束縛は同一 clone 内の worktree 回避しか塞がない。別 clone・pointer ごと全削除・履歴書換えで予算 root を作り直せる。外部 monotonic anchor が無い限り閉じない |
| A-3 | real | パッケージ | successor 世代が意味等価な cell を byte-different に再発行すれば使用量 0 の予算を得る。`derive_cell_key` は 4 digest だけで、duplicate cell 拒否は単一 authority blob 内に閉じている。旧 epoch の保存だけでは防げない |
| A-4 | real | 採用 | preimage 規則で捕捉 commit `H` と bytes の所有者が二義的。非自己参照 topology (authority record 自身を含まない `H`) を定義しないと自己参照 hash になる |
| A-5 | real | パッケージ | full manifest が実 execution sink まで束縛されない (既知 A-2 の未処理)。cell key の 4 digest では別 spec / 別 role bundle を同一 cell にできる |
| A-6 | real | 採用 | commit-reveal は単一候補でも seal 前に多値を漏らす。1 bit (preview / pre-audit 通過) に加え、critic payload が seal 前に連続値 metrics を受ける |
| A-7 | real | パッケージ | create-only `rep_evidence` は producer の自己申告であり物理 query の証明ではない。ledger 側で検証できない |
| A-8 | real | パッケージ | reservation / seal / sidecar の crash recovery と namespace が閉じていない |
| A-9 | real | 採用 | 「現行 baseline で発火する検査」の多くは前段で停止するか schema 不在を赤と数えており、対象条件に到達しない |
| A-10 | real | パッケージ | recipient schema validation は D164 型の恒真 tripwire になりうる |
| A-11 | real | パッケージ | 既知 A-6 (別 origin の event が global CAS で post-query commit を妨害する) が未処理 |
| A-12 | real | 記録のみ | 既存期待値の変更はあるが D96 手続は明示されている |
| B-1 | real | 採用 | 全案実装後でも埋まるのは 11 層のうち機構面 6 層まで。第 1 層 (authority 値・発行) が空で正の artifact path も無いため、**成果として閉じる層は 0** |
| B-2 | real | **訂正 (採用)** | **親の (P3)「第 1 段が予算束縛を実体化する」は撤回する。** 予算 counter が動くのは `BatchCommitted` 受理時だけで、それを呼ぶ production caller は無い。単一候補 × R は「同じ wire を複数 commitment にできる」だけである |
| B-3 | real | 採用 | 上記「起票できない理由 1」 |
| B-4 | real | 採用 | 上記「起票できない理由 2」。E 段 loop の既存 CLI を使う最安の生死実験手順を具体的に提示した |
| B-5 | real | 採用 | 8c 結線で得られるのは pilot 配線証拠だけ |
| B-6 | real | パッケージ | linux-baremetal 再測定の可否が repo から判断できず、authority bootstrap が測定タスク待ちになる |
| B-7 | real | 訂正 | N6 の誤り (下記) |
| B-8 | real | パッケージ | reservation 後の crash recovery が未設計 (A-8 と同旨) |
| B-9 | 疑い | パッケージ | epoch router と全 origin CAS の並行性契約が無い |
| B-10 | real | 採用 | sidecar は cross-reference であって proof chain ではない。名乗りを限定する |
| B-11 | real | 採用 | 上記「起票できない理由 3」 |
| B-12 | real | 訂正 | 設計案の成果物影響欄の一部が実効を過大申告している |
| B-13 | real | **訂正 (採用)** | **親の (P2)「既存型を適用し新機構を発明しない」は言い過ぎ。** s8b の構造は参考にできるが、origin 固有の作り直し (epoch route・世代跨ぎ cell 一意性・累積予算) が要る |

## 親の記述の訂正 (段 1 brief に対して)

- **N6 を訂正する (erratum)。** 親は「既存 3 / 部品あり 1 / 規則なし 5 / authority 値 4」と分類したが、
  正しくは **「既存 2 / 部品あり 2 / 規則なし 5 / authority 値 4」**である。`ccbench_commit_oid` は
  manifest が full 40-hex を要求する (`reflux_origin_ledger.py:81` の `_OID_RE`) のに対し
  `pin.CURRENT_PIN` は 7 文字 prefix (`pin.py:28`) であり、**そのまま preimage にできない**。
  親が実コードで裏取りした (段 2 と両レンズが独立に同じ訂正を出した)。
  なお `candidate_ir.schema_ref` は「値規則あり・内容参照なし」として細分するのが正確である。
- **(P3) を撤回する (B-2)。** 「第 1 段 (単一候補 × R replicate) が予算束縛を実体化する」は誤り。
  実体化するのは production caller が `BatchCommitted` を出したときだけであり、それは本設計を
  実装して初めて成立する。N3 が示したのは「ledger の受理規則上そういう batch が作れる」ことに
  留まる。さらに A-1 により、作れたとしても**「候補 batch を作った」とは記録できない**。
- **(P2) の表現を訂正する (B-13)。** 「既存型を適用し新機構を発明しない」は言い過ぎで、
  s8b から流用できるのは record 構造・承認連鎖・tombstone・transition allowlist の型までである。
  epoch route、世代跨ぎの cell 一意性、累積予算は origin ledger 固有に作る必要がある。
- **(P1) の射程を狭める (A-2)。** git-common-dir 束縛の維持は**同一 clone 内の worktree 回避**しか
  塞がない。「予算が新品にならない」と一般化してはならない。
- **(P6) を補強する (B-6 / 段 2)。** clocks の hardcode 修正だけでは足りない。現 artifact は
  short pin を保持し、登録済み `numactl` を run command に付けず、現 producer が出す
  `build_admissions` を持たず、**workload cell が 8c の ycsb-a/b/c と別 cell**である。
- **(P7) の「durable」を限定する (A-8 / B-10)。** producer 側 artifact に置く層選択は妥当だが、
  crash recovery と namespace を閉じるまで durable とは言えず、「proof chain」とも名乗れない。

## 本 wave が確定したこと (裁定として固定する)

- **D163 決定 2 は現 main (v2) でも成立する** (N2、親が実行して確認)。ただし理由はより強い —
  production 初期化は欠落ではなく `_initialize_locked` 冒頭の**明示的な禁止**である (N13)。
  したがって解消は入口追加では足りず、**禁止の条件付き解除という受理集合の変更**を伴う。
- **最初の genesis が origin 集合を永久に固定する** (N14)。origin を後から足す event 型が無く、
  authority blob の 1 byte 変更で runtime 全体が読めなくなる。**bootstrap と世代移行は不可分**である。
- **D163 の「runtime を消せば新品になる」は現 v2 production には当たらない** (段 2 の指摘、親が確認)。
  現在は消すと単に起動不能になる。「削除後に新品」は fixture 経路と、**将来 provisioning を素朴な
  `absent ⇒ genesis` にした場合**の危険である。この区別は (2-a) の設計要件になる。
- **N3 は真だが意味は限定される。** 同一 wire の R 行で合法 batch は作れるが、それは
  「ledger transaction batch」であって「候補 batch」ではない (A-1)。かつ sealed member row 数は
  物理 query 数の証明ではない (D166 決定 5 が既に固定)。

## 名乗りの上限 (本 wave)

本 wave が名乗ってよいのは **「[T-244] P3 の (1)(2)(3) について、推奨付きの設計裁定パッケージを
起草した」**までである。名乗ってはならない — P3 充足・部分実装、P4 / 軸 (iii)、P7、
producer 結線、予算束縛の実現、cap 引上げ、certified 選択の前進。
**P3 は依然 FAIL、`MAX_APPROVED_GENERATIONS = 1` と D114 の cap も不変**である。

## 裁定パッケージ

正本は同ディレクトリの `README.md`。
