# 段 4 裁定 — [T-139] producer 実装 (dev-wave 2026-08-09)

**裁定: vertical slice 全体は実装しない。scope を「activation + 参照束縛の純関数 2 本」へ縮小して実装する。**
`4→5→6→7→8→9` を通常どおり進む (「実装しない」裁定ではない)。

段 3 の敵対レンズ 2 本は**ともに NO-GO** を返した (レンズ A = blocker 11 / must-fix 2、
レンズ B = blocker 8 / must-fix 4、計 25 所見)。**親は全件 real と裁定する (refuted 0 件)。**
これで親の一般化が段 3 で覆るのは **7 wave 連続**である。

---

## 0. 親が撤回する誤り

- **(P1) の読み分けは半分だけ正しかった (レンズ A 所見 5)。**
  親は「D162 段 C の validator は pilot の後」から「correctness の検査も後」を導いたが、
  これは **適格性 validator の後置**と **correctness verifier の即時 gate** の混同である。
  絶対規律 3 は「verifier は毎 iteration 回して次の一手のシグナルにする」を要求する。
  trace-enabled run が G2 anomaly を出したのに driver が pointer を保存するだけなら、
  終端 reject すべき候補へ性能 attempt と費用が積まれる。
  **correctness verifier は pilot と同じ単位に要る。**(P1) をその形へ訂正し、次 wave の必須要件に移す。
- **(P3) の e2e 正例は成立しない (レンズ A 所見 13 / レンズ B 所見 9)。**
  stub driver が完成 JSON を返す形の「正例」は、submission intent・PBS preflight・実 driver・
  collector・binding 必須 sink をすべて迂回する。**偽陽性であり、pilot 投入可否を証明しない。**
  本 wave は e2e 正例を主張しない。
- **(P6) の alpha 台帳を本 wave の scope に入れる判断は撤回する (レンズ A 所見 9)。**
  段 2 案の「固定 Git ref に置く」は canonical ではない — clone A と clone B が push せずに
  それぞれ `(F, 1)` を CAS 予約でき、各 local validator は重複なしと判定する。
  **台帳の canonicality は設計択一であり、親が決めてよい範囲を超える。**裁定パッケージへ返す。

## 1. 所見の裁定 (real / refuted、採否、scope)

**全 25 所見が real、refuted 0 件。**重複を統合すると独立な所見は 18 件である。

| # | 所見 (統合後) | 出所 | 裁定 |
|---|---|---|---|
| F1 | N5 — `a04` の preflight 写像と `record-items` の `post_performance_failure` 条件が直接矛盾する | A1 / B1 | real・**ユーザー裁定へ**。schema digest 固定の前提が壊れている |
| F2 | approval trust root が P5 / P7 / plan の三通りあり、どれも実装されていない | A2 / B3 | real・**本 wave が activation payload で一意化する** (scope 内) |
| F3 | schema digest が `PreregBinding` に束縛されず、後続 commit で緩めた schema へ差し替えられる | A3 / B4 | real・**scope 外へ移す** (schema を本 wave では発行しない)。次 wave の必須要件 |
| F4 | binary 非同一性制約は 3 arm の循環置換で恒真化できる (`C_S=P_D, C_D=P_X, C_X=P_S`) | A4 | real・scope 外。次 wave の必須要件 (集合としての非同一性 + exec witness) |
| F5 | correctness verifier が未配線で後段へ先送りされている (絶対規律 3 違反) | A5 | real・**§0 で親の誤りとして撤回**。次 wave の必須要件 |
| F6 | N3 — `a12` が未較正・core §7 の第 2 erratum が不在のまま `submit_pilot` へ進める | A6 / B5 | real・**ユーザー裁定へ**。本 wave は `submit_pilot` を実装しないので現時点で経路は無い |
| F7 | `a03` 恒真化 mutant を予定テストが kill しない (判定だけ `allowed=True` 固定) | A7 | real・scope 外 (driver 未実装)。次 wave の必須要件 |
| F8 | binding 必須 sink を generic writer (`create_json`) で迂回できる | A8 / B7 | real・scope 外 (writer 未実装)。次 wave の必須要件 |
| F9 | alpha 台帳を固定 Git ref に置くと clone 間で二重予約できる | A9 / B6 | real・**ユーザー裁定へ** (設計択一)。(P6) 撤回 |
| F10 | `attempts[]` の exact coverage が collector 検査と publish の間で競合する | A10 | real・scope 外。次 wave の必須要件 (series close CAS / ledger-head digest) |
| F11 | nested closure の保証が `$defs` 限定で、inline object に穴が残る | A11 | real・scope 外 (schema 未実装)。次 wave の必須要件 |
| F12 | 変異の単一理由帰属が成立しない (欠落と余剰を 1 変異にまとめている等) | A12 | real・**採用 (scope 内)**。本 wave の変異登録を §3 で単一理由へ分解した |
| F13 | e2e 正例が production driver を通らず、半実装 land を再導入する | A13 / B9 | real・**採用**。§0 で (P3) を撤回し、A+B を land しない |
| F14 | `reason_code` enum がプランと承認済み `record-items` で不一致 | B2 | real・scope 外 (schema 未実装)。次 wave は承認済み enum を正とする |
| F15 | (P1) は §11 と整合するが validator→consumer→certified 選択が未配線で、実効 vertical slice ではない | B8 | real・**採用**。本 wave は「vertical slice を通した」と主張しない |
| F16 | 編集所有が素集合でない (決定 fragment を U0 と U5 が二重所有) | B10 | real・**scope 縮小により消滅** (fragment は親 1 人が書く) |
| F17 | T-126 機構の流用境界が未定義 (`QualificationRoot` の root 固定、retry 0/1、failure enum、SPRT 意味論) | B11 | real・scope 外。次 wave の必須要件 |
| F18 | 規模見積りが 1 wave に収まらない (production 4,900〜6,000 行 + test 2,550〜3,200 行) | B12 / plan | real・**採用**。分割する |

## 2. プラン v2 — 本 wave の確定 scope

### 2.1 実装する (Codex `role=author`)

| 単位 | 内容 | 理由 |
|---|---|---|
| **U1 — erratum operations applier / checker** | `erratum-core-s15.md` §3 の検査 1〜4 を機械化する純関数。git blob を入力に取り、2 operation を累積適用して合成後 bytes と digest を返す。`len(operations) == 2` / 各 `old_sha256` の行照合 / `a01`〜`a12` の出現件数 == 2 / `new_text` と `old_text` の差分が 1 token、をすべて課す。失敗は例外で fail-closed | **次 wave の approval manifest が要求する `composed_sha256` を、手計算でなく機械で導出できるようにする。**親は §4 で手計算したが、手計算を trust root にはできない |
| **U2 — 追補 A envelope parser** | `addendum-a-reissue.md` §0 の grammar (`fields := "## fields" の直後から次の "## " 見出しまで` / `key := その範囲内の "### " 見出しの先頭トークン`) を実装し、exact-13 の key 集合を返す。全文 grep で `aNN` を集める実装を禁じる | 追補 A §0 が「機械可読形の発行は producer 実装 wave の責務」と明記する。exact-key 解決のすべての土台であり、どの未裁定事項にも依存しない |

**いずれも admission gate ではない。**公開 API (`resolve_effective_preregistration` /
`PreregBinding` / `submit_pilot` / `verify_receipt`) は 1 つも export しない。
モジュールの docstring に「本 module は投入 gate ではない」を明記し、それを固定するテストを置く。

### 2.2 実装しない (裁定待ち、または次 wave)

受領証 JSON Schema と digest 固定 (F1 の裁定待ち) / `PreregBinding` と公開 resolver (manifest が
`F_e` の子孫にしか置けない) / `submit_pilot`・`verify_receipt` / alpha 予約台帳 (F9 の裁定待ち) /
PBS 測定本体・driver・collector・durable intent / correctness verifier 配線 / e2e 正例。

### 2.3 docs (親が書く)

**activation payload** — §51 の承認を機械可読へ写した decision fragment。次を逐語で持つ。

```
target_core        path / commit 88d68f91… / sha256 ac939af4…60e9
approved_blobs     addendum_a      622bd786… / f7db96ce…cfec
                   derivation_map  7ec08816… / bf5b6783…6025
                   erratum         1d235e0e… / a1abc60e…9dd6d3
                   record_items    1d235e0e… / 1957026c…8fd3
erratum_application_order  [t139-core-s15-exactkey-v1]   (配列。実装に len==1 を置かない)
composed_sha256    d1782b04…de82
superseded         2026-08-08_t139-addendum-a/addendum-a.md = 1f561258…46bdd は非承認
ruling_record      worklog エントリ 346 (fold commit 2169a06c)
```

**この fragment を fold した commit が `F_e` になる。**payload 自身は `F_e` を書かない
(同一 commit に自分の SHA を literal で持てないため)。次 wave が `F_e` の子孫に
approval manifest を置き、literal な `approval_fold_commit = F_e` を収める。
これで F2 の三通りが一意化する。

## 3. 変異事前登録 (`DW-M01`)

`tools/mutation_harness.py` を使う。**単一理由帰属を F12 の指摘どおり分解した** —
欠落と余剰、範囲限定と件数検査を 1 変異にまとめない。

| # | 変異位置 | 期待する受理集合の変化 | 期待 node |
|---|---|---|---|
| M1 | U1 の `len(operations) == 2` 検査を無効化 | 3 operation の erratum が通る | `test_erratum_rejects_operation_count_not_two` |
| M2 | U1 の `old_sha256` 行照合を無効化 | 別の行を指す erratum が通る | `test_erratum_rejects_old_sha256_mismatch` |
| M3 | U1 の「`a01`〜`a12` の出現件数 == 2」検査を無効化 | 出現が 2 件でない core にも適用される | `test_erratum_rejects_occurrence_count_not_two` |
| M4 | U1 の「差分が 1 token」検査を無効化 | 本文を書き換える operation が通る | `test_erratum_rejects_multi_token_delta` |
| M5 | U1 の合成後 digest 照合を無効化 | 誤った合成 bytes が通る | `test_erratum_composed_digest_must_match` |
| M6 | U2 の範囲限定 (`## fields` 〜 次の `## `) を外し全文の `### ` を拾う | §0 や末尾節の `aNN` が field に数えられる | `test_envelope_parser_ignores_headings_outside_fields` |
| M7 | U2 の exact-13 検査を `⊇` へ緩める (**余剰のみ**) | 14 個目の field を持つ追補が通る | `test_envelope_parser_rejects_extra_key` |
| M8 | U2 の exact-13 検査を `⊆` へ緩める (**欠落のみ**) | 12 field の追補が通る | `test_envelope_parser_rejects_missing_key` |
| M9 | U1/U2 の失敗経路を例外でなく既定値へ落とす (fail-open) | 解決失敗が `{a01..a12}` へ緩和される | `test_resolution_failure_is_fail_closed` |

**正例も登録する** (受理集合を縮小する wave の義務)。
承認済み追補 A が exactly `{a01..a13}` へ parse され、承認済み erratum が
`composed_sha256 = d1782b04…de82` を与えることを固定する
(`test_approved_addendum_parses_to_exact_thirteen` / `test_approved_erratum_composes_to_expected_digest`)。
**M6〜M8 は parser 直テストだけでなく公開入口経由でも赤くなること**を実装子へ要求する (F12)。

## 4. 親が実測した値 (一次資料から。段 2 の申告値と全件一致した)

| 対象 | 実測 |
|---|---|
| core blob at `F` | `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9` (450 行) |
| erratum op1 の対象行 (404 行目) の SHA-256 | `6e87b981b2d3550ea56278a50f9544a86bab575d18de3ea7f3984abdeca5681e` ✓ |
| erratum op2 の対象行 (424 行目) の SHA-256 | `b5e2c7b290c1c21aff84f4b520468df551c9d0e4bd76d2102ace3208b3e1b7d1` ✓ |
| `a01`〜`a12` の出現件数 | **2 件** (404 / 424 行のみ) ✓ |
| 2 operation 適用後の core digest | `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82` |
| 承認済み 4 blob の digest | 上の §2.3 の表のとおり。段 2 の申告と全件一致 |
| 旧版追補 A の digest | `1f5612587ffeacd39285a28fb1b2e35df6e904689ec30bcc4877e85223146bdd` (承認版と相違、N2 の pin は効く) |

**erratum §3 の検査 1〜4 は、承認済み blob に対してすべて成立する。**恒真ではない
(検査 3 は「出現が 2 件」を要求し、実測も 2 件だった)。

## 5. 成果物影響 (`DW-G05`)

- **U1 / U2 を実装しない場合:** 次 wave の approval manifest が `composed_sha256` と
  exact-13 key を**親の手計算に依存**する。自己申告を権威にしない規律に反し、
  manifest の値が誤っていても誰も検出できない。
- **activation payload を land しない場合:** approval manifest は**永久に書けない** —
  manifest は自分の fold commit の SHA を literal で持てないため、先行 fold が構造的に要る。
  `F_e` が無い限り resolver は fail-closed のままで、pilot は投入できない。
- **本 wave が A+B を land した場合 (棄却した案):** schema digest と公開 resolver が固定され、
  受理集合の拡大 (`∅ → R13`) を実装した状態で実 producer 正例を持たない。
  台帳だけが「producer 実装済み」へ進む (前 wave の B5 と同型、レンズ 2 本が独立に blocker 判定)。

## 6. ユーザー裁定へ返す 4 問 (裁定パッケージ)

別ファイル `package.md` に詳細を書く。要旨は次のとおり。

1. **Q-A (F1 / N5):** `post_performance_failure` に第三の分岐
   (`a03` failure evidence + 対応する `environment_observations[]`) を認めるか。認めないと
   preflight で落ちた正当な attempt を記録できない。**受領証 schema の digest 固定はこの裁定待ち。**
2. **Q-B (F6 / N3):** core §7 の「較正する」義務が未達のまま段階 2 が発効している。
   §47 R2 (a) が承認した第 2 erratum を誰がいつ起草するか。それまで pilot を機械的に止めるか。
3. **Q-C (F9 / N4):** alpha 予約台帳の canonicality をどこに置くか
   (固定 Git ref は clone 間の二重予約を防げないと敵対検証が示した)。
4. **Q-D (F18):** 残りを 2 波に割るか 3 波に割るか。親の推奨は
   **本 wave (activation) → contract+producer 1 波 (Q-A〜Q-C の裁定後、A+B+C を同一 land)**。
   A+B だけを先に land する分割は F13 により採らない。
