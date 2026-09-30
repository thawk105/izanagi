# 段 1 brief — dev-wave-lock-order-axis ([T-2886]、gen-opt md_13、2026-09-30)

- worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis (base main 4f412c67b、CCBench gitlink C 68106660)
- 指示: /work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_13.txt と common-4.txt。仕様の正本: output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md §4 (と §11 の訂正)、関門設計 output/insights/2026-09-29/gen-opt-correctness-gate/README.md §3.1・§3.4・§7 の U3。

1. 研究前進: 段 A の試し ([T-2896]、文献の最適化「競合度順の施錠」を LLM に書かせて正しさ関門の下で測る) の入口を作る。完了判定 = 提案文字列が 検疫 → 文法 → 単独 compile (+UBSan harness) を通り、骨格 patch を当てた Silo の trace build で名前つき対照 (版が新しいほど先に施錠) が既存判定器を 1 回通り、trace 上で key 順と違う施錠順が実際に起きた件数 (発火) が 0 でないこと。[T-2888] (U5 driver 接続) の前提が満たされる。
2. scope: 新軸 (仮称 silo-lock-order-policy) の (a) API header、(b) 受理文法 (policy-C++ v1 規則、表だけ新軸)、(c) 単独 compile と UBSan harness、(d) 検疫 → 文法 → compile を 1 か所で掛ける gate 関数 (既存 policy_gate と同形、driver 本体は変えない)、(e) 骨格 patch (validationPhase の sort 1 か所、INSERT/DELETE を含む取引は stock sort、inert)、(f) build 変数の登録 (condition_meaning_gate の表へ追記)、(g) 名前つき対照の手書き方策 1 本、(h) test、(i) 生死確認用の使い捨て driver (repo 外、Codex author)。
3. scope 外: driver 接続 (U5)・codex_roles/policy.py の axis 固定・小モデル関門・性能比較・D1/D2 照合 (md_14)・関数方策 patch との同時適用・coder 向け spec md (U5 で作る)・計数専用 instr patch。
4. 確定裁定: D2305 (計算を使わない関門実装は並行で進める)。md_13 の計算は 2 node 時間未満なら確認不要。common-4 §2: md_13 は新しい軸の file と既存の検疫・文法の分岐への最小の追加だけ、方策 driver 本体 (p3_s4_loop_policy.py) と生成器対照の部品 (silo_policy_contrast*.py) は変えない。共有の登録簿は追記だけ。
5. 不変条件: (i) 既存 4 軸 (backoff・sort・trigger-gating・silo-function-policy) の受理集合を変えない — 既存 test を無変更で緑、加えて既存文法の正例負例 corpus で決定一致を示す。(ii) 規律 1: SILO_ORDER_VARIANT=0 で前処理後 bytes が stock と一致 (source_digest.resolve == STOCK)、TRACE=0 の性能 build に新しい記号や計数を残さない。(iii) 規律 2: 候補は pointer・handle・key・集合・trace・counter・同期・sort の名前に到達できない (許可リスト、表に無い名前は拒否)。(iv) SILO_ORDER_VARIANT=1 は NO_WAIT_LOCKING_IN_VALIDATION=1 と NO_WAIT_OF_TICTOC=0 を #error で要求。(v) 比較は (prio 降順, storage 昇順, key 昇順) の全順序で骨格が行い、TID word は 1 要素 1 回 loadAcquire。(vi) 既存 P 行 (pre/post sort の多重集合検査) は hole の外で変えない。
6. 成果物: 新規 file 群 + 追記、test、patches/silo-lock-order-variant.patch (仮名)、patches/README.md 節 (親)、一次資料 output/insights/2026-09-30/gen-opt-lock-order-axis/README.md (親)、spool worklog fragment (親)。
7. 実測環境: login で文法・compile test、受入は tools/run_tests.py dispatch。生死確認は既登録の tools/pegasus/dispatch_compute.py --task generic で repo 外 driver を 1 job (見積り 0.2〜0.3 node 時間、2 未満)。新 Pegasus 実行体は作らない (F660)。
8. 分割方針 (段 5): 単位 A = 文法・API header・compile/UBSan・gate 関数・axis 定数・手書き対照・その test。単位 B = 骨格 patch・condition_meaning_gate 登録・template test (inert/前処理/#error)。単位 C = 使い捨て生死確認 driver (repo 外)。A と B は所有 path 素集合。C は A・B の統合後。

親の provisional 裁定 (攻撃対象):
- (P1) 文法は silo_policy_grammar.py を「profile (表の束) を引数に取る」形へ最小改造し、既定 profile で既存挙動を完全に保つ。代案: 新 module に parser を複製 (重複 600 行)。既存 module に hash 固定は無い (git grep で確認)。
- (P2) 検疫は p3_s4_loop.quarantine の汎用経路 (構造検疫 + coder_effect_gate) で足り、同関数に分岐は足さない。文法・compile は新軸の gate 関数で掛ける。
- (P3) 骨格 patch は stock (C 68106660) に単独で当て、silo-sort-variant.patch とも silo-function-policy-variant.patch とも同時適用しない (排他は axis 定数と test で明記)。
- (P4) 発火の証拠は trace の W 行の key 順から数える (新しい計数 patch を作らない)。W 行が施錠順で出ることを段 2 で現物確認する。
- (P5) condition_meaning_gate の表に SILO_ORDER_VARIANT を inert_values=("0",) で追記し、表を固定する既存 test の期待集合に 1 entry 足すことを段 4 で個別に許可する (他の期待値は変えない)。
- (P6) 名前つき対照の置き場は orchestrator/campaign/silo_lock_order_hand/ (関数方策の hand dir に倣う)。
