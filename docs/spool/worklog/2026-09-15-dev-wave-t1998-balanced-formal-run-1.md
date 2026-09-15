---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t1998-balanced-formal-run
seq: 1
title: [T-1998] 依頼の三工程は着手前に完了済みで、着地後の main から認証判定を再現して持ち越しを閉じた (docs のみ、branch worktree-dev-wave-t1998-balanced-formal-run、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- ユーザー依頼は「既存 balanced 1job submitter で計算ノードへ投入し、結果を回収して既存 consumer で
  解析する。2026-09-10 に人間専任が解除され AI が担当すると裁定済み (D1874 の正式測定認可と事前登録は
  保つ)。認可を再度求める必要はない。事前登録前の生値は混ぜない。再利用する job body の global prune
  が別 invocation と干渉しうる旨が過去に訂正記録として残っているので、投入前に現況を確かめる。
  規律 2 を緩めない。本題の投入・回収・解析だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」。
- **依頼の三工程は着手前にすべて完了していた。** [T-2557] が 2026-09-13 に投入・回収し
  (job `995755.nqsv`、Elapse 712 秒、8 genome すべて commit、abort 0 件)、consumer の拒否 2 件を
  [T-2589] が 2026-09-14 に是正して (`4d7cd40a9`)、**再測定なしで同じ保全成果物を `accepted` へ**
  認証していた。結果は `docs/paper-story/2026-09-14.md` にも取り込み済みで、双子の [T-2557] は
  worklog 1477 で閉じている。**[T-1998] だけが「次の一手」に持ち越しのまま残っていた記帳漏れ**で、
  D1938 と worklog 1433 の本文がどちらも両者を同一の実行手番と書いている。
- **親は投入器を起動しなかった。** 事前登録 §7 が「投入は 1 回だけ」と凍結しており、認証済みの
  試行が 1 本ある状態で 2 本目を出すと、どちらを主張へ使うかの規則が事前登録に無い。事後に選べば
  prospective の看板が下りる。これは D1874 が「事前登録の前に取れた値を後から主張へ入れない」と
  定めて守ろうとしたものと同じ性質の毀損である。新しい対照を測るなら新しい事前登録が要る。
- **本 wave の純増は、着地後の main での再現実測 1 点だけである。** [T-2589] の認証は自分の wave
  branch 上で行われ、同 README §6 は受入全走が 3 回とも非帰属の輻輳で止まり land できていないと
  書いていた。したがって「着地後の main の consumer が同じ判定を返すか」は未実測だった。
  main `0600887d9` の作業木から保全成果物を `consume_balanced_stock_inline_pair` へ通し、
  `accepted` / ratio 1.1122537536191646 / improvement_percent 11.225375361916456 と
  両腕 5 標本・median・変動係数・identity が **[T-2589] の記録と全桁一致**することを実測した。
  一次資料は `output/insights/2026-09-15/t1998-landed-main-recheck/README.md`。
- **投げ文の前提が 2 点覆った。** (1) sizing の正本として挙げられた
  `orchestrator/tests/test_paper_story_a1_balanced_sizing.py` は A-1 の 3 workload 横断実験用の
  sizing certificate を検査するもので、本測定の sizing ではない。balanced の腕対応は T-1998 と同じ
  対だが、D1993 項 6 が両者を 1 つの横断実験として集計しないと明記している。本測定の sizing は
  事前登録 §6 と consumer の `EXPECTED_SAMPLE_COUNT = 5`。A-5 job body は A-1 sizing を参照しない。
  (2) 干渉リスクとして挙げられた job body の global prune は現況では不在で、
  `tools/pegasus/a5_second_boot_backoff_sweep.sh` に `prune` の文字列は 1 件も無い。T-2354 が
  2026-09-09 に撤去しており、事前登録 §4.1 が固定する digest はその撤去後の bytes の値である。
  2026-09-13 の実測済みの試行もこの撤去後の job body で走っている。D1804 の限界節が残した競合経路は
  現行 job body には存在しない。
- **親は provenance 監査の過程で保全成果物の生の `result.json` を読んでおり、再投入しないという
  判断を下す前に効果量を見ている。** 判断の根拠は値ではなく事前登録 §7 の凍結文言だけだが、
  見た事実は隠さず記録する。
- **危うく重複測定を出すところだった。** 出力親 directory を作ろうとして既存の成果物に当たるまで、
  親は済を疑っていなかった。持ち越し stub は「未了」に見えるが、双子タスクの完了で終端している
  ことがある。着手前に一次資料で済を照合する既知の作法が、そのまま発火した事例である。
- 工数: codex 子 0 本。軽量版 (設計択一なし・正しさ防壁に触れない・受理集合を変えない) と
  裁定し、段 2・3 と段 6 の review 子を省いた。実装面の差分がゼロなので変異 matrix は DW-S04 により
  免除、受入全走は免除していない。
- セッション異常 2 件。`EnterWorktree` tool が
  `Could not read the repository git config to neutralize filter drivers` で 2 回とも失敗した
  (`git config --list --local` は rc=0 で読める)。手動 `git worktree add` と
  `EnterWorktree --path` で回避した。`git worktree add` 自体も 21 分かかり、同時刻に別 session
  5 本が同じ repo へ worktree add を走らせていた。`dev_wave_submodule_init.py` は 1 回目
  `runtime-io-failure: update-no-fetch` で落ち、2 回目 rc=0 で成功した。いずれも競合由来である。

## 次の一手差分

### 完了

- [T-1998] balanced stock-inline 対の正式測定は [T-2557] が投入・回収し、[T-2589] が consumer を
  是正して認証済み。着地後の main から再解析しても `accepted` / ratio 1.1122537536191646 /
  improvement_percent 11.225375361916456 が全桁再現した。事前登録は v1 のまま、bytes 不変。
  事前登録前の生値は主張へ混ぜていない。一次資料は
  `output/insights/2026-09-15/t1998-landed-main-recheck/README.md`。
  remaining: none
  base: ef3ca39dee11f0d3576f928233e9abfa305989306eeca8d2f0277fb27f905244
