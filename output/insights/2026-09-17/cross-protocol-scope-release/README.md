# Silo 固定スコープの解除 — cross-protocol 対応を可能にする裁定パッケージの一次資料 (2026-09-17)

- wave: `dev-wave-cross-protocol-scope-release` (branch `worktree-dev-wave-cross-protocol-scope-release`、docs のみ、実装面 0 byte)
- 起点: ユーザーの `/dev-wave` 引数「今もスコープはsiloベースに固定されている？それ解除した方が良いのでは？」
- 決定の記録: `docs/phase3.md` の「2026-09-17 改訂」節と decisions (本 wave の fragment を fold が採番)
- 逐語: `verbatim/` (親 brief、段 2 plan、段 3 レンズ A / B、段 4 裁定、各 prompt)。行末空白のみ可逆に正規化、内容は無変更
- 計測: なし。本 wave は測定も build も行っていない

## 1. ユーザー発話 (逐語、裁定の一次資料)

1. 引数: 「今もスコープはsiloベースに固定されている？それ解除した方が良いのでは？」
2. 補足 1: 「2026-07-27の裁定かな」
3. 補足 2: 「今の所論文のパンチが弱いから、クロスプロトコル対応を可能にしておいた方が良いのかなと思う。他方、クロスプロトコルの道具としてccbench側に近年の新しい手法を追加するとかも優先度高いかなぁ」

**発話が決めたのは方向 (Silo 固定を解除し cross-protocol 対応を可能にしておく) だけである。** pin 前進の再承認、A→B の厳密な順序、C-1 の論文必須化までは承認していない。これらは段 4 で親が起草した具体化であり、取消し可能。

## 2. 「今も固定されているか」への答え — 3 面とも固定されていた (wave 開始時点)

| 面 | 現物 | 状態 |
|---|---|---|
| 裁定 | `docs/phase3.md` 2026-07-27 改訂 (1) (「スコープを Silo ベースに固定する — …複数プロトコルから選ばせる問題設定は当面採らない」)、原文 = archive worklog 2026-07-27 (25) のユーザー裁定 8 件 | 失効宣言なし。2026-08-11 裁定 (T-755 Q1〜Q3 (a)) で成立方法は確定、D1360 (2026-09-01) は「残るのは実装」 |
| 実装 | genome 空間: tictoc / cicada を [T-2135] (2026-09-02) で登録 (`orchestrator/campaign/genome.py` の `TICTOC_SPACE` / `CICADA_SPACE` / `SPACES`)。floor driver: `orchestrator/campaign/between_run_floor.py` の `BASELINES` は protocol 別辞書 `{silo, mocc}`、tictoc は引数解析で拒否。層 3: `orchestrator/campaign/layer3_report.py` が protocol を照合 ([T-2115]、2026-09-01)。編集面: `orchestrator/campaign/source_digest.py` の EBS / ALLOWLIST に `cc/mocc/transaction.cc` (trace-hook 専用、D579)。較正: mocc / tictoc 各 2 件 (rr50 / rr95) accepted、within-run floor は用途限定で登録 (D2083)、cicada は 0 件 | between-run floor は D1373 の関門で未実測 (mocc hook が現行 pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` の祖先でない)。非 Silo (mocc / tictoc / cicada) の性能比較は 0 件。mocc は変異探索面外 (D579) |
| 論文 | `docs/paper-story/2026-09-17.md` §1「2026-07-27 のユーザー裁定でスコープは Silo ベースに固定されている」、§8 C-1「Silo ベースに固定した以上、現在の論文の必要条件ではない」 | C-1 は将来スコープ (C 群) |

**親 brief の誤りを段 2 / 段 3 が訂正した 3 件:** (1) 層 3 の protocol 照合キーは [T-2115] で実装済み (D1360 当時の「無い」を現況へ転写していた)。(2) 「文献調査は D1760 / D1931 で停止中」は一括では偽 — D2095 で軸 1 を部分再開、D1760 は通常の調査を許す、D1931 の停止は軸 3 の登録済み検索に限る。(3) D2104 項 13 に「主経路完了まで」という期限は無い。

## 3. 段 4 裁定 (要約。全文 = `verbatim/s4-adjudication.md`)

| # | 判定 | 要点 |
|---|---|---|
| P1 順序 | 修正して採用 | mocc 第 2 例の最小経路 (A) を近年手法の CCBench 追加 (B) より先行。B の候補調査は独立に着手可。完全汎用化を待機条件にしない。TicToc は mocc の必須鎖外 |
| P2 pin 束縛 | 却下 | D297 合格は SHA 束縛の置換を認めない (§5 の表)。過去の certified 判定は無効化されないが、新 pin 系列は登録・identity・凍結の更新が要る |
| P3 主張 | 修正して採用 | 増分主張は「二つの CC 実装で合成・評価手順を実証した」に限る。mocc variant 対 stock (第 2 例の証拠) と C-1 (stock 最良比較) は別項 |
| P4 roadmap | 修正して採用 | 準備着手の前倒しに限定、roadmap 本体は非改訂。selector 据置き、b2 本格投資の条件は従来どおり |

### 言えること・言えないこと (第 2 例の証拠が揃った後の上限。現時点の成果ではない)

| 階層 | 強まる範囲 |
|---|---|
| 評価器 | MOCC の名指し実装・条件にも正しさ検査と性能比較経路を適用できた (hook だけでは不足) |
| システム | 同じ合成手順で生成したなら、第 2 実装で合成から検証まで完遂した。stock 対比較だけなら評価経路の拡張まで |
| LLM 固有 | 増分なし (非 LLM 対照との差は未取得) |
| 無人自律 | 増分なし (protocol 数はセッション非依存駆動の証拠ではない) |

言えない文: 「10 protocol から workload に最適な protocol を選べる」「descriptor が合成結果の改善を因果的に駆動する」「一般の CC に対して LLM による無人合成が非 LLM 手法や既知軸最良を上回る」。**論文のパンチの主因は第 2 例だけでは埋まらない** — B-1 (既知軸最良の超越)、B-5 (LLM 固有性の対照)、A-1 (本走認可) 側にもある (レンズ A R3。本 wave の scope 外)。

## 4. 観測した候補 (D1603 材料 (1) の素材 — 採用の確定は準備 T で行う)

- hook branch: `izanagi-t1943-mocc-g2-readfrom-witness` (submodule `external/ccbench` の local remote-tracking ref)
- 先端 OID (2026-09-17 観測): `e9e477ca1b55348ab4530de0b1cf663ce4555290`
- 現行 pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` に対し `merge-base --is-ancestor` は rc=1 (非祖先)。現 pin との diff は `cc/mocc/transaction.cc` のみ、141 行追加 (レンズ B の静的観測)
- 同 OID の `cc/mocc/CMakeLists.txt` は `transaction.cc` を SOURCES に列挙し、列挙された `cc/mocc/transaction.cc` に `#if TRACE`・`trace.hh` include・`izanagi_trace::next_txid()` の 3 証拠がある = D1373 の text-level 関門を通る構造 (レンズ B 所見 3 の静的観測)。**ネットワーク到達性・D297 合格・verifier 通過・測定成功は未確認**
- 見送り台帳の旧候補 `c9c1a9c` (2026-07 承認済み) は今回の採用候補とみなさない
- 初回候補は mocc 単独。TicToc は別候補 (同じ候補に積むと `tools/check_trace0_preprocess_identity.py` の保証範囲 (SILO_SPACE の context 列挙、新規 include の特例は mocc の trace.hh 1 行限定) との適合が残件になる、レンズ B 所見 6)

## 5. pin の full SHA を束縛する物 (D1603 材料 (3) の素材 — 波及表の骨格)

| 層 | 所在 | 束縛 | pin 前進時の帰結 |
|---|---|---|---|
| gitlink / 現行定数 | `external/ccbench` の HEAD gitlink、`orchestrator/campaign/pin.py` `CURRENT_PIN` | full SHA / 短縮 7 桁 | 定数更新。歴史的 driver は自分の pin を保持 (張替え禁止) |
| 承認済み定数 | `orchestrator/campaign/s8b_approved.py` `CCBENCH_FULL_SHA` | full SHA | 承認の更新が要る |
| A-1 事前登録 | `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` / `v3-pilot.json` の `canonical_pin` | full SHA | 新登録または追補。旧登録は旧 checkout で保持 |
| A-1 source 契約 | `orchestrator/campaign/paper_story_a1_source.v2.json` の `canonical_head` | full SHA | 同上 |
| A-1 実行・consumer | `orchestrator/campaign/paper_story_a1_paired.py` (policy の固定 OID と実 checkout の HEAD を比較) | 照合 | 新 pin checkout では旧登録の実行・再解析が拒否される |
| A-2 | `orchestrator/campaign/paper_story_a2_certification.py` (evidence・campaign identity・`pin.CURRENT_PIN` を照合) | 照合 | 新系列の identity |
| campaign identity | `orchestrator/campaign/ident.py` (`ccbench_commit` を preimage に含め、保存 preimage との不一致を拒否) | preimage | 新 campaign は新 ID (content-addressed)。旧 lock の resume は拒否 = 過去判定の取消しではない |
| campaign.lock | `identity_preimage` 内の `"ccbench_commit"` | exact key | 同上 |
| source evidence | `orchestrator/campaign/source_digest.py` (`ccbench_commit` を保持) | 保持 | 新 evidence |
| 凍結 floor | `output/s8b-freeze/floor-protocols/*--511c9538….json` の `ccbench_pin` | full SHA | 再凍結の要否を確認 |
| 凍結 evidence manifest | `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json` の `current_pin` | full SHA | 歴史記録として保持 |
| 性能事前登録 | `docs/backoff-policy-performance-preregistration.md`、`docs/backoff-counterfactual-preregistration.md`、`docs/dynamic-backoff-preregistration.md` | full SHA + patch stack | erratum または新登録 |
| balanced 別事前登録 | `docs/t1998-balanced-stock-inline-preregistration.md` | gitlink full SHA | 同上 |

同一視できない物: `docs/phase3-main-experiment.md` は当該 SHA を直接固定しないが freeze に `CCBENCH_COMMIT` を含め起動時照合を要求する。`orchestrator/preregistration/` に SHA literal は無い。`orchestrator/campaign/env_contract.py` は較正 record の path / hash を固定し CCBench SHA を直接固定しない。H1/H2 系 driver (`p3_autonomous_workload_trial.py`) は base の commit を継承する — A-1 と同じ full SHA literal 固定と断定する証拠は無い。

**結論 (レンズ B (b)):** pin 前進は過去の certified 判定を遡って無効化しない (規律 7)。新 pin で継続する系列には登録・identity・凍結の更新が要る。D297 の合格はこの表の束縛を内容ハッシュへ置換する承認にならない。

## 6. 準備 T 5 本 (番号は fold が振る。いずれも superproject の gitlink を動かさずに完了できる)

| 暫定名 | 優先 | 完了判定 | 前提・注記 |
|---|---|---|---|
| cross-protocol-pin-evidence | P1 | D1603 材料 3 点が insight に揃い、見送り台帳の pin 更新項の再承認として提示できる状態。材料 (2) = `tools/check_trace0_preprocess_identity.py` による D297 検査 (前処理比較、実 build 不要、login node 可、checker の保証範囲を明記)。検査が拒否した場合も「前進可能」とは判定しない | 初回候補は mocc 単独 (§4) |
| mocc-mutation-proof-design | P1 | D579 が要求する独立の auditor-live 相当の機械実証の設計 (hole 位置、auditor 入力、X/P/I・hot/cold lock 被覆、陽性/陰性 control と期待拒否) を後続実装者が使える形で固定。設計完了で変異探索を解禁しない | チェックリスト再掲に留まるなら実証 wave の plan 段へ統合 |
| recent-cc-candidate-selection | P2 | 近年 CC 手法の候補表 (一次資料・実装可用性・ライセンス・YCSB 適合・trace 移植費用・証明面・既存 CC との差) と、追加対象・棄却理由の提示。入口 = literature map の NeurCC (2025) / ATCC (2026)。D2095 と重複取得しない。CCBench への実装追加とは分ける | A に従属させない |
| tictoc-trace-hook | P2 | submodule branch 上で `TsWord` 版 ID の trace-hook + positive / negative control、branch commit と control 証拠の保存 | TicToc の正式編集面認可が前提 (D579 の mocc 限定認可は流用不可)。push は人間 |
| tictoc-floor-baseline | P2 | `between_run_floor.py` `BASELINES` に根拠つき TicToc baseline を追加、引数解析・protocol 別出力・hook 不在時拒否を確認。完了条件に実測を含めない | 単独では測定は開通しない (hook + pin 再承認が別途要る) |

層 3 の protocol 照合キーは [T-2115] で実装済みのため起票しない。

## 7. 段 2 / 段 3 の所見

- 段 2 plan (codex read-only、`gpt-6-astra`、medium): 事実訂正 3 件、docs 改訂 8 hunk + fragment 2 件、準備 T 5 本 (pin 前進要 0 本)、P1 部分異議・P2 異議
- 段 3 レンズ A (論文価値、lane sol): 所見 13 件 (real 10 / refuted 3)。最重要 = 第 2 例合成実証と C-1 の分離 (R2)、候補 0 件は誤り (R4)、「主経路完了まで」の期限は存在しない (R8)
- 段 3 レンズ B (主経路衝突、lane luna): 所見 10 件 (real 7 / refuted 3)。最重要 = SHA 束縛は実在し D297 では置換できない (所見 1)、mocc は pin 前進だけで D1373 関門を通る構造 (所見 3)、D297 材料 (2) は実 build 不要 (所見 4)
- 両レンズの P1〜P4 判定は一致 (修正して採用 / 却下 / 修正して採用 / 修正して採用)
- 親が現物で検算した plan の主張: `BASELINES` の鍵集合、層 3 の protocol 照合、[T-2115] / [T-2135] の archive 実在、D2095 の内容、A-1 事前登録の `canonical_pin` (すべて一致)
- 段 6 レビュー (docs 差分への敵対レビュー 1 本、`verbatim/s6-review.md`): must-fix 3 / nit 2、裁定との実質的な不一致なし、fragment 文法違反なし、凍結版 2026-09-17.md の変更なしを確認。対応表 (親が是正案を逐語で適用し、grep で照合):

| 所見 | 対象 | 対応 |
|---|---|---|
| M1 発話の加工要約を直接引用として記録 | `docs/phase3.md` 2026-09-17 改訂節 冒頭 | closed — 「Silo 固定の解除を問い、…方向を示した」へ置換、逐語は本 insight §1 を指す |
| M2 「plan も P1〜P4 で一致」は誤り (plan は C-1 の B 群化を提案) | worklog fragment | closed — 「両レンズの判定ラベルは一致、plan の C-1 B 群化案は採らず分離」へ置換 |
| M3 stale 注記が §6 / §7 の過大主張禁止まで失効させると読める | `docs/paper-story/README.md` | closed — 失効範囲を §1 と §8 C-1 の理由に限定、C-1 将来スコープの結論維持と §6 / §7 規則の有効を明記 |
| N1 「性能比較 0 件」の母集合 | paper-story README・worklog fragment・本 insight §2 | closed — 「非 Silo (mocc / tictoc / cicada) の性能比較は 0 件」へ |
| N2 3 証拠の所在の指示語 | 本 insight §4 | closed — `cc/mocc/transaction.cc` を名指し |

## 7b. 受入全走 (2026-09-17)

| 走 | worktree | 結果 | 判定 |
|---|---|---|---|
| 1 | `…/dev-wave-cross-protocol-scope-release` (branch 同名) | rc=70: 16 error + 1 failed / 24490 passed / 67 skipped (claimed main ec25bd2d0) | 16 error = `git archive` / `git ls-files` の `TimeoutExpired` 15 + real-repo lock deadline 1 (受入 4 本並走下の負荷、非帰属)。1 failed = `test_pegasus_dispatch_compute::test_compute_marker_is_cross_namespace_evidence_without_release_handshake` — script に埋め込まれた worktree path の `scope-release` に `"release" not in script.lower()` が当たる決定的な自分起因赤 (failures 台帳の新規 F、fold で採番)。junit 本文 = `verbatim/` には置かず job dir (`wave/junit_reds.py` 出力) で判定 |
| 2 | `…/dev-wave-cross-protocol-scope-lift` (branch `worktree-dev-wave-cross-protocol-scope-lift`、同一 commit から新設 + main 取り込み bebb65eba) | `child-green`: 24544 passed / 67 skipped / 0 failed (tested main 594f5ac89 / tested tip 43761ab59) | 緑。門番 = leader 3 本・load1 21.31 < load5 31.56 で GO |

worktree を切り直した理由: branch 改名だけでは path が script に残る。submodule を含む worktree は `git worktree move` / `remove` が `fatal: working trees containing submodules cannot be moved or removed` で拒否される。旧 worktree / branch は捨て (cleanup 対象)。

## 8. verbatim 一覧

`verbatim/parent-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、`verbatim/s4-adjudication.md`、`verbatim/s6-review.md`、`verbatim/prompt-plan.md`、`verbatim/prompt-consult-A.md`、`verbatim/prompt-consult-B.md`、`verbatim/prompt-review.md`、`verbatim/user-utterances.md`。sha256 は `verbatim/MANIFEST.json`。
