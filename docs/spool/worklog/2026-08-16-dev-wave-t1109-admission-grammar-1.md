---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1109-admission-grammar
seq: 1
title: 実機の job ID が admission を通らず 8c live が全面的に塞がっていた件を解き、失敗経路が診断 report を残せるようにした — 「実在値が自分の述語を通らない」型を族として positive control で撃つ (コード + テスト + docs、branch worktree-dev-wave-t1109-admission-grammar)
---

## 本文

- **ユーザー裁定 (2026-08-15 の /rulings 全件束、authority: ユーザー) を 3 件実装した。**
  [T-1109] = 択 (a) 受理文法を `(?:0:)?` へ拡張、[T-1110] = 択 (a) `transport-admission-error` を
  足す、[T-1111] = 義務づける (起動を止める型の fail-closed admission 述語に限定)。
  控えは wave 外の裁定 inbox にあり、branch `worktree-rulings-20260815-full` が未 land のため
  canonical worklog には本 wave 時点で未反映だった。
- **repo 自身が 526 file の反証を抱えていた。** `output/env/pegasus/calibration/job-staging/` には
  `0:867863.nqsv` 〜 `0:867876.nqsv` 等の**実機 `PBS_JOBID` を directory 名に持つ** tracked artifact が
  526 file あり、`reservation.json` は `"job_id": "0:867876.nqsv"` を持つ。
  transport の述語が「colon を含まない」と主張し続ける間、repo は同じ値を tracked で保持していた。
  **F97 型 (実在値が自分の述語を通らない) は、多くの場合 repo 内に既に反証が置かれている。**
- **本 wave の最重要の実測は [T-1110] の性質が想定と違ったことである。**
  完全性検査は「書かれた report を後から検証するもの」ではなく
  **report を書くこと自体の関門**だった ({{F:completeness-gate-blocks-its-own-report}})。
  実走 journal の `run-finish` は report path を書いているのに実体が無く、
  原因は検査の例外で書き込み行に到達していなかったことである。
  この所見は並行 job (8c live pilot 担当) が送ってきた journal を親が開いて確認する過程で出た。
  **同 job と親は、admission 失敗経路で発火する関門が
  `assert_autonomous_trial_completeness` ただ 1 つであることに独立に到達し、一致した**
  (build 系 3 関門は `fatal_error` / `cells` の guard で飛ぶ)。
- **段 3 の敵対 2 レンズは独立に NO-GO を返し、親 brief の誤りを 5 件反証した。** 特に
  「positive control の実在値は実走 journal から取れる」は偽で、**あの journal に job ID は無い**。
  一次出所を tracked artifact へ差し替えた。「族の member は 2 件」も偽で、
  実際は 8 件だった。「D96 が機械検査を一律禁止している」も過度な一般化だった
  (D96 は AST 案 1 件を却下し、独立 2 例と再裁定での再提案を明示的に許している)。
- **段 6 の敵対 2 レンズは production の防壁を崩せなかった。** early return による検査飛ばし、
  campaign root 免除の悪用、terminal 分岐の過剰拒否、`0:` 付き値による receipt 同一視や
  redaction の穴、既存負例の弱体化は**いずれも反証された**。
  **must-fix 5 件はすべて親の記録と変異登録の不備だった。**
- **親が段 4 裁定の前提を 1 件、実装子に反証されて訂正した。** member 7 (competing-bench) を
  「clean production probe の raw triple が repo に無い」として `unmet` にしていたが、
  tracked `isolation.txt` が 6 file (内部 53 記録すべて同一) 実在した。
  述語は生の 3 つ組をそのまま受け取るため正直な control が書ける。
  **「入力が無いので未達」と台帳に書けば実測に反する虚偽になる**ので、裁定へ addendum を書き、
  単位 D を追加した。段 6 レンズ A はこの不一致 (裁定文書に addendum が無いこと) を正しく突いた。
- **変異事前登録に 3 件の欠陥があり、本走前に訂正した。** (a) `_EVENTS` と `_TERMINAL_EVENTS` が
  同一 literal を共有するため裸の置換では 2 箇所に当たり帰属が壊れる、(b) 期待 nodeid が
  自動生成 ID 依存で確定しない、(c) **1 件が等価変異** (テストの独立 pin を production 定数参照へ
  替えるだけで、production が同じ文字列を持つため必ず生存する)。
  **(c) は本 wave が撃っている恒真ゲート型そのものであり、そのまま本走すれば
  「新設検査が捕まえた」と誤記録するところだった。**
- **副次的に、記録済み journal と現行 producer の shape が乖離していることを見つけた。**
  記録側の `run-start` は現行 producer が無条件に書く 3 field を持たないのに、
  `SCHEMA_VERSION` は双方とも同じである。schema_version を上げずに field を足している。
  本 wave の fixture は現行 producer から導出した。恒久対応は別タスクへ切った。
- **セッション異常 2 件。** (1) 待ち手を producer 起動直後に張ると、
  出力ゼロの `rc=0` を約 1 分で返す false completion が 1 度起きた (再現性 2 回中 1 回)。
  3 点照合 (成果物実在 + `.done` + producer 死) を守っていたため誤進行は防げた。
  (2) login node が並行 wave の輻輳で `bounded scope の memory.max / memory.oom.group を
  走行中に attest できない` を返し続け、**同一手順で直前に緑だった対象も同じ症状で落ちた**。
  環境障害と判定し、他 wave と同じく計算ノードへ回して実走した。
- **変異本走は 8 件すべて KILLED し、期待 node 完全集合と一致した** (baseline PASSED、harness rc=0)。
  ただし**第 1 走は probe である** — V3〜V6 の 4 件が MISMATCH になった。
  変異自体は 8 件とも検出されており検出力の不足ではなく、親の期待 node 集合が過小だった
  (V3 は登録 2 件に対し実測 17 件)。原因は「新設 gate が発火すると後段の検査が走らず
  診断がまとめて置き換わる」型で、親は新設検査を直接撃つ 2 件しか数えていなかった。
  実測 node を完全集合として再登録して第 2 走を行い、
  さらに local main 取り込み後の**最終 commit で第 3 走を権威走行とした** (`DW-M07`)。
  取り込みで `autonomous_trial_completeness.py` を含む実装面 5 file が結合され
  焦点テストが 813 → 816 件へ増えたが、**8 anchor はすべて一意のままで期待 node 集合も変化せず、
  8/8 KILLED と baseline PASSED を再現した。**
  逐語と erratum = `output/insights/2026-08-16_t1109-admission-grammar/`。
- **親が `DW-O17` を踏み忘れて provenance を赤にし、既知違反登録を使わずに手順どおり直した。**
  main 側の別 wave が本 wave と同じ実装面 5 file を触っていたため、親が自分で作った
  main 取り込み merge が `check_ai_provenance` の **rc=1 (実装面に Codex role=author がない)**
  に掛かった。`DW-O17` は「実装面 path が両親と異なれば Codex `role=author` へ」と
  既に定めており、**踏み忘れたのは親である。**
  `git diff-tree --cc` は空 (合成差分ゼロ = 両側の変更の和集合) だったが、
  checker は「全 parent と異なる path」を file 単位で数えるため成立する。
  **既知違反 registry への登録は採らなかった** — 同 registry の項目はすべて
  ユーザー裁定の参照を要求しており、親の自己登録は防壁の自己迂回になる。
  また checker 自体の是正 (`--cc` を使う精密化) も、land が **tip 側 checker** で
  監査する構造上は自分の赤を消せる立場にあったが、
  **自分に都合よく防壁の受理条件を変える行為なので採らなかった。**
  採った手順: merge 手前へ巻き戻し → 親が結合を用意 → **Codex author が結合後の
  実装面 5 file を監査して所有** (`COMPOSITION-SOUND`、是正ゼロ) → 著者行を確定。
  結果 `check_ai_provenance` は **rc=0 / 3,500 件・新規違反なし**。
  **先行 5 例が registry 登録で処理してきた型だが、`DW-O17` の手順で正面から通せることを実証した。**
  副次的に判明した制約: Codex 子は Git 管理領域へ書けず `git merge` を実行できない
  (`ORIG_HEAD.lock` が read-only)。また取り込みが `docs/dev-wave/` を持ち込むと
  未 commit 差分で子のランチャーが起動を拒む。したがって
  **親が merge を commit してから子が監査する順序でしか成立しない。**
- **工数:** codex 子 8 本 (plan 1 / consult 2 / author 4 / review 2 / fix 1)。
  実装子の wall-clock は 350 / 568 / 423 秒。

## 次の一手差分

### 完了

- [T-1109] 受理文法を `(?:0:)?<request-id>` へ拡げ、qsub authority は不変に保った。
  新たに拒否される値は 0 件で、既存負例 15 件はすべて拒否のまま。
  設計判断は {{D:pbs-jobid-env-grammar}}。
  remaining: none
  base: 4cf8d339b3d1a61512099c4d80797b15facff23bfdf382330000b661529a9521

- [T-1110] `transport-admission-error` を受理 event と terminal event の両方へ足し、
  admission 失敗経路が verified partial `report.json` を実際に永続化できるようにした。
  `_EVENTS` への追加だけでは足りず、error 専用 gate・`first_run_event`・terminal 配置・
  zero-cell coverage・campaign root 要求の限定免除の 5 面が必要だった
  ({{F:completeness-gate-blocks-its-own-report}})。
  remaining: none
  base: a02559b4c446e55df0bb065b80b90cf46b9181fc298c34fdf943b34a38007ebd

### 更新

- [T-1111] **P2・部分実施**: 「起動を止める型の fail-closed admission 述語は、実在の
  production 値を自分の述語へ通す positive control を持つ」を族として義務づけ、
  {{D:fail-closed-admission-positive-control}} に境界定義と 8 member の inventory
  (停止点 / 実在値の正本 / positive nodeid / 充足状態) を固定した。
  **member 8 件中 6 件に control を置いた。** 残る 2 件は
  member 2 (runtime attestation、D143 のユーザー裁定待ちで真正面に書けば現在は赤) と
  member 8 (provider live env / receipt 一致、実在値を未取得) で、
  **skip・xfail・期待反転で緑に見せず `unmet` のまま残した。**
  member を機械列挙する registry gate は、この 2 件が unmet のまま作ると
  偽の完備性を与えるため新設しない。残余は {{T:admission-control-unmet-members}} へ。
  base: 305ef9e3156a10750fc7dbe0dc994ca35b7f01923d0a53a576310b09e7224309

- [T-1112] **P1・ユーザー裁定待ち**: 8c A/B/C live pilot の再投入。
  本 wave で [T-1109]/[T-1110]/[T-1111] が閉じ、**起票の前提を 1 つ満たした** —
  実機 job ID が transport admission を通り、admission 失敗時も診断 report が残る。
  **ただし段 3 の敵対 2 レンズが独立に、残る閂を 2 件測定した。**
  (a) F97 の runtime attestation (D143 未裁定) は build 前で止めるため、
  文法が直っても build・measurement・certified 選択は生成されない。
  (b) 計算ノード実機での D122 (2)(i)(iii)〜(viii) は**未測定**である
  (proxy 2 key の実在と policy exact 一致、TLS override 不在、従量 env 不在、policy path の健全性)。
  本 wave は login node のみで走っており、実機測定は行っていない。
  **起票してよいか、(a)(b) を [T-1112] 自身の第 1 段として測るかはユーザー裁定へ返す。**
  base: a6fe161424df38a7f27497b72bebfe289b30dfe6dbbf1063e5fecd2df1f3da6d

### 新規

- {{T:admission-control-unmet-members}} **P2・新規**: {{D:fail-closed-admission-positive-control}}
  の unmet member 2 件を閉じる。member 2 は D143 の裁定が前提。member 8 は
  provider live env / receipt 一致の実在 production 値を取得する必要がある。
  両方が閉じたら member registry の機械 gate 化を再提案してよい
  (D96 は AST 案 1 件を却下しただけで、独立 2 例と再裁定での再提案を許している)。

- {{T:reservation-not-wired-to-8c-launch}} **P1・新規**: 8c の事前登録証拠契約は
  `run_trial -> reservation.single_process_required -> campaign launch` を要求するが、
  `check_reservation` の実 call site は t126 driver と 8b の 2 driver だけで、
  8c launch path への到達が確認できない。**契約と実装の乖離**であり、
  reservation control が緑でも 8c の allocation provenance は保護されていない。
  配線するか契約から明示的に外すかを決める。

- {{T:waiter-attach-race-guard-blocked-by-budget}} **P3・新規・ユーザー裁定待ち**:
  段 8 の自己改善候補が **docs 予算に阻まれて実装できなかった**。
  候補は `DW-O01` へ「親は投入直後に pid file の実在と非空を確認してから待ち手を張る」の
  1 文を足すもので、本 wave が実測した false completion
  (producer 生存・`.done` 不在・成果物不在で待ち手が即時 rc=0) への手順側の防壁だった。
  **ただしこの候補文言は本 wave 中に反証された。** 2 回目の発生では
  `--pid-file` ではなく**実在する生存 pid を `--pid` で直接渡していた**ため、
  「pid file 未書込の窓を掴む」という当初の仮説は成立しない。
  発生は producer 投入 4 件中 2 件で、いずれも待ち手の出力は空だった。
  `wait_for_producer` の fail-closed 分岐 (`producer-liveness` / `producer-timeout` /
  `producer-files`) はいずれも非 0 と診断行を返す構造であり、
  **観測 (rc=0・出力ゼロ) は待ち手プログラムのどの経路とも一致しない。**
  したがって疑わしいのは待ち手ではなく背景 task の完了通知側である。
  追記すると `check_docs` が `docs/dev-wave/**: L1.5 unique footprint 9710 bytes > 予算 9566 bytes`
  で赤になる。**予算値を上げる変更は通常の自己改善に含めない契約**なので変更を止めた。
  択 (a) L1.5 の別節を意味等価に縮約して枠を作る (dev-wave docs の圧縮は exact pin を壊すため
  高リスク)、択 (b) 予算値の引き上げを独立審査する、
  択 (c) 発生源を特定してから機械的防壁を足す、択 (d) 見送る。
  **親の推奨は択 (d) 見送り。** 反証の結果、足そうとした 1 文は誤った仮説に基づいており
  有効な防壁にならない。さらに wave 末で決定的な観測が出た — 同一の待ち手について
  **先に「完了・rc=0」の通知が届き、その後で本当の結果 `rc=70` が届いた**。
  つまり発生源は待ち手プログラムではなく**背景 task の完了通知が先行・誤配される**ことであり、
  これは `DW-O01` が既に「完了は `.done` と exit code だけで判定し、grep も通知も判定にしない
  (通知は先行しうる)」と規定済みの事象である。
  **新しい防壁ではなく既存規律の遵守で足りており、実際 3 点照合が 2 回とも誤進行を防いだ。**
  L1.5 予算を消費してまで追記する価値はない。

- {{T:acceptance-scheduler-attestation-flake}} **P2・新規**: 受入全走で
  `orchestrator/tests/test_dev_wave_wait.py::test_public_main_real_signal_releases_lease` が
  1 度だけ赤になった (11,182 passed / 1 failed / 65 skipped)。
  失敗はシグナル処理に到達する前で、テストが内部起動した受入サブプロセスが
  `stage=acceptance-scheduler-attestation rc=70 detail={"observed":[],"reason":"marker-count"}`
  で落ちている (期待 rc=143 に対し実測 70)。
  **同 nodeid の単独再走は緑** (`1 passed in 2.58s`、`--force-dispatch`)。
  本 wave の差分は `dev_wave_wait.py` とその test に 1 行も触れていないため
  `DW-O18` に従い非帰属とした。並列 11k 件走行下でのみ marker が観測されない条件があると疑われる。
  既知赤 registry ([T-1116] 系) の対象にするか、attestation 側で並列走行時の
  marker 観測を確実にするかを決める。

- {{T:trial-journal-schema-version-not-bumped}} **P2・新規**: 自律試行 journal の
  `run-start` に field を足したとき `SCHEMA_VERSION` を上げていない。
  記録済み artifact と現行 producer が同一 schema_version で別 shape になっており、
  記録を fixture に使うと stale な形を固定する。version 規約を決めて追随させる。
