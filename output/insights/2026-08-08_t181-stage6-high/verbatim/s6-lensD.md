必読パスはすべて読めた。pytest・`check_docs.py` は実行していない。以下は差分読解、AST による nodeid 列挙、書込みなしの regex メモリ上 probe に基づく静的判定である。

## 契約の忠実性 — 段 4 の 8 点

### CF-01

- ID: `CF-01`
- 主張: `実装 wave は` が保存され、docs-only wave へレビュー義務は拡大していない。
- 根拠: `docs/dev-wave/workers.md:48`「`実装 wave は…必ず 2 本並列`」。`docs/dev-wave/core.md:13-15`「`docs-only は子ゼロでよい`」。
- 判定: **refuted / nit**（欠落懸念は反証）。
- 成果物影響: 放置しても docs-only の受理集合、台帳、land 差分は変わらない。

### CF-02

- ID: `CF-02`
- 主張: `DW-S06-C` の「全体へ 1 本でよい」は、1 巡あたりの reviewer 本数として保存されている。
- 根拠: `docs/dev-wave/workers.md:67`「`焦点再レビューは全体へ reasoning=high で 1 本でよい`」。
- 判定: **refuted / nit**（削除懸念は反証）。
- 成果物影響: 各巡の reviewer 数は 1 本のままで、所見数・消費量・land 差分は増えない。

### CF-03

- ID: `CF-03`
- 主張: A/C の local literal と別々の exact pin は実装済み。
- 根拠: `workers.md:48,67` の各 `reasoning=high`、`tools/check_docs.py:3414-3423` の別 tuple、`:3426-3436` の節別判定。
- 判定: **refuted / nit**（未充足懸念は反証）。
- 成果物影響: A=high/C=max の矛盾 docs は C finding で拒否される。

### CF-04

- ID: `CF-04`
- 主張: whole-document 可視化を pin と H2 inventory の両方へ適用している。
- 根拠: `tools/check_docs.py:3399-3426`「`visible_workers_text` を節抽出へ」、`:3662-3667`「`visible_text` から H2 inventory」。
- 判定: **refuted / nit**（実装欠落懸念は反証）。
- 成果物影響: fence/comment 内へ H2 全体を隠した docs は pin と inventory の双方で拒否される。

### CF-05

- ID: `CF-05`
- 主張: 曖昧値の受理穴は、終端 allowlist と canonical literal exact-one で塞がれている。
- 根拠: `tools/check_docs.py:286-293` の allowlist、`:3435`「`values != [expected] or visible_section.count(literal) != 1`」。
- 判定: **refuted / nit**（受理穴自体は閉じた）。ただし変異帰属は `M6` で破綻する。
- 成果物影響: `reasoning=high/max` 等は現在の受理集合から除外される。

### CF-06

- ID: `CF-06`
- 主張: hidden-section/C=max/M4+M5 の登録自体は実施された。
- 根拠: `mutation-prereg.md:12-18` の M2/M4/M5/M7、`:33-35` の P1〜P3。
- 判定: **real / nit**。登録はあるが、M4/M5/M6 の kill 意味論は後述のとおり未成立。
- 成果物影響: 訂正しないと mutation ledger が実効 kill 数を過大計上する。

### CF-07

- ID: `CF-07`
- 主張: `operations.md` の縮約は、旧 4 主張を逐語でも意味でも完全には保存していない。
- 根拠:
  - 旧 `b97ad3b5^:docs/dev-wave/operations.md:3-4` は「`条件付き運用の正本。発火条件は入口の条件 dispatch が正本で`」。
  - 現 `docs/dev-wave/operations.md:3-4` は「`発火条件は入口の条件 dispatch、成立時の実行手順だけは本書が正本`」。
  - `が正本` が発火条件側から消え、語順も変更されているため逐語保存ではない。とくに「入口の条件 dispatch が正本」という明示的 canonicality が省略された。
  - これに対し `b97ad3b5 message:L23-24` は「`4 主張はいずれも保存している`」と断定する。
- 判定: **real / must-fix**。
- 成果物影響: 発火条件の正本を単なる所在と誤読でき、条件 dispatch と leaf の競合時に実行・停止判断、ひいては land 差分が変わる。

### CF-08

- ID: `CF-08`
- 主張: local-main SHA の停止条件は、結果上は stale を踏まなかったが、実行 gate として確認できない。
- 根拠:
  - `s4-ruling-package.md:57-59` は「`停止条件に local main の SHA 比較を足す`」。
  - `launch-s5.sh:6-10` は prompt/done/worktree だけを検査し、main SHA 比較がない。
  - `prompt-s5.txt:13-20` も docs commit 前提だけで SHA 停止条件を持たない。
  - 一方、実際の `b97ad3b5` の親は現在の main `cf90afcc` であり、今回の baseline 自体は stale ではない。
- 判定: **real / must-fix**（契約 gate 未実装。今回の stale 発生は refuted）。
- 成果物影響: 次の main 更新を見落とすと、byte 会計・共有 caller・fixture の片側を落とした land 差分になりうる。

## 記録の正直さ

### RH-01

- ID: `RH-01`
- 主張: `b97ad3b5` は T-181 の未認証状態、禁止主張、採用根拠、supersede を正しく分離している。
- 根拠: message `L6-14` に `experiment_complete=false`、`decision=null`、全 10 mismatch、非劣性・同等性・採用の証明ではない、採用根拠はユーザー裁定のみ、T-227/T-184 を明示 supersede、敵対レビュー 2 本は未測定、が揃う。
- 判定: **refuted / nit**（過大な evidence 主張は見つからない）。
- 成果物影響: この message 単独では T-181 を採用証拠へ昇格させない。

### RH-02

- ID: `RH-02`
- 主張: `303db412` 単独では射程がやや強く読める。
- 根拠: message `L1-4` は「`段 6 の reasoning を機械 pin`」と書く一方、launcher 非結線・docs drift 限定を再掲しない。技術本文 `L6-24` を読めば `check_docs` の pin と分かるが、件名だけなら実起動保証にも読める。対して `b97ad3b5 message:L27-29` は docs 限定を明示する。
- 判定: **real / nit**。今後の decision/worklog/insight では必ず「docs 契約 + drift pin のみ」と明記する必要がある。
- 成果物影響: 誤読すると台帳が「実起動 high を機械保証済み」となり、実際の reviewer 所見集合との乖離を隠す。

### RH-03

- ID: `RH-03`
- 主張: evidence 開示後のユーザー再裁定が、指定された監査可能 artifact 集合には逐語で残っていない。
- 根拠:
  - `s4-ruling-package.md:1,22-25` は「`ユーザー再裁定待ち`」「`親は採否を決めず返す`」。
  - 同 `:27-35` は α/β/γ の選択肢であり選択結果ではない。
  - その後 `b97ad3b5 message:L3` は「`ユーザー裁定 (選択肢 β)`」と断定する。
- 判定: **real / must-fix**。後続のユーザー発話が別に実在する可能性はあるため、その一次資料が提示されれば refuted。
- 成果物影響: 放置すると「採用根拠はユーザー裁定のみ」という唯一の根拠が追跡不能なまま decision と land 差分へ固定される。

### RH-04

- ID: `RH-04`
- 主張: D207 との限定例外関係がまだ記録されていない。
- 根拠:
  - `docs/decisions.md:9891-9902` は effort 引下げを paired・blind・非劣性評価だけへ送る一般原則。
  - `s3a.md:61-68` は今回を「D207 の段 6 限定・人間裁定による明示的例外／supersession」と記録するよう要求。
  - `b97ad3b5 message:L6-8` は T-227/T-184 の supersede と「D207 の段2/3は変更しない」だけで、今回が D207 原則の限定例外とは書かない。
- 判定: **real / must-fix**。
- 成果物影響: 放置すると今後「未 pin 箇所なら未認証 evidence で effort を下げられる」という decision precedent が残る。

### RH-05

- ID: `RH-05`
- 主張: 新 finding と関連テストには、時系列状態の断定や S06 の非劣性示唆はない。
- 根拠: `tools/check_docs.py:278-285` は「`現行 adoption pin と不一致`」だけ。`test_check_docs.py:5293-5300` が同逐語を固定する。新テストに非劣性を主張する docstring/comment はない。
- 判定: **refuted / nit**。
- 成果物影響: finding 逐語によって T-181 の認証状態や採用根拠が改変されることはない。

## 変異の帰属

以下の nodeid は実在する。静的な kill 予測であり、実走結果ではない。

| ID | 実在 nodeid / 根拠 | 判定 | 重要度・成果物影響 |
|---|---|---|---|
| M1 | `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max_exact`。`:5194-5212` は S06-A finding だけを exact 要求 | **real** | 有効。tuple 削除で production が A=max を受理し、land 可能 docs 集合が拡大 |
| M2 | `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_c_max`、`:4985-4991` | **real / nit** | helper では有効。ただし C=max の production exact node がなく、E2E 証拠は M8 の共有 caller に依存 |
| M3 | `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_decoys_and_duplicates`、`:5027-5039` | **real / must-fix 記録条件** | `high and max` が membership 化で受理される。S02/S03 node も赤になるため、ledger に S06 node を別記する |
| M4 | `...::test_dev_wave_reasoning_effort_pin_rejects_hidden_whole_s06_sections`、`:5145-5157` は赤くなる | **real だが実効 kill ではない / must-fix** | pin helper は変わるが production は inventory が拒否。単独を KILLED と数えると台帳を過大化 |
| M5 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact`、`:5217-5238` は exact finding 差で赤くなる | **real だが実効 kill ではない / must-fix** | rc は pin 層が非ゼロに保つ。診断 finding だけの赤であり `DW-M03` 上の kill ではない |
| M6 | `...::test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_ambiguous_values`、`:5094-5111` | **refuted / must-fix** | allowlist を旧 regex に戻しても `visible_section.count(literal) != 1` が拒否を継続。テストは regex 値 assertion で赤くなるだけで、受理集合は不変 |
| M7 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact` | **real / must-fix 記録条件** | M4+M5 同時なら hidden section が production で受理される。これだけが B-02 の実効 kill |
| M8 | `...::test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s06_a_max_exact` | **real** | production call 削除で S06-A=max が rc=0。既存 S02/S03 に依存しない S06 固有 receipt が既に存在する |

`M6` は書込みなし probe でも、`high/max` 等について「旧 regex は `['high']`、canonical literal count は 0、したがって count 併用時は引き続き拒否」と確認した。よって `M6` 単独を kill と数えてはならない。

正例の対応は次のとおり。

| 正例 | 実在 nodeid | 静的判定 |
|---|---|---|
| P1 | `...::test_dev_wave_reasoning_effort_pins_accept_current_workers_contract` | 現行 A/C high を受理 |
| P2 | `...::test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples` | A/C の可視 high + hidden max を受理 |
| P3 | `...::test_dev_wave_reasoning_effort_pins_accept_s06_b_inherited_without_literal` | 現在の B literal 不在を確認。ただし checker が将来の B literal を禁止する gate ではない |

登録漏れ・再照準案:

- `M9`: `or visible_section.count(literal) != 1` だけを削除する。S06 alias が新たに受理されるため、`test_dev_wave_reasoning_effort_pin_rejects_dw_s06_a_real_keys_and_quotes` が実効 kill する。production exact の S06 alias nodeも追加すべき。
- `M10`: 終端 allowlist の旧 regex 化と M9 を同時適用する。これが `high/max` 等の production 受理集合を実際に広げる B-04 の両層変異。
- 可視化先行の単独無効化は登録漏れではなく M4/M5 が該当する。ただし単独 kill 集合から外し、M7 だけを実効 kill とする。
- M3 の S06 固有性は S06 decoy node の失敗を ledger に残すことで測る。
- M8 の S06 固有性は S06-A=max production exact nodeが rc=0 へ変わることを測る。S02/S03 の赤件数だけを根拠にしない。

## 未処理の段 3 所見

### S3-01

- ID: `S3-01`
- 主張: B-05 の `DW-O16` override 防止が取りこぼされている。
- 根拠: `s3b.md:79-87` は O16 の effort 空 pin または権威節の機械化を要求。現 `docs/dev-wave/operations.md:83-87` に effort はなく、`tools/check_docs.py:3400-3424` は workers の4節しか検査しない。
- 判定: **real / must-fix**。
- 成果物影響: O16 に将来 `reasoning=max` を足しても checker が通り、C=high と矛盾した実行から所見・fix・land 差分が変わる。

### S3-02

- ID: `S3-02`
- 主張: B-01 の射程制限は commit には入ったが、これから書く三記録にも必須。
- 根拠: `s4-ruling-package.md:73-79` と `b97ad3b5 message:L27-29` は「docs drift のみ・launcher 別途」を明記。一方 `303db412 message:L1` は「段 6 の reasoning を機械 pin」と縮約。
- 判定: **real / must-fix（記録）**。
- 成果物影響: decision/worklog/insight が実起動保証と書けば、台帳の保証値が実装より強くなる。

### S3-03

- ID: `S3-03`
- 主張: B-06 は scope 外 residual として明示し続ける必要がある。
- 根拠: `workers.md:24,55,59-60` は S06-B が S05-A=high を意味的に継承。`303db412 message:L9-10` は S05-A/B を pin 対象外と明記。P3 test `:4905-4916` は現行 literal 不在を見るだけで、将来 drift を拒否しない。
- 判定: **real / nit**。ただし「段 6 全 child を機械 pin」と記録するなら must-fix。
- 成果物影響: 誇張すると B/fix 子の effort drift を台帳が見逃し、fix 内容と land 差分が宣言から乖離する。

### S3-04

- ID: `S3-04`
- 主張: A-08/A-09 の D207 限定例外と evidence-aware 再裁定の一次資料が未処理。
- 根拠: `s3a.md:61-75`、および RH-03/RH-04。
- 判定: **real / must-fix**。
- 成果物影響: adoption decision の唯一の根拠と precedent が不正確なまま canonical 台帳へ入る。

## 総括

**NO-GO**。

- `operations.md` 縮約は旧 4 主張を逐語保存せず、発火条件の正本性を弱めている。
- local-main SHA 停止 gate は結果上不要だったが、段 4 設計どおりには実装・記録されていない。
- M4/M5 は単独の実効 kill ではなく、M7 だけが production 受理集合を変える。
- M6 は canonical-count 層に mask されるため単独 kill 主張が不正。count 単独変異と両層変異が必要。
- O16 の conflicting effort を checker が拒否しない。
- evidence 開示後の β 再裁定一次資料と、D207 への限定例外記録が必要。
- 今後の decision/worklog/insight は「docs 契約 + drift pin のみ」「S05-A/S06-B は対象外」を必ず明記する。
