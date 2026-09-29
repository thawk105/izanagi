# [T-2867] 段 1 brief — silo-function-policy 生成器対照の実装と生死確認 (親、2026-09-29)

起点: local main `035fc11fa`。依頼逐語: `verbatim/request.md`。事前登録の草稿 (未発効): `docs/silo-policy-generator-contrast-preregistration.md` (以下「草稿」)。

**研究前進:** 論文の「なぜ LLM か」の図 (関数単位の空間で LLM×C++・LLM×IR 対 random×IR・進化×IR を同じ評価数上限で比べる、D2259・D2272 項 4) を回せる実装を着地させ、段階 F の生死確認 3 本 (LLM×C++・LLM×IR の実 LLM 1 iteration、機械生成 IR の 1 評価) の job Elapse で草稿 §11.3 を取り直し、§12 の発効束を埋めてユーザーの規模判断 (n = 12 / 10) に返す。完了判定 = 実装の land + 生死確認 3 本の成立 (各系列で job 1 と評価 1 が計測 dir の WAL で終端) + 取り直した見積り。これは [T-2892] と T-2850 の再提示 (D2277 項 3) の前提でもある。

**scope (草稿 §5 の 1〜7 と段階 F):** (1) 政策 driver: 系列ごとの campaign identity、停止規則の切り離し (対照の経路だけ)、機械生成 IR の口 (auditor なし、D2214 項 8)、初期点 2 個 (IR `0000`・`0001` と同じ方策)、stock と静的 10 µs (元の適用方法) の口、同時検査の key (D2251)、session の分類、job body の対照 mode。(2) G_rand と (1+1) 進化 (草稿 §4.4・§4.5)。(3) 系列制御 (台帳・A/B の計上・次の単位の導出・endpoint) と起動器 (login、1 評価 1 job、429 保留)。(4) LLM の round tool と親の指示文 (1 原提案ごとの新 `claude -p` session)。(5) report (族 A・B の Holm、草稿 §7.4 の判定順)。(6) 生死確認と見積りの取り直し、草稿 §11.3・§12・§15 の更新 (草稿 §0 の起草版の規則)。runbook と `tools/pegasus/README.md` への対照 mode の手順の追記 (最小)。

**確定済み裁定:** D2272 項 4 (4 arm は決定、系列数は発効時にユーザー)、D2263 (草稿)、D2258 (実行契約は規則として継承)、D2281 (計測は iteration ごとの計測 campaign、claim leaf 不変)、D2256 (gate の順・coder 入力の firewall・LLM 候補は全件 auditor)、D2270、D2251、D2214 項 8、D2212 項 4 (1 タスク 2 node 時間以上は確認)。**未裁定を先取りしない:** T-2881 (通常 loop の予算の数え方) — 通常 loop の `check_stop` の挙動は変えない。T-2870 (auditor.md の出力節・`leakproof_context` の改訂) — role 定義と固定文脈は変えず、auditor の閉じた出力形は round tool の prompt に書く (runbook §1(d) と同じ)。

**不変条件:** 規律 2 — 全 arm の全候補・初期点・再計測は同じ gate と pipeline (検疫 → 構文 → 単独 TU → [LLM 由来なら auditor] → 書込 → digest 再照合 → trace build → legacy verify 1 + 性能構成 verify 5 → trace-disabled bench)、anomaly は即 reject で B を消費、機械生成を LLM 生成と偽らない。LLM arm の系列では機械生成の口を拒否する (初期点の登録 IR だけ全 arm で可)。規律 1 (性能値は trace-disabled build)。規律 6 (LLM 出力・critic 出力はデータ)。coder 入力は driver の `--emit-coder-input` の出力だけ。既定 (対照でない) の driver の campaign identity と挙動は bytes 不変。LLM の親はサブスクの `claude -p` だけ (API キー・代替 provider なし)。偵察の点 ID・比を生成器・LLM に渡さない。v1 の preimage で引く値は発効前に誰も見ない → 試験と生死確認は別の版文字列 (cohort) を使う。新しい gate・検査・汎用化・互換層を足さない (DW-G05)。

**成果物の形:** コード + テスト (Codex author)、生死確認の証跡 (insight `output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md`)、草稿の §11.3・§12・§15 の更新、runbook の最小追記、spool fragment (worklog・decision)。

**分割方針 (段 2 で interface を先に固定し、所有 path 素集合で並列):** U1 driver (`orchestrator/campaign/p3_s4_loop_policy.py` + test)、U2 job body (`tools/pegasus/p3_s4_loop_pegasus.sh` + test)、U3 生成器 (新 module + test)、U4 系列制御と起動器 (新 module + 新 tool + test)、U5 round tool と親 (新 tool + 指示文 + test)、U6 report (新 module + test)。U1 の CLI・台帳 schema・単位 file の形を段 2 plan が固定し、U2〜U6 はそれを前提に書く。

**受入・実測環境:** 受入・焦点走は Pegasus (`tools/dev_wave_wait.py acceptance`)。生死確認は AI worktree 容器の外の submit checkout (job dir 下、detach + submodule 初期化 + hydrate + lock、系列 C の `make-submit-tree.sh` の形) から qsub。LLM の親は login node の `claude -p`。計算投入は見積り (約 3〜3.5 node 時間 = 生死確認 ≈ 1.5 + 検査 ≲ 1.9) を示してユーザー確認後。

**(P1) 親の provisional 裁定・攻撃対象:** 全ての計測 slot (job 1 の stock・初期点 2、評価、score の各 session、参照の各 session) を、系列 cfg に slot 座標を足した slot ごとの計測 campaign で測る (D2281 の拡張)。機械故障の retry は attempt 番号を変えて新しい claim を取る。
**(P2)** 系列 identity は対照の座標 (cohort・arm・系列番号) を search_config に足した形で、対照を指定しない既定の cfg は bytes 不変。
**(P3)** job の中身は 1 つの単位 file (launcher が書く) で指定し、job は起動時に「台帳から導いた次の単位」との一致を確かめる (草稿 §5.6)。単位の種類 = job1 / eval / score / reference。
**(P4)** 機械生成の候補は proposal の形を LLM と分け (`generator` の provenance 付き)、auditor を要求しない。系列の arm が LLM なら機械生成を拒否 (登録初期点を除く)。
**(P5)** critic への入力は、前回の critic 以後に増えた slot の計測 campaign の digest と、その slot の本文・同 job の stock。系列 dir の履歴 (`policy_history.jsonl`) は初期点と候補の行を持つ (初期点は最初の原提案の前に入る)。
**(P6)** 静的 10 µs は `patches/silo-backoff-fixed.patch` + `BACK_OFF=1, BACKOFF_FIXED=10` (骨格 patch なし) を方策 driver の同じ session 契約で測り、両 build の compile command に define が 1 個ずつあることを確かめる (偵察 driver `silo_policy_recon.py` の先例)。
**(P7)** report は B-5 report の統計核 (`exact_sign_flip_p`・`_holm`・`stock_cv_floor(v2=True)`・`decide_comparison(v2=True)`) を import し、台帳の読込と系列数 n (12 / 10) と「生成不成立」の数え方 (探索点を持つ系列の数) は本対照の側で持つ。
**(P8)** 生死確認は 3 系列 (LLM×C++・LLM×IR・random×IR、各 job 1 + 評価 1)。進化は計算で回さず固定入力の試験で確かめる。score・参照 job の単価は job 1 と評価の session 単価からの換算とし、そう書く。
