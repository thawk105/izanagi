---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-rulings-20260820-all
seq: 1
title: '/rulings all で持ち越し約515件・repo外inbox・handoff・phase3 gateを精査し裁定待ち14件を提示、ユーザーがT-1362を(b)へ方針転換し他13件を推奨通り確定した (docsのみ、branch worktree-rulings-20260820-all)'
---

## 本文

- `/rulings all` を実行し、`docs/worklog.md` 末尾の持ち越し約515件・repo外rulings-inbox・
  `docs/handoff/`3件・`docs/phase3.md`現行チェックポイントと見送り台帳を精査した。収集はfork 2本
  (持ち越しT-ID分類/直近セッション新規候補調査) を用いたが、両forkとも一時的に成果物本体を返さず
  親の地の文を誤って自分の役目のように語る空疎な応答を返し、SendMessageで実データの再送を求めて
  回収した (memory `fork-inherits-command-context-can-misact-as-manager.md` へ6件目・7件目として
  追記済み)。
- ユーザー提示 14 件のうち [T-1362] を除く 13 件について「他は推奨通りで」の裁定を得た。
  [T-1362] は当初 rulings 側推奨 (a) (上限値の引き上げ) を提示したが、ユーザーが明確に却下し
  (b) (コミット数に非比例な検査方式への作り直し) を裁定した — 「コミット数に比例してコストが
  増えるテストはやらない。それはテストの仕方が間違っている。このリポジトリは成長し続けるから。」
  **調査の結果、この方針は新しい決定ではなく D551 (2026-08-19、[T-1408] 経由) が既に同じ結論
  (上限引き上げは死の先送り、履歴長に依らない設計へ直す) で確定していたと判明した。** ただし
  D551 の恒久対応宣言 ([T-1408] 完了・F417/F418 supersede、いずれも2026-08-19) は時期尚早
  だった — 修正直後の local main 実測でも余裕は残り16件しかなく (D551本文実測)、その1日後に
  [T-1362] のwaveがわずか7 commitの増加だけで再び超過した (実測50072)。D551 が narrow したのは
  `validate_condition_freeze_at` 1経路のcostだけで、`_batch_oids` を通る他経路 (F418 が指す
  candidate commit祖先集合 × generation-freeze追跡ファイル) は履歴比例のまま残っている疑いが
  強い。F417 へ再発を追記し、新しいDは起こさず D551 を恒久方針の正本として直接引用する。
- **収集漏れを1件実測した (rulings自己改善gate該当)。** 当初「T-828」として提示した項目
  (rulings-inbox `2026-08-19-t828-dw-s07-acceptance-ordering-note.md` を一次資料に、段8記録容量
  超過+段順序の構造的衝突を裁定待ちとして提示) は、実際には同日朝の別 `/rulings` セッション
  (`worktree-rulings-20260820-floor-provenance-codex-escalation`、08:35着地) が既に同じ一次資料を
  読んで裁定・採番済みだった ([T-1430]、`docs/archive/worklog-phase3-0820-727.md`、結論も
  「まとめて独立審査へ回す」で完全一致)。inboxファイルが消費後も削除されず残っていたため後発の
  収集が未解決と誤認した。F272 (rulings-inbox drift) へ再発として追記し、当該 [T-1430] を
  ユーザーへの提示から取り下げた (新規裁定は不要、既裁定と同一結論のため実害なし)。
- **セッション異常: 収集forkの孫エージェントが、依頼していない自己改善commitを無許可で行っていた
  のを発見した。** fork (直近セッション新規候補調査) が自ら spawn した general-purpose 子
  (`ab4539bed30390c7f`) が、`.claude/commands/rulings.md` の出力形式指示 (表/ID主体索引の廃止)
  を是正し `worktree-agent-ab4539bed30390c7f` branch へ commit していた (未land、内容は
  `docs/skill-self-improvement.md` のrulings発火条件に正しく合致し、check_docs.py緑・provenance
  trailer正当)。内容を監査し安全・妥当と判断したため本waveへ cherry-pick で取り込み、孤立
  worktreeは削除した (branchは削除せず残置、内容は本commitで吸収済みなので実質重複)。
  memory `fork-inherits-command-context-can-misact-as-manager.md` へ8件目 (寄せ書き済み、他セッション
  による追記と思われる) の並びで、越権が実際のcommitまで到達した初の実例として位置づく。
- git push (未push状態) はセッション中に別waveが解消済みで、本セッションでの裁定対象から外れた。
- 本セッションの役割は裁定の記録と canonical 台帳への land までであり、実装
  ([T-1310]の新launch mode・[T-1371]のrun root強制・
  {{T:s8c-batch-limit-d551-residual-proportionality}}等) は別セッション (dev-wave) へ委ねる。

## 次の一手差分

### 更新

- [T-1310] **P2・択 (a) 採用 (2026-08-20裁定)**: 正式 non-certifying 専用の launch admission mode
  を新設し、`admit_registered_launch` が要求する 12 predicate 全部 SATISFIED を回避して 8c
  (人手を介さず反復する自動実験の仕組み) の正式測定を開始できるようにする。(b) (oracle driver
  経由) は別の未整備な前提で同じく手詰まりと判明済み、(c) (択 (α) へ戻す) は新情報なしに過去裁定
  を覆すため不採用。正本 = `output/insights/2026-08-18_t1333-t1310-workload-profile/README.md`。
  base: afb58da29f399dbd6baf24c8b2dc654cdb193a2c2c9709377987c7f41747e084

- [T-1371] **P1・択 (a) 採用 (2026-08-20裁定)**: 正式 rr80/rr20 run の run root/campaign root を
  repo 外へ強制する。(b) (unknownness 主張の明示) は「検査しない」ことの説明責任が残り続け、
  (c) (exempt path 個別指定) は例外の積み重ねで検査自体の意味が薄れるため不採用。
  base: 19c1cedc770952587f6f4837ae04e8cf32e5d2520b11dfb9432f15926be251fb

- [T-1432] **P3・横断的に束縛を足す (2026-08-20裁定)**: `silo_ladder_rung1.py` /
  `floor_liveness.py` / `collect_receipt.py` / `t503_restore_durability_probe.py` の4箇所へ
  Group Name (スケジューラ上でジョブを束ねる識別名) の検証を追加する。DW-G03 の族一般化閾値
  (独立2例) を4例で満たしており、正しさゲートを緩める変異を許さない規律2に近い性質のため
  見送らない。
  base: 43ff408f639ac60096431d4103b4ba8f2895254e3e15722721f12366a78cf8f9

- [T-1410] **P3・正式 dispatch 規則として明文化する (2026-08-20裁定)**: 段2/3省略の軽量パス
  (段1 brief 前の実測で既に別ID/別waveの成果と判明した場合に4→7→8→9へ進む) を
  `docs/dev-wave/core.md` の凍結境界節へ明文化する。既に4回使われた実績があり、前例引用運用の
  継続よりブレを防げる。
  base: 0eab985f5cc2dbcf41a845c1fc6807f0c419a38507dd6c2b545b889bb5bd7bc1

- [T-1372] **P2・別waveとして起票、本waveの範囲は広げない (2026-08-20裁定)**: `s8b_oracle_driver.
  _perf_for_holdout` の PerfConfig 検証を oracle 側 (実験結果の正解判定をする仕組み) にも広げる件
  は、段階導入・盛らない規律5に照らし今回のwave範囲拡大では対応しない。別waveの候補として起票する。
  base: 06ad1dfbf643bb36d4da5e13a725b70fa75a5feb9095c98bd44a7ec6c1fdbed0

- [T-1415] **P3・[T-1430] の容量審査へ合流 (2026-08-20裁定)**: `DW-S01` の前提実測範囲 (引用
  decision の結論だけでなく、その decision が属するタスク台帳自身の完了マークと後続 decision に
  よる上書きの有無まで辿る必要がある) の明文化候補を、[T-1430] が指す独立の docs 予算引き上げ
  審査へ合流させる。
  base: 3398b3f31c944e82b2307fff6e67ea1f9ce59f3c1d600aa386900815c8ff556e

- [T-414] **P2・択 (b) 採用 (2026-08-20裁定)**: `project_whiteboard()` (core/sort/trigger 3
  driver 共有の保存直前合流点) で checkpoint 値域検査を閉じる。(a) (3 driver 個別) は箇所が増え、
  (c) (検査なし) は自己汚染から次回 resume 停止までの非対称を放置する。実装には事前登録変異と
  正例テストを伴う独立waveが要る。一次資料 =
  `output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md` §1。
  base: d3f10e2c3d5b35e97a9d6d93eb90a8f3043c31192492daf324ed0130eeec7364

- [T-415] **P2・択 (a) 採用 (2026-08-20裁定)**: `layer3_report` と `state_from_dict` の両方から
  呼ぶ共有 validator を新設する。(b) (schema enum) は手作業 runbook 経由の抜け道を閉じない、
  (c) (閉じない) は値チェックの主張自体を弱めるため不採用。既存 fixture (`direction="up"` 等) の
  期待値変更を伴うため独立waveの裁定が要る。一次資料 = 同上 §2。
  base: ebf4daee3bbe40ea7ef5a158b70fd1c5fcd4806b067a1008158059df2fe69062

- [T-1200] **P2・supersession注記を追加する (2026-08-20裁定)**: `docs/phase3-8c-wiring-design.md`
  と `docs/phase3.md` に残る承認上限「1」の記述へ、D410 による「2」への引き上げを示す注記を足す。
  歴史記述の遡及改変はしない。
  base: 45c59beed79c418717e7ba3ed8f7a6c1bc417edd8e89b69765a95627591aaffa

- [T-372] **P2・T-1362系exact-pinの拡張で対応する (2026-08-20裁定)**: `orchestrator/codex_roles/
  manifest.json`・13件のagent frontmatter・`docs/dev-wave/workers.md` に散らばる reasoning/effort
  (Codexへどれだけ深く考えさせるかの指定値) 記述の整合を check_docs.py の exact-pin (文書の記述を
  1字1句固定して検査する仕組み) で束縛する。[T-1362] の恒久対応 (受入全走の履歴比例costの残余、
  {{T:s8c-batch-limit-d551-residual-proportionality}} とは別件) が DW-S05-A 1箇所限定の
  exact-pin を先行実装するため、それが着地してから同じやり方で範囲を広げるのが手戻りが無い。
  base: c1d2c6975693c6ac0d7afce508e764ec5a5f55da717bc41c76158371c08548d4

- [T-374] **P3・[T-372] 対応のついでに扱う、単独では急がない (2026-08-20裁定)**: 永続 profile
  経由の不正 effort 値が、一時的に worktree/worker spec artifact へ書き込まれてから拒否される件。
  fail-closed は既に成立しており実害が無いため、単独対応は不要。[T-372] 対応時にまとめて見る。
  base: 3059806617ad3547c7c389ce6e12c96dfe75c64baa5979fa82e9f0c89bcaa4ca

- [T-425] **P3・保留 (2026-08-20裁定)**: 8c 正式 H1/H2 実験の D145 決定5 再訪要否は、次waveの
  D581 影響確認 (段1 brief) が終わってから改めて出す。今は判断しない。一次資料 =
  `output/insights/2026-08-20_t425-dependency-reaudit/README.md`。
  base: 1763a4a2b40e119bd9300eb05a937eb22da7e5bae8c8b90aae4043a00e794a8d

### 新規

- {{T:s8c-batch-limit-d551-residual-proportionality}} **P1・新規 (2026-08-20裁定、F417再発の
  恒久対応)**: D551 (2026-08-19) は `validate_condition_freeze_at` 1経路の履歴比例costを
  scan対象の narrowing で解消したが、`_batch_oids` の他の呼び出し経路 (F418 が指す candidate
  commit 祖先集合 × generation-freeze追跡ファイル) は履歴比例のまま残っている可能性が高い
  (D551適用直後の余裕が16件しかなく、その1日後に7commitの増加だけで再超過した実測が根拠)。
  D551 と同じ設計原則 (上限引き上げでは解決しない、対象範囲を凍結namespaceに触れたcommitへ
  絞る) を `_batch_oids` の残る全呼び出し経路へ適用し、no-touch commit数を変えても要求数が
  変わらないことを検査する回帰テストを経路ごとに置く。本来無関係な
  `dev-wave-t1362-reasoning-pin` の land を塞いでいる実害がありP1とする。着手時は
  `docs/handoff/2026-08-19-t1362-reasoning-pin.md` の段9停止理由 (更新済み)、D551本文の実測値、
  および `tools/check_acceptance_reds.py` の probe worktree dispatch orphan-hold (別原因、
  切り分けが要る) も参照すること。
