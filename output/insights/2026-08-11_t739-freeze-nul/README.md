# 2026-08-11 [T-739] 凍結発行・検証層への NUL 検査拡張 — 逐語と実測

裁定 (a) 「凍結発行・検証層にも NUL-only 検査を広げる」を実装した dev-wave の一次資料。
設計判断の正本は decisions、経緯の正本は worklog の該当エントリ。ここには逐語と実測値を置く。

## 何を塞いだか

`evidence_contract_sha256()` は `load_contract_bytes()` を通らないため、証拠 path に NUL を含む
契約でも hash を返し、凍結発行 (`prepare_revision`) と履歴検証がその契約を凍結記録の
`evidence_contract_sha256` / `protected_sha256` へ束縛できた。[T-714] (CR/LF) と [T-730] (NUL) が
`_safe_path` と `read_blob_at` の 2 層で塞いだ穴の、凍結層側の残りである。

## 実測 (probe は repo 外で走らせた運転用のもの。ここには逐語だけを置く)

| 測定 | 値 |
|---|---|
| `evidence_contract_sha256(NUL 入り契約)` の変更前の戻り値 | `524df6b941de655b213c86aa8fa2de7437290a89aa93bf7cbf8eb16f132f0e30` (拒否せず受理) |
| 同じ契約を `load_contract_bytes` へ | `contract-path-control-char` で拒否 |
| 現行契約の `evidence_contract_sha256` | `c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471` (変更前後で不変) |
| 既発行 g1 の `protected_sha256` | `853e6c44442780f180997b86819efaa8cbf245ae15d1a37a83e5b9a4ee99286e` (不変) |
| 実契約の `path` field 数 | 38 (required_evidence 26 + consumer_requirement 12) |
| テストへ焼いた legacy 契約の変更前 hash | `5203daa58be7cc33303ded109851d9ab9feabc34177a5aa0afef8488ccb6ba7b` |
| 走査の追加メモリ (width 10,000) | raw の 12.13 倍 (parse+canonical peak 4.7 MB、走査追加 2.3 MB) |
| 走査の追加メモリ (width 100,000) | raw の 11.56 倍 (parse+canonical peak 33.9 MB、走査追加 23.0 MB) |
| `MAX_BLOB_BYTES` | 16,777,216 (16 MiB) |

**legacy 契約の hash は実装後には再計算できない** (新しい検査が拒否する)。テストが独立オラクルを
持てるよう、親が実装前に測って literal として渡した。`verbatim/probes.md` の `oracle_probe.py` がその測定である。

## 変異

`mutation-spec.json` / `mutation-ledger.json`。**6/6 KILLED、期待 node 集合と実測が完全一致**
(両方向の差分 0)。

| id | 意図 | 期待 = 実測 node 数 |
|---|---|---|
| `M1-remove-gate` | 検査呼出しの削除 = **wave 前の実コードの形** | 47 |
| `M2-first-only` | list 走査を先頭 1 件へ切り詰め (「先頭だけ検査する」実装の検出力) | 40 |
| `M3-over-reject` | `is_path` 条件の削除 = **承認外の過剰拒否を検出する正例** | 1 |
| `M4-order` | 検査を canonical 化の前へ移す | 1 |
| `M5-nul-to-cr` | `"\x00"` を `"\r"` へ取り違え | 49 |
| `M6-nul-position` | `endswith("\x00alias")` へ (末尾 NUL しか見ない実装) | 2 |

`M6` は段 6 のレビューが見つけた検出力の穴である。追加前は 41 個の拒否テストがすべて NUL を
末尾に付けていたため、`endswith` 実装が生き残った。

## 走行

| 走行 | 結果 |
|---|---|
| 実装後の焦点実走 (core / predicates / invariant) | 231 passed / rc=0 |
| fix 後の焦点実走 (同上) | 234 passed / rc=0 |
| 受入全走 | 8210 passed / 20 skipped / 516.99 秒 / rc=0 |
| 変異 matrix | 6/6 KILLED |

実装子と fix 子は sandbox から pytest を起動できなかった (`tools/run_tests.py` が Pegasus の
dispatch preflight `qstat -Q rc=1` で停止)。両者ともテストを弱める迂回をせず事実を報告したため、
親が計算ノードで実走した。

## 逐語

- `verbatim/s1-brief.md` — 親 brief (P1〜P4 の provisional 裁定つき)
- `verbatim/s2-plan.md` — 段 2 起草 (親 P1・P2 への反対を含む)
- `verbatim/s3-lensA.md` / `verbatim/s3-lensB.md` — 段 3 敵対相談 (両方 NO-GO)
- `verbatim/s4-adjudication.md` — 段 4 裁定 (所見の real/refuted、プラン v2、変異事前登録)
- `verbatim/s5-impl-prompt.txt` / `verbatim/s5-impl-out.md` — 段 5 実装
- `verbatim/s6-review1.md` / `verbatim/s6-review2.md` — 段 6 敵対レビュー (両方 NO-GO)
- `verbatim/s6-adjudication.md` — 段 6 レビュー裁定 (must-fix 1 件採用、1 件を実測して nit へ格下げ)
- `verbatim/s6-fix-prompt.txt` / `verbatim/s6-fix-out.md` — 段 6 fix
- `verbatim/probes.md` — 親の実測 probe 3 本の逐語 (repo へ実行可能な `.py` を入れないため markdown で残す)
