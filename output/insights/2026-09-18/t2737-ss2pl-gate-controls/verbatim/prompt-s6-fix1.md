単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe

## 継承する契約

段 5 author の prompt `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s5-author-prompt.md` の「試作 patch の契約」「probe の契約」「禁止」「出力形式」を**全文そのまま継承**する (読めなければ即停止)。裁定 `s4-ruling.md` が正本。既存テストの期待値を変えない (本 wave は repo の test に触らない)。tracked file を編集しない。commit / `git add` / stash / branch 操作をしない。

## 必読

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s4-ruling.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s5-author.md` — 段 5 author の最終報告
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/README-probe.md` — author の README (login 実走結果、残差 diff)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/patches/ss2pl-lock-protocol-study-define-only.patch` と `…-abort-unconditional.patch`
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/t2737_gate_probe.py`
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/external/ccbench/cc/ss2pl/transaction.cc` (stock、337-350 の `insert()`)

## 所見と fix (1 件)

**所見 F1 (real、親):** revS の S arm (tpcc target、IMPL=0/KIND=1/DLR=1/WFG=0) の `transaction.cc` 前処理 bytes は stock と 2 箇所で違う。うち `insert()` の `if (tuple != nullptr) { return Status::WARN_ALREADY_EXISTS; }` (stock) → `if (tuple != nullptr) return Status::WARN_ALREADY_EXISTS;` (現行 patch が整形、revS が継承) は**stock 本文の復元**で消える。裁定の固定復元範囲 (stock の本文・配置を戻す) に含まれる。もう 1 箇所 (`ERR` macro の `__LINE__`、stock 97 行目 vs revS 154 行目) は patch が上流に行を挿入する限り `#line` 指令でしか消えないので、**本 fix では直さない** (人為的な行番号同期はしない)。README にその旨を書く。

fix の内容:
1. revS と abort-unconditional の両 patch で、`insert()` の当該行を stock 逐語 (`{ return Status::WARN_ALREADY_EXISTS; }` の形) に戻す。他の行は変えない。2 版の差分が abort ブロックだけであることを再検算する。phase1 (YCSB, IMPL=1) 側の local 前処理一致 (`work/check_phase1_projection.py`) も再実走して変わらないことを示す。
2. README-probe.md を更新: 残差は `__LINE__` (ERR) の 1 箇所 (diff 2 行) だけになったこと、それを `#line` で消さない理由、login-precheck を再実走した結果 (S の `cmp` rc と残差行数、IMPL cell の `reason_code` と gate evidence の `root_diff_line_count`)。
3. `--selftest` を再実走し rc と PASS 数を報告。

## 出力形式

`## 総括` (必須) に: (1) 変更した file と行 (patch 2 本の該当 hunk)、(2) 2 版差分の再検算結果、(3) 再実走した login-precheck の S 残差 (行数と内容) と IMPL cell の `reason_code` / `root_diff_line_count`、(4) selftest rc、(5) 所見 F1 の closed / partial / regressed、(6) 成果物 4 点の新しい sha256 と byte 数。走らせていないものは「未実走」。
