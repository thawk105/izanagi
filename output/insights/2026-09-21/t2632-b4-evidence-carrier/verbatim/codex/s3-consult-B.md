## 1. 4 項の被覆

**判定: refuted。P1 は採用可能。** [プラン](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md:5) の §1〜3 が side channel、§5 が参照点の定義と発効記録、§6 が codec 経由化を被覆する。新規 campaign より前に実装・定義を land する順序は brief:10 とプラン:215 にある。

D2194 項 3 の逐語は、参照点について「**事前登録 §5.1.1 の解釈の確定**」「**最後の `success` に対応する attempt を side channel で引く**」である（[裁定:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md:9)）。プラン:202 はこの定義を採用している。

一次資料 [§4.3:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md:214) の「`reference` 欄を持たせるのが自然」は設計候補であり、必須 field の裁定ではない。whiteboard の時間順 → side channel の iteration／variant／attempt → WAL の commit／bench_done という対応を保存できれば、専用欄なしでも後続の参照点解決は可能。

ただし、次の二つは区別すべきである。

- 「新 object・新 producer は作らない」は、新しい snapshot／receipt 実体を作らないという文脈であり、あらゆる参照欄を禁止する根拠ではない。
- 6 field 列挙も将来の `reference` 欄を永久に禁止する根拠ではない。本 wave で追加する必要がない、という結論で足りる。

[誤前提] としての「reference 欄がなければ次 wave は実装不能」は反証できる。今回、参照点の**適格性確認まで完了した**と扱うことはできない。

## 2. 過剰

**判定: real — nit。追加予定の caller tests に重複がある。**

プラン:301 の `test_v2_campaigns_reach_empty_issuer` は、fixture を v2 化した既存 [test:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py:81) と実質同じ。プラン:305 の unknown-v2-trial も、同プラン:267 で変更する既存 unreadable parametrization の `trial` ケースと重なる。既存 test に assertion を足して兼用できる。

**放置時の影響:** 適格行・参照点・台帳・certified 判定は変わらず、同じ境界を検査する test と fixture 構築が増える。

その他の scope 逸脱は **refuted**。

- プラン:17 は trigger 固有 header を移植しないと明記。先例の `INFORMATION_SOURCES`／`GATE_RECORD`／firewall は [trigger:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop_trigger_gating.py:395) の E 段固有義務であり、base への移植は不要。
- 固定の `schema_version` 文字列はあるが、版間 migration・互換 decoder・schema 台帳の追加計画はない。版管理機構の導入とは区別できる。
- 破損停止・atomic 書込みは記録を保つ局所処理であり、新しい研究 gate ではない。
- [artifact_admission.py:949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/artifact_admission.py:949) は trigger 専用。プランは base に広げない。base report の存在を admission や certified の証明と呼ばなければ、[防壁の射程誤認] は生じない。

## 3. 依頼文と裁定の食い違い — P7

**判定: refuted。親の読みは妥当。**

依頼自身が保存先を `reports/<driver>_provenance.json` と指定し、D2194 項 3 (1) も同じ保存先・iteration ごとの6 fieldを確定している。

実装上、[trigger:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop_trigger_gating.py:299) の `_write_source_preimage_artifact` は、proposal の raw hash を名前にして **materialized source の preimage** を保存する。proposal canonical identity や iteration 対応そのものではない。一方、同 file:427 の `_append_provenance_entry` が iteration merge と checkpoint 前保存を担う。

したがって、report の意味・merge は後者、公開時の堅さは前者を参考にする切り分けでよい。可変 report に source artifact の「異なる内容での再利用拒否」を移植しない点も、checkpoint 前中断後の `certified → duplicate` 回復と整合する。

base に source preimage artifact まで追加すべき根拠はない。追加すれば [権限逸脱] となる scope 拡張である。

## 4. 研究前進の実効性

**判定: real — should-fix。実装の scope は妥当だが、成果の説明と caller の既存説明を限定する必要がある。**

新規 base campaign の CLI 経路で赤 precursor が出た場合の変化は次のとおり。根拠はプラン:47・68・202 と、一次資料 [12 field 対応表:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md:225)。

| D2100 field | 本 wave 後の出所 |
|---|---|
| `initial_proposal_sha256` | harness が読んだ document の canonical hash が直接残る。hash 未提供の直接 API 呼出しは null のまま |
| `attempt_id` | iteration → WAL build attempt の対応が残る。ただし B-4 scheduled attempt ID との同一視・割当ては未実装 |
| `digest_red_classes` | 対象 attempt の reject WAL 証拠へ辿れる。B-4 分類値の構成・受理は別 |
| `reference_tps`・`reference_snapshot_hash`・`reference_receipt_hash` | 先行 success があれば、祖先候補の量と record hash を辿る出所・定義が揃う。適格な参照点としての確定は未完了 |
| `reference_is_unique` | 全 PerfConfig／env_tag 一致の証明不足が残る。特に reps／ycsb_max_ope |
| `block_id`・`workload`・`calibrated_workload_member`・`bootstrap_member`・`arm_digest_received` | 本 wave では不足を解消しない |

caller は [caller:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py:93) で候補ごとに `_MISSING_SOURCES` を展開するため、**赤候補1件につき12件のまま**。これは scope と整合する。裁定 (4) は「`trial` 読取りを既存 codec 経由へ直す」であり、side channel consumer の追加は要求していない。[consumer 取り残し] として読み取り機能を増設する必要はない。

修正すべきなのは説明である。

- caller:56 と :92 の「current storage format」「All twelve sources are absent」は、新しい carrier を含む保存形式全体の説明としては古くなる。「この caller が読む checkpoint／lock だけでは構成できない静的不足分類」と限定する。
- [brief:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage1-brief.md:5) の「不足報告 + 空 batch 到達」は、**赤候補あり → 不足報告・issuer 未呼出し／候補なし → 空 batch で issuer 到達**の二経路と明記する。caller:158 が実際に分岐している。

**放置時の影響:** 適格行・台帳・certified 判定は増えないまま、出所の保存と適格行の構成、または赤候補からの issuer 到達を混同して成果を過大評価し得る。

この限定を入れれば、本 wave の完了判定は達成可能。D2120 項 5 の「非空発行経路の完成・条件 9 の充足・T-2632 達成には数えない」とも整合する。

## 5. 局所修正の可否

**判定: refuted。プランの最小修正で足りる。**

caller 全体で lock の内容を利用するのは、読込み・object 検査と `trial` 取得だけ（caller:67・68・73）。他 field を読む箇所はない。

プラン:224 の byte decoder と :230 の `decoded.identity.get("trial")` で足りる。[codec:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/campaign_lock.py:404) の `CampaignLockCodecError` は `ValueError` 派生なので、既存 caller:82 の catch で `CampaignInputUnreadable` に写る。codec:934 の v1 branch は trial 必須ではないため、brief:23 の無条件添字よりプランの `.get` が適切。

既存 unreadable test の8分岐は [test:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py:214) にある。v2 化で変更が必要なのは正常 lock fixture と未知 trial の作り方であり、欠落・壊れた JSON・whiteboard 型・row・result 欠落・深い JSON の意図は維持できる。プランには分岐削除がない。[手順漏れ] は認めない。

## 6. 削除・非接触

**判定: refuted。不要な削除・凍結面への変更は計画されていない。**

プラン:295 は loader stub の capture 対応だけを更新し、検証失敗時の `capture == {}` を維持する。既存 [test:9362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py:9362) の意図を保っている。

プラン:161・215・§8 は、sort／trigger driver、共有 duplicate 評価ロジック、凍結事前登録、bootstrap 集合、admission を非変更としている。whiteboard の5 fieldと planner 非参照の検査もある。caller fixture の v2 化を理由に、base の legacy duplicate fixture まで一律に書き換える必要はなく、その計画もない。

項目4の説明修正と、base `drive_iteration` docstring の手順に provenance 保存を挿入する程度で十分。既存契約の削除や追加の gate・台帳は不要である。

## 総括

**must-fix は認めない。** P1・P7 と caller の局所修正は妥当。**should-fix は成果・不足報告の説明の限定、nit は重複予定 test の統合**である。

本 wave は出所の保存と参照点定義を前進させるが、適格行の生成・参照点の適格性証明・非空発行の完成までは達成しない。静的検査のみで、ファイル変更・テスト実走は行っていない。