# [T-2545] 段 4 裁定 — D1881 の名指し実装

親が段 2 プランと段 3 敵対相談 2 本 (レンズ A = 正しさ境界 / レンズ B = 整合と実効性) を
real / refuted で裁定し、plan v2 と変異事前登録を確定する。
裁定 inbox の再走査: wave 開始 `61e0e9c4a` から `main` は 1 commit も進んでいない。
D1881 を上書き・停止する新裁定は無い。

## 採用する所見 (real)

### R1 — 完了主張を「発行器を置いた checkout」に限定する (レンズ B3 / B5)

**採用。** この変更で閉じるのは「新 issuer API を経由する発行が、事前登録の名指し root
以外を拒否する」ことに限る。閉じないものを明示する。

- `p3_s4_loop.py` の `require_b4_proposal_registry_binding` と
  `load_b4_prerun_publication` の受理条件は**不変**。呼び手の root を受ける経路は残る。
- 別 checkout の名指し場所で正しく発行した bundle を、別 checkout の呼び手が
  絶対 root で指定する経路は残る。
- ⇒ **`B4_PRERUN_NON_GUARANTEES` の `publication_under_a_different_root_is_not_prevented`
  は本 wave では変更しない。** 系全体の非保証として依然真である。
  T-2546 へ引き継ぐときは、同列が receipt bytes (`p3_b4_prerun_issuer.py` の receipt payload と
  strict loader の完全一致検査) と材料レポートの provenance hash に束縛されている事実を
  併記する。「文言だけの訂正」ではない。

### R2 — 関連 fixture の追従を scope 内とする (レンズ A4 / B4、段 2 プランの裁定候補 1)

**採用し、scope 内に入れる。** 新検査は発行器の全呼び手に効くので、次の 3 file の
publication 発行 fixture は追従しないと「関連テストを通す」完了条件を満たせない。
これは新機構の追加ではなく既存 fixture の追従であり、依頼の scope 外項目 (gate・検査・台帳・
一般化の追加) に当たらない。

- `orchestrator/tests/test_p3_b4_raw_record_producer.py`
- `orchestrator/tests/p3_b4_proposal_binding_support.py`
- `orchestrator/tests/test_p3_b4_material_report.py`

**禁止する解き方:** 新検査を無効化して downstream を通す。期待 reason を置換して隠す。
公開 API へ repository root や事前登録 path の引数を足す
(**呼び手が指定できる時点で D1881 が閉じる穴が再び開く**)。

### R3 — 実 repo 解決の正例を 1 本足す (レンズ A3 / B7)

**採用。** tmp repository へ `_REPOSITORY_ROOT` を差し替える fixture は、
文書読取・抽出・比較は通すが `__file__` 由来の実 repository 解決を検査しない。
差し替えを使わず、発行もしない検査を 1 本足してこの射程を埋める。

- `_REPOSITORY_ROOT` が実 repository を指し、そこの実事前登録文書から
  名指し値がちょうど 1 本抽出され、期待値と一致することを確認する。
- publication は作らない。`output/` へ何も書かない。
- 成立条件は「文書を同梱する source checkout から import したとき」と明記する。
  installed-package 配置への対応機構は作らない (B7 の是正どおり、提案しない)。

### R4 — 不変条件の文言を訂正する (レンズ A1 / A7 / A8 / A9)

親 brief の次の 4 点を訂正して plan v2 の不変条件とする。

1. (A1) 「既存の拒否 reason を 1 つも変えない」ではない。正しくは
   **「受理集合は縮小のみ。既存 reason がそのまま残るのは、正常な宣言かつ名指し root の場合に限る」**。
   別 root では新 reason が先行するので、そこでの拒否 reason は変わる。
2. (A7) 「`output/` 配下 0 件ゆえ既存 publication の再発行・無効化は発生しない」は探索範囲を
   超える。旧発行器は `output/` 配下に限らず任意の絶対 root を受けたので、
   **「この worktree の `output/` 配下では固定名成果物 5 種を 1 件も確認しなかった」**に限定する。
3. (A8) §5 への行追加が落ちる地点は `_SECTION5_LABELS` との exact 集合一致ではなく、
   その手前の**行数検査**である。結論 (行追加不可) は変わらないが機構の帰属を訂正する。
   集合比較が発火するのは行数を保ったまま未知ラベルへ置換した場合。
4. (A9) §6 の test pin は見出し全文ではなく**抽出終端の prefix**。
   「現行 §6 見出しの後ろへの今回の追記は §5.1.1 の pin を変えない」に限定し、
   「任意の項目追加が全検査上安全」とは書かない。

### R5 — admission の文書全体 pin を閉包へ加える (レンズ B1)

**採用 (記録のみ)。** `orchestrator/campaign/p3_b4_admission_record.py` は
事前登録文書**全体**の SHA-256 と、発効 commit / HEAD の文書 bytes 一致を要求し、
`p3_b4_closed_critic.py` がそれを sidecar へ転記する。§6 への追記で文書全体の hash は変わる。
**ただし base / sort / trigger の admission record は現 worktree に 1 件も実在しない**ため、
無効化される対象が存在しない。再発行は要らない。閉包の記載漏れとして insight へ残す。

### R6 — descendant 負例を帰属証拠から外す (レンズ A10)

**採用。** 名指し root を未作成にしたときの descendant は、新検査が無くても
`_ensure_new_publication_root` の親ディレクトリ不在で `PUBLICATION_ROOT_INVALID` になる。
単一理由性が立たないので、受理集合縮小の証拠には**既存の親を持つ sibling** を使う。
descendant は reason 優先順序の確認にだけ残してよいが、変異の kill 根拠にはしない。

## 採用しない所見 (refuted)

- (A2) 新述語の恒真化 — 期待値を呼び手の root からでなく独立した文書から作るので自己一致にならない。
  正例と負例が同じ文書を使うことは恒真化の原因にならない。段 2 プランの形を維持する。
- (A3 の前半) 提案 fixture が新検査を迂回する — 迂回しない。射程の限定だけが要るので R3 で埋める。
- (B6 の変更要求なし) §6 配置 — 両レンズが支持。配置は変えない。

## plan v2 (確定)

段 2 プランを次の差分で確定する。それ以外は段 2 プランどおり。

1. 事前登録 `docs/phase3-b4-reflux-ablation-preregistration.md` の `## 6.` 見出しの直後、
   既存 9 条件の前に名指しを 1 本入れる。既存 9 条件の番号・本文・見出し逐語は変えない。
   値は `output/b4-prerun-publication` (repo 相対)。
2. 発行器 `orchestrator/campaign/p3_b4_prerun_issuer.py`:
   新 reason `PUBLICATION_ROOT_NOT_PREREGISTERED`、モジュール定数 `_REPOSITORY_ROOT`、
   厳密照合 helper、`root = _canonical_absolute_path(...)` の呼び出しが閉じた直後で検査。
   `_ISSUER_PATCHES` の逐語錨 3 本を壊さない。`CHANGE_CLOSURES[ISSUER]` は据え置く。
   公開 API に引数を足さない。`.resolve()` を呼び手 root へ適用しない。
3. test: 段 2 プランの負例・宣言不正 3 種・既存正例の付け替えに加えて、
   **R3 の実 repo 解決の正例 1 本**を足す。
4. **R2 の 3 file の fixture 追従**を同じ変更単位に含める。
5. 所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` へ追加 nodeid を親の実測値で登録する。

## 変異事前登録 (DW-M01)

実装前に登録する。位置は実装後に確定し、単一理由性 (同じ入力を拒否する層が前後にも内側にも
無いこと) を実装後に確認する。確認できない候補は登録から落とし、実効 gate へ再照準する。

| ID | 変異 | 期待 kill | 単一理由性の担保 |
|---|---|---|---|
| M1 | 新 helper 呼び出しを削除 | 別 root (既存の親を持つ sibling) の負例 | 予定群・result mapping は有効。sibling の親は実在させ `PUBLICATION_ROOT_INVALID` を併発させない |
| M2 | 完全一致比較を prefix 一致へ緩める | prefix sibling の負例 | 同上。境界なし prefix 一致だけが差になる |
| M3 | 宣言数検査 `!= 1` を `< 1` へ緩める | 宣言 duplicate の負例 | 呼び手 root は正しい名指し場所に固定し、root 不一致を併発させない |
| M4 | 照合対象を `line.strip()` にする | 宣言 ambiguous (先頭空白) の負例 | 同上 |
| M5 | 新検査を `_ensure_new_publication_root` の後ろへ移す | sibling 負例の副作用 assertion (root 検査呼び出し 0 回) | reason は同じなので、観測は委譲 spy の呼び出し回数で行う |

**承認外の過剰拒否の正例 (DW-M01 の縮小 wave 要件):**

| ID | 正例 | 意味 |
|---|---|---|
| P1 | 名指し root での完全 bundle 発行が通り、既存 consumer の再検証も通る | 縮小が正規経路を巻き込んでいない |
| P2 | 名指し root 配下の別 future result path が許される既存挙動が残る | 既存の受理が失われていない |
| P3 | R3 の実 repo 解決検査 | 名指しが実 repository の実文書から到達可能 |

## 段 5 の分割

実装面は素集合 1 単位 (発行器 + 上記 test 群 + 3 file の fixture 追従 + 所要台帳) なので
Codex 実装子 1 本。docs 本文 (事前登録の 1 本) は親が書く。
