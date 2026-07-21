# worklog アーカイブ — Phase 3 (2026-07-19)

`docs/worklog.md` から移動した凍結分。訂正注記のみ追記可。
一覧は `docs/archive/README.md`。

---
## 2026-07-19 (14) — patchharness index.lock 競合の限定・有界 retry (計測なし)

並列 xdist で patchharness の revert と他 worker の読み取り系 Git が index.lock を競合し、
revert 漏れから実 submodule が dirty になる事故の恒久修正。commit はユーザー指示により作成しない。

- `_git` 全呼び出しへ `GIT_OPTIONAL_LOCKS=0` を付与し、読み取り系 Git の任意 lock を抑止。
- checkout と実適用 apply に限り、rc=128 かつ stderr に `index.lock` がある場合だけ 200ms 間隔・
  最大5 retry。stdout/stderr/rc は不変、CompletedProcess の追加属性と最終例外へ retry 痕跡を保持。
- 注入 runner の4回帰テストを追加。対象 12 passed / rc=0。optional-lock 値、index.lock 限定、
  retry 上限の3変異を全 kill。check_codex_agents / check_docs / diff check は rc=0。
- 全走3回は実行 sandbox の Git 管理領域が read-only のため、実 submodule の checkout が
  `index.lock: Read-only file system` で全回 rc=1 (1896 passed、失敗 1/2/1)。各回後に既存 template
  patch を逆適用して pinned-clean へ復元。これは一時競合ではなく環境の恒久拒否であり、限定 retry は
  5回で痕跡付き fail-closed した。書込可能な通常環境での3連続 rc=0 は未実証。

### 次の一手
1. Git 管理領域を書き込める環境で `python3 tools/run_tests.py` を3回連続実行し、rc=0を確認する。
2. commit / push は人間が行う。

## 2026-07-19 (1) — Pegasus env_contract 登録段 wave 完了 (実測 = 較正のみ、性能計測なし)

worklog (13) 次の一手 2 の消化。標準ループ ([[orchestration-loop-pattern]]) ×4 巡。正本 = insights
`2026-07-18_env-contract-pegasus-consultations.md` (相談逐語・親裁定表・実装結果・attempt 経過・
プラン/所見台帳付録)。運用事実の固定先 = pegasus-runbook §7.1、失敗型 = failures F22。

- **相談**: codex gpt-5.6-sol reasoning=max ×3 並列敵対 (attestation 設計 / enforcement 4 点 /
  較正ジョブ)。全所見 real 採用 (縮小 2)。hybrid 方式 (契約 attestation_mode + calibration/v2 同居)
  等を裁定
- **実装**: codex 12 単位 + 実機対応 fix 7 単位 (計 19、gpt-5.6-sol high/medium)。opus レビュー 17
  本 (2 レンズ/単位 + 統合 3)、変異ゲート累計 100+ 変異 KILL。レビューが捕らえた主要 real 欠陥:
  walltime 完全一致の統合不整合 (実機必 reject) / visibility gate 未接続 / host 照合 fail-open 実証 /
  shell ERR trap で拒否 forensic 消失 / build_v2×隔離 worktree seam / report status gate の数値漏出
  実証。xdist 間欠 fail (index.lock→patch 残骸) も恒久対策 (GIT_OPTIONAL_LOCKS=0 + 有界痕跡リトライ)
- **実測**: smoke ×6 で前提凍結 (tolerance 2.0% / numactl none / システム toolchain / kthreadd 指標 /
  request_id 正規化)。certification attempt 1〜10 (総実走 ~15 分、~0.1pt) — 9 回 fail-closed で実機
  前提を逐次確定し (F22 に型記録)、**attempt 10 (867876) が accepted**:
  `registered/calibration-753f535a8d024727.json` (clocks 2100 / records 1M 下限基準 / within-run
  CV 1.17% / bnode011 / final-receipt 済み)
- **登録**: registry へ pegasus entry (contract_sha256 = e576e9cd...、attestation_mode=required、
  single_process=True/allow_resume=False、linux-baremetal 不変)。契約不変式 required⟹single_process
  追加。W5 統合レビュー = commit 可 (12/12 変異正当 KILL、sha/golden 独立再計算一致)
- **最終ゲート**: 全走 1927 passed / 0 failed (rc=0、ベースライン +378)。check_docs /
  check_codex_agents / check_ai_provenance 緑
- **発効なし規律**: official mode 拒否・linux-baremetal 正本据え置き不変。本登録は bootstrap 登録
  であり正式比較可能を意味しない (between-run floor は floor 実測段の入口で)

### 次の一手
1. ユーザー接点: §10.2 追認リスト 5 項 (前 wave 起票、protocol 凍結の前提) + 本 wave 新規追認なし
2. protocol JSON 実凍結 (master_seed=2026-07-18T17:16:12+09:00 / env_tag=pegasus) → 予測封印 →
   floor 実測 (claims/ 事前作成 + IZANAGI_RESERVATION_* export、runbook §7.1)
3. 次 wave 冒頭で: s1 freeze 系テストの submodule 読取 isolation (patch 窓を読む既存フレーク、
   W5 レビュー所見) + テストの patch 適用を tmp worktree へ隔離する恒久対策
4. push / PR はユーザー引き渡し (Pegasus 規約)。branch = worktree-s8b-env-contract-pegasus

## 2026-07-19 (2) — 追認リスト 5 項のユーザー承認を記録 (発効なし・計測なし)

worklog (13)・(14) 次の一手 1 の消化。C2-2 wave 起票の「新規追認リスト」5 項 (PortableBuiltRecord
schema / closure UTF-8・no-NUL / L 全体捏造は保証外と明文化 / M substate + 二相 finalize / run
artifacts の G 同梱・免除の限定列挙) を、2026-07-19 にユーザーが**全項承認** (推奨どおり)。記録の
正本 = insights `2026-07-18_s8b-c22-consultations.md` §10.5。提示材料は実装コード突合の独立抽出
(opus) に基づく平易化資料。

### 次の一手
1. protocol JSON 実凍結 (master_seed=2026-07-18T17:16:12+09:00 / env_tag=pegasus) → 予測封印
   — 前提は全充足 (追認 5 項 = §10.5、env 登録 = worklog (1))
2. floor 実測 (claims/ 事前作成 + IZANAGI_RESERVATION_* export、runbook §7.1)
3. 次 wave 冒頭: s1 freeze 系テストの submodule 読取 isolation + patch 適用の tmp worktree 隔離
4. push はユーザー引き渡し (Pegasus 規約)

## 2026-07-19 (3) — エージェント model/effort 経済監査と是正 (計測なし、branch model-economy-tuning)

ユーザー相談「claude/codex 子の設定が無駄に高度な箇所はないか (Claude トークン消費が速い)」からの
監査 wave。監査 = Claude workflow 11 agents (finder 4 / 敵対検証 6 / 抜け 1)、是正のレビュー =
Claude workflow 9 agents + codex exec 2 レーン (gpt-5.6-sol/high)。フラグ・裁定の要旨の正本 =
output/insights/2026-07-19_agent-model-economy-audit.md、設計決定 = D61。

- ユーザー裁定 2 件: (a) 親セッション既定 (fable[1m]/xhigh) の opus/high への引き下げを承認 —
  ~/.claude/settings.json の AI 編集は auto-mode classifier に拒否されたため手動変更を引き渡し。
  (b) verifier の codex 列を terra/medium へ再ピン (D61。専用固定ルールは削除せず新値で維持)
- 棄却 finding 4 件 (codex 相談 max 定型 / s6 opus ハードコード / profiler opus / opus tool-less 群)
  と codex adapter 一律説の反証は insight に凍結
- セッション異常・正直な記録: 監査 finder 1 体 (opus/high) が縮退出力 `summary:"test"` (他 2 系で
  裏取り済み)。codex scanner レーン初回は OpenAI 安全フィルタが「攻撃」表現を誤検知して失敗 →
  中立表現で完走。親の誤報告 2 件 (truncate grep 由来の「sonnet 系 3 role 一律 sol/high」説、
  verifier 高頻度説) はレビューが検出し訂正 — verifier 頻度の誤りは codex レーンのみが検出しており、
  製品またぎ二重レビューの実益例
- 素材: 正しさ番人の設定変更は「機械ルールの削除でなく新値での再ピン」で防壁構造を保存する (D61)。
  経済最適化圧力が正しさ側の防壁を素通りで壊さない形

### 次の一手
1. ユーザー: ~/.claude/settings.json の手動変更 (model: "opus" / effortLevel: "high")
2. ユーザー: branch model-economy-tuning の push / PR 判断 (Pegasus 規約で AI は push しない)
3. 新 workflow script は起動前に `python3 tools/check_workflow_models.py` で自己検査 (memory 更新済み)

## 2026-07-19 (4) — test runner の並列度を環境自動追従に (ユーザー指示、branch test-runner-autoscale)

`tools/run_tests.py` の固定 `-n 8` を `min(使えるコア数, 32)` の自動追従へ。「使えるコア数」は
`os.process_cpu_count()` / `sched_getaffinity` で cgroup・CPU affinity を尊重するため、PBS ジョブ内
では割り当て分、素のマシンではコア数どおり、共有 login node でも上限 32 で頭打ち (全コアを掴まない
行儀を自動で満たす)。上限根拠は再実測 (約1946 テストで -n 8/16/32/96 = 18.7/14.6/10.5/13.0s。
worklog 2026-07-17 の推奨 8 はテスト 996 件時点の値で、倍増した現行では頭打ちが 32 付近へ移動。96 は
worker 起動コストで 32 より遅い)。明示上書き = `-n <数>` (最優先) / `IZANAGI_TEST_NPROC=max|<数>`。

- 動機: ユーザーが「毎日 -n を手調整したくない、環境のコア数に追従させたい」と指示。文字どおりの
  全 96 コアは安定 (2 連続 clean) だが 32 より遅く共有機で無作法なため、追従 + 上限 32 を既定にし、
  `IZANAGI_TEST_NPROC=max` で文字どおり全コアも選べる形にした
- positive control: `orchestrator/tests/test_run_tests_nproc.py` (affinity 上界・cap・max 解除・数値
  上書き・不正値フォールバックを入力別 pin)。ランナー経由の全スイート = 自動 -n 32 で 12.6s / 1957 passed
- 索引の腐敗回避: tests/README.md の「並列度 8 / -n auto を使わない」記述を自動追従版へ更新済み

### 次の一手
1. ユーザー: branch test-runner-autoscale の push 判断 (Pegasus 規約で AI は push しない)

## 2026-07-19 (5) — テストスイート衛生 wave (branch test-hygiene、計測なし)

handoff 2026-07-19-test-hygiene.md を標準ループ (codex 敵対相談 3 本 → 並列実行 5 単位 → 敵対
レビュー 3 本 → 親検算) で完遂。相談 13 + レビュー 13 の全 26 所見 real (refuted 0)。逐語と親裁定は
output/insights/2026-07-19_test-hygiene-consultations.md、調査正本と実行証跡は
output/insights/2026-07-19_test-suite-hygiene-survey.md。プラン v1 の前提 2 つが相談で反転した
(「逐語上位集合」不成立 → 固定 baseline 追加後に削除 / 弱テスト 10 件中 4 件は raise-only 契約
どおりで強化不要)。親検算は gen_S 計算ノードで mutant matrix 10 件 (8 判別 + 2 非判別を明示、
全件復元後 green) + node-ID 集合 gate (1976→1978、削除 1・追加 3 のみ) + 全スイート緑。

- 素材: 敵対相談がプラン前提を反転させた実例 2 件 (上記)。盲検でなく事前登録 mutant + 第一失敗行
  記録で「新アサートのみ赤」を機械判定した初の wave
- flake 所見: test_s8b_protocol_builder の repo-tree snapshot テストが xdist 並列下で 4 走中 1 flake
  (git status --porcelain 前後比較が untracked 出入りに脆弱)。本 wave の diff から独立
- 逸脱: 着手条件「3 プラン以外 handoff 空」字義未充足のまま続行 (observability handoff 残存、
  稼働セッションなし確認、包括的ループ指示を GO と解釈 — 個別明示 GO ではない)
- セッション異常: codex exec の stdin 未クローズで敵対レビュー 3 本が 100 分停止 (F23 登載)
- 環境知見は survey insight 実行証跡節に固定 (計算ノード python、pygments、PYTHONPATH)

### 次の一手

1. ユーザー: branch test-hygiene の push 判断 (Pegasus 規約で AI は push しない)
2. protocol_builder の repo-tree snapshot テストの xdist 耐性 (tracked のみ比較 or 直列化 marker) —
   処置裁定は backlog-triage (B) の棚卸し表へ
3. (変わらず) B=backlog-triage は A 完了により着手条件の一部が満ち、ユーザー GO 待ち

## 2026-07-19 (6) — B=未消化タスク棚卸し: 裁定パッケージ完成 (branch backlog-triage、計測なし、発効なし)

標準ループで B1 (裁定パッケージ作成) を完遂: codex 敵対相談 3 本 (22 所見、CC-1 の前提のみ refuted、
残り 21 real) → 掃引 6 単位 (worklog 3 ファイル + insights 59 ファイル + 台帳裏取り、原子 462+追補 5 項目) →
表起草 → 敵対レビュー 3 本 (20 所見、全 real) → codex fix + 親検算。成果物 =
output/insights/2026-07-19_backlog-triage.md (**裁定行 59、全行未裁定・発効なし**)。相談・裁定の逐語 =
output/insights/2026-07-19_backlog-triage-consultations.md。

- 着手判断: worklog (5) の「GO 待ち」の後にユーザーが発した新規の包括的ループ指示を B への GO と
  解釈 (個別明示 GO ではない)。許可範囲は裁定パッケージ作成まで (処置確定・phase 反映・C 着手を含まない)。
  着手条件「A/B/C 以外 handoff 空」は observability handoff 残存で字義未充足のまま続行した逸脱
  (稼働セッションなし・編集面の直列化可を確認)
- 素材: 発掘の主要例 — hole 内コメント機械拒否 (injection 経路、insight 高推奨→3 回申し送り後に脱落、
  B-001)・ermia 台帳前提の消滅 (live path 再導出で要再定義、B-014)・§5-(viii) 限界受入の持ち越し脱落
  (B-005)。台帳 calibration 行は K 感度/thread 再較正の独立 2 タスクに分離、K 感度は発火条件が既に真
- レビューが親掃引の誤りも検出: 3 連続 rc=0 (B-054) は完了済みの巻き戻し誤判定 → 完了に訂正。
  優先閲覧段落は台帳規約 (優先度はユーザーのもの) 違反 → 削除
- 付随変更: C handoff の着手条件を「B handoff 消滅 + 裁定反映済み」へ精密化、output/README.md に
  凍結スナップショット責務 1 文、failures F24 (完了検知のログ本文 grep 誤検知、ユーザー指摘) 追記
- セッション内対応: ユーザー依頼で claude.ai コネクタを settings.local.json で無効化 (コンテキスト固定費 32k 削減)

### 次の一手

1. ユーザー: output/insights/2026-07-19_backlog-triage.md の 59 行の裁定 (裁定が B2 と C の前提)
2. 裁定後 B2: 生存項目を phase3 見送り台帳・worklog へ反映し、B handoff を削除 (→ C 着手条件成立)
3. ユーザー: branch backlog-triage の push 判断 (Pegasus 規約で AI は push しない)
4. (変わらず) test-hygiene の push 判断は worklog (5) 参照。xdist flake の処置裁定は棚卸し表 B-051 へ登載済み

## 2026-07-19 (7) — B2=未消化タスク棚卸しのユーザー裁定反映完了 (branch backlog-triage、計測なし)

ユーザー裁定により棚卸し 59 行が全件確定 (**本エントリが裁定の正本**)。証拠・述語の凍結 =
`output/insights/2026-07-19_backlog-triage.md` (本文不変)。

- **49 一括承認**: 条件付き保留は発火条件付きで見送り台帳へ、完了確認 B-038/B-054 は terminal 記録
- **昇格 8**: B-001/003/004/005/035/051/052/053。B-005 (floor 前受諾 gate) と B-035 (D39 erratum) は
  本反映で完了、残 6 件は承認済み・未着手
- **代替 2**: B-015 = K=4 を設計定数として感度主張なしで終了 (論文の機序図・K=4 依存主張の凍結直前に
  再評価)。B-050 = fable 既定継続は意図的、opus は監査・統合時の個別指定のみ
- B handoff は B2 完遂として削除。反映は codex 全数レビューで検証 (59/59 分類正、所見 5 は表現のみ・是正済み)

### 次の一手

1. **防壁 wave**: B-001 + B-003 + B-004 の実装 (承認済み・未着手)
2. **テスト衛生 wave**: B-051〜053 の xdist 直列 group 化 (承認済み・未着手。worktree 隔離は再発時)
3. **C (backlog-guard-mechanism)**: 第 1 条件成立。残る条件 = 機構形式のユーザー裁定 (推奨 = ID + 機械検査)
4. ユーザー: branch backlog-triage の push 判断 (AI は push しない)

## 2026-07-19 (8) — 承認済み 2 wave 実装: 防壁 (B-001/003) + テスト衛生 (B-051〜053)、B-004 は裁定パッケージ化 (branch approved-waves、計測なし)

worklog (7) 次の一手 1・2。標準ループ (プラン → codex 敵対相談 4 本 [gpt-5.6-sol max、32 所見
real 32/refuted 0] → 実行 = codex 並列 3 worktree → レビュー = codex 並列 [所見 U1:3 / U2:0 /
U4:4、全 real] → 親変異 matrix + 受入実測 → 再投げ 4 回)。commit 216078e (B-003)、e427194
(B-001、D62)、7489b99 (B-051〜053、D63)。相談・レビュー・実行報告の逐語と実測の正本 =
`output/insights/2026-07-19_approved-waves-consultations.md`。

- **U3 = B-004 は NO-GO → 裁定パッケージ** (同 insights §U3): (a) 定数 pin は承認 extime 値が不在
  (experiment_numbers 未裁定) で「値の発明」、(b) freeze 一致検査も floor extime_s ≡ oracle extime の
  authority 未裁定を要する。**X3-52 erratum**: 「reps 束縛完了」は floor 側のみの証拠で oracle
  manifest は reps=999 も受理 (実測) — oracle 側 reps は unresolved
- B-057 発火 → 変異 11 件を実装前に事前登録。初版で 2 件生存 (U4 収集監査の自己参照恒真 [F15 型] +
  SUT 結線 guard 不在) → 是正後 全 KILL。B-056 発火 → coverage baseline/final 観測 (gate 化なし)
- 対照実験で B-051 の競合相手を同定: `--dist load` では snapshot が別 worker の submodule patch 窓
  (CCBench submodule) を観測して赤。loadgroup 直列化で対象反復 17/17×2 + 全走連続緑
- 異常記録: (i) codex 相談 C1 初回投が OpenAI 安全フィルタで途中終了 (98k tokens 浪費) —
  敵対プロンプトのセキュリティ語彙は防御的表現へ言い換える (再投で完走)。(ii) 統合直後の全走 1 回に
  1 fail、**ログを tail のみで破棄し node 不明** (親の運用ミス)。直後の同条件 7 連続 + 反復 17/17 は
  全緑。再発時は failing node ID の保存を第一とする。(iii) codex sandbox は submodule gitdir が
  read-only で patch 復元不能 — exec worktree の submodule 復元は親が実施する運用
- 工数: codex 相談 4 + 実行 3 + fix 4 + レビュー 3 (全 gpt-5.6-sol)、親 = fable (裁定・変異・統合)

### 次の一手

1. **ユーザー裁定 (B-004 パッケージ)**: experiment_numbers の extime/reps 値と floor/oracle の
   同一性 authority (推奨 = authority object 導出の一致検査、insights §U3)。X3-52 の oracle 側 reps
   unresolved の再裁定を同梱
2. **ユーザー裁定 (U2 残余 3 述語)**: P_timeout_reason / P_build_reason / P_reason_type_crash
   (insights §U3 隣接残余。timeout/build-failed の reason 非検査と verify-inconclusive の unhashable
   TypeError)
3. C (backlog-guard-mechanism): 変わらず (前エントリ参照 — 機構形式のユーザー裁定待ち)
4. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main)

