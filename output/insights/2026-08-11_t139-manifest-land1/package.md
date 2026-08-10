# [T-139] 第 2 波 — ユーザー裁定パッケージ (2026-08-11)

wave `dev-wave-t139-manifest-w2`。裁定 R1〜R5 に従って land 1 (文書承認 fold) を実行しようとしたが、
**R1 を裁定した時点で未見だった事実が、承認対象そのものを承認不能にしていた。**
段 2 のプラン (codex `gpt-5.6-sol`) と段 3 の敵対レンズ 2 本 (`gpt-5.6-sol` / `gpt-5.6-luna`) が
ともに NO-GO を返し、親は所見のうち 2 件を refuted、残りを real と裁定した。

**本 wave は承認候補 3 点を承認可能水準へ直した。land はしていない。**
理由は下記 S1 のとおりで、記録項目の確定はもともと D229 決定 (7) と事前登録 §11 段 A が定める
**単独の裁定 gate** の対象であり、R1 (a) が認可したのは land の順序であって、
まだ存在しなかった schema blob や欠陥のある草案の**内容**ではない。

---

## S0. 直したもの (branch `worktree-dev-wave-t139-manifest-land1`、local main から分岐)

| 成果物 | 内容 |
|---|---|
| `record-items-v2.md` | **自己完結版**。前 2 版の受理条件を再掲し、第三分岐 (`a03` 不成立証拠) の追加、`pre_performance_infra_failure` の `a04` 準拠への**縮小**、全 nested object の exact key 閉包、到達 point 条件つき `binary_rehash` (最大 9 要素)、`malformed_reason` の非 null 必須化と評価順序、`a13` の append-only 全履歴検査、消費 cluster slot の pilot での 1〜8 固定、schedule 表の canonical bytes、受領証の粒度と terminal 性、役割別 phase 閉集合、申告値と実体の 3 者一致、非保証節、**§10 の閉包 8 件の明示** |
| `erratum-core-s7-stresscheck-v2.md` | operation を **1 件から 2 件**へ (core 221 行 + 333 行)。**置換内容を `new_sha256` と `expected_composed_sha256` で pin** し固有検査を 12 件へ。合成 digest は `e0b0caea…8e0c` |
| `receipt-schema-v1.json` | 上記に対応する機械可読 schema (JSON Schema draft-07、1326 行、object schema 51 件すべて `additionalProperties:false` + `required`)。Codex `role=author` が起草・修正 |
| 承認 decision fragment | **機械可読 payload**。D262 の `record_items` 承認を role 付きで前向きに supersede |

**schema と要件文書の関係は「exact 1:1」ではない。** draft-07 は配列内の種別別件数・参照整合性・
raw 再計算を表現できないため、**要件文書 §7.1 が列挙する 20 項目は schema の外**にあり、
固定 semantic validator (land 2) が担う。schema の適合は受理ではない。

**この 3 点は敵対レビュー 2 本 (レンズ C = 凍結述語の一意性・網羅性 / レンズ D = producer 視点の攻撃) を
通した後の版である。** 両レンズはいずれも初版に NO-GO を返し (blocker 9 件 / 4 件)、
親は 12 件を real として採用、1 件を refuted と裁定した。**残余リスクは §S8 に書いた。**

**land 1 に残っている作業は「S1〜S7 の裁定 → main 取り込み → 受入全走 → land」だけである。**

---

## S1. land 1 の 3 文書の内容を承認するか (最重要)

### 承認前に見つかった欠陥 (すべて親が一次資料で実測。両レンズも独立に再現)

| # | 欠陥 | 実測 |
|---|---|---|
| 1 | **凍結 core は較正義務を 2 箇所に持つ** | 221 行と **333 行** (`\| a12 \| weak null の型 I 誤りを較正する事前 simulation の仕様 \|`、LF 込み sha256 `a7852ad9…9952`)。`較正` の出現はこの 2 件のみ。221 行だけを置換すると core が「§7 = stress check、§14 = 較正」の**二重状態**になる |
| 2 | **草案が承認後に自分の承認状態について偽を述べる** | 両草案の `approval_status: draft_unapproved`、「本書は承認されていない」。先例 (承認済み追補 A・erratum-1) にこの field は無い |
| 3 | **草案が裁定外の受理拡大を含む** | `pre_performance_infra_failure` を marker 不在だけで成立させており、`a04` が「開始後の失敗・置換しない」と定める attempt (性能 raw を持つ / `a03` 不成立) を**予備置換可能**にしていた |
| 4 | **exact key 閉包が未完で内部矛盾があった** | `binary_rehash` 3 要素 (`a05` は 3 arm × 3 点 = 9)、`malformed_reason` の null 可否が節間で矛盾、`exclusivity.method` の enum が開放、`environment.attestations[]` / `dependency_pins[]` / `actual_runs[]` / `correctness_evidence[].run_scope` / `toolchain.dynamic_deps[]` の key 未定義 |
| 5 | **`a13` の検査が現 tip の重複だけだった** | 過去の予約行を削除して同じ `(family_root, ordinal)` を再登録した履歴を受理する。R3 (a) の append-only 全履歴検査を満たさない |
| 6 | **受領証 schema が存在せず、dialect も未確定だった** | この環境の `jsonschema` は 3.2.0 で `Draft202012Validator` を持たない (Draft 7 のみ) |
| 7 | **pilot が消費する 8 slot の identity が未凍結だった** | `a09` は slot 1〜13 の schedule を発行するが、pilot がどの 8 本かを定めておらず、**結果を見て選べた** |

### 問い

**直した 3 文書 (`record-items-v2.md` / `erratum-core-s7-stresscheck-v2.md` / `receipt-schema-v1.json`)
を承認し、land 1 を実行してよいか。**

- **(a) 承認して land 1 を実行する (親の推奨)。** 次 wave は「main 取り込み → 受入全走 → land」だけを行う。
- (b) 承認前に人間が全文を読む。→ 承認は遅れるが、凍結する述語を人間が確認できる。
- (c) 一部だけ承認する。→ `receipt_schema` の digest を `PreregBinding` に固定できないので
  pilot は投入不可のまま。R1 が land 1 に schema blob を含めたのはこれを避けるためである。

---

## S2. core の逐語を 2 箇所変えてよいか

裁定 Q-B / R2 (a) が想定したのは **§7 の 1 箇所**の置換だった。上記 #1 により、
それだけでは core が矛盾したまま残る。

- **(a) erratum-2 を 221 + 333 の 2 operation にする (親の推奨)。**
  未承認 blob 1 枚と合成 digest の更新だけで済み、新しい artifact を増やさない。
  合成 = `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c` (適用順不変、
  置換後 core に `較正` 0 件)。
- (b) 221 行だけを置換し、333 行は別の前向き correction で扱う。→ 承認単位が 2 つに増え、
  どちらか一方だけが承認された中間状態が生まれる。
- (c) 333 行を放置する。→ core が「§7 = stress check、§14 = 較正」の二重状態のまま凍結される。
  絶対規律 3 が禁じる「保証していない性質を保証したと書く」が残る。

**承認済み追補 A の `a12` 見出し行**にも `較正` の語が残るが、直後の本文が「本 field はその較正を
与えない」と明記している。**親の推奨は据え置き** (legacy label として承認 payload と材料 report に
逐語で記録する) である。承認済み blob の再発行は、追補 A の digest を pin する payload と実装 pin を
連鎖的に変えるため、受理集合を動かさない語の整合には見合わない。

---

## S3. 受領証 schema の dialect

- **(a) JSON Schema draft-07 (親の推奨)。** 根拠は好みではなく実測 —
  この環境の `jsonschema` は 3.2.0 で 2020-12 の validator を持たず、
  repo の既存受領証 schema (`orchestrator/qualification/t126_final_receipt_schema.json` 等) も
  draft-07 + `definitions` 形式である。必要な keyword (`patternProperties`・`propertyNames`・
  `additionalProperties:false`・`if/then/else`) はすべて draft-07 に存在する。
- (b) 2020-12 で書き、engine を land 2 で導入する。→ 承認した schema をその時点の engine で
  検査できず、**dialect の差が受理集合を動かす**余地が残る (`unevaluated*` の扱い)。
  依存追加はサブスク外の話ではないが、pin と供給の管理が新たに要る。

いずれを採っても、本 wave の schema は**両 dialect で意味が同一の keyword だけ**を使い、
参照を `definitions` + JSON pointer に限る (`$defs` を使わない) ため、変換は `$schema` 行の
差し替えで済む。

---

## S4. pilot が消費する cluster slot を 1〜8 に固定してよいか

`a09` は slot を 1 起点で定義し、任意の prefix `1..r` で先行 workload の本数差を
`⌈r/2⌉ − ⌊r/2⌋ ≤ 1` に保つ設計である。したがって**先頭から連続して消費する**ことが prefix 均衡の
前提であり、`a10` は適格 pilot cluster を 8 本とする。

- **(a) `pilot_cluster_slots = [1,…,8]` を受領証要件として固定する (親の推奨)。**
- (b) 追補 A へ erratum を当てて `a09` 側で固定する。→ 承認済み blob の再発行を伴う。
- (c) 固定しない。→ producer が結果を見て残り slot を選べる (`{1..8}` と `{6..13}` の両方が
  「8 本・各 slot の schedule は正しい」を満たす)。**実行順・観測値・pilot 共分散・`J` が
  結果依存で変わる。**

---

## S5. `a13` の予約と R1 の「同一 land」の因果循環

`a13` は **pilot 投入より前に** canonical 台帳へ `(family_root, ordinal) = (F, 1)` の予約が
入っていることを要求する。一方 R1 は manifest + producer + pilot 投入・測定を**同一 land**に置き、
`tools/dev_wave_land.py` は完成済み tested tip を**一度だけ** ff/fold する。
予約は pilot の前、受領証は pilot の後に main へ入る必要があるため、**1 回の land では時系列が閉じない。**

- **(a) 予約 entry (JSONL 1 行) を land 1 の fold へ同梱する (親の推奨)。**
  予約 entry は data であり gate ではない。land lock の内側で fold されるので
  `a13` の「producer が選べない canonical な台帳で原子的に」を満たす。
  これで `予約 land → land 2 branch で pilot → 受領証 commit → land 2 を 1 回 fold` が成立する。
  ただし R1 が列挙した land 1 の内容 (承認 decision + record-items + schema + erratum) に
  **予約 entry を追加する**ことになるため、裁定なしには実行できない。
- (b) 予約を land 2 の tested tip に入れ、pilot は land の後に走らせる。
  → 「pilot 投入・測定を同一 land」に反する。
- (c) 予約の canonical 権威を main 以外 (remote ref / 共有 CAS) に置く。→ R3 (b) であり
  裁定済みの R3 (a) と矛盾する。

**(a) を採る場合、台帳 path・entry の canonical bytes・append-only 検査の仕様は
`record-items-v2.md` §6.7 が既に定めている。**land 1 に足すのは 1 行の data と、
その行を承認 decision が pin することだけである。

---

## S6. land 2 を 1 land のまま複数 session に跨げるか

段 2 の見積りは production 7,600 行 + test 7,820 行 = **15,420 行**、pilot 1 本までの最小集合でも
**11,770 行**。PBS は検証割当て 1 + 適格 pilot 8 (+ 予備 2) = **9〜11 割当て × 3600 秒**。

レンズ B は「1 session に必ず収まらない」の証明は**成立しない**とした (session 上限が未定義で、
性能割当ては並列化しうる)。ただし GO も証明できない。core は pilot 1 本目から scheduler 会計を
検証して「1 本ずつ保守的に上限を更新」とするため、8 本同時投入を前提にはできない。

- **(a) 同一の未 land branch を複数 session が継承し、最終的に 1 回だけ land する (親の推奨)。**
  R1 の「同一 land」は保たれる。第 1 波・第 2 波と同じ形の継承である。
- (b) pilot 1 本地点で中間 land する。→ R1 に反する。かつ pilot 1 本では `n_p = 8` を満たさず
  `J` も certified 選択も動かないので、**「gate が効いた」証拠にならない。**
- (c) land 2 を分割してよいことにする。→ R1 の再解釈。

---

## S7. scope 外だが real な層 (次 wave の必須要件として受け取ってよいか)

本 wave では実装しない。**land 2 の段 1 brief へ必須要件として持ち込む。**

| # | 所見 | 成果物への影響 |
|---|---|---|
| 1 | **resolver が「台帳 → manifest」の第 1 矢印を持たない** | `approval_fold_commit = F_r` を保った偽 manifest が、攻撃者の三つ組を列挙し expected digest も自分から供給すれば、祖先検査と自己整合をすべて通る。**未承認 blob が承認済み identity になる** |
| 2 | **Git trust root が `PATH` 差し替えで迂回できる** | 偽 `git` が `rev-parse` / `merge-base` だけ偽装すれば、`F_r` より前の測定が通る。SHA の偽造は不要 |
| 3 | **symlink / TOCTOU 防止が未指定** | 検査時と hash/parse 時で別 raw を読める。`a03`・run log・intent・correctness evidence の参照先が入れ替わる |
| 4 | **correctness anomaly の構造化還流契約が無い** | G2 cycle を検出しても、どの trx・rw edge が壊れたかが次 iteration・材料 report へ届かない (絶対規律 3) |
| 5 | **変異の単一理由帰属が未証明** | 前後の層が先に拒否すると「当該 node だけが落ちる」を主張できない。M26 案は承認経路が固定集合 API のため wave 前実コードと非同型 |
| 6 | **`a05` の build 手順を既存 probe から直接再利用できない** | 既存 positive-control probe は全 build `CCBENCH_TRACE=0`、compiler を `command -v` で解決し、`r4` の compile validator は mode macro を拒否する |
| 7 | **`b03` 個別公表系列台帳** | 追補 B が段階 1 に留め置かれ、公表 core は別 wave が起草中。記録要件が未凍結 |

---

## S8. 残余リスク (承認するなら引き受けることになるもの)

裁定は求めないが、承認の意味を正確にするために書く。

1. **§10 の閉包 8 件は承認済み文書から一意に導けない選択である。** 承認するとこれらが受理述語になる。
   反転したい項目があれば S1 の裁定で名指ししてほしい (特に閉包 1 = pilot slot 1〜8 は S4 の問い)。
2. **schema の適合は受理ではない。** §7.1 の 20 項目は semantic validator が実装されるまで
   **1 つも発火しない。**したがって land 1 の時点では「受領証を機械的に検査できる」状態にはならない。
   これは R1 (a) が「コード・gate を含めない」と定めた帰結であり、欠陥ではない。
3. **既存 driver は要求証拠を取得していない** (S7 #6 の展開)。レビュー D が既存 probe を読み、
   次が未取得と判定した — 全 build が `CCBENCH_TRACE=0` で correctness 用の trace-enabled build が
   無い / 全 TU の `translation_units` と canonical `compile_commands` を保存しない /
   executable の inode・per-run `exec_witness`・9 点 `binary_rehash`・dynamic deps・ELF interpreter を
   取得しない / `exclusivity.raw` と scheduler accounting trace を受領証形式で取らない /
   marker が単純な state file で 36 観測窓・canonical schedule・wait trace を保存しない。
   **要件が実装不能なのではなく、land 2 で collector / driver を作る量がこれだけあるという意味である。**
4. **本 wave の 2 レビューは実装を走らせていない** (read-only)。文書と schema の静的検査、
   digest 再計算、部分 schema の正例・負例検査だけである。
5. **要件文書は 1 晩で書かれた。** 前 2 版はいずれも次 wave のレビューで blocker を出しており、
   本版も同様の残余がある可能性を排除できない。凍結の可否は S1 の裁定に委ねる。

## S9. dev-wave の改善候補 3 件 — docs 予算に入らないため裁定へ返す

段 8 で本 wave の実測から 3 件の手順改善が出た。いずれも `docs/dev-wave/operations.md` の既存 leaf 節
(`DW-O02` / `DW-O18`) へ 1〜2 行で統合できる内容だが、**`docs/dev-wave/**` の L1.5 予算に入らない**
(実測: 現状 9508 bytes / 予算 9566 bytes = 余裕 58 bytes ≈ 日本語 19 文字。
2 件を最短化しても 9700 bytes で 134 bytes 超過した)。

予算値を上げる変更は自己改善に含めない規律であり、dev-wave 系への外出しは D94 で却下済みなので、
**編集を止めて返す。**

| # | 実測した事象 (いずれも本 wave で実害) | 統合先候補 |
|---|---|---|
| 1 | **段 5 の子が読む正本を親が稼働中に編集した。** schema 実装子が要件文書を読んでいる間に親が同節を直し、子の出力が旧版基準になった (`planned_execution.runs[]` の件数制約が旧値のまま)。fix 1 巡を要した | `DW-O02` — 「投入後は子が読む path を凍結し、変更が要るなら子を止めて再投入する」 |
| 2 | **prompt の必読 path が子の worktree に存在しなかった。** land 1 branch は local main 起点なので第 1 波の未 land 草案が無く、レビュー C が fail-closed して 1 巡を空費した (子の挙動は正しい) | `DW-O02` — 「必読 path は投入前に子の worktree で実在を確認する」 |
| 3 | **file 選択走が `from tests import` の import path を確立せず偽赤を出す。** docs-only の対象実走で 2 件が `ModuleNotFoundError: No module named 'tests'` で落ちた。差分が到達しえない形であり、権威は land 時の全走 | `DW-O18` — 「選択走は import path を確立せず偽赤を出す。権威は land 時の全走」 |

裁定の選択肢: **(a) 予算の独立審査を起票して 3 件を入れる (親の推奨)** / (b) 陳腐化した既存節を
特定して等価縮約で空ける (どの節が陳腐化したかの判定自体が別 wave の仕事) / (c) 3 件を入れない
(同じ事故が次 wave で再発する)。

## 付録 A. 報告のみ (裁定不要)

- **承認済み追補 A `a01` (B) の算術誤記 (正しい値は 2640)。** 検証割当ての非余裕小計は
  `180+1440+360+360+180+120 = 2640` であり、`a01` (B) の表本文も **2640** と書いている。
  ところが同 field の直後にある検算文だけが **2340** と書いており、**この 1 箇所が誤記である。**
  本 wave の要件文書 §6.9 は正しい **2640** を採り、`2340` を一切参照しない。
  **受理集合は phase 別 cap で決まるため変わらない。**承認済み blob の再発行を伴うため
  erratum の対象にはしない (scope 爆発を避ける)。将来 core / 追補を再発行する機会があれば同時に直す。
- **pilot 1 本の E2E は成果物を変えない。** `a10` は適格 pilot 8 本を要求するため、
  1 本では `J`・certified 選択・材料 report・試行台帳の値が 1 つも動かない。
  pilot 1 本を「gate が効いた」証拠として報告してはならない。
- **単独性は保証できない。** 計算ノードは専有割当てを保証せず、外部 process の情報は診断に留まる。
  受領証は単独性検査の**生出力 pointer** だけを持ち boolean を持たない。

## 付録 B. 親が実測した値 (両レンズが独立に再現・全件一致)

```text
F_e (D262 の fold commit)          dce4ae4fed6f4fb33747165c5b92c16d01822850  (HEAD の祖先)
凍結 core (450 行)                 ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
core 221 行 (LF 込み)              225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89
core 333 行 (LF 込み)              a7852ad9a4812f8adc8ebf33354a5934bd6620205a23defa48732a1737a89952
core 中の `較正` を含む行           221, 333 の 2 件のみ
合成 (erratum-1 のみ)              d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82
合成 (erratum-1 + 2 op 版 erratum-2) e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c
現行 record-items (D262 が pin)     1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3
jsonschema (実環境)                3.2.0 / Draft202012Validator 不在
```
