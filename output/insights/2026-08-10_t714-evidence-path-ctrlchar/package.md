# [T-714] 証拠 path の CR/LF fail-closed 拒否 — 材料パッケージ

wave: `dev-wave-t714-evidence-path-ctrlchar` / 2026-08-10
base main: `e91bf56d` → 取り込み後 `4fd852dc` / tested tip: `fc2eff20`

## 何をしたか

裁定 (a) どおり、証拠 path の CR/LF を 2 層で fail-closed 拒否した。

- `read_blob_at` (`orchestrator/campaign/s8c_preregistration.py`): git へ渡す値を一度だけ
  exact `str` へ固定し、**その値**が CR/LF を含めば `path-control-char` で拒否する。
- `_safe_path` (`orchestrator/campaign/s8c_preregistration_evidence.py`): `_nonempty_string` の
  呼出しより**前**に CR/LF を明示拒否し、`contract-path-control-char` を返す。

受理集合の縮小は CR/LF を含む path だけである。設計判断は decisions の該当 D。

## 実測 (probe v2、blob OID / sha256 で照合)

| 入力 | blob OID | 判定 |
|---|---|---|
| `CLAUDE.md` | `1744da0e…` (13812 bytes) | 基準 |
| `CLAUDE.md\r` | `1744da0e…` | **alias 成立** |
| `CLAUDE.md\x00not-the-contract-path` | `1744da0e…` | **alias 成立 (NUL、裁定範囲外)** |
| `CLAUDE.md\t` | — (missing) | alias しない |
| `./CLAUDE.md` | — | `_safe_path` が `contract-path` で拒否済み |
| `Path("CLAUDE.md")` (非 str) | `1744da0e…` | 非文字列も通る (従来どおり) |

初回 probe (v1) は blob の**長さ**しか比べておらず「同一 blob」を実証していなかった。
段 3 のレンズ A が指摘し、v2 で測り直した (failures の F29 再発として記録)。

## 変更前の受理・拒否 (実測)

- `_safe_path` は末尾 CR/LF を**すでに拒否**していたが、理由は path 検査ではなく
  `_nonempty_string` の `value != value.strip()` という**付随的**効果である。
  `strip()` は先頭・末尾の CR/LF/tab を落とすが、NUL は落とさない。
- **埋め込み** CR/LF (`dir/in\rside.py`) は canonical かつ非 `..` なら受理されていた。

## 検証

- 受入全走: **7860 passed / 20 skipped / 475.31 秒 / rc=0** (tested tip `fc2eff20`)。
- 変異 matrix (事前登録 14 件、runner は新規 15 node に限定):
  **13 KILLED / 1 MISMATCH / SURVIVED 0 / TIMEOUT 0**。
  MISMATCH は M13 のみで、失敗 node は登録 2 件を含む 3 件だった。余分な 1 件は契約 blob を
  読む registry 統合テストで、過剰拒否が原因である (実装・テストの欠陥ではなく親の事前登録の
  不備)。初回台帳 `mutation-ledger.json` は消さず erratum として残し、期待集合を訂正した
  `mutation-ledger-m13b.json` で **KILLED (完全一致)** を得た。
- M13/M14 は**過剰拒否**を検出する正例側の変異である (受理集合を狭める wave の要件)。

## 未解決 (ユーザー裁定へ返す)

`ruling-package.md` を参照。NUL が同型に alias する (実測済み)。裁定 (a) の文言は CR/LF で
あり、承認外の gate を親が足さないため実装していない。

## 収録物

- `verbatim/` — 段 1 brief、段 2 プラン、段 3 敵対 2 本、段 4 裁定、段 5 実装報告、
  段 6 レビュー 2 本と fix 報告
- `prompts/` — 各段の prompt 逐語
- `mutation-spec.json` / `mutation-ledger.json` — 初回 (M13 の erratum を含む)
- `mutation-spec-m13b.json` / `mutation-ledger-m13b.json` — M13 訂正再走
- `verbatim/probe-sources.md` — 段 1 (v1) と段 4 (v2) の実測 probe 逐語。
  実行可能資材を repo へ置かないため markdown で凍結する (v1 は erratum の証跡)
- `ruling-package.md` — 裁定パッケージ
