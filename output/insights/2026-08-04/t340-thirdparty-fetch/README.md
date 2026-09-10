# [T-340] Pegasus third-party source の pin 検証つき取得経路 — 逐語と実測

2026-08-04 の dev-wave (branch `worktree-wave-t340-thirdparty-fetch`) の逐語・台帳・実測を凍結する。
可変状態の正本は worklog 末尾であり、本ディレクトリは再現用の一次資料である。

## 何を作ったか

`tools/pegasus/fetch_third_party.py` — masstree / mimalloc / googletest を repo 外の永続 cache へ
pin 検証つきで取得し、そこから worktree 内 staging へ offline で供給する CLI。
`fetch` (network) / `hydrate` (offline) / `verify` (offline) / `verify-deps` (offline)。

**この helper は任意の operator preflight であり、取得の権威ではない。** 最終判定は凍結された
`submit_silo_ladder_rung1.sh` / `silo_ladder_rung1.sh` の pin/clean 検査のままである。
取得経路は submit receipt にも evidence にも値として漏れないため、
「由来が台帳から追える」とは主張しない (段 3 レンズ A 所見 4 の指摘を受けた scope 格下げ)。

## ファイル

| ファイル | 中身 |
|---|---|
| `brief.md` | 段 1 brief (前提実測つき) |
| `s2-plan.md` | 段 2 codex プラン |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 2 レンズ (計 18 所見) |
| `s4-ruling-planv2.md` | 段 4 裁定 + プラン v2 + 変異事前登録 |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-lensC.md` / `s6-lensD.md` | 段 6 敵対レビュー 2 レンズ (計 13 所見) |
| `s6-fix.md` / `s6-fix2.md` | 段 6 fix 子の報告 |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 matrix 本走 1 回目 (M1〜M15) |
| `mutation-spec-m15.json` / `mutation-ledger-m15.json` | M15 の再照準本走 (単層 + 両層同時) |
| `resource-class/` | 資源分類の実測 (runbook §7.0 の専用 scope + memory.current sampling) |

## 実測 1 — 共有 FS の directory create-only publish (pegasus02、2026-08-04)

| base | renameat2(RENAME_NOREPLACE) | os.link(dir) | rename→空 dir | rename→非空 dir | mkdir 排他 |
|---|---|---|---|---|---|
| `/home/SFC/tanab` | EINVAL | EPERM | 置換成功 | ENOTEMPTY | EEXIST |
| `/work/1/SFC/tanab` | EINVAL | EPERM | 置換成功 | ENOTEMPTY | EEXIST |
| `/tmp` | ok | — | — | — | — |

runbook は `/home` だけを EINVAL として記録していたが **`/work` も同じ**である。
calibrator の link+unlink fallback は directory には使えない (`os.link` が EPERM)。
したがって publish は `os.mkdir(dest)` の排他予約 + `os.rename(stage, dest)` とした。

## 実測 2 — `~/github` の 5 clone (2026-08-04)

5 本とも pin 一致・clean・origin 一致。ただし **gflags と glog は shallow clone**
(`.git/shallow` が実在) であり、masstree/mimalloc/googletest とは管理形態が異なる。
これが「cache root の既定を `gflags_source_path` の親から導く」案を却下した決め手である。

## 実測 3 — 資源分類 (runbook §7.0、規範値 512 MiB)

certified peak = 観測ピーク + max(25%, 128 MiB)。

| 経路 | 観測ピーク | certified peak | 分類 |
|---|---|---|---|
| `fetch` (cold: 3 本を GitHub から clone) | 94 MiB | 222 MiB | local-ok |
| `fetch` (warm: 検査のみ) | 12 MiB | 140 MiB | local-ok |
| `hydrate` | 61 MiB | 189 MiB | local-ok |
| `verify` | 12 MiB | 140 MiB | local-ok |
| `verify-deps` | 12 MiB | 140 MiB | local-ok |

`submit_silo_ladder_rung1.sh` が `unknown` に分類されている理由 (login で外部 3 repo を clone) と
同族の経路だが、実測して規範値未満だったので `local-ok` とする。
**pin が変われば入力サイズが変わるので再分類が要る** (`tools/README.md` の発火命令 4)。

## 実測 4 — consumer 接続の実証

`hydrate` の出力 `source_root` は
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` であり、凍結 submitter の
`THIRD_PARTY_ROOT` と一致する。hydrate 後に **凍結 submitter を `--prepare-third-party-only` で
実走して rc=0** を得た (clone 分岐は destination 実在により通らない)。

## 変異 matrix

- 1 回目: KILLED 10 / MISMATCH 4 / SURVIVED 1。
  **MISMATCH 4 件 (M02, M10, M12, M14) はすべて過剰決定**であり、
  「expected but not failed = none」— 登録 node は全件赤で、冗長 gate が追加で赤くなっただけである
- **SURVIVED 1 件 (M15) は真の検出漏れだった。** `_hydrate` 末尾の全 destination 再検証が
  内側の publish 後検証を mask し、rc と stderr に差が出なかった。実際に消える挙動は
  rollback だけである。初回結果は erratum として残す
- 再照準後: M15 (単層) / M15C (両層同時) とも **KILLED**、単一理由で一致
