# silo-function-policy 軸の段階 E — 兄弟 driver・coder role 2 形 (C++ / IR)・runbook・firewall の機械化 (2026-09-26、[T-2865])

- 位置づけ: 軸オンボーディング (`docs/axis-onboarding.md` §3 E、§4 第 3 列) の段階 E の記録。設計の正本は `output/insights/2026-09-21/silo-function-synthesis-space/README.md` (以下「設計」)、採用判断は D2214、段 E へ進める裁定は D2243 項 1。本段の設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: branch `worktree-dev-wave-t2865-silo-policy-stage-e`、起点 local main `6d198ca8a` (2026-09-26 18:50 JST に開始 gate rc=0)。submodule pin `6810666` (= `pin.CURRENT_PIN`、不変)。
- 逐語 (`verbatim/`): 依頼 `request.md`、D2214・D2243 項 1 の写し、段 1 brief `brief.md`、段 2 plan `s2-plan.md`、段 3 相談 `s3-consult-{A,B,C}.md`、段 4 裁定 `s4-ruling.md` と interface `interface.md`、段 5 実装子の報告 `s5-author-{core,role}.md`、段 6 のレビュー `s6-review-{A,B}.md`・裁定 `s6-ruling-{1..4}.md`・fix 子の報告 `s6-fix-{1..4}.md`・焦点再レビュー `s6-focus-{1..3}.md`、変異 matrix `mutation/`。prompt と codex の受領証は wave の job dir (repo 外)。
- **firewall の記録:** 親は段階 D の insight の §0〜§2.1 (列挙の因子の定義を含む) を読んだ。coder の入力・role 本文・coder 用の固定仕様にはそれを書いていない。driver が coder 入力へ読むのは段階 D の `projection.json` の `binary` と `scope` だけで、偵察・小比較 (D2240) の file は開かない。子 (codex) の prompt では段階 D の §2.1 以降・`verbatim/`・`projection.json` 以外の偵察 file・小比較の insight を読むなと指示した。

## 0. 要約

1. **兄弟 driver `orchestrator/campaign/p3_s4_loop_policy.py` (495 行) と test (417 行) を足した。** C++ 形と IR 形の proposal を、共有検疫 (構造 + effect) → 型付き構文検査 → 単独 TU compile → auditor の digest 照合と deny-only veto → 書込 → digest 再照合 → pipeline (legacy + 性能構成の verify) の順に通す。planner は無く、停止は予算だけ。
2. **coder role 2 本 (`coder-v4-autonomous-policy`・`coder-v4-autonomous-policy-ir`) と auditor 改訂を、ユーザーの明示承認 (2026-09-26 19:5x JST、「承認する (推奨)」) の後に入れた。** role 登録簿は 14 → 16 件。
3. **firewall を driver の 1 関数に機械化した。** coder 入力は段階 D の `projection.json` の `binary`・`scope`、固定のリーク防止文脈と接続仕様、stock の baseline、当該 campaign の自系列履歴 (justification を除く) だけから組む。失敗理由は閉じた code に正規化し、verifier の witness は先頭 8 件と件数・全 cycle 数だけ渡す。
4. **計算ノードでの実走 (build・verify・bench) と本 driver 用の Pegasus job body は、段 4 裁定で段階 F の前提へ送った。** E の計算は焦点走と受入だけ (§3)。
5. 段 6 は NO-GO が 3 巡続き (レビュー A/B、焦点再レビュー 1・2)、fix 4 本の後の焦点再レビュー 3 で GO。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 段階 E (兄弟 driver・tool なし coder role の C++ 版と IR 版・runbook・firewall の機械化) へ進める。planner は外す。後段へ渡すのは段階 D の projection.json の二値と射程文だけ。D2240 の小比較の点 ID・因子・比・順位は coder の入力へ流さない。`.claude/agents/` の具体差分は wave 内でユーザーの明示承認を取ってから入れる。実装は Codex author。正しさゲートは不変。段階 F は別 session。本題だけ。
- 段 3 相談は 3 本 (A リーク制御と正しさ境界、B fails-closed と回帰、C 過剰と削除) とも adopt_with_conditions。段 4 で次を裁定した (`verbatim/s4-ruling.md`):
  - 親の暫定案 P1 (共有 `quarantine()` に本軸の分岐を足す) を撤回。段階 C/D の診断経路 (`prepare_policy`) の引数契約を壊すか二重 compile になる (3 本が一致して指摘)。
  - `prior_critic_reverse` を proposal から除き、停止は予算だけ。
  - auditor の違反型上限は呼出し側の引数にし、本 driver だけ 26。
  - 手書き 2 形の計算ノード実走と job body は E の完了条件から外す (相談 C)。
- 段 1 brief の「完了判定 (1) pipeline.evaluate へ通す」は、`--no-build` の配線確認と fixture test までに修正した (実走の最初の証拠は F)。

## 2. 実装 (commit)

| commit | 内容 |
|---|---|
| `41b8019a9` | 段 5 の統合: IR parser `parse_policy_ir` (閉じた tagged object)、auditor 上限の引数化、proposal 契約 `policy-cpp` / `policy-ir`、reject subtype `policy-grammar` / `policy-compile`、coder entrypoint 登録、driver と test、coder 用の固定接続仕様 `silo_function_policy_coder_spec.md`、role 2 本と auditor 改訂と role 登録簿 (manifest・review ledger・policy・adapter 3 件・README・check tool・test) |
| `47d352205` | 段 6 fix 1: 性能動作点を campaign identity に束縛、失敗理由の構造化射影、coder だけの preview、dry-pass が WAL を要求しない、`--critic-output`、探索 namespace と caller inventory への登録、MOCC proof test の束縛を auditor 項目の一致へ |
| `cc5d8375e` | runbook `docs/phase3-silo-policy-runbook.md` と docs 地図の 1 行 (親) |
| `2ee50cc9f` | 段 6 fix 2: reason の閉じた code 化、witness の件数上限、`--record-reject`、runbook の preview 拒否手順 (親) |
| `ad3e8cfa5` | 段 6 fix 3: 性能 file の登録簿へ追加 |
| `650b9b80c` | 段 6 fix 4: `anomaly_count` を `witness_count` に改名 |

- 実装面の全ハンクは Codex author (gpt-6-sol、reasoning medium) が子 worktree (`.codex/worktrees/t2865-unit-{core,role}`) で書き、親は所有 path 限定の patch を統合した。
- role 単位の子は sandbox が `.codex/` への書込みを拒否したため、adapter 3 件と README 案を子の `/tmp` に生成した。親はその bytes を配置し、`tools/check_codex_agents.py` が期待 bytes と一致すると判定した (16 role、rc=0)。
- 実装子はどれも pytest を実走できなかった (sandbox から qstat 不可、login の直接 pytest は hook 拒否)。test は親が計算ノードで走らせた (§3)。

## 3. 焦点走 (計算ノード、`tools/run_tests.py --force-dispatch`)

| 走 | 木 | request | Elapse | 結果 |
|---|---|---|---|---|
| focus-1 | 段 5 統合前 (未 commit) の変更 test 5 file | 29786.nqsv | 32 秒 | 149 passed / 3 failed (未 commit 由来: contract loader の drift 2、tracked file の AST 閉包 1) |
| focus-2 | `41b8019a9`、変更 test と consumer test・inventory 4 群ほか 38 file | 29930.nqsv | 141 秒 | 4392 passed / 9 failed / 12 skipped (探索 namespace の driver 登録簿 6、certified writer の caller inventory 1、MOCC template proof の auditor sha 2) → fix 1 |
| focus-3 | `cc5d8375e` + 未 commit の runbook 編集、39 file | 29964.nqsv | 146 秒 | 4410 passed / 2 failed / 12 skipped (性能 file 登録簿 1 → fix 3、b4 wiring probe の作業ツリー検査 1 = 焦点走の待機中に親が runbook を未 commit で編集した非帰属の赤) |
| focus-4 | `650b9b80c`、同 39 file | 29984.nqsv | 147 秒 | **4417 passed / 0 failed / 12 skipped** |

## 4. 段 6 の経緯

| 巡 | 入力 | 判定 | 直したもの |
|---|---|---|---|
| 1 | レビュー A (正しさ境界、NO-GO)・B (過剰と削除、NO-GO)、focus-2、親の runbook 起草 | `verbatim/s6-ruling-1.md` | 動作点の束縛 (A)、失敗理由の構造化 (A・B)、coder だけの preview (B・親)、dry-pass (B)、`--critic-output` (親)、登録簿 (focus-2)、MOCC proof test の束縛 (focus-2)、変異の再照準 |
| 2 | 焦点再レビュー 1 (NO-GO: WAL の reason の自由文が coder へ) と親の点検 2 件 | `s6-ruling-2.md` | reason の閉じた code 化、witness 件数の上限 (段階 C の負例で cycle 39,124 件)、preview 拒否の記録口 `--record-reject` (親: 記録しないと次の coder が自分の拒否理由を受け取れない、規律 3) |
| 3 | focus-3 | `s6-ruling-3.md` | 性能 file 登録簿 |
| 4 | 焦点再レビュー 2 (NO-GO: 辺の key の自由文字列、`anomaly_count` の意味) | `s6-ruling-4.md` | `witness_count` への改名。辺の key の検証は仮想リスクとして不採用 (trace は固定骨格の計装が出し、候補は受理契約で文字列・pointer・外部名を持てない) |
| — | 焦点再レビュー 3 (最終巡) | GO | must-fix 0。J1 の不採用裁定も実コードで妥当と判定 |

- MOCC template proof の test (`orchestrator/tests/test_mocc_template_proof.py` の `_consumer`) は、proof JSON (`output/env/pegasus/calibration/s3_mocc_template_proof.json`、2026-09-19 記録) に記録された auditor.md の whole-file sha256 と現行の一致を要求していた。承認済みの auditor 改訂で赤になり、束縛を「記録した MOCC 用 auditor 項目 == 現行項目」に置き換えた (規律 7、D は同 wave の decisions fragment)。auditor.md の改訂は 2026-09-02 以来で、proof 記録後は初めてだった。

## 5. 変異 matrix (dev-wave、段 4・段 6 の事前登録)

- 独立 clone (D1009) の固定 commit `650b9b80c` で `tools/mutation_worktree.py` を dispatch 本走 (`--runner-mode dispatch --detached`)。test の集合は `test_p3_s4_loop_policy.py`・`test_silo_policy_ir.py`・`test_auditor_gate.py`。期待 node は全件 SURVIVED 期待の probe で観測した失敗 node の完全集合から作り (DW-M08)、final はそれとの完全一致だけを KILLED と数えた。spec・観測 node・final 結果 = `verbatim/mutation/`、spec 生成の道具は wave の job dir (各 anchor が対象 file の累積置換後にちょうど 1 回現れることを検査)。
- **final: 16 / 16 KILLED (MISMATCH 0・SURVIVED 0)、基準走は 3 走とも PASSED。**

| ID | 壊したもの | 落ちた node (final、完全一致) |
|---|---|---|
| M-E2 | 単独 TU の拒否を受理扱い (構文は通り TU だけで落ちる本文 = 未使用の局所変数) | gate の digest と拒否時無書込の test |
| M-E3 | auditor の digest 照合と veto を外す | gate の digest test、型 22〜26 の veto test |
| M-E4 | 本 driver の veto 上限を 21 に | 型 22〜26 の veto test |
| M-E5 | auditor_gate の既定上限を 26 に (5 か所) | 既存の型 22 拒否 test、既定 21 の新 test |
| M-E6 | IR parser の未知 key 拒否を外す | IR parser の全 node 種 test |
| M-E7 | IR の整数判定を `isinstance` に (parser 2 か所と `validate_ir` の両層) | IR parser の全 node 種 test、`test_reject_types_literals_and_abort_inputs[bad3]` |
| M-E8 | proposal の重複 key 拒否を外す | schema・preview・上限 26 の test 3 |
| M-E9 | coder 入力に `excluded` を足す | cfg と coder 入力の射影 test |
| M-E10 | 履歴の射影に justification を足す | 同上 |
| M-E11 | verify 構成を legacy+s2 に | 同上 |
| M-E12 | campaign identity と実行時 perf の照合を外す | 動作点の照合 test |
| M-E13 | WAL の reason を outcome に写さない | 例外 reason の閉包 test、履歴の構造化射影 test |
| M-E14 | preview にも auditor を要求する | coder だけの preview test、`--record-reject` の CLI test |
| M-E15 | reason の正規化を外す (自由文をそのまま) | 例外 reason の閉包 test |
| M-E16 | witness の 8 件上限を外す | witness の先頭 8 件と件数の test |
| M-E17 | `--record-reject` が gate を通る候補も記録する | 拒否だけを記録する test |

- **事前登録からの変更 (erratum):**
  1. M-E1 (構文拒否を受理扱い) は、構文拒否の本文では単独 TU compile が呼ばれず (`compiled is None`) compile 拒否へ落ちるだけで受理集合が変わらないため、段 6 裁定 1 で diagnostic sensitivity pin (P-E2) に移し kill に数えない。P-E1 (reject subtype の別名化) も同じく diagnostic pin。どちらも走らせていない。
  2. M-E5 の最初の形 (既定値 4 か所) は probe で SURVIVED した。`parse_auditor_dict` 自身が既定値 21 を持っており (`auditor_gate.py` の同関数の署名)、注入が効く経路を外していた (照準漏れで、gate の欠陥ではない)。5 か所目を足した形を M-E5 だけの probe で取り直し、2 node の検出を確認してから final に入れた (DW-M02)。
  3. M-E12〜M-E17 は段 6 の裁定 1・2 で追加登録した (fix の前)。
- 変異走の runner 時間の合計は 2,544 秒 (probe 472 秒・M-E5 の probe 55 秒・final 2,017 秒。final の 1 走は待ち行列込みで 1,177 秒。待ち行列を含む上限値)。

## 6. scope 外と段階 F の前提

- **段階 F の前提 (AI 側、F を始める前に要るもの):**
  1. 本 driver 用の計算ノード投入経路。既存の `tools/pegasus/p3_s4_loop_pegasus.sh` は `p3_s4_loop` 固定で、PIN 検査も `p3_s4_loop.PIN` を見る。driver 選択を足すか兄弟の job body を足し、契約 test (`orchestrator/tests/test_p3_s4_loop_job_contract.py` が型) と投入許可台帳 (`tools/pegasus/admission_registry.json`) を揃える。
  2. fresh session (新 role はセッション開始時にだけ登録される)。
  3. 計算の見積りと確認 (1 iteration = build・legacy verify 1 rep・性能構成 verify 5 rep・bench 5 rep。job Elapse の実測単価で見積もり、検査込みのタスク合計が 2 node 時間以上なら投入前にユーザー確認)。
  4. stock の baseline (`--emit-coder-input` の必須入力) を同じ動作点で測る手順。
- **実装していないもの:** 手書き 2 形の計算ノード実走 (段 4 で F へ)、非 LLM の IR arm と比較 harness (設計 §5 の比較 A/B)、公平性の機械観測・候補ごとの sanitizer・TRACE 計数 (設計 §3.4 の見送り)、逆方向推奨を使う停止判断、`p3_s4_loop.quarantine()` への分岐。
- **残存リスク:**
  - 実 LLM の出力が policy-C++ v1 / IR の受理契約をどれだけ通るかは未測定 (F で測る)。
  - pipeline を通る実走 (build・verify・bench) は本 driver では未実走。配線の証拠は `--no-build` の fixture test と、段階 C の診断経路の実走 (同じ骨格・同じ検査器) だけ。
  - 自由文 `scope` (段階 D の射程文) の内容は検査していない。
  - verify と perf で同じ分岐を踏んだとは言えない (設計 §3.1)。
