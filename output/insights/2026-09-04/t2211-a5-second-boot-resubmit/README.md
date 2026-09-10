# A-5 (D1100) の再投入 — T-2226 着地後も同じ条件関門で止まり、理由の本体を config.h 不在と確定した

- 日付: 2026-09-04
- wave: `worktree-dev-wave-t2211-a5-resubmit`
- authority: none — 本書は投入と失敗の記録であって、性能の測定原典ではない。
  **性能値は 1 つも含まない。A-5 は未充足のままである (D1525)。**
- 直前の一次資料: `output/insights/2026-09-02_t2211-a5-second-boot-measurement-attempt/README.md`
  (前回の投入)、`output/insights/2026-09-02_t2205-a5-second-boot-measurement-job/README.md`
  (投入器と job body を作った wave)。

## 何をしたか

[T-2226] (inert 比較の差の分類、D1611) が main に着地したので、[T-2211] の指示どおり
**同じ投入器を、着手直前の local main (`1b7822110`) からもう 1 回走らせた。**

```
bash tools/pegasus/submit_a5_second_boot_backoff_sweep.sh \
  --output-parent /work/1/SFC/tanab/a5-second-boot-runs
```

**結果: 2 job とも前回 (09-02) と同じ条件関門で止まり、測定値は 1 つも取れていない。**
本 wave は実装に手を入れていない (実装面の差分 0)。

**充足の判定はしない。** D1525 (2026-09-03 ユーザー裁定) により、Pegasus で取れた結果を
D1100 の「別 boot の再現」と読み替えることはせず、**A-5 は未充足のまま残す。** 今回は値が
取れていないので、この明記は「値が取れても充足と書かない」という前提の確認でもある。

## 投入と結果 — 2 job、2 ノード、2 boot

| job | workload | ノード | boot ID | 開始 | Elapse | rc | 止まった段 |
|---|---|---|---|---|---:|---:|---|
| 977066.nqsv | write-heavy | bnode026 | 6224b0b3-3a7e-41e3-a0f9-2b299b93dfd9 | 21:57:07 JST | 137 秒 | 1 | backoff_sweep (条件関門) |
| 977067.nqsv | balanced | bnode027 | e746ff51-e68b-4468-b130-1dfe64dfe6a0 | 21:58:58 JST | 138 秒 | 1 | backoff_sweep (条件関門) |

- 投入時刻 21:55:36 JST、group `a5-second-boot-backoff-sweep-20260904T125536Z-519045`、
  投入元は隔離 worktree (`.claude/worktrees/dev-wave-t2211-a5-resubmit`)。
- job が照合した repository commit = `1b7822110c54536f82ecab8d058d7a9253bfd3ce`、
  CCBench gitlink = `511c9538e4e8efa54b45cda62e72389ed3b706ec`。job 完了まで branch へ commit していない。
- 2 job とも `failure.json` は `stage=backoff_sweep`, `returncode=1`, `campaign_wals=[]`。
  campaign WAL が空 = 測定は 1 反復も開始していない。前回 09-02 の 4 job と同一の形。
- 依存 build (gflags / glog、`-j 48`) は 2 job とも成功している。compiler は GNU 11.4.0。
- 今回は write-heavy が先に走り balanced が約 2 分 queue で待った (同時刻に別 job が 1 本走っていた)。
  09-02 は 2 job が同時に落ちた。投入器の fan-out 自体は前回と同じ。
- 出力原本は repo 外 `/work/1/SFC/tanab/a5-second-boot-runs/` に残し、stdout / stderr /
  failure.json / reservation.json / submit receipt の写しを本 directory に置いた。

## 止まった場所と理由コード (規律 3: 構造化して残す)

driver の拒否文は 2 job とも同一である。

```
condition gate rejected the driver before build/measurement:
BACKOFF_FIXED=red/preprocess-failed  (7 件)
```

7 件 = 静的 backoff の 6 値 (`2, 5, 10, 25, 50, 100`) と、分母に使う inert (stock) 比較
(`BACKOFF_FIXED = -1`) の 1 件。いずれも `supply-effectuation` arm の `preprocess-failed` である。

### 理由の本体 — login node での再現で確定した

`backoff_sweep.py` の拒否文は `macro=status/reason` しか持たず、各 record の `evidence.detail` を捨てる。
そこで login node (pegasus、g++ 11.4.0、cmake 3.22.1) で **同じ形の supply arm を 1 回だけ再現**し、
record の全文を `login-node-gate-reproduction.json` に写した (使い捨て script は
`login-node-gate-reproduction.py.txt`。repo へは入れていない)。

- 再現の形: `patchharness.checkout` で CCBench pin `511c953` の scratch worktree を 2 本作り、片方に
  `patches/silo-backoff-fixed.patch` を当て、`capture_define_inputs(patched, stock_root=stock)` を
  **configure_args なし** (= `backoff_sweep.py` と同じ) で呼び、`BACKOFF_FIXED=10` と `-1` の
  `evaluate_define_supply_effectuation` を走らせた。gflags / glog は
  `/work/1/SFC/tanab/izanagi-a2-deps` を `CMAKE_PREFIX_PATH` で与えた。
- 結果: **2 request とも `red/preprocess-failed`**。detail は次のとおり (path を省略)。

```
cc/silo/include/../../../include/masstree_wrapper.hh:20:10:
fatal error: config.h: そのようなファイルやディレクトリはありません
   20 | #include <config.h>
compilation terminated.
```

これは A-2 の解剖 (`output/insights/2026-09-02_a2-condition-gate-patched-root/README.md`) が
**第 2 層**と名付けた赤と同一である。owner TU `cc/silo/transaction.cc` の include chain にある
`masstree_wrapper.hh` が `<config.h>` を要求し、この file は CCBench の `cmake/ThirdParty.cmake` が
**build 時の custom command** で生成する (`add_custom_target(masstree_build ...)`)。関門は configure
しかしないので、関門の build tree には存在しない。

**login node の再現は診断であって job の記録ではない。** ただし compiler の版 (GNU 11.4.0) は job と
同じであり、失敗箇所は compiler や依存 prefix に依らない include の欠落なので、計算ノード上の
7 件も同じ理由と見てよい。

### なぜ T-2226 の着地では直らなかったか

[T-2211] の項は「塞いでいた [T-2226] の実装が着地したので順序待ちから外れた」と書いていたが、
これは**関門の 3 層のうち第 3 層 (inert 比較の root path 依存) にだけ当たる**。

- T-2226 (commit `4ad505f2c`) が変えたのは inert 比較の**差の分類**で、preprocess が成功した後に
  効く検査である。preprocess 自体が落ちる第 2 層より後段にある。
- 第 2 層を A-2 経路で直した修正 (`buildcache.prepare_masstree_fetchcontent` を関門文脈で 1 度呼び、
  `-DFETCHCONTENT_BASE_DIR` を configure_args で渡す) は
  `orchestrator/campaign/paper_story_a2_certification.py` の `_condition_gate_family_context` に
  入っており、`backoff_sweep.py` の `_require_backoff_condition_gate` には入っていない。
  後者は `capture_define_inputs(source_root, stock_root=stock_root)` を configure_args なしで呼ぶ。
- 09-02 の insight は「第 2 層だけを直しても第 3 層で止まる見込み」と予測していた。今回はその手前の
  第 2 層が backoff_sweep 経路で**未修正のまま**であることを、予測でなく実測で確定した。

したがって順序待ちの前提が 1 つ欠けていた: **[T-2226] は必要条件であって十分条件ではない。**

## この wave が実装に手を入れなかった理由

- [T-2211] の依頼は「投入と記録だけ、新規 gate・台帳・一般化は scope 外」である。
- 関門は正しさの防壁であり、通すためだけの修正が偽の緑を作りうることは A-2 の insight が一般化した
  教訓である。第 2 層の修正は「検査した木と build する木を一致させる」不変条件を伴う設計変更で、
  Codex `role=author` の実装子と敵対レビューを要する (絶対規律 2 を緩めない)。
- 本 wave の親は実装面を編集しない (dev-wave の凍結境界)。

## 次の一手

1. **`backoff_sweep` 経路へ第 2 層の修正を入れる別 wave** (Codex 実装子)。A-2 と同じ形
   (関門文脈で masstree FetchContent を 1 度用意し `-DFETCHCONTENT_BASE_DIR` を configure_args で
   渡す) が最短。A-2 の教訓「検査した木と build する木を一致させる」を不変条件にする。
2. その着地後に同じ投入器をもう 1 回走らせる。**そこで初めて第 3 層 (D1611 の差分分類) が
   backoff_sweep 経路で実測される。** 緑を得られるかは未実測である。
3. 値が取れても A-5 は未充足のまま (D1525)。成果物にはその旨を書く。

## 副産物 (scope 外、記録のみ)

- 投入器の受領証 `submit.jsonl` の `job_id` field には qsub の出力全文
  (`Request 977066.nqsv submitted to queue: gen_S.`) が入る。09-02 の受領証も同じ形で、今回新規ではない。
  job ID だけを取り出す consumer は今のところ無い。
- balanced job (977067) の後片付けで superproject 側の `git worktree remove` が rc=128
  (`'.../job-repo/external/ccbench' is not a working tree`) を返した。`prune` は rc=0 で、job 終了後の
  login node で `git worktree list` に `/scr/` の残骸は無い。09-02 の 2 回目 (主 checkout 投入) の balanced も
  同じ rc=128 だったので投入元に依らない。一次障害でなく、失敗経路の後片付けの二次的な癖である。

## 一次資料

- `/work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260904T125536Z-519045*`
  (原本) と本 directory の写し
- `login-node-gate-reproduction.json` / `login-node-gate-reproduction.py.txt`
- `output/insights/2026-09-02_a2-condition-gate-patched-root/README.md` (3 層の解剖)
- `output/insights/2026-09-04_t2226-inert-root-diff/README.md` (第 3 層の修正)
- D1100 / D1525 / D1611 / D1198
