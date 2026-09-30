# 相談 D: 高速化・削除計画への最強の反論

原則この brief だけで答えること。repo の広い探索はしない。裏取りは最大 5 件。20 分以内に返す。確信の無い点は「未確認」と書く。読み取り専用。日本語で、平易に。

## 背景 (brief 作成者が repo から確認済み)

- izanagi: ワークロード特化の並行性制御 (CC) を AI が合成・選択する研究 repo。main 8fe87f852。
- 2026-09-29 ユーザー裁定: 対話型の dev-wave (1 タスク=1 背景 AI セッション、repo に結果と失敗を溜め次の wave が読む) を研究の主経路に正式採用。論文 (VLDB EA&B: P0〜P6 + TPC-C) 優先。8c (無人多世代ループ) の目標と「未達」は残す。8b/8c の official 系列 (凍結・批准・受領証・予算束縛の手続き) は 2026-09-21 から論文の必須経路外。
- 同日のユーザー依頼 (逐語):「この裁定で進めるにあたって、日常の営みを高速化できるところは高速化しておきたい。不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいようにするとかさ。」「ちなみに、izanagi/readme.mdとかも更新する必要あるよね」
- 絶対規律 (人間のみ変更可): 正しさゲートを緩めない (規律 2)、verifier は毎反復で構造化シグナル (規律 3)、測定記録は現行コードとの差だけで無効にしない (規律 7) 等。実装面の変更は Codex author 必須 (D95)。
- 実測: dev-wave 1 本平均 154 分 = 無活動残差 28%、受入 (門番待ち 15% + 走行 13%、docs wave の門番待ち平均 48 分)、変異 probe+final 12〜24%、Codex 子 16%、login 検査 2%。受入全走の実 wall は直近 1 例で約 14 分 (ユーザー裁定の上限は最悪 5 分、未達)。48 worker。所要台帳 26,614 nodeid / worker 時間 16,048 秒 (競合下の丸め値、相対比較用)。
- 既裁定: D1990 (09-14)「repo 膨張は削除可能な不要物ではない、安いテストを消しても効かない (<0.01s の 12,223 件で 25.8 秒)」。D1989「削除は参照 4 分類で現役拘束 consumer 無しが条件」。D2179「一回限り tool の削除は 実施済み・結果凍結済み・現行機構の実装でない の 3 連言、専用 test が本当に専用であること」。D700「T-080 stub-free E2E は opt-in 撤去し受入で常時実行、削除案は受理集合が縮むので却下」(当時 11 nodeid の call 合計 492 秒、最長 51 秒)。D335「成長比例 test は削除せず恒久保留、解除はユーザー明示命令のみ」(保留 50〜63 node、所要 0 秒)。D440 等の権威判定器 (check_acceptance_reds) は止めない。output/ の削除は `output/PRUNED-INDEX.jsonl` (path・blob・size・最後に存在した commit・分類・理由、`git show <commit>:<path>` で引く) が既定。docs の削除は git-history-only 化 + 墓標 `docs/archive/README.md` の先例。
- 調査で得た候補 (sonnet 調査役 3 本、read-only):
  - テスト: s8b 系 44 file が台帳の 37%。T-080 stub-free e2e 群 (test_s8b_oracle_driver の約 20 関数) 約 3,566 秒・shard-0 律速 (D2242)。test_s8b_floor_campaign の official/pilot_resume 系 25 関数約 1,574 秒 (同一 setup 重複、論文 A-1 が一部関数を使うので公開 preflight・pristine 検査は残す)。`orchestrator/submission_gate/` は tests 以外から import 0、test_t338_submission_gate_unit1..5 + test_t139_submission_path 約 790 秒。B-4 の p3_b4_producer_auth_experiment (docstring「production 認証層ではない」) 系 test 約 1,710 秒 (B-4 本走は研究本流)。codex_reasoning_ab (T-189 実験、tool 12.7k 行 + test 17k 行、455 秒、held node 含む)。
  - ツール: 一回限り (t1434_t1222_science_slice、size/verify_paper_story_a1_balanced、strip_claude_session_trailers.sh)、8b official 専用 (acceptance_issuer_reference、acceptance_receipt_signature、s8b_budget_approval_preflight、issue_env_contract_activation、scan_env_coincidence) と各 test・docs。orchestrator の一回限り分析 (backoff 系 analysis 4 本 3.7k 行) と閉包上単独で消せる leaf 4 本 (s8b_floor_evacuation、s8b_oracle_exploration、s8b_verdict、s8c_gate_report)。pegasus 一回限り probe 群 + t810 束 (admission_registry.json・test_hooks の pin と同時編集)。8b/8c の大半の module は現役 module (buildcache、p3_autonomous_workload_trial ほか) が import しており、ファイル削除だけでは消せない。
  - 文書: docs/phase3.md 597KB のうち「見送り台帳」467KB (78%)。旧 8b/8c runbook・設計 (8c-wiring-design は参照 0、s8b-budget-approval-user-turn.md は参照 0)、search-repetition-trial-preregistration 系 4 本。MEMORY.md (AI の自動記憶索引) 28KB が毎セッション常駐。
  - 毎回走る CLI: check_docs.py wall 68〜98 秒、うち backlog guard 65%・Lustre stat 29k 回、docs 規模比例。check_ai_provenance.py 全史 13,481 commit 走査 1 分 56 秒 (commit 数に線形、D254 権威)。
  - 手続き: 変異 matrix は「実装差分ゼロ」以外で必須 (D95/D237/D301)。門番 (load/leader 数で投入時刻を選ぶ sleep loop) は正しさを担わない (D2148 項 12)。docs-only wave も受入全走必須 (DW-S04)。
  - 並行 wave `dev-wave-land-cleanup-enforce` が tools/dev_wave_cleanup.py・tools/check_docs.py・hooks/・.claude/settings.json・test_hooks.py・test_check_docs.py を編集中。他に 15 本前後の研究 wave (Cicada/VHash/MOCC/TPC-C/silo-policy) が稼働中。
  - D2172 が 09-20 に一度棚卸し済みで check_silo_validation_isolation.py・mocc_g2_repro_ledger.py・s6_proposal_rounds_power.py は残す裁定。

## Claude (親) の計画案

削除の記録: repo 直下に `pruned/` を新設し、wave ごとに `pruned/<日付>-<slug>.jsonl` (output/PRUNED-INDEX.jsonl と同じ schema: path・blob・size・最後に存在した commit・分類・理由・関連 D) を 1 本置く (並列 wave の追記衝突を避ける)。`pruned/README.md` に `git show <commit>:<path>` / `git log --diff-filter=D -- <path>` の引き方。docs は既存の墓標方式も併用。README.md から pruned/ を案内。

wave (外出し投げ文、編集面を分ける):
- md_1 (docs、今すぐ): 裁定の decisions fragment、roadmap §1・§2 の協議改訂 (in-place)、README.md 更新 (研究の進め方の節新設、層2 は現在 human-supervised・無人多世代ループ 8c は未達の目標、pruned/ 案内)、`pruned/README.md` 新設。
- md_2 (今すぐ): 一回限り tool + 8b official 専用 tool と専用 test、それらだけを説明する docs (D2179 の 3 連言と専用性を現物確認)。
- md_3 (今すぐ): `orchestrator/submission_gate/` と t338/t139 test、orchestrator の一回限り分析 4 本、leaf 4 本と専用 test (test_ccbench_spawn_sites の pin 同時更新)。
- md_4 (cleanup-enforce wave の land 後): pegasus 一回限り probe + t810 束 (admission_registry・test_hooks・test_pegasus_tools)。
- md_5 (docs、今すぐ): phase3.md の見送り台帳を docs/archive へ移し見出しだけ残す、参照 0 の旧 8b/8c 文書を git-history-only 化 (墓標)、旧 runbook の archive 退避。凍結 bytes・hash 束縛のある文書は動かさない。
- md_6 (ユーザー裁定後): T-080 e2e 群と floor_campaign の official 系重複 setup を削る (D700 を上書き)、B-4 producer_auth_experiment 系と T-189 codex_reasoning_ab 束の削除 (held node の解除を含む)。
- md_7 (ユーザー裁定後、cleanup-enforce land 後): check_docs の高速化 (stat/読取キャッシュ、backlog guard の計算量)、変異 matrix を「test・gate を新設/変更する wave」に限定、門番待ちに上限 (例 10 分で投入)。
- 見送り: 8b/8c module の切り離し設計 (8c の目標は残るので触らない)、check_ai_provenance の増分化 (D254 権威、別途)、D335 の保留 test (所要 0 で得るもの無し)、MEMORY.md 圧縮 (AI 自身の運用で別途)。

ユーザーへ諮る裁定案: R1 = D700 を上書きし T-080 e2e と重複 setup を削除 (推奨: 削除。旧系列の手続き検査で正しさゲートではなく、凍結記録の完全性検査 ratified_verify 等は残す)。R2 = B-4 producer_auth_experiment 系と T-189 束の削除 (推奨: T-189 は削除、B-4 実験は本走が使わないことを確認して削除)。R3 = 変異 matrix の限定と門番待ち上限 (推奨: 両方採用)。

## 求める回答
- この計画を**通してはいけない理由を最も強い形で**作ること。特に: 正しさゲート (規律 2) を実質的に縮める削除が紛れていないか (T-080 e2e、floor_campaign、B-4 実験、変異 matrix の限定、門番上限)、規律 7 (記録の完全性・凍結 bytes の束縛) を壊す文書移動、D700/D335/D1990/D2179 との矛盾、削除して速くならない項目への工数浪費、並行 wave との衝突、8c の目標を残すと決めたのに 8c の資産を消している箇所。
- **攻撃が成立しなかった項目は正直にそう書くこと。全項目を無理に成立させない。**
- 最後に、攻撃を踏まえた修正版の計画を短く (残す項・落とす項・順序)。
