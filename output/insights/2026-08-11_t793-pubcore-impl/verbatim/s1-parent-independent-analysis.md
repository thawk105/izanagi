# 親の独立解析 (段 2/3 の子と突き合わせる用。子には渡さない)

段 2 プランと段 3 レンズ B が同じ問いに答える。**先に親が独立に導出しておき、
食い違いを段 4 で裁定する** (子の結論をそのまま採らないため)。

## 1. D291 payload の fence 文法 (実測)

- `## D291` 見出しの 13 行後から 203 行後まで、**単一の ` ```text ` fence** が payload 全体を包む。
- **top-level key はちょうど 14 個**である (出現順):

```
decision_kind                          (= 形式)
prior_exact_byte_authority             (= 形式)
procedural_history                     (: block)
source_core                            (: block)
source_study_inputs                    (: block, nested)
document_relations                     (: block, nested 3 role)
approved_blobs                         (: block, nested 2 role)
approved_values_for_future_addendum_p  (: block, nested + value_projection の <-> 写像 9 行)
historical_candidates_rejected_for_role (: block, nested 2 role)
exact_closure                          (: block, 番号付き 1.〜6.)
operational_state_on_fold              (: block)
authority_field_note                   (: block, 散文)
role_coupling                          (: block, 散文)
operational_boundary                   (= """ 三重引用)
```

- parser はこの 14 を exact-key として要求すべきである (欠落も余剰も解決失敗)。
- `document_relations` は **3 role** (`source_addendum_b` / `publication_core` /
  `future_publication_addendum_p`)。**`approved_blobs` の 2 role とは集合が違う** —
  `exact_closure` 1. が「ちょうど 2 role」と言うのは `approved_blobs` の側である。
  ここを取り違えると正しい payload を拒否する。
- `document_relations` は「**節全体**が exact 一致」であり、散文の `note` 行も対象である。
  → 実装は field 単位の照合ではなく、**節の正規化 bytes 一致**が素直。
  正規化の単位 (行末空白・空行・indent) を決め打ちすると承認済み payload を拒否しうるので、
  「D291 の実 bytes で必ず通る」ことをテストの正例にする。

## 2. pubcore v2 §10.4 の 11 変異 — 本 wave の被覆 (親の独立導出)

| # | 変異 | 本 wave | 責務 |
|---|---|---|---|
| 1 | 適格 cluster の一部だけを公表 dataset として受理 | × | 公表 validator (別 wave) |
| 2 | 固定表から行を落とす | × | 公表 validator / renderer (別 wave) |
| 3 | `qualification_status` を再計算・申告値使用 | × | source validator + 公表 validator (land 2 / 別 wave) |
| 4 | 共分散の対角だけを使う | × | 統計本体 (別 wave) |
| 5 | Holm の `<` を `≤` へ緩める | × | 統計本体 (別 wave) |
| 6 | 実行時に BH / Simes へ切替 | × | 統計本体 (別 wave) |
| 7 | **`ledger_kind` に閉集合外の値を名乗って新しい `k = 1` を取る** | **○** | 本 wave (i) |
| 8 | 同一 dataset への第 2 の公表 core の結果を受理 | **△** | 本 wave は台帳側 (create-only / ordinal 非解放) のみ。dataset identity の照合は公表 validator が要る |
| 9 | **追補 P が §9 の閉集合の外の field を設定** | **○** | 本 wave (iv-b) |
| 10 | stress check が縮退 dataset を除外・再抽出 | × | 統計本体 (別 wave) |
| 11 | 公表側結果を certified 選択の入力へ渡す | × | consumer 結線 (別 wave) |

**したがって「本 wave が §10.4 を機械執行した」とは書けない。** 11 中 2 件 + 1 件部分である。
worklog にはこの表のまま書く (実装したふりをしない)。

## 3. (ii) marker gate の非自明な点 (親の設計上の発見)

`check_docs.py` には既に `_check_literal_placeholder_guard` (F36) があり、
`LITERAL_PLACEHOLDERS = ("<反映>", "<受入結果を反映>", "<受入全走結果を反映>")` を
`docs/worklog.md` / `docs/archive/worklog-*.md` / `output/insights/**/*.md` から raw text で走査する。
`__UNRESOLVED__` は**この 3 語に含まれない**ので (ii) は純増検出力である。

**ただし「marker をどこにも書いてはならない」という gate にしてはならない。**
`output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md:36-37` に
marker が**正当に**存在する (草案であり、未確定であることを示す marker そのものが仕様)。
全面禁止にすると land 済みの正当な草案で即座に赤になる。

正しい gate は条件付きである — **「canonical な承認 payload が pin する文書」「承認対象として
提出される文書」が marker を含んでいたら赤**。すなわち gate の入力は
(a) 承認 payload / fragment が pin する三つ組の集合、(b) その各 blob の bytes、である。
草案のまま insights に置かれているだけの文書は通る (これが「通る正例」になる)。

## 3b. D291 の前提の独立実測 (`verify_d291_triples.py`、全件一致)

| 対象 | 結果 |
|---|---|
| `source_core` (`88d68f91…`) | **OK** 32135 bytes、digest 一致 |
| `source_study_inputs.addendum_a` (`622bd786…`) | **OK** 54776 bytes、digest 一致 |
| `approved_blobs.publication_core` (`66934dda…`) | **OK** 42414 bytes、digest 一致 |
| `approved_blobs.source_addendum_b` (`25a66d20…`) | **OK** 17888 bytes、digest 一致 |
| `required_core_ref` を `symbolic:F_p` = `b13b7ea8` で解決 | **OK** 42414 bytes、digest 一致 (承認 blob と同一 bytes) |
| working tree の 2 承認文書 | **両方とも承認 bytes と一致** (編集されていない) |

`exact_closure` 2. の非承認 blob 主張も**そのまま再現した** — 全 reachable commit の tree を
走査した結果、`publication-core-v2.md` の unique blob は 2 件 (承認 1 + 非承認 `45d83e7a…` 1)、
`addendum-b-v2.md` は 3 件 (承認 1 + 非承認 `0ea71fff…` / `2313a261…` 2)。D291 の記載と一致する。

→ **D291 の前提は覆らない。**段 4 で再裁定を要する新事実は §8.1 の `family_root` 同一性主張のみ。

## 4. D292 との整合で気をつける点

本 wave の gate は **deny を増やす方向にのみ**働く。
`require_*` 系の関数名にし、`allow_*` / `can_submit_*` / `is_admitted` のような
**許可を返す名前を作らない**。戻り値も `True` を返さず `None` を返して例外で落とす形にする
(既存 `require_approved_addendum_a_fields` と同型)。
「gate が通った = 投入してよい」と読める戻り値を作らないこと。
