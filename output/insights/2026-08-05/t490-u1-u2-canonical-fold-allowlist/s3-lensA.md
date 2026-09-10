静的レビューの結論は **NO-GO** です。`quarantine` 内の畳み込み自体は妥当ですが、P1 の「唯一の materialize 境界」という前提が成立していません。pytest・build・freeze 再生成は実行していません。

## 所見1 — `quarantine` だけでは identity 多重化が閉じない

**要約:** `render_hole` の呼び出しは1箇所でも、既 materialized source を直接 identity/build に渡せる公開経路が残る。

**判定: real（blocker）。** 実際の `render_hole` 呼び出しは [p3_s4_loop.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:225) の1箇所だが、これは「全 source admission がここを通る」ことを意味しない。

| trigger 関連経路 | `src_token` / `variant_id` 確定点 | 計画した畳み込みとの関係 |
|---|---|---|
| S8a sweep | [quarantine:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_sweep.py:421) → [resolve/variant:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_sweep.py:425)、同じく [443→451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_sweep.py:443) | 後。閉じる |
| trigger loop | [quarantine:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_trigger_gating.py:404) → [run_campaign:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_trigger_gating.py:565) → [resolve/variant:202,240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/loop.py:202) | 後。閉じる |
| S1 → S8b | [quarantine:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:551) → [resolve:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:562) → S1 ID [780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:780)、S8b ID [123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:123) | 後。floor/oracle も同じ `PreparedCell` を使うため閉じる |
| extime calibration | [quarantine:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_verify_extime_calibration.py:339) → [evidence/token:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_verify_extime_calibration.py:347) | 後。閉じる |
| preview 群 | 例: [autonomous preview:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_autonomous_workload_trial.py:653) | `write=False` で token/ID を作らない |
| characterization | template patch を直接適用して [resolve_evidence:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_coverage.py:131)。適用点は [253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_coverage.py:253) | `quarantine` 非経由。hole は mask predicate でなく初期 `true` なので直ちにU-1違反ではないが、「別 materialize 経路なし」は偽 |
| 公開 `run_campaign` / `evaluate` | 任意の `ccbench_dir` を受ける [loop.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/loop.py:101)、[pipeline.py:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/pipeline.py:461) | **畳み込みなし** |

特に `pipeline` は source evidence を [624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/pipeline.py:624) で先に解決し、binding 検査は後段 [668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/pipeline.py:668)。しかも materialized hole を `.strip()` 比較するため、余分な外周空白を保持した source も受理する [pipeline.py:71-84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/pipeline.py:71)。`loop` はさらに、その検査より前に variant ID を作る [loop.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/loop.py:240)。

**成果物影響:** digest が分かれる空白形では、同じ binding mask が別 variant/WAL キーとして skip 集合・certified 選択・材料 binding の双方に入り、試行台帳上も別候補として残る。

**推奨する最小の対処:** planned fold は維持し、`source_digest.resolve*` より前に共有の post-materialization assertion を追加する。hole が strip-member なら「信頼済みテンプレ indent＋emitter bytes」と完全一致させる。characterization の非member `true` は対象外にし、`loop`・`pipeline`・直接 evidence caller で共用する。直接 API の padded source 負例も追加する。

## 所見2 — diff-quarantine reject の ID は raw のまま多重化する

**要約:** 畳み込み後に検疫が失敗しても、reject WAL の `diffq-*` は呼び手が保持する未畳み込み文字列から作られる。

**判定: real。** `quarantine` 内でローカル変数を正準化しても、戻り値には正準 implementation がない。呼び手は元の文字列を `record_diff_reject` に渡し、[diffq_variant_id:237-253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:237) が raw bytes を hash する。S8a の実呼び出しも [s8a_trigger_sweep.py:443-446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8a_trigger_sweep.py:443) の形である。

**成果物影響:** certified 選択には入らないが、同一 predicate の exact／padded 形が異なる reject variant として試行台帳・critic rejection 参照を重複させる。

**推奨する最小の対処:** trigger membership 成功後の正準 implementation を reject identity にも渡す。非member reject の raw 識別は維持し、trigger の post-membership reject だけ正準 ID にする。

## 所見3 — P-D の測定は実 `src_token` を測っていない

**要約:** raw predicate の SHA 差を、preprocess 後 digest である `src_token` の差へ一般化している。

**判定: real。** 段1 probe は単に2文字列を `hashlib.sha256` している [probe_premises.py:43-49](</work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/probe_premises.py:43)。実 identity は全対象 source を compiler preprocess して hash する [source_digest.py:320-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/source_digest.py:320)、[同:640-651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/source_digest.py:640)。プランの identity テストも file bytes を hash する fake resolver に留まる [plan.md:120-122](</work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:120)。

また、brief は「受理集合変更は U-2 だけ」とする [brief.md:45](</work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/brief.md:45) 一方、U-1 fold は現在 preprocess/build で落ちる可能性のある NBSP・U+3000 等を compiler 到達前に除去する。P-C が測ったのは membership だけで、end-to-end 受理ではない。予定テストも `\x0b` と `\x0c` を落としている [plan.md:114-116](</work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:114)。

**成果物影響:** 実 digest が空白を正規化する形では「別 variant」という前提が偽になり、逆に現在 downstream reject される形では fold 後に初めて certified 候補となり、受理集合が U-1 でも拡大する。

**推奨する最小の対処:** 7種すべてについて membership→quarantine→実 `resolve_evidence`→build admission の before/after matrix を計算ノードで測る。fake resolver テストは構造証明として残し、brief の不変条件を「membership 集合不変」に限定する。

## 所見4 — canonical index の collision 防壁に負例がない

**要約:** duplicate strip key を import-time `RuntimeError` にする設計は正しいが、その失敗動作を固定するテストがない。

**判定: real（テスト防壁不足）。** 現行32本が一意であること自体は [test_reflux_ir.py:243-250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_reflux_ir.py:243) から反証されない。しかしプランの synthetic builder test は「値側の空白保持」だけで [plan.md:107-110](</work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:107)、silent overwrite/dedup 変異を赤にしない。

**成果物影響:** 将来2 mask が同じ strip key を持った際、一方の emitter bytes が他方へ割り当てられ、材料レポートの mask/hash と materialized source、variant 参照が食い違う。

**推奨する最小の対処:** `["predicate", " predicate "]` のような synthetic collision が exact `RuntimeError` になる負例と、上書き実装への単一理由 mutation を追加する。

## 所見5 — 凍結物の「6件／3件」と23件の「閉包」は過剰一般化

**要約:** P-F は measurement freeze だけの件数であり、P-G の manifest key-set は正本自身が暫定と明記している。

**判定: real。** `measurement_freeze` は確かに6 gate／3 comparatorだが、`known_axes_freeze` にも6／3があり [known_axes_freeze.json:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/output/s1-freeze/known_axes_freeze.json:28)、[同:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/output/s1-freeze/known_axes_freeze.json:619)、`holdout_freeze` に4／2がある [holdout_freeze.json:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/output/s8b-freeze/holdout_freeze.json:172)、[同:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/output/s8b-freeze/holdout_freeze.json:526)。関連 pinned freeze 全体では16 gate／8 comparatorである。さらに manifest のコメントは23件 key-set を「独立改竄境界でも恒久 membership でもない」と明記する [test_frozen_artifacts.py:87-89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_frozen_artifacts.py:87)。

ただし、静的に確認した16 gate は exact、8 comparator は外周空白付きで、定性的結論は現在成立する。

**成果物影響:** 現在の bytes に直ちに差はないが、未列挙または将来追加された freeze を「manifest で閉じた」と誤認すると、再 materialize 時の token・variant・材料参照 drift を検知できない。

**推奨する最小の対処:** 3つの関連 freeze を明示的に全数棚卸しし、「23件は現行 bytes pin」とだけ記述する。恒久 membership や semantic freeze 検査はU-3/U-4へ残し、本 wave では主張を広げない。

## 所見6 — U-2 allowlist は既知値の `str` subclass を意図せず拒否し得る

**要約:** 現行 `isinstance(configuration, str)` と新しい hash-set membership の組合せは、既知ラベル subclass の受理挙動を変える。

**判定: real（direct caller の受理集合）。** 現行型検査は exact型でない [s1_direct_comparison.py:494-497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:494)。例えば内容が `"stock_common"` で別 `__hash__` を持つ `str` subclass は、現行では4分岐を通らず flags-only yield へ達するが、プランの `configuration not in frozenset` [plan.md:76-81](</work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:76) では拒否され得る。U-2 が許可したのは未知ラベル拒否であり、既知内容の追加縮小ではない。

**成果物影響:** direct caller の既知6構成セルが新たに materialize refusal となり、certified 集合・材料レポート・試行台帳から予定セルが欠落する。

**推奨する最小の対処:** exact文字内容を認可した後、分岐には allowlist 側の exact `str` 定数を渡す。既知内容 subclass の維持と未知 subclass の拒否をそれぞれ負例・正例で固定する。

## 所見7 — 通常の6構成と flags-only 2構成は維持される

**要約:** exact built-in `str` の公式経路では、`stock_common` と `p2_2_flag_opt` を含む6構成の挙動は変わらない。

**判定: refuted。** 公式 S1 domain は6値 [s1_measurement_freeze.py:39-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_measurement_freeze.py:39)、S8b も同じ6値 [s8b_holdout_freeze.py:76-83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_holdout_freeze.py:76) で、holdout verifier が binding を再構成する [同:809-813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_holdout_freeze.py:809)。`prepare_cell` の4分岐後、残る2値はそのまま `resolve`／yield へ進む [s1_direct_comparison.py:516-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:516)。

**成果物影響:** exact公式入力について certified 選択・材料レポート・試行台帳の受理集合と参照は不変。

**推奨する最小の対処:** プラン済みの6値正例、flags-only で patch/quarantine が呼ばれない検査、producer-domain drift guardを維持する。

## 所見8 — `sort_best.comparator` への波及経路は見つからない

**要約:** 提案どおり trigger marker 分岐内だけで代入する限り、sort comparator は逐語保持される。

**判定: refuted。** trigger marker は [axis_trigger_gating.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/axis_trigger_gating.py:23)、sort marker は [p3_s4_loop_sort.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_sort.py:96) で別値。S1 は構成ごとに marker・patch を対で選ぶ [s1_direct_comparison.py:516-535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:516)。既存テストも comparator の逐語引き渡しと sort marker を固定する [test_s1_direct_comparison.py:273-309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_s1_direct_comparison.py:273)。

**成果物影響:** 現行 comparator bytes、そこから得る `src_token`・variant、certified/material/trial 参照は不変。

**推奨する最小の対処:** planned `sort_quarantine_preserves_outer_whitespace_bytes` を残し、trigger guard を外す mutation で固定する。

## 所見9 — 新設拒否が retry／上位 except から fail-open する経路はない

**要約:** `DriverError` や正準化失敗は、retry後の成功扱いや certified 扱いには変換されない。

**判定: refuted。** S1 は `DriverError` を明示的に再送出する [s1_direct_comparison.py:807-819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:807)、main は refused 終了にする [同:887-894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:887)。transient 判定は cause/context 内の `OSError`／`SubprocessError` だけ [同:592-601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:592)。Oracle も非transient prepare 失敗を `binding-refused` とし [s8b_oracle_driver.py:1410-1429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1410)、最終的に `protocol_violation` へ倒す [同:1482-1502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1482)。loop の広い except も certified ではなく abort を記録する [loop.py:272-293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/loop.py:272)。

**成果物影響:** 拒否対象が certified 選択へ混入することはなく、材料・試行台帳では refusal／abort／protocol violation として残る。

**推奨する最小の対処:** 例外型を維持し、S1だけでなく floor/oracle の未知 configuration が retryされず completedにもならない外周テストを追加する。

## 総括

- P1 の「唯一の共有 materialize 境界」は偽であり、このまま実装へ進めない。
- `quarantine` 内 fold に加え、pre-identity の materialized-hole assertion が必要。
- reject-only `diffq-*` も正準 identity に揃えなければ試行台帳の多重化が残る。
- P-D は raw SHA しか測っておらず、実 `src_token` と end-to-end 受理集合を再測定する必要がある。
- 凍結物は実際には16 gate／8 comparatorで、23件 manifest は現行 pin にすぎない。
- exact公式6構成、flags-only 2構成、sort comparator 非干渉、fail-closed 例外経路は静的に成立する。
- pytest・build・freeze 再生成は実行しておらず、緑とは報告しない。