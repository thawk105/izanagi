---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t407-ruleops-binary-blob
seq: 2
---

## {{D:ruleops-inventory-skip-non-utf8}}. RuleOps inventory は decode 不能な blob を読み飛ばして件数だけ出す

**決定:** `tools/ruleops.py inventory` は、選択した対象のうち strict UTF-8 として decode できない
blob を `items` から除外し、除外した件数を出力の根の `skipped_non_utf8` (整数) へ常時出す。
D99 決定 (2) の選択 scope (直下の `orchestrator/tests/test_*.py` と `output/insights/**` の
tracked regular blob) は変えない。変えるのは inventory item の外延と出力の形である。

**除外条件は decode 不能だけ**とし、suffix、path 名、JSON / Python としての妥当性、NUL の有無、
size を除外理由にしない。件数は `--kind` 適用後の集合の中で path 単位に数え、同じ blob OID が
複数 path にあればそれぞれ数える。**除外した path は出さない。** 根の key が 1 つ増えるため
inventory schema を `ruleops-inventory/v2` へ上げる。`inspect`、候補 ledger、mutation receipt、
insight candidate 本文の非 UTF-8 fail-closed は変えない。

**理由:**
- 列挙が仕事のツールが、対象 1 件の decode 失敗で列挙全体を停止するのは、安全を生まない
  fail-closed である。同ツールは規約文書の検査が目的であり、測定の生出力は元々対象外である。
- 除外条件を decode 不能に限れば検査の意味は落ちない。suffix や path で判定すると、
  同じ bytes が置き場所で扱いを変える二義的な受理集合になる。
- 件数を出さずに黙って落とすと、人間が `items` を対象の全数と誤解する。件数は「一覧が不完全である」
  という警告として最小かつ十分である。ただし**どの対象が落ちたかは示さない**ため、
  `--kind test` の値が正のとき `items` を「直下 test を全数確認した」根拠にしてはならない。
- 同じ版名が 2 つの形を指す状態を作らないため schema を上げる。repo 内に v1 を pin する consumer、
  保存済み inventory JSON、JSON Schema はいずれも存在しないことを 2 レンズが独立に確認した。

**却下した選択肢:**
- 非 UTF-8 blob を `artifact_format="binary"` として一覧に載せる — 一度は親が推奨し承認も得たが、
  記録済みの裁定と食い違うため撤回した。測定の生出力を退役候補の母集団へ入れる意味がない。
- 保存形式の変更または該当証拠の作り直し — commit 済み証拠の bytes は同じ evidence tree の
  receipt が sha256 で pin しており、書き換えると自己整合を壊す。producer だけを直しても
  既存 blob は残るため停止は解消しない。
- 選択 scope を狭めて evidence を外す — D99 決定 (2) の対象範囲そのものの変更であり、
  別の裁定を要する。
- 件数を出さずに読み飛ばす — 人間レビュー用の一覧が signal なしで不完全になる。
