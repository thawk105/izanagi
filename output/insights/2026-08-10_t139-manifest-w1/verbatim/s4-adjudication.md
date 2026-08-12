# 段 4 裁定 — [T-139] 第 1 波 (dev-wave-t139-manifest-w1、2026-08-10)

**裁定: 依頼された (i)〜(v) のうち、承認 manifest・受領証 schema の digest 固定・a13/b03 予約台帳・
producer 本体 (resolver / binding / verify_receipt) は本 wave では実装しない。**
docs 4 点と、第 2 erratum の機械化 1 点だけを実装する。`4→5→6→7→8→9` を通常どおり進む。

段 3 のレンズ 2 本はともに **NO-GO** (A = blocker 5 / must-fix 3、B = blocker 5 / must-fix 6 / nit 1)。
**親は全件 real と裁定する (refuted 0 件)。** これで親の一般化が段 3 で覆るのは 8 wave 連続である。

親の実測値 (`F_e` の祖先性、core digest、221 行の digest、pin 閉包) はレンズ A が再計算して
全件一致した。**覆ったのは実測値ではなく、そこから導いた「承認できる」「1 wave で閉じる」という
一般化のほうである。**

---

## 0. 親が撤回する誤り

- **(P1) の「再発行すれば D262 との乖離が解消する」は誤り (レンズ A B1)。**
  D262 は現行 record-items の digest `1957026c…8fd3` を承認済み blob として固定している。
  **`F_e` より後に生まれた blob を `F_e` が承認することはできない。** 追補 A の先例 (旧版が
  そもそも非承認) とは状況が違う。再発行版を承認するには新しい承認 fold `F_r` が要り、
  manifest はその子孫にしか置けない。再発行という**形**は正しいが、
  「本 wave 内で承認まで到達できる」という部分が誤りだった。
- **(P3) を「D263 は説明文だから無視してよい」で済ませたのは不十分 (レンズ A M1 / B B1)。**
  D263 は canonical decision であり、その事実文を明示的に supersede せずに
  承認集合を確定してはならない。無視ではなく**上書き記録**が要る。
- **「pilot 停止 gate を実装する」という読みは誤り (レンズ A B3)。**
  現行の public 経路には T-139 の投入 API が 1 つも無く、D264 の非 export 検査が
  `test_module_exports_no_admission_api` で機械固定されている (実測: 同名 4 つは
  `__all__` にも属性にも無い)。**pilot は今すでに機械的に止まっている。**
  ここへ「停止 gate」を新設すると、D264 が名指しで却下した**恒真 deny の stub** そのものになる。
  Q-B が求める機械停止は**既に成立しており、本 wave の作為で満たすものではない。**
  必要なのは「gate を作るとき第 2 erratum の承認を条件に含める」という要件の記録である。

## 1. 所見の裁定

**全 19 所見が real、refuted 0 件。** 重複を統合した独立所見と裁定は次のとおり。

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| F1 | 再発行 record-items は `F_e` に承認されない。承認には新 fold が要り、manifest はその子孫 | A-B1 | real・**ユーザー裁定へ** (Q-D と構造的に両立しない) |
| F2 | D263 の「第 2 erratum は既に承認済み」は事実誤り | A-M1 / B-B1 | real・**採用**。新 decision で当該事実文を supersede し状態を三値化 |
| F3 | 現行 public 経路は恒真 deny。承認後に通る正例が未構成 | A-B3 | real・**採用**。gate を作らない根拠とする |
| F4 | Q-A 第三分岐は厳密な受理拡大で、marker 無し attempt を捏造できる | A-B4 | real・**採用**。実装はするが非保証として明記し、ユーザーへ注記 |
| F5 | land lock は Git common dir 内。独立 clone の二重予約は防げない | A-B5 / B-M5 | real・**採用**。保証境界を逐語で固定し、台帳実装は次 wave |
| F6 | `PreregBinding` は caller が偽造でき、`PATH` 経由で git も差し替えうる | A-B2 | real・scope 外 (U6 未実装)。次 wave の必須要件 |
| F7 | structured reason が pass/fail の言い換えに留まる | A-M2 | real・scope 外。次 wave の必須要件 |
| F8 | `manifest_ref` の自己参照と parser 署名が矛盾 | A-M3 / B-M3 | real・scope 外。次 wave の必須要件 |
| F9 | record-items が完全 schema でなく、未閉包の nested object が残る | B-B2 | real・**採用 (scope 内)**。再発行版で閉包を与える |
| F10 | gate が効く全層 (intent / driver / collector / writer / correctness / consumer) が scope 外 | B-B3 | real・**採用**。裁定パッケージへ名指しで返す |
| F11 | 新規変異 matrix が無い | B-B4 | real・**採用**。§3 で登録 |
| F12 | 未 land wave を積み上げる手順が無い | B-B5 | real・**採用**。§4 に手順を書く |
| F13 | 見積りが「文書」と「コード」を混ぜており比較不能 | B-M1 | real・採用。§2 で分離 |
| F14 | U1 の artifact commit が他単位の所有を奪う | B-M2 | real・**scope 縮小により消滅** (docs は親が単独で書く) |
| F15 | synthetic v2 は非恒真性の証拠に留まり実効 gate の正例ではない | B-M4 | real・採用。正例を主張しない |
| F16 | D264 を緩める前提で計画しない | B-M6 | real・**採用**。4 名前の非 export を維持する |
| F17 | U6 の実装面を過少表示 | B-N1 | real・nit。§2 の見積りで是正 |
| F18 | `verify_receipt` は `orchestrator/campaign/t080_freeze_migration.py:1956` に**既に別概念で実在**する | 親の実測 | real・**採用**。`DW-O13` / D75 の同名二義化。次 wave は別名か明示的な namespace 分離が要る |
| F19 | 追補 B `b03` が primary とは別の「個別公表系列台帳」を要求する (main b6a4f5b0 で land) | 親の実測 | real・**採用**。台帳は 2 本。段 1 の U5 scope は過小だった |

## 2. プラン v2 — 本 wave の確定 scope

### 2.1 docs (親が単独で書く)

| 単位 | 内容 |
|---|---|
| **D1 — record-items 再発行版** | Q-A 第三分岐 (`a03` failure evidence + 対応する `environment_observations[]` の実在) を `post_performance_failure` の第三の充足経路として入れる。あわせて F9 の未閉包 object (`allocations[]` / `liveness[]` / `attempts[]` / `phase_caps[]` / `translation_units{}` / `cluster_slots[]`) に exact key を与える。F4 の捏造余地を「本案が保証しないこと」へ明記する。**承認済みとは名乗らない** |
| **D2 — 第 2 erratum 起草** | `erratum_id: t139-core-s7-stresscheck-v1`。core 221 行 (`事前 simulation で較正する。`) への 1 operation。§3 に**この erratum 固有の**検査を書く (operation 数 1、`old_sha256` 一致、対象語句の出現ちょうど 1 件、置換後も core の他の受理条件を変えない)。erratum-1 の locator 404/424 と非重複 |
| **D3 — decision fragment** | D263 の「第 2 erratum が既に承認済み」を前向きに supersede し、erratum の状態を `validator_registered` / `draft_unapproved` / `approved` の三値に分ける。**registry 登録は承認ではない** |
| **D4 — 裁定パッケージ** | F1 / F4 / F5 / F10 / F18 / F19 をユーザーへ返す (§5) |

### 2.2 実装 (Codex `role=author`。1 単位のみ)

| 単位 | 内容 |
|---|---|
| **U-E2 — 第 2 erratum の機械化** | D263 の registry へ `t139-core-s7-stresscheck-v1` の固有 validator を足す。あわせて **`DRAFT_ERRATA` (未承認集合) を導入し、承認集合を問う経路が draft を返さないことを機械検査する。** erratum-1 と第 2 erratum の locator 非重複と、2 件適用後の合成 digest が erratum-1 単独の `d1782b04…de82` と**異なる**ことを固定する |

**gate API は 1 つも増やさない。** `resolve_effective_preregistration` / `PreregBinding` /
`submit_pilot` / `verify_receipt` は本 wave でも export しない (D264 維持、F16)。
`test_module_exports_no_admission_api` は緑のままでなければならない。

### 2.3 実装しない (裁定待ち、または次 wave)

承認 manifest (F1 の裁定待ち) / 受領証 JSON Schema と digest 固定 (F1 と F9 閉包の後) /
`a13` primary 台帳と `b03` 公表台帳 (F5 の保証境界と F19 の 2 本化を裁定後) /
`resolve_effective_preregistration`・`PreregBinding`・`verify_receipt` (F6 / F7 / F8 / F18) /
submission intent・PBS・driver・collector・receipt writer・correctness verifier・certified consumer。

### 2.4 見積り (F13 に従い分離)

| 単位 | docs 行 | production 行 | test 行 |
|---|---:|---:|---:|
| D1 | 380〜480 | 0 | 0 |
| D2 | 150〜190 | 0 | 0 |
| D3 | 45〜60 | 0 | 0 |
| D4 | 120〜160 | 0 | 0 |
| U-E2 | 0 | 90〜140 | 150〜220 |

## 3. 変異事前登録 (`DW-M01`)

`tools/mutation_harness.py` を使う。対象は U-E2 のみ (docs 単位は実装差分ゼロ)。
単一理由帰属を確認済み — 各変異の入力を前後で拒否する層が無いことを、
registry が `erratum_id` 単位で分岐する構造から確認した。

| # | 変異位置 | 期待する受理集合の変化 | 期待 node |
|---|---|---|---|
| M1 | 第 2 erratum validator の operation 数 `== 1` 検査を無効化 | 2 operation の s7 erratum が通る | `test_s7_erratum_rejects_operation_count_not_one` |
| M2 | 同 validator の `old_sha256` 行照合を無効化 | core 221 行以外を指す erratum が通る | `test_s7_erratum_rejects_old_sha256_mismatch` |
| M3 | 同 validator の「対象語句の出現ちょうど 1 件」検査を無効化 | 出現が 1 件でない core にも適用される | `test_s7_erratum_rejects_occurrence_count_not_one` |
| M4 | `DRAFT_ERRATA` の除外を外し draft を承認集合へ含める | 未承認の第 2 erratum が承認済みとして扱われる | `test_draft_erratum_is_not_in_approved_set` |
| M5 | locator 非重複検査を無効化 | 重なる locator を持つ erratum 対が合成できる | `test_overlapping_locators_rejected` |
| M6 | 未知 `erratum_id` の fail-closed を既定値へ落とす | 未登録 ID が検査を飛ばして通る | `test_unknown_erratum_id_fails_closed` |

**wave 前の実コードの形を含む変異 (M4)。** wave 前は「registry に居る = 使ってよい」を
区別する構造が無く、`_ERRATUM_VALIDATORS` の membership がそのまま適用可否だった
(`erratum.py:383` の `_ERRATUM_VALIDATORS.get(document.erratum_id)`)。
M4 はその**wave 前の逐語と同型**の変異である。生存したら検査側を直す。

**正例も登録する** (受理集合を縮小する変異があるため)。
承認済み erratum-1 が従来どおり `d1782b04…de82` を与えること
(`test_approved_erratum_composes_to_expected_digest` の緑維持) を回帰として固定する。

## 4. 未 land wave の積み上げ手順 (F12)

本 wave は Q-D に従い land しない。次 wave が引き継ぐために次を固定する。

1. 本 wave の **base main SHA** と **wave tip SHA** を worklog fragment と handoff に逐語で残す。
2. 次 wave は **main からではなく本 wave の tip から** worktree を作る。
3. 受入全走・変異結果は**本 wave の tip に対する測定値**として記録し、次 wave はそれを
   緑判定の代わりに使わない。**最終 wave の tip で全走・全変異・provenance を再実施**してから
   一度だけ land する。
4. 本 wave の spool fragment は本 branch に置いたままにする (**wave 側で fold しない**)。
   採番は最終 land の lock 内で一度だけ行われる。

## 5. ユーザー裁定へ返す (裁定パッケージ)

別ファイル `package.md` に詳細を書く。要旨:

1. **Q-D の「同一 land」が manifest の構造要件と両立しない (F1)。** 新しい承認済み blob
   (record-items 再発行版・受領証 schema) は、それを承認する decision を fold した後でなければ
   manifest に pin できず、manifest は自分の fold SHA を literal に持てない。
   **最低 2 回の fold = 2 回の land が構造的に要る。**
2. **Q-A 第三分岐の残存捏造余地 (F4)。** 裁定どおり実装するが、marker 無しの attempt を
   「環境観測が不成立だった」と申告するだけで正当化できる。閉じるには producer 権限外の
   collector が要る。certified 値は上がらないが、**試行台帳の「実行しなかった」が偽造可能**になる。
3. **`a13` 台帳の保証境界 (F5) と、`b03` による 2 本目の台帳 (F19)。**
4. **gate が効くために必要な未実装層の一覧 (F10)。**
5. **`verify_receipt` の同名衝突 (F18)。**
