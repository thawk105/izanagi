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
## 2026-07-14 (1) — 全体方針の根本評価 (ユーザー依頼「ドツボにハマってる気がする」)

ユーザー依頼で roadmap / phase doc / リポジトリを横断検査 (計測ゼロ・計測窓不使用)。9 レンズ
(実態 6 + 敵対突合 2 + 信頼中核の正本精読)、全レンズ独立コンテキスト read-only。診断全文・
提言・裁定欄の一次資料 = `output/insights/2026-07-14_strategy-review-overall-direction.md`。

- 最重要 3 件: (1) Phase 3 で LLM 合成が stock を floor 超で上回った実証 = 0 件 (floor 超の
  実測はすべて機械 sweep の成果)、(2) LLM ループは軸が生きる高競合動作点で未実走 (敗北で
  なく未戦 — 工程欠落)、(3) 停滞の構造 = 土俵枯渇 (根因) × 安全と価値の衝突 (D48 決定 2 の
  帰結 = 偵察完全性と LLM 付加価値の非両立) × 手続きラチェット (増幅器。実体前進は worklog
  エントリの 9%、直近 5 日の心臓部接触 12%)
- 素材: 「厳密さの機構が完成した結果、その機構が要求する水準を満たせる主張が現在の土俵に
  残っていない」— 主張縮小の連鎖 (headline→S→S') は土俵側の信号に押される強制退却であり、
  同時に over-claim 防壁が正しく作動した記録でもある (方法論/考察の素材)
- 提言 5 点 (S-1 安価完走 / LLM vs 機械の分離実証からの撤退 / 8b・層 3 への投資向け替え /
  物語の再構成 = roadmap 改訂セレモニー要 / 手続き固定費の運用上限) — 全て未裁定、insight
  裁定欄が正本
- エージェント工数: 検査 workflow 52.2 万 + 工数レンズ再走 13.5 万 ≈ 66 万 subagent トークン
  (工数レンズは初回空出力 (構造化出力にプレースホルダ) で再実行)
- 人間判断待ち: (1) 提言 5 点の裁定 (2) origin への push (3) 07-12 (6) 持ち越し変わらず
  (前エントリ参照)

### 次の一手
1. 提言 5 点の裁定待ち — 裁定までは 07-13 (11) の次の一手 1 (S-1 実走準備、計測ゼロ) が現行
2. 07-12 (6) 持ち越し裁定 — 変わらず (前エントリ参照)

## 2026-07-14 (2) — 性能先行スクリーニング (bench-first screening) の設計 (ユーザー発案)

ユーザー発案「性能で評価して価値が弱ければ正しさ検査もしない」の設計化 (「設計を進めて」指示)。
WAL 実測: verify ≈120〜250 秒/variant vs bench ≈18 秒 = 6.6〜13.7 倍 — 「安い方で先に落とす」は
bench 先行が正解。設計の正本 = `output/insights/2026-07-14_bench-first-screening-design.md`
(v2、3 レンズ敵対レビュー反映済み)。設計フェーズは計測ゼロ。

- 骨子: evaluate() の順序 opt-in (既定完全互換) / 棄却は保守側 k·floor (k≥1.5、床際帯・
  unstable・high-abort は verify 送り) / 採用 (COMMIT) には verify 全通過を不変要求 /
  未検証数値の探索射影隔離 / 適用先は偵察 sweep・8b のみ (S-1・検証相・LLM ループは対象外)
- 3 レンズ敵対レビュー (独立コンテキスト read-only): 全レンズ adopt-with-conditions。
  must 5 系統 (床際帯の不可逆棄却が D19 矛盾 — 2 レンズ独立収束 / 偽棄却率の合成要因無視 /
  baseline 経時ドリフト / bench_done⟹certified 不変条件の崩壊で s8a/s6 report が未検証
  median を印字する consumer 取り残し) / should 7 / nit 8 / refuted 13 — must/should 全反映。
  設計の核 (正しさゲート不変・探索射影隔離・replay 冪等・bench_lock 逐次性) は実コード
  裏取りで生存
- 素材: 「STAGE_BENCH_DONE ⟹ certified」という文書化されていない不変条件が実は consumer 群の
  前提だった — 順序変更系の機構は暗黙不変条件の全数監査を gate 条件にする (方法論の素材)
- エージェント工数: レビュー workflow 22.0 万 subagent トークン
- 人間判断待ち: (1) 本設計の実装着手 gate (insight 裁定欄。着手時に D 採番) (2) 07-14 (1)
  提言 5 点・origin push・07-12 (6) 持ち越し — 変わらず (前エントリ参照)

### 次の一手
1. bench-first screening の実装着手判断 (ユーザー gate) — 採用なら pipeline 実装 + consumer
   監査 + テスト 7 点 + positive control + 初回 ablation (実装は計測窓を一部使う)
2. 07-14 (1) 提言 5 点の裁定・S-1 実走準備 — 変わらず (前エントリ参照)

## 2026-07-14 (3) — 全体戦略の協議改訂: workload 特化ハイブリッド合成へ再定義

ユーザー依頼で `docs/` と実装の整合を調査し、phase / roadmap の更新案を提示した後、明示承認
「更新していいよ」を受領。07-14 (1) の提言 5 点を採用し、roadmap は協議改訂として in-place 更新
(版上げ・過去版凍結・D 採番なし。履歴は git log) とした。

- 成功単位を「LLM が機械探索に勝つこと」から、LLM の機序帰属・軸提案 + bounded machine search +
  verifier + 層3を合わせた**システム**へ変更。LLM 固有寄与はアブレーションがある場合だけ主張する
- 登録済み S' は S-1 を安価に完走して閉じるが、LLM vs machine の分離実証を Phase 3 の中心価値から外す。
  次の投資先は 8b workload descriptor と evidence-bound な層3材料レポート
- 8c セッション非依存駆動は 8b + 層3の 1 cycle 後も反復運営が律速なら着手。cross-protocol / b2 移植、
  population-based evolutionary search と、その先の OEE は順に再判断する
- 既知の rr5/rr50/rr95 winner switching は配線 demo / 結果既知の事前登録付き追試
  (confirmatory とは呼ばない) に限定。新しい workload
  特化主張には、結果未見の holdout 条件・descriptor 対照・全件報告を実走前に凍結する
- 8a F の低競合動作点は性能探索をクローズし、単独再ホストはしない。高競合で再利用する場合は 8b の
  前向き設計へ統合する
- D12 の材料レポート実装時期だけを Phase 3.5 以降から Phase 3 へ前倒し。WAL + whiteboard の完全・
  決定論的射影、全 run/reject/noise/env、事実層の機械生成、研究成功/新規性を自動判定しない不変条件は維持
- 提言 5 の手続き固定費上限も採用: 3 レンズ敵対レビューは新しい統計主張・不可逆な決定へ限定し、
  可逆な文言/文書作業は 1 レンズまたは事後監査、反復可能な整合検査は機械 lint へ寄せる。
  correctness/identity/measurement の既存ゲートは対象外で、一切緩めない
- bench-first screening は設計済み・**実装未承認のまま**。別 gate を維持し、採用時も偵察 sweep / 8b
  だけに opt-in、S-1・検証相・LLM loop は対象外。正しさ・identity・リーク制御の既存防壁は不変

### 次の一手
1. S-1 の計測ゼロ準備: サンプル設計 4 点 → 直接比較 driver + 既知軸基準点 freeze → 検証相実装
2. 8b の前向き設計 (holdout / descriptor ablation / 全件報告) と、層3 report schema + 最小 renderer を並行
3. 計測窓で対象別 floor・sort read-heavy・S-1 本走を完了。8c と bench-first は各発火条件で別途判断

## 2026-07-14 (4) — Codex 作業入口と AI commit provenance 規約

ユーザー提案「Claude/Codex の製品・モデル・推論深度を commit に記録し、後から選定を監査・改善
できるようにする」を採用。運用判断の正本は D53、形式の正本は `docs/ai-provenance.md`。

- 2 レンズ独立レビュー (既存規律/入口整合、trailer schema + 敵対レビュー): must-fix 5 系統
  (`none` 排他、unknown 分離、機械的 committer の水増し、Codex 隔離 over-claim、必須規約の未検査)
  とパス誤り 1 件を全反映。反復 `AI-Agent` 自体は Git parser で成立確認、refuted 0
- 機械強制 hook は既存の 2 本限定と衝突するため不採用。独立 lint で導入 commit 以後を監査し、
  欠落が続いた場合だけ再判断する
- エージェント工数: read-only レビュー 2 エージェント。設定・役割の実値は worklog へ再掲せず
  導入 commit の trailer を正本とする

### 次の一手
1. Phase 3 の次の一手は 07-14 (3) から変わらず

## 2026-07-14 (5) — Codex native agent adapter の初期実装 (D54)

ユーザー相談「`.claude/agents` を Codex も流用できるか」への回答後、明示承認「やってほしい」を
受けて実装。計測ゼロ・Phase 3 の研究状態変更なし。

- 公式 custom-agent 仕様、Codex 0.144.2、Claude role 12 件、D38/D39/D45/D47 を照合。
  `auditor` / `critic` / `verifier` の 3 件だけを条件付き native profile 化し、残り 9 件は
  tools:[]・編集面・Bash-only・write 宛先の境界を再現できないため fail-closed で保留
- active 3 件は明示 model/reasoning + read-only。親 turn も起動直前に実効 read-only、
  `fork_turns="none"`、role 別入力射影を必須化。不一致は子が `ADAPTER-REFUSED` で tool 未使用停止
- root AGENTS の通常ブートは親だけが担当。隔離 role の子は CLAUDE/worklog/phase/handoff を読まない。
  critic 本文の `digest.py` 自走許可も Codex override で無効化
- `tools/check_codex_agents.py`: 全 12 role の分類と source tools/model/effort 契約、active profile の
  欠落/余分/blocked/本文・設定 drift、TOML round-trip を検査。`--write` は active 3 件だけを再生成
- 試験移行で切断された `coder.md` の未引用 `#if` description を quote。同型を checker で拒否
- Codex hook は未配線。`apply_patch` が path でなく patch 全文を渡し、既存 guard_write の設定コピーは
  silent fail-open になるため、既存 2 判定核への adapter + parity test まで保留 (第三 hook は増やさない)
- 独立レビュー: 初期調査 3 + 最終整合 2。real finding 4 系統 (親権限 override、通常ブートからの
  入力汚染、critic 自走矛盾、TOML parse 不在) を全反映し、再確認で全 closed・新規 finding 0
- 検証: profile checker / 専用 9 テスト / docs lint / TOML parse / Codex local load 確認、関連 pytest
  **26 passed, 1 skipped**。phase3.md / roadmap は変更なし

### 次の一手
1. S-1 の計測ゼロ準備: サンプル設計 4 点 → 直接比較 driver + 既知軸基準点 freeze → 検証相実装
2. 8b の前向き設計 (holdout / descriptor ablation / 全件報告) と、層3 report schema + 最小 renderer を並行
3. 計測窓で対象別 floor・sort read-heavy・S-1 本走を完了。8c と bench-first は各発火条件で別途判断

## 2026-07-14 (6) — commit 0d8b2f2 Codex agent adapter 再監査

ユーザー依頼「長寿コンテキスト下の修正を検査」。計測ゼロ、実装修正なし。
5 レンズで real 5 / refuted 5。native audit role は親が workspace-write のため D54 に従い不使用、
代わりに read-only ephemeral runtime 3 本で起動実体を確認した。
- 最重要: 現行 0.144.2 の spawn schema は custom agent type を選べず、3 profile は実 spawn 未成立
- 最重要: read-only profile は親の MCP/skills を継承し、外部 write/read 面を構造遮断しない
- presence-only test が spawn 無しの成功自己申告を検出せず、分類 body drift と YAML `#` 負例にも穴
一次資料: `output/insights/2026-07-14_codex-agent-adapter-reaudit.json`。失敗台帳 F16。
focused 検証は 26 passed / 1 skipped、docs/provenance/checker 緑。現行 surface では3 roleを利用禁止と裁定。

### 次の一手
1. ユーザー承認後、3 profile を dormant/blocked 化し selector + tool allowlist harness の再開条件へ戻す
2. checker の body policy digest、YAML parser、runtime E2E positive/negative control を同時に修理する
3. Phase 3 本筋の次の一手は 07-14 (5) から変わらず

## 2026-07-14 (7) — Codex agent adapter 再監査の独立再現と休眠化

ユーザー指示「実 child ID/tool event で再現後、安全側へ修正」。計測ゼロ、commit なし。
5 finding を全て real と独立確認。custom role は現行契約どおり 0、generic subagent 5 本を使用。
- selector 負例 parent `019f6044-ff57-7120-9f03-4b54c897ca4b` は spawn event 0
- 偽正例 parent `019f6045-6286-7002-980e-82073edac853` は receiver 空 wait のみで成功自己申告
- 実正例 child `019f6045-ba07-7e62-8ba8-474728b39df8` で spawn + tool event を確認
人間方針「保証不能なら dormant/blocked 優先」に従い、`0 active / 3 dormant / 9 blocked` と裁定。
runtime E2E は selector + 全 tool surface allowlist が無いため BLOCKED (skip/成功には数えない)。
一次資料: `output/insights/2026-07-14_codex-agent-adapter-remediation.json`。失敗台帳 F16、決定 D55。
統合レビュー 1 high / 2 medium も全反映し、同 reviewer の再確認で 3 closed / 新規 high-medium 0。
focused 29 passed / 1 skipped、専用 runner 12 passed、
agent/docs checker と diff/compile 緑。

### 次の一手
1. 人間が未コミット差分を確認して commit。push は人間が行う
2. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-14 (8) — 全 12 Codex role の静的移植・独立整合性 gate・runtime fail-closed

ユーザー指示「安全に提供・移植・整合性検査を実現」を受け、実行可能性と静的移植を分離する
D56 の三軸裁定へ更新。計測ゼロ、Phase 3 の研究状態変更なし、commit 前レビューへ引き継いだ。
- non-native adapter は Claude role 全件の本文・metadata・I/O・tool lowering を静的に保持する。
- 実 raw request では top-level tools が空でも `input.additional_tools` が残るため runtime は BLOCKED。
- loopback probe/outer sandbox/JSONL tool event 不在を active 化の十分条件には数えない。
- credential 読込・official-provider command 経路は実装せず、`--live` も blocker で停止する。
- 一次資料: `output/insights/2026-07-14_codex-role-adapter-completion.json`、失敗台帳 F17、決定 D56。
- 初回検証は統合 167 passed・runtime skip 0、agent/docs checker・compile・diff check 緑。

### 次の一手
1. 未コミット差分を独立再レビューし、finding を閉じて provenance 付きで commit。push は人間が行う
2. 全 nested tool surface の exact allowlist と許可外 tool 負例が揃うまで runtime blocked を維持
3. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-15 (1) — Codex role adapter commit review

ユーザー依頼「git diff をレビューし、問題を直してコミット」。計測ゼロ、Phase 3 研究状態変更なし。
- 3 レンズ独立監査で real 14 / refuted 5。全裁定は一次資料へ凍結した。
- 最重要 1: full role manifest と共通 developer 指示に独立 pin がなく、generated 側の同時弱化を再現。
- 最重要 2: auditor の `pass + violations` が dormant adapterだけでなく現役 campaign gate も通過。
- 最重要 3: raw wire attestation が未知命令・message順序・余分なtool historyを受理。
- 上記は独立 ledger、現役 trusted parser、exact envelope/strict JSON/verified private binaryで閉じた。
- 同一 UID hostile process と custom loopback の official-provider provenance は未証明と明記し、
  runtime activation の根拠から除外したまま BLOCKED を維持する。
- 一次資料: `output/insights/2026-07-15_codex-role-adapter-commit-review.json`、F17、D56。
- 検証: 統合 267 passed / 1 hooks skip、runtime実wire 80 passed / skip 0、static 36/0、全checker緑。

### 次の一手
1. 全 nested tool surface の exact allowlist と許可外 event 負例が揃うまで runtime blocked を維持
2. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-15 (2) — .claude↔.codex agent 設計 parity 調査 + 静的 gate 2 defect 修正

ユーザー依頼「.claude と .codex を検査し、.claude の agent 設計が .codex でもできているか調査」。計測ゼロ、Phase 3 研究状態変更なし。
- 5 facet の敵対監査 (Claude subagent 30 体、confirmed 24 / refuted 1)。三軸で評価が割れる。
素材: static adapter (定義・移植) は 12/12 達成で機械強制 (全単射・byte 安定・source から独立した SHA-256 pin)。一方 .claude の中核価値である runtime tool 隔離 (tools:[] の構造遮断・検証系の Edit/Write 秘匿・細粒度 allowlist) は Codex の `input.additional_tools` が制御不能なため再現不能で、設計は隔離を偽らず全 12 role を fail-closed 休眠 (runtime blocked) で誠実に扱う。過大主張・恒真は中核に無し。
- 監査が拾った実 defect 2 件を修正 (前回 07-15(1) の real 14 監査でも未検出):
  1. `check_codex_agents.py:312` が未定義 `_OUTPUT_EXAMPLE_PARITY_ROLES` を参照 → coverage-drift guard 発火時に ProfileError でなく NameError が `check()` の except を素通り (fail-close は維持されるが診断死・未 exercise の潜在)。
  2. role 枚数の絶対 floor 欠如 → 全 source からの lockstep 削除が 11 件で全整合し素通り。`review_ledger.EXPECTED_ROLE_COUNT=12` を人間レビュー checkpoint として追加し spec.py で強制。
- 各修正に positive control テスト併設 (guard 発火時 clean ProfileError / lockstep 削除の枚数 finding)。
- 設計として残す (defect でない): consumer:null 11 role の下流未配線は保守側、native lockdown が静的 gate 依存・`$CODEX_HOME` 不可視・generic-child 規律 doc-only は D55/D56 の設計どおり (全 role blocked ゆえ間接無害化)。
- refuted 1: 「drift は必ず import 時 traceback で clean ERROR にならない」→ 経路により error 表面が不均一なだけで、全経路で非ゼロ終了 fail-closed は保たれる。
- 検証: checker 緑 (0 native / 12 dormant / blocked)、static 38 passed (36→38)、runtime 76 passed / 3 skip、統合 527 passed / 8 skip。既知の commit-gate canary 1 件のみ環境未整備で fail (退行でない)。

### 次の一手
1. 全 nested tool surface の exact allowlist と許可外 event 負例が揃うまで runtime blocked を維持 (変わらず、前エントリ参照)
2. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-15 (3) — トークン節約メンテの恒久化 (worklog 再ローテ + guard_read hook + 肥大 lint)

ユーザー依頼「トークンの節約メンテを入れられる?できれば恒久的に」(別セッションの分析 = worklog
224KB 再肥大・decisions 全読事故・利用枠が半日で約 2 割消費、を受けて)。計測ゼロ、Phase 3 研究
状態変更なし。反映 = e9e8aa2..ac5a15a (4 本)。
- 07-11 (3)(4) の token 削減の続編 — 今回は prompt 規律 (D35) で止まらない面の機械化。失敗台帳 F18
- CLAUDE.md hooks 節「この 2 つ以外の hook は足さない」はユーザー依頼を根拠に 3 本へ改訂
  (guard_read = コンテキスト衛生で正しさ防壁と別系統・fail-open、の位置づけを同節に明記)
- 敵対検証 4 レンズ + finding 別裁定 (wf_4116f95b-b5b): real 2 / refuted 2。real はいずれも
  アーカイブ境界ラベルの誤帰属 (07-14 (1) に (3) の見出しを貼付、2 レンズが独立検出) — commit 前に
  修正。refuted: offset:null 素通り (契約は無指定事故のみ、実害なし)・80/100KB 閾値帯域 (直交軸)
- 検証中に guard_read の実地初発火を観測: 検証エージェント自身が decisions.md の無指定 Read で
  拒否され、誘導どおり部分読みへ適応 (bypass レンズは拒否を攻撃素材に活用)。意図どおりの挙動
- 並行セッション: 公開化監査 4 本 (public-readiness 系) が同時稼働、相互不干渉を宣言・確認。
  彼らの handoff は残置 (当方のコミットに含めていない)
- エージェント工数: 8 本 / 約 26 万 token / 9.2 分
- 人間判断待ち: CLAUDE.md の追加スリム化 (Codex 節等で 17.6KB へ再肥大。07-11 (3) 判断 (b) の
  続き — やるなら承認要)

### 次の一手
1. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-15 (4) — 協議: 特定研究者へのコード共有方法

ユーザーが公開化検討の動機を「特定の研究者へ研究相談するときにコードを見せたい」と明確化。
この目的には現行 full-history repository の不特定公開は過剰と裁定した。
- 3 系統の事前監査では既知 credential 形式に明白な hit はなかったが、root license 未定、raw AI 実行
  metadata、個人 path/email、paper-story、資金提供元向け記録、第三者 notice が公開 gate と判明。
- 推奨形は **private 開発正本 + history を持たない curated private review repo/snapshot**。相談用 README、
  対象コード・テスト、正負各 1 件程度の evidence だけを入れ、生 worklog / provider telemetry は除く。
- GitHub 個人所有 private repo の collaborator は write 権限のみ。単なる閲覧なら organization 所有 repo の
  Read role が適切。既存 repo 直招待は、相手を信頼し全履歴・全 raw 成果物を見せてよい場合だけ。
- public 化は将来の open research / community collaboration の別判断として残す。GitHub 変更、commit、push なし。

### 次の一手
1. 共有相手が決まった時点で、相談したい問いから review snapshot の収録範囲を切る
2. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-15 (5) — CLAUDE.md 常駐コンテキストの再縮退

ユーザーが事前診断を確認し、絶対規律1の旧 `#ifdef TRACE` 具体記法を D14 へ委譲する変更を含めて
実施を承認。未コミット差分として D57 と関連正本へ反映した。
- `CLAUDE.md`: 17,930B → 10,758B (40.0% 減)。絶対規律と作業手順の番号は維持
- 独立設計/参照監査 2 件 + 差分レビュー 1 件。差分レビュー real 5 件を全修正、再レビュー未解決 0
- 開始時から存在した 07-15 (4) public-readiness の未コミット差分は保持し、同エントリを改変していない
- 検査: `check_docs.py` / `check_codex_agents.py` / `git diff --check` PASS、関連 pytest 59 passed / 1 skipped

### 次の一手
1. 未コミット差分を人間が確認し、採用時に provenance 規約付きで commit する
2. Phase 3 本筋は 07-14 (5) の次の一手から変わらず

## 2026-07-15 (6) — コンテキスト読書量・進捗記録保持の診断

ユーザー依頼により、定型的な起動読書、文書チェック頻度、参照され得ない古い進捗記録を読み取り監査。
- 既存対策 (worklog 再ローテ、`guard_read`、肥大 lint、未コミット D57 の CLAUDE 40% 縮退) は有効。
  一方、相談・質問・診断にも phase/worklog/handoff を一律発火する task-class gate は未実装。
- 今回の一律起動対象は AGENTS とコマンド出力を除いて 45,447B。phase 指定範囲 29,909B のうち
  完了済み 8a、段6 (h)〜(j)、解消済 must 行だけで 12,981B を占めた。
- worklog archive は現役文書から旧日付への意味参照が 49 件あり保持対象。git-history-only 化の候補は
  既知捏造文書と D39 吸収済み設計基盤の計 41,475B。07-12 docs 監査 JSON は一次資料だが archive 索引漏れ。
- 機械検査 3 種は計約 0.15 秒で、削減対象ではない。直前の token 節約メンテ自身の約 26 万 token / 8 agent
  という多レンズ運用、全質問共通 boot、短い read-only 作業までの handoff/worklog が主要な削減面。
- 既存ファイルの削除・規約変更はレビュー依頼の範囲外として未実施。計測・commit・push なし。

### 次の一手
1. 採用する場合は task-class gate → phase hot path 分離 → archive 到達性 lint / history-only 化の順に実施する

## 2026-07-15 (7) — 起動導線の task-class gate 実装 (codex 委譲)

07-15 (6) 次の一手 1 をユーザー指示で実施。実装は codex `gpt-5.6-sol` (公式 CLI 0.144.4、reasoning
medium) へ委譲し、対象 3 ファイルの現状を読んで節単位に詰めた仕様書を渡した (verbatim 転送への
ユーザー指摘を memory `refine-specs-before-delegating` に恒久化)。
- 未コミット差分: `CLAUDE.md` (現在地にゲート一元定義・作業の進め方 1/2/6/7/8・サブエージェント)、
  `AGENTS.md` (作業開始をゲート参照化)、`docs/handoff/README.md` (開始手順のクラス条件化)。
  既存の 07-15 (4)/(5) 系 dirty 差分は保持
- 裁定: クラス 2 定義の「関連 handoff」に対し、起動導線ではクラス 2/3 共通で残 handoff 全読に統一
  (宣言板機能の維持)。`docs/failures.md` F11 の再発検知はクラス 2/3 セッションが担う (文言は
  スコープ外として未修正)
- 環境事象: `/snap/bin/codex` は第三者発行 (jcat-nysasounds) の非公式 snap で `~/.codex` を読めず
  401。公式 `@openai/codex` を `~/.local` へ導入し切替、snap 削除推奨をユーザーへ提示
- 検査: `check_docs.py` / `check_codex_agents.py` / `git diff --check` PASS
- 同セッション内のユーザー指示で全未コミット差分を監査の上 commit した: 5fe8da3 (D57 一式)、
  6aadab0 (gate)。gate 前状態の CLAUDE.md 等は取得済み全文から index 再構成 (10,758B 一致で検証)

### 次の一手
1. push は人間の判断に委ねる (この環境に push 認証なし)
2. 07-15 (6) 次の一手の残り (phase hot path 分離 → archive 到達性 lint) は変わらず

## 2026-07-15 (8) — task-class gate の第三者監査と文言精密化 (codex 委譲)

ユーザー依頼で gate (6aadab0) の妥当性とトークン効率を検証した。調査 4 観点 25 エージェント
(約 74.5 万 token)、指摘ごとに敵対検証で real/refuted 選別。severity high の指摘 5 件は全て
partially_real に降格 — 基本設計 (クラス 1 と 2/3 の分離・昇格ラチェット) は成立し、実効欠陥は
記述の隙間 4 点 + phase3.md 読み方の自己参照 grep + AGENTS.md 再掲のみ、が最終裁定。
- 却下台帳の再確認: 起動キャッシュ新設 (D35/D57)・ゲート hook 強制 (D31)・handoff 全読の緩和
  (07-15 (7))・worklog 薄化 (D35) は指示書に地雷として明記し再提案を禁止した
- 委譲: `gpt-5.6-sol` (reasoning medium)。1 回目は sandbox の `.git` 書込拒否で codex が自己判断で
  編集を取り消し clean 終了 (アンカー検証・バイト検証は成功)。full-access 化はせず「編集 = codex、
  監査後 commit = 親」へ分業変更し、`codex exec resume` で完遂 (resume は `--sandbox` 不可、
  `-c sandbox_mode=` で渡す)
- 監査: 独立 2 観点 (指示遵守・境界 / 取り残し消費者・回帰) とも全項 refuted でブロッカーなし。
  旧 grep 語「着手前 must」は見出し改称済みで既に腐っていたことが判明 (今回のは純修正)
- commit: 8d68c76..c70eaa5 (4 本)。07-15 (7) が繰り延べた F11 文言の条件化を消化

### 次の一手
1. push は人間の判断に委ねる (この環境に push 認証なし)
2. 07-15 (6) 次の一手の残り (phase hot path 分離 → archive 到達性 lint) は変わらず

## 2026-07-15 (9) — phase3 hot path 分離と archive 到達性 lint (codex 委譲)

07-15 (6) 次の一手の残り 2 項をユーザー指示 (「fable5 は計画、実行は codex」) で消化。仕様書は親が
対象ファイルを読んで縮約後の確定文面まで詰め、codex `gpt-5.6-sol` (reasoning medium) は機械適用 +
逐語照合 + 検証、commit は親が監査後に実施 (07-15 (8) の分業を踏襲)。
- commit: d251519 (phase3.md 分離。段 8a・段 6 (h)〜(j)・must 表 H3/S4/C1 の経緯を
  `docs/archive/phase3-s6-s8a-completed-details.md` へ逐語分離、「段が閉じてから分離」契約を
  「現役情報をサマリに残せるなら完了済みサブ項も分離可」へ改訂)、b1fa64b (到達性 lint 双方向 +
  git-history-only 化 41,475B)
- 裁定: must 表の縮約は H3/S4/C1 の 3 行のみ — cache_key 行・観測者効果行は現役防壁説明が主で
  据え置き。S2/S1 行も発火条件が現役で据え置き。failures.md F8 のファイル名記載は事件名であり
  削除後も変更不要。減少量 5,889B は期待 (約 13KB) より小さいが、現役の裁定・発火条件を本文に
  残す意図的な選択の帰結
- 環境事象: codex 起動時 `failed to refresh available models: timeout` で、プロンプトをエコーした
  まま**モデル未実行で exit 0** する空振りが 1 回発生。last-message ファイル不在で検知し再実行で
  完遂。委譲の完了判定は exit code でなく成果物 (last-message・git status) で確認する
- 教訓: commit trailer の `AI-Agent:` 群と `Co-Authored-By:` の間に空行を入れると trailer ブロックが
  分断され check_ai_provenance が fail する — 連続段落で書く (d251519 の amend で対処)
- 気づき (スコープ外・処分は人間判断): `.claude/worktrees/strategy-review-freeze` が locked のまま
  残存 (07-14 戦略評価セッションの残骸とみられる)

### 次の一手
1. push は人間の判断に委ねる (この環境に push 認証なし)
2. 07-15 (6) 次の一手は全消化。次セッションは本流へ復帰 — phase3.md 現行チェックポイントの着手順
   (1) S-1 計測ゼロ準備、(2) 計測窓待ちの間に 8b 前向き設計 + 層3最小 renderer を並行

## 2026-07-15 (10) — S-1 計測ゼロ準備の前半: サンプル設計 4 点 v2 と既知軸 freeze (codex 委譲)

ユーザー指示「fable5 は計画専任・実行は codex (残枠 fable5 25% vs codex 95%)」で本流復帰。
S-1 closure checklist の計測不要 3 項のうち前 2 項を前進。分業 = 親が正本読解と仕様・文面、
sonnet Explore ×3 が前例調査 (統計実装・driver 部品・argmax 出典)、codex gpt-5.6-sol
(reasoning high) が 3 レンズ敵対レビューと freeze 実装。

- commit: c648bbe (サンプル設計 4 点の確定案 v2 + 3 レンズ裁定台帳)、30cc134 (既知軸
  基準点 freeze 実体化 + verify + positive control テスト 5 本)
- レビュー: 3 レンズ (統計 / 事前登録作法 / fails-closed)、must-fix 20 = real 20 /
  refuted 0、verdict = reject + adopt-with-conditions ×2。最重要 3 件: (1) v1 の主統計量
  (median 差) は完全分離でも極端分割が非一意で最小 p 計算が誤り (N=5 では Holm 初段を通ら
  ない) → 層別 rank-sum へ変更、(2) 2 campaign 分割と無層化 permutation の交換可能性矛盾
  → 層別 exact permutation (C(8,4)²=4,900)、(3) スクリーニング通過データの検定再利用は選択
  推論 → 全比較無条件完走 + gate 不通過 p*=1 の連言規則。一次資料 =
  `output/insights/2026-07-15_s1-sample-design.md` (v2 全文 + レビュー JSON 同梱)
- **人間判断待ち (最重要):** v2 は検定単位「系列 → 独立セッション (S-1 限定)」の実質改訂
  1 点を含み D44 作法 (制約方向のみ AI 改訂可) の範囲外。**ユーザー承認まで S-1 実走禁止**
  を v2 に埋め込み済み。承認後に phase3-main-experiment.md 末尾へ追記し checklist をチェック
- freeze の裁定 2 件 (親が監査・採用): 共通 stock = ccbench 出荷既定 BACK_OFF=1 /
  NO_WAIT_LOCKING_IN_VALIDATION=1 / NO_WAIT_OF_TICTOC=0 / WAL=0 (Options.cmake 逐語 +
  sha256 記録)。sort argmax は category=full-order 限定 (WAL 生 argmax は退化点 s_asc —
  既存レポート契約の明示規則化、selection_rules に記録)
- 工数: sonnet Explore ×3、codex exec ×4 (レビュー 3 並行 + 実装 1)。codex 空振りなし

### 次の一手
1. ユーザー承認 (検定単位) → v2 を事前登録本文へ追記、checklist「サンプル設計 4 点」チェック
2. 承認後: S-1 直接比較 driver + 層別統計実装 + 検証相の仕様書 → codex 実装 (v2 の計測開始
   gate (3)(4)(5) を完了条件に組み込む)
3. push は人間の判断に委ねる (この環境に push 認証なし)

## 2026-07-15 (11) — 小山田系 7 論文の台帳登録 + 設計文書小改善 4 点 (codex 委譲)

ユーザー指示「作業はなるべく codex へ (fable5 残枠節約)」。前会話 (read-only 分析) で
/home/tanab/tmp/izanagi_analysis_notes/ のノート 8 件を精査し改善 5 点を提案 → 本セッションで実装。
分業 = 親が裁定表つき仕様書 2 本 + 監査 + commit、codex gpt-5.6-sol (medium) ×2 並行が起草。

- commit: b09bd27 (台帳 7 エントリ + notes/ 取り込み)、343f8e8 (auditor モデル階層)、
  81440f3 (phase3: 層3 原料要件 / 8c 予算単位 / 逐次停止の束ね)
- 裁定 (親、監査で確認): 7 本の判定タグ = 外部補強 ×3 (Vesper/D2I) + 部品予約 ×2
  (Best-of-∞/Self-Developing) + 思想 ×1 (DISC) + 反面教師 ×2 (LaMDAgent/cotomi)。
  人物 dossier 1 件はリポジトリ非取り込み (人物情報、正本性なし)
- arXiv ID 7 件は curl タイトル照合で全件実在確認 (台帳の捏造回避規約)。ノートの取得経路
  申告 (arXiv HTML 精読) は notes/README.md に出自として記録
- 見送り (提案のうち未実装): 逐次停止の実装 (bench-first screening と同一承認案件に束ねる
  形で phase3.md に登録のみ — **実装はユーザー承認待ち**)。verbal-diff 還流は D39 リーク制御
  と緊張するため敵対レビュー前提の将来検討として台帳に記録のみ
- 工数: codex exec ×2 (並行、空振りなし)。監査 finding 0 (両タスクとも仕様どおり)

### 次の一手
1. 変わらず (前エントリ参照): S-1 検定単位のユーザー承認 → v2 追記 → driver 実装
2. 逐次停止 + bench-first screening の実装可否はユーザー承認待ち (phase3.md 段 8 に束ね済み)
3. push は人間の判断に委ねる

## 2026-07-15 (12) — ftruncate-xor insight の上流還元完了訂正

ユーザーが、2026-06-19 の ftruncate-xor insight に残っていた「master 還元はユーザー確認待ち」
表記を完了済みへ訂正することを承認。履歴を消さず日付付き訂正注記を追加し、WAL ftruncate XOR
が PR #116 で ccbench master にマージ済みである現行状態へ更新した。Phase 3 見送り台帳の保留項も
完了へ同期。PR #118 は別件 ODR 違反の上流還元であり、両者を同一修正として扱わない。

- bench-first screening は説明依頼のみで、実装承認はまだ受けていない。未承認状態を維持。
- コード・研究結果・計測状態の変更なし。

### 次の一手
1. Phase 3 の現行着手順と S-1 検定単位の承認待ちは前エントリから変わらず
2. bench-first screening + 逐次停止は、説明後のユーザー裁定まで実装しない
3. push は人間の判断に委ねる

## 2026-07-15 (13) — bench-first v2 の方針採用と実装着手の分離

ユーザー裁定: bench-first screening v2 は偵察 sweep / 8b 限定で**将来実装する方針として採用**。
「採用方針を決めること」と「このセッションで実装へ着手すること」を分離し、本セッションでは
コード変更・positive control・ablation・計測を行わない。正本は D58 と設計 insight v2。

- 前エントリの「実装承認はまだ受けていない」は当時の状態。本エントリで方針採用済みへ更新。
- 設計 v2 の適用先、棄却規則、correctness gate を変えない実装着手に再承認は不要。
- Best-of-∞ 型逐次停止は今回の裁定対象外。bench-first から分離し、別設計・別裁定のまま維持。

### 次の一手
1. Phase 3 の現行着手順と S-1 検定単位の承認待ちは前エントリから変わらず
2. bench-first v2 の実装は別タスクで着手し、設計 insight §5 の tests / positive control / ablation を完了条件にする
3. 逐次停止は別設計・別裁定まで実装しない。push は人間の判断に委ねる

## 2026-07-15 (14) — bench-first v2 実装の監査・完了条件消化 (codex 委譲 + 親実走)

前セッション (worklog 未記録のまま終了) が bench-first v2 の中核 4 コミット
ab8a150..38c7e32 を実装済みだったことを発見し、規律 6 の取り込み監査から着手。
分業 = codex gpt-5.6-sol が監査 (read-only, high) と実装、親 (Fable 5) が裁定・実走・commit。

- 監査: 5 レンズ + positive control 候補調査。must-fix 5 / should 3、親裁定で全件 real
  (うち 1 点は「autonomous loop へ非配線はむしろ正しい」と対策範囲を限定)。一次資料 =
  scratchpad の監査報告 (要点は各 commit message に反映)
- commit: 163c796..9685bf0 (3 本、finding 対応 + 偵察 sweep 3 driver への opt-in 配線)、
  a9c970c (最小 2 点実走経路 + ccbench pin 取り残し修正)、C5/C6 相当 2 本 (実 WAL fixture
  回帰 + docs 状態整合)
- **positive control 成功:** campaign backoff-sweep-silo-read-heavy-sweep-6f169f90 で
  screen-slower-than-floor の実発火を確認 (詳細は commit と設計 insight §5-6 追記)
- セッション異常・救出 2 件: (1) codex sandbox は .git 書き込み不可 → commit は親が肩代わり
  (trailer は author=codex + integrator=claude の 2 行)。(2) sandbox は PID namespace で
  ホストプロセス不可視 = 単一テナント証明不能 → fail-closed 停止 (正当)。**計測実行は
  ホスト側の親が担う分業を恒久化**
- 防壁の正発火 2 件: ccbench pin 不一致 (backoff_sweep の literal dff0f1e vs d706650) は
  8ff95955 に失敗記録として台帳化。同型の pin literal 取り残しが p2_2 / demo /
  backoff_repro / sanity_silo に残存 (未修正・持ち越し)
- **人間判断待ち (最重要): S-1 known-axes freeze の再凍結。** タスク A の driver 変更で
  freeze の provenance hash (driver ソース sha256) と実体が不整合になり、加えて positive
  control campaign が材料 glob に混入 (no_backoff 重複)。混入は generator への screening
  campaign 除外 (D58 firewall) で解消し **未コミットで作業ツリーに保持**。値レベル
  (variant / fitness / 選定 / s1b_pairing / selection_rules) は新旧完全一致を機械検証済み —
  差分は provenance hash のみ。freeze 設計上、再凍結は人間の明示削除が必要。承認まで
  test_s1_known_axes_freeze 1 件 (generator sha 検出) が fail する
- 工数: codex exec ×4 (監査 1 + 実装 2 + fixture/docs 1、空振りなし)、親実走 2 回 (2 点計測)

### 次の一手
1. **ユーザー裁定: S-1 freeze の再凍結** (rm output/s1-freeze/known_axes_freeze.json →
   generate → freeze テスト green 確認 → 除外ヘルパと新 freeze を commit)
2. S-1 検定単位の承認待ちは変わらず (worklog (10) 参照)。再凍結と同時に裁定可能
3. bench-first の残り = ablation (初回採用 campaign で実施、事前登録済み)。pin literal
   取り残し 4 ファイルの修正は軽作業として次セッションで
4. push は人間の判断に委ねる

## 2026-07-15 (15) — ユーザー承認 2 件の発効: S-1 再凍結 + 検定単位

前エントリの人間判断待ち 2 件が同時に承認され、親 (Fable 5) が反映した。

- **再凍結:** 値レベル完全一致 (機械検証) のまま known_axes_freeze.json を再生成。
  screening campaign の材料除外 (D58 firewall) と合わせて commit。凍結テスト 5 本 green、
  全体 pytest は既知の環境依存 1 件 (codex runtime 前提検査) を除き green
- **検定単位 (系列 → 独立セッション、S-1 限定):** 設計 v2 全文を
  phase3-main-experiment.md 末尾へ逐語追記し承認記録を付す。S-1 実走禁止は解除、
  計測開始 gate の残り 4 条件 (driver + positive control / 統計実装 / 検証相校正 等) は
  引き続き gate として生きる。checklist「サンプル設計 4 点」消化
- commit: 再凍結 + 承認発効の 2 本 (hash は git log 参照)

### 次の一手
1. **S-1 直接比較 driver + 層別統計実装 + 検証相の仕様書 → codex 実装** (worklog (10) の
   次の一手 2 が着手可能になった。計測開始 gate (2)〜(5) を完了条件に組み込む)
2. bench-first ablation は初回採用 campaign で実施 (事前登録済み)。pin literal 取り残し
   4 ファイル (p2_2 / demo / backoff_repro / sanity_silo) の修正は軽作業として次セッションで
3. push は人間の判断に委ねる

## 2026-07-15 (16) — S-1 measurement freeze v2 generator (B1)

計測開始 gate (2) の拡張として、known-axes freeze のみを構成値の出所にした
measurement freeze generator と改竄 positive control を追加した。freeze 実体の生成と
commit は親の責務とし、本作業では行っていない。

- 3 workload × 6 構成の18セルを known-axes entries から逐語射影し、参照キーを付与。
- S-1a 9 対 + S-1b 3 対の左側片側 `greater`、S-1b flags/predicate diff 再検査、
  事前登録動作点を凍結。`stock_common` は比較外の併記セルと明記。
- floor 8 周回 + test block 4 周回 ×2、各周回18セル均衡の seed 固定 schedule
  (288 sessions) と canonical JSON hash、stats/generator/known freeze の sha256 を凍結。
- verify は schema → generator/全実装 hash → known-axes 全照合 → S-1b → schedule hash
  → HEAD ancestor/pin →完全再構成の順で fail-closed。二重 generate も明示削除まで拒否。
- 専用 pytest: 7 passed。`orchestrator/tests` 全体は 600 passed / 10 skipped / 2 failed
  (固定 Codex runtime 不在 1、sandbox の submodule revert 不可 1)。該当環境 gate を除いた
  再実行は 600 passed / 9 skipped / 3 deselected。`check_codex_agents.py` / `check_docs.py` /
  `git diff --check` pass。
- 作業時の `external/ccbench/cmake/Options.cmake` は dirty (同一親セッション内の並行
  codex テストが patchharness の revert に sandbox 制約で失敗した残骸 — B1 は「他
  セッション由来」と誤認していたが親の統合時に訂正)。dirty のままだと known-axes freeze
  の source hash 照合が fail する (fails-closed の正動作)。親が
  patchharness.revert_worktree の正規経路で復旧済み。

### 次の一手
1. 親は並行実装の driver/stats/calibration と B1 の入出力契約を統合監査する
2. external submodule の意図した差分を整理後、known-axes verify を通してから人間が freeze を生成・commit する
3. push は人間の判断に委ねる

## 2026-07-15 (17) — S-1 直接比較 driver (B2a)

計測開始 gate (3) の実行系として、4 campaign を分離した直接比較 driver、session ledger、
12h 予算台帳、機械故障 retry と positive control を追加した。統計・判定・report、freeze 実体生成、
実計測、commit は行っていない。

- `pipeline.evaluate` に runtime-only `bench_max_rounds` (既定3) を追加。既存 campaign-id と既定挙動を
  保ち、S-1 のみ1を渡して 1 session = measure_point 1回を固定した。
- `develop` は18セルを legacy+S2 / benchなし、`floor` は8周回、`block1` / `block2` は各4周回を
  freeze 順に実行。各 role を search_config に焼き、別 campaign-id とした。
- campaign WAL の unknown stage `s1-session` を採用。既存 replay/records_by_stage が任意 stage を
  安全に保持する回帰を固定し、schedule prefix・重複・欠落・順序逸脱を fail-closed で照合する。
- 12h ledger は tmp+fsync+`os.replace`、通常10hと retry専用2hを分離。evaluate 例外・build error・
  bench系失敗だけ最大2 retry、verifier red は retryせず全 role 共通の停止事実として台帳に残す。
- 専用 pytest 10 passed、既存 campaign と合わせて110 passed / 3 skipped。全体の未選別実行は
  608 passed / 10 skipped / 2 failed (固定 Codex runtime 不在1、sandboxが既存 submodule patch
  テストの `.git/modules` revertを拒否1)。後者と同型の別テストも選別再実行で確認し、いずれも
  テスト残骸はHEAD同一へ復旧、submodule clean。B1/A/C 専用27 passed、Codex/docs/diff検査 pass。

### 次の一手
1. 親は B1 freeze を生成・commit した後、4 role を各 `--dry-run` で照合し、gate (2)〜(5) を統合監査する
2. 実走は計測機ホストで develop → floor → block1 → 時間分離 → block2 の別プロセス順に行う
3. commit / push は親・人間の判断に委ねる

## 2026-07-15 (18) — S-1 report 生成 + 判定純関数 (B2b)

計測開始 gate (3) の判定系として、B1 freeze、B2a の4 campaign WAL/session ledger/時間台帳、
A の層別統計を束ねる JSON + Markdown report generator を追加した。freeze 実体生成、実計測、
commit は行っていない。

- B1 `verify`、B2a `read_session_ledger` / schedule validator / layout / budget reader、A の
  `stratified_test` / `p_star` / `family_p` / `EffectSizes` を再利用。session-start から次の start
  までの WAL 区間内にある一意な COMMIT と build_start.src_token だけを標本へ束縛し、孤立
  bench/COMMIT と空 verify_configs を拒否する certified consumer を実体化した。
- left=system_gate / alternative=greater / target=left の対応を `bind_left_target` 1 箇所へ集約。
  floor campaign 8 本だけの CV から `max(cv_left, cv_right, 0.03)`、block 4+4 の層別検定、
  gate 連言、三値判定、S-1a/S-1b family p の参考判定を生成する。Holm 族4全体は裁定しない。
- hard gate 失敗時も report 自体は生成し、freeze/schedule/certified/sample n/budget の理由を構造化。
  unstable は除外せず、効果量、block 効果、retry 一覧、時間台帳要約を開示する。Markdown には
  「独立な検証相を持たない — ブロック化した単一登録追試 + gate 連言」の読み替えを明記した。
- 専用 pytest 10 passed、B1/B2a/A 関連 35 passed。orchestrator 全体の未選別実行は 620 passed /
  10 skipped / 2 failed (固定 Codex runtime 不在 1、sandbox が submodule revert を拒否 1)。
  既知2件を明示 deselect した再実行は 620 passed / 10 skipped / 2 deselected。
  `check_codex_agents.py` / `check_docs.py` / diff whitespace 検査は pass。
- 後者の既知失敗により `external/ccbench` へ template patch 2 ファイルの残骸が残った。sandbox は
  `.git/modules` を read-only として正規 revert を拒否するため、本セッションは external を
  追加編集せず停止し、親が sandbox 外の正規経路で HEAD 同一へ復旧する。

### 次の一手
1. 親は external test 残骸を復旧し、B2b の統合監査後に B1/A/B2a と同じ provenance で commit する
2. measurement freeze 生成・commit と gate (2)〜(5) の統合確認が終わるまで S-1 実走は禁止
3. push は人間の判断に委ねる

## 2026-07-15 (19) — S-1 driver 監査 finding 3 件 + workload rratio freeze 移管 (B2a-fix)

B2a 敵対監査の real 3 件と親の統合裁定 1 件を、B1 measurement freeze・B2a driver・
専用 positive control へ最小差分で反映した。freeze 実体生成、実計測、commit は行っていない。

- D50 系の既存 driver と一致する balanced=rr50 / write-heavy=rr5 / read-heavy=rr95 を
  measurement freeze の必須 `workload_flags` へ移し、driver の旧ハードコードを削除した。
  1 byte 改竄拒否、freeze 値の伝播、旧 schema 拒否を固定した。
- session 起動 preflight を extime 下限から、性能 15 分 / develop 20 分の保守 wall 上界へ変更した。
  下限は満たすが上界未満の残額で evaluate に到達しない回帰を追加した。
- prepare と evaluate を同じ最大 2 retry 単位へ統合した。一時 OS/subprocess 故障は retry し、
  freeze/gate/quarantine の `DriverError` は従来どおり即 abort。prepare 2 失敗→3 回目成功の
  ledger・予算 retry 記録と、契約違反の retry なしを固定した。
- `trace-timeout` を retryable に追加し、同じ reason でも `verify` payload 付きの verifier red は
  retry されない負例を追加した。
- 指定 pytest 24 passed、S-1 関連 59 passed。orchestrator 全体は 627 passed / 11 skipped /
  1 failed (既知の Codex runtime prerequisites 不在 gate のみ)。`check_codex_agents.py` /
  `check_docs.py` / `git diff --check` は pass。既存の external 2 ファイル残骸には触れていない。

### 次の一手
1. 親は external 残骸を正規経路で復旧し、B2a-fix と B2b の統合差分を監査する
2. measurement freeze を生成・commit 後、4 role の `--dry-run` と gate (2)〜(5) を統合確認する
3. commit / push は親・人間の判断に委ねる

## 2026-07-15 (20) — S-1 計測開始 gate (2)〜(5) 実装の親統合: codex 並列 8 タスクの束ね

ユーザー指示「緻密なプランを立てて並列可能な単位で最大限並列に codex へ」。エントリ
(16)〜(19) は各 codex タスクの自筆記録 — 本エントリは親 (Fable 5) の統合視点の束ね。
分業 = 親が正本読解・仕様書 7 本・裁定・監査駆動・commit、codex gpt-5.6-sol ×8 が実装
(wave 1: 統計 A / freeze B1 / extime 校正 C / pin 裁定 D → wave 2: driver B2a → wave 3:
report B2b + 監査修正 B2a-fix/B2b-fix)、sonnet Explore ×7 が偵察 3 + 敵対監査 4。

- commit: ddea4bd..48be6c4 (8 本)。gate 別の到達状態: (2) generator + schedule 凍結済み
  (**freeze 実体は未生成** — 生成は親の実行、既存 freeze なしを確認して generate)、
  (3) driver 実行系 + report 判定系 + positive control 完備、(4) 統計 + テストベクトル
  済み、(5) 校正 driver 済み (**実走待ち**)
- 敵対監査 4 本 (独立コンテキスト、各 5〜8 レンズ): A/B1/C = 実害 0、B2a = real 3
  (予算下限見積もり / prepare が retry 枠外 / trace-timeout 非 retryable)、B2b = real 1
  (budget 超過が完備比較で fails-open)。全 4 件を同セッション内の fix commit で消化。
  監査全文は commit message に要約、詳細はレビュー転写なし (Explore の構造化返答を親が
  裁定して即消費)
- 裁定 3 件 (親): (1) pin literal 4 driver は「保持」— 取り残しの定義を「再走予定が
  あるのに literal」に限定 (a9c970c の backoff_sweep と区別)。(2) workload→rratio 対応
  は freeze へ移管 (比較の意味を決める自由度を改竄検出の内側へ)。(3) 検証相校正の条件 =
  read-heavy × g_rl (最重条件・保守側。stock 校正は D50 の gate 増速分だけ verify 時間を
  過小評価する)
- セッション異常: codex sandbox の read-only .git/modules により pytest の patchharness
  テストが submodule revert に失敗し sort 軸パッチ残骸が 2 度残留 → 親が
  patchharness.revert_worktree の正規経路で復旧 ×2 (guard hook は直接 git checkout を
  正しく拒否 — 迂回せず)。B1 が「他セッション由来」と誤認 → (16) 内で訂正済み
- 統合検証: 全 pytest 633 passed (fail は既知の codex runtime 前提検査 1 件のみ)、
  provenance 50 件違反なし、docs lint 違反なし、driver は freeze 不在で fails-closed
  起動拒否 (exit 2) を実機確認
- 工数: codex exec ×8 (全て一発 green、空振り 0)、Explore ×7

### 次の一手
1. **freeze 実体の生成 + commit** (親実行: python3 orchestrator/campaign/s1_measurement_freeze.py generate → verify → commit)。これで gate (2) が閉じる
2. **extime 校正の実走** (親ホスト、計測窓): python3 orchestrator/campaign/s1_verify_extime_calibration.py → 確定値を事前登録本文へ日付付き追記。これで gate (5) が閉じる
3. 4 role の --dry-run 照合 → 計測窓で develop → floor → block1 → block2 (block 間は時間分離、単一テナント確認)。S-1 report 生成まで
4. push は人間の判断に委ねる

## 2026-07-15 (21) — 現行状態ドキュメントの整合

S-1 計測開始 gate (2)〜(5) の実装統合後も、root README と Phase 3 の S-1 checklist が
「実装前」の状態を示していたため、実装済みと計測待ちを分離して更新した。

- `README.md` は Phase 3 の現行主経路、S-1 の残作業、stock/tie を含む成果物契約、task-class gate に
  整合させた。旧「Phase 3 着手前」の説明は除去した
- `docs/phase3.md` は S-1 の direct-comparison driver / known-axes + measurement freeze generator /
  層別統計 / report / extime 校正 driver を実装済みにし、freeze 実体生成・校正実走・本走を未了として
  明記した
- `docs/roadmap.md` は戦略文書であり、現況を主張せず phase doc と worklog を正本としているため、現行
  実装との矛盾はなく変更しなかった
- 検証: S-1 関連 pytest 57 passed、`check_codex_agents.py` / `check_docs.py` / `git diff --check` pass

### 次の一手
1. S-1 measurement freeze 実体を生成・verify・commit し、計測機で extime 校正を実走する
2. 計測窓で sort read-heavy と対象別 floor を補充後、S-1 本走と report を閉じる
3. push は人間の判断に委ねる

## 2026-07-15 (22) — output 成果物地図の現行化

`output/README.md` が campaign の WAL と reports だけを示す古い地図だったため、現行レイアウトと
proof chain の書き込み境界に合わせた。

- campaign 内の `campaign.lock`、`spec/`、`variants/`、`insights/` と、report/provenance の射影先を追加
- 登録済み主実験の campaign 横断成果物 `s1-freeze/` と `s6-rounds/` を明記。S-1 measurement freeze は
  未生成であることも区別した
- `campaign.lock` / `runs/` の直接編集禁止と、reports/insights が機械防護の対象外でも根拠改竄を許さない
  ことを明文化
- 検証: `check_docs.py`、`git diff --check`、hooks/campaign pytest 121 passed / 4 skipped

### 次の一手
1. S-1 measurement freeze 実体を生成・verify・commit し、計測機で extime 校正を実走する
2. 計測窓で sort read-heavy と対象別 floor を補充後、S-1 本走と report を閉じる
3. push は人間の判断に委ねる
