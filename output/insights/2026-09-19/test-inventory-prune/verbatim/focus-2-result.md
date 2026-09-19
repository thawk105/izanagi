## 判定

**focus-1 新規所見 1（対応表 #2）：closed。** 関数単位の分類は本文と整合し、「実挙動併存」への一括分類は解消している。

以下の test 名は `orchestrator/tests/` 相対。

| 対象 | 本文との照合結果 |
|---|---|
| 純粋な定数 pin 7 関数 | 全7本文が定数と literal の比較。§5 の分類は妥当。 |
| `test_paper_story_a1_paired.py:903` | 実ファイルの SHA256 とファイル集合の固定。「資料・派生値 pin」が妥当。 |
| `test_skip_classification.py:315` | README の指定節に既定 nodeid があることを検査。同分類が妥当。 |
| `test_t1434_t1222_science_slice.py:409`、`test_t189_oracle_wiring_slice.py:132` | test 内 helper が JSON 資料から抽出する path 集合と literal tuple の比較。production 関数を通さず、同分類が妥当。 |
| `test_paper_story_a1_headline.py:1232` | Git の祖先関係・固定区間の変更不存在・作業木の clean 状態を検査。production の挙動検査ではなく、同分類が妥当。ただし説明に軽微な誤記あり（後述）。 |
| `test_b10_backoff_grid_submit.py:137` | 資料の文字列 pin と `bash -n` の構文検査が併存。 |
| `test_floor_pair_job_contract.py:91` | 資料由来の spec hash と、shell `select_pin` の出力・実 bytes を照合。併存分類が妥当。 |
| `test_t2187_adaptive_const_probe.py:4130` | 資料の SHA256 pin と production reader の返値検査が併存。 |
| `test_plot_b10_static_tail_formal.py:414`、`test_plot_a1_sized_paired.py:388,471` | production の closure 検査を含む。「(D) でない」への移動は妥当。 |
| `test_spool_fold.py:500,1753` | 直接または helper 経由で `plan_fold` の番号導出・byte-exact 挿入挙動を検査。同じく移動は妥当。 |

**数値・主張範囲：closed。** §5 の file 集合は重複なく **7＋5＋3＋26＝41 file** で、plan の41 fileと過不足なく一致する。冒頭・§2 の内訳、および §9 の併存3関数・非D代表26 file・未確認246関数も整合する。26 file は代表についての判定と明示され、未確認関数への分類拡張や新たな過大主張は認めない。

## 新規所見

**1. nit — README §5 の headline の path 数が誤っている。**

`README.md:104` は「manifest 12 path」と記すが、`test_paper_story_a1_headline.py:1233–1250` の tuple は **17 path**。また本文は固定2区間の diff に加え、祖先関係と対象 path の作業木が clean であることも検査する。

「manifest 17 path の固定2区間での変更不存在、祖先関係、作業木の clean 状態」と直すと正確になる。分類と集計を変える問題ではなく、阻害所見とはしない。

## GO/NO-GO

**GO — (D) の関数単位分類の阻害所見は解消。説明の軽微な誤記1件が残る。**

## 総括

focus-1 新規所見1を closed と判定した。指定された本文と関連 helper を読み、4区分と節間の数値整合を確認した。今回の判定は (D) 分類に限定し、ファイル変更・pytest・変異再走は行っていない。