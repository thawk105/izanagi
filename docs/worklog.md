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

## 2026-07-16 (1) — S-1 gate 全閉鎖 → 本走完走 → 三値判定。並行で 8b draft + 層3最小 E2E

前夜 (20) の次の一手 1〜3 を親 (Fable 5) がホスト直列で完遂。分業 = 親が計測・裁定・freeze 運用、
codex gpt-5.6-terra ×4 (8b 起草 / 層3 実装 / 8b 監査修正 / driver 修正)、監査 Explore ×2。

- **三値判定 (丸めず): S-1a = 家族不成立** (系側 gate vs 既知軸最良 9 比較: vs sort_best 3 成立
  /+55〜98%、vs p2_2_flag_opt・backoff_fixed_best 6 不成立 = gate 側が 9〜55% 低い。family
  p=1.0)。**S-1b = 家族成立** (gate on vs off 3/3、family p=0.000204、+61〜99%)。hard gate 全
  pass、予算 6.37h/12h。**Holm 族 4 全体の裁定と S' 報告文言は人間待ち** (report は参考 α のみ)
- commit 群: 02c840c..d9aef7b (9 本) — freeze 再凍結 ×2 (値レベル不変・schedule_hash 同一を
  機械確認する運用を確立)、extime=3s 校正 (gate (5))、driver 修正、8b draft、層3 renderer +
  実レポート、本走成果物 + report
- **セッション異常 1 (実体化バグ、failures.md F19):** develop v1 で backoff_fixed_best 3 セルが
  build-error → abandoned。親が WAL から診断 (hole に数値文字列を書く誤設計、正 = パッチ +
  フラグのみ)、trial v1→v2 版上げで identity 分離し v1 を失敗記録として保存、v2 で 18/18。
  開発相が本計測前にバグを検出する防壁として実証された
- **セッション異常 2 (計測汚染 near-miss):** 計測中に同居ユーザー leon が bomb_oze.exe (60 コア)
  を実行。develop 相 (verify のみ) だったため実害なし。多コア監視 + SIGINT 中断・ledger prefix
  再開の汚染時手順を handoff に裁定として残した (計測 4 campaign 中の多コア出現はゼロを確認)
- 敵対監査 2 本 (Explore、意図せず Opus 4.8 — 以後は codex read-only へ、memory 3 件更新):
  8b = must-fix 3 (nested schema 開放 / selector 機構矛盾 / holdout 検索の偽 0 件) を含む 9 件、
  層3 = must-fix 2 (双射が生産経路で恒真 / noise floor 常時 null) を含む 11 件。全件を裁定して
  codex へ差し戻し消化。親裁定の要点 = selector を採点 oracle と descriptor 依存予測選択の二層に
  分離 / 双射は本体走査 vs 入力の独立比較 + view 参照整合
- ユーザー協議: (a) サブエージェントより codex 優先 (時限方針、レート枠)、(b) codex 実行面の
  モデル表示が gpt-5.6-terra (依頼語彙 sol とずれ、config 既定も terra — 本セッションの 4 タスクは
  無指定のため terra で走った。trailer は実行面表示どおり terra で正)。協議後の実測で
  `-c model="gpt-5.6-sol"` の指定可・正常完走を確定し、**以後の codex 委譲はモデルを毎回明示
  (既定 sol)、低位モデルでも結果が変わらない難易度なら低位へ切り替えてトークンを節約する**運用に
  決定 (ユーザー指示 2026-07-16)。config.toml はユーザー所有のため書き換えない (毎回明示で担保)
- 工数: codex exec ×4 (全て一発 green)、Explore ×2、計測 wall 約 6.4h (台帳)

### 次の一手
1. **Holm 族 4 全体の裁定と S' 報告文言の確定 (人間)** — report = `output/reports/s1_direct_comparison/`
2. **8b 設計 draft の承認発効 (人間)** — `docs/phase3-8b-descriptor-design.md`。発効後に selector
   実験の実装へ
3. 層3 renderer の対象拡大 (sweep campaign への適用) と機序仮説層の原料配線は 8b と並行可
4. push は人間の判断に委ねる

## 2026-07-16 (2) — 5 裁定の全承認と実行: 族 4 確定 = S' 不成立、8b 発効 (holdout rr80/rr20)

朝のユーザー協議で前エントリの裁定待ち 5 件が全承認され、本セッション (一晩完走した親) が
確定作業まで実行してから新セッションへ交代する。

- **族 4 判定表の確定 (裁定 1):** S-1b のみ成立、S-2 第 2 段打ち切り、S-1a/S-3 非有意。帰結 =
  **縮小主張 S' は headline 不成立** (合成軸は sort には勝つが flag 最適化・静的 backoff 最良に
  及ばず、既知軸最良の超越は不成立)。最終報告 = `output/reports/s_prime_final_report.md`
  (確定文言 2026-07-13 の §6 雛形を充填、凍結集計には不作用)。事前登録へ日付付き追記 +
  freeze 再凍結 3 回目 (値不変・schedule_hash 同一) = ccfd5f1
- **8b 設計の発効 (裁定 2):** holdout = H1 (rr80) + H2 (rr20) をユーザー選択。理由 = descriptor
  中核フィールド (read/write 比率) 軸上の未測定内挿点で、H3/H4 は校正前提の交絡があるため
  次サイクルへ。選択時点で両条件の測定結果は非存在 (機械確認は実走前 freeze 手順で実行)
- push 可 (裁定 3、実施は人間)・層3 拡張の並行 (副次 4)・codex モデル運用 (副次 5、2066ce6) も承認
- 実装 (8b selector 実験 + 層3 拡張) は新セッションへ委譲 — 引き継ぎプロンプトを提示して交代

### 次の一手
1. 8b selector 実験の実装 (新セッション、codex 委譲主体): holdout freeze 手順 (§3.1 正規表現 +
   rr50 陽性対照) → descriptor 射影 + 検証 gate (§2.2 fails-closed 二段) → selector 役 (tool-less
   構造化出力、勝者名・実測値の遮断) → oracle 評価 driver (§5.1 二層分離)。正本 =
   `docs/phase3-8b-descriptor-design.md`
2. 層3 renderer の対象拡大 (sweep campaign 適用、機序仮説層の原料配線) を並行
3. push は人間の判断に委ねる (未 push: 前セッション分含め 02c840c..HEAD)

## 2026-07-16 (3) — 8b 前半 2 段 + 層3 v2 の実装 (codex 委譲 + 親統合)。後半 2 段は繰延

ユーザー裁定でスコープを縮小 (全 4 段 + 層3 は 1 セッションに重すぎる) し、8b-1/8b-2/層3 を
codex (gpt-5.6-sol ×4) に委譲、親が仕様起草・監査・統合・実適用を担った。計測なし。

- **8b-1 holdout freeze 手順 (289477c):** §3.1 三軸 conjunction 検索 + rr50 陽性対照 + 番人
  テスト。**実リポジトリ search は全条件 pass** (rr80/rr20 conjunction 0 件、陽性対照 35 件、
  15,184 files)。親統合 2 点 = verify の二層化 (per_axis_counts の再実行完全一致は無関係
  ファイル追加で偽陽性破綻する欠陥)、git 列挙の通常ファイル限定 (ccbench 入れ子 submodule
  gitlink / untracked symlink・入れ子 repo での誤発火)
- **設計未規定点の発見 → 要ユーザー承認:** 固定 6 構成は workload 間で実体が異なる (gate
  g_rl/g_rt、backoff 5/10/2µs、sort sp_dd/sk_ad、p2 flags)。holdout への束縛規則
  `nearest-read-ratio-v1` (rr80→read-heavy / rr20→write-heavy anchor、実測参照値は再帰除去)
  を実装裁定として freeze に明示記録する設計にした。**freeze 生成 (generate --confirmed-by)
  はこの裁定の承認後に人間確認者名を与えて実行する**
- **8b-2 descriptor 射影 + 二段検証 gate (98aadce):** schema 逐語凍結、canonical 整数文字列、
  禁止キー再帰走査 (キー限定 — enum 値 maximize_throughput_tps の偽陽性回避を明記)、
  positive control (measured_tps/winner 注入が両段で落ちる)。テスト 18 passed
- **層3 renderer v2 (da163d0) + 実レポート 6 本 (66e3193):** sweep 対応 (whiteboard_provenance)、
  floor 照合の実欠陥 2 種を実適用で発見し修正 — (a) records/threads のみの一意仮定が標準動作点
  1m/48 で不成立 (floor 無し JSON への発火 + 5 件重複) → workload 込み within/between 二種
  独立照合へ、(b) stage "abort" 未知拒否 → 正規化 + aborts view。trigger sweep 6 本へ生成
  (双射 pass)。screening payload 持ち (6f169f90) は対象外注記。機序仮説層の原料配線
  (agent_outputs.jsonl 案) は insight に設計凍結、実装は v3 繰延
- **自己一致の実検出:** codex B のテストが三軸静止リテラルを含み、holdout 検索に conjunction
  hit した → 実行時組み立てへ修正。「holdout 軸の JSON 形リテラルを repo に静止させない」は
  今後の実装でも維持する規律 (freeze の番人テスト + 実検索が防壁)
- **codex 運用の教訓 2 点:** (1) B が worklog へ越権追記 → 差し戻し。以後の仕様書に
  「worklog へ書くな」を明記する。(2) codex は CLAUDE.md に従い自分用 handoff を作り正常
  終了時に自削除した (良い挙動、放置時は親が回収)
- 検証: 対象テスト 55 passed (holdout 10 / descriptor 18 / layer3 27)、check_docs 違反なし、
  check_ai_provenance 71 件違反なし、ccbench clean (codex に pytest の対象限定を徹底)

### 次の一手
1. ユーザー承認 2 件: (a) variant_binding 規則 nearest-read-ratio-v1、(b) 承認後に
   `python3 orchestrator/campaign/s8b_holdout_freeze.py generate --confirmed-by <確認者> --confirmed-at <日付>`
2. 8b 後半の実装: selector 役 (tool-less 構造化出力、勝者名・実測値の構造遮断、入力 builder は
   descriptor_for_holdout + freeze variant_binding の whitelist 射影) → oracle 評価 driver
   (§5.1 二層分離、s1_direct_comparison の器を再利用、floor/budget null の間は bench 拒否)。
   oracle 実測は親が計測窓で直列
3. push は人間の判断に委ねる (未 push: 02c840c..HEAD)

## 2026-07-16 (4) — holdout freeze の生成 (ユーザー承認)

束縛規則 nearest-read-ratio-v1 をユーザーが承認 (選択肢提示の上で「承認して生成まで」)。
`generate --confirmed-by thawk105 --confirmed-at 2026-07-16` → verify pass (4d9610b)。
rr80 anchor=read-heavy / rr20 anchor=write-heavy、実測参照値は除去済み、floor/budget は
再実測後の再凍結で充填。あわせて「承認依頼は 何を/なぜ/選択肢/承認後 の 4 点を平易に書く」
をメモリ化した (「これわからんわ」の指摘から)。

### 次の一手
1. 8b 後半の実装: selector 役 (tool-less 構造化出力、freeze variant_binding の whitelist 射影)
   → oracle 評価 driver (§5.1 二層分離、floor/budget null の間は bench 拒否)。実測は親が直列
2. push は人間の判断に委ねる (未 push: 02c840c..HEAD)

## 2026-07-16 (5) — 8b 後半: selector 系 + oracle 評価 driver の実装 (codex 並列委譲 + 二波監査)

worklog (4) 次の一手 1 を実装。プランニングを gpt-5.6-sol(max) 相談 2 本 (selector 側 /
oracle driver 側) に並列で投げ、両裁定を採用。実装は codex(gpt-5.6-sol, high) を最大 3 並列で
回し、親は仕様起草・裁定・監査・統合・commit を担当。計測なし (floor/budget null の段階)。

- **6 commit (e247552..98e4133):** §9 再凍結 draft / selector 入出力 / selector 予測凍結+役
  +inventory 同期 / oracle manifest+budget / oracle report+judge / oracle driver+gate+pipeline
  bench_wall_s。テスト 8b 対象 178 passed + pipeline 回帰 100 passed、check_docs/
  check_codex_agents/check_ai_provenance いずれも違反なし
- **設計未規定点 → §9 再凍結 draft (承認待ち、8 項目):** off=stock_common 固定、selector は
  不透明 ID カタログのみ (raw variant_binding は既知 argmax 由来ゆえ全遮断)、swapped 追従は
  family ID 一致、予測はセル独立 1 回・fallback 禁止、予測凍結と oracle の分離、集約=median of
  medians、実走後 resume 拒否。**承認まで予測の実実行はしない**。selector-8b は static dormant
  で実体化 (Codex runtime は blocked 維持、13 static)
- **敵対監査 2 波 (codex read-only、real/refuted 選別):** 第 1 波 (A/C/D2 = 14 file) real 9 /
  refuted 5、第 2 波 (B/D1) real 4 / refuted 6。最重要 = report/judge の false-green 4 経路
  (expected binding 欠落で binding_ok=True / retry で correctness red が後続 commit に上書き
  = 規律2 直撃 / holdout 全落ちでも determinate / manifest hash 自己申告受理) と driver の
  null-restore が未承認 floor で gate を開く恒真化。全 13 件を F1/F2 で修正し番人テストを追加。
  監査全文は scratchpad 退避 (audit-wave1/2-out.md、insight 未凍結 — 次セッションで output/
  へ移すか判断)
- 素材: 「勝ち筋値を LLM に渡さず不透明 ID + 中立語彙で選ばせる」設計と「値でなく lineage が
  性能結果由来なら遮断する」判断は、workload-aware selection のリーク制御の一次事例
- codex 運用: 実装は編集面を互いに素な新規ファイルへ割り、WAL 語彙を仕様書の同一表で固定して
  独立ドリフトを防いだ。B の .codex/ 2 file は sandbox read-only で /tmp 退避 → 親が反映
- 計測機工数: codex 実装 5 + 監査 2 + 修正 2 + 相談 2 = 11 セッション (全 gpt-5.6-sol、
  相談 max / 実装・監査 high)

### 次の一手
1. **§9 再凍結 draft の 8 項目にユーザー承認**を得る (4 点形式で別途提示)。承認後にのみ
   selector 予測の実実行 (selector-8b を Claude role runtime で 6 セル) が可能になる
2. floor/budget の再実測 → holdout freeze v2 の再凍結 (数値充填 + strict v2 verifier 実装)。
   これが済むまで oracle driver の run 系は gate で拒否され続ける (設計どおり)
3. 監査全文 (scratchpad audit-wave1/2-out.md) を output/insights か output/ 監査 JSON へ凍結
4. push は人間の判断に委ねる (未 push: 02c840c..98e4133)

## 2026-07-16 (6) — Pegasus 利用 runbook の新設

ユーザー提供の Pegasus 操作情報と project 名 `SFC` を基に `docs/pegasus-runbook.md` を新設し、
docs 地図から索引した。利用可能キューは固定一覧でなく実行時の `qstat -Q` を正本とする。
Pegasus は当面デバッグ環境とし、正式計測へ採用するまでは既存 `linux-baremetal` の測定値へ
混ぜない境界を明記。ユーザーから追加確認した 2026 年度 node 仕様、1 job 1 node 占有、PBS
`-b` / OpenMPI directive、48-core hybrid 上限、quota、ストレージ、転送方法まで反映済み。

- 検証: `git diff --check`、`check_codex_agents.py` pass。`check_docs.py` は今回と無関係な既存の
  `docs/ccbench-anatomy.md` → 欠落 `docs/protocols_en.md` 参照 2 件で fail

### 次の一手
1. Pegasus を正式性能計測へ採用する場合のみ、専用 env-tag と再 calibration/noise floor を設計

## 2026-07-16 (7) — Pegasus runbook 実機検証 + 横断 docs のマシン非依存化

pegasus02 上で前エントリの runbook を実機検証。gen_S スモークジョブ (Request 866621.nqsv) が
投入 7 秒後に開始・完走し「投げて帰ってくる」を確認。qsub probe で gpu キューは SFC から
`EACCESSDEN`、debug は対話型で `qsub` 不可 (`EWRNGTYP`) を実測し、`cuda/12.3.2` 不在、`/scr` の
所在等と合わせて runbook を補正。一次資料 = /work/SFC/tanab/pegasus_smoke_20260716/ (ジョブ
出力 + evidence/、残ジョブなし)。

- ユーザー方針 (協議決着): 横断 docs に特定マシン (pegasus/cygnus) を焼き込まない。マシン固有の
  事実は各マシン専用 runbook のみに置き、CLAUDE.md・orchestrator-design・failures F3 への追記は
  共有計算環境一般の原則文とした。「主戦場がどこか」は可変状態なので文書へ再掲しない
- 監査: codex 敵対レビュー (レンズ 7)。REAL 5 = 単一観測の過度な一般化 — 全採用し実測範囲へ
  縮小。MINOR 1、REFUTED 6。Explore の波及調査は修正要 5 件 → 3 件採用・2 件持ち越し (下記)
- 工数: codex exec ×1 (reviewer)、Explore ×1。運用知見: codex の `--sandbox danger-full-access`
  起動は許可分類器に却下される — read-only / workspace-write で使う
- 持ち越し: roadmap §5 は旧計測機 (Dell R760) 前提のままだが、正式計測の正本は依然
  linux-baremetal のため現状は誤りでない — Pegasus を正式計測へ採用する時に roadmap-history
  手続きで改訂。phase3-s4b/s5/s8a runbook の実走前ゲート (pgrep 単独性確認) は共有環境非対応 —
  再利用時に「専有計算ノード確保」へ差し替え
- 追補 (協議決着 2): 原則文の側でも「専有ノードの確保」を常に可能と仮定しない (ユーザー指摘)。
  Pegasus 不可時に cygnus 等の共有ノード上で計測するしかない場合、load average 監視・外乱回避・
  外乱検知時の再計測の技法が第一線に戻る。F3 恒久対応・CLAUDE.md・orchestrator-design を
  この形へ再修正 (技法系を捨てない)

### 次の一手
1. Pegasus を正式性能計測へ採用する場合のみ、専用 env-tag と再 calibration/noise floor を設計
   (併せて roadmap §5 改訂 + 実走系 runbook のゲート差し替え)

## 2026-07-16 (8) — Pegasus 時代の全体調査: cygnus 前提除去・roadmap §5 協議改訂・トークン衛生

izanagi 全体を調査し、旧計測機 cygnus (Dell R760) の名指しと「ノード割当て = 専有の保証」の
絶対断定を除去した (65b535e, 3b887aa)。

- 協議決着: (a) スケジューラのノード割当てを専有の保証と見なさない (ユーザー指摘。gen_S は
  Exclusive submit=OFF / CPU 48/48 を `qstat -Qf` で実測。evidence は
  /work/SFC/tanab/pegasus_smoke_20260716/evidence/)。単独性確認は計測を走らせるノード上で行う。
  (b) roadmap §5 は協議改訂 (版凍結なし・版数不変)、設計判断は **D59** (正本 env-tag 据え置き /
  別環境の正式採用 4 条件 / マシン非依存方針)
- 置き場の裁定: Pegasus 対応 TODO は phase3.md に常設しない (D35 ブート規律 + 可変状態一元化)。
  README 2 種は委譲構造が正しく変更不要。phase3 チェックポイントは worklog (4)(5) の現在地に
  同期し、着手順に監査成果物凍結タスク (c) を補完
- 監査: codex 敵対レビュー第 2 回 (レンズ 7)。REAL 2 (handoff README の旧専有断定 / 着手順の
  凍結タスク脱落) + MINOR 2 (must 表の効力語復元、roadmap §3.6(5) の機種名) — 全採用。
  REFUTED 4 (Exclusive submit=OFF の解釈・協議改訂手続き・ノイズ修理・着手順整合は問題なし)
- 工数: Explore ×2 (トークン衛生監査 / 置き場調査)、codex exec ×1 (reviewer)。memory 2 本
  (専有前提の除去を追記、verify-single-tenant-before-measuring を再作成)
- 運用知見: guard hook は「保護パス言及 + $() 構文」の commit を fails-closed で拒否する —
  コミットメッセージに保護パスを含むときは `git commit -F <file>` を使う

### 次の一手
1. §9 再凍結 draft 8 項目のユーザー承認 → selector 予測の実実行 (phase3 チェックポイント (a))
2. floor/budget 再実測の env 選択は人間判断待ち: linux-baremetal で取るか、Pegasus 専用 env-tag
   を先に設計するか (D59 の境界)
3. Pegasus を正式計測へ採用する場合の env-tag/calibration/ゲート差し替えは変わらず (entry (7))
4. push は人間の判断に委ねる (未 push: 02c840c..HEAD)

## 2026-07-16 (9) — 8b 監査記録の凍結 (原文消失 → 再構成) + §9 承認前検証 + 所見修正

checkpoint (c) 着手時に、凍結対象の二波監査全文 (audit-wave1/2-out.md、scratchpad 退避分) の
消失を発見 (failures **F20**)。codex gpt-5.6-sol (max) の敵対相談 3 本 (凍結プラン / §9 提示前
検証 / 計画全体) で方針を検証し、実行は Claude workflow 2 本 (計 32 agents、検証・起草・修正・
第 3 波監査・反証) へ委譲、親が裁定・レビュー・統合した。計測なし。

- **凍結 (4bde427):** 再構成 = `output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md`
  (12/13 件を証拠階層 (worklog-detail / commit-attributed) つきで再構成、1 件は内容不明のまま
  残す。refuted 11 は件数のみ)。第 3 波監査 = `2026-07-16_s8b-third-wave-audit.md` (別 ID 系列
  A3-x)。相談逐語 = `2026-07-16_s8b-freeze-consultations.md`。リーク制御一次事例 =
  `2026-07-16_s8b-selector-leak-control-case.md`。phase3 は checkpoint (c) を「再構成 + 消失
  記録」へ改訂 + 段 6 完了化 (族 4 承認は worklog (2)) + 段 8 表記同期
- **§9 承認前検証 (相談 C2 → workflow 敵対検証で R1〜R6 全 REAL):** (R1) 現行 holdout_freeze は
  §9 追記による design hash 不一致で verify が失敗中 (状態の陳腐化、コードは fails-closed に
  動作)。(R3) 予測生成の実行規律 (fresh・各 1 回・再利用禁止) は宣言のみで trusted runner が
  不在。(R5) §6 に量化 4 点 (swapped 両/いずれか、floor 符号、同一 holdout 性、rationale 証拠
  基準) が未規定 + prediction と oracle を結合する judge 未実装。(R6) resume 拒否は
  --output-root 変更と truncated-only WAL で迂回可能。**§9 を承認しても実実行は解禁されない**
- **修正 (d96a9f0、s8b 系 150 passed + 独立敵対レビュー approve):** C2-R2 = 凍結検証が偽造 raw
  (非 JSON + status=valid 宣言) を受理する恒真化 → strict 再 parse 照合へ。C2-R4 = commit pin
  が形式検査のみ ("a"*40 がテスト正例) → git cat-file 実在検証へ。A3-1 = report が schedule 外
  index の trial window を黙殺し red が隠れる false-green (high) → 全数照合で protocol
  violation 化。A3-2 = excluded_reason 経路のテスト皆無 (F15 型) → 分岐実行をトレース確認済みの
  テスト追加
- 第 3 波監査 confirmed の残り 2 件は設計判断待ちとして凍結: A3-3 (複数 block manifest で
  budget 台帳が破綻 — 共有 path は 2 block 目焼失、別 path は総枠 block 数倍化) と A3-4 (全行
  binding-refused でも rc 0)。uncertain 2 件 (A3-5 verify-inconclusive 証拠束縛、A3-6 freeze
  再読込 TOCTOU) は v2 設計要件/強化候補として記録
- 工数: codex 相談 3 (max)、Claude workflow 30 + 2 agents。運用知見: 所見別の独立反証 2 票制
  (default-refuted) が 9 所見中 killed 2 / uncertain 2 を弾き、もっともらしい誤所見の採用を
  防いだ。pytest 不在環境のため fix agent が pip3 install --user pytest (9.1.1) を導入

### 次の一手
1. **§9 の 8 項目承認** (提示単位: bundle A={1,2,3} / B={4,5,6} は各一括、C={7}/{8} は個別。
   項 2 差し戻しは 1/3/6 を道連れにする依存あり)。承認後の実実行にはさらに前提条件: (i) freeze
   再凍結で design hash 追随 (R1)、(ii) trusted prediction runner 新設 (R3)、(iii) §6 量化
   4 点の再凍結 + 結合 judge 実装 (R5)、(iv) resume 拒否の強化 (R6)、(v) A3-3/A3-4 の設計裁定
2. floor/budget 再実測の env 選択は人間判断待ちのまま (linux-baremetal 継続 or Pegasus 専用
   env-tag 設計、D59 の 4 条件)
3. push は人間の判断に委ねる (未 push: 02c840c..HEAD)

### 追記 — セッション末のユーザー裁定と引き継ぎ (同セッション)

- **§9 裁定 (4 点形式で提示):** bundle A = 項 1〜3、bundle B = 項 4〜6 を**承認 (発効)**。正本は
  更新済み (§9 冒頭の承認状態 + phase3 checkpoint (a))。**項 7〜8 は「もっと詳しく説明して」で
  保留** — 次セッションは以下の要点で再提示して裁定を得る:
  - 項 7 (median of medians): 各 trial 内の bench rep 中央値 → 構成ごとに trial 中央値たちの
    中央値。二重中央値は共有環境の外乱スパイクに頑健 (平均は 1 スパイクで汚れる)。floor は §6 の
    on/off 予測構成差の判定にのみ使い、argmax の tie-break には使わない。exact tie は勝者なし =
    判定不能へ倒す (救済しない)。実装・テスト済み (report の rep 集約 + judge)。n/reps の欠測
    規則の数値は floor 再実測後の再凍結で充填
  - 項 8 (実走後 resume 拒否): 実走後は WAL に holdout 条件が現れ、freeze の「結果を見ていない」
    保証 (未既知性検索) が失効する。途中再開を許すと「一部結果を見た後の再実行」と区別できず
    cherry-pick 経路になるため安全側で拒否。driver の拒否は実発火を確認済み (単なる assert では
    ない)。既知の迂回 2 経路 (--output-root 変更 / campaign-start 1 行だけの truncated WAL) は
    R6 で実証済みで、強化 (lock+WAL 存在判定 + output-root 非依存の実走済みマーカー) は前提条件
    (iv)。代償: クラッシュした block は再開不能 → 複数 block 運用の破綻 (A3-3) と合わせて実行
    トポロジーを設計裁定してから数値再凍結に進むのが正
- **floor env のユーザー回答:** 「正式採用というか、普通に pegasus も cygnus も使う。今はこれは
  pegasus で動いている」— 二者択一でなく併用が前提。含意: 計測の正本性は D59 のとおり env-tag
  単位のまま変わらない。floor/budget を Pegasus で取るなら専用 env-tag + calibration + noise
  floor が前提条件、cygnus (linux-baremetal) なら既存 tag で再実測可。次セッションで「どの
  env-tag の floor を v2 に充填するか」を工数比較つきの具体案で再提示する
- **再開手順 (次セッション):** (1) 項 7〜8 の裁定を得る → §9 全発効、(2) floor 実測 env の確定、
  (3) A3-3/A3-4 (+ A3-6 の単一 object 要件) を含む実行トポロジーと freeze v2 schema の設計 →
  承認 → strict v2 verifier 実装、(4) trusted prediction runner (R3) と resume 強化 (R6) の
  実装、(5) freeze 再凍結 (R1 の design hash 追随 + 数値充填)。ここまで済んで初めて selector
  予測 6 セルの実実行に到達する。本セッションの一次資料はすべて repo 内
  (output/insights/2026-07-16_s8b-*.md 4 本 + 本エントリ) — scratchpad に唯一コピーは残して
  いない (F20 恒久対応を実践)

## 2026-07-16 (10) — 8b 裁定準備: 裁定パッケージ + freeze v2 設計素材の凍結 (相談 4 + workflow 16)

再開手順 (1)〜(3) の裁定に必要な資料を作成した。計測なし・実装コードなし。codex gpt-5.6-sol
(max) の敵対相談 4 本 (C-A = 項 7/8 提示、C-B = floor env、C-C = 設計骨子、C-D = プラン全体) を
並列実行して全所見を親裁定し、Claude workflow 16 agents (起草 2・所見別検証 8・修正 2・再検査 2・
横断整合 2) で起草・修正、親が全文レビューして最終修正 3 件を直接適用した。

- 成果物 (insights 3 本): 相談逐語 + 親裁定 = `2026-07-16_s8b-ruling-prep-consultations.md`、
  裁定パッケージ (6 裁定単位) = `2026-07-16_s8b-ruling-package.md`、freeze v2 設計素材
  (T/C/S/R3/R6/R5 層 + 受入ベクトル 9 本) = `2026-07-16_s8b-freeze-v2-design-material.md`
- 最重要所見: (1) C-C 2 = R6 マーカーと crash 再走は両立不能 → 択 (a) 再走なし / 択 (b) 項 8
  改訂 + attempt registry の中心裁定へ昇格。(2) C-A 3 = median→mean 変異で現行テストが PASS する
  false-green (親が in-process 再現)。(3) C-B 6 = 競合検知 pgrep が s8b-build-cache 配下の孤児
  bench を見逃す F3 潜在ギャップ。R3 は exactly-once → at-most-once へ契約修正 (C-C 7)
- 検査: s8b 系 150 passed (worktree)。R1 再現 = freeze verify rc=1 (design hash 不一致の
  fails-closed 正常動作)。resume 拒否 (driver:359) の回帰テスト不在を確認 (裁定 2 に明記)
- ユーザー指示 (恒久): subagent へのモデル明示割当て — fable 継承をやめ、レビュー = opus /
  起草・機械検査 = sonnet。memory (subagent-model-economy) へ保存済み
- 作業は worktree branch worktree-s8b-ruling-prep (基準 50b499b)。push はユーザー判断

### 次の一手
1. 裁定パッケージの 6 裁定 (§9 項 7 / 項 8 + crash 再走ポリシー / A3-3 トポロジー / A3-4
   status・rc / R5 truth table / floor env) をユーザーから取得 → §9 承認状態と worklog へ記録
2. 裁定後: strict v2 verifier / R3 runner / R6 強化 / F3 pgrep 修正の実装 (設計素材の受入
   ベクトル V1〜V9 に従う)
3. worktree branch の main への取り込みと push はユーザー判断

## 2026-07-16 (11) — 裁定パッケージのユーザー裁定: 1〜5 承認、6 は択 C + Pegasus 継続

ユーザー裁定 (「ほとんど承認、6 だけコメント: 今はしばらく pegasus で作業します」) を記録:

- **裁定 1 (§9 項 7 median of medians) 承認・発効。** 回帰テスト整備 (V9) と rep 採否規則は
  freeze v2 側 TODO として登録済み
- **裁定 2 (§9 項 8) 承認・発効、択 (a) = crash 後の再走なし** (推奨解釈で記録。crash は実験全体
  判定不能、再走導入は択 (b) attempt registry の §8 再凍結が条件)
- **裁定 3 (A3-3: 単一 block + 累積台帳 + 事前一括 reservation)・裁定 4 (A3-4: completed 強化 +
  rc 優先順位)・裁定 5 (R5 truth table 5 項目 = 両 holdout / 方向付き floor / 同一 holdout 束縛 /
  fail-closed 伝播 / rationale 診断限定) の推奨案を承認。** 再凍結本文は freeze v2 で凍結
- **裁定 6: 択 C (env-neutral 共通実装の先行) を採用。** v2 数値を束縛する唯一の env-tag は
  floor 実測開始時に確定 (ユーザーは当面 Pegasus で作業 → cygnus 実測の実行者・時刻は未定の
  まま、Pegasus レーンの整備は必要になった時点で D59 4 条件に従う)
- 正本反映: §9 承認状態 + phase3 checkpoint (a) 完了化

### 次の一手
1. 前提条件の実装 (設計素材 + V1〜V9 に従う): F3 pgrep 修正 / C 層 status・rc / T 層 単一 block +
   reservation 台帳 / R6 lock・マーカー・truncated 閉鎖 (択 a) / S 層 load_verified_freeze +
   世代 schema / R3 runner (at-most-once) / R5 結合 judge (truth table は裁定 5 の値で確定)
2. floor protocol の凍結案作成 → 承認 → env-tag 確定 → floor/budget 実測 → freeze v2 再凍結 (R1)
3. worktree branch の main への取り込みと push はユーザー判断

## 2026-07-16 (12) — freeze v2 前提条件の実装 wave 1 (5 レーン workflow + 親レビュー)

裁定 1〜6 発効を受け、設計素材の T/C/S/R3/R6/R5 層 + F3 修正を Claude workflow 16 agents
(5 レーン: driver 系直列 4 段 + F3/R3/R5/S-freeze 並列、実装 = opus/sonnet、レーン内敵対
レビューつき) で実装した。fable subagent 不使用 (モデル経済指示の実践)。計測なし。

- 新規: s8b_run_marker.py (freeze byte hash マーカー + O_EXCL lock)、s8b_prediction_runner.py
  (R3 at-most-once + journal 束縛)、s8b_verdict.py (R5 結合 judge、truth table = 裁定 5 の値)。
  改修: 予算台帳の事前一括 reservation (crash 非解放・3 値分離)、manifest 単一 block 強制、
  completed 強化 + rc 優先順位、load_verified_freeze 単一 object 貫通、pgrep path 非依存化、
  git blob 束縛骨格 + 未承認世代の一律拒否。テスト 150 → 222 passed (受入ベクトル V1〜V9)
- workflow 事故 1 件: レーン A 段 4 が構造化出力の再試行上限で異常終了 → 実装は完了していたが
  レビュー段が飛んだため、親が opus 子でレビューを再投げ。所見 6 件 (fix-required 1) —
  medium 1 = --marker-root CLI が --budget 撤去と同型の経路上書き迂回を再導入 → CLI 面から
  撤去 (親)。low 2 件 (entries 永続 assert・reservation 合計 cross-check) は sonnet 子で強化。
  low 3 件は記録のみ (レーン同居・dead code 化した重複検査・v1 拒否経路の再読込)
- レーン内レビューの主な捕捉: R3 の claim が payload を束縛しない F14 型 (freeze 付け替えで
  provenance 汚染、修正済み)、S 層 git blob 救済の fail-open (修正済み)、R5 の swapped 両
  holdout 判定が基数を検査しない穴 (修正済み)
- 工数: workflow 16 + 単発子 3 (レビュー opus、修正 sonnet、Explore sonnet は (10) 計上済み)

### 次の一手
1. wave 2: floor protocol の凍結案 (対象集合・n・reps・時間分離・算出式) を作成 → ユーザー承認
   → env-tag 確定 (裁定 6 で保留) → floor/budget 実測 → freeze v2 再凍結 (R1 design hash 追随、
   世代 field 列挙と承認束縛方式の §8 裁定を含む)
2. strict v2 verifier 本体は wave 2 の再凍結と同時に実装 (骨格は今回済み)
3. worktree branch (worktree-s8b-ruling-prep) の main への取り込みと push はユーザー判断
