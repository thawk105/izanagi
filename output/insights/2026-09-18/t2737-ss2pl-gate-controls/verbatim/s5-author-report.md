## 総括

- [revS patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/patches/ss2pl-lock-protocol-study-define-only.patch)：86,782 bytes／SHA256 `69182355d671fb99e59ff824f092ceb7fc78eac7f5f4469b70b83a04560f85e3`
- [abort-unconditional patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch)：86,673 bytes／SHA256 `14d71e36561c611e2dbe3638be16ab6c6651cba6f328077aec169cbcf7f55224`
- [probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/t2737_gate_probe.py)：37,306 bytes／SHA256 `418448c934e4cbeb3f6d36cced22aa87526f695a644ff1711ce90f58cf832068`
- [README](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/README-probe.md)：12,792 bytes／SHA256 `7d093f1b01cfffd420dda7292c8fffa8881f38b3f64b171de995b490cd711497`
- S は**不一致、path 差以外の残差4行**（行番号・`insert()` の brace）。IMPL cell は `stock-inert-mismatch`。
- 最終 selftest：**rc=0、15 PASS**。login-precheck：**rc=0**。abort 所有権は revS 拒否／無条件除去版受理。
- 裁定の固定復元範囲を維持。S 一致は未達。warm-up・plain build・trial・計算ノード45 cell は未実走。
- 最終 git status は `?? probe-t2737/` のみ。tracked 無変更、commit なし。
- 推奨投入：`dispatch_compute.py --task generic --walltime 00:40:00 -- python3 -B …/t2737_gate_probe.py … --cells recommended`。全絶対パス引数を含む完全 argv は README に記載済み。