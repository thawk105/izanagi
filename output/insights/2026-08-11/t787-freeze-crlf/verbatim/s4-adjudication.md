# 段 4 裁定 — [T-787] 凍結層の CR/LF fail-closed 拒否

段 3 は 2 本とも NO-GO。所見を real/refuted、採用/不採用、scope 内/外で裁定する。

## A. 裁定要とされた所見 (レンズ A 所見 1)

**real・scope 内・親裁定で解決。**「NUL の全域優先は単一 blob 内でしか成立しない」

- 事実: 履歴検証 (`validate_condition_freeze_at`) は祖先順に各 commit の evidence blob を
  hash する。祖先 A が CR/LF 契約、後続 B が NUL 契約という履歴では、現行は A を通し B の NUL で
  拒否するが、本 wave 後は A の CR/LF で拒否する。`freeze_reason_code` と pointer が変わる。
- **裁定: 不変条件 2 の射程を「単一 `evidence_contract_sha256(raw)` 呼出し内」に限定する。**
  履歴・発行 transaction 全体での NUL 優先 (二段検査) は採らない。理由:
  1. **受理集合は 1 bit も変わらない。**どちらの履歴も従来から拒否であり、変わるのは診断語だけ。
  2. **到達不能。**レンズ A の独立実測で、HEAD 祖先の distinct evidence blob は 1 個・CR/LF path は
     0 件。親も現行契約 38 位置に CR/LF/NUL 0 件を実測済み。
  3. 履歴全体で NUL を優先するには全祖先を 2 周する必要があり、D281 の単一 choke point・
     単一走査・early-return を壊す。診断語の優先順位のためにその代償は釣り合わない。
- 帰結を worklog と decisions へ明記する。「NUL 優先は 1 契約内の規則であり、履歴では
  **祖先順で最初に禁止制御文字を含む契約**が理由語を決める」と書く。
- ユーザー裁定 (a) の実体 (CR/LF を凍結層で fail-closed 拒否) は不変なので、再裁定へは戻さない。

## B. 採用する must-fix (全件 real・scope 内)

| # | 出所 | 内容 | 成果物影響 |
|---|---|---|---|
| F1 | A2 | 非 str の外側 `path` が内側 path を遮蔽する弱実装がテストを通る。`{"path":[{"path":"x\r"}]}` と深い変種 `{"path":{"x":[{"path":"x\n"}]}}` を拒否側で固定 | malformed 契約の内側 CR/LF path が凍結 hash と `protected_sha256` に束縛され、発効だけ失敗する非対称が残る |
| F2 | A3 / B2 | 文書順の pointer が固定されていない。複数 NUL・複数 CR/LF の fixture (canonical key 順と文書順が逆転する `{"z":…,"a":…}`) で最初の pointer を要求 | 凍結失敗が参照する pointer が別 node に変わり、既存 NUL の診断契約と修復対象参照が壊れる |
| F3 | A4 | 過剰拒否の正例が VT だけ。U+0085 / U+2028 / U+2029 と、文字どおりの `\r` `\n` 2 文字列を受理側で exact hash 固定 | 過剰な newline 判定が入ると有効な契約が凍結台帳・proof chain から除外され、certified 選択も発行不能になる |
| F4 | A5 | activation report の反転を、**pre-wave hash literal に正しく束縛した legacy CR/LF g1** で固定する (`_install_legacy_nul_bound_g1` と同型)。契約だけ変えると `record-protected-mismatch` が残り恒真になる | public activation report と digest の期待値が誤って記録され、受理反転を後段 `contract-invalid` が隠す |
| F5 | B1 | root 直下の exact `path` (`{"path":"x\ralias"}` CR/LF 2 node) が未検査。深さ条件で狭める弱実装が生存 | root-level CR/LF path が受理集合に残り、hash と protected hash が凍結台帳に入る |
| F6 | B3 | non-string `path` の **dict** 正例が無い (`{"path":{"nested":"x\ralias"}}`)。`is_path` を dict の子へ誤伝播する弱実装が list 正例を通す | CR/LF を含む schema 非検証入力の受理集合が狭まり、従来 hash・protected hash が変わる |
| F7 | B4 | canonicalization 順序の変異用 fixture は **escaped raw bytes** (`b'{"path":"x\\r\\ud800"}'`) で作る。生の CR/LF byte は strict JSON に先取りされる | 変異 kill が `bad-json` と混同され、検査位置の証明が成立しない |

## C. 採用する設計修正 (段 2 起草)

- **CR/LF は即 raise しない。**NUL は見つけ次第 raise、CR/LF は文書順で最初の pointer だけ保留し、
  走査完了後に NUL が 1 件も無かった場合だけ raise する。親が独立実測で裏取り済み
  (前=CR 後=NUL の契約は現行実装で後方 NUL の pointer `/conditions/11/consumer_requirement/path` で拒否)。
- 関数名は `_assert_no_forbidden_control_chars_in_contract_paths` (P2 を修正して採用)。
  親 brief の `_assert_no_control_chars_in_contract_paths` は「全制御文字を拒否」と誤読されるため撤回。
- 理由語は新語 `evidence-contract-path-crlf` (P1 の分離は維持)。NUL の理由語は不変。
- 検査位置は canonical 化の後 (D281 のまま)。detail は `repr(pointer)` のみ。

## D. 不採用・格下げ

- 「統一語 `…-control-char` へ改名」= **不採用** (既存 NUL の診断契約と D281 の参照を壊す)。
- 「二段検査で履歴全体の NUL 優先」= **不採用** (A の裁定のとおり)。
- helper 誤流用の注意 (B4 の `b"\\u0000" in raw` を CR/LF へコピーしない) = **nit だが実装子へ明記**。

## E. T-739 凍結成果物の扱い

`output/insights/2026-08-11_t739-freeze-nul/` は歴史資料であり **1 byte も編集しない**。
同 wave の `M5-nul-to-cr` は CR 受理テストを期待 node に含むが、台帳を live code へ突き合わせる
テストは存在しない (親が実測)。本 wave の変異 spec は同ディレクトリを実行対象にしない。
worklog に「過去台帳の期待 node は当時の仕様に対する記録であり、本 wave 後は再現しない」と注記する。

## F. 変異事前登録 (DW-M01)

anchor は段 6 fix 後の最終 commit で再検証する (DW-M07)。期待 node は fix 後に完全集合を再導出する。
全変異は `orchestrator/campaign/s8c_preregistration.py` の 1 ファイルを対象とし、
同じ入力を拒否する層は前後に無い (発効層は別経路で、凍結層を通らない)。

| id | 変異 | 種別 | 期待 |
|---|---|---|---|
| M1-revert-nul-only | 検査関数と呼出しを wave 前の NUL-only 実装へ exact revert | negative | KILLED (CR/LF 拒否 node 全部) |
| M2-drop-cr | CR 条件だけ削除 | negative | KILLED (`*-cr` node) |
| M3-drop-lf | LF 条件だけ削除 | negative | KILLED (`*-lf` node) |
| M4-crlf-immediate-raise | CR/LF を保留せずその場で raise | negative | KILLED (NUL 優先 node のみ) |
| M5-crlf-last-pointer | `first_crlf_pointer is None` を外し最後の CR/LF を採用 | negative | KILLED (複数 CR/LF node) |
| M6-scan-order-reversed | `reversed(...)` を外し走査順を逆転 | negative | KILLED (文書順 pointer node) |
| M7-endswith | `in` を `endswith` へ狭める | negative | KILLED (中間位置・38 位置 node) |
| M8-drop-is-path | `is_path` 条件を削除 | positive-guard | KILLED (非 path 受理 node) |
| M9-all-c0 | CR/LF 判定を全 C0 へ拡大 | positive-guard | KILLED (VT・U+2028 等の受理 node) |
| M10-schema-positions-only | CR/LF だけ既知 v1 位置に限定 | negative | KILLED (malformed・root node) |
| M11-before-canonical | 検査を canonical 化の前へ移動 | negative | KILLED (surrogate 併存 node) |
| M12-detail-repr-node | detail を `repr(node)` へ変更 | negative | KILLED (制御文字非漏洩 assertion) |

M8・M9 は**承認外の過剰拒否を検出する正例**である (DW-M01 の要求)。
M4 と「reason 統一」は 1 変異へ混ぜない (レンズ B の指摘)。reason 統一は M1 が包含するため独立登録しない。

## G. 実装子への所有分割

実装子 1 本。単独所有 = `orchestrator/campaign/s8c_preregistration.py` の検査関数と呼出し、
`orchestrator/tests/test_s8c_preregistration_core.py`。発効層・契約 JSON・docs・変異台帳・commit は
親所有で実装子は触らない。
