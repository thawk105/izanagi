# 段 6 レビュー裁定 — [T-2027] 根クラス 2

段 6 敵対レビュー A (受理集合と正しさ境界) / B (呼び出し閉包と実効性) の所見を、
親が real / refuted、採用 / 不採用、must-fix / nit に裁定する。

## 親の独立実測

レビュー A 所見 1 を親が repo 外 probe で再現した
(`probe_review_a1.py`、対象は worktree の現物)。

| 入力 | 結果 |
|---|---|
| dependency entry なし + 実在する根 1 本 | **受理** |
| dependency entry なし + `[good, missing]` | **拒否** `current dependency prefix roots element is unavailable` |
| dependency entry なし + `[missing]` | **拒否** 同上 |
| dependency entry あり + `[good]` (file は good に実在) | **受理** |
| dependency entry あり + `[good, missing]` | **拒否** 同上 |
| dependency entry なし + 明示的な空 tuple | **受理** |
| dependency entry なし + `None` | **拒否** `current dependency prefix root context is required` |

**所見 1 は real。** production は `buildcache.py` が `effective_dependency_prefix` の
全要素を渡すので、`CMAKE_PREFIX_PATH` に stale な要素が 1 つあるだけで
fresh collection・cache hit・受領書発行が止まる。成果物 (built record・certified 選択・
レポート・台帳) がまるごと発行されなくなるので `DW-G05` の must-fix。

## 裁定表

| # | 出所 | 内容 | 判定 | 採否 |
|---|---|---|---|---|
| F1 | A 所見 1 | dependency root の解決が過剰必須化。既知欠陥 B と同型の再発 | **real** (親が実測) | **must-fix。fix 子へ** |
| F2 | A 所見 2 / B 所見 3 | 裁定 §4.5 で落とすと明記した形 B 由来 node `test_v3_dependency_prefix_hit_validation_failure_never_rebuilds` が復活 | **real** | **must-fix。fix 子が削除** |
| F3 | B 所見 2 | m06 が mask される | **real** | **採用。親が変異 spec を再照準** (親作業、fix 子の対象外) |
| F4 | B 所見 4 | 「絶対根を completion へ保存しない」の文言と `preimage.dependency_prefix` の実体が矛盾 | **real (文言の誤り)** | **採用。親が裁定文言を訂正**。identity の変更は D1220 に抵触するので不採用 |
| F5 | B 所見 1 | `**kwargs` を持つ collector が fail-closed 判定を素通りする | **real だが本 wave の純増ではない** | **不採用 (nit)**。`supports_policy` の `VAR_KEYWORD` 分岐は変更前から存在し、production collector は明示 signature を持つので成果物への影響を 1 行で書けない (`DW-G05`)。backlog へ記録 |
| F6 | A 所見 3 | origin ambiguity の負例が overlap gate に先取りされ単一理由でない | **real** | **採用 (nit)**。node は残すが「分類分岐の証拠」として数えず overlap の証拠としてのみ扱う。テスト自体は変更しない |
| — | B の変異 old 指摘 | 裁定表の m03〜m06 が逐語でなく説明文 | **real** | **採用済み**。`mutation-prereg-verification.md` で逐語 anchor へ差し替え、m05 は値を `None` へ変える形へ再照準 |

## F3 の再照準 (m06 → m06b)

`DW-M02` に従い、初回の照準 (明示条件だけの単層変異) は消さず erratum として残す。
**m06b は両層同時変異**とする。

- 層 1: `s8b_compiler_input.py` の `if is_v3 and current_dependency_prefix_roots is None:`
  ブロックを削除する。
- 層 2: 同 file の `_canonical_dependency_prefix_roots` へ入る手前で
  `None` を `()` として扱うようにする。

**kill 期待を事前登録する** (`DW-M04`)。親の probe で
「明示的な空 tuple は受理・`None` は拒否」を実測済みなので、
両層を潰すと `None` が受理へ倒れる = 受理集合が広がる向きの変化であり、
`test_v3_none_dependency_context_is_rejected_but_explicit_empty_is_accepted` が殺す。

## F4 の文言訂正

段 4 裁定 §4.2 の「**絶対根を completion や durable receipt へ保存しない**」は
**「新しい root field を completion・durable receipt・built record へ重複保存しない」**と読む。
`preimage.dependency_prefix` が絶対根を持つのは D1220 が維持を定めた既存経路であり、
本 wave はそこを変えない。**本 wave が絶対根を新たに保存する経路は作っていない**ことを
レビュー B が `s8b_binary_admission.py:269-285` と `s8b_floor_campaign.py:4435-4448` で確認した。

## 焦点走の追加 (レビュー B の指摘を採用)

親の当初一覧から漏れていた 3 file を焦点走へ加える —
`test_s8b_materialization.py`、`test_s8b_freeze_io.py`、`test_s8b_ratified_freeze.py`。
**いずれも親が既に走らせており緑である** (371 passed の群に含む)。
`test_plain_runner_coverage.py` も追加する。
