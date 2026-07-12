# 段 8a E 段実装設計 — 3 レンズ敵対レビューの一次資料 (finding 全文・裁定台帳)

- 日付: 2026-07-12 / workflow: wf_3ee6392c-870 (3 レンズ並列・独立コンテキスト・
  agentType=Explore read-only、計 23.0 万 token / 14.3 分)
- 対象: E 段実装設計 v1 (provenance 受け皿 = 監査 L4-1 の宿主確定を含む)。設計書は
  scratchpad (セッション限り) — 裁定反映後の実体が正本: `p3_s4_loop_trigger_gating.py` /
  `auditor_gate.py` / `docs/phase3-s8a-trigger-runbook.md` / coder 定義草案 insight
- verdict: 3 レンズ全員 adopt-with-conditions。must 3 (独立 2 — FC-4 と regression MF1 は
  同一指摘の収束) / should 10 / nit 5。全採用 (部分採用 1 = regression SF4)
- 決定の要旨は D51 (decisions.md)。本 insight は finding 全文の凍結

## レンズ: fails-closed (規律 2/3 — 欠落・破損・経路迂回で黙って通らないか)
**verdict: adopt-with-conditions**

### [must-fix] FC-1
- claim: §2 の書き込み順序『drive_iteration が checkpoint 保存直後に provenance を書く』は、entry 記録を WAL commit と checkpoint 前進の後ろに置くため、provenance 書き込みで例外が出ると『WAL は commit 済み・checkpoint は iteration++ 済み・provenance entry 欠落』の中途半端な状態になり、再開時にその iteration は飛ばされて entry が永久に欠落する。設計が謳う『自動で忘れ得ない構造』はこの境界で破れる (fail-open)。
- evidence: p3_s4_loop.py:739-745 (drive_iteration: state.iteration+=1 → run_one_iteration [この中で run_campaign が STAGE_COMMIT を焼く:647-657] → save_loop_state)。p3_s4_loop_sort.py:385-389 も同順。設計 draft L68『checkpoint 保存直後に呼ぶ』・L72『例外 → iteration 全体が止まる』は、commit/checkpoint が既に永続化された後の停止なので『止まる』が『記録が残る』を意味しない。
- suggested_fix: 書き込み順序を規定する: (a) header (information_sources/liveness_binary/firewall — outcome 非依存) は drive_iteration 入口 (run_one_iteration の前 = build/commit の前) に書く。(b) per-iteration entry は run_one_iteration の後・save_loop_state の前に書き、provenance 書き込み失敗時は checkpoint を前進させない (再開で _resolve_duplicate 経由で同 iteration を replay)。(c) _resolve_duplicate / replay 経路 (p3_s4_loop.py:557-585, s8a_trigger_sweep.py:329-335) でも entry を書く義務を明記 — 中断再開で commit 済み variant の entry が欠落する穴を塞ぐ。
- **裁定: 採用 (must)。ヘッダ = drive_iteration 入口 (build 前)、entry = run_one_iteration 後・save_loop_state 前。entry 失敗で checkpoint 非前進 (テスト test_drive_iteration_entry_failure_blocks_checkpoint)。duplicate 経路も drive_iteration の一括 entry 書きで記録される。**

### [should-fix] FC-2
- claim: 手本の _write_provenance は非 atomic 書き込み (open(path,'w') 直書き、tmp+os.replace 無し) である。設計はこの様式を『踏襲』しつつ『破損 JSON で例外 (fails-closed)』を新たに要求する。両者を素直に合わせると、書き込み途中のクラッシュで truncated JSON が残り → 以後の全 iteration が『破損で例外』で恒久停止 (campaign が provenance で brick)。atomic 化の指定が無い。
- evidence: s8a_trigger_sweep.py:362-364 は os.makedirs 後 open(path,'w')+json.dump で直書き (LoopState の save_loop_state:405-413 が使う PID-tmp + os.replace とは非対称)。設計 draft L50-53 は『_write_provenance の様式を踏襲』、L73-74 は『JSON 破損も例外』。
- suggested_fix: provenance 書き込みを save_loop_state と同じ atomic 様式 (f'{path}.{os.getpid()}.tmp' → os.replace) にする。§2 に『手本は非 atomic だがここは atomic に強化する』と明示 (踏襲の一語で non-atomic を継がない)。
- **裁定: 採用。atomic 書き (PID-tmp + os.replace、save_loop_state と同様式)。手本の非 atomic は継がない旨を docstring に明記。**

### [should-fix] FC-3
- claim: 手本 _write_provenance は既存ファイルが壊れていると except で existing={} にリセットし、既存 entries を黙って捨てて上書きする (fail-open な truncation)。設計は逆に『破損で例外』を求めるが、merge 意味論 (スキーマ進化で未知キーが増えた既存ファイルをどう扱うか、entries を落とさないか) が未規定。『破損=例外』と『部分実行で truncate しない』の両立条件が曖昧。
- evidence: s8a_trigger_sweep.py:347-353 (except (JSONDecodeError, OSError): existing={} で既存 entries を silent 破棄 → entries={**existing(空), **prov} で上書き)。設計 draft L52『merge 書き (部分実行で truncate しない)』と L73-74『破損で例外』が同じ手本の中で相反。
- suggested_fix: merge 規則を明文化: (1) 既存ファイルが読めるが未知キー/新スキーマ → 保存 (捨てない、前方互換)。(2) JSON decode 不能 → 例外で停止 (手本の silent reset を継がない、FC-2 の atomic 化で自傷リスクを下げた上で)。test (c)(d) が両方を別ケースで押さえることを §7 に明記。
- **裁定: 採用。未知キー保存 (前方互換、test_provenance_preserves_unknown_keys_forward_compat)、decode 不能は例外 (silent reset を継がない)。**

### [should-fix] FC-4
- claim: §3 の『4 点を auditor_gate.py へ純粋移動 (semantics 不変・公開名維持)』は _auditor_reject_result について成立しない。この関数はモジュール大域の SOURCE_REL / MARKER_ID を直接参照して digest を組むため、共有モジュールへ移すには軸定数を引数化する必要があり、署名が変わる = 純粋移動でも公開名維持でもない。『既存 test 無改変で緑』の regression 主張が崩れうる。
- evidence: p3_s4_loop_sort.py:151-172 (_auditor_reject_result が SOURCE_REL:171 / MARKER_ID:171 を大域参照)。同様に _quarantine_and_audit:175-207 も SOURCE_REL/MARKER_ID/genome/state を参照し純粋には切り出せない。
- suggested_fix: 移動対象を『軸非依存な純粋部分』に限定して列挙し直す: AuditorVerdict / AuditorGateFailure / compute_diff_digest / _AUDITOR_VERDICTS / digest 照合ロジックのみ移動。_auditor_reject_result は (diff_region, template_diff_id) を引数化した上で移すと明記し、sort 側は軸定数を束ねた薄い wrapper (後方互換 alias) で旧署名を保つ、と regression 保全の具体を書く。test_auditor_gate.py の『semantics 不変検査』が引数化後の等価性を押さえること。
- **裁定: 採用 (must、regression MF1 と収束)。移動対象を軸非依存部品 5 点に限定、_quarantine_and_audit/_auditor_reject_result は各 driver の wrapper に残置。sort テスト 17 本無改変緑で regression 保全を実証。**

### [should-fix] FC-5
- claim: E 段 gate 通過の根拠 (D50 決定 1 の floor 超地形 + worklog 07-11 判断待ち + ユーザー『進めてください』を承認と解釈した §0 の解釈) が provenance schema に無い。後から監査する者は provenance を見ても『なぜ E 段に入ってよいと判断したか』の gate 根拠を追えない。規律 3 (正しさシグナルを構造化して次の一手の入力に) の観点で、gate 判断こそ記録すべき構造化シグナル。
- evidence: 設計 draft L54-64 の header schema は axis/pin/space_version/information_sources/liveness_binary/firewall のみで gate 判断フィールドが無い。§0 L25-26 で gate 解釈を宣言しているが記録先が無い。D50 L1855-1857 も『E 段へ進むかは人間判断 gate』と記録義務を並置。
- suggested_fix: header に gate フィールドを追加: {basis: 'D50 決定 1 floor 超 3 workload cross-run 再現', approval: 'user 2026-07-12 進めてください → worklog 07-11 (5)/(1) への承認と解釈', firewall_scope: '流すのは生死二値のみ'}。外部入力 (ユーザーの短い指示) をどう解釈したか (規律 6: データとしての解釈) を記録し監査可能にする。
- **裁定: 採用。provenance ヘッダに gate_record {basis/approval/firewall_scope} を追加 — E 段 gate 通過の根拠 (D50 決定 1 + ユーザー指示の解釈) を構造化記録。**

### [should-fix] FC-6
- claim: --extra-source PATH:ROLE のパース規則・失敗時挙動が未規定。PATH:ROLE を単純 split(':') すると ROLE (日本語自由文) にコロンが含まれた場合に壊れ、コロン無しの不正入力を silent に無視すると『読んだ文書が provenance に記録されない』= まさに記録義務が防ごうとしている汚染監査の穴になる (fail-open)。
- evidence: 設計 draft L75-76 は『--extra-source PATH:ROLE で追記可能 (任意、複数回指定可)』とだけ書き、パース/検証/失敗挙動を規定していない。既存 driver の load_proposal_file は『非 bool は fail-open させる (規律2)』(p3_s4_loop.py:702-705) と fail-closed 原則を持つのに、ここだけ沈黙。
- suggested_fix: split(':', 1) で最初のコロンのみ分割 (ROLE 内コロン許容)、PATH/ROLE いずれか空なら ValueError で fail-closed、を §2 に明記。任意オプションだが『指定したら必ず記録、malformed は停止』とし、黙って drop しない。
- **裁定: 採用。parse_extra_source は partition(':') で最初のコロンのみ分割 (ROLE 内コロン許容)、PATH/ROLE 空は ValueError (silent drop しない)。**

### [should-fix] FC-7
- claim: provenance の書き手が drive_iteration に限定されており、実際に全 iteration が通る funnel の run_one_iteration ではない。fixture の main() 経路 (非 --run-iteration) は run_one_iteration を直呼びするため provenance を一切書かない。設計の『run_one_iteration 直呼び…で記録が抜ける穴は無いか』に対し、穴はある — 義務が funnel でなく wrapper に載っており『自動で忘れ得ない構造』の主張より弱い (宣言止まりの構造)。
- evidence: p3_s4_loop.py:820-835 (main の fixture 経路が run_one_iteration を直呼び、drive_iteration を経ない)。p3_s4_loop_sort.py:489-512 も同型。設計 draft L68-71 は provenance を drive_iteration にのみ配線。
- suggested_fix: header 書き込み (軸非依存) を run_one_iteration 側に置くか、run_one_iteration に『provenance 未配線経路は fixture 専用』の assert を入れる。あるいは fixture main が recon insight 非依拠 (記録義務なし) であることを §8 で明記し、F 段の実経路が必ず drive_iteration を通ることをテストで固定 (funnel 保証)。
- **裁定: 採用。fixture main 直呼びは配線確認専用 (偵察 insight 非依拠) で provenance 対象外と docstring/runbook に明記。F 段実経路 (--run-iteration → drive_iteration) が funnel であることをテストで固定。**

### [should-fix] FC-8
- claim: §4 の禁止識別子 grep を『auditor 目視の補助・執行の正本は目視のまま』と位置づけるが、auditor 目視は harness が機械検証できない (digest gate は『auditor がこの diff を見た』ことは保証するが『禁止識別子を検査した』ことは保証しない)。結果、禁止識別子について機械的に fail-closed な唯一の関所は実は grep であり、それを『補助・完全性主張しない』と格下げすると、正本 (目視=機械執行なし) と補助 (grep=非 load-bearing 宣言) のどちらも hard gate として扱われない曖昧さが残る。
- evidence: axis_trigger_gating.py:53-64 (SYNTAX_CONTRACT_FORBIDDEN の執行は D48 決定 2 で『構文恒真検査でなく auditor 目視』とされるが decisions.md:1737 も『auditor 目視 + 偵察退化点の明示列挙』で機械執行でない)。設計 draft L116-117 が grep を『補助 defense-in-depth・完全性は主張しない・正本は目視』と格下げ。
- suggested_fix: grep は禁止識別子について hard reject (subtype='syntax-contract') する fail-closed gate であると明言し、『grep 緑は auditor 目視義務を免除しない』を runbook に明記。目視が正本なのは『grep が捕えない意味的違反 (超集合)』についてであって、リスト上の識別子は grep が機械執行する、と役割分担を分離して書く (どちらが何を執行するかの曖昧さを消す)。
- **裁定: 採用。役割分担を明文化: リスト上の識別子は grep が機械執行する hard gate、auditor 目視はその超集合 (意味的違反)。「grep 緑は目視義務を免除しない」を runbook §1(f)/§2 に明記。**

### [nit] FC-N1
- claim: 禁止識別子 grep が implementation 文字列への部分一致だと、コメントや無関係な部分文字列 (例: `// avoid read_set_`) にも当たり過検出する。方向は安全側 (reject) だが、正当な hole でも稀に誤 reject しうる。
- evidence: axis_trigger_gating.py:58-64 の識別子は member 名 (read_set_ 等) の部分文字列。hole は述語代入 1 行 (patch:102 `izanagi_gate_pass = true;`) で straight-line だが、grep 対象が単純 substring なら文脈非依存。
- suggested_fix: 識別子境界 (\b) 付き正規表現にするか、C++ コメント除去後に検査する。過検出は安全側なので優先度は低いが §4 に検査の粒度を一文書く。
- **裁定: 採用。識別子境界 (\b 前置) 付き正規表現。過検出は安全側として許容する旨を docstring に明記。**

### [nit] FC-N2
- claim: provenance 宿主パスが『<campaign root>/reports/』で proof-chain 外・guard_write 通過という主張は正しいが、実際の書き手は driver の Python (open/json.dump を Bash 経由で実行) であり Write ツールでないため guard_write hook 自体が適用されない。主張の結論 (書ける) は正しいが根拠の一語が不正確。
- evidence: guard_write.py:45-59 は runs/・campaign.lock・build-variants のみ保護 (reports/ は非対象) だが、これは Write/Edit/NotebookEdit ツールへの hook (guard_write.py:104-119)。driver の直書きには効かない。
- suggested_fix: §2 の表現を『reports/ は proof-chain 保護対象外 (guard_write が守るのは runs/campaign.lock/build-variants のみ)』に精密化。
- **裁定: 採用。設計文言を「reports/ は proof-chain 保護対象外 (guard_write が守るのは runs/・campaign.lock・build-variants のみ)」に精密化 (driver 実装の comment)。**

### 問題なしと確認された主張 (checked_claims)
- reports/ は proof-chain 保護外で書き込み可 — guard_write.py:45-59 が保護するのは output/campaigns/*/runs/・campaign.lock・build-variants のみで reports/ は非対象、を確認
- 軸定数を axis_trigger_gating から全て import する方針は D48 必須条件 5 (decisions.md:1738-1739, 1804) および axis_trigger_gating.py:22-32 の単一正本規定と整合
- auditor 機械 gate の digest 照合は宣言止まりでなく実照合 — p3_s4_loop_sort.py:191-196 が実 working_diff の sha256 と auditor.diff_digest を突合し不一致で AuditorGateFailure、を確認 (§3 の移動元が本物の gate)
- SYNTAX_CONTRACT_FORBIDDEN (thid_/result_/read_set_/write_set_/node_map_) は axis_trigger_gating.py:58-64 に実在し、coder 定義への転記義務 (D49 条件 4, decisions.md:1803-1804) の転記元である
- kUnset→true の fail-safe sentinel 契約は骨格 patch (silo-backoff-trigger-gating-variant.patch:96,102,124) と axis_trigger_gating.py:54-56 の両方で一致
- hole = #if BACKOFF_TRIGGER_GATING 枝内の述語代入 1 行 (patch:101-105) で、gate 変数宣言 (patch:84) と gated call (patch:107-111) は marker 外 = coder 不可触、という §0 の記述は骨格現物と一致
- verdict/prior_critic_reverse の fails-closed 検証 (未知値・非 bool で例外) は既存 driver (p3_s4_loop_sort.py:339-357, p3_s4_loop.py:698-706) に実装済みで、§7 テスト方針と整合
- E 段へ流すのは生死二値のみ (floor 超地形あり) という firewall は D50 決定 1 (decisions.md:1855-1857)・D48 条件 7・axis-onboarding §3-D (160-165) と一致

## レンズ: リーク制御 (D39 決定7 / D45 / D48 条件7 / axis-onboarding §3-D firewall)
**verdict: adopt-with-conditions**

### [must-fix] MF1
- claim: §5 が IzanagiAbortReason enum を『骨格抜粋として見せる』と指示する一方『要因別の意味説明・頻度・どれが効くかの示唆は書かない』とも指示しており自己矛盾。骨格 (patch) の enum 本体は各メンバに意味コメントを持ち、kInsertNode/kScanNode には『YCSB never fires』(= 不感=構造ゼロ、要因部分集合の絞り込みヒント) が付いている。『骨格抜粋』を素直に verbatim で見せると、この意味説明と不感 2 要因のヒントが coder 入力へ漏れ、§5 自身の禁止と衝突する。
- evidence: 設計 §5 L135-136 (enum を骨格抜粋として見せる/意味説明は書かない) vs patches/silo-backoff-trigger-gating-variant.patch L56-67 (enum に per-member 意味コメント + L65-66 『insert/scan: YCSB never fires』)。不感 2 要因は axis_trigger_gating.py:48 GATEABLE_REASONS から除外済み=偵察隣接の絞り込み事実。
- suggested_fix: §5 に『coder へ見せる enum 抜粋は裸のメンバ名のみ (kUnset..kScanNode) とし、骨格ソースの per-member コメント (意味説明・YCSB never fires を含む) を機械的に strip する』と明記し、抜粋生成の出所 (手書き固定 or コメント除去済み) を driver/coder 定義草案の側で固定する。
- **裁定: 採用 (must)。coder へ見せる enum 抜粋は裸メンバ名のみに固定 — coder 定義草案に strip 済みテキストを埋め込み、実 patch からの都度抜粋を runbook §1(b) で禁止。**

### [should-fix] SF1
- claim: §2 が E 段 provenance の書き手を『s8a_trigger_sweep.py の _write_provenance の様式を踏襲』と規定するが、その手本関数は header に effective_reasons (=偵察の勝ち要因部分集合そのもの)・floor_cv・freq_source という診断数値を焼く。『様式踏襲』を素直にコピーすると、偵察の crown jewel (勝ち gate 部分集合) が E 段 provenance ファイルに載る。provenance は現状 LLM 入力へは読み戻されない (構造的に隔離、下記 checked) が、D48 条件 7 の firewall と防御多重の観点で、手本が診断数値を含む点は明示的な罠。
- evidence: 設計 §2 L50-51 (_write_provenance 様式を踏襲) vs orchestrator/campaign/s8a_trigger_sweep.py:355-361 (doc に effective_reasons/floor_cv/freq_source を格納)。effective_reasons の中身は偵察の勝ち要因 (D50 実効 3bit)。
- suggested_fix: §2 に『E 段 provenance header に含めてよいのは axis/pin/space_version/information_sources/liveness_binary/firewall のみ。手本 (_write_provenance) が持つ effective_reasons/floor_cv/freq_source は偵察診断値ゆえ明示的に除外する』と列挙し、テスト §7 に『provenance header にこれら禁止キーが現れたら fail』の否定 assert を足す。
- **裁定: 採用。_write_provenance に偵察診断キー (effective_reasons/floor_cv/freq_source) の書き込み拒否を実装 + テストの否定 assert (test_provenance_write_rejects_recon_diagnostic_keys / test_provenance_header_writes_sources_gate_record_and_firewall)。**

### [should-fix] SF2 (uncertain 申告)
- claim: §5 が coder 定義を sort 版と『同構造』とするだけで coder の入力スキーマ全フィールドを列挙しておらず、firewall 監査 (E 段へ流すのは生死二値のみ) に照らした入力面の点検が設計上欠落。sort 版の入力は baseline:{throughput_ops_sec:88124.1, abort_rate_pct:7.9} という具体診断数値ブロックを含むため、『同構造』を素直に踏襲すると baseline の throughput/abort 実数が trigger-gating coder 入力に載る。D48 条件 7 の文言 (E 段へ流してよいのは生死二値のみ) に照らすと baseline 実数の是非が未判断のまま。
- evidence: 設計 §5 (入力スキーマの列挙なし、planner_direction 読み方のみ言及) vs .claude/agents/coder-v4-autonomous-sort.md L48 (baseline throughput_ops_sec:88124.1/abort_rate_pct:7.9 を入力に含む)。firewall 正本 axis_trigger_gating.py:11-16。
- suggested_fix: §5 に coder 入力 JSON の全フィールド (leakproof_context / 骨格抜粋 / planner_direction / whiteboard / baseline?) を明示列挙し、baseline 数値ブロックを『落とす or stock 汎用値のみ』と firewall 判断を明記。使用する leakproof_context ファイルが trigger-gating 偵察に言及しない汎用版であることも固定。
- **裁定: 採用。coder 入力 5 フィールドを定義草案に全列挙し「入力はこの 5 フィールドのみ」と明記。baseline は E 段 campaign 自身の実測で偵察由来でないため sort 同様残す (根拠を草案に明記)。leakproof_context は汎用版を使用 (runbook)。**

### [nit] N1
- claim: §4 の新規『禁止識別子の機械 grep』reject は subtype=syntax-contract で diff-quarantine 経路 (render_rejections) に相乗りする設計だが、§4/§7 が evidence の中身を規定していない。sort の相乗りヘルパ _auditor_reject_result は violations 等を verbatim で evidence に詰め、render_rejections はそれを critic digest に描画する。syntax-contract の evidence が coder の gate 式全体 (=coder の要因部分集合の推測) を echo すると、それが critic 還流に載る。critic は planner から whiteboard 射影で隔離されるため勝ち筋の planner 到達は無いが、evidence は最小 (マッチした禁止トークン名のみ) に留めるのが project_whiteboard の思想と整合。
- evidence: orchestrator/campaign/p3_s4_loop_sort.py:160-172 (_auditor_reject_result が violations を evidence に verbatim) + orchestrator/critic/digest.py:575-576 (evidence を digest へ描画) + 設計 §4 L116-117。
- suggested_fix: §4 に『syntax-contract reject の evidence はマッチした禁止識別子名のみを記録し、coder の gate 式本文は載せない』と明記。
- **裁定: 採用。syntax-contract reject の evidence はマッチ識別子名のみ (_syntax_contract_reject_result)。式本文の非混入をテストで assert。**

### [nit] N2
- claim: §2 liveness_binary の文字列 'floor 超地形あり (3 workload cross-run 再現、D50 決定1)' は D50 決定 1 の文言と一致し許容範囲だが、'3 workload cross-run 再現' は純粋な生死二値よりわずかに情報量が多い (再現度の含意)。provenance が LLM 入力へ読み戻されない前提では実害なしだが、E 段入力へ liveness を渡す局面が将来出る場合は D50 の生死二値定義に厳密に丸めること。
- evidence: 設計 §2 L62-63 vs docs/decisions.md D50 L1855-1857 (E 段へ流してよいのは生死二値のみ)。
- **裁定: 採用。LLM 入力に渡しうる生死二値は LIVENESS_BINARY="alive" のみに丸め、監査向け詳述は provenance の gate_record 側に分離。**

### 問題なしと確認された主張 (checked_claims)
- make_critic_digest (p3_s4_loop.py:231-248) は render_text(build_digest=calibrator perf) + render_rejections(load_rejections/load_liveness_rejections/load_diff_rejections/load_verify_abort_signals=全て WAL 由来) のみを読み、reports/ や provenance json を一切読まない。project_whiteboard (p3_s4_loop.py:253-265) は state フィールドのみ。grep でも campaign consumer が reports/provenance を読む経路なし → §2 provenance ファイル (information_sources/liveness_binary/firewall/entries) は critic digest・whiteboard・planner 入力から構造的に隔離されている (レビュー中心問 #1 の答=遮断済み)。
- §5 出力スキーマは implementation/justification/confidence のみで value も strategy_summary も無い (設計 §5 L142)。sort 版で削られた strategy_summary 型のリーク面 (coder-v4-autonomous-sort.md L117-121 / p3_s4_loop_sort.py:99-104) は再発していない。
- trigger-gating driver は L.project_whiteboard / whiteboard_for_planner / state_from_dict を再利用するため delta_pct≡None 強制 (_DELTA_PCT_LIVE=False, p3_s4_loop.py:268-281,338-399) と機序フィールド排除が汎用機構経由で継承され、勝ち筋 (性能値・機序) の planner 到達は型と値契約の二重で塞がれている。
- provenance entries の proposal_path が指す coder proposal JSON (implementation=どの要因を gate したか) は coder (tools:[]) が読めず、planner-v4 は D45 で Read 剥奪、偵察 insight のパス文字列も provenance 内に留まり LLM 入力へは載らない → 偵察勝ち点・パスの coder/planner 到達経路なし (中心問 #4 の答=パス文字列も LLM 入力に載らない)。
- coder へ見せる enum の『メンバ名』自体は coder が gate 式を書くのに必須の物理的編集面であり (patch L56-67 の enum は骨格の一部)、勝ち筋 (どの要因を gate すべきか) とは独立 = リークではない。漏れ面は MF1 の per-member コメントに限局。
- auditor gate reject の violations 還流 (p3_s4_loop_sort.py:151-172 → render_rejections) は critic までで、project_whiteboard が critic 帰属を落とし planner へは whiteboard (機序なし) のみ射影されるため、勝ち筋の planner 逆算経路は既存設計で遮断済み (trigger-gating も同機構を再利用)。

## レンズ: regression (既存の緑を壊さないか・既存機構との整合)
**verdict: adopt-with-conditions**

### [must-fix] MF1
- claim: §3 の「4点を auditor_gate.py へ純粋移動（semantics 不変・公開名維持）＋後方互換 alias で既存テスト無改変緑」は _auditor_reject_result と _quarantine_and_audit については成立しない。両関数は軸固有の module-global (MARKER_ID / SOURCE_REL / ENV_TAG) に閉じており、軸非依存の共有モジュールへ verbatim 移動すると当該グローバルが未束縛になり NameError（または placeholder で silent に誤値）になる。
- evidence: p3_s4_loop_sort.py:170-172 の _auditor_reject_result は digest dict に diff_region=SOURCE_REL / template_diff_id=MARKER_ID を焼く。同 L184,186 の _quarantine_and_audit は L.quarantine(marker_id=MARKER_ID, source_rel=SOURCE_REL) と record_diff_reject(env_tag=ENV_TAG) を呼び、型注釈も coder: CoderProposalSort（sort 固有）。これらは s6_sort_sweep.py:174,191,220,262-263 でも MARKER_ID/SOURCE_REL/_BASE/TEMPLATE_PATCH として外部依存されており sort module に残す必要がある。共有モジュールに MARKER_ID は定義できない。
- suggested_fix: 移動対象を「本当に軸非依存な部品」= AuditorVerdict / AuditorGateFailure / compute_diff_digest / 照合コア（working_diff と expected_digest を取る純関数）/ reject-result builder（marker_id・source_rel・env_tag を引数で受ける版）に限定する。_quarantine_and_audit と _auditor_reject_result は各 driver に薄い wrapper として残し自軸定数を注入する。§3 の文面から「純粋移動・公開名維持・無改変緑」を撤回し「軸定数の引数化を伴う抽出＋各 driver の wrapper」と正しく記述する。AuditorVerdict/AuditorGateFailure/compute_diff_digest の3点は同一クラスオブジェクトの alias で無改変緑が成立する（ここは主張どおり）。
- **裁定: 採用 (must、FC-4 と同一指摘の 2 レンズ収束)。同上。**

### [should-fix] SF1
- claim: provenance の fails-closed（INFORMATION_SOURCES 空で ValueError）が iteration の checkpoint 保存「直後」に走る設計だと、静的な設定欠落を毎 iteration ビルド・iteration++ を消費してから検出することになり、fail-fast にならない。
- evidence: 設計 §2 は「ヘッダ = run 開始時に自動で焼く」と「書き手 = drive_iteration が checkpoint 保存直後に呼ぶ（ヘッダ merge＋entry 追記）」を併記し矛盾。drive_iteration の実順序は state.iteration+=1 → run_one_iteration → save_loop_state → digest 書き（p3_s4_loop_sort.py:385-394）で、この直後に provenance を置くと検証が最後尾になる。
- suggested_fix: INFORMATION_SOURCES の必須キー/非空検証は driver 入口（iteration++・build 前、default_cfg 構築時か drive_iteration 冒頭）で実施し、静的欠落は 1 度のビルドも走らせずに落とす。ヘッダ焼きも run 開始時に確定させる。
- **裁定: 採用 (FC-1 と同方向)。INFORMATION_SOURCES の検証は _write_provenance_header (drive_iteration 入口) — 静的欠落は 1 度のビルドも走らせず停止。**

### [should-fix] SF2
- claim: provenance の entry 書きが checkpoint 保存後（post-commit）で raise しうる設計は、iteration が既に加算・save 済みのまま例外→非ゼロ終了となり、retry 時に別 iteration として二重加算/重複 variant を生む窓を作る。
- evidence: drive_iteration は save_loop_state（p3_s4_loop_sort.py:389）で iteration を確定してから digest 書き（L391-394）。ここに provenance 書きを後置すると、その失敗が「checkpoint は進んだが記録は無い」不整合を残す。entries は str(iteration) キーだが retry は check_stop→iteration+=1 で別キーになり冪等でない。
- suggested_fix: 当該 iteration の entry は save_loop_state の前に書くか、checkpoint と同一の逐次・冪等（同 iteration キー上書き）書き込みに畳み込む。provenance 失敗時の再実行が iteration を二重消費しないことをテストで固定（§7 に追加）。
- **裁定: 採用 (FC-1(b) と同一)。entry は save_loop_state 前 + 同 iteration キー上書きで冪等 (test_provenance_entry_merge_preserves_existing_and_is_idempotent)。**

### [should-fix] SF3 (uncertain 申告)
- claim: 新 driver の default_cfg の identity フィールド（spec_slug / search_tag / spec_content / trial）を設計が沈黙している。sort の値を流用すると campaign-id のディレクトリ名（slug＋search_tag）が sort ラベルで焼かれ、campaign 出力の軸別分離（§7.2）が崩れる。
- evidence: campaign_id は CampaignId(slug=cfg.spec_slug, search_tag=cfg.search_tag, cfg_hash8)（ident.py:45-48）。cfg_hash は search_config.axis 差で分かれるので root 衝突はしないが、slug/search_tag はハッシュに含まれず（canonical_preimage は spec_content/ccbench_commit/search_tag/search_config/trial のみ、ident.py:28-34）ラベルとして露出する。§4 は verify=legacy+s2 のみ明記し spec_slug 等に触れない。
- suggested_fix: §4 に trigger-gating 固有の spec_slug（例 p3-s8a-trigger-loop）/ search_tag / spec_content / trial を明示し、sort からの流用を禁止する旨を記す。テスト（§7 の identity 節）で slug/search_tag が sort と異なることを assert。
- **裁定: 採用。spec_slug=p3-s8a-trigger-loop / search_tag=s8a-trigger-autonomous / trial 固有化 + sort と異なることをテストで assert (test_default_cfg_identity_distinct_from_sort)。**

### [should-fix] SF4 (uncertain 申告)
- claim: 既存 provenance JSON 破損で hard raise する設計は、手本（偵察器 _write_provenance）が JSONDecodeError を握って existing={} で継続するのと非対称。provenance は proof-chain 外の診断側チャネルなのに、その破損で loop 全体を止める。kill 中断で partial write した provenance が次 iteration を封鎖し、逐次 merge の耐中断意図と逆行する。
- evidence: 手本 s8a_trigger_sweep.py:347-352 は破損時 existing={} に倒し継続。設計 §2 は「既存ファイルのスキーマ不整合（JSON 破損）も例外」。provenance は reports/ 配下で proof-chain 外（guard_write.py:45-59 は runs//campaign.lock/build-variants のみ保護）＝正しさゲートではない。
- suggested_fix: empty-INFORMATION_SOURCES（記録義務の欠落）は fails-closed のまま入口検証に、既存 JSON 破損は quarantine（破損を退避 or existing={} で継続）にし、診断側チャネルの破損が correctness な loop を止めない設計にする。規律3 の対象は正しさシグナルであり provenance 側チャネルは対象外である点を §2 に明記。
- **裁定: 部分採用 (FC-3 との衝突裁定)。「破損で loop を止めるのは過剰」の停止回避は不採用 — 記録義務の silent 黙殺 (existing={} リセット) の方が害が大きい。ただし復旧材料の保全は採用: 破損ファイルを .corrupt.<unix秒> へ退避してから例外停止 (atomic 化で partial write 自体がほぼ消える前提)。**

### [nit] N1
- claim: §4 の新 subtype='syntax-contract'（禁止識別子 grep reject）は render_rejections で auditor-* 分岐にも専用 hint にも該当せず、else の「フレーム/hole 逸脱（型明示・推理不要）」hint が出る。禁止識別子 reject は hole 逸脱ではないため読み方が誤誘導になる。
- evidence: critic/digest.py:577-588 — subtype.startswith('auditor-') 以外は一律「フレーム/hole 逸脱」hint。syntax-contract は該当せず else に落ちる。
- suggested_fix: critic.digest に syntax-contract 用の hint 分岐を足すか（禁止識別子の混入＝合成枝の語彙違反であり frame 逸脱ではない旨）、subtype を auditor-* 系（auditor 目視の defense-in-depth）に寄せて既存 hint に載せる。§4/§7 でこの consumer 整合を明記。
- **裁定: 採用。critic/digest.py の render_rejections に syntax-contract 専用の読み方ヒント分岐を追加 (フレーム逸脱ヒントの誤誘導を解消)。テスト test_render_rejections_uses_syntax_contract_hint。**

### 問題なしと確認された主張 (checked_claims)
- reports/ は proof-chain 外で書き込み許可 — guard_write._protected_artifact は campaigns/*/runs//campaign.lock/build-variants のみ拒否し reports/ は素通し（guard_write.py:45-59）。ただし harness の python 実行時 open() 書き込みは guard_write（PreToolUse Write|Edit のみ発火）の管轄外であり、guard_write 通過という設計文言は実害はないが厳密には無関係。偵察器も同経路で reports/ に書けている前例あり。
- provenance / INFORMATION_SOURCES は campaign-id ハッシュに非関与 — canonical_preimage は cfg の spec_content/ccbench_commit/search_tag/search_config/trial のみを覆い reports/ 内容や env/実測値は覆わない（ident.py:21-42）。provenance 書き込みは campaign.lock/WAL identity に影響しない。
- D50 教訓の _clear_stale_build_dir は buildcache.build 内（run_campaign 共有経路）にあり、新 driver も run_campaign 経由・cache_root=build-variants で自動的に効く（buildcache.py:110, 177-189）。sort と同 PIN d706650 の worktree 隔離既定 ON＋ccbench_dir=sub＋cache_root 明示は sort driver 現物（p3_s4_loop_sort.py:461-467, 245-251, 292-300）と整合。
- AuditorVerdict / AuditorGateFailure / compute_diff_digest は軸非依存で clean move＋alias 可能。既存テストは S.AuditorGateFailure 等を同一クラスオブジェクトとして catch するため（test_p3_s4_loop_sort.py:145,234,254 等）alias が同一 identity なら無改変緑が成立する。
- auditor-violation / auditor-uncertain subtype は既存 critic.digest が既に専用 hint で処理済み（digest.py:577-584）。新 driver がこの2 subtype を流用しても render/load 側は regression なし。load_diff_rejections は rejection_type==DIFF_QUARANTINE_REASON で拾うため新 subtype も回収される（digest.py:303-309）。
- 兄弟 driver 間 import（trigger→sort）を避け共有モジュールに昇格する §3 の判断は正しい。axis_trigger_gating.py:4-7 が s6_sort_sweep→p3_s4_loop_sort の歴史的レイヤ違反を「踏襲しない」と明記しており、trigger→sort import は同型の違反になる。
