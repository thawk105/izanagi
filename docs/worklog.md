# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

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

## 2026-07-20 (1) — B-004 wave 実装完了: 公式実験数値 pin (extime=5/reps=5) + report 隣接 3 穴 (branch approved-waves、計測なし)

worklog (8) 次の一手 1・2。**ユーザー裁定 (2026-07-19、会話はコンテキストクリア済みのためここが
記録の正本): 公式実験は extime=5 秒 / reps=5。floor と oracle は結合 (単一 authority) で実装は
一致検査。試行錯誤 (探索) は 3 秒 3 回目安で検証器の対象外。oracle 側 reps (X3-52 erratum) と
隣接 3 穴 (P_timeout_reason / P_build_reason / P_reason_type_crash) も同時承認。**

標準ループ (プラン v1 [handoff 控え] → codex 敵対相談 2 本並列 [gpt-5.6-sol max、14 所見
real 14/refuted 0、プラン v1 に NO-GO] → プラン v2 → 実行 = codex 並列 2 worktree → レビュー =
codex 並列 2 本 [所見 E1:3 / E2:1、全 real] → fix 再投 2 → 親変異 matrix N1〜N14 全 KILL +
受入全走 7 連続緑)。設計判断 = D64。相談・実行・レビュー・fix の逐語と変異実測の正本 =
`output/insights/2026-07-20_b004-experiment-numbers-consultations.md`。

- **裁定パッケージ 5 件** (承認 scope 超えのため実装せず、同 insights に凍結): report→judge→
  verdict の manifest 検証迂回 + 探索 namespace 隔離 (high) / reps=5 の観測証拠件数意味論 /
  gate-check preflight 偽緑 / 段階順序 truth-table / payload 非 Mapping クラッシュ
- B-057 発火 → 変異 12 本を実装前事前登録 + レビュー起因 2 本追加。レビュー前は N13/N14 相当が
  実測 survivor (floor reps re-literal / s8b_approved 再輸出恒真) → fix 後 14/14 KILL。
  B-056 発火 → coverage baseline/final 観測 (同水準、新 leaf 2 本 100%、gate 化なし)
- **D63 列挙漏れを補完** (D64 に erratum 併記): 結線監査 meta-テスト自身が real-repo 競合面なのに
  直列 group 外で、統合後の全走で間欠赤 (2/3、failing node はログ保存 — (8) 異常 (ii) の教訓を
  適用)。二重台帳の両側更新で閉鎖、片側のみの変更は監査が実測検出 (恒真化防止が設計どおり機能)
- golden SHA は相談予測・実装再計算・レビュー独立再構成の三重一致。codex 相談で安全フィルタ
  発火ゼロ (防御的表現の運用知見を適用)
- 工数: codex 相談 2 (max) + 実行 2 (high) + レビュー 2 (high) + fix 2 (medium)、親 = fable
  (裁定・統合・変異ゲート・flake 真因同定)

### 次の一手

1. **ユーザー裁定 (裁定パッケージ 5 件)**: 上記 insights の §裁定パッケージ。推奨順 = P-A1 の (b)
   探索 namespace 隔離 (小) → P-B5/P-B6 (report 証拠 truth-table と payload guard、同一分岐群の
   隣接 wave) → P-A2 (reps 意味論) → P-A5 (gate-check)
2. C (backlog-guard-mechanism): 変わらず (前エントリ参照 — 機構形式のユーザー裁定待ち)
3. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main、
   本 wave 分を含め未 push)

## 2026-07-20 (2) — 裁定パッケージのユーザー裁定記録 (発効なし・計測なし・実装は次セッション)

worklog (1) 次の一手 1。ユーザー裁定 (本セッション、ここが記録の正本):

- **P-A2 (reps の意味論): 裁定確定 — 「reps=5 は成功した測定値 5 個」を意図する。**
  足りなければ不合格。report が測定値の個数を数える検査を実装してよい
- **P-A5 / P-B5 / P-B6 (gate-check preflight / 段階順序 truth-table / payload 型 guard):
  推奨案どおりの実装を一任で承認** (「よしなに」)。実装順の推奨 = P-B5/P-B6 (report 同一
  分岐群の隣接工事で 1 wave に同梱) → P-A2 → P-A5
- **P-A1 (公式判定の名乗り): 裁定継続。** ユーザー質問「探索も 5 秒 5 回に揃えれば齟齬の
  心配はなくなるか」への回答を記録: **なくならない** — 穴は数値差でなく「後段が検査通過を
  確認しない」こと。揃えると未検査入力は依然通る上に探索と公式の見た目の区別が消えて
  混入リスクはむしろ上がり、探索も 25 秒/点に遅くなる。推奨は引き続き (b) 探索成果物の
  別 namespace/書式化 (→ 段階導入で (a) 後段の検査必須化)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-B5 + P-B6 (+ P-A2 の個数検査) を 1 wave、
   P-A5 を続けて。正本 = insights 2026-07-20 の §裁定パッケージ + 本エントリの裁定
2. P-A1: ユーザー裁定継続 (推奨 (b)。上記 Q&A 参照)
3. C (backlog-guard-mechanism): 変わらず (前エントリ参照)
4. ユーザー: push 判断 (AI は push しない。main へのローカル merge は本セッションで指示済み)

## 2026-07-20 (3) — P-A1 のユーザー裁定確定 (発効なし・計測なし・実装は次セッション)

worklog (2) 次の一手 2。ユーザー裁定 (本セッション): **P-A1 は推奨案で確定** — (b) 探索成果物を
別 namespace/書式に隔離し official 側が型で拒否する (小) を先行し、(a) report→judge→verdict の
検査必須化 + 旧形式受理の廃止は段階導入。これで裁定パッケージ 5 件は全件決着 (P-A2 確定 /
P-A1・A5・B5・B6 推奨案承認)。

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-A1(b) → P-B5 + P-B6 (+ P-A2 の個数検査)
   → P-A5 → (段階導入の設計判断として P-A1(a))。正本 = insights 2026-07-20 の §裁定パッケージ +
   worklog (2)(3) の裁定
2. C (backlog-guard-mechanism): 変わらず (前エントリ参照)
3. ユーザー: push 判断 (AI は push しない)

## 2026-07-20 (4) — 裁定パッケージ 5 件の実装 wave 完了 + ハイブリッド標準ループ初回試行 (branch approved-waves、計測なし)

worklog (3) 次の一手 1。**ループ形式の変更 (ユーザー発案の試行):** 親 (fable) は緻密プランを書かず
brief (scope/裁定/不変条件) のみ書き、緻密プラン起草を codex へ委譲。親の担当 = 裁定・scope 監査・
統合・変異ゲート実測・記録。ユーザー未返信のまま仮定で進行 (「品質を変えずに節約できるならそうしたい」
の意向に沿う。差し戻し可能な設計で実施)。

標準ループ (brief → codex プラン起草 [max] → 敵対相談 2 並列 [max、25 所見 real 25/refuted 0、
プラン v1 NO-GO] → 親裁定でプラン v2 [V1〜V16] → 実行 = codex 3 単位 [E1 ∥ E2 → E3、high、
worktree 分離、cherry-pick 競合ゼロ] → 親検算 → 変異 matrix 20/20 → 全走 [plain-runner ガード発火
1 件 → fixup] → 敵対レビュー 2 並列 [9 所見、real コード 4 = symlink/TOCTOU・数値有限性・judge
fixture 5 値化・未知 schema 負例] → fix 1 単位 → 変異 22/22 KILLED [レビュー起因 RM1/RM2 は fix 前
生存を実測 → fix 後 KILL] → 全走 7 連続緑)。設計判断 = D65。逐語・変異台帳・新裁定パッケージの
正本 = `output/insights/2026-07-20_wave2-adjudicated-package-loop.md` +
`2026-07-20_wave2-mutation-ledger.json`。

- commits: 4857534 (E1: P-A1(b) 型/namespace 隔離) → bfef26f (E2: truth-table leaf + P-A5) →
  038e749 (E3: report 配線 B5/B6/A2) → 5c09ef3 (自走 harness fixup) → a89e2b8 (レビュー fix 4 件) +
  本 docs commit。基点 58934ae
- 検収: 全走 7 連続緑 (2111 passed / 19 skipped)、変異 22/22 KILLED (B-057、exact diff 台帳凍結)、
  coverage 観測 (B-056): report 76→83% / judge 77→84% / 他同水準 (gate 化なし)
- **新裁定パッケージ 3 件 (実装せず、insights §裁定パッケージ)**: P-C1 rep 成功の rc=0 意味論 /
  P-C2 prepare retry の report 偽陽性 (既存挙動、親裏取り済み) / P-C3 意味論 leaf が generator pin 外
- 運用知見: (i) fix unit が担当外 docs を編集 → 親差し戻し (exec プロンプトに docs 禁止を恒久明記)。
  (ii) 親が commit で hooksPath 迂回フラグを誤用 → 即是正 (git hooks 未配線で実害なし。予防的迂回も
  禁止)。(iii) codex 安全フィルタ発火ゼロ (防御的表現の運用知見を継続適用)
- ハイブリッド観測 (サンプル 1): codex 9 本 (max 3 / high 5 / medium 1)、品質面の劣化兆候なし
  (相談 25 所見はプラン v1 の実穴、レビュー 4 real は全て fix で閉鎖 + 変異裏取り)。継続判断は
  ユーザーへ

### 次の一手

1. ユーザー: ハイブリッド形式 (プラン起草の codex 委譲) の継続可否
2. **ユーザー裁定 (新裁定パッケージ P-C1〜C3)**: insights 2026-07-20 wave2 §裁定パッケージ。
   推奨順 = P-C2 (retry 偽陽性、report 契約の穴) → P-C1 (rep 成功意味論) → P-C3 (P-A1(a) と同時)
3. P-A1(a) 段階導入 (Stage 1〜3、D65): 各段階の個別ユーザー承認待ち
4. C (backlog-guard-mechanism): 変わらず (前エントリ参照)
5. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main、未 push)

## 2026-07-20 (5) — task-run 台帳 pilot 実装 wave (D66) + /dev-wave 改善 (branch approved-waves、計測なし)

handoff 2026-07-19 (AI 開発作業の統計記録) の実装。worklog (4) 次の一手は全件ユーザー裁定待ちのため、
唯一の非ブロック作業を選定 (次の一手 1 のハイブリッド継続は /dev-wave 起動自体を継続意思と解釈 —
明示裁定があれば上書き)。標準ループ (brief → codex プラン起草 [max] → 敵対相談 2 並列 [max、48
must-fix、プラン v1 NO-GO] → 親裁定 プラン v2 = V1〜V26 + 変異事前登録 M01〜M32 [B-057] → 実装 =
codex 3 単位 E1→E2∥E3 [high、worktree 分離、競合ゼロ] → 敵対レビュー 2 並列 [high、27 所見 全 real、
refuted 0] → fix 1 単位 [F-1〜F-21] → 親変異 matrix 実測 31/32 KILLED + M30 等価変異は両層同時
M30c で KILLED → 受入全走 7 連続緑 2248 passed/19 skipped)。設計判断 = D66。逐語・変異台帳の正本 =
`output/insights/2026-07-20_task-run-ledger-consultations.md` + 同 `-mutation-ledger.json`。

- commits: 349cf4e (実装一式) → bd5e67b (/dev-wave 改善) + 本 docs commit。基点 9cbe36a。
  異常記録: 初回積載 (139edd2/224817c/c104962) は AI-Agent trailer と Co-Authored-By の間の空行で
  trailer block が分断され provenance 監査 3 違反 → 未 push のためメッセージのみ修正して積み直し
  (tree 不変)。台帳の commit event は旧 SHA 2 件が append-only で残存し、新 SHA を追記で訂正
- **pilot 発足 + dogfooding**: init-pilot + 実 FS selfcheck 合格 → 本 wave 自身を run 1 として記録
  (`20260720-dev-wave-taskrun-ledger-fb468b60`、test_run 17 件 [red→green 1 周を実записи] + check 2 件 +
  commit 2 件、completed)。dogfooding が実運用縫い目 2 件を fail-closed 発火で捕捉 → 親 fixup:
  (i) root 直下 README.md が unknown 扱いで start 拒否 (validator 許容列挙と文書 layout の不一致)、
  (ii) 記録付き外側 run の env が既存 golden テストの subprocess mock を汚染 (conftest に autouse
  隔離 fixture)。両方とも回帰テスト同梱、fix 後に変異 matrix + 全走を再走済み
- **/dev-wave 改善 (ユーザー指示 2026-07-20)**: wave 実測の観測 4 点 (-o 作法化 / wave 専用 tmp /
  read-only sandbox の pytest 不能 / 依存単位・意図的赤・等価変異の扱い) + pilot 自己記録の導線を
  スキルへ反映 (bd5e67b)。main へのローカル取り込みはユーザー指示に従い本セッションで実施 (push はしない)
- 工数: codex 7 本 (max 3 / high 4)、親 = fable (裁定 2 回・統合・変異ゲート実測・dogfooding・記録)

### 次の一手

1. **task-run pilot 運用中 (〜10 run または 08-03)**: クラス 2/3 の実装・統合セッションは
   `python3 tools/task_run.py start` で記録を開始し、受入走に `IZANAGI_TASK_RUN_ID` を付け、
   `finish` で閉じる。手順の詳細正本 = `output/task-runs/README.md` (CLAUDE.md へは配線しない —
   pilot 実証後にユーザー提案)
2. **ユーザー裁定 (新裁定パッケージ P-C1〜C3)**: 変わらず (worklog (4) 参照)
3. P-A1(a) 段階導入 (Stage 1〜3、D65): 各段階の個別ユーザー承認待ち (変わらず)
4. C (backlog-guard-mechanism): 変わらず (機構形式のユーザー裁定待ち)
5. ユーザー: branch approved-waves の push 判断 (AI は push しない。基点 aba3774 = main、未 push)

## 2026-07-20 (6) — /dev-wave 段 8「スキル自己改善」の常設化 (ユーザー指示、計測なし)

ユーザー指示 (本セッション、ここが記録の正本): **wave 開始時に改善案メモ → 終了時にスキルへ反映を
/dev-wave 自体に組み込む。小さい改善 (段構成・権限・防壁・裁定境界を変えないもの) は AI が自律反映、
大きい変更はユーザー裁定。** 段 8 として明文化し commit 8664323、main へ 9360e25 としてローカル
取り込み済み (push はしない)。

### 次の一手

変わらず (worklog (5) 参照 — pilot 運用中 / P-C1〜C3・P-A1(a)・C の裁定待ち / push 判断)

## 2026-07-20 (7) — /rulings スキル新設 (ユーザー指示、計測なし)

ユーザー指示: 裁定待ち確認の定型プロンプトをスキル化。**全件 1 行索引 + 先頭 N 件 (既定 5) の平易な
詳説** (件数固定でなく索引で全体量を常に可視化する構成は AI 提案をユーザーが了承)。commit 79c1e7c、
main へ be3a455 として取り込み済み (push はしない)。

### 次の一手

変わらず (worklog (5) 参照)

## 2026-07-20 (8) — P-C1/C2/C3・C の ユーザー裁定確定 + push 現況 (発効なし・計測なし・実装は次セッション)

ユーザー裁定 (本セッション /rulings 経由、ここが記録の正本):

- **P-C2: 推奨案で確定** — 正当な prepare retry の attempt lifecycle を閉表化 (trial-result なし +
  retry 1 件 + 次 attempt 番号一致の window を正当 retried として扱う) + 正例テスト
- **P-C1: (b) で確定** — rep ごとの rc を WAL に記録し、report が 5 件とも rc=0 を検査
- **P-C3: 推奨どおり P-A1(a) 段階導入と同時に実施** (generator pin の transitive 拡張)
- **C (backlog-guard-mechanism): 推奨案 (ID + 機械検査) で確定** — handoff の着手条件が全て成立
- push 現況 (親が実測): **main は push 済み** (origin/main = be3a455、ローカルと一致)。
  **approved-waves は未 push** (origin に ref なし。本日 3 wave 分 10 commit はローカルのみ)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) — report 契約の隣接工事として
   1 wave 同梱を推奨。正本 = insights 2026-07-20 wave2 §裁定パッケージ + 本エントリ
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + 本エントリ
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: approved-waves の push (未 push。意図的保留か失敗かの確認から)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (9) — 全ブランチ棚卸し + approved-waves を main へ統合 (計測なし)

ユーザー指示「worktree/branch を全確認し、main に入れられるものを全て入れる」。

- 棚卸し: 未マージは approved-waves のみ (8 ahead / 3 behind)。backlog-triage /
  model-economy-tuning / test-hygiene / test-runner-autoscale / worktree-s8b-env-contract-pegasus /
  origin/worktree-s8b-ruling-prep は全て ahead=0 (取り込み済み。ブランチ削除はユーザー判断に委ねる)
- behind 3 コミットは commands 変更の main への cherry-pick 複製 (内容同一) と確認 → main を
  approved-waves へマージ (競合ゼロ、merge-tree 予行 + 実マージで裏取り) → main を fast-forward
- 検収: 全テスト 2248 passed / 19 skipped、check_docs 違反なし
- push はしない (Pegasus 規約)。統合後の main はローカルのみ先行 (origin/main = be3a455)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) — report 契約の隣接工事として
   1 wave 同梱を推奨。正本 = insights 2026-07-20 wave2 §裁定パッケージ + worklog (8)
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: main の push (統合後ローカルのみ先行。approved-waves ブランチと取り込み済み 5 ブランチの
   削除可否も合わせて判断)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (10) — ブランチ・worktree 掃除の実施 + F26 台帳化 + /cleanup-branches スキル新設 (ユーザー指示、計測なし)

worklog (9) 次の一手 4 のうちローカル分をユーザーが裁定 (削除)。同一セッションで掃除 →
main push (ユーザー) → 本 commit の順。

- 掃除: ローカルブランチ 6 本 (approved-waves + 取り込み済み 5 本) と worktree
  s8b-c22-launch-cert を削除、ローカルは main 1 本に統一。main はユーザーが push 済み (a71057b)
- 掃除中に submodule 起因の罠 2 件を実測 (remove 無条件拒否・deinit の設定共有で main checkout の
  external/ccbench が一時未初期化 → update --init で復元済み) → **failures F26 に台帳化**
- **`/cleanup-branches` スキル新設** (.claude/commands/cleanup-branches.md): 棚卸し → 安全条件
  (ahead=0 のみ、-D 禁止) → F26 対応の worktree 削除手順 (deinit 禁止) → 事後検査 →
  push 系のユーザー引き渡し、の最小チェックリスト。ユーザー裁定 = 「failures 追記が本筋、
  スキルは最小」の推奨を承認

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) (worklog (8) 参照)
2. **承認済み実装 wave**: C = backlog-guard (worklog (8) 参照)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: 本 commit 後の main push + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep。push 操作のため AI は行わない)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (11) — /cleanup-branches に自己改善段を追加 (ユーザー指示、計測なし)

/dev-wave 段 8 と同型の「スキル自己改善」を §6 として追加 (発火条件つき — 記載と実挙動の
食い違い・新しい罠・手順不足を実測した場合のみ。failures 台帳との整合と 1 コミット化を規定)。
併せて初回実行 (worklog (10)) で得た未記載の知見を §3 に反映: ExitWorktree remove は ff 済み
コミットでも「未取り込み」と誤警告することがある — discard で押し切らず keep → 手動手順で畳む。

- 運用知見: EnterWorktree の fresh 基点は origin/main のため、ローカル main が push 前だと
  worktree に直近コミットが無い状態で始まる — 基点確認 (`git log --oneline -1`) を worktree
  作成直後に行う (本セッションで実測、reset --hard で復旧)

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: P-C2 + P-C1(b) (worklog (8) 参照)
2. **承認済み実装 wave**: C = backlog-guard (worklog (8) 参照)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: main push (99bce0c + 本 commit の 2 件先行) + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (12) — P-C2 + P-C1(b) 実装 wave (D67、branch worktree-dev-wave-pc2-pc1b、計測なし)

worklog (8) 次の一手 1 の承認済み実装 wave。ハイブリッド標準ループ (/dev-wave) で実施。

- **P-C2**: 正当な transient prepare retry が report で protocol_violation になる偽陽性を、
  per-row の attempt lifecycle DFA (受理形は `S1→pipeline→T1` と `S1→R→S2→pipeline→T2` の二形のみ、
  retry と trial-result の双方を窓へ全単射に束縛) で解消。**当初の局所修正案は敵対相談で却下** —
  それでは正規 driver に作れない列 (偽造 attempt 2) を受理し、攻撃者が選んだ性能値が正式標本に
  なる危険側の偽陰性が残るため。lifecycle 違反時も definitive-red を reason に残す (規律3)
- **P-C1(b)**: rep ごとの returncode を `bench_done.rep_returncodes` に記録し、report が
  非 bool int・件数 = APPROVED_REPS・全ゼロを検査。tps と rc の双方が成立して初めて bench_values を
  公開する。採用ラウンドと rc の対応は **object 同一性**で引く (最小 CV ラウンドが返るため index や
  dataclass equality では別ラウンドと誤対応し恒真化する)。一致が一意でなければ WAL を書かず fail-closed
- 検収: **2278 passed / 26 skipped**、check_docs 違反なし。**変異 18/18 KILLED・全て帰属成立**
- **erratum**: 変異の初回集計で 2 件を誤って「実効」と数えた (受理集合を変えない変異が理由文字列の
  変化だけで赤くなる過剰決定 fixture)。レビュー 2 本の独立指摘と親の追試で判明し、ゲートの構造分離と
  単一理由 fixture への差し替えで是正。経緯は insights の変異台帳 erratum に凍結
- 逐語 = `output/insights/2026-07-20_pc2-pc1b-loop.md`、変異台帳 = 同 `-mutation-ledger.md`

### 次の一手

1. **ユーザー裁定待ち (本 wave の裁定パッケージ 3 件)**: (a) campaign-terminal の物理位置が未検査
   (terminal を trial より前に置いた WAL が completed になる) / (b) session record の issuer
   (`variant`) と `env_tag` が未照合 (既存 report fixture 自体が manifest と異なる env を使っており、
   直すと fixture 群への波及が広い) / (c) WAL 改竄耐性 (duplicate key 最後勝ち・hash chain 不在)。
   いずれも敵対相談で real と判定したが scope 外。詳細 = D67 (7)
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)
3. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
4. ユーザー: main push (99bce0c 以降 + 本 wave の 2 件先行) + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep)
5. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)

## 2026-07-20 (13) — ruling-A のユーザー裁定確定 (発効なし・計測なし・実装は次セッション)

worklog (12) 次の一手 1(a)。/rulings 経由のユーザー裁定 (ここが記録の正本)。

- **ruling-A: 推奨案で確定 — ruling-C と同梱で 1 wave。** campaign-terminal の物理位置を検査する
  (完了宣言は WAL の最後、宣言より後の record は違反、宣言は最後の trial-result より後)。
  ruling-C (WAL 改竄耐性 = duplicate key 最後勝ち・hash chain 不在) を同じ wave に束ねる —
  どちらも「WAL を読む入口の堅牢化」で編集面とテスト土台が近いため。ruling-B (session record の
  issuer / env_tag 照合) は既存 fixture 群への波及が広いので**混ぜない** (未裁定のまま)
- **裁定前に親が実測し、D67 (7) の懸念を解消した**: D67 (7) は「terminal-last を課すと driver が
  terminal 後に書く record との整合検証が要る」として scope 外にしていたが、正規 driver は**両経路とも
  campaign-terminal が WAL への最後の書き込み**である (`s8b_oracle_driver.py:1073` = 予算切れ中断、
  `:1293` = 正常完了。いずれも直後が `return` で追記なし)。budget 台帳の settle は宣言より前かつ
  別ファイルのため WAL 順序に影響しない。よって「terminal は WAL の最後」規則は正規 producer の実挙動と
  一致し、**今回直した型の偽陽性を新たに作る恐れは否定された**
- 着手が安い時期である根拠: official campaign の WAL はまだ 1 件も生成されていないため、既存記録の
  適合棚卸しが不要

### 次の一手

1. **承認済み実装 wave (次セッション、クラス 3)**: ruling-A + ruling-C 同梱。正本 = D67 (7) +
   本エントリ。terminal 物理位置の検査は上記実測 (driver:1073/1293 が最後の書き込み) を前提にする
2. **承認済み実装 wave**: C = backlog-guard (ID + 機械検査)。正本 = handoff
   2026-07-19-backlog-guard-mechanism.md + worklog (8)
3. **ユーザー裁定待ち**: ruling-B (session record の issuer/env_tag 照合。既存 report fixture 自体が
   manifest と異なる env を使っており波及が広い) — 単独 wave を推奨
4. P-A1(a) Stage 1 の承認待ち (承認時に P-C3 を同梱)
5. ユーザー: main push (origin より 3 件先行) + リモートブランチ削除の可否
   (origin/approved-waves・origin/worktree-s8b-ruling-prep) + 本 wave の worktree 3 つとローカル
   ブランチ 3 本 (worktree-dev-wave-pc2-pc1b・wave-pc2-unit1・wave-pc1-unit2) の掃除可否
6. **B-008 (guard_agent 再検証) の発火条件が成立**: 見送り台帳の述語「新しい background job session
   の開始時」に本セッションが該当する (2026-07-20 の /rulings で確認)。拾うか見送り継続かは未裁定
7. task-run pilot 運用中 (worklog (5) 次の一手 1 参照)
