## must-fix

なし。今回の差分に起因する、成果物の値・受理集合・参照を壊す実装不備は確認できなかった。

## should-fix

1. **変異台帳の検出範囲・検出箇所を訂正する。**  
   `/home/SFC/tanab/.claude/jobs/f6bf33bb/ruling-s4.md:60` の M2「新 policy を load する全 test」は成立しない。`test_b7_invalid_policy` の unknown／workloads／cells は変異後も期待する例外を得て緑になる。特に workloads ケースは、workload 数検査を通過しても cell 数検査で同じ `study shape` に一致する。  
   同ファイル`:64` の M6 は、receipt 自体には POLICY_PATH が残るため、env assert では検出されない。実際の検出点は `orchestrator/tests/test_paper_story_a2_job_contract.py:1372` の実 argv 比較。  
   **最小 fix:** 台帳を下記の期待集合・検出箇所へ修正する。実装変更は不要。

## refuted

以下、`M`＝`orchestrator/campaign/paper_story_a2_certification.py`、`C`＝`orchestrator/tests/test_paper_story_a2_certification.py`、`J`＝`orchestrator/tests/test_paper_story_a2_job_contract.py`、`S`＝`tools/pegasus/submit_paper_story_a2_certification.sh`。

- **closed set の拡張は指定範囲内。** `M:363` は canonical path 一件追加、`:378` は study/job 名一件追加、`:388` は同 study の追加環境キー、`:569` は `(3,6)` 一件追加。未知 study・別 shape の拒否は維持される。`S:273`／`:365` も exact study の追加のみ。`load_policy` 単体が任意ファイルを読めるのは既存仕様で、CLI の `_load_selected_policy`／`_exact_qsub_command` は canonical 選択を維持する（`M:5130`, `:5164`）。Path が従来から正規化する表記まで「すべて拒否」とは主張しない。

- **既存 pin・成果物の変更なし。** `git diff 657e1e5a7 c18a80967 --stat` は指定5ファイル、376追加・12削除。`author.patch` は同 commit 間 diff と bytes 一致。A-2/A-6 policy bytes は基準 commit と一致し、SHA はそれぞれ `f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c`／`682e0f4ed980b74d509426d8f074f51f5b8062a1ca7cf82cd8dbbaae93c4446a`。protocol preimage 実装と既存 protocol pin（`C:1880`, `:2061`）も無変更。既存テストの削除・skip 化・期待値反転はない。

- **全件テストは機構経路を通る。** `C:2577` は実 policy のコピーを実 `load_policy` で読み、durable base だけを一時領域へ変更する。実 `preregister_attempt → finish_group → validate_acquisition_bundle → collect_results → materialize` を呼び、6 cell・3 effects・18 member・`COMPLETE.json` を検査する。`_test_token` は渡していない。WAL／receipt は合成 fixture であり、実ベンチ実行を証明するテストではない。揮発 payload の固定 hash を期待値へ焼いていない。

- **3 workload の全件経路に固定2件制約はない。** `M:2237` は policy 順で completion jobs を構成し、`:2303` 以降で全成功時に manifest を作る。`:4061` は `6 × workload_count`＝18 member、`:4326` 以降は6 raw＋3 condition receipt＋9 lock/WAL/claim を要求する。`:4387` は3 receipt を検証する。request IDs は `:2038`／`:2975` で policy 順・`:2980` で一意性を検査。`:4819` は fresh destination を要求し、`:4851` で各 receipt、`:4883` で COMPLETE marker を書く。

- **partial 境界を実際に叩いている。** `C:2687` は成功1件／2件とも full schema・manifest 不在を確認し、partial schema に変更して `M:1933` の exact two-workload 拒否へ到達する。ただし `[2]` は「成功が1件でない」条件にも該当するため、workload 数条件だけの独立証人は `[1]`。同じ入力が後段の manifest 検査にも不適格である点も、単一理由性の説明では区別すべき。

- **submitter テストは実 bash を呼ぶ。** `J:737` の subprocess は実 submitter、wrapper 内も実 loader／`a2.main` を利用する。`:1358` で3 request ID、`:1362` で workload 順、`:1368` で scheduler argv、`:1372` で qsub wrapper が記録した実 argv と receipt を照合する。なお `:746` の finish-group 戻り値は捨てているため、このテストが証明するのは finish-group の呼出しまで。成功経路の証明は前述の全件テストが担う。

- **正しさ gate は同値。** 新 policy の `controlled_define_base`・`legacy_correctness`・`trace0_cmake_argv` は A-2 と完全一致。`M:492` は TRACE=0 を要求する。全 policy cell を分類する `:2982` → `:2876` の anomaly 判定 → `:2988` の outer reject に rr95 も含まれる。B7 全件テストの gain=0.9 は性能負例であり、anomaly 注入テストではない。

## 変異の期待 node

対象2ファイルについての**静的期待完全集合**。以下の `C::`／`J::` は上記ファイルパスへ展開する。集合記号は省略記法であり、未列挙の node を含まない。

**F（2 node）**

```text
C::test_b7_full_collect_materializes[1.1-observed-positive]
C::test_b7_full_collect_materializes[0.9-reject]
```

**L（1 node）**

```text
C::test_b7_policy_literal
```

**P（2 node）**

```text
C::test_b7_cli_canonical_policy[relative]
C::test_b7_cli_canonical_policy[absolute]
```

**N（1 node）**

```text
C::test_b7_noncanonical_policy_rejected
```

**B（2 node）**

```text
C::test_b7_partial_boundary[1]
C::test_b7_partial_boundary[2]
```

**D（4 node）**

```text
J::test_m6_submitter_duplicate_detection_is_study_scoped[b7-same-study]
J::test_m6_submitter_duplicate_detection_is_study_scoped[b7-a2-other-study]
J::test_m6_submitter_duplicate_detection_is_study_scoped[b7-a6-other-study]
J::test_m6_submitter_duplicate_detection_is_study_scoped[b7-prefix-collision]
```

**S（1 node）**

```text
J::test_b7_submitter_three_requests
```

| 変異 | 赤になる完全集合 | 静的根拠・単一理由性 |
|---|---|---|
| M1 | F ∪ L ∪ P ∪ N ∪ B ∪ D ∪ S ∪ `{C::test_b7_policy_bytes_pin}`（14） | 通常ロードは adopted 整合で拒否、bytes pin は直接不一致。既存 genome 負例は rr5 にも不正を作るので緑のまま。全 node が単一の検査で落ちるという意味ではない。 |
| M2 | F ∪ L ∪ P ∪ N ∪ B ∪ D ∪ S ∪ `{C::test_b7_invalid_policy[genome-adopted cell does not match workload policy]}`（14） | 正例は workload 数で拒否。genome 負例は期待例外文言が変わって赤。unknown／workloads／cells 負例は緑。workloads 負例では拒否層が cell 数へ移る。 |
| M3 | P ∪ D ∪ S（7） | canonical path 選択で拒否。D の same-study ケースも期待する重複検出文言を得られず赤。 |
| M4 | F ∪ L ∪ B ∪ D ∪ S（10） | job 名 lookup が失敗。外へ出る例外は KeyError 自体ではなく、それを包む `CertificationError`。 |
| M5 | F ∪ L ∪ B ∪ S（6） | 「B7 は8キーを返す」変異として導出。L は直接集合比較、他は submission receipt の9キーとの不一致。条件から B7 を削るだけなら未知 study 拒否になり、集合は同じでも検出理由は異なる。 |
| M6 | S（1） | receipt の env は正常なまま。`J:1372` で実 argv の POLICY_PATH 欠落を検出する。 |
| M7 | S（1） | receipt 再構成が8キーになり、`M:1583` の環境集合検証で record-submission が失敗。`J:1357` が赤。 |
| M8 | ∅（0） | help 文言を期待値に固定する検査はなく、受理動作も変わらない。SURVIVED 期待。 |

未確認：変異適用後の実測結果。親ログは通常状態の307 passed／1071 passed・6 skipped を示すが、変異の KILLED／SURVIVED 実証にはならない。M5 は実際の置換内容も台帳で固定する必要がある。

## 裁定パッケージ候補

なし。

## 総括

実装上の must-fix は確認できなかった。  
既存 pin・受理境界・正しさ gate は維持され、3 workload 全件回収を静的に追跡できた。  
変異台帳には検出範囲・検出箇所の訂正が必要。  
通常テストの親実走は確認済み。変異期待集合は静的導出であり未実測。