# 段 1 brief — [T-714] CR/LF path の fail-closed 拒否

- 裁定 (確定): rulings-inbox §56 (2026-08-10「推奨通りで」) **[T-714] = (a)**。
  `_safe_path` と `read_blob_at` の両方で CR / LF を含む path を fail-closed 拒否する。
  (b) NUL 区切り移行 / (c) 現状維持 は不採用。
- base main `b0b84837` / branch `worktree-dev-wave-t714-evidence-path-ctrlchar`。
- 受入環境: Pegasus login node、`python3 tools/run_tests.py` の受入全走 (親が実施、lease 必須)。

## 実測した裁定前提 (worktree HEAD b0b84837、read-only probe)

1. `read_blob_at(REPO, HEAD, "CLAUDE.md\r")` は `"CLAUDE.md"` と**同一 blob (13812 bytes)** を返す。
   alias は実在する (裁定前提どおり)。`"CLAUDE.md\n"`・`"\rCLAUDE.md"` は missing。
2. **新事実 (裁定文の前提を部分的に精緻化):** `_safe_path` は末尾 CR / LF を**すでに拒否**する。
   ただし理由は path 検査ではなく `_nonempty_string` の `value != value.strip()` という
   **付随的** (incidental) な効果である。**埋め込み** CR / LF (`"a\nb.md"`) は受理される。
   tab・NUL も受理される。裁定 (a) の方向は変わらないため止めず、段 4 で再確認する。
3. 現行 `s8c_preregistration_evidence_contract.v1.json` に CR/LF を含む文字列は 0 件 (実測)。
4. DW-O09 pin 閉包: `FROZEN_MANIFEST` (23 件) と `condition-freeze.v1.g1.json` は
   **どちらも本 wave が触る 2 module の bytes を pin しない**。freeze record が pin するのは
   prereg markdown 系 hash と契約 semantic hash で、契約 JSON は無改変。よって DW-O10 は不成立。
5. 既存テストに `contract-path` / `contract-string` の理由語検査は 0 件。新テストは純増検出力。

## scope と不変条件

- 編集面: `orchestrator/campaign/s8c_preregistration_evidence.py` (`_safe_path`)、
  `orchestrator/campaign/s8c_preregistration.py` (`read_blob_at`)、対応テスト。docs は親。
- 受理集合の縮小は **CR / LF を含む path のみ**。それ以外の受理・拒否挙動を変えない。
- 既存テストの期待値・assert を緩めない。契約 JSON・凍結成果物・docs 本文を実装子は触らない。
- `read_blob_at` 側の拒否は caller 非依存の防壁とする (`_safe_path` を通らない将来 caller にも効く)。

## 成果物影響 (DW-G05)

実装しない場合: contract が `foo\r` を参照しても `foo` の blob を証拠として採用でき、
`EvidenceRef` の path/hash 対応、12 述語の status、activation report の digest、
それを引く certified 選択と trial ledger の参照が、実在しない path の証拠で満たされうる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 拒否は「CR (U+000D) または LF (U+000A) を含む」ことだけを条件とする。
  NUL・tab・その他制御文字は裁定範囲外とし、実装せず観測として裁定パッケージへ返す (F186 の型)。
- **(P2)** 理由語は `read_blob_at` 側 `path-control-char`、`_safe_path` 側 `contract-path-control-char`
  を新設する (既存 `contract-path` へ相乗りしない — 付随的拒否と区別できなくなる)。
- **(P3)** 分割は単一実装子とする (編集面が 2 ファイル + テストで素集合に割る利得がない)。

## 敵対検証子

受理集合が変わり正しさ防壁に触るため、軽量版にせず段 2・3 と段 6 レビュー 2 本を実施する
(`DW-C00`)。
