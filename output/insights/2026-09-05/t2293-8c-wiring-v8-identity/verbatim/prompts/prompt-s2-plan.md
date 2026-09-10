単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/s1-brief.md` — 親 brief (scope、確定裁定、不変条件、実アンカー表 A1〜A17、provisional 裁定 (P1)〜(P6))
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/decisions-verbatim.md` — D1616 / D1561 / D1190 / D1555 の逐語
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/design-doc-verbatim.md` — `docs/phase3-8c-wiring-design.md` の逐語 (特に §1、§4.1〜4.2、§5、§6.2〜6.5、§7.1、§8、§11、§12、追記訂正 2026-09-03)
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/t2261-insight-s6-verbatim.md` — 衝突を発見した実測の逐語
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/t524-ruling-stage4.md` と `refs/t524-ruling-stage6.md` — 稼働中 wave (実験単位 = slot、attempt registry v3、acceptance receipt v5) の設計前提。**この前提と食い違う案を出してはならない**

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-design` である。コードはすべてこの worktree の中を読む。HEAD は local main `97ee3cd3a` と同一。

## 依頼

**これは設計 wave であり、実装しない。** 成果物は `docs/phase3-8c-wiring-design.md` §11 V-8 行の追記と関連節への追記節である。お前の仕事は、その追記節に書く**解消案の設計を file:line 粒度で起草する**ことである。設計は「実装 wave が触れる file と関数、exact key、拒否条件」を名指しし、実装 wave がそのまま受入条件にできる粒度にする。

出力は 4 部構成にする。各主張に [実測] (現物を読んだ) か [推測] を付けろ。

## 依頼 1 — 親 brief の実アンカー表と provisional 裁定の検証

A1〜A17 を現物で再確認し、誤り・過大・不足を表にせよ。特に次を現物で確かめろ。

- A2 の `CampaignConfig.trial` を物理 run ごとに変える案 (P1) が、`trial` を identity 以外の目的で読む箇所と衝突しないか。`grep -rn "\.trial\b\|trial=" orchestrator/campaign/` を全件見て、`p3_b4_protocol.driver_kind_from_identity` (trial を driver 選択の key にする) や `_campaign_cfg_for_site`、`campaign.lock` の identity 照合 (`ident.ensure_campaign_identity`)、A-1 non-certifying 分岐 (`ident.is_a1_non_certifying_config`) が `trial` の値に依存していないかを列挙せよ。
- A8 の `_assert_resume_allowed` と A17 の generation loop の関係: 現行の registered 8c trial (`generations == 2`) が Pegasus (`allow_resume=False`) で 2 世代目を同 layout に走らせられるのか。走らせられないなら、その事実は本 wave の解消案の前提にどう影響するか (P4 の専用 executor の必要性)。
- A13 の `planned_campaign_run_identity` が本当に topology 外で未参照か。`build_recovery_envelope` の caller (`p3_autonomous_workload_trial.py` の `_prepare_origin_trial_runtime` 付近) が member material をどう作っているか。
- A11 / A12 の FC03 3 項等式と `execution-provenance/v1` exact key。producer 不在の裏取り (`execution-provenance/v1` を書く関数が repo に無いこと)。
- t524 の attempt slot `campaign_id` (`trial_registry.py` の `_ATTEMPT_SLOT_KEYS`、`_reserve_registered_attempt_slot` の slot 照合 `slot["campaign_id"] == binding.campaign_id`) が論理 campaign_id を前提にしていること。物理 run identity を slot へ入れる必要が無いこと (P5)。

## 依頼 2 — 解消案の設計 (file:line 粒度)

(P1)〜(P4) を土台に、次を確定せよ。採用できない provisional 裁定があれば理由付きで対案を 1 つに絞れ。

1. **2 層 identity の定義。** 論理 campaign (`binding.campaign_id` = `PreparedCampaignIdentity.campaign_id`、1 trial 1 つ) と物理 campaign run (`campaign_run_identity[q]`、33 個) の名前・導出式・完全修飾表記 (D75)。導出式は決定的で、run plan 作成時に固定でき、`ident.campaign_id` の既存関数だけで計算できること。`trial` 接尾辞の書式 (例: `-q00`〜`-q32`) と、既存 `trial` 値 `f"{trial_id}-{workload}"` との衝突不能性 (接尾辞付き値が別 trial の素の値と一致しないこと) を示せ。
2. **claim / layout / WAL の分離。** `loop.py:_authorize` の claim、`exploration_campaign_layout(campaign_run_identity)`、`_assert_resume_allowed`、`done` seed が、物理 run ごとに別になることを現物の行で示せ。claim root (`env_scope_dir(...)/claims`) が共有でも 33 claim が衝突しないこと (`protocol_digest` が `trial` を含む) を `campaign_claim._scan_protocol_conflicts` の条件で示せ。
3. **run plan への束縛。** `TopologyMember.planned_campaign_run_identity` を物理 run identity の正本にする。`MemberRecoveryMaterial` を作る側 (caller) がどこで 33 個の `campaign_run_identity` を計算して渡すか (file / 関数)。envelope の create-only 性 (§7.1) により予約前に固定されることの確認。
4. **証拠側の結線。** `execution-provenance` への `campaign_run_identity` 追加 (exact key 集合の変更点、schema version を v1 のまま拡張するか v2 にするかの判断と理由 — producer 不在・凍結 artifact 不在を根拠に書け)。`reflux_formal_consumer` に足す条件 (どの `FormalReasonCode` に載せるか、新 code が要るか) — 「`execution_provenance.campaign_run_identity == run_plan.members[q].planned_campaign_run_identity`」と「33 値の相異」を、既存 FC03 の 3 項等式を**残したまま**足す形。`_validate_bijection` (`FC05a` の `build_attempt_id` 相異) との関係 (冗長か、独立か) を書け。
5. **producer 側の最小要件。** 物理 run の `execution-provenance` を誰がいつ書くか (現行不在)。WAL の trigger binding record (`wal.log_trigger_binding`、D1555 が指摘した producer/consumer の shape 不一致) と `execution_receipt` から `campaign_run_identity` をどう取るか。ここは「実装 wave の受入要件」として境界だけ固定し、実装しない。
6. **実行器。** origin topology mode の executor の置き場所と signature (P4)。`for generation in range(...)` (A17) との排他、`_assert_fresh_campaign_state` を 33 layout それぞれに掛けること、report の `campaign_id` (論理) と `campaign_runs` (物理 33 件) の exact key、`autonomous_trial_completeness.py` の exact key を optional で同時更新する規律 (§6.5)。
7. **既定経路の不変。** originless の exploratory / registered trial の run-start・report・`launch_admission_sha256`・lifecycle の bytes が変わらないことを、変更点ごとに「発火条件 = origin capability 発行時だけ」で示せ。
8. **稼働 wave との整合。** t524 の attempt slot / acceptance receipt v5 / prereg_generation、t1851 (s8b、`campaign_run_id` と測定世代) に対して、本案が**触れる file が 0 件**であること、または触れるなら何を。

## 依頼 3 — 却下した案と恒真化の監査

親の (P6) に加え、次を各 1〜3 行で判定せよ: (a) capability に `campaign_run_identities: tuple[str, 33]` を足す、(b) 33 capability を発行する、(c) FC03 の `execution_provenance.campaign_id` 項を物理値に置き換える (3 項等式を崩す)、(d) `search_config["origin_query_ordinal"] = q` を `trial` 接尾辞の代わりに使う、(e) claim を trial 単位で 1 つにして 33 run を同 process で回す、(f) `planned_campaign_run_identity` を検査せず「33 layout が実在する」だけで物理実行を認める。
恒真化の監査: 提案する各検査について「何を偽装すると素通りするか」を 1 行で書け。

## 依頼 4 — 裁定パッケージ候補と実装 wave への受入要件

設計上の択一が残るなら、各項目に (択一、親推奨、採らない場合の成果物影響) を付けて列挙せよ。実装 wave への受入要件 (§12 へ追記する項目) を変異事前登録の候補 (変異位置の file:関数、無効化する述語、期待する赤) 付きで 6〜10 件書け。

## 制約

- 読取専用である。書込可能 tmp が無いので pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 実装・docs 編集・commit をしない。出力は本 file への回答だけ。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、(P1)〜(P6) の採否・残る択一の件数・実装 wave が触れる file 数を 10 行以内で書け。
