/dev-wave 引数 (ユーザー、2026-09-21 20:4x JST 起動、逐語):

[T-2844] mocc の X/P 計装を CCBench pin `e9e477ca` の単一の子 commit として hook 系統の submodule branch に載せ、D1603 の材料 3 点
  (候補 commit・D297 検査 GCC 2 版 + clang・波及表の点検) を揃える。入力と手順は `output/insights/2026-09-21/mocc-xp-pin-candidate/README.md`
  §3・§4・§7 (段 2 plan `verbatim/s2-plan.md` を流用して段 3 から。段 3 の prompt 下書きも同じ dir)。候補 bytes の目標は §3 (`#include <set>`
  を除き、`std::unordered_multiset` を 2 箇所、blob `e393efbf…`)。差分は Codex author (D95)。submodule の commit は、親が witlight の先例
  (`output/insights/2026-09-19/mocc-witlight-arm-run/README.md` §2・§7) の形で `commit -F` し、bundle の保全と主 checkout の submodule git dir
  への fetch までを行う。正例・負例の compute 1 走は、既存 driver `orchestrator/campaign/s3_mocc_lock_coverage.py` に候補 mode を足して行う
  (この file を編集面に明記)。push・gitlink と承認定数の更新・再承認の提示・探索開始は scope 外 (上流 PR / push は人間判断、D16/D18/D20)。Codex
  の利用枠は 2026-09-21 20:20 以降の codex 子の稼働で復帰を実測済みで、段 1 で再確認する。規律 2 は緩めない。本題の実装だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
