# Cicada の selective precheck を Silo の EVOLVE-BLOCK へ着想移植できるか — カタログカード試作 (No-Go)

- **wave 種別:** Stage 7-(i)（T番号未発行、研究-only）。`docs/phase3.md` 後続段 item7 Group D (i)
  「TicToc/Cicada の最適化技法のうち1つをカタログ化試作」の一歩目そのもの。D32 (`docs/decisions.md`
  711-748 行) が定める「前提/効果/競合」の三つ組カード化を初めて実行した。
- **範囲:** external/ccbench/cc/cicada から技法を 1 件選び、Silo (`external/ccbench/cc/silo/`) の
  EVOLVE-BLOCK 実編集面 (`cc/silo/transaction.cc` の `validationPhase()` 内 write_set_ ロック順序
  comparator、および `include/backoff.hh` の `Backoff` クラス) へ前提が成立するかを判定した。
  **コード変更・ベンチマーク・性能値の実測は一切行っていない。** 「cross-protocol 対応が完了した」
  という主張もしない。
- **基準 commit:** 41c33fe5 (local main、wave 開始時は 46fbce3d だったが段7記録前に別 wave
  [T-1434] の着地で main が進行。docs-only の新規ファイル追加のみで衝突なし)。
  branch `worktree-dev-wave-tictoc-cicada-catalog-card`。
- **前例:** `output/insights/2026-08-20_tictoc-cicada-cross-protocol-task-definition.md` の
  Group D (i) をそのまま実行した。段7 全体の発火条件 (D32 = 8b+層3後) は本カード作成時点でも
  未成立のままであり、本カードはその発火を主張しない — D32 原文が明記する「カタログ化の成果物は
  移植を見送っても層3の説明生成に流用できる」という独立価値に基づく実行である。

---

## 1. 選定した技法

**Cicada の tuple 単位 commit-streak gated selective precheck**
(`Transaction::precheckInValidation()`)。

段2 codex plan (read-only, reasoning=max) が tictoc/cicada 双方から候補 3 件を file:line 付きで
起草し (Cicada selective precheck、TicToc timestamp history、TicToc validation loop fusion)、
段3 敵対相談 2 レンズ (A=技術正確性、B=D32/I5/信頼境界(規律6)/scope 遵守) が並列で攻撃した。
本カードの技法選定・No-Go 判定は、段2 提案 + 段3 の所見 (A: 所見4件、内 real 2件は用語精緻化・
refuted 2件は判定支持。B: 所見7件、全件 refuted=問題なし) + 親 (Claude) 自身の一次ソース直接確認
(下記引用の主要箇所) の三重確認を経て、段4 で親が裁定した。

当初の作業仮説 (「Cicada の適応制御はグローバルな楽観/悲観モード切替であり、Silo の `Backoff` と
同じ適応パラメータ軸に乗るのでは」) は、段2 の一次ソース確認で **反証された** — 実際の機構は
tuple 単位のカウンタに基づく per-tuple スキップであり、グローバル負荷シグナルではない。反証の
過程で見つかった別の技法 (`precheckInValidation()`) をカタログカード化の対象に選び直した。

## 2. 出典 (file:line)

- `external/ccbench/cc/cicada/include/transaction.hh:247-293` — `precheckInValidation()` 本体。
- `external/ccbench/cc/cicada/include/tuple.hh:24-38` — `Tuple` クラス。`atomic<uint64_t>
  continuing_commit_` (32 行目) と `atomic<Version*> latest_` (30 行目) を保持。
- `external/ccbench/cc/cicada/include/cicada_op_element.hh:53-57` — `WriteElement::operator<`。
  `precheckInValidation()` 冒頭の `partial_sort` が使う comparator で、`storage_`/`key_` のみを
  比較する静的順序であり、動的な競合値やカウンタは comparator に現れない (Claude 直接確認済み)。
- `external/ccbench/cc/cicada/include/version.hh:25-38` — `Version{rts_, wts_, next_, status_}`
  の連結リスト。
- `external/ccbench/cc/silo/include/tuple.hh:12-36` — Silo の `Tidword`
  (`{lock:1, latest:1, absent:1, tid:29, epoch:32}` の単一 64bit bitfield) と `Tuple`
  (`Tidword` + `TupleBody` のみ、履歴・連結リストなし。Claude 直接確認済み)。
- `external/ccbench/cc/silo/transaction.cc:444-475` — Silo の read validation (`validationPhase()`
  Phase 2)。`Tidword` を `loadAcquire` で 1 回読み、epoch/tid 一致とロック状態だけを確認する
  (Claude 直接確認済み。version chain も per-tuple カウンタも参照しない)。
- `external/ccbench/include/backoff.hh:16-121` — Silo が使う `Backoff` クラス。
  `Backoff_` という 1 個のグローバル `atomic<double>` を、直近区間の commit throughput の勾配で
  増減させる (Claude 直接確認済み)。tuple 単位の状態は持たない。

## 3. 前提 (precondition)

`precheckInValidation()` が成立するために必要な、Cicada 側のデータ構造・不変条件:

1. **tuple ごとの連続 commit カウンタ** (`continuing_commit_`)。commit のたびに増分し、abort で
   リセットされる (段2 plan・段3 lensA が引用、`transaction.cc:687-720`・`transaction.hh:343-367`。
   本カードでは未直接確認 — 下記「見なかったことにしていない前提」参照)。
2. **MVCC version chain** (`rts_`/`wts_`/`next_`/`status_` を持つ `Version` の連結リスト)。
   precheck は `latest_` から辿って `committed`/`deleted` 状態の版を探す。
3. precheck を省略しても、後段の完全な version consistency check が別途走ること。
   このカードで扱うのは「事前検査の一部を条件付きで省略する」設計であり、正しさ判定そのものを
   弱める提案ではない (絶対規律2 を侵さない前提)。

## 4. 効果

ソースコードのコメント (`transaction.hh:248-251`) は「低競合下では 2 つの最適化 (write set の
`partial_sort` と precheck) がオーバーヘッドになるため、直近 5 回連続で commit していれば
adaptively に省略する」と説明する。

**ただし、実装を直接確認するとコメントと挙動には乖離がある**: `partial_sort`
(`storage_`/`key_` の静的順序、`cicada_op_element.hh:53-57`) は常に実行され、
`continuing_commit_` の閾値判定で条件的に省略されるのは内側の version consistency precheck
だけである (`transaction.hh:254-256` vs `:263-267`)。段3 lensA が指摘し、Claude が直接確認して
支持した所見。「両ステップを adaptively omit する」というコメントの記述は不正確である。

効果自体はソースの設計意図を読み取ったものであり、**性能を実測した主張ではない**。

## 5. 競合

- Silo の write-set ロック順序は、write_set_ 全体を `sort()` した後で `lockWriteSet()` を実行する
  構造である (`cc/silo/transaction.cc:388-408`, `:437-447`)。`partial_sort` (部分整列) を
  そのまま持ち込むと、ロック取得順序の対象範囲が変わり、既存の write-set 全体ロック順序の不変条件と
  衝突しうる。
- Silo の read validation (`444-475`) は `Tidword` 1 個の `epoch`/`tid`/`lock` だけを見る。
  precheck 相当の判定を持ち込むには、version chain か同等の履歴を新設する必要があり、
  既存の単一版設計そのものを変えることになる。
- Silo の `Backoff` (`backoff.hh:16-121`) はグローバル 1 値 (`Backoff_`) を throughput 勾配で
  更新する機構であり、tuple 単位の commit streak を直接表現できない。

## 6. Silo 側で前提が成立するか

**不成立。** 判定は 3 段 (親の一次確認、段2 codex plan、段3 codex 敵対レンズ 2 本) を通じて
一貫している。

- 対象となる EVOLVE-BLOCK 実編集面は `cc/silo/transaction.cc` の write-set ロック順序 comparator
  であり、`Tidword` 単体 (`cc/silo/include/tuple.hh:12-36`) しか持たない Silo には
  `continuing_commit_` に相当する per-tuple 状態も、`Version` 連結リストに相当する多版構造も
  **現行の実編集面の中に存在しない**。
- `include/backoff.hh` のもう一方の実編集面はグローバル 1 値の適応バックオフであり、
  tuple 単位の判定条件を表現できないため、こちらも前提の受け皿にならない。
- 前提を成立させるには EVOLVE-BLOCK の外側 (`Tuple`/`Tidword` のデータ構造そのもの) を拡張する
  必要があり、これは「合成枝の中身への変異」という現行 Phase 3 の変異境界を超える設計変更になる。

## 7. No-Go 理由

1. **データ構造の不在。** per-tuple カウンタと multi-version chain という 2 つの前提が、
   Silo の単一版 `Tidword` 設計と根本的に相容れない。両者を橋渡しするには EVOLVE-BLOCK の外側で
   `Tuple` の構造自体を変える必要があり、「既存 gate 一式がそのまま効く」という D32 が期待する
   b2 の安価な入口の前提から外れる。
2. **既存機構との軸不一致。** Silo に既にある適応機構 (`Backoff`) はグローバル 1 値であり、
   Cicada の技法が要求する tuple 単位の粒度と一致しない。「同じ適応パラメータ軸に乗る」という
   当初仮説は、精査の結果、支持されなかった。
3. **正しさ境界への配慮。** 前提を無理に緩めて (例: グローバル閾値で代用する等) 移植を成立させると、
   read validation が本来検出すべき mismatch を見逃す方向に効きうる。絶対規律2 に照らし、
   前提の緩やかな解釈で Go 判定へ倒すことはしない。

本判定は **この 1 技法・この 1 実編集面ペアに限定**する。Cicada の他の技法 (下記「見送った候補」)
や、EVOLVE-BLOCK の実編集面が将来拡張された場合の判定はここに含まれない。DW-G03 (族一般化には
独立2例) の精神に従い、「Cicada の技法は Silo に移植不可能」という全称化はしない。

## 8. 論文に使える限定的な記述

> Silo の commit プロトコルは単一版タプル (64-bit `Tidword` bitfield) を前提とする一方、
> Cicada の commit-streak gated selective precheck は per-tuple の連続 commit カウンタと
> multi-version chain に依存する。両者のメタデータ前提は根本的に異なり、コード片の直接移植は
> 成立しない。この不一致は、最適化を「前提・効果・競合」の三つ組へ抽象化して初めて特定できる
> ものであり、素朴なコード比較では見えにくい。

（訂正: 初版は上記不一致を CCBench 著者の I5「異なる実装の混合は深い分析には不適切」の
具体例として引用していたが、これは誤り。I5 は実装者間の技術力・ワークロードハックの差が
プロトコル間の性能比較を不公平にするという比較妥当性の問題であり、本カードが扱う
「技法が要求するデータ構造を移植先が持たない」という構造的非互換性とは別の論点である。
ユーザー指摘により 2026-08-22 に訂正。）

上記は 1 事例の観察であり、「TicToc/Cicada の最適化は Silo に移植できない」という一般化の根拠には
ならない。論文で使う場合は本カードが扱った技法・実編集面のペアに限定して引用すること。

## 9. 見送った候補 (段2 plan が検討・不採用)

- **TicToc の timestamp history** (`pre_tsw_` による旧版保持、`tictoc/transaction.cc:376-400`)。
  Silo の tuple に相当する履歴領域が無く不成立。加えて段3 lensA の指摘により、TicToc 内でもこれは
  常時機構ではなく `#if TIMESTAMP_HISTORY` の compile-time feature であることが判明した
  (`tictoc/transaction.cc:381-400`, `:508-510`)。
- **TicToc の validation loop fusion** (`tictoc/transaction.cc:357-367`)。段2 plan は「Silo に
  既に同等の機構がある」と判定したが、段3 lensA の精査により、TicToc 側は write-set の融合のみで
  read-set 側は別走査のままと判明し (`tictoc/transaction.cc:357-368`, `:369-452`)、Silo 側
  (`max_wset_`/`max_rset_`/`maxtid`、`cc/silo/transaction.cc:145-193`, `:449-475`, `:563-582`)
  も「完全に同等の融合」ではなく「必要な走査中に最大値を畳み込むという抽象技法として独立に
  実現済み」と表現を修正した。前提は成立するがカタログカードとしての新規性が乏しいため不採用。

## 10. 今後の芽 (段3 lensA が発見、今回は未検証)

段3 lensA (技術正確性レンズ) が、射影外の一次ソース走査から次の 2 候補を報告した。
**いずれも本カードの No-Go 判定を覆すものではなく、今回は検証していない** (1技法限定の scope
のため)。次にカタログ化を行う際の出発点として記録する。

- Cicada の Early Abort Check (update/delete 時点で最新版の `wts`/`rts` を検査し、precommit 前に
  中断する。`cicada/transaction.cc:242-283`, `:372-401`)。Silo の update は write set への登録
  だけで同等の事前検査を持たない (`cc/silo/transaction.cc:524-554`)。
- TicToc の `NO_WAIT_OF_TICTOC` 経路にある lock-conflict 最適化 (部分 unlock・read-set
  pre-verify・retry の統合、`tictoc/transaction.cc:574-624`)。Silo は unlock して retry するだけ
  (`cc/silo/transaction.cc:155-168`)。

これらが現行 EVOLVE-BLOCK 実編集面に乗るかどうかは未判定であり、Go/No-Go いずれの予断も持たない。

## 11. 見なかったことにしていない前提

- **`continuing_commit_` の増分・リセット経路 (`cicada/transaction.cc:687-720`,
  `include/transaction.hh:343-367`) は、段2 plan と段3 lensA が独立に引用したが、本カードの
  親著者は自分の目で直接確認していない。** Tuple 構造体でのフィールド定義 (`tuple.hh:30-38`) と
  precheck 側の読み取り (`transaction.hh:266-267`) は親が直接確認済みであり、判定の根拠として
  十分だが、増分/リセット経路そのものは 2 段の一致に依拠している。
- カタログカード化という手法自体の一般的な有効性 (「前提/効果/競合の三つ組は移植可否を正しく
  予測できるか」) は、本 1 件だけでは判定できない。DW-G03 の「独立2例」を満たすには、最低もう
  1 件 (別技法または別プロトコル) のカード化が要る。
- 段7 (cross-protocol 対応、item7 全体) の発火条件 (D32 = 8b+層3後) が満たされたかどうかは、
  本 wave でも判定していない。本カードは Group D (i) 単体の一歩目であり、item7 全体の発火や
  b2 (本格移植投資) の可否を決めるものではない。
- 実測 (correctness run を含む一切の Pegasus job 投入) はすべて人間 `qsub` 手番であり続ける
  (D87/D86(3))。本カードは静的ソース確認のみであり、実行を伴う検証は一切していない。
