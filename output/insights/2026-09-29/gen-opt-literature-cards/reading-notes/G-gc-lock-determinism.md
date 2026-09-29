# G-gc-lock-determinism 読みメモ (2026-09-29)

指示めいた文字列: なし (取得した 3 本の PDF 本文を grep と通読で確認)。

## 取得状況の一覧

| # | 論文 | 状態 |
|---|---|---|
| 1 | One-shot GC (OneShotGC)、SIGMOD 2023 / PACMMOD 1(1) | **本文は取得できなかった** |
| 2 | Diva、SIGMOD 2022 | **本文は取得できなかった** |
| 3 | Aria、PVLDB 13(11) | 取得・読了 |
| 4 | VLL、PVLDB 6(2) | 取得・読了 |
| 5 | The Case for Determinism、PVLDB 3(1) | 取得・読了 |

### 1. OneShotGC (未取得)
- 書誌 (OpenAlex と Semantic Scholar で確認): Aunn Raza, Periklis Chrysogelos, Angelos-Christos G. Anadiotis, Anastasia Ailamaki。Proceedings of the ACM on Management of Data, 2023。DOI 10.1145/3588699。
- OA は hybrid (CC-BY と表示) だが、`https://dl.acm.org/doi/pdf/10.1145/3588699` は curl では bot 判定 HTML (5,491 bytes)、WebFetch では HTTP 403。EPFL Infoscience (record/305174) も人間確認ページ。arXiv に同題は無い (arXiv API で検索)。
- 検索の要約に「OneShotGC は版の走査なしに GC する多版 storage 設計」とあるが、本文を読んでいないのでカードは作らない。

### 2. Diva (未取得)
- 書誌 (Semantic Scholar・OpenAlex で確認): Jongbin Kim, Jaeseon Yu, Jaechan Ahn, Sooyong Kang, Hyungsoo Jung。SIGMOD '22。DOI 10.1145/3514221.3526135。
- OA は closed (OpenAlex: `is_oa=false`、Semantic Scholar: CLOSED)。ACM DL は 403 の見込みで、墨天轮の複製は権限不足で 404。
- 検索要約に「版 index と版 data を分離し、provisional version indexing と時間区間ベースの GC を行う」とあるが、本文未読のためカードは作らない。

### 3. Aria
- 取得元: `https://vldb.org/pvldb/vol13/p2047-lu.pdf` (`www.vldb.org` は接続リセット。`vldb.org` で成功)。取得時刻: 2026-09-29 10:07 JST 頃 (ファイル mtime)。
- SHA-256: `48644eaf273f001fec91cc056f9fef98a7362d22510390e97c4c38c39d2365d6`。保存先: `src/aria.pdf`、`src/aria.txt`。
- 読んだ節: Abstract、§1-2 背景、§3、§4、§5、§6、§7.1、§8.1-8.5 と Fig. 9-12。
- 読んでいない節: §7.2 以降の分散・fault tolerance、§8.6-8.7、関連研究以降。
- 最適化 (JSONL に 3 件):
  - `aria-batch-reservation` (protocol-core): batch 実行と write 予約 (最小 TID)。read/write set の事前宣言は不要、ただし batch と barrier が前提。
  - `aria-deterministic-reordering` (optimization): Rule 2 で RAW を WAR に変換。YCSB skew 0.999 で 3.0x (Fig. 11、本文 §8.4)。
  - `aria-fallback-strategy` (optimization): abort 率で切替える Calvin 型 lock の再実行。事前宣言は不要 (commit phase 後の set を使う)。
- JSONL に入れなかった候補:
  - read 予約を省く「WAR は既定で見ない」既定動作: batch-reservation の一部 (Rule 1 の議論) のため独立させない。
  - 実行フェーズで予約失敗時に commit phase を飛ばす最適化 (§4.1): 名前付きの独立節が無い小さな最適化。

### 4. VLL
- 取得元: `https://www.vldb.org/pvldb/vol6/p145-ren.pdf`。取得時刻: 2026-09-29 10:07 JST 頃 (mtime)。
- SHA-256: `13121c0106129e6faed1c79434659dbad6cd5b679dc3ef9b9e7679fb02d822c6`。保存先: `src/vll.pdf`、`src/vll.txt`。
- 読んだ節: Abstract、§2.1-2.5、§3 冒頭、§3.1 (Fig. 4-5 の本文)。
- 読んでいない節: §3.2 分散実験、§3.3 CPU 費用、§4 関連研究、§5。Fig. 4-5 の軸の数値は本文の記述だけを引いた。
- 最適化 (JSONL に 2 件): `vll-core` (protocol-core、事前宣言の read/write set が前提)、`vll-sca` (optimization、bit 配列 DX/DS で衝突判定)。
- JSONL に入れなかった候補:
  - TxnQueue の blocked 数の上限 (§2.1): 調整パラメータ。名前付きの独立技法ではない。
  - 単一 thread 版 VLL と "waiting" 状態 (§2.2): 分散・H-Store 型向けの変種。
  - SCA 内の hash 結果の cache (§2.5): 「minor optimization」と本文が呼ぶ。SCA に含めた。
  - 事前の exploratory read (§2.3): 事前宣言の充足手段として `vll-core` の prerequisites に記載。

### 5. The Case for Determinism in Database Systems
- 取得元: `https://www.cs.umd.edu/~abadi/papers/determinism-vldb10.pdf` (著者頁)。`vldb.org` の `pvldb/vldb2010/papers/R06.pdf` は取得できず (HTML 36 KB、PDF でない)。取得時刻: 2026-09-29 10:07 JST 頃 (mtime)。
- SHA-256: `22f513193b4a2db11b22faaeac3bf8ecec232b2e5b32b401915713315ad5a8fb`。保存先: `src/determinism.pdf`、`src/determinism.txt`。
- 読んだ節: Abstract、§1.3、§2、§3 前半、§4.1、§4.2、§5。
- 読んでいない節: §3 の解析モデルと図 (clogging 実験) の詳細、§6 以降、付録。
- 最適化 (JSONL に 2 件): `det-ordered-locking` (protocol-core、全 lock 要求の事前把握が前提)、`det-dependent-txn-decomposition` (optimization)。
- JSONL に入れなかった候補:
  - 二次 index 探索の read committed 向けの緩和 (§4.2): decomposition の一部として記載した。
  - preprocessor で非決定論的な呼び出し (random、time) を先に解決 (§4.1): 設計上の前提であり性能の最適化ではない。

## 事前宣言・batch の要否の一覧 (`requires_predeclared_sets`)

| card_id | 値 | 根拠 |
|---|---|---|
| aria-batch-reservation | false | 実行後に write set が判明 (§1 の主張、§4.1)。ただし batch 単位と barrier が必要 |
| aria-deterministic-reordering | false | 同上 |
| aria-fallback-strategy | false | commit phase 後の判明済み set を使う (§6) |
| vll-core | true | 全 lock を critical section で一括要求 (§2.1、§2.3) |
| vll-sca | true | 各 txn の read/write set の hash を使う (§2.5) |
| det-ordered-locking | true | 到着時に全 lock を要求 (§2) |
| det-dependent-txn-decomposition | true | 探索 txn で set を確定してから本体を実行 (§4.2) |

## 補足 (注意点)
- 効果の分類 (`effect_category`) は、Aria の 3 件と Determinism の 2 件で「推測」を明記した。3 分類に素直に入らないのは、abort 再試行や決定論の獲得が主目的の技法である。
- 性能の数値は、Fig. 9-12 (Aria) と Fig. 4-5 (VLL) の本文に書かれた値だけを引用した。図の値を読み取った数値は書いていない。
- Aria の Fig. 9 のスループット比 (1.6x、1.4x、2.4x) は §8.2 の本文の総括文による。
