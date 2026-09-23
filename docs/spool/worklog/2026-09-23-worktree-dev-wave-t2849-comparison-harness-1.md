---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-dev-wave-t2849-comparison-harness
seq: 1
title: [T-2849] 5 手法比較基盤 (S1) の単位 1〜7 と [T-2853] (1) の trace 保全口を実装した — B-5 の兄弟 module の系列 driver と BO・進化の生成器、参照 genome と harness slot の評価入口、K0 LLM の巡 tool と役割定義の改訂、job body の harness 分岐、env opt-in の zstd 保全。焦点走 3,645 passed・変異 26 / 26 KILLED (コード + test + 役割定義 + insight、branch worktree-dev-wave-t2849-comparison-harness)
---

## 本文

- 設計判断は {{D:t2849-harness-impl}}、記録は insight `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md`。Codex author 3 単位 (評価入口と保全口 / 系列 driver と生成器 / 巡 tool と job body と pin) を並列に投じ、fix は U-B・U-C が 1 巡、U-A が 2 巡。role adapter は親が repo の renderer で生成した (D1861、段 6 レビューが byte 一致を独立に再計算)。
- 段 1 の親の暫定案「役割定義を変えず K0 の critic 還流と兄弟 key を別項目へ送る」は、段 3 の相談 2 本がそろって反対し、親も real と判定して撤回した (設計 insight §2.7 が K2 限定を既に指摘し K0 への拡張を単位 4 に含めていた。親の「裁定時に未見」は不正確だった)。前例 (commit `4bd962643`) と同じ分担で planner-v4 と coder-v4-autonomous を改訂した。
- 段 5 の Codex 子 3 本は sandbox で試験を 1 件も実走できなかった (`tools/run_tests.py` は qstat の preflight で rc 16、直接の pytest は login の hook が拒否)。焦点走 1 回目 (統合 commit `16ee35040`) は 3,631 passed / 10 failed で、赤はすべて本 wave の新規試験 (fixture・注入位置の誤り 7 件、実装 3 件)。既存試験の回帰は 0 件。fix 後の焦点走 2 回目 (`a4f7a2323`) は 3,645 passed / 0 failed / 18 skipped。
- U-A の fix 1 巡目の子は「本 wave が足した試験の期待値そのものが誤り」(K0 の authority を policy 束縛用の context にまで要求していた) として停止した。親は試験側の誤りと再裁定し、評価へ渡す context だけを検査する形に直させた (既存 test の期待値は変えていない)。
- 棄却した所見: 段 6 レビュー B の nit 2 件 (台帳 `append` を B-5 から継承できる、生成器の未使用の設定引数)。成果物を変えないので採用しなかった。
- 変異: probe (全件 SURVIVED 期待) で 26 件すべてが名指し試験に帰属し、観測 node を登録した本走で 26 / 26 KILLED、対照 1 件 SURVIVED。
- 計算 (D2212 項 4): 開発の検査の job Elapse は実測で焦点走 241 s・collect 8 s・単価実測 13 s・変異本走 435 s。変異 probe は受領証が使い捨て作業木と一緒に消えて実測できず、同じ runner argv の本走と同程度とみなすと合計 ≈ 0.31 node 時間。段 4 の見積り (≤ 0.99) は変異 job の単価を測らずに置いた値で、probe 後に同じ argv の 1 job で単価 (13 s) を実測してから本走を投じた。受入全走はこの記録 commit の後に走る。
- 最終の受入全走 1 回目 (tip `6c62652da`、tested main `fb12a492b`、13:29〜13:39 JST) は 10,998 件中 1 件の赤で止まった: `orchestrator/tests/test_plain_runner_coverage.py` が、U-A の新規 test 2 本 (`test_t2849_loop_entry.py`・`test_t2853_trace_preservation.py`) に自走 harness も allowlist 記載も無いことを検出した。本 wave 起因 (F42 の再発、failures fragment)。U-A の fix 子が 2 本へ同形の自走 harness を足し (試験の本体・期待値は不変、production 不変なので変異の結果は変わらない)、受入を取り直した。
- 並走との調整: [T-2853] (2)(3) の wave と「同じ項は後から land する側が main を取り込んで統合する」と取り決め、相手の land (`a2c2d2976`) 後の本文を base にした。

## 次の一手差分

### 更新

- [T-2849] **P1 (VLDB 差分分析 P2: 公平な比較基盤と第 2 プロトコル)**: 設計は D2220 と insight
  `output/insights/2026-09-22/t2849-comparison-harness-design/README.md`、(1) 実装 (単位 1〜7、S1 = silo の backoff 値空間) は {{D:t2849-harness-impl}} と insight
  `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md` で済んだ (系列 driver `orchestrator/campaign/t2849_comparison_harness.py`、生成器
  `t2849_generators.py`、K0 巡 tool `tools/t2849_llm_round.py`、job body の harness 分岐、参照 genome の入口 `--reference-genome`)。残りは 2 つ。
  (2) MOCC の差し込み (単位 8、pin の前進と MOCC の動作点の較正の後、設計 insight §9)。(3) 第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload、検証だけで約
  8〜16 node 時間、準備・build・性能測定は別)。有限空間だけで LLM が負けてもコード合成一般の結論にしない ([T-2848] が要る理由)。S1 の試走の規模・予算・比較の族は
  [T-2850] の事前登録 (D2231) が定めた。BO の失敗集合に候補起因の `rejected-preprocess`・`bench-aborted`・`aborted` を含めるかは試走の発効束で決める (実装は設計
  §3.2 の列挙どおり Tier0・build・anomaly だけ)。完了 = 5 手法が同じ口で走る基盤 (S1) と第 2 プロトコルでの疎通。計算: 1 タスクの job 合計が 2 node 時間以上なら、
  job Elapse の実測単価で見積りを示してユーザー確認後に投入する (D2212 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P2。
  base: b305bbf2af04eddb0ec09068d9bd91703f53b63e85a242a7ae14d48c25f22049
- [T-2853] **P1・(1) の保全口と (2)(3) 済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`、**(2) job dir にだけあった論文根拠データの写し (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/`、sha256 全件一致) と (3) 系列ごとの実行手順・R1 の入力一式は `output/insights/2026-09-23/t2853-repro-package-archive/README.md` で済んだ。(1) の標準評価経路の trace 保全口は {{D:t2849-harness-impl}} で入った** (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in、検証 1 反復の一時 dir を cleanup の前に file ごとに zstd で保全し inventory を書く。未設定なら挙動不変、保全の失敗は原本を残し評価結果を置き換えない。insight `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md`)。残り: (1') 保全口の inventory は file ごとの sha256・bytes・行数、workload flags、genome、trace binary の sha256 までで、R1 の入力一式の残り (verifier の argv・repo commit・pin・patch・verifier module の sha256) を D2160・B-8 の runner と同じ組で残す部分は未実装。今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、保全口の opt-in を有効にする実行経路とあわせて入れる。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5) 主要図の再実行は図ごとに「描き直し / R2 / 独立探索のやり直し」を決めて node 時間を積み上げ、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。新しく論文根拠になった job dir は、実験と並行で同じ手順 (保存先 `tools/`) で写す。
  base: 48e55d7638d8ac3697af04e7007adc5989715c4ee0d2194dbca743e423fe1c6c
- [T-2797] **P2・裁定済み (D2227 項 2、本走を認可) → 発効 commit → 校正 job → 本走 117 job (AI)**: 発効束 draft
  (insight `output/insights/2026-09-22/t2797-effect-bundle/README.md` §1、束 `bundle/b5-effective-bundle.draft.json`) どおり、k = 3 (W 63,777 s / W_stock 16,341 s)、
  総 wall 上限 = 試走 job Elapse 総和 61,261 s × 40 = 2,450,440 s (≈ 680.7 node 時間)、D39 決定 2 の改訂 (B 10 / A 30、3,600 s 上限と収束停止の不適用) を承認済み。
  本裁定が D2212 項 4 の計算確認に当たる (見込み 360.8〜465.9 node 時間、A = 30 使い切りの試算 621.9)。手順: 発効 commit (draft の status と effective 節だけを変える) →
  発効 commit の固定 checkout で校正 job (`orchestrator/tests/test_b5_tier0.py::test_live_*`) → 本走 117 job (3 block × 3 stage、同時 LLM 系列 4、親は 1 系列 1 session を
  `claude --model claude-opus-5 --settings bundle/b5-parent-settings.json` で起動、手順は `bundle/b5-llm-parent-template.md`)。総 wall が上限に届きそうなら止めて再確認し、
  上限に達したら n や正しさ条件を下げず未完走の比較を対称に判定不能として終える。承認対象は発効束が列挙する commit と発効 commit だけ (D2222 項 1)。
  [T-2850] の設計で B-5 と 5 手法比較の関係を整理する (標本は混ぜない、D2220)。**発効 commit は T-2797 wave の land commit を親にして作る。** 束の `files_sha256` が
  束縛する `orchestrator/campaign/p3_s4_loop.py`・`orchestrator/campaign/pipeline.py`・`tools/pegasus/p3_s4_loop_pegasus.sh`・`.claude/agents/planner-v4.md` は
  {{D:t2849-harness-impl}} の wave が変えたので、それ以後の local main 先端で作ると束の sha と食い違う。
  base: a9bc5c52f229bc1cab6ac205a58ad0ea38f3169154df24a88e1f1f98e5388873
