# 層 3 の bench-first screening 対応の現況確定 (論文ストーリー §8 B-9)

**日付:** 2026-09-16
**branch:** `worktree-dev-wave-layer3-screening-currency`
**統合 commit:** `f47876014` (test 5 本 + 実レポート + insight)
**性質:** 新しい計測ゼロ。既存 artifact への現行 producer の実走と、既存裁定の一次資料照合だけ。

## 結論 — B-9 の 3 項は「進める」対象ではなかった

| 項 | 状態 | 根拠 |
|---|---|---|
| (a) bench-first screening campaign への対応 | **2026-08-25 に着地済み** | `b8318b956` ([T-1291]) が schema へ `screening` / `screening_disabled` を追加、`ed251424d` が `settled` を boolean と null の 2 型へ拡張。**renderer は変えていない** |
| (b) 値改変に対する深い一致検査 | **ユーザー裁定で「実施しない」** | 2026-08-03 の裁定 (択 b)。本体着手には択 (a) の再裁定が要る。項目の正本は `docs/phase3.md` の見送り台帳 |
| (c) 機序仮説層 (v3) | **発効条件待ち** | 凍結設計が要求する `runs/agent_outputs.jsonl` は repo 内に 0 件。DW-G04 により実装せず起票のみ |

**したがって本 wave の成果は「B-9 を進めた」ではなく「B-9 の 3 項を実測で仕分け、(a) の
成立を成果物で確定し、論文の記述を現況へ直した」である。**

## 着手順と残件

1. **済 (本 wave)** — (a) の成立を成果物で確定し、射影の完全性を回帰 pin し、
   論文入口 (`docs/paper-story/README.md`) と `docs/phase3.md` と `docs/glossary.md` を現況へ直した。
2. **次 (ユーザー手番)** — (b) の再訪には 2026-08-03 裁定の択 (a) の**再裁定**が要る。
   AI 側から着手できない。再裁定が出れば、既存 7 件の層3 レポートの再生成要否判断を伴う
   独立 wave になる (裁定本文がそう書いている)。
3. **その次 (発効条件待ち)** — (c) は `runs/agent_outputs.jsonl` を生む loop 再走と同時に実装する。
   起票済み。設計は `output/insights/2026-07-16_layer3-mechanism-wiring-design.md` に凍結済みで、
   本 wave は 1 行も足していない。

**B-9 は閉じていない。** 3 項のうち 1 項が済み、1 項が裁定で止まり、1 項が条件待ちである。

## この wave が新しく得た検出力 (正直な範囲)

追加した 5 本のうち、**単独で殺せる変異があるのは 3 本だけ**である。

| 新テスト | 対応する変異 | 新 tip | 変更前 commit |
|---|---|---|---|
| `test_named_screening_abort_preserves_complete_screen_payload` | MUT-A (`_view_row` が `screen` から key を落とす) | KILLED | SURVIVED |
| `test_screening_abort_variant_is_listed_in_rejects` | MUT-B (reject の `source_ref` を別 event へ) | KILLED | SURVIVED |
| `test_screening_abort_without_verify_done_builds_without_verification` | MUT-C (abort から架空 verification を捏造) | KILLED | SURVIVED |

**残る 2 本 (`..._participates_in_input_ref_multiset` と
`..._primary_mutation_fails_bijection_at_equal_count`) の検出力は、producer の
`_assert_bijection` が無条件に強制している gate と分離できない。** 確認用の pin として置き、
kill の証拠には数えない。

**3 本が塞いだ性質は、ちょうど producer が強制していない 3 つである** —
view の値の完全性、reject の `source_ref` の指し先、架空 verification の不在。
**これは 2026-08-03 の裁定が「所見として記録に残す」とした内容そのものである。**
本 wave はその所見を**テスト側から可視化しただけ**で、producer に新しい拒否は 1 つも足していない。

## 変異 matrix (DW-M08 の新旧両走)

- 新 tip `f47876014`: baseline **245 passed**、**3/3 KILLED**、期待 node 完全一致、
  SURVIVED 0 / MISMATCH 0。**各変異が殺したのは新テスト 1 本だけで、既存テストは無傷。**
- 変更前 `ac472026c`: **3/3 SURVIVED**、失敗 node 0 件。
- 生台帳 = `mutation-ledger-new-tip.json` / `mutation-ledger-pre-change.json`、
  spec = `mutation-spec-new-tip.json` / `mutation-spec-pre-change.json`。
- **段 4 の初版登録 5 件のうち 4 件は過剰決定だったので、実装後に再照準した。**
  既存テストまたは producer 自身の fail-closed が先に殺すためである。
  経緯は `s6-adjudication.md` の「変異事前登録の差し替え」。

## 注意して書くこと (表現の規律)

- **保存した材料レポートを「admitted」と書かない。** 現物は
  `admission_decision.admission_status` = `historical-not-reclassified`、
  `certifying_input` = `false`、`current_verifier_conformance` = `unknown`、epoch `E0` である。
  **top-level に `admission_status` / `classification` という key は存在しない。**
- **「任意の screening campaign について完全」と書かない。** 成立したのは名指し 1 件についてである。
- **次の 3 つを混ぜない。** (i) 記録済み 7 件について生成当時に成立した双射、
  (ii) 現行 producer で描画できる campaign 集合、(iii) 材料レポートを保存している 8 件。
  (i) と (ii) は D170 のため一致しない。
- **既存 7 件が再生成できないことを欠陥と書かない。** D170 の裁定どおりの挙動である。

## 文書

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief (段 4・6 で覆された前提には訂正注記がある) |
| `s4-ruling.md` | 段 4 裁定 (R6 は段 6 で覆された) |
| `s6-adjudication.md` | 段 6 裁定 — 敵対レビュー 2 本の所見と親の裏取り。**採番・docs の事実誤り 4 件の訂正はここが正本** |
