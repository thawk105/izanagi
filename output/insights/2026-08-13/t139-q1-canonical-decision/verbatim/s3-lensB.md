### 1. 読んだ資料と、読めなかった資料

指定された必読資料 14 件はすべて読了。読めなかった資料はない。加えて `CLAUDE.md`、dev-wave dispatcher、`docs/spool/decisions/README.md`、指定 D の canonical 本文、現行 preregistration/publication module、受領証 schema、record-items、現存 fragment を読んだ。Web 取得・編集・テスト実行は行っていない。

### 2. 判定 (GO / NO-GO / 条件付き GO)

**NO-GO。** 承認済み a10/a11 の数値契約との不一致、D291 exact role closure の曖昧さ、`F_r*` resolver の実装 seam 欠落、fragment slug drift があり、このまま land すると受理集合・J・参照 identity が不定になる。

### 3. 所見一覧

| 項目 | 内容 |
|---|---|
| ID | B-1-1 |
| 攻撃面 | B-1 |
| 主張 | B4 の `2^-80` dyadic 格子は、承認済み a10/a11 の `1e-9` 以下の認証区間契約を変更している。 |
| 証拠 | `s2-plan.md:135`；`output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:724-748`；`docs/decisions.md:12898-12906` |
| 成果物影響 | `J`、`design_not_feasible`、conformance vector、受領証の受理集合が変わり、certified 選択・レポート・台帳が既存 authority と一致しなくなる。 |

| 項目 | 内容 |
|---|---|
| ID | B-1-2 |
| 攻撃面 | B-1 |
| 主張 | `addendum_b alias / source_addendum_b` は、D291 の exact 2 role に alias を追加するのか外部入力だけを正規化するのか不明である。 |
| 証拠 | `s2-plan.md:200-214`；`docs/decisions.md:13369-13377,13441-13447`；`docs/decisions.md:14076-14079` |
| 成果物影響 | alias を manifest role として受ければ role 集合が広がり、拒否すれば plan の root mapping が実装不能になる。 |

| 項目 | 内容 |
|---|---|
| ID | B-1-3 |
| 攻撃面 | B-1 |
| 主張 | bytes 級 approval、commit root、vector digest を要求する契約は D320 の既定見送りに対する T-139 限定 supersede 文言が未確定である。 |
| 証拠 | `docs/decisions.md:14532-14540`；`src-rulings7.md:18-20`；`src-worklog-516-t139.md:8-15`；`s2-plan.md:254` |
| 成果物影響 | 個別裁定の例外範囲が台帳上不明なままとなり、approval manifest と vector pin の land 可否、後続 resolver の authority が揺れる。 |

| 項目 | 内容 |
|---|---|
| ID | B-2-1 |
| 攻撃面 | B-2 |
| 主張 | B1 は correctness compile にも `configure_argv` がある前提で書かれているが、現行 schema の correctness compile field は `argv` である。 |
| 証拠 | `s2-plan.md:64-66`；`output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json:805-825`；`record-items-v2.md:228-245` |
| 成果物影響 | 実在しない field を追加すれば schema closure が変わり、追加しなければ correctness 側の 3 者一致検査が欠落する。 |

| 項目 | 内容 |
|---|---|
| ID | B-3-1 |
| 攻撃面 | B-3 |
| 主張 | B4 は `approval_manifest` を承認済み `blobRef` と分類するが、D282 の 6 role と D291 の 2 role のどちらにも存在しない。 |
| 証拠 | `s2-plan.md:130-136`；`docs/decisions.md:12898-12922`；`docs/decisions.md:13369-13377`；`receipt-schema-v1.json:257-288` |
| 成果物影響 | manifest 自体の authority が循環または未定義になり、実装は余計な role を受け入れるか、全 transcript を拒否することになる。 |

| 項目 | 内容 |
|---|---|
| ID | B-3-2 |
| 攻撃面 | B-3 |
| 主張 | `F_r*` を読む新しい versioned loader と既存 D282 loader の共存契約が plan にない。 |
| 証拠 | `s2-plan.md:61-66,157,197-214`；`orchestrator/preregistration/approval_payload.py:16-32,166-171,461-497`；`orchestrator/preregistration/__init__.py:3-28` |
| 成果物影響 | 既存 loader を変更すれば D282 の exact 6 role 契約が壊れ、変更しなければ `F_r*` を解決できず manifest acceptance が空のままになる。 |

| 項目 | 内容 |
|---|---|
| ID | B-3-3 |
| 攻撃面 | B-3 |
| 主張 | intent set、receipt set、transcript、manifest の各 discovery 結果を D234 の単一 `PreregBinding` と受領証 field へ束ねる入力写像が未定義である。 |
| 証拠 | `s2-plan.md:34-47,98-137`；`src-D234.md:64-94`；`record-items-v2.md:150-159,421-476`；`orchestrator/preregistration/__init__.py:3-5` |
| 成果物影響 | 個別 writer が存在しても admission path が結線されず、実体を検査しない恒真 deny または authority を失った受理経路になる。 |

| 項目 | 内容 |
|---|---|
| ID | B-4-1 |
| 攻撃面 | B-4 |
| 主張 | plan が宣言する slug と、現存する land 候補 fragment の slug が異なる。 |
| 証拠 | `s2-plan.md:24-30` は `t139-acceptance-predicate-envelope`；`docs/spool/decisions/2026-08-13-dev-wave-t139-q1-canonical-decision-1.md:7-17` は `t139-admission-predicate-and-approval-envelope`；`src-spool-readme.md:59-63` |
| 成果物影響 | `(wave, namespace, slug)` identity が分岐し、worklog からの placeholder 参照、fold、最終 D 参照のいずれかが不一致になる。 |

| 項目 | 内容 |
|---|---|
| ID | B-5-1 |
| 攻撃面 | B-5 |
| 主張 | Q2 の exact manifest root が将来の B1 `F_r*` に依存するため、Q1 と Q2 を一体化したままでは Q2 が B1 の後続 land に人質を取られる。 |
| 証拠 | `src-Q1-Q2-package.md:8-23,56-64`；`s2-plan.md:143-157,259-263`；`src-land2q4-package.md:116-126` |
| 成果物影響 | B1 の schema または approval payload が変わるたび Q2 の manifest digest と受理集合も変わり、Q4 の一 session 契約を満たせない。 |

| 項目 | 内容 |
|---|---|
| ID | B-7-1 |
| 攻撃面 | B-7 |
| 主張 | plan の未完了一覧は、schema digest binding、approval manifest、resolver と receipt writer という前提 #4〜#6 を独立した pilot blocking gate として列挙していない。 |
| 証拠 | `s2-plan.md:259-267`；`src-land2q4-package.md:42-52`；`record-items-v2.md:164-173,780-827` |
| 成果物影響 | decision land 後に契約だけを実装済みと誤記でき、`submit_pilot` の非空受理例、certified 選択、レポート、試行台帳はいずれも生成できない。 |

### 4. B-1 で照合した既存 D の一覧と、それぞれの照合結果

| D | 照合結果 |
|---|---|
| D234 | 外部署名と 7 条件は plan が保持しており直接衝突なし。ただし binding への入力写像は B-3-3。 |
| D262 | 歴史的な旧 `record_items` 承認であり、D282 の後発 role supersession を経由する必要がある。 |
| D264 | pure reference helper から gate API を export しない契約と整合。ただし新 gate は別 module に置く必要がある。 |
| D282 | exact 6 role、legacy root 除外、alpha reservation の扱いを維持する必要がある。新 `F_r*` loader の共存が未定義。 |
| D291 | exact 2 role、全 `document_relations`、historical reject、role coupling を要求する。alias 表記だけが衝突候補。 |
| D292 | plan は pilot/main の禁止を維持しており整合する。land 直後の解禁はできない。 |
| D305 | 単一 role 公開 API を作らず batch resolve する点は整合する。alias を role として受けない明記が必要。 |
| D306 | marker gate の保証範囲を `approved_blobs:` 形式へ限定する点と直接衝突しない。vector digest の安全性まで同じ gate と称してはならない。 |
| D308 | compiler 解決と toolchain binding の同一 land 規則であり、本 plan の docs-only 契約とは直接関係しない。 |
| D320 | bytes 級 pin・commit root・digest を新設する内容は既定見送りと衝突する。第 7 束の T-139 限定例外を明示的に supersede として書く必要がある。 |

### 5. 反証を試みて refuted になったもの

- **Q1/Q2 の取り違え:** refuted。`src-worklog-516-t139.md:8-15` と `src-rulings7.md:18-20` はともに Q1 = 受理述語 4 件、Q2 = 固定 envelope + namespaced projection と記録している。
- **`submission.py` に short-write 検査と fsync がない:** refuted。`orchestrator/qualification/submission.py:143-164` に `O_EXCL`、書込みループ、file fsync、directory fsync がある。残る read-back 欠落は `src-land2q4-package.md:82-88` の別所見である。
- **D305 が単一 role 公開 API を既に要求している:** refuted。`orchestrator/publication/approval_d291.py:542-596` は exact 2 role の batch resolve であり、plan の batch 前提はこの点では正しい。

### 6. scope 外だが real な所見 (裁定パッケージ候補)

- `s1-brief.md:131-140` のとおり、tracked な worktree-local handoff と `DW-O20` の external handoff 条件が衝突し、background job wave の起動 gate が main 単独で赤になる。
- `qualification/submission.py` は durable write 自体は実装済みだが read-back 検証がないため、T-139 decision の land 可否とは別に submission durability の裁定候補である。

## 総括

承認済み数値の書換えと role closure の曖昧さは受理集合を直接変えるため blocker である。  
現行 API は D282/D291 の既存承認を読む helper に限られ、T-139 の新 envelope と binding を結ぶ seam がない。  
slug drift も fold identity を壊すため、fragment をそのまま land できない。  
D320 の T-139 限定例外と、land 後も pilot を解禁しない前提を canonical 本文へ明記すべきである。