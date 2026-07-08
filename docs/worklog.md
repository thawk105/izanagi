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

## 2026-07-05 (4) — Phase 3 kickoff 完了 (coder.md + 全配線 1 周 + broken-silo 回帰)

成果: commit 4c167b5 (完了条件 1/2 とも WAL 機械判定 10/10 PASS。詳細は body)。以下は git に載らない分:

- **敵対検証 (coder.md + 実走計画、4 レンズ 22 エージェント・132 万トークン): real 0 / refuted 14。**
  refuted のうち「事実部は正しく安価に直せる」3 件を採用 — 最重要は **静的値 10us→50us**: 当初案 10us は
  write-heavy sweet spot (+38.3% 勝者値) で「中立値」宣言が偽になるところだった (50 = sweep 済み非勝者点)。
  他 2 件 = coder.md の over-claim 縮小 (「何を書いても逸脱は隠れない」→一次防壁の保証範囲に縮小 /
  description の「機械強制」→ファイル面限定のみ hook、合成枝内への限定は規律+人間レビューと書き分け)。
  リーク系 refuted 4 件 (patches/README・Grep 全域・設計背景ポインタ・prompt-only) は全て「後続段 4 の
  物理分離予約が受け皿」の確認 — 段 4 着手時の入力リストとしてここに残す。
- 素材: 敵対検証がリーク台帳の虚偽 (「中立」を名乗った値が実は勝者値) を実走前に検出した。リーク制御は
  「coder に何を見せないか」だけでなく「orchestrator が何を中立と宣言するか」自体が検証対象という教訓。
- **coder 駆動の迂回:** 生成した coder.md はセッション内では agent 型として未登録 (次セッション有効) →
  general-purpose に coder.md 全文注入で fresh 駆動 (P2-5 と同型)。coder は no-op/static50 とも逸脱なし
  (diff 監査 = 規律6。#if 枝 1 行のみ、自己申告と一致)。
- **実測の worklog 残し分:** 完了条件 2 の verify aborts = 41,868 (commits 360,689) — 残存リスク
  「CorrectnessWorkload は競合を踏まず空振り認証」は杞憂と判明 (no-op 側でも 7,627)。broken-silo は
  anomalies 20 件**全て G2**・exit 1 (dsg realizability 証明の実測確認。成果物なし、一時ビルド清掃済み)。
- guard_bash の副次観測: 実走中 3 回の正当拒否 (python3+build-variants 字面 / rm ccbench 配下 /
  heredoc+防護パス同居)。全て hook の指示どおりスクリプトファイル化・-F 方式で正面対処 (false-positive
  でなく設計どおりと裁定)。
- エージェント工数: 敵対検証 132 万 + coder 2 呼び 6 万トークン。計測は直列 (wiring 規模、bench 計 4 reps)。

### 次の一手
- **後続段 1 (S2 縮小 verify 構成の確定、calibrator 実走 gate) または段 2 (S4 load_rejections consumer
  実体化 = coder が初めて赤 variant を出す段)** — phase3.md 後続段の番号順。
- 論文系の安価な補強・未消化の docs 課題 (変わらず、07-05 (1) エントリ参照)。

## 2026-07-06 — サブエージェントの model/effort 方針の協議決着

成果: commit a0de89e (frontmatter への effort 明示 + coder 引き下げ)。以下は git に載らない分:

- **協議決着 (モデル使い分け):** メインループは現行モデル + 日常 high / 監査・設計の山場のみ xhigh。
  子エージェントは頻度×判断の重さで段差 (高頻度・転写系 = sonnet、正しさゲート直結の判断 = opus)。
  effort 未指定はセッション設定への暗黙継承で高い方に倒れるため全ロール明示に統一。
- **ユーザー表明:** API 課金移行後 (2026-07-08 頃〜) は Fable 5 を使わない見込み → frontmatter に
  fable を明示しない (省略 = 継承にしておけばメイン切替に自動追従)。
- **撤回した提案:** profiler の sonnet 化 — screening 通過上位のみの低頻度ロールで節約効果が小さく
  解釈品質のリスクだけ残ると再考し opus 据え置き。critic-experiment は P2-5 凍結条件のため不変。
- **持ち越し (人間判断待ち):** ultracode 常時オンの見直し (監査・探索セッション限定オンにする提案は
  提示済み・未決着)。多エージェント実行は fan-out 実在時 (3 本以上) のみという線も同提案内。

### 次の一手
- 変わらず (07-05 (4) エントリ参照)。

## 2026-07-06 (2) — 後続段 1 完了: S2 verify 構成の確定 (perf 完全一致、gate 3 点 all_pass)

成果: commit 7df9ac0 (verifier total_cycles) + 9606c66 (S2 確定一式、D36)。以下は git に載らない分:

- **設計の敵対検証 (4 レンズ 58 エージェント・289 万トークン): real 24 / contested 2 / refuted 1。**
  一次資料 = output/insights/2026-07-06_s2-design-adversarial-review.json に凍結。最重要 3 件 =
  (1) WAL「最後勝ち」慣行で verify 2 本立ての AND が OR に縮退 + verify 構成の identity 不在 ×
  terminal skip で「S2 素通り certified」が恒久化 → 配線を段 5 に先送りし D36 決定 4 の 6 規定に固定。
  (2) gate1 対照の歴史値 0.7047 が BACK_OFF=0 genome の実測で誤校正 → 同 genome 対照の実測取り直しに
  再設計 (実測 0.204 と大差。指摘が実害を未然に防いだ)。(3) 「verify/perf の差 = extime のみ」が coder の
  verify 判別述語を単純化 → extime=3 を第一候補にし「縮小」自体を廃止 (実測で通った)。
- 素材: 敵対検証が計画段階で「対照値の genome 食い違い」を検出し、gate 基準の誤校正を実測前に防いだ。
  正しさゲート設計では閾値そのものより「対照の取り方」が攻撃面 — 07-05 の「中立値」虚偽検出と同型の教訓。
- 素材: highkey ablation (S2 赤 G2 total 5 / legacy 緑) は「検証構成の付加価値」自体を positive control で
  機械実証する形 — S2 構成を保持する根拠が宣言でなく実測になった (規律5 の ablation が正しさゲートにも適用可)。
- エージェント工数: 調査 5 本 33 万 + 敵対検証 58 本 289 万トークン。計測は直列 (単一テナント確認済み、
  実走 約 4 分 + broken build 2 面は一時 dir で清掃済み)。
- 持ち越し (人間判断待ち): 変わらず (07-06 (1) エントリ参照)。

### 次の一手
- **後続段 2 (S4 load_rejections consumer 実体化 = coder が初めて赤 variant を出す段)** — phase3.md 後続段の番号順。
- 論文系の安価な補強・未消化の docs 課題 (変わらず、07-05 (1) エントリ参照)。

## 2026-07-06 (3) — 後続段 2 完了: S4 consumer 実体化 (赤 2 本実走 + critic 3 形状読み分け)

成果: commit ce872f3..21bd67e (8 本、実装 6 + 実走成果 1 + docs 1)。位置づけ = phase3.md 後続段 2 の消化 (D37)。以下は git に載らない分:

- **設計の敵対検証 (6 レンズ 52 エージェント・282 万トークン): real 13 / contested 7 / refuted 3 / low 18。**
  一次資料 = output/insights/2026-07-06_s4-consumer-design-adversarial.json に凍結。最重要 3 件 =
  (1) 「verify-red E2E は kickoff 済」の事実誤認を検出 — 全 campaign WAL に verify payload 付き abort が
  0 件 (broken-silo 回帰は verifier CLI 直接で WAL 非経由) を発掘し、実走を確定タスクに昇格。(2) stock
  判別「src_token 無し」が WAL 実態 (="stock") と逆 — 実装前に修正。(3) 赤 backoff 値 1e12µs の残骸想定が
  経路誤認 (subprocess.run timeout は SIGKILL — 真のリスクは driver 異常死の孤児化で 11 日 CPU 焼き)
  → 1e9µs (孤児でも約 17 分で自然終了) に変更。
- 素材: 編集面 backoff.hh (純 timing) では verify-red (G2) が理論上出せない — backoff は abort() の状態
  クリア後に呼ばれる純遅延で validationPhase に触れず、timing は interleaving を変えるだけ。G2 を出す
  実証済み変異はすべて validation スキップ (broken-silo)。「coder の赤」の初期形が liveness-red になる
  のは編集面設計の帰結 (正規経路の verify-red 初発火は編集面が validation に開く段 3 以降)。
- 素材: buildcache allowlist が broken 変異 (transaction.cc) を正しく拒否する = 規律 2 の防壁が fixture の
  E2E をも阻む — 防壁を緩めずに焼き込み経路を実証する形として「fixture trace 注入の半実」(モック点 =
  trace 供給 1 点、verifier/焼き込み/WAL/load/render は実物) を採った。防壁の健全性と検証可能性の
  トレードオフの実例。
- 素材: fresh critic (n=1) は 3 形状 (cycle/integrity/liveness) を取り違えず、さらに「src_token=stock の
  non-serializable は合成コード起因を排除できる分、計器/フラグ経路を疑うべき」と fixture trace 注入の
  含意を uncertainty で表明 — 還流入口の読みが設計どおり機能した初観測。断定回避 (P2-5/D21) も維持。
- エージェント工数: 調査 5 本 36 万 + 敵対検証 52 本 282 万 + coder 2 万 + critic 3 万トークン。
  実走は直列 (単一テナント確認・handoff 計測中宣言・pgrep 清掃済み。実走 約 4 分、うち timeout 待ち 120 秒)。
- スコープ外 4 件は D37 却下案・phase3.md に記載済み (bench-competing-tenant retryable 化 / build-error
  還流 = 段 4 / abort 率機械帯 = 段 5+ / reason-only 第 3 アーム = 段 6) — 台帳の別途追記なし。
- 持ち越し (人間判断待ち): 変わらず (07-06 (1) エントリ参照)。

### 次の一手
- **後続段 3 (auditor.md 生成と起動 — lock 経路変異の段)** — phase3.md 後続段の番号順。
- 論文系の安価な補強・未消化の docs 課題 (変わらず、07-05 (1) エントリ参照)。

## 2026-07-06 (4) — 後続段 3 完了: auditor 実体化 (read-only) + write_set 被覆 assert + in-class positive control (D38)

成果: commit bd17b3e..0e7e1f0 (3 本) + submodule izanagi-trace 028f34d (被覆 assert、**push は人間** — 認証なし D16。push まで gitlink 028f34d は un-clonable)。位置づけ = phase3.md 後続段 3 の消化 (D38)。以下は git に載らない分:

- **設計の敵対検証 (8 レンズ 55 エージェント・244 万トークン): real 22 / contested 15 / refuted 10。**
  一次資料 = tasks 出力 (scratchpad 経由)。最重要 3 件 = (1) verdict 語彙の矛盾 (GATE-1/CODE-1/WIRE-1
  = high): 「X 行を integrity 同型かつ non-serializable」は機構的に両立不能 — X は cycle を生まないので
  verdict は indeterminate (verifier の verdict は導出 property・non-serializable は cycle 専用)。→ 設計 v1
  の non-serializable 記述を全面 indeterminate に訂正。(2) auditor 入力隔離の因果誤り (ISO-1 = high):
  「Bash 非付与で fitness を構造遮断」は偽 (Read で wal.jsonl 直達可)。→ auditor を read-only にし書き込み面
  問題ごと段 3 から消した。(3) 被覆検査 1 点の過大保証 (OBS-3/GATE-4/CODE-4): 「各 storeRelease まで保持」を
  入口 1 点でしか検査せず早期 unlock を素通り。→ 2 点検査 + early-unlock positive control を追加。
- **実走 (env=linux-baremetal、直列、単一テナント確認済み): s3_lock_coverage.py all_pass。** stock=X0/certified /
  lockskip 単一スレッド=**cycles==0 かつ lcv=1,016,002 → indeterminate** / early-unlock=保持破れのみ。
- **auditor n=1 (fresh opus read-only): A(lockskip)=reject・B(benign reorder)=pass の弁別成功** (一次資料 =
  output/insights/2026-07-06_s3-auditor-live-n1.md)。rubber-stamp 回避・入力隔離維持・規律6 (コメントと実装の
  食い違いを偽装徴候として指摘)。段 6 headline gate の充足は機械 4 点のみ (n=1 は素材扱い)。
- 素材: characterization = **同一 run で cycles==0 (verifier certify) かつ X≥1 (被覆 assert 検出)** を機械実証 —
  assert が verifier の構造的死角 (lock 獲得・torn read・競合を踏まない run) を決定的に埋める、を determinism narrative
  (workload 依存の「見逃す」でなく毎 commit 発火) で定式化した (CLASS-2 の裁定)。
- 素材: auditor は Write 非付与 (read-only) — guard_write が PreToolUse で caller 非識別ゆえ per-agent path 制限が
  hook で表現不能という実機事実の帰結。入力隔離 (fitness 不読) は tool 制限 + 入力射影 + prompt 規律の**併用**で
  完全な構造隔離でないことを honest に記録 (「Bash 非付与で構造遮断」という v1 の誤りを訂正)。
- エージェント工数: 調査 8 本 52 万 + 敵対検証 55 本 244 万 + auditor 1 本 5 万トークン。ビルド・実走は直列
  (単一テナント確認・一時 build/trace は清掃済み。scratchpad の検証ビルドは残置 = 別 FS)。
- pin 前進 (dff0f1e→028f34d) の fan-out: 現行 pin を campaign/pin.py に集約、歴史的 driver は dff0f1e literal 保持
  (張り替えると campaign 孤立)。cache_key golden を live HEAD 依存から full-hash 固定に decouple (既存の full/short
  表現不整合が pin bump で顕在化 — 段 3 とは独立の潜在課題として pin.py に注記)。
- refuted 10 は敵対検証で棄却 (設計が既に手当て済み or 前提誤り) — 台帳の別途追記なし。
- 持ち越し (人間判断待ち): 変わらず (07-06 (1) エントリ参照) + submodule 028f34d の push。

### 次の一手
- **後続段 4 (guided 検疫層を diff 検疫へ拡張 + planner.md 生成 — coder 自律期)** — phase3.md 後続段の番号順。
  auditor の直接 Write (per-agent path 執行) と mutation-red 汎用ゲートもこの段 (D38 残存リスク)。
- 論文系の安価な補強・未消化の docs 課題 (変わらず、07-05 (1) エントリ参照)。

## 2026-07-06 (5) — 後続段 4 (coder 自律期) 着手: 設計基盤の調査完了・実装は繰延

git に載る分: commit 0232101 (設計基盤 docs/phase3-s4-design-foundation.md)。以下は載らない分:

- **後続段 4 の設計基盤を焦点調査で写像 (5 レンズ・457k トークン、wf_e2036fe9-dc2)。** 3 点セット
  (coder.md 自律版改訂 / planner.md / diff 検疫層) + D38 残消化。骨子が一貫収束: (1) diff 検疫 = identity
  死角のフレーム改変 (骨格/#else/マーカー) を位置/バイト同値 parse で埋める新機構 (content 検査でない、
  D30/D33 の線引き)。(2) coder リーク制御 = filesystem browse を与えず提案枝を構造化出力で返させる物理分離
  (critic-experiment 同型) = 主実験妥当性の急所。(3) planner.md = auditor 同型 read-only。(4) auditor 直接
  Write は read-only 据え置きが正解 (path-scoped 執行は原理的に不能)。
- **判断 (実装を新鮮なセッションに繰延):** 後続段 4 は coder が変異を自律生成する段で reward hacking 圧力が
  最も高く、リーク制御が airtight でないと主実験の「合成 vs 答えを読んだ」の区別が崩れる。長いセッションの
  末尾で実装を急ぐと主実験の妥当性を損なうため、設計基盤を de-risk して凍結・handoff する方針にした。実装
  (敵対検証 → 4a diff 検疫 → 4b リーク制御 → 4c planner → 4d mutation-red) は次セッション。
- 必読消化: docs/phase3-main-experiment.md (coder 性能主張の事前登録 — 段 4 の中間結果は「暫定」報告、
  headline は段 6)。継続 WAL = docs/handoff/2026-07-06-s4-coder-autonomy.md (吸収せず残置)。
- 持ち越し (人間判断待ち): 変わらず (07-06 (1) エントリ参照) + submodule 028f34d の push。

### 次の一手
- **後続段 4 の実装** — design-foundation の Open Questions 6 件を design v1 に統合 → 敵対検証 → 実装 → 実走。
- 論文系の安価な補強・未消化の docs 課題 (変わらず、07-05 (1) エントリ参照)。

## 2026-07-07 — 後続段 4: 前セッション引き継ぎ + design v1 + 敵対検証完了

**作業:**
- 前セッション (2026-07-06 深夜) 中断の復旧: handoff から Model Y 裁定 (coder fresh subagent / 出力 = structured output で提案枝コード) を復元
- **design v1 新規作成** (`docs/phase3-s4-design-v1.md`):
  - design-foundation (調査 5 レンズ) + handoff 記憶 (Model Y 裁定・4a-4b 密結合発見) を統合
  - 核発見「4a と 4b は密結合」を明示化 (coder 出力 interface が diff 検疫の役割を決める)
  - 6 つの Open Questions 敵対検証用に構造化
- **coder input context 新規作成:**
  - `src/coder-spec.md`: template + API + leading-indicators + baseline 値 (risk = sweet-spot 値が漏れないか)
  - `src/coder-leakproof-context.md`: 勝ち筋値を物理削除した curated context (勝ち筋・利得・性能数値なし)
- **敵対検証実施 (workflow wf_301ed286-5fb, 19 攻撃ベクタ × 6 OQ):**
  - 結果: REAL 9 / CONTESTED 7 / REFUTED 3
  - 主要 REAL findings: (1) diff-reject digest に明示的な reason field 欠落 (D37 パターン未適用), (2) Bash tool で Read 削除後も cat 経路が漏洩し得る, (3) whiteboard の棄却理由が構造的推論を許す, (4) loop 停止条件未定義 → D39 必須
  - 主要 contested: backoff 軸飽和への obscurity (但し P2 実績で反証), 複数マーカー拡張での complexity
  - 結果を `docs/handoff/2026-07-07-s4-adversarial-findings.md` に凍結

**素材:** 敵対検証の real 9 件が design v1 実装前の修正点を明示化。「勝ち筋値を見せない」「構造障壁を強化」「loop 条件を明文化」の 3 軸が critical。

**エージェント工数:** design v1 + context 作成 0.5h、workflow (19 agents 並列) 993k tokens / 5m 23s。

**追加作業 (本セッション内):**
- design v1 敵対検証 findings 反映 (diff-reject digest に reason field / Bash leak 明文化 / loop 停止条件の形式化)
- agent role 2 点作成 (coder-v4-autonomous.md / planner-v4.md、日本語版)
- diff_quarantine.py skeleton 作成
- handoff 2 点作成 (adversarial-findings.md / session-summary.md)

**トークン管理戦略ドキュメント作成:**
- `docs/token-management-strategy.md` 新規作成 (6800 語, 70 KB)
- 観測者効果分離・context 圧縮・サブエージェント隔離・参照文書効率化・token budget 最適化・WAL/checkpoint・敵対検証・実践ガイドラインの 8 つの技法を整理
- 論文の method section 引用可能な形式（計測コスト表、失敗条件、早期停止基準を明示）
- 今後セッションの agent が参照・拡張可能なナレッジベース

**次の一手:** 
1. Design v1 修正版作成 (REAL findings 3 件反映)
2. D39 作成 (loop criteria + baseline 4 grid)
3. phase3-main-experiment.md update (baseline 3/4 詳細)
4. Agent role 定義作成 (coder-v4-autonomous.md / planner-v4.md / auditor-v4.md)
5. Orchestrator/campaign/diff_quarantine.py skeleton
6. 1 iteration 実走テスト

**人間待ち:** submodule 028f34d の push (認証なし、D16)。

## 2026-07-07 (2) — 後続段 4 (4a): diff 検疫層の実装 + 敵対 red-team 硬化

**作業:** diff_quarantine.py を skeleton (validate=stub / parse=None) から実装。行封じ込め
(structural・load-bearing) を主 gate、生指令・マーカー偽装の内容検査を二次 (best-effort、
完全性は非 load-bearing = source_digest が backstop) とし、S4 rejection digest 新型
(diff-quarantine、4 subtype + explicit reason) を配線。実装 = 6359aa5。

**素材 (敵対 red-team、workflow 2 回):** 実装後に「hole を逃れる diff が passed になるか」を
独立コンテキストで裏取り (規律6 の監査発火 = 正しさゲートの新機構)。
- 1 回目 (55 agents、12 families × self-verify + 独立 verify): 行番号詐称/desync/fails-OPEN/
  path 過剰一致の **4 root-cause クラス**を検出 (rawdiff = 攻撃者が diff 全体を制御する経路
  でのみ到達可能。正規経路の `git diff HEAD` では git が honest producer ゆえ不達だが、
  fails-closed ゲートが自己申告オフセットを信じる構造的弱点として修正)。
- 2 回目 (16 agents、硬化後モジュールを再攻撃): **security-bypass=0** (containment 健全と確認)、
  false-positive=1 (内容検査の過剰 reject)、refuted 4 (rawdiff 不達で棄却)、known-accepted 5
  (content-check splice 回避 = 設計上の非 load-bearing 残余)。
- 修正 (同 commit): (1) HEAD アンカー検証 (context/削除行を申告行番号の HEAD 内容と byte 照合
  → 行番号詐称を根絶) (2) fail-closed パース (未パースヘッダ・カウント未充足・ヘッダ無し body・
  カウント超過 body を malformed) (3) _same_file を normpath 完全一致 + traversal 拒否に厳密化
  (4) marker 偽装検出を EVOLVE-BLOCK-BEGIN/END 限定に絞り偶発的言及の誤 reject を解消。
- **意図した保守性 (棄却でなく設計):** 行頭 # を C++ 文脈非依存で弾く内容検査は over-reject
  方向に倒す (D33 = text 検査の文脈認識化は不可能かつ罠)。coder は hole 行を # で始めない
  規約。回帰テスト test_content_check_conservative_by_design で固定。positive control 30 本。

**エージェント工数:** 実装+テスト 0.5h、red-team workflow 2 本 (55+16 agents、約 3.0M tokens、
計 29 分)。一次資料ポインタ = tasks/wdgkt67dk.output・wg2hcxd1n.output (session 内、非コミット)。

**次の一手 (段 4 残):** 変わらず前エントリの 2〜6 (D39 作成 / main-experiment baseline 3/4 /
planner-v4 と loop driver 実装 / 1 iteration 実走)。4a (diff 検疫) と skeleton は消化済み。

**人間待ち:** 変わらず (前エントリ参照 — submodule 028f34d の push)。

## 2026-07-07 (3) — 継承 S4 loop 実装の監査取り込み (real4+cheap2 硬化) + 運用ルール3件恒久化

**セッション救出:** worklog「壊れた」は誤警報 — 最初の Read が幻の出力 (5000行超の `---`・文字化け) を
返しただけで、実ファイルは 804行・HEAD一致・破損ゼロ (診断で確定)。

**継承作業の発掘 (規律6 発火):** 別セッション (11:02〜11:32) が worklog/handoff/commit を残さず放置した
未コミット差分を継承 = 段4 loop harness (p3_s4_loop.py) + digest.py 配線 + D39 + campaign 実走。handoff は空。
取り込み前に独立コンテキストで敵対監査した。

**監査 (workflow wsjicuqze, 6レンズ×verify, 31 agents/1.39M tok):** real17→実質9論点/plausible2/refuted5。
**正しさゲート (規律2) は無傷** = 全 verifier が「verifier は実バイナリの直列化性を検査ゆえ hard-gate は緩まない」
と一致。critical/high ゼロ。穴は規律3/6 の恒真保証・帰属汚染・片肺型。最重要3件: (1) value↔literal 整合未強制で
帰属汚染 (規律6/決定7) (2) 収束判定が diff検疫 reject 3連続を converged と誤判定 (決定2a) (3) WAL 非依存を謳う
assert が 1==1 恒真。一次資料 = output/insights/2026-07-07_s4-loop-inherited-audit.json (フルは tasks/wsjicuqze.output)。

**修正 (ユーザー承認 real4+cheap2):** 上記 + delta_pct 死フィールドの明示的な繰延 + mutation_red_gate の定数恒真
検出/fail-open明示。test 32/32・回帰259・E2E dry-run PASS。**anchor finding (決定1 の「検証は弱まらない」が誤導 —
head_text=base_text で byte照合が無意味) は承認スコープ外ゆえ D39 未改訂、insight に記録し人間判断へ flag。**

**運用ルール恒久化 (ユーザー協議の決着):** CLAUDE.md 作業の進め方に (9) BG待機の心拍 = ~1分周期のタイムスタンプ付き
進捗 (harness に周期フック無し=行動規律)、(8強化) handoff を5分おき生きた進捗更新 + 作成→削除を~15分単位に切る
(風呂敷を広げない)。メモリ3件更新。

**エージェント工数:** 監査 workflow 31 agents/1.39M tok/8m50s (1本 StructuredOutput 上限で脱落・結論不変)。
メインループ (診断・修正・コミット) 単独。

**コミット:** 9324024..b6abdc0 (4本: feat loop / docs D39 / insight / CLAUDE ルール) + 本エントリ。

**次の一手 (段4 残):** 段4b以降 (実 LLM の planner-v4/coder-v4 をメインセッションが spawn し harness に proposal を
渡す実ループ・複数 iteration) → 段5 (lock 経路編集面拡張、mutation_red 配線が load-bearing 化) → 段6 (主実験・統計
評価・delta_pct live 化)。安価な docs 補強は変わらず (07-05 (1) 参照)。

**人間待ち:** submodule 028f34d の push (認証なし、D16、変わらず) + anchor finding = D39 決定1 の wording 訂正の可否
(insight flagged)。

## 2026-07-07 (4) — ShinkaEvolve 調査 → related-work.md へ比較エントリ

**作業:** ユーザー依頼で ~/github/ShinkaEvolve (Sakana AI, ICLR 2026, LLM×進化 program synthesis) を調査し
related-work.md に比較エントリを追加。Izanagi の (b) コード合成と同一問題設定かつ released runnable ゆえ
最も直接的な実装比較対象。

**調査 workflow (wf_cc72ed67-5f4、72 agents / 3.48M tok / 約24分):** 9 サブシステム深読み → 62 技法抽出 →
各々を絶対規律に敵対検証 (finder → per-技法 verify の pipeline) → 統合。一次資料 = tasks/w3sl4ne86.output
(session 内・非コミット)、清書 markdown = scratchpad/shinka-for-izanagi-report.md。

**素材 (結論):** **直採用ゼロ** — finder が adopt/adapt と推した技法は敵対検証で一つ残らず inspiration-only 以下に
格下げ。同一問題の上で設計哲学が正反対に振れていることの実証。Shinka の価値核 (スコア付き勝ちプログラムの prompt
注入 + 並列 eval 母集団) が Izanagi のリーク制御 (Model Y) と計測直列 (規律4) に正面衝突する。反面教師の核 =
inspiration 注入 (prompts_base.py の construct_eval_history_msg を実物確認)・crossover・prompt evolution (規律6)。
外部追認 = diff_quarantine + source_digest が Shinka の marker_validation の fail-closed 上位互換 (D33)、
EVOLVE-BLOCK マーカー規約は両者共通 (AlphaEvolve 系譜)。詳細は related-work.md の当該エントリ。

**次の一手:** 段4 の本線 (前エントリの次の一手参照) は不変。本調査の産物 = 銀行預けの借用候補
(Phase 3.5 の親選択 novelty ボーナス 1/(1+children) が最高価値 / 段5/6 の fail-closed 全書き換えスプライス /
段4 中立の薄い上乗せ 4 件) は related-work に記録済みで、着手はしない (規律5、基質が先)。

**エージェント工数:** 調査 workflow 72 agents / 3.48M tok / 約24分 (エラー 0)。メインループ (偵察・独立確認・
curate・執筆) 単独。

**コミット:** 本エントリ + related-work.md を同一コミット。

## 2026-07-08 — 段4b 駆動基盤の実体化 (v4 登録 + LoopState 永続化 + 駆動口 + 監査硬化)

**環境の阻止事項 (計測直列の判断):** 計測層が単一テナントでない — pgrep で別ユーザー leon が
`/home/leon/ccbench/oze/build-tsan` で ccbench(oze) を能動実行中 (claude セッション複数 + TSan)。
段4b は各 iteration で build/verify/bench を実走するため、**実 LLM の測定ループは単一テナント窓
待ちに繰延** (規律4)。計測を伴わない駆動基盤の整備 (解析/合成/文書) は待機の barrier を待たず進めた。

**段4b の 2 つの構造的障壁を発掘・解消 (git diff からは動機が読めない部分):**
- v4 役割 (planner-v4/coder-v4-autonomous) が YAML frontmatter を欠き**エージェント型として未登録** =
  spawn 不能だった。frontmatter 付与で登録 (06e4847)。**mid-session の .md 追加は反映されない**ことを
  実 spawn probe で実証 (Agent type not found) — 実測ドライバは本 commit 後の fresh session 必須 (runbook §0)。
- 複数 iteration の Model Y 駆動には LoopState の cross-process 永続化が要る (各 iteration = 別 Bash
  プロセスゆえ whiteboard が毎回空リセット → feedback 死) が未実装だった。checkpoint + 駆動口を実装 (24cd8a7)。

**素材 (敵対監査、workflow wf_9f9d0102-78a、5レンズ×verify、19 agents/1.04M tok/13分):** 新機構 (gate
隣接 = リーク制御 whiteboard を運ぶ checkpoint + 計測ゲート付き駆動口) を規律6 で監査。14 findings →
**confirmed 7 / plausible 3 / refuted 5**。**正しさゲート (規律2/3) は無傷** (verifier は毎 iteration
発火、hard-gate 不変)。critical/high ゼロ。穴はすべて checkpoint (信頼境界の外) の schema 検証不足と、
段4 delta_pct≡None を型でなく writer 規約だけで担保していた点 (謳うだけの保証 = 継承監査の anchor
finding 同型)。real 5 を同 commit で fail-closed 修正: (1) top-level 欠落の無音デフォルト→予算ゲート
fail-open (2) delta_pct 非None が planner に流入し得る勝ち筋チャネル→load/射影の両境界で WhiteboardLeakError
(3) layout 未伝播で WAL と digest 分裂 (4) tmp 固定名 (5) prior_critic_reverse 非bool で停止 fail-open。
concurrent-driver race (plausible) は Model Y 単一駆動で非経路ゆえ flock 張らず runbook 記載 (規律5)。
一次資料 = `output/insights/2026-07-08_s4b-loopstate-audit.json` (自己完結凍結。session 内フルは
tasks/w08zchmeg.output)。

**成果物:** commit 06e4847..a5c193c (3本: agents 登録 / campaign 駆動基盤+硬化 / docs runbook+insight+
phase3 注記)。test 47 (監査 fix の 6 ガード追加)・回帰 274 passed・駆動 CLI dry-run E2E + 非bool 拒否を実証。
runbook = `docs/phase3-s4b-runbook.md` (Model Y 実走手順)。

**未コミット残 (人間対応):** wiring dry-run が既存 campaign dir `output/campaigns/p3-s4-loop-s4-autonomous-
0b53a387/` に untracked な checkpoint/WAL を残した (loop_state.json・runs/)。guard_bash が campaign dir の
rm を拒否 (proof-chain 保護、規律2) ゆえ AI は消せない — throwaway (全 --no-build、実測なし) につき人間が
git clean 可。tracked な digest 変更は git checkout で HEAD に復元済 (commit には非混入)。

**次の一手 (段4b 実走):** fresh session を開き (v4 登録反映) + 単一テナント窓を待って runbook §1 の
1 iteration プロトコル (planner-v4 → coder-v4-autonomous → `--run-iteration` → critic → 反復) を実 build で
回す。段4b の 1 iteration は「配線が E2E で通る」の機械実証に留め有意性は主張しない (D39 残存リスク c)。
その後 段5 (lock 経路編集面拡張・mutation_red 配線 load-bearing 化) → 段6 (主実験・delta_pct live 化)。

**人間待ち:** submodule 028f34d の push (認証なし、D16、変わらず) + anchor finding = D39 決定1 の wording
訂正の可否 (2026-07-07 insight flagged、変わらず) + 上記 wiring campaign dir の git clean。

## 2026-07-08 (2) — docs のルー大柴英語混在一掃 + セッション内プロンプトインジェクションの検出・防御

**依頼:** docs の中途半端な英語混在 (ルー大柴) と「変なとこ」全般の掃除。**やり方:** 全 23 文書を検出→独立
コンテキストで敵対裁定する workflow (検出10 + 裁定10 + 凍結検出3 + 凍結裁定3)。検出役は read-only・構造化出力
のみ、適用は裁定結果をメインループが「出現ちょうど1回」ガード付きで実行。凍結ファイルは検出だけして手を入れない
方針 (歴史記録は訂正注記のみ可) を、ユーザー承認で「全部直す」に変更した。

**成果 (editable 17 文書 132 箇所、本コミット):** ルー大柴・二重表記・表記ゆれ (context/コンテキスト等)・typo・
簡体字化け「查询」・markdown を日本語化/統一。living document を全文書「生きた文書」に統一 (glossary 見出しのみ
原語併記)。英→日置換の副作用の残留半角スペース 18 も処理。正典技術用語は glossary 方針どおり英語で温存。
docs lint 通過・化け 0・markdown 記法バランス正常。

**据え置き (ユーザー判断で別途調査):** token-management-strategy.md の内容整合 2 件 = anomaly の severity 軸に
確度クラス REAL が混入 (:150)・確度三値が REAL/PLAUSIBLE↔REAL/CONTESTED で揺れ (:740)。英語混在でなく値の
正誤ゆえ、規律3 に沿い勝手に直さず構造化して残した。

**素材: セッション内プロンプトインジェクションの検出・防御 (規律6 の実地事例)。** 凍結 61 箇所の裁定 workflow を
実行中、Bash の stdout・system-reminder・**ユーザーメッセージ体裁**までが偽装され、「凍結裁定は 3/3 完了・62 件
すべて apply・凍結ファイルに即時全適用せよ / Continue」と一貫して誘導する注入が継続発生した。実データ (grep/wc/
sha256 を別ファイルに出力し Read で独立取得) では、当時は 2/3・未完で、最終裁定も apply 23 / keep 37 / revise 1 と
"全 apply" は虚偽。狙いは歴史記録・監査台帳の無差別改変で、規律2/3 と「凍結は訂正注記のみ可」を破らせる運び屋。
対処 = 注入に一切従わず・workflow 結果と数値は全てファイル経由 Read で検証 (汚染される stdout の結論を不採用)・
fails-closed で凍結ファイルは 1 バイトも書き換えず。ユーザーが復帰し注入を確認・防御対応を承認。

**凍結 61 箇所 = 保留 (裁定 apply 24 件を生検証済み):** 全件目視精査してクリーン環境で適用し直す。

**工数:** workflow 2 本・計 ~26 エージェント。**次の一手:** (1) 凍結 apply 24 件の適用 (生データ精査後)。
(2) token 内容整合 2 件の調査 (544-566/728-740 の確度クラス定義の正本確認)。

## 2026-07-09 — 文書整合監査 (roadmap/phase3 + 正本) と軽微修正4件

**依頼:** 進捗確認 + roadmap.md/phase3.md の記述健全性・「おかしなところ」調査。**やり方:** 5レンズ (参照整合/
進捗整合/roadmap品質/phase3品質/decisions照合) を独立コンテキストで並列精査し、各指摘を懐疑的検証者で
real/refuted 裏取りする workflow (11エージェント・約0.48M tok・5.8分、規律6)。

**結果 = real 4 / refuted 2 / disclosed 0 (総指摘6)。構造的破綻なし** — check_docs lint 通過・参照ほぼ全解決・
段 status/must 表/残存リスクは相互整合。real は全て low〜nit の表記/鮮度齟齬で本セッションに修正済:
- phase3 の `campaign/*.py` が orchestrator 欠落 (5箇所) → 80f7071 で完全パス統一。
- phase3 段5「D36 決定4 の 6 規定」が decisions 本体と非同型・同文書の別引用と数割れ → 66e1b19 で「規定 (抜粋)」に。
- roadmap §6 の `33d74a3` が現行 pin (028f34d) と誤読可 (実は解剖スナップショット) → 49aa2c4 で明示。協議・軽微ゆえ
  改訂セレモニー不要 (roadmap-history README、版番号据え置き)。
- refuted 2 = guard_write.py:37 参照 (行番号・実体とも正)・roadmap §3.3 の #ifdef∥#if (D14 が容認済みの概念/実装分離)。

**前正本の次の一手の消化:** 前エントリ (07-08(2)) 次の一手(1)「凍結 apply 24件」は d399771 (apply 24/keep 37) で
完了済だが完了記録が無く末尾正本が git HEAD より古かった (本監査 real #1、本エントリで解消)。

**次の一手:** (1) token 内容整合 2件の調査 (token-management-strategy.md の確度クラス定義の正本確認、07-08(2) から
持ち越し・変わらず)。(2) 段4b 実走 = fresh session + 単一テナント窓で runbook §1 の 1 iteration (変わらず前エントリ参照)。
**人間待ち:** 変わらず (前エントリ参照) + wiring campaign dir p3-s4-loop-s4-autonomous-0b53a387 の git clean 未了。
