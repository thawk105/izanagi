# A-5 (D1100) 別 boot 再取得の実測を投入し、条件関門で止まることを実測で確定した

- 日付: 2026-09-02
- wave: `worktree-dev-wave-t2205-a5-measure`
- authority: none — 本書は投入と失敗の記録であって、性能の測定原典ではない。
  **性能値は 1 つも含まない。**
- 直前の一次資料: `output/insights/2026-09-02_t2205-a5-second-boot-measurement-job/README.md`
  (投入器と job body を作った wave)、worklog エントリ 1203。

## 何をしたか

main に着地済みの投入器を走らせ、A-5 の 2 つの workload を別ノードで同時に測る job を投入した。
**測定値は 1 つも取れていない。** 4 つの job すべてが同じ関門で止まった。

**充足の判定はしない。** [T-2212]「Pegasus の結果を A-5 の充足と見なすか」はユーザー裁定待ちであり、
本書はその手前の事実だけを記録する。旧 `linux-baremetal` 値についても、
反証・無効化・再現失敗のいずれも主張しない (前 wave が凍結した受理規則をそのまま守る)。

## 投入と結果 — 4 job、4 ノード、4 boot

| 回 | 投入元 | job | workload | ノード | boot ID | Elapse | rc |
|---|---|---|---|---|---|---:|---:|
| 1 | 隔離 worktree | 968942 | write-heavy | bnode050 | 44f2da91-becf-4ce6-875c-5beee4a8d218 | 101 秒 | 1 |
| 1 | 隔離 worktree | 968943 | balanced | bnode053 | 60961619-300a-4e6b-ab1e-b8ff57248f42 | 100 秒 | 1 |
| 2 | 主 checkout | 968954 | write-heavy | bnode034 | 70c8f7c6-c4a5-417e-971a-23e43b84730b | 98 秒 | 1 |
| 2 | 主 checkout | 968955 | balanced | bnode036 | 4f0427ea-4825-43a4-8e21-7111eb4ceed5 | 99 秒 | 1 |

- 第 1 回の投入時 repository commit = `24b31d2a37353d63a4f715ed2170d13e25df3fe3`、
  第 2 回 = `e014435471147198f68bd448025917f888f3975f`。
- 2 job は queue 待ちなしで同時に別ノードへ落ちた。**1 ノード直列ではない。**
- 4 job とも `failure.json` は `stage=backoff_sweep`, `returncode=1`, `campaign_wals=[]`。
  campaign WAL が空である = 測定は 1 反復も開始していない。
- 出力原本は repo 外 `/work/1/SFC/tanab/a5-second-boot-runs/` に残した。

### CPU 時間と経過時間について

**job 単位の CPU 時間は取得できなかった。** この機体の `qstat` は完了した job の履歴を返さず
(`-H` は無効 option)、job body も CPU 時間を記録しない。稼働中に観測できた `qstat` の CPU 列は、
経過 79 秒の時点で 0.64 秒 / 0.76 秒だった。この値は依存 build が `-j 48` で走っている最中の
ものであり、子プロセス分を集計していないことが分かる。したがって**この列から
CPU 時間と経過時間の比を論じることはできない**。

いずれにせよ**測定本体は 1 度も走っていない**ので、並列度の設計を評価できる比はまだ存在しない。
比が取れるのは関門が通ってからである。

## 止まった場所

4 job とも同一で、build でも測定でもなく、その手前の**条件関門**である。

```
condition gate rejected the driver before build/measurement:
BACKOFF_FIXED=red/preprocess-failed  (7 件)
```

- 依存 build (gflags / glog) は 4 job とも成功している。ビルド環境の問題ではない。
- 7 件の内訳は、静的 backoff の 6 値と、分母に使う inert (stock) 比較の 1 件である。
- 関門は cmake の configure には成功しており、赤はその後の
  **owner TU (`cc/silo/transaction.cc`) を preprocess する段**である。

## 投入元は原因ではない (対照で除外した)

第 1 回は隔離 worktree から投入した。job body の repo root 判定は「directory かつ非 symlink」
だけなので通るが、隔離 worktree では submodule 配下で `git worktree list` が checkout ではなく
gitdir を返すという癖があり、これが原因である可能性を疑った。

そこで**主 checkout から 1 回だけ対照を投入した。結果は同一の赤だった。**
加えて login node では、job と同じ二段の入れ子 worktree 生成が正常に成功することも実測した。
よって投入元は原因ではない。

第 1 回の log に出た `git worktree list` の rc=128 は、例外処理中に走った後片付けの二次障害であって
一次障害ではない。

## 原因の帰属 — 同日に着地した A-2 の解剖と同型

本 wave の実測中に `dev-wave-a2-condition-gate-patched-root` が main へ着地し、同じ関門を
3 層に解剖していた (`output/insights/2026-09-02_a2-condition-gate-patched-root/README.md` と
同 dir の `ruling-package.md`)。本 wave の赤はその第 2 層と同型である。

1. **第 2 層 = 今ぶつかっている赤。** owner TU の include chain にある `masstree_wrapper.hh` が
   `<config.h>` を要求し、この file は CCBench の cmake が **build 時の custom command** で
   生成する。configure しかしない関門の build tree には存在しないため preprocess が落ちる。
   A-2 側はこれを解消したが、**その修正は A-2 の driver に入っており、
   `backoff_sweep` 経路には入っていない** (main の差分は
   `orchestrator/campaign/paper_story_a2_certification.py` とその test だけ)。
2. **第 3 層 = その先で待っている、ユーザー裁定待ちの構造的な赤。**
   inert (stock) 比較は 2 つの木を別 path に置いて preprocess 出力の bytes 一致を求めるが、
   `__FILE__` を展開する code-owned header が閉包に 1 つでもあると
   `preprocess-root-dependent-builtin` で必ず赤になる。A-2 の裁定パッケージは
   `backoff_sweep` を「同じ形の driver、緑を得られるかは未実測」と名指ししている。
   **A-5 の分母はまさにこの inert 比較 (`BACKOFF_FIXED = -1`) である。**

したがって、第 2 層だけを直しても A-5 の測定は緑にならない見込みが高い。ただしこれは
A-2 側の実測と構造の議論からの**予測であって、`backoff_sweep` では未実測**である。

## この wave が実装に手を入れなかった理由

- 関門は正しさの防壁である。通すためだけの修正が偽の緑を作りうることは、A-2 の insight が
  一般化した教訓として明記している。**絶対規律 2 を緩めない。**
- 第 3 層は受理集合に触るためユーザー裁定へ返されており、まだ決着していない。
  その手前で第 2 層だけを直すと、決着後にやり直す差分になる。
- 本 wave の依頼は実測であり、関門の設計変更は含まれていない。

## 次の一手

1. **[T-2212] の裁定** (Pegasus の結果を A-5 の充足と見なすか) — 本 wave の外。
2. **A-2 裁定パッケージの「裁定してほしいこと 1」** (inert 比較を関門でどう扱うか) の決着。
   これが決まるまで A-5 の分母は関門を通らない。
3. 決着後、`backoff_sweep` 経路へ第 2 層の修正 (関門文脈での masstree 生成物の供給) を
   Codex 実装子で入れ、同じ投入器をもう一度走らせる。投入器・job body 自体に欠陥は
   見つかっていない — 4 job とも設計どおり別ノードへ落ち、契約検査を通り、
   失敗を receipt へ構造化して残した。

## 一次資料

- `/work/1/SFC/tanab/a5-second-boot-runs/` (4 job の stdout / stderr / failure.json /
  reservation.json / submit receipt)
- `output/insights/2026-09-02_t2205-a5-second-boot-measurement-job/README.md`
- `output/insights/2026-09-02_a2-condition-gate-patched-root/README.md` と `ruling-package.md`
- D1100 / D1198 / T-1999
