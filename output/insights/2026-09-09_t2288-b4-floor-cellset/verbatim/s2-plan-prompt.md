単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/brief.md` — 親の段 1 brief v2 (逐語)。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/verbatim-rulings.md` — D1641 全文と事前登録 §5 floor 欄・§5.1 floor 解除条件の逐語。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/handoff.md` — 親が実測した現在地の表。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md` の §5 と §5.1 (見出しで索引して該当箇所だけ読め)

repo の path は上記 worktree のものだけを使う。親 checkout の path を使ってはならない。
`docs/decisions.md` の D1377 / D1530 / D1641 / D1696 / D1759 / D1808 は同 worktree の `docs/decisions.md` を
`grep -n "^## D1759\."` の形で索引して該当節だけ読め。

## 段の宣言

これは段 2 (プラン起草) である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。** 実測は親が段 6 で行う。
実走していない検査を「通した」と書いてはならない。
コードを編集してはならない。commit してはならない。

予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

出力に結合文字 U+0300〜U+036F を使うな。

## 依頼

[T-2288] の土台部分の実装プランを file:line 粒度で起草せよ。

欠陥: `floor_pair_driver.py` の `_bind_checkout_inputs` (1122-1196) は `provenance.calibration` の 1 件を
全 cell へ照合し、`calibration.workload != dict(perf.workload)` で拒否する。このため 1 spec の cells は
同一 workload しか持てず、D1641 が凍結したセル集合「3 workload × contention セル」と、保守側最大の
対象集合「凍結したセル集合 × 2 時間窓の全部」を 1 spec で表現できない。

**まず択一を決めることがこのプランの主目的である。** 親 brief の (P1-a) は 3 案を挙げている。

- (α) workload ごとに 3 spec → 3 成果物 + 事前登録 §5 側の集約規則。
- (β) cell ごとに calibration 参照を持たせ、cell ごとに accepted calibration を束縛する。
- (γ) calibration の束縛から **workload 一致要求だけを外す**
  (`env_tag` / `clocks_per_us` / `threads` / `records` / `quality.status == "accepted"` は維持)。

**3 案を一次資料で比べ、1 案を選べ。** 判定に使う一次資料は少なくとも次を含めよ。

- b10 formal run の provenance が 3 workload すべてに同一 calibration を束縛し、束縛 field に
  `workload` を含めないこと (親の実測。**あなた自身が現物で確かめ、親が誤読していないか判定せよ**)。
- 事前登録 §5 の「校正済み `PerfConfig` … の artifact パスと hash」欄が単数であること。
- 同じ §5 のセル集合が 3 workload であること。
- calibration artifact の `saturation` が何を保証しているか (`records` 飽和の判定根拠を
  `saturation.notes` と `working_set_ratio` まで読め)。**それが workload 混合に依存する量かどうか**を
  判定せよ。ここが (γ) の正当性の核である。
- `calibration_verify.load_verified_calibration` が何を検査し、何を検査しないか。
- issuer `_derive_identity` の `workload_identifier` が集合集約であること、
  `threads` が `next(iter(threads_values))` であること。

親 brief の「変更面の実アンカー」節に親が実測した file:line がある。プランはこれを**独立に検証**し、
誤りがあれば指摘せよ。同意する場合も、同意した根拠の file:line を自分で挙げよ。

## プランに必ず含めるもの

1. **択一の判定。** 選んだ案と、却下した 2 案の却下理由。各々一次資料の file:line つき。
   選んだ案が**受理集合を広げるなら、広がる範囲を「これまで拒否されていた spec のうち、
   これから受理される spec の集合」として厳密に書け。**
2. **変更する file:line と、変更後の関数の完全な形。** 選んだ案に応じて
   `_parse_provenance` (660-672)、`_parse_calibration_reference` (647-657)、`_parse_cells` (798-816)、
   `_bind_checkout_inputs` (1122-1196)、および cell ごとの照合ループ (1184-1196) の変更後の完全な形。
   calibration artifact を 1 spec 内で何回読むかと、重複読取りをどう畳むかも書け
   (現行 `receipt_raw_by_reference` の idiom に合わせるか)。
3. **親の (P1) 5 件への判定。** 各々 real / refuted と、その根拠の file:line。
   (P1-a) 択一、(P1-b) issuer 無変更で足りるか、(P1-c) schema bump の必要範囲、
   (P1-d) DW-G04 の発火 artifact、(P1-e) scope 境界。
4. **受理集合の不変性の論証。** 変更後も次の経路がいずれも塞がっていることを、拒否する行を名指しして示せ。
   - 参照先が `quality.status != "accepted"`。
   - `saturation.records` が cell の `perf_config.records` と一致しない。
   - `env_tag` / `clocks_per_us` が `environment` と一致しない。
   - `attestation_mode` が `calibration=None` を返す mode である (1170-1176 の意図的拒否)。
   - cell 間で `threads` が異なる (issuer の `next(iter(...))` が壊れるため単一性は維持が必要)。
   - (β) を選ぶ場合は、cell が calibration 参照を持たない / 空 / 重複する形も。
5. **schema bump の閉包。** 選んだ案で spec の wire 形が変わるか。変わらないなら
   `SPEC_SCHEMA` を bump すべきか否かを、意味が変わったかどうかで判定せよ
   (受理集合が変われば意味は変わる)。`SUMMARY_SCHEMA` が spec の何を記録しているかを
   `_validate_summary_document` と summary 生成側まで読んで確定し、summary の形が変わるかを判定せよ。
   変わる場合は issuer の `ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION` (39-41) と D1759 への影響を書け。
   `test_floor_pair_driver.py:628-634` の 4 定数同時 pin と `:636-651` の v2 拒否 test の更新も書け。
6. **issuer への波及。** `load_frozen_spec` を呼ぶ `p3_b4_floor_artifact_issuer.py:858` 前後、
   `_derive_identity` (737-812)、および docstring `748-750` が
   `floor_pair_driver.py:759-776, 1136-1147` を行番号で pin している点。行が動くならどう書き換えるか。
7. **test 設計。** 追加・変更する test の
   - node 名、
   - 受理側 (2 cell が別 workload を持つ spec が loader を通る) をどの fixture でどう組むか。
     `registered/` の実 artifact を使えるか、使えないなら何が足りないかを実装まで読んで判定せよ、
   - 4 の各経路に対になる拒否側 test、
   - 既存 209 node を壊さないことをどう示すか (既存 fixture helper `_document_only` / `_prepare_spec` 系の
     後方互換をどう保つか)、
   - 受入所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` に新 nodeid を登録するか否かの判断、
   を書け。既存 test の書き方に合わせること。
8. **段 6 の変異点候補。** 帰属が成立する (赤理由が一つに絞れる) 変異点を 3 つ以上、位置と
   殺すべき test の性質つきで挙げよ。前後や内側の層が先に拒否して帰属が壊れる候補は、
   その理由つきで「登録しない」と明記せよ。
9. **触ってはいけない面。** 変更してはならない file と、その理由。

## 禁止

- `quality.status == "accepted"` 要求、`saturation.records` 一致、`env_tag` / `clocks_per_us` 一致、
  `calibration=None` mode の拒否、cell 間の threads 単一性 — **これらを緩める案を出してはならない。**
  受理集合を広げてよいのは (γ) の workload 一致要求 1 点だけであり、それも一次資料で正当化できる場合に限る。
- 事前登録 §5 を埋める案、事前登録本文を書き換える案 (erratum を含む) を出してはならない。
- issuer の identity 要素・成果物の命名規則を変える案を出してはならない (D1641、D1808)。
- 一般化した multi-calibration framework、汎用の spec 拡張機構を新設してはならない (D1696)。
- 権威 floor の発行そのもの、calibrator の実行、Pegasus への測定投入を含めてはならない。
- `p3_s4_loop*` / `between_run_floor.py` / `s8b_floor_*` / `p3_b4_launcher.py` の挙動を変える案を
  出してはならない (`p3_b4_launcher.py` は並行 wave [T-2316] が所有している)。
- 仮想リスク向けの新しい gate・検査・台帳・一般化を足してはならない (依頼の明示指示)。
- 本題と無関係な refactor、命名変更、型注釈の整理を含めてはならない。

## 出力形式

以下の H2 見出しをこの順で使え。

## 択一の判定
## 前提の独立検証
## 変更プラン (file:line)
## (P1) 判定
## 受理集合の不変性
## schema bump の閉包
## issuer への波及
## test 設計
## 変異点候補
## 触らない面
## 総括
