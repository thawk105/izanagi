# Phase 3 — 段 6 (h)〜(j)・段 8a・解消済み must 行の完了記録 (凍結アーカイブ)

**凍結 (2026-07-15): 追記しない (訂正注記のみ可)。** `docs/phase3.md` (現行 phase doc) から
完了済み記録を分離したアーカイブ。様式は `phase3-kickoff-stages1-5.md` (2026-07-10) と同型だが、
今回は未了の段 (段 6・段 8) の中の完了済みサブ項を分離した (分離契約の 2026-07-15 改訂による。
経緯 = worklog 2026-07-15 の読書量診断)。完了/未了の正本・must 表・残存リスク・現役の裁定
(2026-07-14 の 8a クローズ裁定等) のサマリは引き続き `docs/phase3.md` にある。

本文は分離時点の逐語写し。原文中の「残存リスク節」「must 表」「S-1 checklist」等の節参照は
分離元 `docs/phase3.md` の節を指す。

---

## must 表の解消済み行 (分離時点の全文)

現行 phase3.md の must 表では下 3 行の経緯部分を縮約した。分離時点の全文は次のとおり
(表ヘッダは照合の便宜で再掲):

| must | kickoff | 根拠 |
|---|---|---|
| **H3 hooks** | **完了 (方針 A)** | 最小第二防壁を配線 (D30/D33)。3 巡目検証で real 9/known 6 摘出・全修正 (変異検査済)、critical (source_digest builtin definedness 偽 cache hit) は D34 で封鎖。identity/観測者効果の担保は下 2 行の一次防壁が担う |
| **S4** | 完了済 | 規律3 配線 (verify-red の構造化 anomaly を abort payload + load_rejections)。**consumer 実体化も完了 (後続段 2、2026-07-06、D37)** — liveness-red 別型・render 3 形状・critic 消費規定・実走赤 2 本で閉ループ実証 (「読んで方向を返す」まで。還流 = 次 variant 生成への使用は段 4) |
| C1 (campaign-id drift) | **解消済み (2026-07-09、段5、D40)** | apply→revert で HEAD 不動。読み手 3 本の discover 統一 (065593a, 2026-07-02) で歴史的 campaign の孤立は解消済み。並行合成/patch 常駐で HEAD が動く残課題は git worktree 隔離 (`patchharness.checkout()`、opt-in) で解消 — 各評価が自分の pin を自分の worktree で checkout するため他の並行評価の影響を受けない。driver 宣言値 (phase2.md §C1) がリテラルであること自体は IDENT-1/IDENT-3 により意図的据え置き (変更なし) |

---

## 段 6 前提タスク台帳の完了済みサブ項 (h)〜(j) (分離時点の逐語写し)

   (h) **(完了 2026-07-10、D45) planner→coder 経路のリーク遮断 (D44、headline の前提条件)** — planner-v4 を
   tools:[] 化 (Read 剥奪 = file-read 経路を coder (D39 決定7) と同型に構造遮断。入力は従来どおりメイン
   セッションの射影 inline JSON — 運用上 Read の必要はゼロだった)。allowlist 案は棄却 (根拠は D45)。
   同時に文書地雷 4 点を除去/中和: `coder-v4-autonomous.md` の spec_file 例 → leakproof_context に置換、
   design-v1 §3 の「output/insights OK」記述と design-foundation §3 の「tools=read-only」断定に supersede
   注記、`src/coder-spec.md` §7 の旧設計フローに superseded 注記、`src/coder-leakproof-context.md` 内
   template の coder-spec 誘導参照を実運用 (射影 inline) に一致させた。**遮断は Read 経路に限る** —
   justification 自然文経路・射影の自己規律は残存リスク節に維持。3レンズ敵対レビュー済み
   (must-fix 1・should-fix 6 を全て反映)。定義変更は次セッションから有効、
   (i) **(完了 2026-07-10、D46) sort 軸の機械 sweep 先行実測 (D44、安価な先取り)** — sort comparator
   空間を構文契約から機械列挙 (15 候補 + stock、全点 SWO 構成的保証。ランダム変異は D46 決定4 で
   段 6 (c) へ繰延) し、p2_2 確定動作点で balanced/write-heavy 全点 legacy+s2 verify の偵察
   (preliminary、事前登録外カテゴリ — (c) 判定は出さず、正式 grid への firewall を明文化)。実測:
   32+6 点全 certified・anomaly 0。**balanced は全点 floor 内で winner が再測不再現 (差なし方向)、
   write-heavy は sk_ad の stock 超え +3.55%/+4.12% が 2 run 再現するも分解すると各成分 floor 内・
   floor 未較正・n=2 で断定せず。sort 軸に「順序の質」由来の floor 超地形は見当たらない — 軸選定の
   見直し (段 8a 前倒し等) が人間判断事項** (正本 = D46・`output/insights/2026-07-10_s6-sort-sweep-
   preliminary.md`・`orchestrator/campaign/s6_sort_sweep.py`)、
   (j) **(完了 2026-07-10)** related-work の欠落埋め (D44) —
   Web 調査 5 レンズ + 書誌の独立機械検証 (arXiv バルク 9/9・DOI・リポジトリ実在) を経て
   related-work/README.md §7.1/7.2 へ反映: OtterTune 系 (knob tuning 4 本) と learned DB components
   系 (5 本) を系譜まとめエントリで新設、AlphaEvolve/FunSearch を一次資料裏付けへ更新 (EVOLVE-BLOCK
   マーカーの出典 = AlphaEvolve §2.1/2.3 と確定、FunSearch は arXiv プレプリント不在確認)、
   OpenEvolve は「論文なし」を三重根拠で確定。**副次発見: CCaaLF は v4 で NeurCC に改名され
   SIGMOD 2026 採択** (エントリ・逆引き索引に反映)。生データ =
   `docs/related-work/literature-map/gap-research-2026-07-10.md`。**Polyjuice/NeurCC 実測比較は
   見送りで決着** (ユーザー協議、worklog 2026-07-10 (9)。再判断の発火条件 = 「学習型 CC を定量的に
   上回る」の headline 昇格時のみ、材料は worklog 2026-07-10 (8))。

---

## 段 8a — 軸提案のループ内化 (分離時点の逐語写し)

   - **(8a 完了 2026-07-12) 軸提案のループ内化 (前倒し決着 — sort 軸 iteration 2 見送りの代替本筋、
     worklog 2026-07-10 (10))** — P2-4 が成立可能性を示した役割仮説 (機序帰属からの軸発見) をループに入れる。
     critic の機序帰属を入力に「次の変異軸候補 (EVOLVE-BLOCK hole の位置と骨格)」を提案する役を新設し、
     人間は承認 gate としてのみ関与する。D41→D43 で 1 回実施した軸オンボーディング手順 (骨格 patch・
     検疫対応・positive control・auditor ギャラリー拡張・verifier 死角の特定) を**再利用可能なテンプレ**に
     固めることが前提作業 — 軸あたり固定費を下げないとループ内化しても回らない。**前提作業は完了
     (2026-07-10、`docs/axis-onboarding.md` 新設 — 3 レンズ敵対レビュー済み、must 3/should 8 全反映。
     偵察 insight → LLM ループの新設 firewall と「削るのは再発見コストでありゲートではない」を明文化)**。
     リーク制御と両立する
     (軸提案に勝ち筋の値は不要、機序帰属のみでよい)。次軸の標準手順 = 機械 sweep 偵察 (D46 の器) で
     軸の生死を先取りしてから LLM ループを回す (worklog 2026-07-10 (10) 決着 3 点目)。
     **本体設計は完了 (2026-07-10、D47 — 3 巡の敵対レビュー: v1 で実効性レンズ reject → must 5/
     should 11/nit 6 反映の v2 → 再判定で新規 must 1 → v3 で adopt-with-conditions)。** 役の常設
     定義 = `docs/agent-architecture.md` §axis-proposer。要点: tools:[] + 二層射影 (勝ち筋の値は
     落とし診断数値は保持・recommend 丸ごと除外・死軸は生死二値のみ)・出口基準の事前定義付き
     n=1 実証・**8a 由来軸は当面「探索補助」限定で段 6 headline の対象軸にしない** (事前登録の
     命名固定と原理的に非両立のため、D47 決定 5)。**実体化完了 (2026-07-10、ユーザー明示承認済み =
     worklog 2026-07-10 (13)。`.claude/agents/axis-proposer.md` 生成 + D47 必須条件 5 点消化 —
     条件 2 は残存リスク節、条件 3/4 は axis-onboarding §2/§3-B、条件 5 は定義の出力スキーマ)。**
     **n=1 実証完了 (2026-07-10、D47 決定 4 の出口基準で成功 — 3 項目全 yes の候補 2 件 /
     提案 3 件、採点は射影非関与の独立コンテキスト)。** 一次資料 = `output/insights/
     2026-07-10_s8a-n1-proposal-and-scoring.json` (提案・採点全文) + `output/insights/
     2026-07-10_s8a-n1-provenance.json`
     (三点セット: raw の脚 = P2-3 要旨 insight — critic 再実行による生出力再生成は勝ち筋を含む
     現行文書経由の記憶汚染リスクで不採用、実体化検証 2026-07-10 の決定 / 射影版入力 / 落とした
     対応表)。観測: 恒真 0/3・既存軸再提案 0・**既開通領域への偏り 3/3 (全提案が transaction.cc
     — 開通・未開通対称の地図でも bias が消えなかった。次回 n を増やすときの観測継続項目)**。
     **人間承認 gate 決着 (2026-07-10、ユーザー判断): 提案 1 (silo-backoff-trigger-gating) のみ
     採用。** 提案 2 (wal-flush-cadence) は軸適格性 no、提案 3 (lock-conflict-retry-bound) は
     スカラー縮退リスクの境界で棄却 (採点 insight の判定材料どおり)。
     **段階 B 完了 (2026-07-10、D48 — シート独立再導出 + 3 レンズ敵対レビューで条件付き採用。
     verdict = 3 レンズとも adopt-with-conditions、must 1/should 7/nit 3 全反映、D47 必須検査
     3 点 = 全 PASS)。** 骨格設計の確定 = #if 囲み stock inert / thread_local 7 点全 store +
     sentinel fail-safe / 構文契約は要因 enum + 定数のみ (偵察空間 = coder 空間)。シート
     (裁定反映済み) = `output/insights/2026-07-10_s8a-stage-b-sheet-backoff-trigger-gating.md`。
     **段階 C 完了 (2026-07-10、D49 — D48 必須条件 7 点全消化)。** 骨格 patch
     (`patches/silo-backoff-trigger-gating-variant.patch`、stock inert・identity 実証済み) +
     positive control (計装/misattr patch + `s8a_trigger_coverage.py`、11 検査 all_pass —
     misattr の赤の歯を実走証明、verifier は緑のまま = 死角の実証) + 中立性 3 レンズ全通過 +
     軸定数 `orchestrator/campaign/axis_trigger_gating.py` (D 偵察器/E driver の import 先、
     構文契約禁止リストの転記元)。実装上の設計判断 (計装の characterization 専用分離・hole の
     述語 1 行化・構造ゼロ検査型) は D49 が正本。
     **段階 D 完了 (2026-07-11、D50 — 必須前提 3 点 + D49 申し送り 3 点全消化)。**
     機械 sweep 偵察 (2^3 subset + ident_all + stock、3 workload、全点 verify legacy+s2) で
     **floor 超地形が 3 workload とも cross-run 再現** (best vs ident_all: balanced g_rl
     +84.5%/再測 +91.0%、write-heavy g_rt +61.2%/+61.3%、read-heavy g_rl +98.9%/+98.7%) =
     軸は生の強い候補。insight =
     `output/insights/2026-07-11_s8a-trigger-gating-recon.md` (裁定台帳・kill 残骸毒の
     教訓を含む)。
     **E 段実装完了 (2026-07-12、D51 — gate はユーザー承認 (worklog 07-12 (2)) で通過。
     実装前 3 レンズ敵対レビュー adopt-with-conditions、must 3/should 10/nit 5 全反映)。**
     provenance 情報源記録義務 (D46 (a) ループ版、監査 L4-1) の宿主 =
     `<campaign root>/reports/p3_s8a_trigger_loop_provenance.json` (driver が自動記録・
     省略不能、書き込み順序と fails-closed 群は D51 決定 1)。成果物 = `auditor_gate.py`
     (共有昇格) + `p3_s4_loop_trigger_gating.py` + `docs/phase3-s8a-trigger-runbook.md` +
     テスト 28 本。**coder 定義は承認・配置済み (2026-07-12 ユーザー明示承認 =
     `.claude/agents/coder-v4-autonomous-trigger-gating.md`、承認判断の一次資料 =
     `output/insights/2026-07-12_s8a-stage-e-coder-agent-draft.md`)。**
     **F 段完了 (2026-07-12、worklog 07-12 (6)) — 実 LLM iteration 1〜2 E2E、両 iteration
     certified (verify legacy+S2 とも 0 anomalies)・auditor pass・provenance 全 entry 記録。**
     軸提案 (axis-proposer) から探索 (planner/coder、iteration 内は自動・セッション駆動は人間) まで
     ループ内で閉じた初の軸の実走。
     critic 帰属 = 両 iteration ともノイズ内 tie — この動作点 (records=100k/threads=4、
     abort 約 2.3%) では gate の発火頻度が低く bite しない。checkpoint (campaign
     `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5`) を最終成果物として保存し、この動作点の
     性能探索はクローズ済み。
     **2026-07-14 裁定:** この低競合動作点での性能探索はクローズし、単独の再ホストはしない。高競合で
     再利用するなら、結果既知の追試でなく下の 8b 前向き設計へ統合する。auditor proposed_tests は軸を
     再利用するときだけ採否を再開する。
