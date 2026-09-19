# 候補 identity の事前照合 (親が login で実測、2026-09-19 22:04 JST、build 無し)

方法: wave worktree (main `657e1e5a7`、ccbench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`) の submodule を base に
`patchharness.checkout(PIN)` で scratch worktree を切り、`patchharness.applied("patches/silo-backoff-fixed.patch", PIN, ccbench_dir=<scratch>)`
の内側で `source_digest.resolve_evidence(Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": N}), PIN, ccbench_dir=<scratch>, cxx="g++")` を呼んだ。
`_BASE` = `backoff_sweep._BASE` (`NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0`)。現行 patch の sha256 先頭 = `a5e0710c3f767447`。

| 候補 | src_token (実測) | source_bytes_sha256 (実測) | genome_sha256 | tracked_paths |
|---|---|---|---|---|
| fixed-5 (BACK_OFF=1, BACKOFF_FIXED=5) | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` | 同左 | `7deff2b013e46cedfdb192b0e356b2912cc0eb745b00f7a041c759ec244fc8ea` | `cmake/Options.cmake`, `include/backoff.hh` |
| fixed-10 (BACK_OFF=1, BACKOFF_FIXED=10) | `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d` | 同左 | `e44bf7ae9d29dee35f7b9966b5484b3db07ab1c10547a5588d89d12ad172a16c` | 同上 |
| (対照) fixed-5、patch 無し | `stock` | `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` | — | — |

## 既存記録との照合

| 既存記録 | 値 | 本実測との関係 |
|---|---|---|
| T-1998 事前登録 v1 §5 target `source_bytes_sha256` (2026-09-10 導出、patch 適用下、`cxx="g++"`) | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` | **fixed-5 と完全一致** |
| T-1998 §4.2 が「受理しない」と書いた patch 無しの値 | `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` | 対照 (patch 無し) と一致 = 手順の再現性確認 |
| A-2 attempt `t2364-20260907b` rr50-fixed5 `src_token` (certification.json、`output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json`) | `21def77c944b1b855ea2da5516a7280858957888ec1b0644b80d9ae51e73c98a` | **fixed-5 と不一致** |
| A-2 同 rr5-fixed10 `src_token` | `955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9` | **fixed-10 と不一致** |

## 不一致の理由 (git で実測)

- A-2 の izanagi source commit は `31ec382a7841e188e46f93e8de4261c964facfb2` (稿 §2.3)。`git merge-base --is-ancestor 91a5bfca3 31ec382a7` は偽 = A-2 は
  patch の改訂 `91a5bfca3` (2026-09-07 23:39 JST「静的 backoff の表現可能上限を 999 から 9999 マイクロ秒へ広げる」) を含まない旧 patch で建てられた。
- `91a5bfca3` の `patches/silo-backoff-fixed.patch` の差分は 1 行: `now_backoff` の三項式の**最終 else 分岐** (生値 ≥ 3000 の復号) を
  `% 1000` から `- 2000` へ変更。`BACKOFF_FIXED / 1000 == 0` (5・10 µs) が選ぶ最初の分岐 `static_cast<double>(BACKOFF_FIXED)` は不変。
  commit message: 「生値 0〜2999 の 3 領域 (定数、対称 modulo、二値) の復号結果は数値的に不変であり、stock 枝・骨格・マーカー・待機ループは 1 byte も変えていない」。
- したがって: fixed-5 は T-1998 v1 の target と **bytes まで同一**。fixed-10 は A-2 rr5-fixed10 と **同 genome・同数値挙動 (5/10 µs の分岐は不変) だが source bytes は `91a5bfca3` 分だけ異なる**。A-2 の src_token をそのまま期待値にはできない。

## runner が起動条件として固定すべき期待値 (親案)

- fixed-5: `src_token` = `source_bytes_sha256` = `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12`
- fixed-10: `src_token` = `source_bytes_sha256` = `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d`
- どちらも `stock` や別値なら fail-closed。A-2 の旧 token は「履歴上の対応」として記録に併記し、期待値にしない。
