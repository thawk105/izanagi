[severity: must-fix] [攻撃シナリオ] 追跡済みの reservation 生成 caller が存在しないまま、`_run_workload` に fail-closed 検査を置く案である。テストだけが環境変数を捏造すれば緑にできる一方、実運用の標準 compute 経路は必要な `IZANAGI_RESERVATION_*` を供給できない。これは「wrapper と enforcement は同じ wave、成功 caller を追跡済みテストで固定する」という既裁定にも反する。[根拠 s2-plan.md:93-120,170-175; docs/decisions.md:17449-17492; output/insights/2026-08-16_t330-scr-single-process/s4-adjudication.md:18-33,112-132] [提案] 段 4 を止め、ユーザーの再裁定を得る。配線するなら追跡済み launcher、実 reservation の生成、成功経路の positive control まで同じ wave に含める。

成果物影響: 放置すると正当な Pegasus compute 入力も driver 到達前に拒否され、completed report の受理集合から全標準 compute run が脱落する一方、fixture テストだけは成功し得る。

[severity: must-fix] [攻撃シナリオ] 配線位置がプランと handoff で一致せず、どちらも共通 sink ではない。`_run_workload` への配線は直接の `drive_iteration` を覆わず、`resolved_site == PEGASUS_COMPUTE` 分岐への配線は `OTHER` と injected drive を覆わない。両経路が合流して実測を開始するのは `loop.run_campaign` である。[根拠 s2-plan.md:93-106; handoff.md:27-40,75-79; p3_autonomous_workload_trial.py:1182-1219; p3_s4_loop_trigger_gating.py:549-604,718-831; orchestrator/campaign/loop.py:92-136] [提案] 裁定後は `run_campaign` の measurement authorization に sealed reservation capability を要求し、上位層は同じ証拠を report に転記する構造へ直す。

成果物影響: 放置すると迂回経路の `EvalResult.certified`、campaign WAL、Layer 3 の admitted campaign 参照が allocation receipt なしで生成・受理される。

[severity: must-fix] [攻撃シナリオ] 親 P3 の「attestation は 8c で実際に走る」という二分は偽である。`OTHER` は実測を許可されるが `attestation_mode == "none"` のため、authorization は `attest_and_build_receipt` より前に return する。`do_build=False` も build を省くだけで campaign measurement を止めない。[根拠 brief.md:70-71; orchestrator/campaign/env_contract.py:283-303; orchestrator/campaign/loop.py:61-89; p3_s4_loop_trigger_gating.py:319-347,583-604] [提案] 保証を「標準 Pegasus・required-attestation 経路」に限定するか、正式な 8c では `OTHER` を非認証 exploratory として成果物から明示的に除外する。injected driver も別の carve-out として列挙する。

成果物影響: 放置すると `OTHER` の campaign outcome、fitness、WAL COMMIT は calibration attestation なしでも `certified` 値を持ち、report がその値を保持する。

[severity: must-fix] [攻撃シナリオ] completeness 案が「receipt を主張した場合だけ検査する」ため、receipt producer を削除する変異が検査自体を無効化する。さらに report shape を変えながら schema v3 を据え置くため、receipt のない旧 v3 と新 v3 を区別できない。これは恒真な保証の典型である。[根拠 s2-plan.md:108-126; docs/decisions.md:17179-17195; docs/failures.md:7734-7779; p3_autonomous_workload_trial.py:119-120] [提案] report schema を更新し、receipt の有無ではなく独立に再導出した site、contract、measurement 実行事実から必須性を判定する。receipt は世代ごとの durable journal に封印し、report verifier が独立に照合する。

成果物影響: 放置すると `status="complete"`、cell outcome、Layer 3 admission を保持したまま allocation receipt を丸ごと削除した report が completeness を通る。

[severity: must-fix] [攻撃シナリオ] 現行 reservation は単一プロセスや allocation provenance を証明しない。binding は caller の環境変数から読み、検査するのは主に PBS job、boot、時間、容量であり、現在 hostname、script digest、nonce を scheduler 側の権威と照合しない。プランが列挙する host/script/nonce は記録しただけでは保証にならない。[根拠 orchestrator/campaign/reservation.py:27-55,159-175,218-277; docs/failures.md:7890-7932,8238-8262; docs/decisions.md:18127-18155] [提案] scheduler または kernel 側の caller 外 authority による create-only receipt を使い、D435 の lifetime、reach、authority、over-rejection positive を満たす。できない場合は保証名を「caller self-consistency」に弱め、single-process/allocation attestation を主張しない。

成果物影響: 放置すると重複プロセスで汚染された throughput・fitness でも outcome は `certified` のままになり、report/台帳に自己申告の host・script・nonce が allocation 証拠として残る。

[severity: must-fix] [攻撃シナリオ] 最大 2 世代を走らせるのに、プランの durable receipt は trial/cell 単位であり、各世代直前の再検査と必要残時間の証拠が completeness に結び付いていない。第 2 世代の recheck を削除しても初回 receipt だけで緑になり得る。[根拠 s2-plan.md:104-120,170-175; p3_autonomous_workload_trial.py:122,2403-2651; docs/decisions.md:18127-18155] [提案] `required_s` の式と安全余白を裁定し、各 benchmark 世代の直前検査を generation journal に記録する。実測した全世代について receipt がなければ completeness を失敗させる。

成果物影響: 放置すると予約期限後に開始した第 2 世代の fitness・bench wall time が report と critic 入力へ混入しても、初回 receipt の参照だけで受理される。

[severity: must-fix] [攻撃シナリオ] 提案テストの「recorded real reservation」は、追跡済み production producer を通すとは明記されていない。環境変数を fixture から注入し、driver 非到達を別の早期 reject で満たせば、既存 C12 と同じ「捏造 fixture にだけ述語を撃つ」テストになる。[根拠 s2-plan.md:151-159; orchestrator/tests/test_s8c_preregistration_predicates.py:399-486,500-533; docs/decisions.md:17884-17917; docs/failures.md:160-166,569-644,2051-2062,2616-2629] [提案] 全先行ゲートを通過する public-path witness を用意し、実 driver leaf の sentinel を観測する。reservation call だけを除去すると同じ入力が受理へ反転する mutation control と、追跡済み実値を production loader が読む positive control を必須にする。

成果物影響: 放置すると runtime の reservation call edge が欠落した実装でもテストは緑になり、receipt のない completed report が受理集合に残る。

[severity: should-fix] [攻撃シナリオ] `single_process_required` を C12 の AST が `FunctionDef` として探すから追加する、という理由は保証の実体ではない。既存 `is_reservation_required` と同じ bit を返すだけなら、`allow_resume` や launch 拒否との call edge は証明されず、規律 2 に抵触する見せかけの closure になる。[根拠 s2-plan.md:83-87; orchestrator/campaign/reservation.py:273-277; orchestrator/tools/evaluate_contracts.py:288-358,578-610] [提案] 名前の存在を closure と数えず、T1184 と canonical API を裁定する。runtime consumer、拒否結果、mutation control が同時に存在する場合だけ C12 evidence を更新する。

[severity: should-fix] [攻撃シナリオ] de-scope 案の「消える保証」は歴史的に不正確である。D431 member 6 は t126/s8b だけを保護し、8c を保護しないと明記している。現在の保証が消えるのではなく、将来の 8c 正式受理条件を追加しないという変更である。[根拠 s2-plan.md:181-228; docs/decisions.md:17900-17917] [提案] de-scope する場合も D431 member 6 は保持し、「現行 8c 保証なし」と「将来の formal acceptance が allocation/PBS/boot/deadline 証拠を要求しなくなる」を分けて記録する。

静的検査のみであり、pytest は実行していない。

## 総括

現状の二択なら de-scope を採り、配線は明示的な再裁定と追跡済み launcher を得るまで止めるべきである。  
プラン最大の欠陥は、production の成功 caller がないのに fixture positive と任意 receipt で保証を成立させようとしている点である。  
親 brief の P3 は `OTHER` の attestation bypass を落としており、「reservation だけが実欠陥」という結論は成立しない。  
親 P4 の compute 分岐も全 measurement 経路の発火アンカーではなく、共通境界は `loop.run_campaign` である。  
したがって C12 は未定義のままであり、この wave をもって 8c の reservation/attestation 保証を閉じたと記録してはならない。