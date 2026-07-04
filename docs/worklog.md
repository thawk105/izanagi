# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。**何をやって・何が分かって・次に何をするか。**
git 履歴より粗く、roadmap / decisions より具体的な「作業の物語」。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

**ローテーション:** Phase 境界で過去分を `docs/archive/worklog-<範囲>.md` (Phase 1〜2 分 =
`docs/archive/worklog-phase1-2.md`) へ**移動**し、現行ファイルを軽く保つ (ブート時に読むのは
末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。アーカイブは凍結 (訂正注記のみ追記可)。

---

## 2026-07-02 — Phase 3 着手前 引き継ぎ監査 (workflow 再監査) を audit バックログに反映

新セッションでの再開に備え、リポジトリ全体を独立 workflow (8観点 × 21 エージェント、各 finding を敵対検証) で
再監査した (roadmap §3.7 / D27 の引き継ぎ監査を発火 = Phase 境界トリガ)。**結論は 6/30 audit と一致: 致命バグ・
false-green・規律1-3 破りゼロ。** 11 精査 → 10 REAL / 1 refuted、全件が `docs/audit-2026-06-30.md` に既出 or 追記で
カバー。10 件は「doc 鮮度・over-claim」と「歴史的 campaign の材料レポート射影器が沈黙して空を返す C1 drift」で、
計測データ・正しさ判定には波及しない。

`docs/audit-2026-06-30.md` に反映 (新規ファイルは作らず living なバックログを差分更新、規律5):
- 冒頭に「2026-07-02 再監査」差分サマリ (結論・優先順・未検証領域の完全性クリティック)。
- §2 の C1 drift 項目に `critic/digest.py:215`(`load_p2_2_digests`)を 3 本目として追記、`worklog.md:596`「digest.py で
  3 workload 出力」が現状偽 (空を返す) を明記、severity [LOW→MED]、6/30 の「exit 1」を 7/2 実測 exit 0 に訂正。
- §5 に新規3件: `CLAUDE.md:19` 現在地 stale [MED]・`roadmap.md:231` §6 submodule 運用 D16 未追従・`guided.py:12`
  docstring D26 未追従 (consumer 取り残し)。既存の §5/§8 項目 (roadmap §8・decisions:256・phase2:54・ロスター) も 7/2 REAL 再確認。

**未検証で残した領域 (次の監査候補、完全性クリティック):** 規律1 の `#ifdef TRACE` 別ビルド分離の実挙動、verifier
DSG/G2 検出の偽陰性、hooks 発火 (H3 未実体化)、Phase 3 EVOLVE-BLOCK/source_digest のコード裏取り、
fitness/admission/median の数値正当性。submodule gitlink pin (dff0f1e) と patch 完全一致は前タスクで確認済み。

### 次の一手 (新セッション開始点)
1. **`CLAUDE.md:19` 現在地の更新** (audit §5 🔁 [MED]): Phase 3 kickoff タスク1/2 (source_digest/EVOLVE-BLOCK,
   D22-D27) 完了を反映し C1 を「消化すべき残 must」から外す。次セッションの誤誘導を断つ最優先。**憲法側ゆえ人間確認。**
2. **Phase 3 タスク3 (H3 hooks)** に着手 (本来の blocking 順)。
3. C1 drift 恒久対応 (phase2.md:154-159 選択肢a): report/critic 3 本を `replay.discover_p2_2_dir` 方式に統一。

## 2026-07-02 (続き) — 「現状の洗練」検査: audit 台帳の全項目裏取り + 未検証領域の新規検査

ユーザー指示「進捗とコードを検査して改善 (前進でなく洗練)」を受け、ultracode workflow (~80 エージェント) で
(a) audit バックログ全項目の実態突合 (8 グループ)、(b) 7/2 再監査が「未検証」と残した領域の新規検査 (6 観点:
規律1 TRACE 分離実挙動 / verifier DSG 偽陰性 / source_digest・EVOLVE-BLOCK 裏取り / fitness・統計の数値正当性 /
直近修正コミット群のレビュー / 簡素化・重複)、(c) 新規 finding の敵対検証 (誤検出疑い + 再現性の 2 名投票) を実施。

**backlog 裏取りの結論**: 台帳が実態より古かった — §1 HIGH loop src_token (19e0915)・§1 MED 回帰テスト (同)・
§2 MED rep 失敗 (1e2c01c)・§2 LOW genesis_commits (835ed9b)・§5 root README・§5 phase3 タスク1 は修正済みなのに
`[ ]` のままだった → 台帳を [x] 化 (本コミット)。残りは未対応で自律修正可 ~28 件 / 人間判断 3 件
(§6 submodule dirty の checkout・§2 backoff-if 骨格 #if=D22 人間専管 (6/30 判断を維持)・CLAUDE.md:154 の 7x7 旧表現)。

**新規 finding 36 件 (敵対検証で大半 REAL、UnicodeDecodeError 素通りの実害主張 1 件は棄却)。主要どころ:**
- [HIGH] verifier 偽陰性 (実証済み): trace 形式に完全性情報 (R/W 件数・終端マーカー) が無く、(a) txid 欠番 =
  trx 丸ごと欠落も (b) trx 尾部欠落 = C 行だけ残り R/W 消失も integrity に乗らず certified serializable になる —
  `verifier/parse.py`。部分 trace への防壁ゼロ。
- [HIGH] source_digest の盲領域: 対象ファイル内 `#ifdef GLOBAL_VALUE_DEFINE` ブロックが digest 前処理で
  剥がされ、挙動変更が同 digest = 偽 stock / 偽 cache hit — `campaign/source_digest.py:90`
- [HIGH/MED] D25 retryable の破れ: retryable 判定が `st.last` 依存のため、identity-error → 修復 → 再評価が
  in-flight クラッシュすると permanent skip が復活 (2 finder が独立指摘、実 run_campaign 3-run 再現済み) — `loop.py:60`
- [MED] calibrator CLI `--binary` に trace シンボル検査が無い (buildcache 経路のみ防壁あり) + buildcache の
  nm 不在/失敗が silent pass — 規律1 の防壁が経路依存
- [MED] pipeline: CV 算出不能 (nf.cv=None) が BENCH_DONE 後の log f-string で TypeError → 意図しない
  eval-exception abort + permanent skip — `pipeline.py:258`
- [MED] S4 consumer: `load_rejections` の Rejection が variant id / src_token を落とし、同 canonical 別コードの
  RED variant が planner 視点で alias する — `critic/digest.py:151`
- [MED] prob_superiority の離散 tie 校正: 同一分布でも p_lt≈0.41 (<0.5) となり、P2-5 の「誘導は勝たない」を
  実態より強く見せる方向のバイアス — `search_baselines.py:169`。P2-5 結論への波及は要精査
- [MED] 1e2c01c の rep 失敗 notes が calibration JSON/MD に出ずインメモリ止まり (「沈黙させない」が半分)
- [LOW 群] W 行 (epoch,tid) 無照合 / key 形式無検証 / genesis 番兵未満の版無検査 / between_run_floor None ガード /
  Gate1 の差分散 √2 補正漏れ / cache_key に cc・cxx 不含 / loop silent skip の WAL 痕跡ゼロ 等
- [簡素化] WAL リーダ 4 重実装・canonical パーサ 3 重・dead import 8 件・env_scope_dir 未使用・分位計算 2 実装・
  sys.path 汚染書法不一致 等 (大物の統合は規律5 と凍結スクリプト尊重で見送り、台帳追記に留める)

**修正計画 (コミット単位、上から順に実施。本エントリはセッション引き継ぎ用スナップショット):**
1. docs 鮮度一括 (roadmap §6 D16 相互参照 / §8 7x7→10 プロトコル / phase2:54 テスト数 / decisions:256 patch 名 /
   agent-arch critic-experiment 注記 / patches README broken-silo 手順)
2. コード内 docstring 鮮度 (guided.py D26 追従 / genome.py 行参照→シンボル / calibrator cli.py 出力名 /
   buildcache 補記 / fixtures README 凡例 / orchestrator README 実構成化)
3. agent spec 整合 (python→python3 ×4 / critic.md digest 引数 / 書き込み隔離文言の honest 化 §4 段1)
4. テスト品質 (_skip ヘルパで return 疑似スキップ可視化 / test_critic・test_guided の except Exception 枝 / tests/README)
5. calibrator 小修正 (clocks_per_us fallback を result に記録 / max_records 16m 統一)
6. verifier 硬化: 部分 trace の偽陰性を integrity で塞ぐ (txid 欠番 / W 行版照合 / key 正規化 / genesis 番兵) + テスト
7. campaign 硬化 (D25 retryable を last 履歴でなく reason 履歴で判定 / CV=None ガード / Rejection に id 追加 /
   records assert→例外 / cli --binary trace 検査 / nm fails-closed 化)
8. C1 drift: discover_p2_2_dir 方式を p2_2_report / backoff_sweep_report / critic digest の 3 本に統一 +
   p2_2 RECORDS/THREADS の calibration JSON 照合
9. rep 失敗 notes の永続化 (calibrator report の _point_to_dict に notes)
10. 統計系 (prob_superiority tie / Gate1 √2) — 数値結論に触るため修正内容を精査してから
11. simplify 低リスク分 (dead import 削除・env_scope_dir 整理)
12. CLAUDE.md 現在地更新 (独立コミット・報告で明示。絶対規律セクションは不触)
13. 台帳・worklog 最終同期 + テスト全緑確認 (ベースライン 134 passed 取得済み)

**人間判断待ち (実施しない):** submodule dirty の checkout (destructive、計測時の patch 再適用運用と絡む) /
backoff-if `#if defined()` ガード (D22 人間専管 + inert digest 再固定要、6/30 判断を維持) / CLAUDE.md:154 7x7 表現。

## 2026-07-02 (続き2) — 洗練セッション完了: 15 コミットで backlog + 新規 finding を消化

冒頭エントリ (「現状の洗練」検査) の修正計画を完遂した。テストは 134 → **143 全緑** (+9)、
bare runner 5 本 OK。コミット系列 (54aa6ec 引き継ぎ〜):

1. **docs/spec 鮮度** (d16f7dc, 8e06a37, a1661d2): roadmap §6/§8・phase2・decisions・agent-arch・
   patches README・guided/genome/cli/buildcache docstring・orchestrator README 実構成化・
   agent spec python3 + 書き込み隔離宣言の honest 化 (§4 段1)。
2. **テスト品質** (d96264f): skiputil で return 疑似スキップを両 runner とも SKIP 可視化、
   except Exception 枝、tests/README 新設。
3. **calibrator** (4d1f25f): clocks_per_us フォールバックの成果物記録 + max_records 16m 統一。
4. **verifier 硬化** (36a1193): 部分 trace / 整合破れの偽陰性 4 種を integrity で遮断 —
   [HIGH] txid 欠番 (trx 丸ごと欠落が certified になる実証済み偽陰性)・W 行版照合・key 形式・
   genesis 番兵未満 + UnicodeDecodeError の ParseError 化。手製フィクスチャ p1 の txid を実仕様
   (0 始まり) に追従。実 Silo 184k txn で誤発火なし。
5. **campaign 硬化** (02b08eb, 9cde781, ec5aaaf, a649fe7): [HIGH] D25 retryable の破れ
   (last→last_terminal 基準化、in-flight クラッシュで permanent skip が復活する穴)・identity skip
   可視化・CV=None admission・records assert→例外・TRACE 予約名 reject・規律1 防壁 fails-closed 化
   (calibrator CLI 入口 nm 検査新設 / buildcache nm silent pass 廃止)・cache_key に cc/cxx・
   S4 Rejection にコード軸 id (variant/src_token)・backoff_repro の resume 耐性。
6. **C1 drift 恒久対応** (065593a): discover_campaign_dir 統一で report/critic 3 本が歴史的
   campaign を再出力 (+38.3%/+11.3% の根拠 sweet spot 復活、再生成物は既存とバイト一致 =
   決定的再現の証明)。p2_2 に calibration 実行時照合。
7. **統計/可視性** (cf62e81): rep 失敗 notes の永続化 (JSON + WAL)・確率優越 a (tie 半加算) 追加・
   Gate1 √2 の統計的意味を docstring 化・between_run_floor None ガード。
8. **simplify** (f8f423a): dead import 6 件・repro_command 誤記 (reps=3→5) + .dat 再生成・
   env_scope_dir 集約。大物統合 (WAL リーダ 4 重等) は規律5 で見送り、台帳に方針記録。
9. **CLAUDE.md 現在地** (608a72b、独立コミット・人間レビュー用) + **D28** (warmup 意図的非対応,
   39a607e) + 台帳・worklog 同期 (本コミット)。

**人間判断待ち (実施していない):** (1) submodule dirty の checkout 戻し (destructive)、
(2) backoff-if `#if defined()` ガード (D22 人間専管 + inert digest 再固定)、(3) patches フォーマット
統一 (broken-silo 再生成 = 規律2 positive control の byte 一致検証を伴う)、(4) **P2-5 の主指標を
p_lt→a に置換 + p2-5-summary 再生成 + D21 結論文の再解釈** — p_lt の 0.5 基準は同分布でも 0.4375 と
出る系統バイアスで negative result を強める方向だった。a への置換で「誘導は有意に上回らず」の一部
(balanced) が変わる可能性があり、主張に触るため人間の指示で行う。

**持ち越し (台帳「2026-07-02 洗練検査」§参照):** trx 尾部欠落 (trace 形式拡張 = S1 と同時)、
build-error retryable 非対称 (Phase 3 abort payload 設計と同時)、digest への unstable 伝搬、
Gate1 √2 の閾値意味論 (Phase 3 設計判断)。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks 実体化)** — §1 残り 2 項目 (allowlist untracked / hooks) を同梱。

## 2026-07-02 (続き3) — 人間判断待ち 4 件をユーザー承認のもと消化 (P2-5 再校正 D29 / backoff #error / patches 統一 / submodule clean)

ユーザー「その4件は対応した方が良さそうだよね?」の承認を受け、洗練セッションで人間判断待ちと
した 4 件を全て対応した。

1. **P2-5 指標再校正 (D29、39c44cc)** — 最重要。p_lt の系統バイアス (同分布 null=0.4375) を
   確率優越 a に置換。**敵対検証が機能した**: 当初解釈「balanced では誘導も random より有意に速い
   (t p=0.016)」を独立統計検証が exact 検定 (p=0.144)・Holm 補正・分散縮小 (大外れ回避) の指摘で
   棄却。確定した再解釈 =「貪欲は balanced で有意に速い (a=0.533, exact p≈0.005、旧『ゼロしか
   取れない』を撤回)。誘導は貪欲を超えず (A=0.581 有意差なし)、deceptive では貪欲より有意に有害
   (A=0.230, permutation p<10⁻⁴、打ち切り感度に頑健。機序 = 自信ある早期停止の負債)」。
   *(訂正 2026-07-03: 「p<10⁻⁴」は方式未記録の過大表示 — 厳密 permutation で p=2.52×10⁻⁴。
   Holm ×6 でも有意で結論不変。summary.json `correction_2026_07_03` / D29 末尾の訂正注記参照)*
   **D21 総合結論は不変・むしろ強化** (支柱が vs random から vs 貪欲 ablation へ移動)。
   成果物: p2-5-summary.json に recalibration 追記 (既存キー不変・再実行で消えないマージ保持) /
   insight 追記 / p2_5・search_baselines の a 主指標化 + null 校正テスト / D21 へのポインタ /
   phase2・README・CLAUDE.md の文言更新 / 本 worklog 過去 2 エントリに撤回・再校正の注記。
2. **backoff.hh 骨格に #ifndef+#error (4f7bb3c)** — audit 案の defined() ガードは実測で「gcc が
   短絡し -Werror=undef が発火しない = source_digest の fails-closed が黙って stock 縮退に弱まる」
   トレードオフが判明、より強い #error (全経路コンパイル停止) を採用。inert digest 7664020a /
   variant digest とも byte 一致を実測 (audit が懸念した baseline 再固定は不要)。round-trip 検証済み。
3. **patches フォーマット統一 (92e1cd8)** — broken-silo を git diff 形式に再生成。clean checkout に
   新旧 patch を適用した transaction.cc の byte 一致で規律2 positive control の不変を証明。
4. **submodule clean 戻し (d6bc750 で test 追従)** — dirty が silo-backoff-fixed.patch と完全一致
   (逆適用成功) を確認して checkout。gitlink dff0f1e 不変。patch 適用前提のテスト 3 本は skip として
   可視化される (140 passed + 3 skipped)。次回計測/Phase 3 ビルド時は patch を再適用する。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks 実体化)**。

## 2026-07-03 — セッション運用ルールの明文化 (roadmap §3.8 新設 + CLAUDE.md 手順5、D31)

ユーザー問題提起「仕事を投げて一定時間経つとコンテキストが膨れ上がって質が低下する」を受け、
D27 が明示的に残した穴 (「同一セッション内の緩やかな劣化は前向き層に委ねる → 本質的に未解決」) を
運用ルールとして埋めた。協議合意の改訂ゆえ版数据え置き (版管理セレモニー不要)。

- **roadmap §3.8 新設 (§3.7 遡及層と対をなす前向き層)**: 劣化メカニズム 3 つを名指し
  (ロッシーな自動圧縮 / 自己一貫性バイアス = P2-5「自信ある早期停止の負債」と同型 / 読んだつもり
  ドリフト)。対策 4 ルール = 粘らず捨てる (自動圧縮が入ったら新サブタスクを始めず handoff を書いて
  セッションを終える) / handoff 自己完結基準 (fresh セッションが handoff + 現在地 + worklog 末尾
  だけで再開できる品質) / コンテキスト衛生 (生 trace・生ログ・WAL 全文を main context に入れず
  サブエージェント・digest 経由) / 圧縮跨ぎ再読。加えて **Phase 3 ループ主導権の原則**: 反復ループは
  orchestrator (Python) が回し LLM は iteration 単位で fresh に呼ぶ (品質がセッション寿命に依存しない。
  orchestrator-design.md 既存原則の適用)。設計原理 =「セッションの延命でなく、短命でも仕事が
  途切れない構造」。新機構は足さない (規律5)。§3.7 末尾の委譲文に §3.8 を配線。
- **CLAUDE.md 作業の進め方に項目 5** (短い配線のみ、詳細は §3.8 へ委譲 — D27 と同じパターン)。
- **decisions.md D31** (D30 は H3 hooks の別セッションが予約済みのため番号を跨いで追記)。
  却下した代替 = hook による機械的強制 (コンテキスト残量は hook から観測不能・proxy は誤発火、
  規律5)、対策不要 (圧縮はロッシー)。残るトレードオフ = 自己申告ベースの自己言及 (劣化した Claude
  自身が気づく必要)。下支えは既存の機械ゲート (規律2) + §3.7 遡及監査。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks) の未コミット成果物の取り込み** — 別セッション進行中 (guard_write /
  guard_bash / settings.json / D30 記入待ち)。以後の残り blocking は観測者効果二重検査 → coder.md 全配線 1 周。

## 2026-07-03 — docs 全体の敵対検査 + H3 hooks の over-claim 撤回 + 方針 A 確定 (D30)

ユーザー指示「docs を検査し方向性・設計が優れているか検討して改善」を受け、docs 11 ファイルを 7 視点で
並列敵対検査 (Workflow) + 独立裏取り。**最重要検出 = H3 hooks の over-claim** (5 ファインダーが独立に検出)。

**規律6 の独立裏取りで確定した over-claim (git 履歴には未固定 = working tree のみ):** 前 2 セッション
(**2026-07-02 = hooks 実装 + 1 巡目敵対検証 15 finding / 2026-07-03 = 2 巡目敵対検証**、いずれも worklog 未記録
だったのを本エントリで補足。記録は insight `2026-07-02_...adversarial-review.md` / `2026-07-03_...round2-handoff.md`)
が phase3.md を「H3 hooks 完了・2 巡で硬化」・hooks/README を「配線済み」とマークしたが、実態は
(1) `.claude/settings.json = {}` で**未配線 = 第二防壁ゼロ**、(2) 2 巡目で **real 13 件 (critical 1 = コメント行連結で
コメント除去器を騙し `#define TRACE`/`__DATE__` を素通しさせる GW2R-1)**、(3) 参照先 **D30 が decisions.md に不在**
(宙吊り)、(4) 配線検査テスト `test_settings_json_wires_both_hooks` が赤 (実機確認: 18 passed / 1 skipped / 1 failed)。

**方針確定 = A (ユーザー承認):** 2 巡目 real の質が「テキスト検査で C++ 翻訳フェーズ・shell の完全性を負うのは
原理的に無理」を実証。→ hook を最小第二防壁に軽量化し、identity の honest さは source_digest の preprocess 後ハッシュ、
観測者効果の分離は観測者効果二重検査へ委譲 (「payload 検査が唯一の防壁」の単一障害点を放棄)。B (hook 強化続行 =
軍拡競争・規律5 と衝突) / C (記録のみ) を却下。

**docs 整合 (協議合意ゆえ版管理セレモニー不要):**
- **over-claim 撤回** — phase3.md タスク3 を `[ ]` (進行中・方針 A で再設計) に、must 分類表を「進行中」に、
  hooks/README.md を「実装済・未配線」に訂正。
- **D30 記入** (方針 A の設計判断、却下 B/C 込み)。D24 末尾に部分 supersede ポインタ、D31 冒頭の予約注記を実態化。
- **roadmap 反映** — §3.4-3 (hook = 最小第二防壁、identity/観測者効果は一次防壁)、§3.3 (ビルド等価性の「採用済み」
  stale を実態=symbol 不在 + Phase 3 で preprocess 二重検査に修正)、§2/§3.5 (P2-5 negative result の未反映 stale を
  「誘導は貪欲を超えず deceptive で有害・価値は空間外合成」に更新)。
- **Phase 3 主実験の評価設計を新設** (最大の設計欠落) — 完了定義が kickoff 配線実証しか無かったので、反証可能な主張・
  headline ベースライン集合 (silo stock / クロスプロトコル stock / ランダム変異 / 機械 sweep)・LLM 価値の ablation・
  統計計画 (確率優越 a + between-run floor)・失敗条件を phase3.md 冒頭に事前登録。backoff +38%/+11% が silo 内比較に
  閉じている弱点への対策も配線。
- **残存リスク追記** — S2 空振り認証 (abort≈0 で合成枝が verify 未実行のまま緑)、coder リーク制御未設計 (BACKOFF_FIXED
  勝ち筋がリポジトリ内既知)、観測者効果二重検査の述語が #ifdef TRACE 内側の挙動差を素通しする点、ハーネス自己保護の
  欠落 (orchestrator/hooks 自身が防護対象外)。agent-architecture.md coder 節に kickoff 制約の前進ポインタ。

**用語集 `docs/glossary.md` を新設 (ユーザー指示):** docs が説明なしに使う非自明用語を、専門外の査読者・将来の自分
向けに平易に定義。5 領域 (探索最適化 / 並行性制御DB / 評価測定統計 / 合成機構 / エージェント運用) を並列ファインダーで
横断収集 (142 用語→重複統合 118→執筆時に近接統合) し、私が一貫文体で 5 分類に整理。各項目は「教科書レベルの定義 +
izanagi での使われ方 + 参照先」の 2 段。roadmap 冒頭に発見ポインタを配線。動機 = ユーザーが「貪欲ベースライン・
オラクル天井・deceptive 構造」の意味を尋ね、docs には数値・結論はあるが用語の一般定義が無い (専門家前提で圧縮) と
判明したこと。定義は執筆時点のもので正典は各 docs 本文。

**コミットはしていない (ユーザー未指示)。** working tree に docs 変更 + 用語集 + 前セッションの hooks 実装/テストが
未コミットで併存。テストの唯一の赤 = `test_settings_json_wires_both_hooks` は未配線という実態と整合 (方針 A の配線 step で緑化)。

### 次の一手
- **本 docs 変更 + hooks 実装のコミット** (論理単位ごと、ユーザー承認後)。撤回は済んだので over-claim を履歴に入れない。
- 方針 A の実装順: (1) 一次防壁 (source_digest preprocess ハッシュ + 観測者効果二重検査) を先に load-bearing に →
  (2) hook を最小化 + false-positive 4 件除去 → (3) settings.json 配線 (matcher = `Write|Edit|MultiEdit|NotebookEdit` / `Bash`)。
- 未消化の docs 課題 (本セッションで flag のみ): C1 campaign-id drift の状態が 4 文書で食い違う / 「WAL proof chain」の
  実体定義が無い / 外的妥当性 (Threats to Validity) の集約が無い / coder 自律期の停止条件・fitness 採否・再試行方針が未予約。

## 2026-07-03 — Phase 2 完了監査 (実態突合) + 検出事項の修正

ユーザー指示「docs を調査し phase2 までの仕事がちゃんとできているか検査」。同日の docs 敵対検査
(前エントリ、設計・方向性が対象) と軸を変え、**完了主張 vs 実態 (成果物・数値の一次データ・規律遵守)
の突合**として実施。7 視点 (P2-0/1・P2-2・P2-3/4・P2-5・規律1/2・規律3/4/6・docs 整合) の並列
ファインダー → 重複統合 → 敵対検証 (severity 高は 3 票制) の 23 エージェント構成 (新規計測ゼロ・
読み取りのみ)。

**総合判定: Phase 2 までの仕事は実態が伴い健全。完了主張の虚偽・絶対規律違反は 0 件 (critical/high 0)。**
裏取り済み 78 件の主要な柱: P2-2 の 24 評価 WAL から最速構成を独立再計算で一致 / backoff headline
+38.33%/+11.27% と cross-run 再現を WAL 生データから復元 / P2-5 の全統計量 (A・a・null・誤収束 8/12・
exact p 2 件) を独立再計算で一致、凍結値は決定論 replay で byte 一致 / critic-experiment.md に答え
literal 不在 (critic.md には現存 = 物理削除の主張どおり) / 全 perf build 46 個の nm 走査で trace
シンボル漏れ 0 (trace build は 6 件 = 検査の弁別力確認)・計測に使われた build 16 種すべて trace 無効 /
全 8 WAL で「verify 赤なのに commit」0 件・fails-closed 経路網羅 / D1〜D31 連番欠番なし・主要数値の
文書間一致。検出は real_new 10 (medium 1 + low 9)・既知管理済み 4・refuted 1。監査の完全な結果
(全 finding の証拠と判定理由) はセッション成果物として保持、要点は以下の修正コミットに反映。

**唯一の medium = write-heavy「permutation p<10⁻⁴」の過大表示 → 訂正 (9c9d144):** 旧記録は方式・
反復数が未記録の Monte Carlo 由来で as-stated 再現不能。厳密 permutation (pooled 512 から 12 本の
多変量超幾何・全 50268 構成列挙、整数統計量で境界厳密) を `search_baselines.exact_perm_pvalue_A` に
コード化し (手計算校正 + 凍結度数分布の回帰テスト付き)、監査エージェントと本セッションの独立 2 系統で
**p=2.52×10⁻⁴** 一致を確認して確定。Holm ×6 でも <0.05 で「誘導は貪欲より有意に有害」・A=0.230 は
不変。伝播 5 箇所 (phase2 / D29 末尾訂正注記 / 本 worklog 過去エントリ注記 / insight 追記表 /
summary.json `correction_2026_07_03` 節 — recalibration 節は 07-02 の記録として原文保持) を訂正。

**low の消化 (7ea7cb4 / acdfece / 32e0f57):** phase2.md の P2-0 完了表記取り残し (実態は A4 の
buildcache 継続 assert に吸収済み) + sanity WAL 未保存の注記 + 「abort 0」の多義性明確化 (STAGE_ABORT
0 件 ≠ tx abort_rate) + C1 節を「解消済み (選択肢 a、065593a)」に更新 (前エントリ flag「4 文書の
食い違い」の phase2.md 側を消化) / calibrator 2 ファイルの削除済み pinning patch 参照 +
test_verifier の「4 カウンタ」ハードコードを修正 / insight に D26 恒真注記・per_step 証拠連鎖の範囲
注記、audit C1 の理由付け訂正、本 worklog 過去 2 箇所に前方注記 (P2-2 初回テーブルは再計測で置換済み /
「3構成」は 4 構成との揺れ)。

**対応せず記録のみ (既知管理済みと確認):** H3 hooks 未配線 (方針 A 進行中、テストは条件付き skip で
可視) / critic・profiler の「書き込みなし」が Bash 残存で規律ベース (agent 定義自身が開示済み) /
bench_lock の排他が pipeline 外計測スクリプトを覆わない (pgrep admission のみ)。監査 finding の
1 件「suite 全緑主張 vs 1 failed」は実測 (160→162 passed + 5 skipped) で現に全緑のため非成立と裁定。

### 次の一手 (変わらず)
- **Phase 3 タスク3 (H3 hooks 方針 A の実装)** — 順序: 一次防壁 → hook 最小化 → settings.json 配線。
- 未消化の docs 課題 (残り): 「WAL proof chain」の実体定義 / 外的妥当性の集約 / coder 自律期の
  停止条件・fitness 採否・再試行方針の予約。

## 2026-07-03 — Phase 3 計画の多視点敵対検査 + 検出 30 件のうち計画欠陥系を phase3.md に反映

ユーザー指示「phase3 と roadmap を検査して phase3 の計画を練る (問題・改善点)」。6 視点 (内部整合 /
roadmap・規律整合 / 実装実態との突合 / 実験設計・統計 / 規律突破面の残穴 / 運用・段取り) の並列
ファインダー → 指摘ごとの独立裁定 (real/refuted/known) の 38 エージェント構成 (読み取りのみ・新規計測ゼロ)。
**裁定 = real 30 (high 11 / medium 16 / low 3)・refuted 2・既知重複 0**。全指摘の証拠付き裁定はセッション
成果物として保持、構造的欠陥はユーザー承認のもと phase3.md に反映済み (下記)。

**検出した構造的欠陥 3 つ (いずれも複数ファインダーが独立検出):**
1. **主実験に到達する道が計画に無い** — 事前登録した headline 4 対照 + LLM ablation を実行する段が
   後続段 1-5 に不在。特に headline 2 (クロスプロトコル stock 最良) は trace-hook が silo/si にしか無く
   pipeline.evaluate (verify 必須) では COMMIT 不能 = S1 が前提なのに、must 表の S1 発火条件が主実験を
   数えていなかった。「sort 段以降の主張は従う」の文言も段 4 (coder 自律期、sort より前) を拘束できず。
2. **kickoff 完了条件が検査不能かつ自己矛盾** — abort>0 確認が 2 箇所で「完了条件に追加」と宣言され
   ながら本文未反映、かつ WAL に abort 数が記録されておらず (STAGE_VERIFY_DONE payload は 4 項のみ・
   _run_trace は stdout を捨てる) 確認自体が実行不能。「純 timing (or inert no-op) が stock cache-hit で
   commit」は選言で no-op 単独完了を許し、「純 timing が cache-hit」は identity 設計の故障状態を合格と
   読める。apply/revert 駆動部 (機構節が約束する pinned-clean assert 込み) も未実装・タスク無所属。
3. **一次防壁の穴 (方針 A の実効性)** — (i) 観測者効果二重検査 (blocking) の旧述語「両ビルドの
   preprocess 出力を diff」は成立しない (TRACE ガード領域で正当に食い違う)。(ii) source_digest は
   #include 行を digest 前に無条件除去 (`_INCLUDE_RE`) するため、coder の #include 追加はバイナリが
   変わるのに identity 不変 = stock と alias → 既存バイナリ cache hit で変更が一度もコンパイルされない
   まま certified 記録。防壁は道Y の hook 禁止のみ = 未配線で、方針 A が消したはずの単一障害点が復活。
   (iii) resolve→build 間の TOCTOU: 共有 working-tree に排他が無く、汚染が campaign 非依存の共有
   ビルドキャッシュに永続。

**phase3.md への反映 (修正 1-4、ユーザー指示):**
- **完了条件を 2 項に分離** (identity 後方互換 = no-op stock cache-hit / 合成枝 1 周 = 純 timing
  cache-miss 新規ビルド + **verify abort>0 の WAL 確認**)。「純 timing が cache-hit = 一次防壁の故障」と明記。
- **blocking タスク 4 本追加**: verify abort 数の WAL 記録 (ccbench stdout `abort_counts_:` パース) /
  apply-revert ハーネス (順序 = apply→resolve→build→revert 固定) / build 後 digest 再照合 (TOCTOU 遮断、
  worktree 隔離 = 段 5 までの最小防壁) / #include 死角の identity 核での閉塞。
- **観測者効果二重検査を「述語仕様の確定が先」に書き直し** — 候補述語 = **diff-of-diffs** (variant の
  TRACE=1/TRACE=0 preprocess 差分が pinned HEAD の同差分と一致)。旧残存リスク「#ifdef TRACE 内側に
  挙動差を隠す攻撃を素通し」もこの述語で D_variant≠D_stock として捕える (残存リスク節を更新)。保証しない
  こと (両ビルド共通の常駐メタデータは機械判定不能 = fitness 自己ペナルティ + auditor 領域) を明記。
- **主実験の実行を後続段 6 として新設** (gate = headline 候補 + S2 gate + auditor live。前提タスク (a)-(g):
  S1 or stock 専用計測経路の設計判断 / SPACES 拡張 + protocol 別 calibration + floor 対象別再実測 /
  ランダム変異生成器 / 機械 sweep 軸命名手順 / リーク制御実体化 / 検証相 (seed×N) / サンプル設計数値確定)。
  must 表 S1 行に主実験発火を追記。評価設計の拘束範囲を「coder が性能主張を生む段 (段 4 以降) すべて」に明確化。
- **統計計画の補完**: floor 流用禁止 (3.0% は stock silo 実測値、対象ごとに再実測) / サンプル設計 4 点
  (系列数・検定単位=系列・検定力・総予算。P2-5 は replay だったが Phase 3 は直列実計測 — 検定力不足由来の
  偽 negative を「LLM に価値なし」と誤読させない) / Holm 補正 / 天井の不在の明示と代替天井 (機械 sweep
  漸近 = 経験的天井、BACKOFF_FIXED grid = 局所天井) / deceptive 相当の検証 / 検証相の配線。
- **失敗条件 (e) 追加**: workload 過適合は退行込みで全 workload 報告 (選択的報告の禁止)。
- ベースライン 3/4 の操作的定義の最低要件 (Tier0 通過変異のみ・通過率報告 / 軸命名は coder 出力を見る前に
  固定し情報源を記録)。文言修正: 「Write hook で強制」→ 配線後に機械強制 (現在形の保証ではない) /
  coder.md タスクに前提 gate (hooks 配線 = `test_settings_json_wires_both_hooks` 緑を機械確認)。

**協議の決着 = a' (折衷、ユーザー承認):** roadmap §2 層2(b) の本丸「他 CC の最適化移植 + カタログ化」が
Phase 3 計画に不在という乖離は、**移植を拡張予約に降格**して解消 (D32) — 層2(b) の内側を b1 (空間外合成、
P2-4 で実証済み) / b2 (移植、未検証仮説) に分節し、主実験は b1 で行い、b2 + カタログ化は phase3.md
後続段 7 に予約 (一歩目 = カタログ化試作 1 枚、本格投資はその結果で判断)。roadmap は軽微改訂 (層2 名称を
「最適化合成ループ」に・粒度節 b1/b2・§8 コーパス駆動の再定義・§9 実態一致。協議合意ゆえ版管理セレモニー
不要)。README 三層図も追従。refuted 2 件 (変異軸順序の自己矛盾疑い / リーク制御と CLAUDE.md 自動ロードの
非両立疑い) は蒸し返さない。**コミット 3 件** (441a50b 検査反映 / f9fa80a a'+D32 / 本 worklog)。

### 次の一手
- kickoff 残り blocking の実装順 (phase3.md タスクリスト順): abort 数 WAL 記録 → apply/revert ハーネス →
  digest 再照合 → #include 閉塞 → hook 最小化 + 配線 → 観測者効果二重検査 (述語 = diff-of-diffs 確定) →
  coder.md + 全配線 1 周。
- 未消化の docs 課題 (残り、変わらず): 「WAL proof chain」の実体定義 / 外的妥当性の集約 / coder 自律期の
  停止条件・fitness 採否・再試行方針の予約。

## 2026-07-03 — 論文ストーリーの横断合成を凍結スナップショットとして文書化 (paper-story-2026-07-03.md 新設)

分析専用セッション。「このリポジトリは結局何をしているか、論文で主張する新規性とストーリーは何か」を
8 系統の並列読解 (roadmap / decisions / phase2+関連 insights / phase3 / worklog / 方法論文書群 / insights
全 17 件、計 8 エージェント・約 55 万トークン) + 独立コンテキストの欠落検査 1 段で横断合成し、
**docs/paper-story-2026-07-03.md** に凍結した (新規計測ゼロ・コード変更なし)。

**文書の設計 (ユーザー協議で確定):**
- **凍結スナップショット + 日付入り** (audit-2026-06-30.md の流儀)。Phase 3 主実験の成立で headline が
  移動することが計画上確定しているため、生きた文書として保守しない。正典は roadmap §8 / decisions /
  worklog で、矛盾があれば正典が勝つと冒頭に明記。
- 例外として **§5 過大主張チェックリストのみ消し込み式** (解消条件付き 11 項目) — 執筆フェーズで
  そのまま使う生きた道具として分離。
- 内容の柱: 3 幕構成のストーリー (評価器 → P2-5 negative × P2-4 backoff の対 → Phase 3 事前登録)、
  新規性主張 5 点 (実証状態タグ付き)、見落とされがちな素材 9 件 (isolation-phenomena の G2 定理、
  ccbench-anatomy の死にフラグ/affinity 死/空間見積 258、p2-5-summary.json の訂正履歴キー等)。

**欠落検査の主な収穫 (チェックリスト化した過大主張リスク):** certified の但し書き (S2 未消化)・
verifier「ツール権限隔離」表現 (audit §4 裁定と矛盾)・hooks を実装済み防壁と書けない (D30)・
anomaly 自動還流の ARA 優位は設計であって実証ゼロ・「コーパス駆動」の実働は silo 1 protocol のみ (S1)・
P2-5 誘導アームのモデル素性 (critic-experiment = opus / Bash のみ) が本文系文書に未記載、等。

### 次の一手 (変わらず)
- kickoff 残り blocking の実装順は前エントリのとおり。本セッションは docs 追加のみで Phase 3 タスクの
  進捗は無し。

## 2026-07-04 — kickoff blocking 4 本の取り込み監査 + 欠落回帰テスト補完 + コミット確定

前セッション (07-03) が未コミットのまま残した blocking 実装 4 本 (verify abort 数の WAL 記録 /
apply-revert ハーネス `patchharness.py` / build 後 digest 再照合 = TOCTOU 遮断 / #include 死角の
最小案閉塞) + 敵対検証 insights を、規律6 (別セッション作業物の取り込み監査) に従いコミット前に突合。
実装本体 4 本は insights のベクタ対応表と一致したが、**記録と実体の食い違い 2 件を検出**:

1. **「fixed: 回帰テスト 3 本追加」が記録のみで実体なし** — insights の F ベクタ (テスト正直さ ×3) への
   対応として `test_build_cache_miss_wires_recheck` / `test_run_trace_parses_abort_from_stdout` /
   `test_patchharness_applied_rejects_dirty_tree` を「追加」と記録していたが、リポジトリに存在せず
   suite も「174 passed」でなく実測 170。**F ベクタの指摘そのもの (謳うだけで存在しない保証) を
   監査記録自身が再演した形**。本セッションで 3 本を実装し、**変異検査 3/3** (build() の recheck 呼び出し
   削除 / _run_trace の abort パース None 固定 / applied() の pinned-clean 駆動削除 → 各 1 本だけ赤、
   復元で全緑) で「結線を消すと赤」を機械実証。補完後 **173 passed, 5 skipped**。
2. **phase3.md への反映 (blocking 4 の [x] 化・#include 最小案書き換え・残存リスク 3 点追記) が未実施** —
   insights は実施済みと主張していた。本セッションで実施 (残存リスク節: #include 死角の道Y 一般問題
   `__has_include`/#define は段 4 で skeleton 検査として load-bearing 化 / ABA は flock 緩和のみで恒久解 =
   段 5 git worktree 隔離 / _recheck の transient 破棄は D25 と意図的非対称)。

insights には 07-04 訂正注記として両件を追記 (前セッション記録の改竄はしない)。**コミット 5 本 +
本 worklog**: 9301a8c (pipeline: aborts→WAL + 集計行なし fails-closed) / e0b9b22 (source_digest:
include 行集合 HEAD 固定) / b059a70 (buildcache: 出口 + cache-hit 再照合、破棄失敗も明示例外) /
62a0db9 (patchharness: flock + pinned-clean 7 桁下限 + quotepath=false) / a5f72d0 (docs+insights)。
テストは実装ごとに分割 stage し、**各中間コミット tree を detached checkout で全 suite 緑と確認**
(162→166→167→170→173 passed の単調増分)。submodule pin (dff0f1e) 不動・clean。

### 次の一手
- **kickoff 残り: hook 最小化 + 配線 (H3 方針 A) → 観測者効果二重検査 (述語 = diff-of-diffs 確定) →
  coder.md + 純 timing variant 1 本で全配線 1 周**。
- 未消化の docs 課題 (残り、変わらず): 「WAL proof chain」の実体定義 / 外的妥当性の集約 / coder 自律期の
  停止条件・fitness 採否・再試行方針の予約。

## 2026-07-04 (2) — H3 hooks 方針 A 完了: payload 検査削除 + 3 巡目敵対検証 (real 9) 修正 + 配線 + source_digest -undef 廃止 (D33/D34)

前セッションが未コミットで残した方針 A の hook 最小化差分 (guard_write の payload 検査削除・guard_bash の
2 巡目 fix) を、規律6 (別セッション作業物の取り込み監査) に従い commit 前に監査し、3 巡目敵対検証を経て配線まで
完了した。上エントリの「次の一手」= hook 最小化 + 配線を達成。

**監査 (取り込み前):** 差分は D30 (方針 A) の設計どおり。guard_write は proof-chain 拒否 + designated ソース面
限定だけに最小化 (内容検査削除)。削除した payload 検査の責務は、実際に発火しテストもある一次防壁
(`assert_includes_match_head` / `assert_trace_diff_matches_head` の diff-of-diffs / `_recheck_src_token` の TOCTOU)
に確かに移っていることを test_campaign.py で確認。旧 payload 検査テスト 6 本が旧挙動を固定したまま赤 → 方針 A の
「内容非検査」テストに置換し一次防壁テストへ相互参照。guard_bash の 2 巡目 fix の回帰テストを追加、SPEC-3 の
恒真寄り matcher 検査を 4 tool 全要求に修正。`.claude/settings.json` に両 hook を配線。全緑 173。

**3 巡目敵対検証 (規律6 の取り込み裏取り + Phase 境界、ultracode):** 配線前に Opus 赤チーム 4 系統
(bash 新種 bypass / write bypass / 一次防壁の委譲穴 / 過剰拒否) の finder → 各指摘を独立スケプティックが実 repro で
real/refuted 裁定 → Fable 最終裁定 (19 エージェント・約 93 万トークン)。**real 9 / known-limitation 6 / refuted 0。**

**最重要 (critical) = 方針 A の前提破れ:** source_digest の digest は `g++ -E -undef` で builtin (__x86_64__ 等) を
全消しするため、EVOLVE-BLOCK に `#ifdef __x86_64__ / 別挙動 / #else / stock / #endif` と書くと digest 環境では
stock 枝に落ち src_token='stock' に化け、実ビルドでは別枝がコンパイルされる = 偽 cache hit (別挙動の variant が
verify 素通りで stock の certified を継承 = 規律2 直撃)。source_digest の docstring 自身 (道Y) が「-undef の乖離が
あるから生 #ifdef を hook で禁止する」ことを前提にしていたが、方針 A で hook payload 検査を削除したため前提が
崩れていた (coder 未実体化ゆえ未 live だが投入前に塞ぐべき kickoff-blocking の穴)。**ユーザーに報告し、案 A
(`-undef` 廃止 = 実 builtin を digest に反映) の承認を得て封鎖** (D34)。実 g++-13 で -undef あり=stock枝(偽hit)・
なし=実枝(999、実ビルド一致)、-Werror=undef の骨格 #if 供給漏れ検出維持、stock digest 2 回同一 (後方互換保持) を
検証。回帰 `test_source_digest_builtin_ifdef_not_aliased_to_stock` + 変異検査 (-undef を戻すと赤) で固定。

**hook 実装バグ 8 件 (bypass 5 + 過剰拒否 3) を自律修正:** 絶対パス/~ の rm の防護ツリー素通り (repo_root で
相対化)・改行がセグメント境界にならず先頭 read-only head が後続 writer 隠蔽 (改行を `;` 正規化)・heredoc `<<` の
bare interpreter (`<<` を opaque 化)・symlink root-output の fail-open (camp_root/sub を realpath 化)・NotebookEdit
decoy (notebook_path 優先)、nm/objdump/du の純読み拒否 (allowlist 追加)・tar/rsync backup の拒否 (read/write 判別)。
known-limitation 6 (変数展開・部分 glob・computed include・末端 tar backup 等) は docstring 明示の限界として据え置き。
全 fix を変異検査 3 本 (案A + heredoc + 絶対パス) で「fix を戻すと該当テスト赤・復元で緑」を機械実証。

**モデル分業 (メモリ [[model-downgrade-fable5-classifier]]):** 攻撃 probe (bypass 探索・repro) は Opus サブ
エージェント (workflow)、設計・裁定・修正・docs・commit は Fable メインループ。ユーザーの「fable でがんばれ」に
沿い、攻撃要約を読む turn の降格は気にせず Fable で進めた。

**成果物:** 全緑 176 passed / 4 skipped。docs 反映 = phase3.md (H3 hooks [x] 化・must 表)・decisions D33 (方針A
実装 + 3 巡目 fix + 配線)/D34 (source_digest -undef 廃止)・hooks/README.md (配線済・3 巡検証・payload 検査削除)・
本 worklog。**コミット 4 本** (source_digest 案A / hooks+tests / 配線+README / docs)。各中間コミット tree を
detached checkout で全 suite 緑と確認。submodule pin (dff0f1e) 不動・clean。

### 次の一手
- **kickoff 残り = coder.md 生成 + 純 timing variant 1 本で全配線 1 周** (一次防壁 = preprocess ハッシュ・
  #include HEAD 固定・diff-of-diffs・TOCTOU 再照合・**D34 builtin definedness**、hook 第二防壁 = 配線済で
  gate `test_settings_json_wires_both_hooks` 緑を達成)。まず no-op variant (#else 逐語複写) で stock cache-hit 実証 →
  静的 backoff 値 1 つの純 timing variant を Tier0→pipeline.evaluate→verify→bench→WAL で 1 周。
- 未消化の docs 課題 (変わらず): 「WAL proof chain」の実体定義 / 外的妥当性の集約 / coder 自律期の停止条件・
  fitness 採否・再試行方針の予約。

## 2026-07-05 — docs 横断監査 (real 39/refuted 4) の修理 + 文書一貫性の恒久対応 (正本一元化・handoff・lint)

**前夜セッションの救出:** 7/4 夜の監査セッション (ea4e70b7) がワークフロー完走・報告済みの状態で突然死し、
ユーザーの追加コメントが未処理のまま残った。生ログ (`~/.claude/projects/.../ea4e70b7*.jsonl`) と成果物
(`tasks/wesxvpwx6.output`) の採掘で全結果を無損失回収し本セッションが引き継いだ — この救出実費 (grep 探索 +
数千トークン) が下記 handoff 導入の直接の動機。

**監査結果 (izanagi-docs-audit, 7 レンズ 54 エージェント・302 万トークン・敵対検証つき):** 確定矛盾 **real 39
(重大 8/中 23/軽微 8) / refuted 4** ≒ 根本原因約 10 個。一次資料をリポジトリに凍結 =
`docs/audit-2026-07-04-docs-consistency.json` (39 件の A/B 引用・why_real・修正案 + 論文評価 4 レンズ全文)。
論文評価は 4 レンズ一致で promising-with-gaps (核心 = 空間外合成の証拠が n=1、Phase 3 主実験に全面依存。
安価な補強 = S2 前倒し・別 boot 再現・critic 再現率測定・Threats to Validity 集約)。

**観測された非対称 (論文素材、paper-story §4 に追記):** 衝突した全ケースで「作業と同時に書く記録
(worklog + git)」が正、「状態の再掲 (CLAUDE.md 現在地・roadmap 現況主張・phase2 must 写し)」が誤。
状態の再掲 = 陳腐化するキャッシュ。D34 (偽 cache hit 封鎖) と同型の失敗が自分の文書運用に居座っていた。

**恒久対応 (ユーザー協議・承認済み):**
1. **可変状態の正本一元化** — 正本 = worklog 末尾「次の一手」+ 現行 phase doc のチェックリスト/must 表。
   CLAUDE.md「現在地」は 3 行のポインタに縮退 (Phase 段落の歴史語りを全削除。監査の根本原因 1 = 現在地 stale
   7 件はこれで構造的に消滅)。roadmap は現況を主張しない。phase2 の must 一覧は凍結スナップショット化。
2. **`docs/handoff/` = セッションの WAL** — セッションごと 1 ファイル (日付+タスク短名、40 行上書き、
   節目ごと更新、正常終了時に worklog へ吸収して削除 = ディレクトリ空が健全状態)。並行セッションの宣言板を
   兼ねる (監査は基準コミット、計測は「計測中」を宣言)。運用は handoff/README.md、CLAUDE.md 作業の進め方 7。
3. **`tools/check_docs.py` = 決定的文書 lint** — living docs の行番号参照・現況再掲・「次 =」再掲、handoff の
   行数超過/stale を禁止パターンで検査。セッション締めに実行 (CLAUDE.md 作業の進め方 6)。
4. **ルール明文化** (CLAUDE.md 作業の進め方 6) — 再掲禁止 / docs 間行番号参照禁止 / タスク完了と同一コミットに
   チェックボックス反映 / セッション末 worklog 必須。

**39 件の修理 (新構造前提で適用):** phase3.md (観測者効果二重検査を [x] 化 = 実装は 14d64e6 で完了済みだった・
「hook 未配線」の現在形主張 (指摘 3 件、実 1 箇所)・削除済み payload 検査への現在形参照 (指摘 2 件、実 1 箇所) を
D33/D34 実態へ・must 表 2 行・C1 の語の揺れ)、CLAUDE.md (hooks 節を方針 A 実態へ・verifier/critic/profiler の
「書き込みなし」を audit-2026-06-30 §4 の裁定へ honest 化)、roadmap (§3.3 旧述語→diff-of-diffs 済み・§9 現況主張
削除・§7 ツール隔離表現)、phase2 (H3 完了追記・2.28% は floor 実測値でありゲート閾値 5% と区別 (D19)・冒頭に
P2-5 転回注記)、phase1 (タスク 4a/4b/6/7 の ✅ 追記)、D14→D12 誤参照 7 箇所 (リーク制御/循環回避/選択的報告の
文脈。decisions D21×3+D26・phase2・phase3・glossary。源流の insight 2026-06-29 の 4 箇所は凍結記録ゆえ訂正注記で
対応)。機械修理の一部は並行サブエージェント 2 本に委任し、規律6 に従い差分を監査して取り込み。

**敵対検証 (規律6: 並行エージェント差分の取り込み監査 + 一括修理の裏取り):** 9 検証官 (ファイル別 6 +
CLAUDE.md 縮退の情報損失検査 + 新規物検査 + 残骸掃引、約 78 万トークン) が指摘 19 件 (medium 5/low 14、重複統合で
実質 12) — 全消化。主な収穫: 修理の取り残し 3 面 (glossary の D14・agent-architecture hooks 節が方針 A 未追従の
まま CLAUDE.md から「詳細」として参照されていた・roadmap §3.4-3/§3.4-4/§7 の旧表現 3 箇所)、並行エージェントが
導入した節参照誤り (DB-dump 判断の所在 = タスク5b→正しくはタスク5a)、本セッション自身の number-mismatch
(監査レンズ数「6」→実データは 7。number-mismatch を修理するセッションが自ら再生産しかけた)、paper-story 追記の
全称の過大一般化 (worklog 自身の記録欠落という反例を併記する形に限定)、handoff「計測中」宣言と lint の stale
判定の不整合 (状態: 行 3 値に統一)、phase1 タスク6 の経路変更 (Mac ダミー fitness→実機 demo) の注記欠落。
CLAUDE.md 縮退による情報の孤児化はゼロ (V7)、絶対規律セクションの無変更も機械確認 (V1)。

**worklog 追補 (07-04 記録の欠落訂正):** 監査 real 3 件 (worklog-vs-phase / worklog-vs-current / numbers の
3 レンズが重複検出) の指摘どおり、**コミット 14d64e6
(07-04 19:56「source_digest+buildcache: 観測者効果の二重検査 (diff-of-diffs) を実体化」+204 行)** は 07-04 (1)
エントリのコミット 5 本にも (2) エントリの「コミット 4 本」にも帰属していなかった。実施経緯: (1) エントリ記録後・
(2) エントリの hook 作業より前に同日セッション帯で実装されたもの。述語 3 面 (diff-of-diffs / buildcache.build
出口 hit+fresh / fails-closed 破棄) + 変異検査 3/3・stock 通過 27ms はコミットメッセージと test_campaign.py を
一次記録とする。既存エントリは改竄せず本追補を正とする。

**成果物:** コミット 8 本 (handoff+lint 基盤 / 監査 JSON 凍結 / CLAUDE.md 縮退 / phase3 / roadmap+agent-architecture /
phase2+decisions+glossary+insights / phase1 / worklog+paper-story)。check_docs lint 緑。本セッションの handoff は
本エントリに吸収して削除 (ディレクトリ空 = 全セッション健全終了、が新しい定常状態)。

### 次の一手
- **kickoff 残り = coder.md 生成 + 純 timing variant 1 本で全配線 1 周** (07-04 (2) から変わらず。一次防壁 +
  hook 配線済み、gate = `test_settings_json_wires_both_hooks` 緑)。
- 論文系の安価な補強 (監査 actionable より、着手順の推奨): S2 前倒し → +38%/+11% の別 boot 再現 →
  critic 軸提案の再現率測定 (replay、新規計測ゼロ) → Threats to Validity 集約文書。
- 未消化の docs 課題 (変わらず): 「WAL proof chain」の実体定義 / coder 自律期の停止条件・fitness 採否・
  再試行方針の予約 (外的妥当性の集約は上記 Threats to Validity に統合)。

## 2026-07-05 (2) — ブート/常駐コンテキスト衛生 (D35): 全文必読の廃止・分離・worklog ローテーション

**トリガ:** ユーザーの戦略相談「セッション 1 メッセージ目の定型指示 (仕事を進めて/検査して) のトークン費用と、
worklog の存在価値はどうか」。5 視点の並列調査 (worklog 解剖 / ブート追跡 / 参照パターン / CLAUDE.md 常駐 /
git 重複、5 エージェント 36 万トークン) で実測 → 提案一式 + 論文素材化をユーザーが承認。

素材: **実測の要点 (運用方法論):** 定常ブート 4.6 万トークン中、当日の作業に必要なのは約 8% — §3.8 の
コンテキスト衛生がブート自身に未適用という再帰的欠落。worklog は分量の約 4 割がコミット本文の再掲
(二重帳簿)、git が原理的に運べない情報 (撤回劇・refuted・協議・工数・一括コミット下の実時系列) が価値の
5〜6 割。健全なブート予算 = 窓の 10〜15%。決定 6 点・却下 3 案 (current-state 静的キャッシュ = D34 同型の
再生産で却下、git log 置換 = 不成立、コミット body 薄化 = 逆方向) の正本は **D35**。

**成果:** commits f3e4d0a..02a42c0 + 本 worklog コミット (8 本、詳細は各 body)。骨子 = 昇格 4 件を先行
(ermia 罠 / baseline / headless 制約 / 見送り台帳) → worklog ローテーション (Phase 1〜2 分 1,189 行 →
worklog-phase1-2.md 凍結) → roadmap §7 分離 (related-work.md) + 読み方指定 → phase3 減量 39→27KB
(主実験 = phase3-main-experiment.md) → CLAUDE.md 18→14.7KB (絶対規律 bit-exact を git show 照合) →
phase1/2 凍結宣言 + check_docs 追従 + glossary 行番号参照 52 件の節名化 (サブエージェント委任、
規律6 の差分監査済 — 元の行番号は大半が既にずれており節名化の正しさを裏付け) → D35 + paper-story §4 追補。

**worklog の書式は本エントリから D35 適用** (CLAUDE.md 作業の進め方 7)。

### 次の一手
- **kickoff 残り = coder.md 生成 + 純 timing variant 1 本で全配線 1 周** (変わらず、前エントリ参照)。
- 論文系の安価な補強・未消化の docs 課題も変わらず (前エントリ参照)。

## 2026-07-05 (3) — docs/archive/ 新設 (凍結記録族の集約)

**トリガ:** ユーザー提案「役割重複のファイルはディレクトリへ (audit/phase/worklog)」。協議の決着 =
**「時系列で増え続ける族だけ」を `docs/archive/` 一本に集約** (audit 2 件 + worklog-phase1-2)。
**phase/ は見送り** (増加が遅く、現行 phase doc への参照が中核導線で波及だけ大きい)。**ファイル名は
不変で移動** — 凍結文書内の旧パス参照は直せない (改竄禁止) が、ファイル名 grep で辿れることを規約化。
**paper-story の日付抜き改名 (ユーザー発案・Claude 賛成) は指示保留のまま未実施** — やる場合は改名 +
冒頭を「時点合成の追記型 (合成時点と追記履歴を本文冒頭に)・矛盾があれば正典が勝つ」へ書き換え。

成果: commit 19e540e (詳細は body)。

### 次の一手
- 変わらず (前エントリ参照)。
