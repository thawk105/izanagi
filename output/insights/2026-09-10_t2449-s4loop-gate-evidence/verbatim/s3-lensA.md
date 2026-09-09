## 読んだ資料

指定された 6 資料はすべて読取可能だった。別 checkout・射影外の tests／manifest／job body は読んでいない。静的検査のみで、pytest・実測・編集・git 操作は行っていない。

- 親 [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/prompts/s1-brief.md:1)
- 段 2 [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:1)
- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:327)
- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:345)
- [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:623)
- [CLAUDE.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/CLAUDE.md:67) の規律 2 / 3 / 6 / 7

## real 所見 (成果物影響つき)

1. **High — `[捏造/幻覚][ドリフト]` 段 2 の P1b 反証は成立しておらず、argv 断念では依頼を完了できない。**

   段 2 は、過去 `repro.json` の whole-file manifest を「現行 producer の red record bytes を拘束する consumer」と扱い、`_run_process` 編集を撤回している（[s2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:43)、[同:120](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:120)）。しかし、過去ファイルの hash は過去 bytes を凍結するだけで、将来の producer が同じ red bytes を生成する契約ではない。規律 7 も、過去の測定と現行コードの適合を分離する（[CLAUDE.md:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/CLAUDE.md:97)）。

   実装内の hash は動的整合性である。`evidence` を含む現在の payload から record ID を生成し（[condition_meaning_gate.py:1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1009)）、consumer もその record 自身から再導出する（[同:3979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:3979)）。固定された旧 digest との比較ではない。admitted bool は record ID でなく terminal status から決まる（[同:4063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:4063)）。

   `_run_process` は失敗 detail に argv を含めず（[同:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1559)）、preprocess argv は呼出し時点にしか存在しない（[同:2224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2224)）。driver 側だけでは失われた argv を復元できない。

   **成果物影響:** 現行 tip が再び configure/preprocess で落ちた場合、保存される arm record に argv が無く、T-2449 の完了条件を満たせず、certified 選択材料は依然 0 件のままになる。

2. **High — `[手順漏れ][ドリフト]` `p3_s4_loop.py` の編集は B4 の全 driver kind の admission を確実に動かす。**

   `p3_s4_loop.py` は base / sort / trigger 共通の projection closure member である（[p3_b4_closed_critic.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:623)）。live hash は verified admission 内の期待値と等値比較され（[同:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:687)）、production pair 作成時にも必ず発火する（[同:1267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:1267)）。既存 receipt も current bytes との差で拒否される（[同:1679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:1679)）。

   したがって、段 2 の「live hash 3 値は動くが errata 不要」という結論（[s2-plan.md:124](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:124)）は両立しない。少なくとも runtime の `admission_record_path` に渡す committed admission record の更新または superseding が必要である。

   **成果物影響:** admission record を据え置くと、condition gate の green bytesが同一でも B4 base / sort / trigger の certified pair と既存 receipt の現行検証がすべて rejection になる。

3. **High — `[セッション死・救出][テスト代表性]` 固定名 + `O_EXCL` は再試行時に現行証拠を残さない。**

   段 2 は固定 2 ファイルと create-only を提案し（[s2-plan.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:19)）、既存ファイルを保存失敗として旧 bytes を残す仕様にしている（[同:73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:73)）。同じ evidence root を再利用すると、2 回目の現行 record は一切保存されず、前回 record だけが残る。

   代案は、arm と `record_digest` を含むファイル名にするか、固定名が既存なら byte equality を確認した上で異なる record を digest 名へ保存すること。新しい gate は不要である。

   **成果物影響:** 再投入後のレポートが前 job の arm record を今回の失敗として参照し、commit・argv・reason の帰属がずれる。

4. **Medium — `[手順漏れ]` gate-level admission record が依然捨てられる。**

   driver は admission を計算するが（[p3_s4_loop.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:404)）、red では RuntimeError にして捨てる（[同:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:407)）。段 2 の保存対象は arm 2 本だけで、record ID 群・`admitted=False`・admission digest を束ねる `ConditionFamilyAdmission`（[condition_meaning_gate.py:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:680)、[同:4074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:4074)）は残らない。

   さらに canonical JSON から復元した arm は issuer capability を持たず、production admission へ再投入できない契約である（[同:1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1048)、[同:4023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:4023)）。red 分岐で admission canonical JSON も同じ attempt に保存すべきである。

   **成果物影響:** evidence root には arm の内容は残るが、「その 2 record を用いて実際に拒否した admission」の ID・digest が無く、proof chain／レポートから gate-level 判定を引用できない。

5. **Medium — `[テスト代表性]` `evidence["detail"]` は全 red record の共通契約ではない。**

   段 2 は例外本文を `evidence.get("detail")` で作る（[s2-plan.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:27)）。process 例外由来の red には detail がある（[condition_meaning_gate.py:2562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2562)）が、`compiler-identity-drift`、`compile-command-drift`、`preprocess-bytes-identical` 等は `_preprocess_evidence` をそのまま使い、detail key を持たない（[同:2577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2577)、[同:2617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2617)）。

   **成果物影響:** これらの red では job stderr が `supply_detail=None` となり、「失敗本文を残す」というレポート契約を満たさない。

6. **Medium — `[恒真ゲート][テスト代表性]` 提案テストは admission 不変と rejection 全域を証明しない。**

   正例は supply / meaning / admission をすべて fake にする設計である（[s2-plan.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:84)）。したがって `require_condition_gate_family` の acceptance mutation は発火しない。また、記述上は supply-red / meaning-red の両 rejection 軸を要求していない。`if supply.terminal_status == "red": persist` という誤実装でも、983020 型の fixture だけなら通る。

   さらに full-suite mutation kill を使うと、`p3_s4_loop.py` のどんな byte mutation も先に B4 projection mismatch を起こし得る。新規 nodeid 自身が mutant を殺したかを分離しない限り、保存契約の保証が恒真化する。

   **成果物影響:** meaning-only rejection、または persistence を壊した mutant を「既存 B4 hash 検査が赤になった」だけで検出済みと誤認し、失敗 evidence の欠落を許す。

## refuted (プラン / 親 brief が正しい点)

- `_run_process` の detail に argv を足しても、変更されるのは失敗時だけである（[condition_meaning_gate.py:1573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1573)）。green arm の canonical bytes、reason code、terminal status、admitted bool、driver rc は動かない。動くのは新しい red record ID と、それを参照する red admission ID/digest であり、内容束縛として正しい変化である。
- 指定された 3 実装ファイル内には、`detail` の等値比較・包含比較・`match=` は見つからなかった。CLI は detail を表示するだけである（[condition_meaning_gate.py:4173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:4173)）。
- driver が red record を生成後に捨てるという親の指摘は正しい。
- `p3_s4_loop.py` が B4 projection closure の共通 member で、全 3 hash が動くという段 2 の事実認定自体は正しい。誤りは、その後の「関連 admission 更新不要」という結論である。
- 旧 commit の再走ではなく現行 tip を走らせる方針は正しい。両者は別 producer を測る。

## 親の実測と一般化の検査

### `merge-base` rc=1

- **実測値:** 今回の射影では git object/history を読めないため、rc=1 自体は独立再測定していない。
- **現在コード:** offline args の seam は確認できた。receipt 分岐で args を組み立て（[p3_s4_loop.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1825)）、capture へ渡し（[同:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:378)）、`CapturedDefineInputs` に保持する（[condition_meaning_gate.py:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:807)）。
- **到達経路:** args は CMake argv へ入って configure が実行され（[同:1648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1648)）、生成された `compile_commands.json` の owner entry（[同:1683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1683)）から preprocess argv を作って実行する（[同:2191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2191)）。
- **一般化:** args が preprocess argv に逐語で入るのではなく、CMake が生成した compile command を介した間接到達である。prefix の内容、CMake package discovery、生成された include flags、依存 header の存在までは rc=1 から出ない。「失敗が消えた可能性」は弱い可能性命題としてのみ支持でき、「成功する見込み」には一般化できない。

### `/usr/include/gflags` 不在・pkg-config rc=1

- **実測値:** 射影外の system path / pkg-config は再測定していない。
- **一般化:** その 2 点だけでは system 全体や compiler からの不可視性を証明しない。少なくとも別 prefix、`PKG_CONFIG_PATH`、module、compiler の sysroot／既定 include path、CMake config package、明示 `-I` を揃えて検査する必要がある。「計算ノード固有ではない」は過剰である。

### 「失敗本文は既に record の中にある」

- **実装上は支持。** preprocess `_run_process` が reason/detail を持つ例外を送出し（[condition_meaning_gate.py:2228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2228)）、supply evaluator が `evidence.detail` に写す（[同:2553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2553)）。driver は admission 後、reason code だけの RuntimeError を送出する（[p3_s4_loop.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:404)）。
- したがって「983020 の stderr に reason 行しかない」という親の観測とは整合する。ただし、その `job.stderr` 自体は射影外なので今回独立確認していない。

## (P1a)(P1b)(P1c) への賛否

- **(P1a) 支持。** 保存責務は driver、argv 捕捉だけは `_run_process` が妥当。ただし driver は固定名を避け、arm 2 本に加えて admission canonical JSON も同一 attempt として保存すべきである。
- **(P1b) 支持。** 少なくとも段 2 が示した historical manifest は反証にならない。argv 追加は red record ID／red admission digest を正しく更新するが、green bytes・reason code・terminal status・admitted bool・rc は動かさない。
- **(P1c) 条件付き支持。** 1 本で「現行 producer のこの環境・この入力」の supply arm outcome は判定できる。gate は `run_campaign` より前にある（[p3_s4_loop.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1825)）。ただし投入前に上記 1〜4 を直さなければ、再失敗時の一次資料または B4 admission が欠ける。`value != 20` の WAL skip 根拠は射影外なので独立確認していない。

## nit / 裁定パッケージ候補

- **裁定が必要:** `p3_s4_loop.py` 編集後の B4 admission record を、同じ commit で更新／supersede するか。変更候補は runtime の `admission_record_path` に渡す committed record、その producer／consumer tests、段 2 が引用する B4 preregistration 文書である。`p3_b4_closed_critic.py` 自体の gate 新設・緩和は不要。
- **所有範囲の追加:** argv を維持するため `condition_meaning_gate.py` と対応 test は変更面へ戻す必要がある。`test_p3_s4_loop.py`、acceptance ledger に加え、B4 admission record と関連 test の確認が必要。
- **nit:** 射影外の既存 tests を読めないため、`pytest.raises(match=...)`、detail exact fixture、reason/detail pair fixture の不在は証明できない。段 2 の検索語一覧には `match=` と既存 RuntimeError 本文が含まれておらず、その断定根拠は不足している。
- **nit:** `evidence_root` の canonical shell 変数再 export 要否は、今回読めない job body に依存するため判定しない。

## 総括

段 2 プランはこのままでは不受理である。最大の問題は、historical manifest を現行 producer の互換性拘束と誤認して argv を断念した点と、`p3_s4_loop.py` 編集が B4 の live admission を必ず動かすのに関連 record を変更面へ含めていない点である。

最小修正方針は、`_run_process` の失敗 detail に argv を戻し、driver の red 分岐で digest／attempt に帰属した arm 2 本と admission record を保存し、B4 admission record を同じ source bytes に追随させること。その範囲なら condition gate の受理集合・reason code・admitted bool・rc は維持できる。