# [T-409] 実装 wave 段 4 裁定 — real/refuted、plan v2 差分、変異事前登録

親 = dev-wave manager。入力 = s1-brief.md、s2-plan.md、s3-lensA.md (12 所見)、s3-lensB.md (8 所見 + refuted 1)。
親の独立実測: render_hole の indent 前置 (p3_s4_loop.py:158-171)、parse_template_file の text-mode 読み
(diff_quarantine.py:555)、rung-1 runtime binding 集合 (silo_ladder_rung1.py:252-267、patchharness.py を含む)、
qualification code_identity の執行位置 (campaign 実行時のみ、テスト非執行)、oracle manifest テストの
live-hash 方式 (test_s8b_oracle_manifest.py:71-80)、holdout_freeze.json の source pin 集合、
repo 内 trigger campaign 7 件と sweep provenance の implementation 逐語記録。

## 裁定表 (レンズ A)

| # | 裁定 | 対応 |
|---|---|---|
| A-1 | **real 採用 (must-fix)** — render_hole が indent を前置し raw と実 source bytes が乖離 | 権威 gate 入力 = 実 source の rendered hole bytes。driver 側 proposal 検査は前置 prefilter として残す (同一 checker)。境界 4094/4095/4096 を raw / rendered 両面で登録 |
| A-2 | **real 採用 (must-fix)** — text-mode 読みが CR を消す | gate 用抽出は binary read (または newline="")。CR/NUL/非 ASCII を物理 bytes のまま拒否。CRLF/CR-only 負例を登録 |
| A-3 | **real 採用 (must-fix)** — 数え方・順序の未定義点 | 凍結: type 段 = str 検査 / raw size 段 = code point 数 (純 ASCII では byte 数と一致、encode を呼ばずリーク・例外なし) / character 段 = 許可 25 字集合外を拒否 (非 ASCII・surrogate 含む) / token 化 = maximal munch、無効 lexeme → INVALID_TOKEN / token 数 > 512 → RESOURCE_LIMIT / parse・深度 65 → INVALID_GRAMMAR / semantic → UNSET_NOT_TRUE。A2-5 期待値を凍結: `: :`=INVALID_TOKEN、`= =`=INVALID_GRAMMAR、`! =`=INVALID_TOKEN、`& &`=INVALID_TOKEN、`&&&`=INVALID_TOKEN、`===`=INVALID_GRAMMAR、`\|\| \|`=INVALID_TOKEN |
| A-4 | **real 採用 (partial)** — 自己一致は oracle でない | 手で凍結した独立 truth-table fixture (混合優先順位・括弧を含む) を期待値定数としてテストへ。C++ differential compile は常設スイートへ入れず、段 6 受入で親が 1 回実測し insights へ記録 |
| A-5 | **real 採用 (設計明確化)** — in-process 封印は認証でない | 権威 = build 境界の実 source 再認識 (buildcache/pipeline)。receipt は identity 束縛 artifact であり単独の通行証にしない。偽造 receipt 負例 (object.__new__ 等) は「実 source 再検査が拒否する」ことで KILL |
| A-6 | **real、scope 外 → 裁定パッケージ候補** — ABA 差し替え窓 | 既存 build admission が既知未閉鎖と明記する axis 横断の既存穴。閉鎖は snapshot-build 基盤を要し本 wave 外。post-build 再読 (plan 済) で窓を縮める。新 T 起票案を段 7 で返す |
| A-7 | **real 採用 (must-fix)** — 正当 reject が WAL replay を壊す | pre-admission reject は receiptless build_start + attempt-bound abort (閉 enum reason) を正当 topology とする。receiptless build_done/commit のみ禁止 |
| A-8 | **real 採用 (変異再設計)** — 補助 field が mask される | 権威束縛 = admission body 内 receipt。補助 field は変異 credit に数えない。plan §10 の 333/335 登録取消、332 を 2 変異へ分割 |
| A-9 | **real 採用** — recipe 再構成は現物 field から不能 | 再検査は「source bytes または provenance の implementation 逐語が残る実体」のみ。残らない実体は正直に reject (裁定 択一 2 の「source bytes が残っている限り」と整合)。brief P3 を訂正 |
| A-10 | **real 採用 (must-fix)** — 旧 terminal の標準 record 化は捏造 | 旧 WAL へ再発行しない。独立の reinspection ledger (campaign 別 artifact) に old-record hash → 文法 verdict を記録し、artifact_admission が view 発行時に参照。標準 attempt へ昇格しない |
| A-11 | **real 採用 (must-fix)** — リーク面が入口以外に残る | 抽出例外 (UnicodeDecodeError 等) を閉 reason へ写像。canary (SECRET_CANARY・invalid UTF-8・lone surrogate) を actual-source / cache-hit / reinspection / S8B resume の 4 面で登録 |
| A-12 | **real 採用 (must-fix)** — generic gate 変異が他層に mask | 実テンプレ上で公開 quarantine(..., invalid, write=True) を直接叩く node テストを置き、generic-gate 変異をそこへ単独帰属 |
| A-13 | **real 採用 (partial)** — qualification trust root | 親実測: code_identity 執行は campaign 実行時のみでテスト赤にならない。帰結 = 次回 campaign 前に evidence 再発行が必要 (T-419/T-410 の campaign 再走に相乗り、既裁定パターン)。pin inventory へ qualification series を追加し、worklog へ運用帰結を明記 |

## 裁定表 (レンズ B)

| # | 裁定 | 対応 |
|---|---|---|
| B-1 | **real 採用 (must-fix)** | s8a_trigger_coverage.py / s8a_trigger_freq.py / materializer_admission 登録面とテストを実装子 B2 の scope へ追加 |
| B-2 | **real 採用 (must-fix、最重要)** | artifact_admission.py を scope へ。旧 trigger campaign は reinspection ledger 済のみ admitted view。未 reinspection は fail-closed (admitted にしない) |
| B-3 | **real 採用 (must-fix)** | s8b_oracle_manifest.py / s8b_oracle_report.py / s8b_ratified_freeze.py の exact keyset を trigger/non-trigger 二形態で閉じる。テスト追随含む |
| B-4 | **real 採用 (partial)** | producer 別 migration 分類 (source root 存続 / provenance 逐語あり / 不能) を実装。不能分は正直 reject + 件数を worklog へ。repo 内 7 campaign は sweep 6 = provenance 逐語ありを親実測済み |
| B-5 | **real 採用 (must-fix)** — brief 不変条件「pin 3 本」は誤り (訂正) | 正: known_axes freeze は多数 pin (genome.py 等)、holdout_freeze も pin (上記実測)、oracle manifest は 5 generator を live 照合、rung-1 は patchharness.py 含む runtime binding をテスト強制。**編集禁止 (テスト強制): patchharness.py、env_contract.py、env_attestation.py、verifier/**、silo_ladder_rung1 系、calibrator 系**。**編集回避 (本番検証経路): axis_trigger_gating.py、s8a_trigger_sweep.py、s1_known_axes_freeze.py、genome.py、s8b_holdout_freeze.py**。**編集可 (運用帰結記録付き): pipeline.py、buildcache.py、build_admission.py、source_digest.py、s1_direct_comparison.py、s8b_oracle_report.py** — 後者の帰結 = repo 外の qualification evidence / oracle manifest の再発行が次回 campaign 前に必要 |
| B-6 | **real 採用 (partial)** | role diff は文法 v1 への契約縮小の逐語写像に限定。各 diff 行に文法要素を注記。文法 v1 に無い追加禁止・producer 誘導は入れない。防壁連鎖の記述更新は事実配線の範囲で可。承認射程 = 択一 3 裁定文の「契約を狭める」(文法 v1 全体) と解し、段 7 で射程解釈を明記 |
| B-7 | **real 採用 (must-fix)** | layer3 v4 の trigger/non-trigger 両形・条件付き required・v2/v3 reader・test_t126_qualification_artifacts 追随を定義。claim_boundaries 削除変異を登録 |
| B-8 | **real 採用 (手順確定)** | A→B1→B2 を**同一 wave worktree で逐次**実行 (依存単位のため並列不成立、worktree 分割は不要)。単一化理由 = B は A の公開 API に依存し並列投入しない。handoff へ記録 |
| B-9 | **採用 (P2 訂正)** | brief P2 の「既存 issued flag 様式」は誤り — 既存 receipt の永続 body に issued field は無い。永続 issued field は置かず、runtime seal + exact type + build 境界実 source 再検査で閉じる |

## plan v2 差分 (s2-plan.md への修正指示)

1. **patchharness.py を編集しない** (rung-1 binding テスト赤、親実測)。docstring 更新は取消。patchharness 面の被覆は従来どおり下流 (source_digest/buildcache) の実 source 検査で行う (plan §3 の設計はそのまま成立)。
2. 権威 gate 入力 = 実 source rendered hole bytes (binary 抽出、A-1/A-2)。driver prefilter は raw proposal に対する同一 checker。
3. recognizer の数え方・A2-5 期待値は上表 A-3 の凍結どおり。
4. receipt: 永続 issued field 削除 (B-9)。位置づけ = identity 束縛 (A-5)。
5. WAL: 旧 record の新 WAL 再発行を取消 (A-10)。reinspection ledger 方式へ変更。pre-admission reject topology (A-7)。
6. scope 追加: s8a_trigger_coverage.py、s8a_trigger_freq.py、artifact_admission.py、s8b_oracle_manifest.py、s8b_ratified_freeze.py (B-1/B-2/B-3)。
7. 実装単位: A (recognizer + 純テスト) → B1 (receipt/source/cache/WAL/pipeline/driver 配線 + テスト) → B2 (S8A 直接経路 + artifact_admission + S8B + layer3 + role 単位 + テスト)。同一 worktree 逐次、各単位 codex author。
8. 変異 matrix: plan §10 から 333/335 を削除、332 分割、A-12 の直接 node 帰属、B-7 の claim_boundaries 変異追加。

## 変異事前登録 (DW-M01、実装前凍結)

対象 = 統合 commit 後の最終 code。harness = tools/mutation_harness.py。各変異の単一理由性根拠 =
「検出テストが当該 node を直接呼ぶ unit/integration テストであり、同一入力を拒否する前後層がテスト経路に無い」。
受理集合縮小 wave のため正例も登録する。

| M# | 変異 (置換対象は一意) | 期待 KILL テスト (単一理由) |
|---|---|---|
| M1 | trigger_gate_language: 公開 checker を常時 passed=True | reject corpus (直接 unit) |
| M2 | scanner: 単独 `!` を token として受理 | bare-bang unit |
| M3 | scanner: 空白跨ぎ punctuator 結合 | A2-5 7 ベクタ unit |
| M4 | scanner: 最長一致を 1 文字優先へ | `:: == != && \|\|` 正例 unit |
| M5 | 判定順: raw size 段と character 段を交換 | 混合失敗 order matrix unit |
| M6 | token 上限: 512 境界の off-by-one | 512/513 unit |
| M7 | 深度検査を無効化 | 64/65 unit |
| M8 | semantic: kUnset 検査を削除 | `false`・非 kUnset 式 unit |
| M9 | parser: `&&`/`\|\|` 優先順位を破壊 | 手凍結 truth-table fixture unit |
| M10 | build_admission: checker 不合格でも receipt 発行 | admission reject integration (直接呼び) |
| M11 | build_admission: exact type 検査を isinstance 緩和 | 偽造 receipt integration |
| M12 | buildcache: cache-hit 時の実 source 再検査を skip | cache-hit 直接 node テスト (crafted cache 状態、prefilter 非経由) |
| M13 | p3_s4_loop.quarantine: trigger 検査を skip | 公開 quarantine 直接 node テスト (A-12) |
| M14 | artifact_admission: 旧 trigger campaign を reinspection なしで admitted | legacy fixture 直接 unit |
| M15 | reinspection ledger: 不合格 verdict を合格として記録 | reinspection unit |
| M16 | wal: receiptless build_done/commit を許容 | WAL topology unit |
| M17 | layer3: claim_boundaries を落として schema green | claim-boundary テスト |
| M18 | role parity: adapter sha だけ旧値へ | check_codex_agents parity テスト |
| 正例 P1-P9 | positive-controls 9 式 (raw + rendered indent 付き) | 全層通過 (過剰拒否検出)。driver prefilter〜build 境界まで |

hang_risk: なし (全て純 Python 検査)。両層変異: M12+M13 同時 (mask 裏取り用) を kill 期待付きで追加登録。

## 射程

- 実装しない: ABA 閉鎖 (A-6、新 T 案)、freeze 回帰テスト ([T-442])、backoff/sort 軸 ([T-441]/[T-410])、verifier の workload 縮小検出 (別 T 候補、凍結 README §6)。
- 運用帰結 (worklog へ): 本 wave land 後、次回 campaign 実行前に qualification evidence と S8B oracle manifest の再発行が必要 (T-419 較正再取得 → campaign 再走に相乗り)。
