---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2464-b4-start-time
seq: 1
title: [T-2464] B-4 事前登録の開始時刻欄を発効条件から外した (コード + テスト + docs、branch worktree-dev-wave-t2464-b4-start-time、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「B-4 事前登録の『実行責任者・開始時刻』欄について、開始時刻を発効条件から外す。
  裁定は D1871、台帳は [T-2464]。行 label 集合は変えず本欄に限り `未記入` を受理する。
  §0 の原子性・sentinel 規則は他の欄についてはそのまま維持する。事前登録本文の改訂は同文書の
  改訂契約に従い追補 (erratum) で行い in-place で書き換えない。凍結成果物側の sha と解析規則側の
  sha は別定数に分ける。着手直前の local main から fresh worktree を作る。実装面は Codex author。
  規律 2 を緩めない。本題の欄限定変更と追補だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」。
- **閉じた。** D1649 決定 2 (2026-09-05) が開始時刻の記入義務を撤廃してから、受理側がその裁定を
  実施していなかった。一次資料は
  `output/insights/2026-09-16_t2464-b4-start-time-optional/README.md`。
- **段 3 レンズ A の最重大所見 (高) を親が反実仮想の実測で反証した。** レンズ A は「追加受理経路が
  責任者未指名の説明文と NUL 1 文字を受理する」ことを probe で実測したが、同じ文字列は**変更前から**
  開始時刻が非 sentinel の実値なら受理され、expectation 行を除く他の欄でも受理された。受理側の関数は
  自ら `types, meanings, and rendered non-emptiness are not checked` と非保証を宣言している。
  意味検証を足すと対象行だけが他 9 欄より厳しくなり、D1871 が前提とする欄間の対称性を実装側から
  崩すことになる。判断は {{D:b4-start-time-cell-grammar}}。
- **段 6 レビュー B の must-fix 1 件は、追補の文面が実装より広かったことである。** 初稿は
  「`<値>` が非空で既存の予約 sentinel に該当しない場合」としか書いておらず、実装が禁じる
  読点・等号・改行と、正規化後に全体一致を取ることが抜けていた。`実行責任者 = uid=alice、開始時刻 = 未記入`
  が文書上は適合して実際は拒否されることを親が実測して確認し、追補を正確化して閉じた。
- **親 brief の数え違いを段 2 plan が先に訂正した。** 「§5 に残る未記入は 5 欄」は誤りで、
  対象行以外に 6 欄 (対象行を含めて 7 行) である。段 6 の 2 レビューも独立に同じ訂正を返した。
  親 brief の「whole-file sha の live pin は無い」も過大な一般化で、record 検証が動的に whole-file sha と
  HEAD bytes の一致を要求する。
- **本変更は事前登録を発効させない。** 対象行以外の 6 欄が `未記入` のままなので、変更後も実文書は
  同じ reason で拒否される (実測)。
- **凍結 pin は動かなかった。** 追補を §5.1 の開始時刻節末尾 (§5.1.0 見出しの前) へ入れたので、
  §5.1.1 を pin する raw / semantic sha はいずれも一致したまま (節長 21,833 bytes 不変)。
  文書全体の sha だけが変わる。発行済み admission record は親と 2 レンズが独立に現物で確認して 0 件
  だったので失効対象はない。
- **変異は 2 走に分かれた。** 初回 spec の `timeout_seconds` を 600 に置いたところ m5 が timeout し、
  `hang_risk=false` なので kill に数えられず、harness が orphan-hold を立てて中断した。原因は hang では
  なく Pegasus の queue 待ちで、計測時の scheduler には他 session の job が 14 本あった。復旧は
  hold の手順どおり qstat の不在確認 → 復元 → bytes 照合 → hold と sidecar 削除で行い、手動 `qdel` は
  使っていない。再走は残り 5 変異だけの spec を新しい `--out` / `--attempt-out` で起動し、
  `timeout_seconds` を 2700 へ、D612 の queue-wait / grace 上書きを 1800 / 600 へ上げて完走した。
  合計 baseline PASSED (2 走とも)・9/9 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致。
- **段 3 レンズ B の 1 回目が `Selected model is at capacity` で出力 0 byte になった。** 署名は
  F818 (枠切れ) と同じ `f45_missing_output` だが原因が違い、`--job-id` を変えた即時再投入で成功した。
  署名だけで分岐すると 30 秒で直る事象のために wave を 5 日止める。F818 へ再発として記録した。
- **段 5 実装子は自分でテストを走らせられなかった。** `run_tests.py` の dispatch preflight が rc=16 で
  落ち、「実装済み・未実走」と正直に申告した。実走は親が行った (焦点走 29 passed と 385 passed)。
- **real だが scope 外**として 3 件を裁定パッケージ候補に残した。§5 の値セルが意味・表示上の非空を
  検査しないこと、floor セルの読取経路が admission 検査を通らないこと、admission validator のコード
  bytes が projection closure の入力なので本変更で live closure hash が変わること。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2)。親の実測は probe 4 本・焦点走 2 本・
  provenance full 監査 1 本 (10466 件・新規違反なし)・変異走 2 本。

## 次の一手差分

### 完了

- [T-2464] B-4 事前登録の「実行責任者・開始時刻」欄について開始時刻を発効条件から外した。
  受理側は本欄 1 行だけを緩め、事前登録本文へ追補を足した。行 label 集合は不変。
  remaining: none
  base: 8594454a51264b5a5642bacba4d381415a6a1035ab66844084d54e3da22f552b

### 新規

- {{T:b4-section5-cell-semantics}} **P2・新規**: §5 の値セルが意味・表示上の非空を検査せず、
  説明文・制御文字を受理する。責任者の「不変の識別子による指名」義務が機械的に強制されていない。
  expectation 行を除く 9 欄に共通する既存性質であり、対応するかどうかの裁定を要する。
- {{T:b4-floor-cell-read-path}} **P2・新規**: floor セルの読取経路が admission 検査を通らない。
  material report → floor artifact issuer は文書全体から floor 行を exact prefix で探し、
  §5 の見出し境界・他の欄・責任者・開始時刻を検査しない。
