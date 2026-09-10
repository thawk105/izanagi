結論は **NO-GO** です。must-fix は **8件**。静的読解のみで判定し、pytest・checker・launcher・Codex 子の実走はしていません。ファイル変更もありません。

## 最重要所見: A+ は現状では gate にならない

現行の起動契約は `docs/dev-wave/operations.md:8-13` の文書上の指示です。`hooks/guard_bash.py:39-45` は Codex subprocess を管轄せず、Codex の production caller も実測上ありません（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-brief.md:24-30`）。

したがって、A+ の採用条件である「raw `codex exec` を契約違反にする」は、契約文を追加するだけなら docs pin と同じ強度です。プラン自身も raw bypass を 100%取りこぼすと認めています（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s2-plan.md:132-137`）。

raw 起動を実際に赤くするには、少なくとも「期待された全 job に launcher receipt が存在すること」を段7で集合照合し、欠落を停止する必要があります。未知の job を完全に捕捉するには、さらに launcher-only の実行面か、外部の実行監視が必要です。

## 案ごとの実効性

| 案 | 実際に赤くなる条件 | 赤くならない経路 | 段6 fix の起動保証 |
|---|---|---|---|
| A | launcher 経由で `turn_context` の model/effort 欠落・不一致、receipt/manifest 不整合が出た時 | raw 起動、親が誤った `launch_kind` を選んだ時 | launcher が観測した直後に赤くできる。ただし raw または誤った lane 宣言なら誰も知らない |
| B | 段7で、全 sessions root・全 child worktree・base commit 時点の権威を完全に選べ、strict 照合した時 | 未列挙 root、別 worktree、prompt 分類不能、checker の実行忘れ | 子終了後の段7/9で初めて分かる。現状の stage 分類は33件中30件が `unclassified` |
| C | 宣言、launch-id、`.done`、rollout、docs 再導出値の exact join が崩れた時 | 親が誤った lane を宣言、宣言値を自由入力、全 anchor を省いた raw 起動 | 宣言漏れは事前に赤くできるが、実効 effort 不一致は子終了後。誤った宣言キーなら通る |

案Bを段9だけに置く場合、救われるのは基本的に `DW-O23` による local main land と canonical 台帳の fold だけです。子の実行資源、生成物、wave branch の commit、後続レビューへの利用は既に発生しています（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s2-plan.md:224-230`）。

## 運用摩擦

親が確定・保持する追加項目を数えると、概算は次のとおりです。

- A: 子ごとに `launch_kind`、child cwd/repo、prompt/output、manifest/receipt、sessions root/host、`.done` wrapper の6項目。5〜13本で30〜78項目、さらにwave共通の期待job集合とauthority digestが必要。忘れた引数は fail-closed にできるが、launcherを使わない忘却は現状黙って通る。
- B: waveごとに root/host、時間窓、child cwdまたはartifact anchor、stage/lane対応、strict checker実行、監査成果物保存の6手順。checker実行を忘れると、文書契約だけでは黙って素通りする。
- C: 子ごとに declaration、docs由来値、launch-id、cwd/root/output、`.done`、rollout保存、照合対象登録の7項目。5〜13本で35〜91項目。宣言と `.done` の双方向集合を実装すれば欠落は赤くできるが、全 anchor を省いた raw 起動は見えない。

## worktree、並行wave、命名コスト

現行契約は worktree を分けることしか要求していません（`docs/dev-wave/workers.md:19-24`, `docs/dev-wave/workers.md:52-63`）。実測では13 session中6本、段6 fixを含む別worktreeでした（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-measurements.md:45-54`）。

命名規約を追加する場合、最小限の例でも次のbyteを要します。

- `worktree は \`<wave-slug>-implN\` とする。` = 46 bytes
- `worktree は \`<wave-slug>-fixN\` とする。` = 45 bytes
- 合計 = **91 bytes**

裸のASCII tokenだけでも合計53 bytesです。aggregate残16 bytesには入らず、命名規約だけで予算超過します（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-brief.md:42-43`, `tools/check_docs.py:168-180`, `tools/check_docs.py:254`, `tools/check_docs.py:3688-3708`）。また命名だけでは衝突・再利用・別wave混入を防げません。

具体的な相互汚染例は、T-181 checkerが `--cwd-contains t181` と時間窓で走査するケースです。別wave `dev-wave-t181-reasoning-ab` の別checkoutまで一致し、33 session中20本が別waveでした（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-measurements.md:124-130`）。時間窓だけなら70 session中13本しか対象waveでなく、5.4倍の過剰包含です（同:56-71）。

- Aは、wave-localの期待job集合とsession IDをexact照合する限り耐える。ただしraw bypassには弱い。
- Cは、wave固有の一意なlaunch-idとmanifestを使う限り耐える。
- Bは現行selectorでは耐えない。誤選択を赤くするだけなら fail-closed だが、選択漏れを緑にしない保証がない。

## `~/.codex/sessions` 依存

現行の既定rootは `CODEX_HOME/sessions`、未設定時は `~/.codex/sessions` です（`tools/codex_worker_launch.py:2575-2581`）。このrootはhost-localです。dev-wave Codexを別hostや計算ノードで起動すれば、そのhostのrootにrolloutが出て、login hostのcheckerからは自動では見えません。role runtimeはさらに `/home/role/.codex` を設定します（`orchestrator/codex_roles/launcher.py:592-600`）。

形式変更への耐久性も未定義です。

- `tools/codex_worker_ledger.py:401-457` は既知の `session_meta` と `turn_context` だけを読む。
- ledger側には `turn_contexts == 0` を明示的に異常とする処理がありません（`tools/codex_worker_ledger.py:1082-1090`）。
- launcher側には `context_count < 1` を無効化する検査があります（`tools/codex_worker_launch.py:890-907`）が、B/Cがこれを必ず共有する設計にはなっていません。
- CLI version/schemaのallowlist、未知event、必須field欠落時の形式不一致としての停止が必要です。

容量・保持も弱いです。runbookには ledger 対象が調査時点で約887MB・941 rollout、launcherはprompt/rollout bytes上限なしとあります（`docs/pegasus-runbook.md:549-561`）。receiptはrollout pathとhashを持つだけで、rollout本体をwave artifactへ保存しません。rotation後は、赤くはできても過去waveを検証できません。

## 実測F〜Jとの整合

- F: 実効値収集層が既存という指摘は正しい。ただしプランはなお新規600〜1,600 LOC級の層を想定しており、「既存部品の結線」というbrief追記（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-brief.md:87-99`）と不整合です。
- G: プランは現行prompt-prefix分類を再利用すると書いています（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s2-plan.md:164-170`）。これは実測30/33 `unclassified` と直接矛盾します。分類不能を赤くすれば通常運用が止まり、無視すれば検出力ゼロです。
- H: Bのcwd/time/prompt selectorは、別wave・別checkoutを跨ぐ既知の問題を解消していません。
- I: B/Cは事後検査なので、F56の恒久対応「起動前に落とす」を満たしません（`../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-measurements.md:132-145`）。Aも、CLI値をdocsから導出するだけでなく、model×effortの対応表を起動前に検査する必要があります。
- J: `launch_kind → docs節 → 値` の対応表自体がstage matrixです。`docs/phase3.md:694` がstage matrixを[T-184]所有と明記しているため、このwaveで独自定義してはいけません。

## [T-662] と [T-665] の束ね方

同じrolloutのtop-level `turn_context`で観測できる点は共通ですが、同じ機構・同じ権威ではありません。

- modelはDW-O01の権威行。
- effortはworker節に分散。
- CLIでもmodelは `-m`、effortは `-c model_reasoning_effort=...` です（`tools/codex_worker_launch.py:1098-1107`）。
- F56はmodelごとにeffort受理集合が違うことを実測しています（`docs/failures.md:1311-1322`）。

したがって必要なのは、共通の観測器に加えた「同一jobのmodel×effort pair検査」です。段3で両方とも `max` だからといって、model laneの取り違えは検出できません。`sol/max` と `luna/max` のlaneを入れ替えても、単なる多重集合は一致します。

## 親Pとプラン判定の再判定

- P1: **排他的な3択とする点は誤り。** Aは通常、即時launcher検査に加えてB型のwave集合再照合を必要とし、CはBに宣言層を足したものです。独立した3方式というより層の組合せです（brief: `../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s1-brief.md:68-81`）。
- P2: **親の主張が概ね正しい。プランの「一部誤り」は誤り。** Aのhash・session IDは誤帰属を減らしますが、同一accountがdocs、launcher、receipt、rolloutを書き換えられるというtrust root自体は変わりません。証拠の結合強度とtrust rootを混同しています（プラン: `../../../../dev-wave-jobs/dev-wave-t665-t662-launch-binding/s2-plan.md:328`）。
- P3: **プランの訂正が正しい。** 別worktreeは実際の最大穴であり、単に起動口を一つにしてもraw起動と現行単一repo manifestが残ります（`tools/codex_worker_launch.py:1480-1484`, `tools/codex_worker_launch.py:1565-1581`）。
- P4: **正しい。** 現状の16 bytesではどの案も契約追加を収容できません。
- P5: **誤り。** 同じrollout fieldを読むことと、同一policyで閉じることは別です。model×effort、lane identity、起動前対応表が必要です。
- P6: **必要条件だが不十分。** 多重集合は集計不変条件として必要ですが、lane/job identityを失うため、それだけでは不可です。プランがP6全体を「結論が誤り」としたのは過剰です。正しい形は「lane keyed mapping + cardinality/multiset projection」です。

## 現状維持の害

実害の実績はあります。`grep -n "effort\|reasoning\|model" docs/failures.md` のF56該当出力は次のとおりです。

```text
1304:### F56. worker 起動の model / reasoning は要求値がそのまま receipt になり、不正値と未サポート model が silent に通る
1306:実測した。(a) -c model_reasoning_effort="ultra" (存在しない値)
1307:rc=0 のまま成功し、rollout の turn_context には reasoning=ultra が記録される。
1310:receipt の model は要求 slug のまま、model_calls=0 / cli_reported=0 になる。
1311:(c) model により reasoning の受理集合が異なる
1313:- 根本原因: DW-O01 は model_reasoning_effort="<効いた値>" と書いて起動者の注意に委ねており、
1318:- 恒久対応: model×reasoning の比較や policy 採用を行う台帳は、要求値と記録値を別名で持つ。
1321:(c) 未知の reasoning 値と model×reasoning の非対応組は起動前に落とす。
```

従って「実装しない」は、既に実測された不正effortのrc=0通過を残します。

## must-fix

1. raw `codex exec` の置換漏れを、契約文ではなく期待job集合・receipt欠落・実行面で機械的に赤くする。
2. `launch_kind` と段3 laneを親の自由入力にせず、exact job/output/prompt identityへ束縛する。prompt regex、手入力stage-map、多重集合だけを使わない。
3. 段5/6のchild cwd、repo root、base commit、host、sessions rootをjob単位で束縛し、並行waveの一意なwave IDと照合する。
4. [T-184]所有のmodel×effort stage matrixを起動前に参照し、非対応pairを起動前に拒否する。rollout fieldは `requested_*` / `recorded_*` と明示し、`model_calls=0`を成功観測扱いしない。
5. B/Cの照合を段9だけに置かず、段7の記録・commit前にfail-closedで実行する。
6. CLI/schema version、必須event/field、未知形式、root不明、host不明を赤くし、rollout本体をdurable artifactとして保存する。
7. authorityはwave開始時のbase commit/snapshotで固定し、[T-184]との所有境界を裁定する。live HEADを過去waveの権威に使わない。
8. [T-664]でdocs予算を先に解決し、D60の「現用Codex相談はlauncherを経由しない」という既存決定（`docs/decisions.md:2323-2328`）との移行境界を明示する。T-667のdocs pin対象拡大は再提案しない。

## 追加裁定案

- **R9 — 実行面の閉包:**  
  (a) 期待job集合とreceipt集合のexact equalityを段7で要求する（推奨）、(b) raw起動を許可するが検出保証なし、(c) declaration helperがexecまで担う。契約文だけのraw禁止は択一から除外。
- **R10 — rolloutの耐久性:**  
  (a) 起動hostでrollout・CLI version・sessions rootをwave artifactへ保存（推奨）、(b) `~/.codex/sessions`保持に依存、(c)過去wave検証を要求しない。
- **R11 — stage matrix所有:**  
  (a) [T-184]がcanonical matrixを発行し本waveはgeneric binderだけを持つ（推奨）、(b)本waveがmatrixを新規所有、(c)stage照合をしない。 (b)(c)は不採用。
- **R12 — 起動前pair検査:**  
  (a) model×effort対応表を起動前に検査し、起動後はrecorded値を再照合（推奨）、(b)事後検査だけ、(c)served-model attestまでscope拡大。 (c)はF56/T-189の所有を侵すため不採用。

R2、R3、R4、R8のうち、既に不採用となる選択肢は裁定から削り、実行可能な択一だけを残すべきです。

## 総括

判定は **NO-GO**、must-fix は **8件**です。実走はしていません。

- Aが赤くなる条件: launcher経由で必須`turn_context`・receipt・manifestが不一致になった時だけ。raw起動と誤ったlane指定は赤くならない。
- Bが赤くなる条件: 全root・全child worktree・base authorityを完全選択し、strict照合した時だけ。現行selectorでは取りこぼし上限がない。
- Cが赤くなる条件: declaration再導出値とlaunch-id/rollout/`.done`のexact joinが崩れた時だけ。親が誤ったlaunch kindを宣言すれば通る。

親briefで誤りまたは不十分と判断したのは、P1の排他的3択化、P3の「Aなら構造的に閉じる」という部分、P5の「同一機構で閉じる」、P6の多重集合だけで足りるという不十分性です。P2は親のself-attest判定が正しく、プラン側の訂正が誤りです。

追加すべき択一はR9〜R12です。