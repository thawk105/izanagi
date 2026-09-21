# 段 4 裁定 — Silo の関数単位合成空間 (2026-09-21 22:1x JST、基準 main 36fb14a3d)

- 入力: 段 2 草稿 `codex/s2-plan.md`、段 3 レンズ A `codex/s3-consult-A.md` (adopt_with_conditions)、レンズ B `codex/s3-consult-B.md` (adopt_with_conditions)、auditor `codex/s3-auditor.md` (adopt_with_conditions)。3 レンズとも条件付き採用。
- 裁定 inbox 再走査 (22:07): wave 開始後の更新は `2026-09-21-rulings-full30-verdicts.md` だけで、本題に触れる項なし。VLDB 方針の控えは写し (`verbatim/vldb-direction-verdicts.md`) と byte 一致。
- 実装しない (設計 wave) ので 4→7→8→9。実装面の差分ゼロ → 変異 matrix 免除、受入全走は実施 (DW-S04)。
- 裁定の前提を親が実コードで確認: `validationPhase` は write set を sort してから `lockWriteSet` を呼ぶ (transaction.cc:407 付近) → 上限付き待機でも deadlock なし。`read_internal` は lock が外れるまで spin する (transaction.cc:255) → lock を漏らす骨格誤りは既存 `trace-timeout` に落ちる。式中の `TRACE` 参照は `_trace_pair_diff` (TRACE=1/0 の preprocess 差) に差分行として現れる → 既存 diff-of-diffs が捕まえる。

## 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 判定 | 採否・処置 |
|---|---|---|---|---|
| 1 | s2・A1・B1・B8 | P2「構成上壊せない / verifier 拒否は原理的に 0」は自由 C++ の UB・外部干渉を無視 | real | 採用。安全文言を A1 の条件付き文言に置換 (決定 2) |
| 2 | s2・B1・A1 | P4 の include 前封じ込めは不成立 (最初の CC include で std::atomic と CC 大域が同時に見える) | real | 採用。後置 + 受理契約 + 単独 TU compile (決定 3・4) |
| 3 | B3・A2・auditor V1/V2/V4 | 受理契約が未確定 (許可リストか禁止リストか、保存域、局所の配列・pointer・UB) | real | 採用。部分言語 policy-C++ v1 を設計で固定 (決定 4) |
| 4 | auditor V3 | 骨格 helper と同じ namespace での overload・演算子による名前解決の乗っ取り | real | 採用。helper は別 namespace・完全修飾・組込型比較、hole 側は演算子・template・namespace 操作を禁止 (決定 3・4) |
| 5 | auditor V1 (TRACE 判別部分) | `if (TRACE)` で verify だけ正しく振る舞う | 部分 refuted | 式中の TRACE は既存 diff-of-diffs が差分行として捕まえる。大域・trace 関数への到達は real → 単独 TU compile で閉じる |
| 6 | auditor V5 | hook 内 loop・再帰は lock 保持時間を任意に延ばす | real | 採用。v1 は loop・再帰・goto 禁止 (決定 4) |
| 7 | B2・A4 | lock 周回上限の判定位置が CAS 失敗を数えない | real | 採用。内側ループ先頭で数える (決定 7) |
| 8 | A4・auditor V5 | 上限付き待機を明示の軸にすることは型 10 と同じ害 | refuted | wait 自体は禁止しない。残る convoy・偏りは性能側の限界として明記 |
| 9 | A5・A6・B9・auditor「依頼 4」 | 状態の射程 (txn 内 / worker 内の txn 間 / 共有 / 時刻) | 択一 | **worker 内の txn 間履歴を採用** (骨格所有の唯一の状態 + 成功通知)。共有状態・時刻は v1 に入れない (決定 5) |
| 10 | auditor V6 | hook ごとの実行証拠 (型 4) | real (C 段の機構試験に限る) | C 段の焦点試験は試験専用 probe build で各 hook の発火を示す。候補ごとの TRACE 計数 + PIN 前進は見送り (発火条件付き、決定 9) |
| 11 | auditor V7 | 軸 ON が no-wait flag を黙って上書き | real | 採用。軸 ON で `NO_WAIT_LOCKING_IN_VALIDATION != 1` または `NO_WAIT_OF_TICTOC != 0` なら `#error` |
| 12 | auditor V8 | abort 要因の写像が未定義 | real | 採用。既存 trigger 骨格の 7 記録点へ全点写像 (決定 8) |
| 13 | auditor V9・V10、A8 | 負例が実体を名指ししない、積み直した broken patch が軸 OFF 側に着地しうる、待機方策で検出力が変わる、再読込削除は timeout にならない | real | 採用。C 段の負例を実体名指しで事前登録、軸 ON 経路に載った証拠、2 方策の下で走らせる (決定 9) |
| 14 | auditor T3 | 候補ごとの sanitizer harness | 不採用 | 部分言語が OOB・signed overflow・未初期化・非停止を構造的に除き、残る shift / 除算は字句規則で閉じる。発火条件付きで見送り (決定 4・9) |
| 15 | auditor T5(d) | 新 X 理由 `lock-held-at-abort` | 不採用 | 読み手の spin で既存 `trace-timeout` に落ちる (親が確認)。新しい検査は足さない |
| 16 | auditor V11 | per-worker commit 分布の記録 | 見送り | CCBench の結果出力は ALLOWLIST 外。公平性非保証を明記し、既存の残存リスク (D41 条件 3) に発火条件を付けて残す |
| 17 | A9 | 自由文 (justification・エラー・critic 出力) の還流境界 | real | 採用。justification は記録するが critic・次 coder へ渡さない。候補本文・構造化結果・critic 診断はデータとして渡す (決定 10) |
| 18 | B5・s2 §4.4 | P6 の「同一空間比較」は誤り、arm が不足 | real | 採用。比較 A (同じ IR) と B (C++ 空間拡張) を分け、最小 arm = 非 LLM×IR・LLM×IR・LLM×C++ (決定 11) |
| 19 | B6 | BO は repo に既存なし | real (nit) | BO は最初の結果の必須にせず後段 (P2) へ |
| 20 | B7 | 見積りの単価を上限と呼ぶ誤り、59% の分母 | real | 採用。「旧単価によるシナリオ換算」と表記、分母は subprocess wall 53,805 s (決定 14) |
| 21 | B10 | C 段出口が E 段の driver 出力に依存 | real (nit) | 採用。C 出口から E 依存を外す (決定 13) |
| 22 | B11 | sort permutation 負例の全走・read-validation 再較正・一般 UB 網羅は v1 必須にする根拠がない | real (nit) | 採用。新しい接続に効く負例だけ残す |
| 23 | B12 | 第 3 列は手順書改訂の完了ではない | real (nit) | 採用。C 前の小さな docs wave (新規 T) |
| 24 | B13 | reset 位置 `T:694` は TRACE 開始行、行番号の訂正 | real (nit) | 決定 5 で骨格 reset 自体が無くなる。行番号は insight で訂正 |
| 25 | A3 | v1 は「LLM が壊した CC 論理を verifier が捕らえる」価値を実証しない | real | 採用。研究主張の限界として明記、機構を開く後続版の前提は P0 (決定 15) |
| 26 | A6・auditor V11 | 「長い txn を後回し」は YCSB で成立しない (同じ txn を再試行し続ける) | real (nit) | 採用。飢餓は「worker の駐車」として書く |
| 27 | auditor role 更新案 | 目録に型 22〜26 と型 17〜21 段落の改訂 | 採用 (差分案) | `.claude/agents/` 変更はユーザー明示承認が要る。E 段の着手条件に残す |

## プラン v2 (設計の最終形)

決定 1 境界: 方策 (abort 後の待機量、lock 競合時の retry / abort、成功通知時の状態更新) だけを LLM が書く。validation・CAS・unlock・absent 検査・tid 生成・writePhase・trace・同じ txn の再試行は骨格。

決定 2 安全文言 (A1): メモリ安全・外部干渉なし・契約適合の方策が正常に返る限り、方策の選択は固定骨格の直列化可能性条件を弱めない。任意 C++ の適合性、全実行の正しさ、停止性、公平性を構成上保証するものではない。certified は有限の観測履歴についての判定。

決定 3 置き場と名前空間: `transaction.cc` の include 列の後。骨格型 (enum・Context・Response) は `izanagi_silo_api`、hole は `izanagi_silo_policy` の本体、骨格 helper と状態の実体は hole の後の `izanagi_silo_skel`。骨格からの呼出しは全て完全修飾、action 判定は組込型比較。

決定 4 受理契約 policy-C++ v1 (許可リスト): 型は `uint32_t` / `uint64_t` / `bool` と骨格型だけ。整数 literal は `u` 接尾辞必須。hole に置けるのは PolicyState (scalar メンバ ≤ 16、既定初期化子必須、メンバ関数なし) 1 つ、`constexpr` 定数、関数定義 (必須 3 関数 + 補助関数、定義前使用なし、自己参照なし)。文は初期化子付き局所宣言・代入・if/else・switch・return だけ。`/` `%` `<<` `>>` の右辺は literal (除数は非零、shift 量 < 32)。`static_cast` は許可 3 型へだけ。pointer・配列・参照 (固定引数形以外)・template・lambda・loop・goto・例外・記憶域指定子・namespace 操作・演算子 overload・`__` を含む識別子・先頭 `::` は禁止。機械執行は既存 DiffQuarantine + 既存 coder_effect_gate + 部分言語の構文検査 (許可リストの parser) + 単独 TU compile (hole + 固定 api header だけ、-D なし、`-Wall -Wextra -Werror`)。sanitizer は候補ごとには回さない。

決定 5 状態: 骨格が `izanagi_silo_skel` に置く `thread_local` の PolicyState 1 個を `PolicyState&` で渡す。寿命は worker thread (骨格は reset しない)。成功 commit 後に `policy_on_commit` を呼ぶ。方策は on_commit で自ら reset すれば txn 内状態を再現できる (txn 内案は部分集合)。共有状態・時刻は v1 に入れない。D48 は trigger 軸の契約として不変。

決定 6 観測: AbortContext = {abort 要因 (unset + 7)、骨格 PRNG の乱数}、LockContext = {同じ tuple での試行番号、乱数}、CommitContext = {} (空)。時刻・set サイズ・競合位置・thid・key・pointer・epoch・FLAGS・result_・quit_ は渡さない。

決定 7 骨格の待機: abort 待機は `min(返値, 1000 µs)` を骨格の busy wait で。lock は tuple ごとに試行番号 0 から、内側ループの毎周回先頭で上限 32 を判定 (CAS 失敗も数える)、方策が retry なら `min(返値, 50 µs)` 待機後に `loadAcquire` で再読込、abort または上限到達なら stock の abort 出口 (status・prefix unlock・要因記録・return)。上限は全生成器共通の試走設計値。hook 呼出しは骨格の noinline wrapper 経由。

決定 8 要因記録: 既存 trigger 骨格の 7 記録点 (lock 競合・update 対象不在・read tid 変化・read が他者 lock・node 版・insert node・scan node) へ写像、`begin()` で unset。軸 ON の CC 本来の状態 (両 build に存在)。

決定 9 検証: 比較では legacy + 性能構成の verify を全 arm に適用。新しい reject 閾値は作らない。reject 分類 (検疫・契約 / build / liveness / integrity X・P / G2) と人為的骨格負例を混ぜない。C 段の焦点試験と負例 (inert identity、honest identity、include 一致、diff-of-diffs、既存 4 負例を軸 ON 経路に積み直して即 abort 方策と最大待機方策の 2 通り、機構の変異 = clamp 削除 / 再読込削除 / 上限削除は等価変異として登録 / prefix unlock 削除 / hook 配線解除 / 要因誤記録) は試験専用 probe build で hook の発火を示す。候補ごとの TRACE 計数・PIN 前進・sanitizer は発火条件付きで見送り。

決定 10 還流: coder への入力 = 固定の接続仕様 + 自系列の履歴 (候補本文・結果分類・reject コード・verifier の構造化 digest・critic 診断) をデータとして。justification は台帳に残すが critic・次 coder に渡さない。

決定 11 表現と比較: 材料化形式 = 領域の C++ 本文、identity = genome flags + 骨格 / PIN + source_digest。型付き有限 IR (停止・算術安全を構成で保証、policy-C++ v1 の部分集合へ決定的に描画) の上で random / sweep / 非 LLM 進化 (後に BO)。比較 A = 同じ IR (非 LLM vs LLM×IR)、比較 B = LLM×C++ (policy-C++ v1) vs IR arm。最小 arm = 非 LLM×IR・LLM×IR・LLM×C++。共通条件 = 評価数 B・提案数 A・初期候補・観測・workload・verify・rep・停止・故障 retry・endpoint。

決定 12 接続: planner は外す。兄弟 driver `p3_s4_loop_policy.py` と軸定数 module (C 段)。coder role 新設 (tool なし・構造化出力)、auditor 目録の改訂案、どちらも `.claude/agents/` 変更でユーザー明示承認が要る (E 段)。build admission: IR renderer 出力は generator receipt で MACHINE_GENERATED、LLM と Codex の手書き対照は CODER_AUTHORED + CLI opt-in。

決定 13 段の順序: C 前 docs wave (手順書 §4 の第 3 列と planner 例外) → C (骨格 patch・api header・契約検査・焦点試験・負例・DW-G01 の手書き方策の生死確認) → D (IR 偵察、機械) → 人間判断 → E (driver・role、承認) → F (別セッション、LLM 系列)。C 出口は E に依存しない。

決定 14 見積り: 旧単価 (B-5 試走の固有費 217〜509 s、中央値 498 s。予算換算 510 s) によるシナリオ換算で、上下限ではない。C 段は評価 6 session 0.36〜0.85 h + 負例 8 走 (上側換算 1.13 h) + 受入 (前 wave 実績から ≤ 1.15 h) → タスク合計が 2 node 時間を超えうるので投入前に確認。D は 19 session 1.15〜2.69 h → 確認対象。最初の比較試走は 149 session 8.98〜21.1 h + LLM 48 巡 8.0〜10.4 h → 確認対象。最小の LLM×C++ 1 系列は 16 session 0.96〜2.27 h + LLM 8 巡 1.3〜1.7 h。

決定 15 研究主張: v1 は関数生成の有効率・reject 分類・費用・探索法比較を測る。「LLM が壊した CC 論理を verifier が捕らえた」ことは実証しない。機構を開く後続版の前提は P0 の検出力測定。

## 焦点再レビュー (D1409 の教訓)

決定 5 (状態の射程) と決定 4 (受理契約の具体化) は草稿からの変更。前者はレンズ B が推奨し、A と auditor が害の範囲を判定済みの選択肢だが、最終版を同じレンズで確認してから記録を固定する: 段 7 で insight 最終稿を codex review 1 本 (A・B 両レンズの閉包確認) と auditor 1 本 (決定 3〜5・9 の確認) に並列で渡す。
