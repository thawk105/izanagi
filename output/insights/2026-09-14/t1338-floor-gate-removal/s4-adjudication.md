# 段 4 裁定 — dev-wave [T-434] [T-1709] [T-1338]

基準 main `f5423e2fff3adb164731963ca33e82ed08d08c4d` (wave 中 0 commit 前進)。
段 2 プラン + 段 3 レンズ A / B。**親はすべての所見を現物で照合した。**
裁定 inbox 再走査: D1433 / D1434 以降に二段束縛・受入関門・8c 条件 2 を扱う新裁定は無い。

## 裁定 0 — 親 brief の C のアンカーが誤りだった (最重要)

親 brief は D501 決定 8 の「driver の測定 binary bytes 照合」を
`floor_pair_driver.py:1091 _validate_build_receipt` に同定した。**これは誤りである。**
レンズ A が指摘し、親が現物で確かめた。

- `floor_pair_driver` は **B-4 床値の測定側** driver であり、その receipt 検査は
  「spec が指定する binary と build receipt の対応」を見る。過去 campaign 由来であることを
  要求していない。導入裁定も D501 より後の D1453 (`docs/decisions.md:45757`)。
- D501 決定 8 が描いた性質に一致する現経路は **oracle 側**にある。
  1. `s8b_oracle_driver.py:1049-1066` — 過去床値 campaign の admission receipt から
     `binary_sha256` を取り出し `perf_sha_by_cell` を作る。
  2. 同 `:1778-1782` — それを `expected_perf_sha256` として `pipeline.evaluate` へ渡す。
  3. `pipeline.py:2091-2100` — **今回 build した perf binary の sha256 と照合し、
     不一致なら trace/bench を 1 度も起動せず abort する。**

つまり「今回測る binary が過去 campaign の binary と同じか」を要求しているのは、この供給経路である。
**C の編集面は `s8b_oracle_driver.py` であり、`floor_pair_driver.py` は本 wave で触らない。**

副次的に、レンズ A の must-fix 2 (「C 全撤去は `sort_best` の SWO PASS receipt 検査まで落とす」) は
アンカー訂正により不要になった。`floor_pair_driver` を触らないので、その依存は保たれる。

## 裁定 1 — 撤去の条件を「完全代替の存在」から外す

親 brief の不変条件 5 は「supersede する既存述語を正例で示せない述語は撤去しない」と書いた。
**この条件は撤去できる述語をゼロにするため、裁定 1 で外す。** レンズ A が正しい。

D501 決定 8 の逐語は「manifest の per-pair 対表 exact 検査は freeze の floor 節の**内部整合だけ**を
見ており」「**いずれの撤去も受理集合を広げる**」である。同決定は完全代替を主張していない。
**撤去の授権は「D496 の下で不要になったこと」であって「別述語が同じ入力を拒否すること」ではない。**

したがって新しい条件は次とする。

- 撤去してよいのは **D501 決定 8 が名指した 3 述語だけ**。射程外へ 1 行も広げない。
- 代替の有無は**記録するが、撤去の条件にしない**。
- **受理集合がどう広がるかを完了報告と insight に明記する。**「受理集合を維持した」と書かない。

## 裁定 2 — real と認めた所見 (実装に効く)

| # | 所見 | 出所 | 判定 |
|---|---|---|---|
| R1 | `M:1053` は caller の `freeze_sha256` と manifest 記録値の比較であり、freeze を再 hash しない。A/B の完全代替ではない | 段 2 / レンズ A / レンズ B | **real**。親 brief の supersede 主張が誤り。親も `:1049-1055` のコメントで確認 |
| R2 | `M:1078` は `holdouts[h].variant_binding.entries` を読み `floor.by_holdout[h].pairs` を読まない。A の pairs key 検査は代替なし | 段 2 / レンズ B | **real**。撤去はするが、代替ありとは書かない |
| R3 | A 撤去後も対象検査を通らず成功する正例が 3 件 (`TM:935`, `:946`, `:967`) | レンズ B | **real**。撤去対象の正例なので、A と同じ単位で退役させる |
| R4 | `TM:324` は builder の生成結果を test 自身で数えており `validate_schedule` を呼ばない。代替発火の証拠に使えない | レンズ B | **real**。変異事前登録の照準から外した |
| R5 | `M:1198 build_approved_manifest` は `launch_validate` / `reverify_published_freeze` を呼ばない公式 candidate 入口。上流再計算の代替が届かない | レンズ B | **real**。受理拡大の射程として明記する |
| R6 | B(a) は単純な受理拡大ではなく**文書形の変更**。旧 key 付き文書は `M:1043` で拒否される | 段 2 / レンズ A | **real**。互換層は足さない (scope 外) |
| R7 | `s8b_verdict` の条件 3 と scale gate は schema v3 で既に判定基盤から撤去済み (`s8b_verdict.py:69`) | レンズ A | **real**。親 brief の不変条件 2 の前提が古い。完了報告で「旧三条件を維持した」と書かない |
| R8 | §10 の仕様発効から測定認可は導けない (`docs/phase3-8b-descriptor-design.md:547-553`, D510 決定 7) | レンズ A | **real**。親 brief 冒頭の理由付けの飛躍。本 wave の授権は D501 決定 8 + 本日のユーザー裁定であって §10 発効ではない |
| R9 | `p3_b4_floor_artifact_issuer.py:760-762` の行番号参照が現物とずれている | 段 2 / レンズ B | **real だが scope 外**。`floor_pair_driver` を触らないので本 wave の編集面に入らない。裁定パッケージへ |
| R10 | `M:47-49` の説明が A 撤去後に古くなる | レンズ B | **real・nit**。単位 1 の所有で同時に直す |

## 裁定 3 — refuted / 訂正

- **refuted: 8c 冒頭追記で protected hash が動く。** レンズ A・B が独立に、実 parser で
  メモリ上比較し、前後とも `1e325f9d9ce483b14d02e2c857f785007afa45005112127312b409d77cfee684` で
  不変だった。段 2 も同値を出した。**3 者一致。** 親は実装後に現物で再確認する。
- **refuted: D1433 / D1434 が [T-434] の部分実装を可能にした。** D1433 は単一導入 commit と
  先行順序を維持し、D1434 が閉じたのは所有の問いだけ。`reflux_formal_consumer.py:1479-1491` は
  正常な前段検査後に無条件で `P6Unavailable` を返す。**親の (P1) は維持。**
- **refuted: 現計画の編集で generator identity が動く。** `M:65-73` の 5 file に編集対象は無い。
- **refuted: A/B 自体が variant の anomaly 判定を緩める。** A/B が読むのは floor/budget の形・値・hash。
  correctness-red の失格と PASS 要求は `s8b_oracle_judge.py:281-296` に残る。**絶対規律 2 に触れない。**
- **refuted: 共有 fixture のため所有分割が必ず衝突する。** 正例値は変更不要で、分割は素集合にできる。
- **訂正 (親 brief):** 実アンカー表の C 行と、不変条件 5、研究前進の理由付けを裁定 0・1・R8 で差し替える。

## 裁定 4 — プラン v2 (実装する差分)

**単位 1 — `orchestrator/campaign/s8b_oracle_manifest.py` ほか**

- A 撤去: `_validate_holdout_floor` (`M:609-670`) と呼出し (`M:687-688`)、A 専用 helper
  (`M:568-574`) を削除する。`_holdout_configuration_ids` (`M:577-606`) は `M:1078` が使うので残す。
- B(a) 撤去: `floor_budget_snapshot_sha256` を key 集合 (`M:58`)、生成 (`M:807-809`)、
  照合 (`M:1093-1096`) の 3 箇所から一体で削除する。
- 残す: `M:674-686` (floor/budget null)、`M:689-703` (holdout 集合・budget 値・共有性)、
  `M:1070-1084` (schedule holdout / cell product)、`M:1053` (freeze byte hash)。
- `M:47-49` の説明を実態へ合わせる (R10)。
- `s8b_verdict.py:846-847`: `_validate_execution_snapshot` の呼出しは**消さない**。残る floor/budget
  検査があるため。コメントだけ実態へ合わせる。
- テスト: `TM:957,977,986,994,1003,1011,1020,1037` の 8 負例と `TM:935,946,967` の 3 正例を
  A と同じ単位で退役させる。B(a) について、**撤去した key を持つ文書が `M:1043` で拒否される
  負例を 1 本足す** (これは新設 gate ではなく、既存 exact key 検査の実効を固定する正例・負例)。

**単位 2 — `orchestrator/campaign/s8b_oracle_driver.py`**

- C 撤去: `:1778-1782` の `expected_perf_sha256=plan.perf_sha_by_cell[...]` の供給を削除し、
  `perf_sha_by_cell` の dict と `_V2Plan` の同 field を削除する。
- **残す:** `:1049-1047` 付近の admission receipt 検査 (構造・policy・pin) と、
  store 実体の sha256 が receipt と一致することの検査 (`store-missing` / `store-hash-mismatch`)。
  これは floor store の内部整合であって「今回測る binary が過去と同じか」ではない。
  **D501 決定 8 の射程外なので撤去しない。** store 検査は `perf_sha_by_cell` を作らない形へ残す。
- `pipeline.py` は**触らない**。`expected_perf_sha256` は generic な optional 引数であり、
  D501 決定 8 は名指していない。本 wave 後、この gate の production 供給元はゼロになる —
  これは完了報告に書く事実であって、本 wave で直す欠陥ではない。
- テスト: `test_s8b_oracle_driver.py:5493-5512` (伝搬の正例) と `:6296-6301`
  (`bench-binary-mismatch` の第二防壁) は撤去対象の正例なので退役させる。
  `:5601` と `:6233` の `store-hash-mismatch` は**残す**。

**親 (docs)**

- `docs/phase3-8c-preregistration.md:17` (`## 0.` の直前) へ条件 2 未解決の明記を挿入する。
  条件契約の bytes を動かさない。挿入後に実 parser で protected hash 不変を確認する。
- decisions 1 本 (撤去の採用理由・受理拡大の射程・アンカー訂正)。
- worklog fragment、insight。

## 裁定 5 — 変異事前登録 (実装前に登録。DW-M01)

撤去 wave なので、**残す述語が本当に発火するか**へ照準する。各変異は赤理由が 1 つに絞れることを
実装後に確認する。絞れなければ登録を取り消し、実効 gate へ再照準する (F28)。

| # | 位置 | 変異 | kill 期待 |
|---|---|---|---|
| MU1 | `M:1053` | freeze byte hash 比較を恒真化 | `TM:797 test_verify_detects_freeze_byte_tampering` |
| MU2 | `M:1072-1074` | schedule holdout 集合比較を恒真化 | `TM:450 test_missing_holdout_build_stays_accepted_but_verify_rejects` |
| MU3 | `M:1080` | cell product 比較を恒真化 | `TM:413 test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects` |
| MU4 | `M:1043` | top-level key 集合の exact 比較を部分集合比較へ緩和 | 単位 1 が足す「撤去 key 付き文書の拒否」負例 |
| MU5 | `M:680-686` | 残す floor/budget null 拒否を恒真化 | 単位 1 が実走で同定する既存負例 |
| MU6 | `s8b_oracle_driver.py` の store sha256 比較 | 恒真化 | `test_s8b_oracle_driver.py:5601` (`store-hash-mismatch`) |
| MU7 | 同 admission receipt 検査の例外捕捉 | 握り潰す | 同 `:6233` (`admission-mismatch` 系) |

**受理拡大の事前宣言 (変異ではない。撤去の意図した効果):**

1. floor の `pairs` から key を 1 つ落とした freeze は、撤去後 manifest API で受理される。
2. floor の pair 値が 0・負値、`scalar_alt` が max と不一致、null 相関違反の freeze も受理される。
3. `floor_budget_snapshot_sha256` を整合的に書き換えた文書は、案 (a) では旧 key 自体が拒否される。
4. 過去床値 campaign と別 binary で今回の oracle 測定を走らせても、測定前 abort は起きない。
5. 射程は `M:1198 build_approved_manifest` の公式 candidate 入口にも及ぶ (R5)。

## 裁定 6 — [T-434] と [T-1709]

- **[T-434]:** 実装しない。裁定は D1433 / D1434 で 2026-09-02 に着地済み。実装は [T-941]
  (P6 意味的充足契約の本体) に順序依存し、P6 は未実装。本 wave は carry を
  「裁定着地済み・実装は [T-941] の後」へ更新するだけとし、二段束縛の部品を land しない (D1421)。
  新しい起票はしない (D1433 のとおり共有 git 信頼境界の統一は起票しない)。
- **[T-1709]:** 上記 docs の明記で閉じる。`DECIDER_VERSION` の bump も次世代 record の発行もしない。

## 裁定 7 — scope 外として裁定パッケージへ返す

- R9: `p3_b4_floor_artifact_issuer.py:760-762` の行番号参照のずれ。
- `pipeline.py:2089` のコメント (「供給元は今回未配線」) は `:1780` の配線で既に古く、
  本 wave の撤去でまた意味が変わる。`pipeline.py` を触らない裁定の帰結として残す。
- 過去 insight の行番号 pin の完全閉包は未了 (段 2・レンズ B とも未了と申告)。
