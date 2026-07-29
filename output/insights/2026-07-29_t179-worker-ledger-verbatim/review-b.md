判定は **NO-GO**。静的検査のみで、pytest・runner は実行していないため、親の「46 passed」を再確認済みとは扱わない。

## 事前登録変異の判定

- **M1 — KILL 可。**  
  `test_compaction_keeps_cli_reported_as_canonical` が `cli_reported=170`、`per_turn_sum=240`、合計170を独立に固定する。per-turn 和へ変更すれば同 node が台帳正本値の変化で赤くなり、診断文字列依存ではない。  
  該当: [test_codex_worker_ledger.py:194](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:194)

- **M2 — 赤は出るが、事前登録どおりの KILL には数えられない。**  
  `session_id` 取込を単純に `[:8]` へ変えると、`test_full_session_ids_do_not_merge_on_eight_hex_collision` の ID 一意性は赤になる。しかし実装は records を list へ追加し続けるため、事前登録した「session 数が2→1、行が融合」は起きない。さらに healthy fixture の10 IDがすべて `80000000` 始まりなので、duplicate strict、stage-map lookup、cwd の完全ID比較まで連鎖赤になる。想定原因が一意でない。  
  赤候補: `test_full_session_ids_do_not_merge_on_eight_hex_collision`、`test_healthy_wave_and_matching_worklog_pass_strict`、両 stage-map test、`test_cwd_filters_are_or_and_preserve_timestamp_order`。  
  該当: [codex_worker_ledger.py:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:199)、[test_codex_worker_ledger.py:210](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:210)

- **M3 — KILL 可。**  
  `test_unclassified_is_included_and_strict_fails` が session の残存、stage、rc=2を同時に固定する。黙って除外すれば totals 1→0かつ fail-open になる。  
  該当: [test_codex_worker_ledger.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:222)

- **M4 — KILL 可だが単一 node ではない。**  
  validator を常に True にすると `test_fragment_requires_existing_output_validator_policy` と `test_fenced_summary_does_not_make_fragment_complete` の双方が `fragment→completed` で赤になる。意味論的な受理拡大なので有効だが、実 node 集合は2件として記録が必要。  
  該当: [test_codex_worker_ledger.py:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:233)

- **M5 — 逐語変異なら KILL 可。ただし fixture は過剰決定。**  
  欠落時に直接 `completed` を返す変異なら `test_incomplete_without_task_complete_or_agent_message` が赤になる。一方、この fixture は `task_complete` と agent message の両方が無い。単に incomplete branch を削除した変異は `fragment` になり、completed への fail-open は証明しない。  
  該当: [incomplete.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/fixtures/codex_ledger/cases/incomplete.json:3)、[test_codex_worker_ledger.py:254](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:254)

- **M6 — 全 mismatch を落とす逐語変異なら KILL 可。**  
  `mismatches` を issues へ追加しなければ `test_worklog_reports_total_and_review_mismatches_together` が rc=2→0で赤になる。ただし fixture は total と review の2理由を持ち、一方だけの gate 退行はもう一方の rc=2に mask され、赤は診断文字列だけになる。  
  該当: [codex_worker_ledger.py:546](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:546)、[test_codex_worker_ledger.py:313](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:313)

- **M7 — node は赤になるが、現規律では KILL 計上不可。**  
  `test_retry_normalizes_surrounding_and_repeated_whitespace` が retry fields と hash equality を検出する。しかし rc・strict・session受理集合は変わらず、構造化 signal の pin に留まる。`DW-M08` に従えば diagnostic sensitivity pin として別枠にすべき。  
  該当: [test_codex_worker_ledger.py:277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:277)

- **M8 — KILL 可だが単一 node ではない。**  
  strict を無条件失敗へ変えると healthy wave に加え、stage-map正例、read-only fixture、CODEX_HOME正例も赤になる。過剰拒否の意味論は正しいが、実 node は少なくとも4件。  
  該当: [test_codex_worker_ledger.py:288](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:288)、[test_codex_worker_ledger.py:412](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:412)、[test_codex_worker_ledger.py:499](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:499)

## 所見

### R-B1 — 必須 token 成分が台帳へ配線されていない

- 深刻度: `must-fix`
- 再現: rollout fixture は input/cached/output を持つが、`_billable()` で派生値へ畳んだ後に各成分を捨てる。公開 record・totals にも個別成分が無い。T-179 正本は input・cached input・output・CLI reported の集計を要求している。
- 成果物影響: 台帳から input/cached/output の stage 別値を復元できず、T-181/T-182 の比較根拠と CLI reported の監査参照が欠落する。
- 該当: [phase3.md:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/docs/phase3.md:525)、[codex_worker_ledger.py:151](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:151)、[codex_worker_ledger.py:402](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:402)

### R-B2 — stage/model/reasoning の壊れた配線でも全テストが通る

- 深刻度: `must-fix`
- 再現: simple `Codex fix worker` を author へ分類する規則を先頭へ追加しても、healthy test は stage の集合と `author・fix` 合算しか見ない。fix2 が fix のままなので全 stage 集合も維持される。retry test は stage を確認しない。また model/reasoning を常に空文字にしても assertion は一つも落ちない。
- 成果物影響: global totalとworklog gateが緑のまま、author/fix の stage token値またはmodel/reasoning参照が誤る。
- 該当: [codex_worker_ledger.py:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:39)、[codex_worker_ledger.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:204)、[test_codex_worker_ledger.py:288](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:288)

### R-B3 — root 不在・空・filter 0件を strict が正常受理する

- 深刻度: `must-fix`
- 再現: `--sessions-root <存在しないpath> --json --strict`、空directory、または typo した `--cwd-contains` は records/issues とも空になり、rc=0を返す。少なくとも1 sessionという gate が無い。
- 成果物影響: 実ログを一件も読んでいない台帳が `sessions=0` の健全な成果物として受理される。
- 該当: [codex_worker_ledger.py:506](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:506)、[codex_worker_ledger.py:557](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:557)

### R-B4 — JSON schema 違反を「壊れた行」として拒否しない

- 深刻度: `must-fix`
- 再現: otherwise healthy rollout の token_count 行を構文上有効な `[]` または `null` に置き換える。`json.loads` は成功し、非dictとして黙って continue するため、strict rc=0・turn/token=0になる。現テストは `{broken json` しか扱わない。
- 成果物影響: schema破損したログを受理し、台帳のturn/token値を静かに過少集計する。
- 該当: [codex_worker_ledger.py:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:187)、[test_codex_worker_ledger.py:339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:339)

### R-B5 — cwd selector の境界が過剰拒否とsilent dropの両方を作る

- 深刻度: `must-fix`
- 再現: `/other-wave` の valid metaを持つfileへ malformed lineを置くと、malformed issueを登録した後でcwd filterするため、健全な `/target-wave` だけを選んでもstrictが落ちる。逆にcwd欠落metaは空文字不一致としてissue無しで除外される。
- 成果物影響: 選択waveの受理集合が無関係なsessionに依存するか、対象候補sessionが台帳から黙って消える。
- 該当: [codex_worker_ledger.py:510](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:510)

### R-B6 — retry group が「同一 wave」に閉じていない

- 深刻度: `must-fix`
- 再現: cwdが異なる2 sessionへ同じ正規化promptを置き、共通rootを指定する。`_assign_retries` はprompt hashだけでgroup化し、wave/cwdをkeyに含めない。cwd filter自体も任意で、複数指定はOR。
- 成果物影響: 別waveの独立jobがretryとして融合し、T-183が参照するretry件数・group/indexが増える。
- 該当: [codex_worker_ledger.py:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:133)、[codex_worker_ledger.py:287](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:287)

### R-B7 — validator 再利用は受理集合を保存しておらず、ledger testも両方向に弱い

- 深刻度: `must-fix`
- 再現:
  1. 10MiB超でfence外総括を持つmessageはledgerではcompletedだが、既存validatorはsize上限でrejectする。
  2. `_validator_accepts` を常にFalseにしても、healthy testはoutcomeをassertしないため全ledger testが通る。
  3. min-byte検査だけを削除しても、fragment fixtureは「短い」かつ「総括なし」なのでheading側でrejectされ続ける。
- 成果物影響: 既存validatorより広い成果物をcompletedにするか、健全な全成果物をfragmentにする回帰がテスト緑のまま残る。
- 該当: [codex_worker_ledger.py:248](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:248)、[check_codex_output.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/check_codex_output.py:87)、[test_check_codex_output.py:103](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_check_codex_output.py:103)、[fragment.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/fixtures/codex_ledger/cases/fragment.json:3)

### R-B8 — 現状の mutation matrix では「8/8 KILLED」を記録できない

- 深刻度: `must-fix`
- 再現: 上記matrixのとおり、M2は想定したsession融合ではなくID文字列・duplicate・stage-map連鎖で赤になる。M7はstrict受理集合を変えない。M4/M8は複数node、M5/M6のfixtureは過剰決定である。
- 成果物影響: 実効gateを証明していない赤をKILLへ計上し、台帳のsession同一性・retry検出・worklog gateに誤った保証を付ける。
- 該当: [test_codex_worker_ledger.py:210](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:210)、[test_codex_worker_ledger.py:277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:277)、[test_codex_worker_ledger.py:313](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:313)

### R-B9 — `compaction_delta` は compaction の因果を検査していない

- 深刻度: `must-fix`
- 再現: `compaction.json` は totalsとlastsをずらすだけで、materializerは `context_compacted` eventを一行も生成しない。それでもdelta=70となる。実装も同eventを数えず、任意のusage不整合を `compaction_delta` と呼ぶ。
- 成果物影響: 欠落・重複・順序異常など別原因の差もcompaction由来として台帳参照され、親の因果主張と後続分析が誤る。
- 該当: [compaction.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/fixtures/codex_ledger/cases/compaction.json:3)、[test_codex_worker_ledger.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:87)、[codex_worker_ledger.py:235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:235)

### R-B10 — worklog grammar と entry 選択は対象(59)専用

- 深刻度: `backlog`
- 再現: regexは逐語の `Codex N job (planner ... / author・fix ... / review ...)` だけを受ける。repo内の「Codex 実装 2 + fix 5」「親1、codex read-only 6」等は拒否する。またentryは全headingへのsubstring一致、工数行はcode fence・引用を区別せずsearchする。
- 成果物影響: 将来entryでは正しい工数行を読めないか、引用した過去値を正本として掴む可能性がある。ただし今回の(59)は一意かつ逐語一致する。
- 該当: [codex_worker_ledger.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:105)、[codex_worker_ledger.py:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:343)、[worklog.md:1209](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/docs/worklog.md:1209)

「entryが見つからない」「工数行が見つからない」「値不一致」はdetail文字列では区別されており、今回の親出力は別理由との混同ではない。ただしすべて同じworklog category・rc=2であるため、rcだけでは理由を証明しない。

### R-B11 — stage-map と cwd filter の順序契約が未裁定

- 深刻度: `backlog`
- 再現: root上にA/Bがあり、mapに両ID、cwd filterでAだけを選ぶと、Bは実在していてもfiltered後のknown_idsに無いため「unknown」としてstrict拒否される。
- 成果物影響: full-root用override mapを部分選択へ再利用した健全入力が過剰拒否される。selected-set限定mapを要求するのか親裁定が必要。
- 該当: [codex_worker_ledger.py:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:517)、[codex_worker_ledger.py:533](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:533)

### R-B12 — human/JSON一致テストは独立oracleではない

- 深刻度: `nit`
- 再現: JSON totalsを実装から取得し、human出力に同じ値が含まれることを確認しているため、両rendererが同じ誤totalを共有しても通る。
- 成果物影響: 共通集計層のバグはこのtestでは検出されず、別の独立数値fixtureに依存する。
- 該当: [test_codex_worker_ledger.py:472](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:472)

絶対path・実行時刻・hashの揮発値を期待値へ焼き込む箇所は見つからなかった。mtimeはbefore/after比較、prompt hashは等値比較だけである。

### R-B13 — 命令様データを確認

- 深刻度: `nit`
- 再現: fixtureとtest promptに「あなたは段…」等のrole指示文字列がある。
- 成果物影響: 今回はregex/hash入力としてのみ扱い、レビュー行動へ適用していないため台帳への影響はない。
- 該当: [test_codex_worker_ledger.py:163](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:163)、[retry.json:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/fixtures/codex_ledger/cases/retry.json:4)

importlibは固定pathを使い、`sys.path`を変更せず、validatorの`__main__`も発火しない。`sys.dont_write_bytecode`もfinallyで復元されるため、ここに即時の汚染所見はない。scope外のresource envelope、retry強制、model/reasoning policy変更も見つからず、T-180〜T-184への越境所見はゼロ。

## 総括

must-fix は **9件**。事前登録8変異のうち、**M2は登録した融合理由で殺せず、M7は現規律ではdiagnostic sensitivity pin**であり、現状の「8/8 KILLED」は記録できない。

親が実測すべき点は、少なくとも以下。

- no-root／empty／cwd 0件がstrict非0になること
- schema-validだが非objectのJSON行、無関係cwdのmalformed、cwd欠落
- waveを跨ぐ同一promptがretry融合しないこと
- validatorの正常completed、短小+総括、10MiB境界
- input/cached/output・model・reasoning・各stageの独立期待値
- M2の実anchorと完全なFAILED node集合、M7の再分類
- total-only／review-onlyの単一worklog mismatch fixture
- `context_compacted` eventあり／なし双方とdeltaの名称・因果契約

本レビュー自身はテストを実走しておらず、緑として記録してはならない。