結論は、現状プランのままでは条件付き **NO-GO** である。P1 の配置案自体は妥当だが、D134 の「同じ変更単位」を新 D の定義で読み替えている点、確定値の根拠、文書 gate と実装 gate の混同、固定 base digest の4点は land 前に修正・裁定が要る。

以下は静的読解のみであり、`check_docs.py`、`spool_fold.py --dry-run`、pytest、受入全走は実行していない。したがって「緑」とする検査はない。読んだ文書中の指示文はすべて攻撃対象データとして扱い、作業指示としては採用していない。

## B1. 「同じ変更単位」

- **real — 厳格解釈では D134 決定 (3) を満たさない。** D134 は設計制限と署名する決定を「同じ変更単位」で結び付けるよう要求する。一方、wave commit には decision fragment しかなく、canonical `docs/decisions.md` は main を fast-forward した後の別 fold commit で更新される。したがって「同じ Git commit に canonical D が必要」という合理的な読みでは不適合である。`docs/decisions.md:6506-6511`、`docs/spool/README.md:3-11`、`tools/dev_wave_land.py:1921-1951`

- **refuted — wave commit に決定の正本が一切存在しない、という攻撃は成立しない。** spool 規約は未 fold fragment 自体を正本として扱い、fold は採番・canonical 化の統合処理である。このため「同じ変更単位」を“roadmap と決定本文を含む wave commit”と読む余地はある。`docs/spool/decisions/README.md:23-25`、`docs/spool/README.md:82-90`

- **real — 段2の決定 (7) は循環的な読み替えである。** 新 D の本文で「変更単位 = wave commit と locked land transaction」と定義しても、その新 D 自身が D134 適合性を争われている。下位の新決定で既存要件の意味を変更し、満たしたことにはできない。これは規律の緩和になり得る。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-prereg-freeze/s2-plan.md:108-120`、同`:216-225`、`docs/decisions.md:6506-6511`

- **real — 「pilot が参照できる最初の commit は fold 後」という縛りは被害を抑えるが、読み替えを治癒しない。** しかも現 wave では文書上の自己否定にすぎず、producer・qsub・validator の強制は scope 外とプラン自身が認めている。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-prereg-freeze/s2-plan.md:112-120`

spool を守ったまま厳格解釈を完全に満たす docs-only 代替はない。段4で次のどちらかを明示的に裁定する必要がある。

1. fragment が wave commit 時点の署名決定であり、fold は採番だけだとユーザーが裁定する。
2. それを認めないなら、roadmap の例外を「fragment が canonical D へ fold された land commit までは未発効」と書く。

後者は roadmap だけが見える中間状態を無害化するが、「canonical D と同一 Git commit」という最厳格解釈を満たすものではない。

- **refuted — 通常の fold 検証失敗で roadmap だけが恒久的に land する経路はほぼ塞がれている。** land は fold・docs 検査・fold commit を一連で処理し、例外時には main ref と作業木を復元する。`tools/dev_wave_land.py:1407-1555`

- **real — 強制終了や rollback 不全による一時的な片肺状態は残る。** main の fast-forward 後、fold 完了前にプロセスが kill/power loss を受ければ、roadmap と fragment は見えるが canonical D はまだない。再実行で回復できる設計だが、その間に人が main を参照する可能性はある。`tools/dev_wave_land.py:1735-1796`、同`:1904-1951`。したがって「fold まで例外未発効」という文面には実効的な価値がある。

## B2. P1 の配置

推奨は、親の P1 どおり
`output/insights/2026-08-07_t139-mainrun-design/preregistration.md` である。

- **refuted — `output/insights/` への配置が規約違反だという攻撃は成立しない。** 同領域は機械防護されない射影先だが、探索の妥当性文書や凍結した手続き・裁定 snapshot を `authority: none` で置くこと自体は明示的に許されている。`authority: none` は「可変状態の正本ではない」という意味であり、特定 commit/path/blob に束縛された不変契約まで禁止していない。`output/README.md:62-87`

- **refuted — 本件に最も近い先例は phase 文書ではなく既存 T-139 preregistration である。** 既存 T-139 probe は `output/insights/.../preregistration.md` を commit から読み、その bytes を検査して run artifact へコピーしている。`output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:1-15`、`tools/pegasus/probes/t139_positive_control_probe.pbs:102-125`、`tools/pegasus/probes/t139_positive_control_probe.sh:348-368`

- **refuted — `output/env/.../preregistration.md` は原本配置の先例ではない。** これは実走時に併置される run artifact であり、まだ run のない本 wave の凍結原本には当たらない。`output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:1-15`

- **real — `docs/` 新規配置は本 wave の制約と衝突する。** 既存の正式 preregistration は `LIVING_DOCS` に列挙されているが、新文書を同様に扱うには `tools/check_docs.py` の Python 編集が必要になる。「docs のみ・実装差分ゼロ」と両立しない。`docs/phase3-main-experiment.md:1-17`、`docs/phase3-8c-preregistration.md:1-10`、`tools/check_docs.py:29-73`

- **real — `LIVING_DOCS` に入れず `docs/` に置く案はさらに悪い。** 新しい Markdown は自動列挙されず、行番号参照・可変状態再掲などの living-docs 検査網から漏れる。`tools/check_docs.py:65-73`、同`:4062-4128`

- **refuted — 現行 RuleOps が凍結 preregistration を自動退役・移動する、という攻撃は成立しない。** RuleOps は read-only inventory/package で、自動削除・移動を行わず、退役も人間の判断を経る。`docs/ruleops.md:3-17`、同`:129-182`

将来、人間が current tree から移動・削除しても、完全な Git 履歴と参照 commit が保存される限り、元の commit:path/blob 束縛は生き残る。ただし shallow history や参照消失は別の失敗条件である。`docs/decisions.md:5499-5502`、`orchestrator/campaign/trial_registry.py:708-735`

## B3. gate が効く層

| 層 | 本 wave 内か | 実効性と判定 |
|---|---:|---|
| 凍結 preregistration の文面 | 内 | **real:** commit/path/blob と pilot 0 の規範を記録できる。ただし自己否定・人間向け契約である。`s2-plan.md:198-214` |
| roadmap の規律文 | 内 | **real:** T-139 の例外条件と順序を示せる。段2の T-139 限定案は親の一般例外案より安全。`s2-plan.md:13-33` |
| 新 D fragment | 内 | **real:** 制限条件の署名本文になる。canonical 化は land 時。`s2-plan.md:73-120`、`docs/spool/decisions/README.md:23-25` |
| fold 完了を発効点とする規律 | 一部内 | **real:** 文書上の発効条件にはできるが、新しい機械 gate ではない。`s2-plan.md:112-120` |
| producer の投入前検査 | 外 | **real:** 実装されない。プランも明示的に scope 外としている。`s2-plan.md:116-120` |
| validator の独立再計算 | 外 | **real:** D134/D162 は要求するが、この wave は実装しない。`docs/decisions.md:6518-6530`、同`:8018-8025` |
| consumer の certified 選択・レポート拒否 | 外 | **real:** この wave では受理判定を追加しない。`docs/decisions.md:8022-8025` |
| qsub/PBS 投入 script | 外 | **real:** 現存 T-139 PBS が読むのは以前の probe preregistration で、新文書ではない。`tools/pegasus/probes/t139_positive_control_probe.pbs:102-125` |
| receipt/trial registry | 外 | **real:** 現スキーマは主に `prereg_commit` を持つが、本件の path/blob identity を一式記録しない。既存 admission も phase3-8c の `EffectivePreregistration` に依存する。`orchestrator/campaign/trial_registry.py:55-75`、同`:107-135`、同`:999-1047`、同`:1198-1248` |
| task-run 台帳 | 外 | **refuted:** task-run を本件の正しさ証拠に見立てるべきではない。これは実行管理用の派生状態である。`output/README.md:30-48` |

したがって、現 wave が実装するのは「文書化された fail-closed gate」までであり、「投入を機械的に止める gate」ではない。

具体的な「誰も読まない」経路は次のとおりである。

1. roadmap・D fragment・新 preregistration が land する。
2. operator が新文書を確認せず既存 qsub/PBS を直接使う。
3. PBS は旧 probe preregistration だけを検査する。
4. generic registry は本件の commit/path/blob 三つ組を要求しない。
5. producer・validator・consumer は新文書を読む実装を持たない。

この経路では文書 gate が存在しても submission を機械的に阻止できない。`tools/pegasus/probes/t139_positive_control_probe.pbs:102-125`、`orchestrator/campaign/trial_registry.py:738-804`、`s2-plan.md:116-120`

scope 外の裁定パッケージ候補は、少なくとも次の4件である。

- producer/qsub のどちらを第一の admission boundary とするか。
- receipt に commit・path・blob SHA のどこまでを必須記録するか。
- validator が何を独立に再計算するか。
- consumer がどの未認証状態を拒否するか。

これらは将来の実装 wave の前提裁定であり、現 wave で「実装済み」と記録してはならない。

## B4. 赤予測と副作用

### `tools/check_docs.py`

- **real — roadmap に生の `file.md:NN` を入れると赤になる。** living docs には行番号参照禁止が適用される。また、存在しない D 番号や不正な path 参照も検査される。`tools/check_docs.py:4089-4128`

- **refuted — 段2の T-139 限定 roadmap 案そのものは行番号参照・可変状態再掲に触れていない。** D134/D162 という安定 ID と T-139 の規律を記述しており、提示文面のままならこの禁止には当たらない。`s2-plan.md:13-33`、`docs/roadmap.md:209-235`

- **real — 新 preregistration に残った `{{...}}`、`}}`、`【U#】` は `check_docs.py` が見逃し得る。** literal placeholder は限定された3語だけであり、insights の探索も非再帰 `glob("*.md")` なので日付ディレクトリ配下を走査しない。`【U#】` の一般検出もない。`tools/check_docs.py:110-114`、同`:1147-1249`、同`:1274-1337`

- **real — decision/worklog fragment 内の未解決 brace は spool schema 側で赤になり得る。** malformed/unknown placeholder は fragment validator が拒否する。`tools/spool_fold.py:918-930`、同`:1273-1283`

- **refuted — worklog `title` に引用符を付けると機械的に赤、という主張は成立しない。** parser は非空文字列として受理し、引用符を含んだまま H2 に描画する。規約上は引用符なしが望ましいが、現在の checker にその禁止はない。`tools/spool_fold.py:286-309`、同`:1406-1408`、`tools/check_docs.py:551-553`

- **refuted — 一般 `docs/` 文書が byte budget 検査を受ける、という攻撃は成立しない。** byte budget は特定の command/reference/provenance skill 等に限定され、一般 docs は対象外である。`tools/check_docs.py:168-202`、同`:3260-3289`、同`:3528-3573`

### `tools/spool_fold.py --dry-run`

- **real — 固定 base digest が不一致なら赤になる。** `[T-139]` 更新の `base:` は、現時点では `docs/worklog.md:3080-3091` の substantive item 全体を対象にする。carry stub 自体を hash してはならず、stub なら参照 entry を再帰的に遡る。`docs/spool/worklog/README.md:81-88`、`tools/spool_fold.py:1004-1027`、同`:1128-1188`、同`:1349-1359`

正しい digest 規則は以下である。

1. 対象 ID の現行 item を探す。
2. compact carry `- [T-139] (NNN)` 等なら、entry NNN の同 ID を substantive item まで遡る。
3. bullet の先頭行と直後の継続行を含む item block を取る。
4. 内容を trim・Unicode 正規化せず、終端だけ1個の LF とした UTF-8 bytes を SHA-256 する。

根拠は `tools/spool_fold.py:286-325`、同`:350-351`、同`:1128-1188`。段2の固定値は、その時点の preimage と一致する保証がなく、親の独立値とも不一致なので使用してはならない。

- **real — `次の一手` の ID 保存則違反は赤になる。** `更新` fragment は対象 ID の置換として扱われ、欠落・重複・不正 carry は fold 時に拒否される。`docs/spool/README.md:86-110`、`tools/spool_fold.py:1293-1315`、同`:1337-1352`

- **real — fragment filename と frontmatter の byte 不一致は赤になる。** `kind`、`slug`、sequence、filename の整合は厳密に検査される。`docs/spool/README.md:28-49`、`tools/spool_fold.py:754-798`

- **refuted — D232 の並行採番衝突は placeholder を正しく使えば dry-run/fold が解消する。** D 番号は fold 時に canonical の最大番号から割り当てられる。`tools/spool_fold.py:1790-1809`

- **refuted — worklog が閾値付近だから fold 自体が必ず赤、という予測は成立しない。** fold は必要なら canonical worklog を archive へ回転させる。`tools/spool_fold.py:1868-1875`

### 受入全走

- **real — repository 実体を使う `check_docs` 系テストは上記の schema・参照エラーを継承する。** `orchestrator/tests/test_check_docs.py:6366-6374`

- **refuted — 新しい authority-none insight があるだけで RuleOps acceptance が必ず赤になるわけではない。** 現規約は新 insight ごとの固定 inventory や follow-up を要求していない。`docs/ruleops.md:36-38`、`tools/run_tests.py:629-666`

実走していないため、環境依存を含めた受入全走の成否は未判定である。

## B5. 親の実測主張

- **refuted — T-139 限定の roadmap 改訂にセレモニー 1〜3 が必要、という攻撃は成立しない。** roadmap-history はユーザーと協議・合意済みの改訂を版凍結・版上げ・改訂理由 D の対象外としている。worklog entry (299)/(300) には T-139 の採択内容と順序が記録されている。`docs/roadmap-history/README.md:13-27`、`docs/worklog.md:2646-2676`、同`:3066-3091`

- **real — 親 brief の一般的 paired-cluster 例外まで広げると、その免除根拠を失う。** 合意は T-139 の U3 と実行順序に関するもので、一般政策への展開ではない。段2の T-139 限定案が必要である。`brief.md:45-54`、`docs/worklog.md:2663-2672`

- **refuted — 新 D を書くことは roadmap セレモニー手順3の代用ではない。** 協議改訂では手順3自体が不要で、別件として D19/D134 の適用条件を限定する独立 D を書く構造である。`docs/roadmap-history/README.md:20-27`

- **refuted — 「現時点の次番号が D232」という観測自体は正しい。** canonical の末尾は D231 である。`docs/decisions.md:10856`

- **real — D232 を固定 ID として brief に焼くのは不安定である。** 並行 land で変わり得る。ただし段2プランは `<DNNN>` placeholder と fold 時採番を使っており、実装上は D232 に依存していない。`brief.md:8-17`、同`:78-81`、`s2-plan.md:54-60`、`tools/spool_fold.py:1790-1809`

- **refuted — 「一般 docs は byte budget 対象外」という親の主張は正しい。** `tools/check_docs.py:168-202`

- **refuted — P1 を採用する限り、「実装面ゼロなので段5の Codex 実装子を起動しない」は正しい。** 列挙された成果物は Markdown のみである。反対に `docs/` 配置を選び `LIVING_DOCS` を編集するなら、この主張は成立しなくなる。`brief.md:65-76`、`tools/check_docs.py:29-73`

## B6. 段2プラン固有

### 決定 (7)

- **real — D134 の意味を書き換えて適合を宣言している。** locked land transaction は既存手続きの説明には使えるが、D134 の「同じ変更単位」の定義を新 D 自身で変更することはできない。`s2-plan.md:108-120`、同`:216-225`、`docs/decisions.md:6506-6511`

- **real — pilot を fold 後に限定する条項は実質的な補償だが不十分。** canonical D のない状態での正規 pilot を規範上禁止する点は有効だが、現在は producer/qsub に強制されないため、手続き上の曖昧さを消せない。`s2-plan.md:112-120`

### package.md と確定値

- **real — 段2の指摘は正しい。** `package.md` は11件を未裁定とし、κ も未定と書いている。したがって「確定済み11件の正本」という brief の説明は不正確である。`output/insights/2026-08-07_t139-mainrun-design/package.md:3-11`、同`:75-76`、`brief.md:19-24`

- **real — 採択結果の根拠は worklog entry (299)/(300)、最終的には fold 後の新 D である。** `package.md` は裁定前の問い・選択肢・推奨理由を保存する凍結パッケージであり、事後的に書き換えるべきではない。`docs/worklog.md:2646-2676`、同`:3066-3091`

両原則を両立する記載例は次である。

> 裁定前の質問・選択肢・推奨理由は `package.md`（`authority: none`、凍結）を参照する。採択結果は worklog entry (299)、entry (300) および land 後の本件決定を正本とし、本書はその結果を指定 commit/path/blob へ射影する。`package.md` は採択後に改変しない。

- **real — 「U1〜U11 の確定値」をそのまま数値まで確定済みと読むことはできない。** U8 は ledger 分離までは採択されているが、正式 trial 前に必要な cap/cumulative 数値は閉じていない。U11 も方式選択はあるが数値表がない。`package.md:151-164`、同`:214-231`、`docs/worklog.md:2668-2672`

### wave commit の6ファイル

- **real — 「既知の完全な6点」という列挙は不足している。** brief だけを記録対象に含め、段2プラン、段3の逐語所見、段4裁定、後続 stage の記録を含めていない。dev-wave は段ごとの逐語記録を insights に保存する。`s2-plan.md:226-253`、`docs/dev-wave/core.md:87-100`

推奨する commit 境界は次のとおり。

- substantive commit: roadmap、decision fragment、凍結 preregistration、配置 README。
- record commit: worklog fragment、brief、段2・段3・段4および生成された後続記録。

両 commit を同じ locked land transaction に含める。D134 の原子的内容を明瞭にしつつ、後から生成される段記録を無理に substantive commit へ混ぜずに済む。もし運用上 wave commit を1個に固定するなら、「6点で完全」という表現をやめ、全段記録を列挙に加える必要がある。

### pilot submission 数 0

- **refuted — pilot 0 は無意味ではない。** U8/U11 の数値不足を隠して launch authorization を作ることを防ぎ、「現時点で投入不可」を commit/blob に凍結するという成果物影響がある。`package.md:151-164`、同`:214-231`、`s2-plan.md:198-214`

- **real — ただし T-139 の次の一手を pilot 投入可能な状態へは進めない。** worklog 上の順序は「roadmap 例外 → prereg freeze → producer → pilot」なので、zero-submission 版は fail-closed checkpoint であって、正の preregistration 完了ではない。`docs/worklog.md:3080-3091`

したがって、数値不足そのものをこの docs-only wave の must-fix にして推測値を埋めるべきではない。must-fix は成果物を「pilot を許可する凍結版」と誤記しないこと、および `[T-139]` を未完のまま維持することである。

### base digest

- **real — 段2が固定値を完成値として掲げたのは欠陥である。** digest は現在の substantive item bytes に依存し、並行 worklog fold でも変わる。親の独立計算と一致しない以上、値を信用してはならない。`s2-plan.md:237-243`、`docs/spool/worklog/README.md:81-88`

対象と計算規則は B4 のとおりであり、現在の対象は `docs/worklog.md:3080-3091`。値そのものは本所見では裁定しない。

## 総括

判定は条件付き **NO-GO**。

land 前の必須修正・裁定は次の4点である。

1. D134 の「同じ変更単位」について、fragment を署名決定と認めるかを段4で明示裁定する。新 D の自己定義だけで済ませない。
2. 本 wave の gate は文書層だけであり、producer・validator・consumer・qsub・receipt には未実装だと成果物へ明記する。
3. 確定結果の根拠を `package.md` ではなく worklog entry (299)/(300) と fold 後の新 D に直す。U8/U11 の未確定数値を捏造しない。
4. 固定 base digest を撤回し、最新 substantive `[T-139]` item から規定どおり再計算して dry-run で確認する。

P1 の `output/insights/.../preregistration.md` 配置、T-139 限定 roadmap 案、pilot 0 の fail-closed snapshot は採用可能である。ただし、それを「投入 gate を実装した」「pilot 前提が完了した」と表現してはならない。