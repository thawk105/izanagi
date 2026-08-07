---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t609-certified-writer-closure
seq: 1
title: [T-609] certified writer の認可を sink へ移し、PBS wrapper に静的 admission を前置した — 認可の成果物束縛は入れていない (コード + docs、受入 7199 passed / 20 skipped、変異 7/7 KILLED・SURVIVED 0、branch worktree-dev-wave-t609-certified-writer-closure)
---

## 本文

- **起票文の scope は狭すぎた。** [T-609] は `loop.run_campaign` の
  `env_contract is None` 素通りを塞げと書いていたが、certified を書く実体は
  `pipeline.evaluate` であり、`run_campaign` を通らない production 経路が実在する。
  起票文が名指しした `s8a_trigger_sweep.py:457` の driver 自身が、すぐ隣の `:463` に
  screening 経由の第 2 の未防護経路を持っていた。同型が `s6_sort_sweep` `backoff_sweep`
  にもあり、`s1_direct_comparison` は既定 `evaluate_fn` で直接呼ぶ。
  段 3 の 2 レンズが独立に指摘し、親が現物で確認した。強制点を sink へ移した {{D:certified-writer-sink-authorization}}
- **親の provisional 裁定 (P1)〜(P5) は全部または一部が反証された。**
  最大の誤りは「既存 `env_contract` を全 caller へ配線すれば受理集合は不変」。同引数は
  認可用ではなく build の新旧プロトコル selector を兼ねており、配線すると build 移行が
  同時に起きる。legacy 側で拒否され v2 側で受理される入力が構成でき、規律 2 に触れる。
  親の一般化が段 3 で覆るのはこれで **5 wave 連続**である。
- **親の実測 8 件のうち 4 件が誤りだった。** caller 数 (14 → 12 module・15 呼出し)、
  「契約を渡すのは 2 本だけ」(trigger-gating は compute で既に渡す)、
  「残り 12 本の実行値が登録契約と完全一致」(`sanity_silo` は numactl を渡していない)、
  「floor の最初の書込みは 88 行」(実際は 30 行の `mkdir "$TMPDIR"`)。
- **段 6 の敵対 2 レンズは must-fix 10 件で NO-GO。** 最も重かったのは
  「source commit へ束縛されているのは入口 adapter 1 ファイルだけで、admission 本体は
  現 worktree から import される」。つまり「投入時のコードで検査した」という主張が
  成立していなかった。レンズ C と D が独立に検出した。import 済み repo module の bytes を
  receipt の `source_commit` blob と照合する形へ直した。
- **fix 第 3 巡が持ち込んだ fail-open を親が差し戻した。** 呼び先の signature を検査して
  認可引数を落とす互換分岐が `loop.py` へ入れられていた。注入された sink を無認可で
  呼べるようにするもので、本 wave の目的そのものを壊す。採用せず、テスト側の代役関数の
  signature を直す最小 fix へ置き換えた。fix 巡回が `DW-O16` の 3 巡を 1 つ超えたのは
  レビュー所見の未解決ではなくこの差し戻しのためである {{F:fix-child-fail-open-to-green}}
- **受入全走の赤 110 件は gate の欠陥ではなかった。** 全走は計算ノードへ dispatch されるため
  実行中の site が `PEGASUS_COMPUTE` になり、linux 環境向け契約を使う既存テストが
  「計算ノードでは登録済み pegasus 契約だけ受理」で落ちていた。テストがホストの環境識別を
  継承していた潜在的な非決定性が、認可を必須化したことで表面化したものである。
  conftest でテストに環境を明示宣言させる形にした {{D:tests-declare-site-not-inherit}}
- **受入全走が 1 度 30 分上限で SIGKILL された (99% 到達)。** 同じ木で再走したときは
  17 分 54 秒で完走したので、計算ノード側の遅さであって本 wave の変更由来ではない。
  ただし `tools/run_tests.py` の受入経路は walltime 固定 (`00:30:00`) で override 手段がなく、
  余裕は薄い。最も遅い 15 件はいずれも既存の `test_t126_pegasus_tools.py` (1 件 60〜67 秒)。
- **変異は 7/7 KILLED、SURVIVED 0、MISMATCH 0、期待 node と実測 node が全件一致。**
  当初登録した「必須引数の欠落」は Python の signature 側でも同じ入力が弾かれ単一理由に
  ならないため、レンズ C の指摘に従い証拠から外した。`numactl is None` の単独 branch も
  直後の型検査に覆われる過剰決定だったので、shape gate 全体の置換として定義し直した。
- **本 wave の成果は proof chain へ束縛された閉包ではない。** 認可の事実は
  campaign identity にも WAL COMMIT にも残らず、`attestation_mode="none"` では receipt も
  発行されない。T-609 以前の無束縛 COMMIT を認可済みの再起動が terminal として skip できる。
  この束縛は [T-530] の残件であり、本 wave では入れていない。

## 次の一手差分

### 完了

- [T-609] 認可の強制点を `pipeline.evaluate` (certified を書く実体) へ移し、必須
  keyword-only 引数として exact 型・registry 同値・実行値完全一致 (`numactl` の未指定と
  空を区別)・compute の exact-Pegasus・build selector との同値の 5 条件を、layout / WAL /
  build のいずれよりも前に強制した。production の sink caller 5 本と `run_campaign` の
  12 module・15 呼出しを配線した。PBS wrapper 2 本には、最初の script 書込みより前に
  静的 admission preflight を置き、helper を receipt の `source_commit` から git blob として
  標準入力へ流すことで hash literal の相互 pin と投入後 checkout drift の両方を回避した。
  受入 7199 passed / 20 skipped、変異 7/7 KILLED (SURVIVED 0)。
  正本 = `output/insights/2026-08-07_t609-certified-writer-closure/`
  remaining: none
  base: b8d5ec826c02c11363f84133ac2b388ca57b8a746eb7d0b77cba87bb597fc895

### 更新

- [T-530] **P1・前半のみ完了 (2026-08-07、[T-609] wave)。残りは hash 束縛**:
  「契約を渡さない既定値が site 検査より前に返る」迂回は塞いだ。**ただし起票文の
  「単独で塞ぐと承認外の受理縮小になる」という前提は、実測では成立しなかった** —
  塞いだ結果の受理集合の変化は縮小のみで、拡大は 1 件もない。残件は起票文が対で求めていた
  **campaign identity と WAL COMMIT への contract hash 束縛**である。現状、認可の事実は
  成果物 bytes に残らず、T-609 以前の無束縛 COMMIT を認可済みの再起動が terminal として
  skip できる。`attestation_mode="none"` の receipt 発行と resume 受理集合の変更を伴うため
  ユーザー裁定が要る
  base: 4b6e48a06949dd0815358b3e001abe576bb5a39d7ebec1d5d0ab3618bb3e53bb

### 新規

- {{T:write-free-attestation-before-first-write}} **P2・新規・裁定待ち**:
  `attestation_mode="required"` の実 probe は TSC probe が一時ファイルを作るため、
  PBS wrapper の preflight へ入れると preflight 自身が最初の writer になる。したがって
  現状の preflight は静的 admission (registry・protocol/control・calibration bytes・site) までで、
  hardware attestation は最初の書込みより前に行えていない。書込みを伴わない事前ビルド済み
  probe の別設計が要る。段 6 のレンズ C・D が独立に指摘
- {{T:site-policy-evidence-hardening}} **P2・新規・裁定待ち**:
  `site_policy.classify_site` は hostname の `bnode[0-9]+` だけで計算ノードと判定し、
  NQSV / PBS 証拠を分類条件にしない。既存テストも証拠なしの `bnode123.other.example` を
  計算ノードとして固定している。CI や別施設のホスト名で誤検出しうる。既存裁定
  (「計算ノードの権威は bnode hostname と affinity」) を覆すため独立裁定が要る
- {{T:floor-protocol-source-commit-binding}} **P2・新規**:
  qsub 後に `output/s8b-freeze/floor_protocol.json` の `master_seed` を変えても、job 側の
  dirty 検査は `output/` を除外するため検出できず、driver は working-tree の変更後 protocol を
  読んで別 schedule を走らせる。既存の TOCTOU であり本 wave の変更が作ったものではない。
  receipt の `source_commit` から blob を読み、検証済み bytes を driver へ渡す構成が要る
- {{T:no-bench-certified-contract-scope}} **P2・新規・裁定待ち**:
  `sanity_silo` は `do_bench=False` で numactl を実際には使わないため、認可を通すために
  渡した numactl は宣言値に留まる。「bench を走らせない correctness-only の COMMIT を
  計測契約束縛の対象と数えるか」は独立の裁定である。本 wave は認可の穴を塞ぐために配線したが、
  numactl gate が `sanity_silo` で実効的だとは主張しない
