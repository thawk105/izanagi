## 検査範囲

指定8ファイルと指定 worktree の実装を静的検査した。書込み・campaign・pytest は実施していない。出力ファイルのパスが未指定で、書込みも禁止されているため、本回答を成果物本文とする。

以下、`brief` は `parent-stage1-brief.md`、`plan` は `stage2-plan.md`、実装の省略パスは `orchestrator/campaign/` 配下を指す。

## 1. 完了条件が「適格在庫の増加」から「第1項だけの充足」へ後退している

- **所見**: brief の完了条件と plan の達成扱いは、T-2632 の要求を満たさない赤1件でも完了できる。
- **根拠**: `brief:26`「適格性述語の第 1 項を満たす行を 1 件以上得る」、`plan:192`「赤１行取得は brief の第１項に関する達成」。対して `t2632-ledger.md:1–2` は「適格な赤 precursor の在庫を 0 件から増やす」「適格条件は変えない」。
- **成果物影響**: 全条件適格数が0のまま T-2632 を完了と記録でき、台帳の達成状態が実在庫と乖離する。機械の201行受理集合は変わらない。
- **是正**: 第1項該当行の取得は中間成果とする。完了・不成立・継続未了を分け、全条件の証拠がない行を適格在庫へ算入しない。

## 2. 旧 checkpoint の停止と、現行 CLI の開始先を混同できる

- **所見**: 旧 base checkpoint の期限切れは正しいが、plan の probe は現行 CLI がその checkpoint を復元することを立証していない。
- **根拠**: `plan:148` は `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json` を読む。一方、`p3_s4_loop.py:2430–2431` は `layout = exploration_campaign_layout(str(ident.campaign_id(cfg)))`、`layout.py:596` は `root=os.path.join(root, "exploration", "campaigns", cid)`。停止自体は `p3_s4_loop.py:1270–1271` の `elapsed >= MAX_WALLTIME_S` と、`:2488–2493` の `"ran": False` で実効性がある。
- **成果物影響**: 旧成果物の継続不能を、現行起動経路も停止する証拠として記録すると、調達可否と再開条件を誤る。
- **是正**: 「この旧 state を読み込ませれば停止する」と限定する。現行 cfg・環境・admission policy が決める campaign identity と出力先を別に確認する。時刻改変や停止回避は行わない。

## 3. 新規通常 campaign の既存起動経路は実在する

- **所見**: 新規開始経路は将来の仮説ではなく既存実装に存在するが、今回使える入力一式と適格赤の生成可能性は未確認である。
- **根拠**: `p3_s4_loop.py:2483–2485` は checkpoint 不在時に `state = LoopState(start_wall=time.time())`。`tools/pegasus/p3_s4_loop_pegasus.sh:581–587` は proposal 指定時に `--allow-coder-derived-build`、`--isolate-worktree`、`--fetchcontent-prebuild-receipt`、`--run-iteration` を渡す。`tools/pegasus/README.md:328` は「親が直接 `qsub` する」、`:368–370` は固定SHAの専用 checkout と外部 evidence root を要求する。
- **成果物影響**: この経路を未調査のまま調達不成立の根拠にすると、利用可能な通常合成を検討せず台帳を閉じることになる。ただし経路の存在だけで適格在庫数は増えない。
- **是正**: 段4では次の既存起動形に必要な実体の有無を判定する。未確認のパスを埋めた実行可能 command としては報告しない。

非K2の自然な proposal を渡す起動形は、既存 README の指定に従うと次である。これは未実行のテンプレートである。

```bash
qsub -v IZANAGI_S4_REPO_ROOT="$S4_REPO",IZANAGI_S4_EXPECTED_HEAD="$S4_HEAD",IZANAGI_S4_EVIDENCE_ROOT="$S4_EVIDENCE",IZANAGI_S4_THIRDPARTY_SOURCE_ROOT="$S4_THIRDPARTY",IZANAGI_S4_PROPOSAL_PATH="$S4_PROPOSAL" \
  -o "$S4_EVIDENCE/job.stdout" -e "$S4_EVIDENCE/job.stderr" \
  "$S4_REPO/tools/pegasus/p3_s4_loop_pegasus.sh"
```

必要条件は固定SHAの専用 checkout、tracked clean、CCBench pin 一致、自然な role 出力 proposal、外部の新規 evidence directory、hydrate 済み依存 source、policy に一致する gflags/glog、Python 3.10、PBS allocation と計測の単独性である。job body は現在の `.claude/worktrees/` 配下を拒否する（`:116–119`）。proposal を省くと fixture 分岐になる（`:588–593`）ため、本件では省略できない。

この段では専用 checkout・proposal・環境の実在一式を確認していない。新規 campaign の正当性と bootstrap・参照点・非汚染の証明も別途必要である。

## 4. `--no-build` の逐語は「適格性の独立した禁止述語」ではない

- **所見**: plan 本文の「適格在庫の調達完了を保証しない」は支持できるが、それを「`--no-build` 由来だから必ず不適格」と強める根拠は示されていない。
- **根拠**: `p3_s4_loop.py:2527–2529` は `"No-build is a wiring-only path"`、`"not an admitted campaign consumer input"` とし、`:2530` で `critic_digest_generated=False` にする。凍結述語 `prereg-s5-1-1-population.md:31–40` には build フラグによる独立した除外はない。build 有効時も `p3_s4_loop.py:1911–1913` は `rejected` を記録して build 前に返る。
- **成果物影響**: build フラグを追加の適格性述語にすると除外集合を変える。逆に build 有効を適格の証明にすると、校正・bootstrap・共通参照点・非汚染が未証明の行を算入する。
- **是正**: `--no-build` は今回の調達経路として採用しないという運用判断に留める。build 有効の自然な検疫 reject も、全凍結条件を満たした場合だけ候補から適格へ昇格させる。

## 5. 保存済み proposal の許容は、自然発生という呼称だけでは成立しない

- **所見**: plan に明示的な母集合製造の許可はないが、保存済み proposal の処理を新規 campaign へ移すだけでは適格性は引き継がれない。
- **根拠**: `plan:135` は「保存済みの自然な proposal を処理する場合も、その一部として扱う」と同時に「失敗しそうな proposal だけ選ぶ経路は設けない」とする。凍結本文 `prereg-s5-1-1-population.md:38` は「事前に固定した bootstrap 集合に属する。実走開始後に足さない」、`:40` は「どちらのアームの digest も受けていない」。
- **成果物影響**: 保存物の出自・固定時点・選択経緯を省略すると、事後選別や digest 汚染のある行を適格として扱い、manifest の先頭201行が変わり得る。
- **是正**: 当該保存物について既存の固定証拠・生成時入力・予定 attempt との対応を確認する。確認できなければ適格とは数えない。新しい gate や台帳は追加しない。

## 6. P1-b の循環指摘と base 限定は倒れない

- **所見**: 母集合欄の空欄から bootstrap 所属不能を導く親の説明は誤りであり、plan の訂正と現登録での base 限定は支持される。
- **根拠**: `prereg-s5-and-s5-1.md:43–45` は「`analysis_manifest` が実在し」「artifact path と sha256 と行数」を記入条件とする。`p3_b4_analysis_ledgers.py:928–930` は所属真偽値を入力として使う。対象 driver は `prereg-s5-and-s5-1.md:5` の `"base (silo-backoff-magnitude)"`、`:47` は「driver の差替え」を不成立とする。
- **成果物影響**: 親の説明を残すと、manifest 生成前に必要な bootstrap 証拠の独立評価を止める。一方、sort/trigger の赤を代用すると、選択済み driver と異なる母集合になる。
- **是正**: P1-b を「独立した証拠が未確認」と訂正する。空欄を所属偽の証拠にしない。sort/trigger の赤は原因分類の検査に留め、現登録の代替在庫へ算入しない。

P1-a は**記録分類として**支持される。sort の oracle/auditor 拒否も `record_diff_reject` と `"rejected"` に写る（`p3_s4_loop_sort.py:261–272`）ため、原因まで純粋な diff 検査に限定する読みは倒れる。P1-d の「CLI 自身は LLM を生成しない」は `p3_s4_loop.py:2544` と `:2768` が支持するが、開発 wave 内で通常合成を行えるかという運用上の裁定までは実装から導けない。

## 7. 既存 gate は非恒真だが、証拠の真実性までは保証しない

- **所見**: plan が維持する適格性・201行・issuer の不足拒否は実効的な分岐であり、現物の所属証明まで機械検証するものではない。
- **根拠**: `p3_b4_analysis_ledgers.py:1071–1083` は `_attempt_is_eligible(attempt)` で選別し、不足時に `B4DesignNotFeasible`、充足時に `eligible[:EXPECTED_BLOCK_COUNT]` を返す。`p3_b4_prerun_issuer.py:835–843` はその戻り値で `_reject(...DESIGN_NOT_FEASIBLE...)`。ただし所属値の検査は `p3_b4_analysis_ledgers.py:337–338` の `type(value) is not bool` である。
- **成果物影響**: gate 維持だけを適格証拠の保証とすると、根拠のない真偽値でも件数条件を満たせる。完全性検査も与えられた予定入力との整合性であり、未申告の予定 attempt が存在しないことを単独では証明しない。
- **是正**: gate の保証範囲を「入力述語・順序・件数・台帳整合性」に限定して記録する。所属や予定全件性の根拠は既存証拠で確認する。発火の実走検証は親に残す。

## 8. 不成立の記録は plan の限定を採り、親の「構造的理由」を撤回すべきである

- **所見**: plan の限定付き不成立記録は妥当だが、brief の構造的不可能を要求する完了条件とは両立しない。
- **根拠**: `brief:26–27` は「得られない構造的理由を実測で確定」。対して `plan:180` は「新しい通常 campaign で自然な赤が生じないことの証明ではない」、`:193` は「この wave では調達不成立」「構造的に不可能と一般化しない」。
- **成果物影響**: 旧3 checkpoint の在庫0と期限切れを構造的不可能として insight に残すと、材料レポートや後続判断が未実施の供給経路まで否定した証拠として引用できてしまう。
- **是正**: 「調査対象の在庫0」「旧 state の継続停止」「新規調達未実施／入力未確認」を別々に記録する。T-2632 の未達を構造的不可能や観測された非有意へ変換しない。

## 総括

- **倒れた主張**: 親の「第1項の赤1件で T-2632 完了」、母集合欄の空欄を bootstrap 判定不能の原因とする説明。旧 checkpoint の停止を現行 CLI 全体の NO-GO へ広げる読みも成立しない。
- **倒れずに残った主張**: 調査対象の在庫0、旧 state の入口停止、記録上の reject/fail 区別、base 限定、201行未満の実走拒否。plan に凍結契約の明示的な緩和や事後選別の許可は見つからなかった。
- **段4で必ず裁定すべき択一**: 正当な通常 base campaign の入力・環境・証拠を確保して本 wave で調達へ進むか、今回は観測と未達理由だけを記録して T-2632 を未了に残すか。どちらでも、第1項の素材取得を全条件適格在庫の増加とは扱わない。