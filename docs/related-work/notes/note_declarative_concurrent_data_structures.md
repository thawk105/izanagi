# 調査ノート: Declarative Concurrent Data Structures

- **論文**: Declarative Concurrent Data Structures (DCDS / 試作系 Rösti)
  - venue/year: arXiv preprint 2024、`cs.DB` (cross-list `cs.DS`, `cs.PL`)、v1 (2024-04-20)、
    License: arXiv.org perpetual non-exclusive license
  - authors: Aunn Raza, Hamish Nicholson, Ioanna Tsakalidou, Anna Herlihy, Prathamesh Tagore,
    Anastasia Ailamaki (いずれも EPFL, Lausanne, Switzerland。第 1・第 2 著者は等貢献)
  - arXiv: 2404.13359 / https://arxiv.org/abs/2404.13359
  - 本文取得元: https://arxiv.org/html/2404.13359v1 (HTML v1、2026-08-27 取得、80,867 文字に整形、
    SHA-256 `2c2ff59178a083fd38f0295a5852635a1c860df6f968ef55941acd38a7216e68`)
  - 本文中の会議情報は `Conference: ; ;` の雛形のままで、投稿先は特定できない
- **このノートを書いた理由**: `docs/related-work/claim-survey/2026-08-26-inventory.md` の
  軸 1 分類 pilot が、監査前の 1 行要約からは包含条件 A を決められず `要裁定` に残した 1 件だから。
  同 pilot は「`literature-map/` の柱 1 にあるが、逆引き索引にも 7.1 本文にも現れず、
  採録を却下したのか未処理なのかを示す記録が見つからない」とも記録している。
- **信頼境界**: 本文は絶対規律 6 でいう「データ」である。読解にあたり誘導記述の有無を機械走査した
  (結果は末尾「規律 6 の走査」)。
- **引用の作法**: 以下で `>` と引用符を使った英文は arXiv HTML v1 の本文からの逐語である。
  ただし **HTML 整形由来の空白と数式マークアップだけは正規化した。語列は変えていない。**

---

## 一言要約

**逐次仕様だけを書かせ、コンパイラが並行性制御を注入して thread-safe なデータ構造を機械語まで
生成する**、という枠組みの提案。宣言が「このデータ構造に対して他の操作は来ない」を保証するので、
汎用 DBMS には削れない同期を削れる。試作系 Rösti は S2PL + NO_WAIT を注入し、
in-memory OLTP DBMS (Proteus) に対して YCSB で最大 2 倍のスループットを出す。

**LLM も学習も進化探索も一切使わない。** 自動化はコンパイラ最適化である。

---

## 対象の確定 (包含条件 A の根拠)

**結論: この論文の主題領域はトランザクションの並行性制御を含む。A は ✓ である。**

判定の全根拠と、採らなかった反対の読みは
`docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md` の §2 にある。
ここでは要点だけを置く。

- 注入するのはトランザクションの CC である。

  > "Currently, Rösti injects strict two-phase locking (S2PL) ( Bernstein et al., 1987 ) CC with
  > NO_WAIT deadlock avoidance protocol."

- 実行時にトランザクションマネージャがあり、`begin_txn` / `end_txn` / commit / abort / rollback を持つ。
- 評価単位は毎秒トランザクション数 (MTPS) で、比較対象は in-memory OLTP DBMS である。
- **勝因を論文自身が並行性制御の特化に帰属させている。**

  > "In summary, Rösti outperforms in-memory DBMS due to the simple fact that it specializes
  > concurrency control to the target workload, avoiding unnecessary synchronization which a DBMS
  > couldn't, and reduces the total amount of work given the specialized generated data structure."

**反対の読み** — 論文が自分で述べる目的はデータ構造の生成である
("a framework for the automatic generation of concurrent data structures from a serial
specification")。成果物の種類で A を判定するなら A✗ / B✓ / `部分接地` になる。
採らなかった理由は上記裁定記録の §2.2 に書いた。

---

## 手法の核

### 枠組み (DCDS)

frontend DSL → DCDS-IR → 論理最適化 → **CC 注入** → 物理最適化 → コード生成。

**枠組みは CC アルゴリズムを規定しない。**

> "The specific CC algorithm used is not prescribed by the framework and is a choice left to the
> implementation of the framework."

**最適化は正しさに必要ではない。**

> "The Logical Optimizer and Physical Optimizer only improve the performance of the resulting CDS;
> they are not necessary for correctness."

### 論理最適化 (同期を削る本体)

宣言が全操作を閉じることを使って、汎用 DBMS には不可能な削除を行う。

> "Further, in contrast to DBMS, Rösti has complete knowledge of the workload and by construction,
> ensures that no other operation will be performed on the declared data structure."

4 つのパス: 合成型の未使用関数の削除 / 未使用属性の削除 / 読み取り専用属性の定数化 /
**書き込み専用属性の削除**。最後のものは「観測可能な副作用の無い write-write 衝突の同期」を
丸ごと消す。DBMS は将来の未知ワークロードを排除できないので同じことができない。

### CC 注入

関数をトランザクションのスコープと見なし、各文が触れる属性へ shared / exclusive の施錠文を
挿入する。既に取得済みなら挿入せず、shared の後に exclusive を要求されたら昇格する。
S2PL に従い解放は関数末尾 (return 経路の直前) へ置く。

**nascent 最適化:** 合成型のメソッド呼び出しでは、対象が「このスコープ内で作られ、
まだ共有位置へ書かれていない」なら施錠を挿さない。連結リストの push で新ノードが
head になるまで施錠不要、という例が挙がっている。

`const` 関数かどうかは注釈ではなく IR 構築時に推論する。

### 物理最適化は将来課題 — そこに izanagi の軸がある

> "The physical optimizer will operate on concurrent IR and optimize the injected CC operations;
> For example, by lock grouping across attributes and reordering lock acquisition statements to
> reduce the runtime cost of aborts."

**施錠取得順序の並べ替えで abort コストを下げる、というのは izanagi の sort-strategy 軸そのものである。
DCDS では未実装の将来課題である。**

---

## 実験

- ハードウェア: 2 ソケット、物理 12 コア + hyper-thread の構成で 1〜48 worker まで振る。
- ワークロード: YCSB 風。レコード数は `1M * num_workers`。読み書き比と分布 (一様 / Zipfian) を振る。
- 比較対象: (1) 既存 C++ ライブラリ実装、(2) in-memory OLTP DBMS の Proteus
  (MV2PL + snapshot isolation、cuckoo hashing の主索引)。
- 結果: map と list を合成した recency-sorted container で最大 2 倍のスケーラビリティ改善。
  in-process OLTP としても Proteus に対して最大 2 倍。
  両系とも 4 スレッド付近でマイクロアーキ資源が飽和する。

**直列化可能性の検査は行っていない。** 論文が定義する correctness は
「データ競合・ライブロック/デッドロックが無く、衝突する並行操作が不整合な結果を出さない」である。

---

## izanagi との関係

### 借りるもの

- **「汎用 CC はワークロード特化に負ける」を、AI を使わずに測った外部証拠。**
  izanagi の前提 (ワークロード特化 CC に価値がある) を、別の手段で独立に支持している。
  2 倍という数字は同一機・同一ベンチでの対測定である。
- **宣言が閉じているほど同期を削れる、という機序。** izanagi の workload descriptor が
  何を閉じれば何を削れるのかを考えるときの参照点になる。

### 借りないもの

- **DSL による宣言そのもの。** izanagi は CCBench の C++ 実装を素材にするので、
  「ユーザーが逐次仕様を書く」経路は取らない。
- **正しさを構成に置く設計。** DCDS は CC 注入が正しいことを前提に、検証器をループに置かない。
  izanagi は絶対規律 2・3 により verifier を毎反復回す。**ここは明確に別の立場である。**

### 主張との距離 (軸 1)

**最も近い外部候補である。** 対象が同じ (トランザクションの CC)、目的が同じ
(ワークロード特化で汎用実装に勝つ)、出力がコードである。

**違いは 3 つで、どれも §3 の 1 の限定語に対応する。**

1. **LLM も進化探索も無い。** 自動化はコンパイラのパスである。
2. **CC プロトコル空間を拡張しない。** Rösti が注入するのは S2PL + NO_WAIT の 1 種だけで、
   走行中に別のプロトコルを合成する経路が無い。
3. **正しさ検証器をループ内に持たない。**

**将来課題として名指しされているのは「既知アルゴリズムの実行時適応的な選択」であって、
新しい CC の合成ではない。**

> "The most appropriate concurrency control algorithm depends on workload, such as optimistic CC
> for low-contention while pessimistic for high-contention workloads ... The DCDS framework will
> enable dynamic tracing of workload at runtime and then adapt the optimizations and CC mechanism
> accordingly."

---

## 規律 6 の走査

整形本文 80,867 文字の全体 (節・表・参考文献を含み、先頭切り出しなし) に対して、
`ignore (all )?(previous|prior|above)` / `disregard` / `system.?prompt` /
`you are an? (ai|assistant|language model)` / `as an ai` / `new instruction` / `override` /
`do not follow` / `instead,? (please )?(output|write|say)` / `jailbreak` / `prompt.?inject`
を大文字小文字を無視して走査した。**hit は 0 件である。**

末尾に arXiv の site UI 由来の文字列 (`Report Issue`、`Have a free development cycle?` 等) を含むが、
本文ではなく HTML の chrome であり、従っていない。

**走査語は有限である。** この走査は「誘導記述が無い」ことの証明ではない。

### 語の全件走査 (母集合を併記した内部の不在)

同じ母集合に対する小文字一致の件数:
`concurrency control` 28 / `transaction` 79 / `abort` 7 / `workload` 24 / `oltp` 7 / `2pl` 3 /
`two-phase` 2 / `isolation` 2 / `snapshot isolation` 1 / `throughput` 3 / `verif` 1 /
`serializab` 0 / `mvcc` 0 / `linearizab` 0 / `model check` 0 / `tpc` 0 / `many-core` 0 /
`latency` 0 / `machine learning` 0 / `neural` 0。

`llm` の 1 件は参考文献の著者名 `Aaron Ballman` の一部である。

**この不在は、この 1 論文の中の不在である。世界の不在ではない。**

---

## 引用/リンク

- abs: https://arxiv.org/abs/2404.13359
- HTML v1: https://arxiv.org/html/2404.13359v1
- 判定の全根拠: `docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md`
- 分類 pilot の起点: `docs/related-work/claim-survey/2026-08-26-inventory.md`
- 検索契約: `docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md`
