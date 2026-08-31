# [T-493] sort comparator 権威集合 / [T-2076] 基準 snapshot 再裁定 — 材料

wave branch `worktree-dev-wave-t2076-t493-sort-oracle-parent-reference`、実装 commit `acaed1452`。

## 構成

- `s1-brief.md` — 段 1 brief (親)。scope・不変条件・実アンカー表・provisional 裁定。
- `s4-adjudication.md` — 段 4 裁定 (親)。real / refuted 19 件、変異事前登録、裁定パッケージ。
- `s6-review-adjudication.md` — 段 6 レビュー裁定 (親)。must-fix 2 件の処理と変異登録の erratum。
- `mutation-spec.json` / `mutation-result-a1.json` — 変異事前登録と本走結果。
- `verbatim/` — 子の成果物 (plan 1、相談 2、実装 1、レビュー 2、fix 1)。

## 親が実測で確定した事実

いずれも子の主張を鵜呑みにせず親が再測したものである。

| # | 事実 | 測り方 |
|---|---|---|
| 1 | `trusted_snapshot` / `snapshot_corpus()` は実装側に不在 | 追跡 file 全件検索。hit は否定 assert 1 件のみ |
| 2 | 現行の corpus 保護は read-only arena + seccomp (T-1574、D1271 起票日より前に着地) | `git log` と TU 本文 |
| 3 | 候補文の外形検査は lambda 本体を制約しない | `sort_swo_oracle.py` の validator 本文 |
| 4 | `active_order` は報告経路に効かない | 添字は読まれない配列にのみ使われ、比較入力も出力順も position 索引 |
| 5 | 凍結 2 file の実 sha256 は manifest と一致 | `sha256sum` |
| 6 | 凍結 bytes 検査は hold 中で実効関門ではない | `freeze_verification_hold.HELD` と held check id 集合 |
| 7 | oracle test は現行では受入全走から除外されていない | 除外表が空 |
| 8 | 凍結文書の generator pin は着手前から drift 済み | 記録値と現行実装の sha256 を突き合わせ。本 wave 起因ではない |
| 9 | name 改竄は新しい権威層で先に止まる。無改変の凍結文書は通る | repo 外 probe (下記) |

### 9 の probe 出力 (逐語)

親が repo 外に置いた probe を pytest 無しで走らせた結果である。probe 本体は実装面にあたるため
repo へは入れない (親は Codex `role=author` を付けられない)。

```text
VALIDATE_SCHEMA_RAISED: entries.balanced.sort_best.name/comparator が権威集合と不一致
CLEAN_DOC_PASSED
```

fix 後に 2 node の本体を同じ方法で再現した結果は次のとおりである。

```text
NODE1_OK: freeze JSON の内容が現行 generator による機械再構成と不一致
NODE2_OK: entries.balanced.sort_best.name/comparator が権威集合と不一致
PROBE_ALL_OK
```

## 実走した検査

| 検査 | 結果 |
|---|---|
| 焦点走 (権威 test + freeze test)、fix 後 | 38 passed / 9 skipped、rc=0 |
| 焦点走 (consumer 4 file) | 202 passed / 23 skipped、rc=0 |
| glob 走査メタ test | 3 passed、rc=0 |
| 変異 matrix (3 変異) | 3/3 KILLED、`matches_expectation=true`、baseline PASSED |
| 全史 AI provenance 監査 | 7159 件、新規違反なし |
| `check_docs.py` | 違反なし |
| `spool_fold.py --dry-run` | `status=planned` |

skip 9 件は submodule 可視性に依存する既存 node で、本 wave の変更とは無関係である。
`test_verify_rejects_one_byte_freeze_tamper` もその一つのため、dispatch 走では表面化しない。
親は login node の probe で当該 node の本体を直接確認した。

## 変異の運用メモ

主 checkout の共有木は並行 wave の untracked 集合が動き続けるため、既定の
`--source-repo` では事後検査が rc=125 になった。独立 clone を `--source-repo` へ渡すと
構造的に断てる。plan-only rc=0 を確認してから detached で本走した。
