---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2844-mocc-xp-hook-branch
seq: 3
---

## 新規

### {{F:hook-commit-trailer-not-from-ruling}}. submodule の hook commit を、段 4 裁定で決めた trailer と照合せずに `commit -F` し、message の作り直しで OID が変わった [手順漏れ]

- 事象: 独立 2 例。(1) 2026-09-19 の witlight wave で、hook commit W の初版 `e0905b3d` は trailer 2 行 (author / manager) で、採否に寄与した Codex reviewer 行が無く、段 6 レビュー A の must-fix で message だけ amend した (`5b02546f`、tree 不変)。identity 検査 2 本と負例を新 OID で走らせ直した (`output/insights/2026-09-19/mocc-witlight-arm-run/README.md` §2)。
  (2) 2026-09-21 の本 wave で、候補 commit C の初版 `1035f1e3` も reviewer 行を欠いた。段 4 裁定は trailer 3 行 (author / reviewer / manager) と決めていたが、親が裁定より前に書いた message の下書きを更新しないまま `commit -F` した。下流 (author B・D297・compute) が参照する前に親が気づき、同じ tree・親で message だけ直した `68106660` に置き換えた (`output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md` §2)。実害は OID の置換 1 回で、成果物・判定は変わらない。
- 根本原因: submodule の hook commit は superproject の `check_ai_provenance.py --message-file` 検査の対象外 (submodule には provenance の導入履歴も checker も無い) で、trailer の欠落を機械では検出できない。親は commit script と message の下書きを段 4 裁定より前に用意し、裁定後に message を読み直さなかった。
- 恒久対応: memory `hook-commit-trailer-from-ruling` (hook commit の `commit -F` 直前に、message の trailer を段 4 裁定の trailer 決定と行単位で照合する。OID は下流の固定期待値・bundle・fetch に焼かれるので、照合は D297 や compute の前に行う)。
- 再発検知: submodule commit の message を `git show -s --format=%B <OID>` で出し、段 4 裁定の trailer 行と比べる。差があれば下流が参照する前に置き換える。

## 再発

### F1031

- **再発: 2026-09-21 (near miss、[T-2844] wave)** — 変異用の独立 clone を作る script に、候補 JSON の commit の 40 hex SHA を `git rev-parse` の出力から写さず、頭 9 桁 (`6fa89b563`) から後半を推測で補完して渡した。`git update-ref` が nonexistent object で拒否し、clone の途中で止まったので実害は無い。`rev-parse` の値で作り直した。同日 2 度目の再発で、既存の再発検知 (`nonexistent object` で推測 SHA を疑う) が効いた。行動規律は既存どおり (直前の `git rev-parse` の出力を逐語で写す)。
