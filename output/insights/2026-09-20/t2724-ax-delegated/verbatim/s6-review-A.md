## レビュー結果

対象は `947fd160a..ca3907e57` と未 commit の docs 差分です。必読資料を確認し、pytest・変異実走・ファイル書込みは行っていません。Git 読取り、trailer 解析、blob の hash 照合を実施しました。

**must-fix は1件です。批准の受理式と A/X 自体に不備は認めませんが、standalone `gate_check` の既存検出力が補完されていません。**

## RA-1 — standalone gate の manifest 拒否検出が失われた

**判定: real / must-fix**

対象: [test_s8b_binding_driftguards.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-ax-delegated/orchestrator/tests/test_s8b_binding_driftguards.py:298)、同 `:327`。

旧 `test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal` は、standalone `gate_check` が binding schema の異常を `manifest-verify:` refusal に変換することを検査していました。

変更後、この node は launch validation で先に戻ります。補完した tmp repo テストは `run_block` を呼ぶため、通るのは以下の別経路です。

| 経路 | manifest 異常の処理 |
|---|---|
| 旧 standalone gate | `s8b_oracle_driver.py:534` の `verify_manifest` → `:546` の例外翻訳 |
| 新 tmp repo テスト | `:1325` の active 解決失敗 → `:379` の `_manifest_structural_refusal` |

したがって、例えば **`:546` で binding schema の `ManifestError` だけ refusal へ積まない変異**は、旧 node では検出でき、新しい実 repo node と補完2本では検出できません。schema validator 自体の検査を残しても、standalone 経路の翻訳検査の代替にはなりません。

未発効 tmp repo に対する standalone `gate_check` の補完を追加し、承認済み spec fixture を与えたうえで、binding schema refusal が集約されることを検査してください。既存6 node の名前・root・hold を変える必要はありません。

## RA-2 — trailer の受理集合は署名済み式と一致する

**判定: refuted / 修正不要**

対象: `orchestrator/campaign/s8b_ratified_freeze.py:518,528,574`。

実装は署名済みの次式そのものです。

`raw件数=1 ∧ parse値数=1 ∧ raw="AI-Agent: "+値 ∧ (値=none ∨ 構造化文法・予約語・none制約を満たす)`

現物の raw/parser 関数と `git interpret-trailers` による確認結果です。`V` は適合する構造化値を表します。

| 入力 | raw / parse 件数 | 結果・拒否段 |
|---|---:|---|
| canonical `AI-Agent: V` | 1 / 1 | 受理 |
| CRLF | 1 / 1 | raw に `\r` が残り canonical 比較で拒否 |
| 末尾空白 | 1 / 1 | parser が空白を落とすため canonical 比較で拒否 |
| 小文字 key | 1 / 1 | canonical 比較で拒否 |
| 本文中のみ、後ろに通常段落 | 1 / 0 | parse 件数で拒否 |
| 本文＋末尾に同じ `V` | 2 / 1 | raw 件数で拒否 |
| trailer の後に通常段落 | 1 / 0 | parse 件数で拒否 |
| 継続行付き | 1 / 1 | parse 値に継続内容が入り canonical 比較で拒否 |
| CAB を末尾に併記 | 1 / 1 | 受理 |
| CAB を本文に置き、末尾に適合 AI-Agent | 1 / 1 | 受理 |
| 不正な waiver 行＋適合 AI-Agent | 1 / 1 | 受理 |
| waiver のみ | 0 / 0 | raw 件数で拒否 |

**CAB・waiver の不正を、この helper は検査しません。** これは署名済み式の範囲と一致します。ただし、helper の受理を「commit message 全体が provenance 監査適合」と読むことはできません。

構造化枝は `fullmatch`、予約 product 4語、`model/reasoning=none` を検査します。`role=manager`、`product=claude`、scope 省略は裁定どおり受理します。

none 枝については、成功条件を展開すると `raw == ["AI-Agent: none"] ∧ parsed == ["none"]` となり、旧 `_is_none_commit` と同じ受理集合です。

## RA-3 — 不変防壁の変更は認めない

**判定: refuted / 修正不要**

対象: `orchestrator/campaign/s8b_ratified_freeze.py:543,615,638,1210,1320`。

production file の全 hunk を読み、既存関数のソース文字列も比較しました。変更された既存関数は **`_assert_user_commit` だけ**です。

以下は byte 不変です。

- `_is_none_commit`、`_assert_candidate_commit` と G の none 拒否。
- `_assert_user_commit` の呼び手4箇所（`:1243,1258,1273,1286`）。
- approval/pointer の diff 1 file、X^ == A。
- `_unique_introduction`、`_immutable_introductions` と `history-mutated`。

`_assert_user_commit` 内の merge・ancestry の条件も不変です。

## RA-4 — A/X の現物は契約を満たす

**判定: refuted / 修正不要**

対象: `output/s8b-freeze/approvals/7e111406…json:1`、`output/s8b-freeze/active/577537e2…json:1`。

`git show --stat`、commit/blob の `git cat-file -p`、`sha256sum` で確認しました。

| 項目 | A | X |
|---|---|---|
| commit | `a3bf67a8c` | `70e87c9c9` |
| 親 | `4114cf51b` の1件 | A の1件 |
| diff | approval 追加1件 | pointer 追加1件 |
| AI-Agent | 適合する Codex author 1行 | 適合する Codex author 1行 |
| CAB | 無し | 無し |
| record | 264 bytes、exact 4 keys | 265 bytes、exact 5 keys |

双方とも canonical JSON、末尾改行なし。作業木・author の作成先・commit blob の bytes は一致します。

- approval hash: `3787d97beb698c650153167e91d85cfbe9b2da1d87b38068427163a696821f90`
- pointer hash: `577537e223ffa6930e2b983ae384780dc3e6fd7427d7c03009a81882aaf64653`

approval filename は世代 sha、pointer filename は自身の hash と一致します。`approval_sha256` は A blob の hash、`parent_active_sha256` は null。`approver` には委任と `2026-09-20 13:2x JST` が明記されています。両作成 script の `"xb"` も現物確認済みです。

## RA-5 — 変異は検出可能だが、crash・診断差分による検出を区別する必要がある

**判定: 条件付き / 記録上の注意。現時点で追加 must-fix なし**

対象: `orchestrator/tests/test_s8b_ratified_freeze.py:2299` 以降。以下は**静的な検出予測であり、KILLED の実測ではありません**。

| 変異 | 検出根拠・帰属 |
|---|---|
| m1 | `:2299` の本文＋末尾同値は raw=2/parse=1。raw guard 削除後は受理され、helper の直接比較で検出。単一理由。 |
| m2 | 本文のみは raw=1/parse=0。guard 単純削除では `values[0]` の `IndexError`。crash kill であり受理拡大の実証ではない。 |
| m3 | 構造化2行で両件数を緩和すると、先頭 raw/value は適合して受理。helper 直接比較で検出。 |
| m4 | `:2335` の verbatim 末尾空白 case が `strip()` 比較への緩和を検出。 |
| m5 | 同 test の小文字 key case が検出。parse は1値あり、別 guard に遮られない。 |
| m6 | `:2325` の `claude-opus`。`if not match` の単純削除なら後続 `match.group` の `AttributeError`。これも crash kill。 |
| m7 | 文法には適合する予約 product 4語が検出。 |
| m8 | 文法には適合する model/reasoning=none が検出。 |
| m9 | `:2420` は A/X 同時導入も含む。混在受理後は `approval-pointer-same-commit` となり exact reason 差で検出するため、この node 単独は単一違反ではない。ただし `:2299` の `mixed` が helper を直接検査し、topology から独立して検出する。 |
| m10 | `:2360` は適合 trailer を明示確認した merge。merge guard の単独検査。 |
| m11 | `:2395` の未 merge side commit。helper 適合後の ancestry guard を検査。 |
| m12 | `:2565`。削除後も後続の `values == ["none"]` により `generation-commit-provenance` で拒否。裁定どおり reason 差による kill。 |
| m13 | `:2476`。approval にだけ extra file、A→X は正常。単一理由。 |
| m14 | `:2494`。pointer にだけ extra file、親は A。単一理由。 |
| m15 | `:2512`。双方 diff 1 file、間に commit を挿入。親条件だけを破る。 |

登録変異で静的に検出不能なものは認めません。**帰属上の留保は m2/m6 の crash、m9 の指定統合 node、m12 の診断差分です。** author S1 報告は m2/m6 の限界を明記しています。

文法同期 test（`:2380`）は pattern・flags・予約語集合を exact 比較し、`values=[value]`、`check_cab=False` で `validate_message` の戻り値3リストを `not any(findings)` により判定しています。単一値の文法・意味条件同期として有効です。parser/CAB/waiver の同期試験ではありません。

p1/p2 は `test_backoff_extended_sweep.py:1671,2025` の完全一致 assert で検出する構造です。実際の digest も新値 `92099c87…`、A/X を除いた値は旧値 `6a4ee1ef…` と一致しました。

## RA-6 — 実 repo 真値と tmp repo の no-active 集約は妥当

**判定: refuted。ただし standalone の不足は RA-1 / その他修正不要**

対象: `test_s8b_oracle_driver.py:134,301,535,4608`、`test_s8b_binding_driftguards.py:327`。

`_ACTIVATED_G1_REFUSALS` は全文2件の frozenset です。比較 helper は **件数と集合の両方**を要求し、prefix・any への弱体化や重複の見逃しはありません。

6 node の名前、`root` 指定、receipt/ratified memo 呼出しを AST で比較し、不変を確認しました。payer の ratified memo 非使用も不変です。growth hold・serialization pin・conftest は bytes 不変でした。

`_t080_repo(receipt="never-issued")` が no-active になる根拠は、receipt 欠落そのものではありません。この fixture は legacy 2 file と base だけを commit し、active pointer を作りません。そのため `resolve_active_generation:1402` が no-active を返します。

追加2本は、この実解決を mock/memo せず、`run_block:1325` の例外翻訳と manifest 構造拒否の集約を検査しています。prepare/evaluate 未呼出、output・budget・marker 未作成も要求しています。**run_block の補完としては有効です。**

## RA-7 — 親の実測と期待値は一致する

**判定: refuted / 修正不要**

対象: `test_s8b_oracle_driver.py:134`、親資料 `p3/after-g1.json:1`、`focus-held2.log`。

- `focus-s1.log`: child rc=0、**143 passed**。
- `focus-held2.log`: child rc=0、**8 passed in 103.26s**、hold 6関数の opt-in を記録。
- `after-g1.json` の拒否2行と `_ACTIVATED_G1_REFUSALS` は、件数・全文とも一致。
- `verify-active-1.json` の generation commit、世代 sha、A/X hash は現物と一致。
- P3 g1 は no-active が消え、`journal-state-invalid` に変化。`allowed:false`。
- v1 path は記録どおり4拒否です。

これらは焦点走の成功です。ログ自身も受入全走ではないと明記しており、変異実走の証拠にはなりません。

## RA-8 — 文書に小さな不一致が残る

**判定: real / nit**

対象: [旧 insight README:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-ax-delegated/output/insights/2026-09-18/t2724-freeze-g1-gen/README.md:169)、実装 commit `4114cf51b` の message。

1. README §5 は委任後の「実施の形」として手順を残していますが、approval script は依然 `"approver": "user"` です。実物には委任と裁定日があり、冒頭注記にもこの代入の読み替えはありません。script または隣接説明を実物に合わせるのが適切です。
2. 実装 commit message の「単一行の正負例13値」は、現物の **15値（none 1＋適合4＋不適合10）**と違います。履歴を書き換える必要はなく、最終記録では15値としてください。
3. driftguard `:301` の「検出力は補完テストで維持する」は、standalone 経路について RA-1 のとおり過大です。

一方、author 3報告・runbook・hooks README は、批准成功と P3 未達を区別しています。「人間性を証明した」「全 gate を受理した」「hook を変更した」という誤記は認めません。

## 総括

must-fix 一覧:

- **RA-1:** standalone `gate_check` の binding schema 例外翻訳・refusal 集約を、tmp repo の補完テストで復元する。

**採否推奨: RA-1 修正まで保留。** 受理式、不変防壁、A/X の record・commit、実 repo の exact 真値更新は採用可能です。修正後は予定の変異実走で、crash kill・診断差分 kill・受理拡大の検出を区別して記録してください。