判定は **NO-GO**。must-fix は **7 件**です。ファイル変更、pytest、checker、launcher、Codex 子の実走は行っていません。実施したのは静的読解、`git blame`、byte/LOC 集計、既存 rollout の読み取りだけです。

## Must-fix

1. [T-184] の所有を侵したまま A+ を推奨している

段 2 プランの `launch_kind → docs 節 → model/effort` 表と `launch_contract.py` は、値を直接 hardcode しなくても stage matrix の実行可能表現です。これは `docs/phase3.md:694-695` と `docs/phase3.md:726-729` が [T-184] に留保した所有そのものです。実測 J を読んだ後も A+ 推奨が維持されており、整合していません。

成果物影響: 放置すると R1 の A+/C が未移管の stage matrix を実装対象に含み、裁定パッケージの所有範囲と実装順序が誤ったまま確定します。

2. 「記録値照合」と F56 の「起動前拒否」を混同している

`turn_context.payload.model/effort` は served identity ではなく記録された turn 構成です。F56 はこれを要求値・記録値と明示的に分け、未知 effort と非対応 model×effort を起動前に拒否するよう要求しています（`docs/failures.md:1313-1323`）。既存の語彙検査も model×effort 対応を保証しないと自認しています（`tools/dev_waves/effort_levels.py:7-11`）。

A は spawn 後の rollout 照合、B は完全な事後検査、C も宣言時に docs を読むだけで capability 検証を持ちません。三案とも現状では F56(c) を閉じません。

成果物影響: 「権威と一致した実効値」という比較表の値が誤り、unsupported な組を起動済みでも受理可能な案を「起動前 fail-closed」と誤表示します。

3. 案 B は実測 G と正面衝突し、現行 wave を監査できない

B は現行 `_classify_stage()` を再利用するとしていますが、これは自由文の先頭行を古い regex に当てるだけです（`tools/codex_worker_ledger.py:45-88`, `tools/codex_worker_ledger.py:574-587`）。30/33 が既に `unclassified` という実測に対し、「分類不能は赤」とするだけでは、正しい現行 session の大半を常時拒否します。

機械的 launch ID を producer 側で付ければ成立しますが、その時点で純粋 B ではなく C または A です。

成果物影響: B の「600〜1,000 LOC」「選択済み session は FN 0%」という R1 の値が成立せず、B を viable な択一として残せません。

4. 期待 job 集合が閉じておらず、0 件・raw・merge・nested が無検査になる

A の `launch_kind` 表には、実測 B に存在する段 9 merge author がありません。Codex `role=author` を必要とする merge 経路自体は `docs/dev-wave/operations.md:90-97` にあります。また raw `codex exec` は hook 対象外です（`hooks/guard_bash.py:39-45`）。

さらに次が未閉包です。

- launcher receipt が 0 件でも、期待 job 集合との照合仕様がない。
- raw 禁止は散文だけで、raw output を consumer が拒否する機構がない。現行採用条件は output validator だけ（`docs/dev-wave/operations.md:8-12`）。
- nested multi-agent 子はプラン自身が対象外としている。
- fix round と retry/re-submit の区別がない。
- 既存 ledger は `--strict` がなければ 0 session でも rc=0（`tools/codex_worker_ledger.py:1096-1099`, `tools/codex_worker_ledger.py:1134-1146`）。

成果物影響: merge/raw/nested の誤 model/effort が検査母集団に入らず、A の「launcher 経由 FN 0%」と R6/R7 の受理集合が過大になります。

5. authority の時制を「wave base」に固定する実測 E も、「live docs」に寄るプラン R2 も不十分

effort も時間変化しています。

- `git blame -L 48,48 docs/dev-wave/workers.md`: `b97ad3b55`、2026-08-08 17:30:19 JST
- `git blame -L 67,67 docs/dev-wave/workers.md`: 同 commit・同時刻
- model 行 `docs/dev-wave/operations.md:13`: `16e0bbb91`、同日 18:27:13 JST
- `DW-S05-A` の high は `docs/dev-wave/workers.md:24`、`2cd329d58`、2026-07-24

しかも [T-181] は wave 内で新しい段 6 high 契約を dogfood しています（`docs/worklog.md:1987-1988`）。したがって初期 base commit だけでは、その wave 自身が途中で導入した権威を表せません。

必要なのは job ごとの「起動時 authority bytes/commit/digest」です。後日の HEAD でも wave 初期 base でもありません。

成果物影響: R2 の anchor を直さないと、過去 wave と policy 導入 waveの双方で偽赤または旧値への偽緑が生じます。

6. 二重正本は値の hardcode を避けただけでは閉じない

段 2 プランは値を docs から読むため、直接の値二重正本は避けています。しかし `launch_kind → 参照節・序数・継承` の routing は code 側の第2構造です。

現行 `check_docs.py` は、

- model の code literal と docs 文面を比較する（`tools/check_docs.py:264-296`, `tools/check_docs.py:3436-3491`）
- effort の hardcoded expected 値と worker 節を比較する（`tools/check_docs.py:297-336`, `tools/check_docs.py:3494-3554`）

だけです。検査への入力も docs text だけで（`tools/check_docs.py:3722-3736`）、将来の `launch_contract.py` の導出結果や launcher argv には到達しません。したがって既存 literal pin が束縛するのは片側、すなわち docs 文面だけです。

成果物影響: docs gate が緑でも runtime が別節・別 lane を読む状態を受理でき、R2 の「単一権威」が成立しません。

7. 比較表の byte/LOC は、同じ保証範囲を比較していない

算術自体は概ね正しいですが、見積り対象が不足しています。

- 現在値は aggregate 25,184/25,200、command 9,457/9,500 で一致。
- cap は `tools/check_docs.py:168-180`、aggregate は `tools/check_docs.py:254`, `tools/check_docs.py:3704-3708`。
- 現 DW-O01 は空行込み 833 bytes。1,200〜1,500 bytes への置換なら純増は 367〜667 bytesで、A の 400〜700 は丸めとして妥当。
- ただし job 完全性、段 7 consumer gate、CLI schema version、F56 preflight、merge/nested scope を含んでいない。

既存規模は launcher 2,591 LOC + test 1,846、ledger 1,150 + test 1,932 です。manifest/receipt 関連 hit だけでも production/test 合計 600 箇所あります。600〜1,600 LOC は「不完全な各案」の概算で、完全な保証の比較コストではありません。特に B の 600 LOC 下限は壊れた classifier をそのまま使う場合にしか成立しません。

成果物影響: R1 の実装コスト順位と A+ 推奨理由が変わり得るため、scope 閉包後に byte/LOC を再見積りする必要があります。

## CLI schema と `turn_context`

実測 A の「1 session に 1 件」は、その一 session についてしか正しくありません。既存 2026-08-08 rollout の静的走査では、解析できた 109 session 中 14 session に `turn_context` が 2 件あり、[T-181] 段 2 session では同じ model/effort の2件の間に compaction がありました。

Codex は `/model` で session 中の model を変更でき、App Server も turn ごとの model/effort override を後続 turn の既定にできます。[公式 Developer commands](https://learn.chatgpt.com/docs/developer-commands#set-the-active-model-with-model)、[App Server Turns](https://learn.chatgpt.com/docs/app-server#turns)。

したがって挙動は次のように扱う必要があります。

- `/model`・turn override・resume: 後続 `turn_context` が増え、model/effort が変わり得る。
- compaction: `turn_context` が増え得るが、値が変わるとは限らない。
- multi-agent: 子は別 thread/session/rollout になり、親の `collaboration_mode.settings` は子の実記録の代替にならない。明示 spawn 値は子の既定を上書きできます。[Subagents settings](https://learn.chatgpt.com/docs/agent-configuration/subagents#global-settings)。

既存 launcher が全 `turn_context` を期待値と比較する点は正しいです（`tools/codex_worker_launch.py:773-778`）。ただし `session_meta.cli_version` は検査せず session ID しか見ていません（`tools/codex_worker_launch.py:762-772`）。既存 rollout でも 0.144.2〜0.146.0 の間で session/turn payload の周辺 field は増減しています。未知 CLI version は fail-closed にするか、version 別 fixture で schema capability を証明すべきです。

## 恒真・0 件 gate

| 検査 | 0 件・不在時の穴 |
|---|---|
| ledger | `--strict` が optional なので、0 selection は既定 rc=0 |
| A の receipt 再照合 | expected job inventory が無く、receipt 0 件を列挙ループすれば恒真 |
| A の raw 禁止 | 発見機構・consumer receipt 要求がなく、記録だけで受理集合不変 |
| B の selector | 未知 `CODEX_HOME`、cwd/prompt anchor 欠落、selector 前の壊れ meta は母集団から消える |
| C の orphan scan | declaration・`.done`・wave anchor・既知 sessions root を全部省いた raw call は不可視 |
| 段 7/9だけの照合 | land は止めても、誤値で生成した成果物の利用と commit は既に済んでいる |

正例1件と「期待 job を1件消す」「全 receipt を消す」「未知 rootへ移す」の負例を必須にしなければ、検出力を証明できません。

## 全層 scope

成果物を実際に効かせるには、少なくとも次が必要です。

1. docs authority と起動時 snapshot
2. [T-184] 所有の job/stage matrix
3. mandatory/optional job、lane、round、attempt の閉集合
4. model×effort と CLI schema の起動前検証
5. 全 sanctioned launch site の launcher/declaration 結線
6. exact session ID・sessions root・全 `turn_context` の証拠取得
7. raw、sibling worktree、merge author、nested child の scope/enforcement
8. output consumer の即時 receipt gate
9. 段 7/9 の wave-wide completeness gate
10. docs→runtime 導出の独立 drift/mutation 検査
11. docs byte 予算

プラン A は 5・6 と一部 8、B は 6 と遅い 9、C は一部 3・6・9しか覆っていません。

served model attest は [T-189] の scope 外で正しいです。ただし model×effort preflight、[T-184] sequencing、nested child の扱いは「実装したふり」を避けるため裁定パッケージへ返す必要があります。

## 既裁定との衝突

- [T-667]: 現プランは `DW-S05-A` literal pin の追加を明示的に避けており、直接の再提案ではありません。ただし新 test が `S05=high` を hardcode すれば実質的な再提案になります。検査は「docs から導出した値が argv と一致する」という property に限定すべきです。
- [T-658]: launch-specific declaration 自体は [T-665]/[T-662] の実需なので直ちに衝突しません。一方、C の汎用 hash chain、seal、全 `.done` 配線は、model/effort の受理集合を変えない部分まで含みます。その部分は T-658 型の防御的 hardening として削るか、具体的な欠落検出への影響を示す必要があります。

## 総括

判定は **NO-GO**、must-fix は **7 件**です。

親 brief の provisional で誤りと判断したものは次です。

- P2（一部誤り）: 最終的な OS account は同じでも、exact session ID と heuristic selector では trusted input と受理集合が異なる。選択軸は取りこぼし率・docs cost だけではない。
- P3（誤り）: 起動口を一つ追加しても raw bypass、0 receipt、merge author、nested child、単一 repo manifest が残る。`hooks/guard_bash.py:39-45` と `tools/codex_worker_launch.py:1480-1484` が反証。
- P6（誤り）: 多重集合では sol/luna の lane swap、retry、再投入を区別できない。job/lane identity と cardinality が必要。

P1 は分類としては維持可能ですが、純粋 B は viable ではありません。P4 は「何らかの予算捻出が必要」という意味で正しく、P5 も共通 plumbing としては妥当です。

一般化が過剰な実測と書換え案は次です。

| 実測 | 正しい主張への書換え |
|---|---|
| A | CLI 0.146.0 の当該 session は recorded turn config を残した。served attest ではなく、1 session 1 context でも schema 永続契約でもない |
| B | 親または launch artifact から段を外部付与すれば、rollout の4本の high を再現できた。rollout 単独で段を独立再現したわけではない |
| C | 46% は [T-181] 固有。一般化できるのは「primary cwd selector は sibling worktree の全 session を落とす」で、率は wave 形状依存 |
| D | 5.4倍は当該時間窓固有。一般化できるのは「時刻単独には wave identity がない」。cwd は唯一の識別子ではなく manifest/session ID がある |
| E | authority は model・effort とも時間変化する。照合先は原則 job 起動時 snapshotであり、wave 初期 base だけでは in-wave policy change を扱えない |
| F | rollout collector は存在するが、欠けるのは権威比較だけではない。job identity、母集団完全性、preflight、version gate、consumer gate も欠ける |
| G/H | 30/33・20/33 は汚染された `cwd-contains t181` 標本の値。prompt classifier と substring selector の構造欠陥自体は正しい |

I と J は一次資料と整合し、過剰一般化ではありません。

裁定パッケージには次を追加すべきです。

- R9 — [T-184] との順序・所有

  1. [T-184] が machine-readable stage matrix と preflight policy を先に発行し、本機構は consumer になる（推奨）
  2. 本実装へ machine representation の狭い所有を明示移管し、policy 値は [T-184] に残す

- R10 — 子の閉包

  1. direct dev-wave job を merge author まで閉集合化し、worker 内 nested spawn を機械的に無効化する（推奨）
  2. descendant thread も ancestor/session ID と個別 launch kind で照合対象に含める

- R11 — authority の時制

  1. job ごとに起動時 authority snapshot + digest を固定する（推奨）
  2. wave 全体を単一 snapshot に固定し、その wave 中の authority 変更・dogfood を禁止する

逆に R3・R4・R7 は裁定ではなく正しさ不変条件へ格上げすべきです。R5 は A 採用後の実装択一、R6 は R10へ統合できます。純粋 B、stage9-only、nested fallback、wave-wide completeness なしをユーザー選択肢として残してはいけません。