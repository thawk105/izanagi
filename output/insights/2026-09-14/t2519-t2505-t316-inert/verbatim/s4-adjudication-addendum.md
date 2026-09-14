# 段 4 裁定の追補 — 本 wave の実測は既知失敗型の独立 3 例目である (2026-09-14)

段 7 の記録を書く前に親が `docs/failures.md` を引いたところ、**本 wave が「新しく見つけた」と
書きかけていた構図は、既に 2 件の独立記録を持つ既知の失敗型だった**ことが分かった。
段 4 裁定 (`s4-adjudication.md`) はこの事実を見ずに書かれている。本追補がそれを訂正する。

## 親の手順上の誤り

**段 1 の一次資料に `docs/failures.md` を含めなかった。** `CLAUDE.md` 絶対規律 6 は
「監査・レビューのレンズ設計時は `docs/failures.md` の型タグを攻撃面に含める (過去に起きた型の
再発検査)」と定めている。段 1 でも段 3 のレンズ設計でも failures を引かず、段 3 の 2 レンズにも
渡さなかった。そのため「原因を静的に特定した」という親の分析も、段 3 の 2 レンズの検証も、
**既知の 2 例をまったく参照しないまま行われた**。実測 2 で得た直接証拠は正しいが、
「初めて分かった」という位置づけは誤りである。

## 既知の 2 例

### F934 (独立 2 例目として既に記録されている)

> **F934. patch 由来 define の条件関門が、patch を materialize しない driver では構造的に通らない
> [恒真ゲート] [誤前提]**
>
> - 事象: 認定 launcher `tools/pegasus/certify_calibration.sh` と同じ argv で
>   `orchestrator.campaign.condition_meaning_gate` を実走したところ rc=2、`admitted=false` で、
>   2 アームとも red だった。`supply-effectuation` は `configure-failed` で detail が CMake の
>   「Manually-specified variables were not used by the project: CCBENCH_BACKOFF_FIXED」…
> - 根本原因: `CCBENCH_BACKOFF_FIXED` は `patches/silo-backoff-fixed.patch` が
>   `cmake/Options.cmake` と `include/backoff.hh` へ供給する define である。launcher は pin された
>   CCBench の素の detached worktree をビルドし、patch を materialize しない。
>   **供給していない define を渡しているので、供給と実効化を見る関門は正しく拒否している。**
>   D1198 が義務化した関門の射程に、patch を当てない driver が入っていた。
> - **独立 2 例目である。** 同じ `runtime-meaning` 赤を A-1 driver
>   (`orchestrator/campaign/paper_story_a1_paired.py`) で先に記録している。

**t316 はこの型の独立 3 例目である。** 構図は完全に一致する — 素の CCBench 木、
gate が足す `-DCCBENCH_BACKOFF_FIXED`、未使用変数警告、`configure-failed`。

### F855 (未使用変数の流用という側面)

> **F855. condition gate は configure 成功でも stderr 非空を red にし、driver が渡した未使用 CMake
> 変数の警告で compute 走が停止した [手順漏れ]**
>
> - driver の `_common_configure_args` が silo driver に無い `-DRULE_LAUNCH_COMPILE=` を渡していた
>   (gflags / glog の install build から流用)。
> - 根本原因: gate は fail-closed で正しい。driver 側が「CCBench の project が使う変数だけを渡す」
>   という gate の暗黙契約を知らず、**driver は gate の status しか出力しないため理由が見えなかった**。
> - 恒久対応: driver から未使用変数を除去 (fix-2)。

**t316 も `-DRULE_LAUNCH_COMPILE=` を gflags / glog の install build から流用している。**
実測 2 の警告本文に `RULE_LAUNCH_COMPILE` が載ったのは、F855 とまったく同じ経路である。

## 裁定の訂正

| # | 段 4 の記述 | 訂正 |
|---|---|---|
| 1 | 原因の構図を本 wave の発見として扱っていた | **F934 の独立 3 例目、かつ F855 の同型再発である。** 新しい F は作らず、両 F へ「再発: 2026-09-14」を追記する (skill 自己改善契約の routing 1) |
| 2 | 「直し方の設計択一を新規 T として起票する」 | **維持するが、D1864 と F934 を参照して族の 3 例目だと明記する。** D1864 は「patch が供給する define を、その patch を materialize しない経路で新しい protocol へ広げない。`BACKOFF_FIXED` はこれに当たる。**silo の現行挙動は据え置き、扱いはユーザー裁定へ返す**」と定めており、t316 はその「silo の現行挙動」側にある driver である。起票は D1864 の据え置き対象の具体化として書く |
| 3 | decisions fragment の {{D:t316-inert-unreachable-on-stock-tree}} | **F934 / F855 / D1864 への参照を本文へ入れる。** 「新規に判明した」という書き方をしない |
| 4 | insight README の「新しい失敗型ではない」節 | A-2 insight だけでなく **F934 と F855 を名指しする**。独立 3 例目であることを書く |

## DW-G03 (族一般化には独立 2 例) の適用

F934 が既に 2 例を記録し、本 wave が 3 例目である。したがって族一般化の条件は**満たされている**。
ただし **本 wave では族一般化を実装しない。** 理由は次のとおりで、段 4 の scope 裁定を変えない。

- 依頼が「本題の実測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示している。
- 族一般化の中身 (patch を materialize しない driver すべてから、供給していない define を外すか、
  関門の射程から外すか) は D1864 が「ユーザー裁定へ返す」と定めた論点そのものであり、
  親が実装で先回りしてよい領域ではない。
- 3 例目を記録して族一般化の前提が揃ったことを台帳へ残すのが、本 wave の正しい終端である。

## 本 wave の残る価値 (既知型の再発であっても失われないもの)

1. **T-2505 / T-2519 が求めた「t316 実経路での計算ノード実測」は、本 wave が初めて行った。**
   既存の t316 受領証 2 件 (2026-08-10) には `condition_gates` が 0 件である。
   F934 / F855 はいずれも別 driver の記録であり、t316 の実経路を測っていない。
2. **F855 が「driver は gate の status しか出力しないため理由が見えなかった」と書いた問題を、
   t316 について閉じた。** 拒否理由の `detail` が job stderr に出るようになった。
   F855 の恒久対応は「login で `_require_condition_gate` と同じ関数列を呼ぶ probe で読む」
   だったが、本 wave は **計算ノードの実走そのものから読めるように**した。
3. 未使用変数が **4 件** (F934 が挙げる `CCBENCH_BACKOFF_FIXED` に、t316 固有の 3 件が加わる) で
   あることを実測した。
