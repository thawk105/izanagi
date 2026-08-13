# 2026-08-13 t1014-t1001-guards — 受入形 `--dist` 拒否と worktree 占有走査 checker

wave branch: `worktree-dev-wave-t1014-t1001-guards`
ユーザー裁定: 2026-08-13 rulings 第 9 回 #11 (T-1014) と #15 (T-1001)

## この directory の中身

| file | 内容 |
|---|---|
| `spec-a.json` / `ledger-a3.json` | 変異 A (受入形 `--dist` 拒否)。5/5 KILLED |
| `spec-b.json` / `ledger-b.json` | 変異 B の**初回**。MUT-B1 が MISMATCH (probe) |
| `spec-b.json` / `ledger-b2.json` | 変異 B の再走。4/4 KILLED |
| `spec-c.json` / `ledger-c.json` | 変異 C (docs 契約検査)。2/2 KILLED |

`spec-b.json` は再登録後の内容である。初回の期待 node は `ledger-b.json` の
`expected_nodes` に記録が残っている。

## 変異の要旨

### A — `tools/run_tests.py` の受入形 `--dist` 拒否

| id | 壊す箇所 | 結果 |
|---|---|---|
| MUT-A1 | 早期拒否を削り **wave 前の形** (既定 loadgroup 先置き + ユーザー引数後勝ち) へ戻す | KILLED (5 node) |
| MUT-A2 | `--dist=` 等号綴りの取り出しを削る | KILLED (1 node) |
| MUT-A3 | `--dist` を `_NONSELECT_VALUE_OPTIONS` から外す | KILLED (6 node) |
| MUT-A4 | 非空 `PYTEST_PLUGINS` の受入形状除外を削る | KILLED (1 node) |
| MUT-A5 | 明示 `--dist loadgroup` まで拒否する (**過剰拒否の正例**) | KILLED (1 node) |

MUT-A3 は fail-open の形である。allowlist から外すと `_is_acceptance_run` が偽になり、
拒否ではなく黙って partial 走行へ降格する。したがって 6 node が同時に落ちる。

### B — `tools/check_worktree_occupancy.py`

| id | 壊す箇所 | 結果 |
|---|---|---|
| MUT-B1 | cmdline channel を削る (cwd only へ) | KILLED (9 node) |
| MUT-B2 | containment を文字列 `startswith` にする | KILLED (1 node) |
| MUT-B3 | cwd permission の uid 分割を握り潰す | KILLED (2 node) |
| MUT-B4 | 判定不能を rc=0 へ写像する | KILLED (2 node) |

base commit に file 自体が存在しないため、B の変異はすべて post-implementation mutant である。
「wave 前へ戻す」変異は成立しない。純増は「base に checker が存在せず、占有中 worktree の
削除を止める機構が無い」という構造差で示す。

### C — `tools/check_docs.py` の checker 実在検査

| id | 壊す箇所 | 結果 |
|---|---|---|
| MUT-C1 | 契約 pin を **wave 途中で恒真だった 2 literal 包含**へ戻す | KILLED (3 node) |
| MUT-C2 | 検査自体を削る | KILLED (4 node) |

MUT-C1 が本 wave の敵対レビューが摘出した恒真形そのものである。`rc0` という literal は
同じ command の §1 に既に 2 回出現しており、実質 1 literal しか効いていなかった。

## 親が実データで測った値

`docs/spool/` の fragment と、fold 後の worklog エントリを正本とする。要点だけ再掲する。

- `/proc` の channel 別到達可能性 (Pegasus login node): 全 1984 PID のうち cwd が読めるのは 49、
  permission denied が 1935。cmdline は 1984 件すべて読める。
  自分と同じ uid でも cwd が読めないのは `sshd` と `(sd-pam)` の 2 件。
- 是正前の checker は未占有ディレクトリで rc=2、issue 1947 件、JSON 109,071 bytes。
  是正後は rc=0、issue 0 件、JSON 156 bytes。
- cwd が対象外で argv だけが対象を指すプロセスを rc=1 / `sources=["cmdline"]` で検出できることを
  live probe で確認した。これは裁定 #15 が名指しした codex worker の形である。
- 受入全走 = 10748 passed / 65 skipped / 0 failed (146.99 秒、計算ノード)。
