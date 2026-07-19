# 2026-07-19 backlog-triage wave — codex 敵対相談 逐語凍結 (F20)

- 構成: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=repo
  (worktree s8b-c22-launch-cert, 相談時基準 5073116。相談 CC-3 により branch は main 80343a2 基点へ
  付け替え済み — tree 同一)
- 相談 3 本 (並列): CA=発掘方法論攻撃 / CB=裏取り・棚卸し表設計攻撃 / CC=プロセス・文書契約攻撃
- 親裁定: 22 所見中 real 21 / 前提一部 refuted 1 (CC-1)。プラン v2 への反映は
  docs/handoff/2026-07-19-backlog-triage.md (完了時は worklog 2026-07-19 エントリ) を参照

## CA (発掘方法論) プロンプト (逐語)
```
あなたは敵対的レビュアーです。私 (オーケストレータ) の「未消化タスク棚卸し」プランのうち、発掘方法論 (X1〜X3) を攻撃してください。
前提: docs/handoff/2026-07-19-backlog-triage.md (プラン v1 全文) を読むこと。基準 HEAD 5073116。
攻撃観点 (これに限らない):
1. 「黙って落ちた」判定の偽陽性・偽陰性 — 意味ベース突合で codex/claude が「消化済み」と誤判定する具体的な失敗形は何か。実際に docs/archive/worklog-phase3-0702-0713.md と docs/archive/worklog-phase3-0714-0716.md の「### 次の一手」を数エントリ精読し、言い換え・分割・部分消化 (項目の半分だけ消化) の実例があるか確かめよ
2. 掃引の網羅性 — 「### 次の一手」見出し以外の場所 (本文中の「後で」「次セッションで」等の約束、handoff 由来の項目、insight 内の推奨) に落ちた項目は存在しないか。実際に grep して漏れ経路を実証せよ
3. X3 の抜き取り検証設計 (7/5 台帳創設時の過去分掃引の完全性を 5 件逆引き) は統計的に意味があるか。もっと強い検査が同コストで可能か
4. 判定単位の曖昧さ — 1 項目が複数サブ項目を含むとき (例: 「AとBをやる」) の帰結判定規約が未定義ではないか
出力: 所見ごとに {severity: high/medium/low, 攻撃シナリオ (何がどう壊れるか具体的に), 根拠 file:line, 提案}。所見ゼロならゼロと明言し、検算した実例を示すこと。
```

## CA 出力 (逐語, tokens used 201,853)

結論: X1〜X3 v1 のままでは「黙って落ちた項目を網羅した」とは主張できません。所見は 4 件です（high 2、medium 2）。基準 HEAD `5073116ab73b`、変更は行っていません。

1. 見出し限定の母集団から、実在する高リスク未処置項目が漏れる

- severity: high
- 攻撃シナリオ: X1〜X3 は `### 次の一手` だけを起点にします。しかし実際には、本文の「持ち越し」、inline の `**次の一手:**`、セッション末追記、handoff、insight 推奨に約束が存在します。実例として、`hole` 内コメントの機械拒否は insight で「real・反証不能・高推奨」とされ、F 段 handoff へ申し送られ、本文で持ち越されましたが、直後の `### 次の一手` から消えています。現 HEAD のテストは今も `//` コメントを通す正例を固定しており、未消化です。X1 の抽出母集団には入らないため、本物の偽陰性になります。
- 根拠: X1〜X3 の限定は [backlog-triage.md:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:19)。高推奨は [strategy-review-headline-axis.md:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-12_strategy-review-headline-axis.md:33)、実装前 should-fix 束は同 [line 36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-12_strategy-review-headline-axis.md:36)。handoff 申し送りは [worklog-phase3-0702-0713.md:1905](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0702-0713.md:1905)、本文持ち越しは同 [line 1975](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0702-0713.md:1975)、直後の次の一手からの脱落は同 [line 1978](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0702-0713.md:1978)。コメント通過テストは [test_diff_quarantine.py:430](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_diff_quarantine.py:430)。ほかにも inline 次手が [worklog-phase3-0702-0713.md:1082](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0702-0713.md:1082)、見出し外の再開手順が [worklog-phase3-0714-0716.md:943](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:943) にあります。
- 提案: 先に source-side の候補集合を作るべきです。`次の一手|持ち越し|人間判断待ち|未着手|別タスク|次セッション|再開手順|要確認|推奨` を高 recall で抽出し、worklog 本文・現存/履歴上の handoff・insight の `real + must/should/推奨` を和集合にする。その後に人間/LLM が義務か単なる説明かを裁定してください。現存する別 handoff を除外するなら、除外範囲も明文化すべきです。

2. 1 項目を 1 状態へ落とす規約では、実在する部分消化を表現できない

- severity: high
- 攻撃シナリオ: 「層3 renderer の対象拡大」と「機序仮説層の原料配線」は同じ 1 項目でした。後続では前半だけ完了し、後半は v3 へ繰延されています。この項目を `(a) 消化` とすれば後半を落とし、`(b) 継続` とすれば完了済みの前半を未完扱いします。同型として、「bench-first ablation + pin literal 4 ファイル修正」は、ablation が継続する一方、pin 修正は「保持」という理由付き非実施へ分岐しています。また「selector/driver 実装 + oracle 実測」も実装だけ完了し実測は gate 待ちです。
- 根拠: 元の複合項目は [worklog-phase3-0714-0716.md:708](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:708)、部分消化は同 [line 757](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:757)、v3 繰延は同 [line 762](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:762) と [phase3.md:359](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:359)。ablation/pin の複合項目は [worklog-phase3-0714-0716.md:470](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:470)、pin 保持裁定は同 [line 620](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:620)、ablation 継続は [phase3.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:32)。実装と実測の混在は [worklog-phase3-0714-0716.md:772](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:772) と同 [line 823](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:823)。
- 提案: `A と B`、独立した矢印段階、異なる成果物・所有者・発火条件を持つ節は、判定前に原子的 child へ分割する。親は全必須 child が terminal のときだけ閉じる。状態も `done / continued / blocked(owner) / deferred(trigger) / rejected(reason) / superseded(by) / partial(children)` を持たせ、「黙って落ちた」は状態ではなく「terminal disposition も live carrier もない」という派生判定にしてください。

3. 「意味ベース + commit に痕跡」は、同名別物を誤って消化済みにできる

- severity: medium
- 攻撃シナリオ: S-1 には `known_axes_freeze.json` の再凍結と、別物の measurement freeze 生成があります。前者が完了した後も後者の実体は未生成でしたが、どちらも本文では「S-1 freeze」「freeze 実体」「再凍結」と省略されます。LLM が話題類似度や commit message の「freeze」を根拠にすると、別成果物の完了を流用して偽の「消化済み」を付けられます。逆に、`renderer 対象拡大`→`sweep 対応` のような具体化を別物と扱えば偽の「黙って落ちた」になります。
- 根拠: known-axes の具体的パスと作業は [worklog-phase3-0714-0716.md:470](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:470)、完了は同 [line 482](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:482)。別の measurement freeze generator は同 [line 498](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:498)、その実体未生成は同 [line 611](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0714-0716.md:611)。プランは「痕跡」で消化を認めています [backlog-triage.md:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:20)。
- 提案: 意味一致は候補生成にだけ使い、閉鎖根拠にはしない。各原子項目に「対象 artifact/path、完了述語、必要 test/裁定、owner」を付け、`done` はその述語を直接満たす file:line/commit がある場合だけ許す。対応関係も `same / split-into / merged-from / superseded / unrelated` として明示し、単なる commit 言及は補助証拠へ降格すべきです。

4. X3 の「5 件逆引き」は完全性検査として統計的情報がない

- severity: medium
- 攻撃シナリオ: 台帳に入った既知 5 件を逆引きしても、検査できるのは「台帳項目の出所が正しいか」という precision/provenance です。台帳に入らなかった項目は抽出確率 0 なので、真の漏れが 0 件でも 100 件でも 5/5 成功します。recall、すなわち「source にあった項目が台帳へ入った割合」には何の下限も与えません。親の「無作為 5 件」も母集団・seed・原子化規約がなく、同じ意味判定バイアスを再演できます。
- 根拠: X3 の設計は [backlog-triage.md:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:25)、親の 5 件検算は同 [line 41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:41)。台帳の目的と既知 5 件は [phase3.md:385](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:385)。7/5 より前の `### 次の一手` は実際には 10 ブロック（行 33, 136, 166, 190, 237, 283, 345, 374, 404, 453）あり、先頭は [archive:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0702-0713.md:33)、末尾は [archive:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase3-0702-0713.md:453)。
- 提案: 「5 件逆引き」は出所監査と改称する。完全性には source-side forward tracing を使う。同コストで強くするなら、5 件の逆引きで到達した各 source エントリについて、その項目だけでなく同じ本文・兄弟項目を全列挙して前向き追跡する。さらに見出し母集団だけなら 7/5 前は 10 ブロックなので全数検査が妥当です。抜き取りを残すなら、原子化後の source 母集団 N、層化規則、seed を固定し、本文・handoff・insight を必ず各 1 件含めてください。

## CB (裏取り・表設計) プロンプト (逐語)
```
あなたは敵対的レビュアーです。私 (オーケストレータ) の「未消化タスク棚卸し」プランのうち、裏取り (X4) と棚卸し表・推奨処置の設計 (X5) を攻撃してください。
前提: docs/handoff/2026-07-19-backlog-triage.md (プラン v1 全文) を読むこと。基準 HEAD 5073116。
攻撃観点 (これに限らない):
1. 見送り台帳未完 5 件 (docs/phase3.md の見送り台帳節を読め) それぞれについて、「前提が生きているか」の裏取りに何を証拠と数えるべきか。プランは証拠基準を定義していない — 各件の検証に必要な具体的ファイル・節を挙げ、裏取りが浅くなる失敗形を示せ
2. 推奨処置 3 分類 (昇格・発火条件付き保留・理由付き廃棄) の判定基準が恣意的にならないか。「廃棄には理由の記録が必要」という台帳規約と整合するか。発火条件の書き方が曖昧だと将来また黙って落ちる — 発火条件の要件を定義せよ
3. 裁定中立性 — 表の書き方がユーザー裁定を先取り・誘導する形 (推奨を確定扱いにする等) になる危険。越権の具体的検査項目を挙げよ
4. 追加登載 2 種 (xdist flake 項、テスト調査の発火条件付き施策 3 件) の登載形式は既存台帳項目と整合するか。output/insights/ の書式規約 (output/README.md) と衝突しないか
出力: 所見ごとに {severity: high/medium/low, 攻撃シナリオ, 根拠 file:line, 提案}。所見ゼロならゼロと明言せよ。
```

## CB 出力 (逐語, tokens used 202,332)

基準 HEAD は `5073116ab73b3b9993835aefc0873b550ebad28f` と一致しました。所見ゼロではありません。high 5 件、medium 6 件です。

1. balanced backoff は「実装可能」と「取得済み」を誤同定できる

{severity: medium

攻撃シナリオ: X4 が `POINTS` に balanced がある、または docstring に「write-heavy + balanced」とあるのを見て「部分吸収済み／廃棄可能」と判定する。しかし既定実行は write-heavy のみで、追跡済み成果物も rr5 だけである。論文メモ自身も balanced profile 未取得を明記している。

根拠 file:line: [docs/phase3.md:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:391)、[orchestrator/campaign/backoff_profile.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:20)、[orchestrator/campaign/backoff_profile.py:225](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:225)、[output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.md:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.md:1)、[docs/paper-story/notes-2026-07-10.md:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/paper-story/notes-2026-07-10.md:7)

提案: 「取得済み」と数える証拠を、現 pin・balanced (`rratio=50`)・0/2/5/10/25/50/100µs 全点を持つ committed JSON/MD、trace-disabled、環境・thread・records・診断ノブの inert 性を束縛したもの、と定義する。X4 は read-only なので、現状は「driver は対応、成果物なし、未消化」とするべきである。}

2. over-throttle の「効果確認」と「機序分離」を混同できる

{severity: high

攻撃シナリオ: `phase2.md` や insight の「機序的に閉じた」を拾い、MLP 低下 vs cache 余熱の分離まで完了扱いする。実際に閉じたのは sweet-spot の spin 希釈であり、over-throttle 側は有用 IPC 低下の方向を観測しただけで、現ドライバの主要カウンタは cycles/instructions または spin/abort/tps に限られる。

根拠 file:line: [docs/phase3.md:392](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:392)、[docs/phase2.md:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase2.md:106)、[output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:184](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:184)、[output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:190](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:190)、[orchestrator/campaign/backoff_profile.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:47)、[orchestrator/campaign/backoff_overthrottle.py:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_overthrottle.py:63)

提案: 完了証拠には、MLP 仮説と cache-warmth 仮説の反対予測を事前に書き、少なくとも outstanding-miss/stall 系と LLC miss/MPKI・warm/cold 制御を組み合わせた識別実験を要求する。同じ useful IPC 系列の再解釈は分離証拠に数えない。現状の正しい裁定材料は「二次効果 real、原因未分離」である。}

3. mocc trace-hook は汎用 S1 の存在だけでは吸収されない

{severity: medium

攻撃シナリオ: 「S1 発火時に吸収」と書かれているため、S1 行が存在するだけで mocc 項を吸収済みにする。逆に、任意の cross-protocol 着手を mocc 固有 hook の自動発火とみなす。現 pin の MOCC source は trace header/hook を持たず、探索空間も silo のみで、hook 無し protocol は pipeline の空 trace reject に落ちる。

根拠 file:line: [docs/phase3.md:393](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:393)、[docs/phase1.md:143](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase1.md:143)、[external/ccbench/cc/mocc/transaction.cc:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/mocc/transaction.cc:1)、[orchestrator/campaign/genome.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/genome.py:87)、[docs/phase3.md:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:185)、[orchestrator/campaign/pipeline.py:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:512)

提案: 発火条件を「MOCC を certified な live 比較に採用する」または「visible/invisible reads の正しさ比較を復活させる」に限定する。吸収完了には、現 pin の `#if TRACE` hook、commit/read/write 被覆、commit 数一致、orphan/dup なし、TRACE=0 symbol 不在、MOCC 実トレースの certified 結果を要求する。}

4. ermia の前提は現 pin の live call path と既に不一致

{severity: high

攻撃シナリオ: 古い「`cstamp<<1`・commit 二系統」をそのまま実装仕様として採用し、現 live path の版 ID を誤写像して全 read を orphan 化する。現 source では shifted cstamp を使う `ssn_commit()` は定義されている一方、公開 `commit()` は `ssn_parallel_commit()` だけを呼び、その経路は version に未 shift の `cstamp_` を保存している。

根拠 file:line: [docs/ccbench-anatomy.md:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ccbench-anatomy.md:211)、[external/ccbench/cc/ermia/transaction.cc:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:503)、[external/ccbench/cc/ermia/transaction.cc:553](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:553)、[external/ccbench/cc/ermia/transaction.cc:765](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:765)、[external/ccbench/cc/ermia/transaction.cc:905](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:905)

提案: この行は「未消化」の前に「前提要再定義」と裁定する。現 pin の call graph、reachable commit path、初期版、read が観測する版 field を再導出してから hook 仕様を決める。完了証拠は同一 workload で si 赤／ermia 緑、両方 integrity clean、commit 数一致、TRACE=0 compile-out とする。古い罠メモの存在自体は証拠に数えない。}

5. calibration 項は二つの独立タスクで、段6(b) は現在も休眠かつ K を吸収しない

{severity: high

攻撃シナリオ: phase3 の「protocol 別 calibration」を見て K 感度も thread 変更も部分吸収済みにする。また JSON に 4-thread の点があるため再 calibration 済みと誤認する。段6(b) は旧 headline 復活時のみの休眠タスクで、K sweep を含まない。JSON の 4-thread 点は scale sensitivity の単点で、4-thread 用の records sweep/noise calibration ではない。

根拠 file:line: [docs/phase3.md:395](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:395)、[docs/phase3.md:263](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:263)、[docs/phase3.md:268](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:268)、[docs/decisions.md:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:222)、[orchestrator/calibrator/analyze.py:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/analyze.py:24)、[output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:70)、[orchestrator/calibrator/sweep.py:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/sweep.py:247)

提案: `K 感度`と`thread 変更時の再 calibration`を別行にする。K 完了証拠は事前登録した K 範囲ごとの採用 N・miss・working-set 結論表。現 sweep は最小 1m で既に L3×6.6 のため、低い K の感度は左打切りされており、必要なら sub-1m が要る。thread 完了証拠は各 live thread 数について workload 署名付きの完全な records sweep、採用 N、within/between floor を持つ `calibration_t<T>_*` であり、scale 単点は数えない。}

6. 3分類が事実状態と処置を混ぜ、完了・吸収・裏取り不能を強制的に「廃棄」へ落とす

{severity: high

攻撃シナリオ: X4 が「既に完了」「別タスクへ完全吸収」「起源の主張が refuted」「証拠不足」を見つけても、X5 の選択肢は昇格・保留・廃棄しかない。結果として完了を廃棄と記録したり、証拠不足を価値なしへ変換する。既存台帳は実際には「完了」を独立状態として保持している。

根拠 file:line: [docs/handoff/2026-07-19-backlog-triage.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:31)、[docs/phase3.md:389](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:389)、[docs/phase3.md:396](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:396)、[docs/phase3.md:399](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:399)

提案: 二軸化する。

- 事実状態: `未消化 / 部分吸収 / 完全吸収・完了 / 前提消滅・refuted / 重複 / 裏取り不能`
- AI 処置案: `昇格候補 / 条件付き保留候補 / 廃棄候補 / 正本の完了記録だけ更新`
- 人間裁定: 常に `未裁定`

昇格は「現行承認 scope の blocker、または trigger が既に真」、保留は「価値は生存・trigger は偽」、廃棄は「active consumer なし、目的が superseded/refuted/重複である一次証拠あり」とする。低優先度や高コストだけでは廃棄不可とする。}

7. 発火条件に必要な実行可能性が定義されていない

{severity: high

攻撃シナリオ: 「必要になったら」「S1 発火時」「スイートが遅くなったら」のような自己参照・主観条件を置き、誰も評価せず再び黙って落ちる。または異なる環境で一度閾値を超えただけで不要な作業を発火させる。

根拠 file:line: [docs/handoff/2026-07-19-backlog-triage.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:32)、[docs/axis-onboarding.md:144](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/axis-onboarding.md:144)、[docs/axis-onboarding.md:229](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/axis-onboarding.md:229)

提案: 各保留行に最低限、次を必須化する。

- 一意 ID と、真偽値で書ける predicate
- 観測対象、コマンド／artifact、対象 commit・環境
- 閾値、統計量、反復数
- 現在値、現在は真か偽か、最終確認日
- 誰が・どの checkpoint で再評価するか
- 真になった際の具体的 action、反映先、完了条件
- 失効・supersede 条件

「S1 発火時」は「旧 headline 2 の復活がユーザー承認された、または段7 cross-protocol が active task に昇格した」のように展開する。}

8. 「テスト調査の発火条件付き施策 3件」は元資料を変形している

{severity: medium

攻撃シナリオ: 元資料では条件付き施策は表の #6 と #7 の2行で、#7 は coverage と差分 mutation を一つにまとめている。X5 がこれを「3件すべて発火条件付き」と再記述すると、coverage 観測と mutation 標準化に存在しなかった裁定・trigger を捏造する。

根拠 file:line: [docs/handoff/2026-07-19-backlog-triage.md:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:33)、[output/insights/2026-07-19_test-suite-hygiene-survey.md:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:118)、[output/insights/2026-07-19_test-suite-hygiene-survey.md:127](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:127)、[output/insights/2026-07-19_test-suite-hygiene-survey.md:128](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:128)

提案: source ID #6/#7 を保存する。#7 を二分するなら「X5 による派生案・未裁定」と明記する。trigger は別々に設計する。

- fixture 共有化: 指定 runner・指定環境で full suite median が180秒超、かつ ratified_verify git fixture が有意な時間占有を持つこと
- coverage: hygiene wave または安全 gate 変更時の観測イベント。達成率 gate は禁止
- 差分 mutation: validator／拒否 gate の変更または escaped defect 発生時。対象 diff、operator、予算、結果の扱いを固定

全体時間だけでは fixture が遅さの原因とは言えない。}

9. xdist flake の「tracked のみ」案は元テストの保証を弱めうる

{severity: medium

攻撃シナリオ: 1/4 flake の対策として status 比較を tracked-only に変更し、SUT がリポジトリ直下へ untracked ファイルを漏らす回帰を見逃す。元テストの契約は「実 repo tree 不変」であり、tracked-only は同値な修正ではない。一方、原因は xdist worker の untracked 出入りという有力仮説だが、単発再現しないため causal attribution も未確定である。

根拠 file:line: [docs/worklog.md:814](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:814)、[docs/worklog.md:824](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:824)、[output/insights/2026-07-19_test-suite-hygiene-survey.md:159](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:159)、[orchestrator/tests/test_s8b_protocol_builder.py:256](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:256)、[orchestrator/tests/test_s8b_protocol_builder.py:266](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:266)

提案: 棚卸し行を「観測済み flake」「原因仮説」「保証契約」「修正候補と保証差」「acceptance」に分ける。直列化／隔離 worktree は保証を保つが速度を失い、tracked-only は保証を弱める、と対称に記す。tracked-only を採るなら、SUT の tracked・untracked 両方の repo-root 漏出を殺す別 positive control を必須にする。}

10. 「推奨」列だけでは裁定中立性を機械的に検査できない

{severity: medium

攻撃シナリオ: 見出しではユーザー裁定待ちでも、各行を「廃棄」「昇格」と断定形・太字・先頭選択肢で書き、代替や反証を省く。commit 済み文書が事実上の裁定として後続 AI に読まれる。現プランには人間裁定欄、代替案、非発効宣言が schema としてない。

根拠 file:line: [docs/handoff/2026-07-19-backlog-triage.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:31)、[docs/handoff/2026-07-19-backlog-triage.md:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:35)、[output/insights/2026-07-14_strategy-review-overall-direction.md:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-14_strategy-review-overall-direction.md:14)、[output/insights/2026-07-16_s8b-floor-protocol-package.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-16_s8b-floor-protocol-package.md:3)、[output/insights/2026-07-16_s8b-floor-protocol-package.md:581](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-16_s8b-floor-protocol-package.md:581)

提案: R3 の越権検査を明記する。

- 冒頭に「裁定資料・非正本・承認まで何も発効しない」
- `事実状態 / 反証・不確実性 / AI推奨（非拘束） / 代替案 / ユーザー裁定（未裁定） / 反映先`
- phase3/worklog の状態、checkbox、台帳行を裁定前に変更していない
- 推奨を factual verdict や priority として記述していない
- 推奨と非推奨で証拠粒度・強調・並びを不当に変えていない
- commit/worklog が「廃棄完了」「昇格完了」と宣言していない
- 原項目の逐語・出所・最強の反対根拠が保存されている

}

11. `output/insights` の棚卸し表が第二の生きた台帳になりうる

{severity: medium

攻撃シナリオ: X5 の表を裁定後も更新し続け、phase3/worklog と二重に状態を持つ。また廃棄理由を insight にだけ残し、phase3 の「理由をここに書く」規約を満たしたつもりになる。`output/insights` は証拠・散文の射影先であり、可変状態の正本ではない。

根拠 file:line: [docs/handoff/2026-07-19-backlog-triage.md:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:44)、[CLAUDE.md:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:153)、[output/README.md:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:42)、[output/README.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:47)、[output/README.md:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:63)、[docs/phase3.md:389](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:389)

提案: X5 文書を「基準 5073116 の探索妥当性監査スナップショット・非正本・Izanagi 内部項目につき CCBench 還元判断は非該当」と固定する。裁定後は書き換えず、既存5件の廃棄理由・完了・昇格は phase3 の元行へ日付・理由・証拠 pointer 付きで反映する。追加項目には行ごとに正本反映先を指定し、phase3 に属さない保守項目を無理に研究台帳へ混ぜない。}

## CC (プロセス契約) プロンプト (逐語)
```
あなたは敵対的レビュアーです。私 (オーケストレータ) の「未消化タスク棚卸し」プランのプロセス・文書契約面を攻撃してください。
前提: docs/handoff/2026-07-19-backlog-triage.md (プラン v1 全文) を読むこと。基準 HEAD 5073116。
攻撃観点 (これに限らない):
1. 着手判断 — handoff の着手条件「ユーザーの着手 GO」を包括的ループ指示で充足と解釈した。この解釈の危険と、worklog への記録形式として十分な開示は何か
2. branch 基点 — 未 merge の test-hygiene HEAD (5073116) から backlog-triage を分岐した。test-hygiene が merge されない/修正される場合の帰結と、代替 (main 分岐) との比較。本作業の成果物 (insight 1 ファイル + handoff/worklog) が test-hygiene の成果物 (survey insight、flake 所見) を参照する事実を踏まえて判定せよ
3. 文書契約 — 棚卸し表を output/insights/ に置くのは output/README.md の書式・責務と整合するか。worklog 書式 (docs/worklog.md 冒頭 D35)、CLAUDE.md 作業の進め方 6a (可変状態の正本は worklog 末尾と現行 phase doc のみ — 棚卸し表が第 3 の TODO 正本にならないか)、check_docs.py の検査 (次アクション主張は worklog 末尾のみ、:145 付近) に抵触しないか。実際に tools/check_docs.py を読んで具体的な赤条件を特定せよ
4. C (2026-07-19-backlog-guard-mechanism.md, ID 機構) との相互作用 — B の表の項目粒度・形式が C の ID 付与を難しくしないか
5. 完了形の変形 (handoff を削除せず裁定待ち中断へ戻す) は docs/handoff/README.md の契約と整合するか
出力: 所見ごとに {severity: high/medium/low, 攻撃シナリオ, 根拠 file:line, 提案}。所見ゼロならゼロと明言せよ。
```

## CC 出力 (逐語, tokens used 151,193)

所見ありです（high 3 件、medium 4 件）。最大の問題は、B の個別 GO が未充足のまま、棚卸し結果が第三の TODO 正本になり得ることです。

### 1. 包括指示の再利用は、B の着手権限を満たさない

- severity: high
- 攻撃シナリオ: 包括的ループ指示は A の着手根拠として既に使用されています。その A 完了後に作られた正本の worklog 末尾は、改めて「B はユーザー GO 待ち」と明記しています。ここで同じ包括指示を B にも再利用すると、後発の明示状態を過去の曖昧な指示で上書きすることになります。「個別 GO ではない」と記録しても、権限不足自体は治りません。
- 根拠: [backlog-triage.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:11)、[worklog.md:817](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:817)、[worklog.md:826](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:826)、[CLAUDE.md:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:153)
- 提案: B 個別の GO を取り直す。worklog には少なくとも「指示日時・B 個別 GO の有無・許可範囲 X1〜X5・許可されない範囲（処置確定、phase 反映、C 着手）・直前 worklog の GO 待ちを上書きする後続指示か」を一項目で残す。個別確認がないなら、形式は「着手条件未充足のまま解釈で進めた逸脱」であり、「充足」と書いてはいけません。

### 2. 「他 handoff 空」の充足主張も事実と合わない

- severity: medium
- 攻撃シナリオ: 元の「3 プラン」は commit `95ed6fe` で導入された A/B/C です。A 削除後に残った B/C/observability を新しい「3 プラン」と数え直せば、observability を例外集合へ潜り込ませられます。しかし observability は別 commit 由来で、現在も `中断` として残り、worklog・output README・check_docs を将来編集する計画です。再開されれば B と衝突します。
- 根拠: [backlog-triage.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:10)、[test-suite-hygiene-survey.md:136](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:136)、[ai-development-observability.md:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:4)、[ai-development-observability.md:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:94)、[handoff/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:15)
- 提案: 例外対象を「3 ファイル」のような可変な数でなく、A/B/C のファイル名で固定する。observability が残るなら「条件未充足だが、所有者不在を確認し、競合ファイルを直列化する」と明示するか、ユーザーに waiver を求める。

### 3. 5073116 基点は証拠整合性には有利だが、成果物を stacked branch 化する

- severity: medium
- 攻撃シナリオ: test-hygiene が未 merge の状態で B を `5073116` から分岐すると、B を main に merge するだけで A のテスト変更一式まで暗黙に取り込みます。A が却下・amend・squash された場合は、B が旧 survey と旧 flake 証拠を参照し続けるか、cherry-pick 時に参照先を失います。一方、当時の main `240d1cc` から分岐すると、B が直接使う survey insight、consultations、worklog 所見が存在せず、証拠の永続性が落ちます。したがって「507 基点そのものが誤り」ではなく、「stacked 依存を独立成果物のように扱う」のが誤りです。
- 根拠: [backlog-triage.md:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:6)、[backlog-triage.md:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:33)、[worklog.md:806](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:806)、[test-suite-hygiene-survey.md:127](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:127)、[test-suite-hygiene-survey.md:159](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:159)
- 提案: 未 merge 時点なら「A merge 待ち後に main から B」を第一選択とする。先行するなら stacked dependency、merge 順 A→B、A 改訂時の X4/X5 再実行を handoff に明記する。なおレビュー時点では `5073116` は既に main の `80343a2` に merge 済みで、両 tree に差分はありません。今は `80343a2` を基点に直すのが最も明快です。

### 4. 棚卸し insight が第三の TODO 正本になり、棚卸し自身が「黙って落とす」

- severity: high
- 攻撃シナリオ: X5 は未裁定項目、発火条件、推奨処置を一覧化します。その後 worklog に新規エントリを足すと、現在の末尾にある flake 項目は末尾正本から外れます。しかし phase 反映は裁定後まで行わないため、項目の実体が insight と残 handoff にしかない空白期間が発生します。これは「worklog 末尾と phase doc だけ」という二正本契約への直撃です。既存の未裁定 insight でも、YAML は `pending` のまま本文が「全件裁定完了」になっており、lint 対象外文書の状態ドリフトは既に実例があります。
- 根拠: [backlog-triage.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:31)、[backlog-triage.md:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:44)、[CLAUDE.md:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:153)、[worklog.md:824](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:824)、[clarity-proposals-unadjudicated.md:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-17_clarity-proposals-unadjudicated.md:4)、[clarity-proposals-unadjudicated.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-17_clarity-proposals-unadjudicated.md:11)
- 提案: `output/insights/` は「凍結した監査証拠・裁定パッケージ」としてなら条件付きで適合します。冒頭に `authority: none`、`default_effect: no-state-change`、`as_of_commit`、`canonical_state: worklog tail + phase3` を明記し、行には現在の owner・進捗・次アクションを持たせない。B の中断時 worklog 末尾には、実際の次の一手として「ユーザーが B-001〜B-N の裁定パッケージを裁定する」と、既存の生きた項目の扱いを明記する。`output/README.md` の現行説明は CCBench/探索妥当性中心なので、プロセス監査も許すなら責務を一文追加するのが安全です。[output/README.md:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:17)、[worklog.md:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:19)

### 5. `check_docs.py` 緑は、この計画の文書契約をほぼ検証しない

- severity: high
- 攻撃シナリオ: C handoff は「次アクション主張は worklog 末尾だけ」という検査が既にあるように記述していますが、実装は `CLAUDE.md` と `roadmap.md` 内の字面 `次 =` だけを赤にします。insight、handoff、phase doc、worklog の次アクション保存則は検査しません。また handoff の許可状態値も検査せず、現在の不正な `実行中 (...)` や予定する `中断 (...)` は通ります。実際に現ツリーで実行した結果も `check_docs: 違反なし` でした。
- 根拠: insights/worklog/archive は living lint 対象外 [check_docs.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:21)。問題の検査は `doc.name in ("CLAUDE.md", "roadmap.md") and re.search(r"次\s*=", line)` のみ [check_docs.py:145](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:145)。handoff は「状態行なし」または `作業中|計測中` の 48 時間 stale だけが赤です [check_docs.py:208](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:208)。C の記述は過大です [backlog-guard-mechanism.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-guard-mechanism.md:36)。
- 提案: B の親検算に手動チェックを追加する。「insight に authority/status/next-action 正本なし」「worklog 新末尾に裁定待ちが残る」「phase 未反映であることを明示」「handoff 状態値が完全一致」の4点です。C 実装時は保存則の正負例に加え、許可外 handoff 状態値と insight 内 TODO が lint 対象外である境界もテストする。現行の具体的な赤条件は、pin 抽出失敗、D 見出し重複、列挙 living doc 不在、living doc の行番号参照・現 Phase 再掲・狭い `次 =`・pin literal・不存在 D/path、archive 索引不整合、worklog 100KB 超、handoff 状態行欠落または稼働状態 48h stale です。[check_docs.py:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:106)、[check_docs.py:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:113)、[check_docs.py:122](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:122)、[check_docs.py:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:172)、[check_docs.py:200](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:200)

### 6. B の「項目」粒度では C の ID 保存則を定義できない

- severity: medium
- 攻撃シナリオ: B は安定した行キー、分割・統合 lineage、原子的処置単位を定めていません。実データでも survey の一行は coverage と差分 mutation をまとめていますが、B は二施策へ分割しています。phase 台帳の calibration 行も K 感度と thread 数変更時の再較正を一項目にしています。C で一 ID を振ると片方だけ消化できず、二 ID にすると B の一行との対応が失われます。さらに C の「本文で ID に言及すれば消化」は、単なる参照でも保存済みと誤判定できます。
- 根拠: [backlog-triage.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:31)、[test-suite-hygiene-survey.md:128](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:128)、[phase3.md:395](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:395)、[backlog-guard-mechanism.md:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-guard-mechanism.md:20)、[backlog-guard-mechanism.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-guard-mechanism.md:24)
- 提案: B 表を「ユーザーが独立に採否・保留を裁定できる最小単位」一行にする。各行に監査ローカルキー `B-001`、`source_occurrences`、`split_from/duplicate_of`、構造化 trigger、依存関係、推奨、裁定後の canonical target を持たせる。`B-*` は証拠キーに留め、C の正式な `T-*` はユーザー裁定で生き残った原子行にだけ付与する。C の検査も単なる ID 出現ではなく、`consumed`・`continued`・`deferred-to-ledger` の明示遷移を要求すべきです。

### 7. 「完了形の変形」は中断としては正しいが、状態値と C の開始条件が壊れている

- severity: medium
- 攻撃シナリオ: ユーザー裁定待ちなら handoff を残すこと自体は契約に適合します。ただし現在の `実行中 (...)` は許可値でなく、予定する `中断 (ユーザー裁定待ち)` も「値は3つに限定」に反します。また B を「完了」と呼ぶと、C の「B 完了後」を満たしたと誤解して、裁定前の推奨項目へ ID を付け始められます。
- 根拠: [backlog-triage.md:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:4)、[backlog-triage.md:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-triage.md:44)、[handoff/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:15)、[handoff/README.md:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:27)、[handoff/README.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:36)、[backlog-guard-mechanism.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-backlog-guard-mechanism.md:10)
- 提案: マイルストーンを分ける。B1 は「棚卸し証拠完成・B は未完」で、ヘッダを正確に `- 状態: 中断`、別行に `- 中断理由: ユーザー裁定待ち` とする。B2 は裁定を worklog/phase に反映し、最終 worklog を書いて handoff を削除する段階。C の着手条件は「B handoff が消え、裁定済み surviving items が二正本へ反映済み」に変更する。

ファイル変更はしていません。診断として実行した `python3 tools/check_docs.py` は緑でしたが、上記のとおり、その緑自体が所見 5 の盲点を実証しています。

## 親裁定 (詳細)

- CA-1〜4: 全て real。母集団拡大 (本文約束マーカー + insights 推奨)、複合項目の原子化と 8 状態語彙、
  意味一致の候補限定 (done は完了述語の直接証拠必須)、逆引きの precision 監査への改称 + 前向き追跡
  (7/5 前 10 ブロック全数) をプラン v2 に反映。CA-1 の実例 (hole コメント機械拒否の脱落) は seeded
  検証として X6 に登載
- CB-1〜11: 全て real。台帳 5 件の完了証拠定義を X4 に焼き込み。二軸分離 (事実状態/AI 処置案/人間裁定)、
  発火条件の述語化、survey #6/#7 の出所忠実性、xdist flake 行の分解、裁定中立性 checklist (R3)、
  insight の凍結スナップショット化を X5 スキーマに反映
- CC-1: 攻撃シナリオの前提 (包括指示の「再利用」) は事実誤認で refuted — 本セッションの指示は
  worklog (5) commit 後にユーザーが発した新規発話。ただし提案は採用 (「充足」と書かず解釈による
  逸脱として記録、許可範囲 = 裁定パッケージ作成までを明記)
- CC-2: real。「3 プラン以外空」は observability handoff 残存で字義未充足 — 稼働セッションなし・
  編集対象直列化可を確認の上、逸脱として worklog に記録
- CC-3: real。main 80343a2 基点へ付け替え (5073116 は merge 済み・tree 同一)
- CC-4〜7: real。insight 非正本 header (authority: none 等)、check_docs 盲点の手動 4 点検査、
  行粒度 = 独立裁定可能な最小単位 + B-xxx 監査キー、handoff 状態値の契約 3 値化と B1/B2 分離、
  C 着手条件の更新をそれぞれ反映
