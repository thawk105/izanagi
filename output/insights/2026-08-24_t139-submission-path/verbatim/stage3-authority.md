## 所見

### F1. canonical payload の発効権限がない

**real / blocker**

- 根拠: 親 brief は entry 874 を「既存裁定内の実装可」と要約するだけです。[stage1-brief.md:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage1-brief.md:4) D574 が認めたのは新しい exact-byte payload という承認対象の種類と trust edge であり、今回 plan が選んだ `decision_kind`、exact keys、successor grammar、I/M/V の具体的三つ組、payload bytes そのものではありません。[decisions.md:23168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/decisions.md:23168)
- entry 874 本文自体は射影されていません。しかし、要約どおり「既存裁定内の実装可」であっても、新しい canonical decision の内容を実装者が決め、その自己申告 bytes を authority として発効させる権限にはなりません。
- 具体的失敗: 実装者が選んだ payload が自分で D282 の successor を名乗り、自分で選んだ manifest/index を承認します。これは D574 決定(4)の「有効な approval payload」を「未承認 artifact の自己申告」に置換します。
- 成果物影響: plan の P commit、P を根拠にした production writer 正例、P を effective fold とする receipt は authority 不成立です。
- 推奨対処: P は scope 外へ出し、I/M の commit が安定した後、exact payload bytes をユーザー裁定へ戻してください。現在waveの正例は後述の非canonical fixtureだけに限定します。

### F2. `I -> M -> P -> C` は canonical fold の時系列と循環する

**real / blocker**

- 根拠: plan は P を C より前の通常 commit として扱います。[stage2-plan.md:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage2-plan.md:144) しかし同系統の先行 package 自身が、decision は spool fragmentであり、実 D 番号と fold は land 時に確定すると記録しています。[q1-package.md:237](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/q1-package.md:237)
- 具体的失敗: C のテスト、commit、受入時点では P はまだ canonical `docs/decisions.md` に存在しません。resolver は D282 を返し、writer は `vector_authority_unavailable` で拒否するのが正しい挙動です。P が見えるのは C の受入後、land lock 内の fold 後だけです。
- 成果物影響: production writer 正例を事前受入できません。fold 後に初めて開く経路が未検証のまま land します。
- 推奨対処: 安全な順序は `I/Mを不活性artifactとしてland -> exact Pを裁定・fold -> Pを含むbaseからCを実装・受入` です。単一authorの直列 commitでは解消しません。

### F3. local history を canonical authority と誤認している

**real / blocker**

- 根拠: plan は固定 D282 から `measurement_head` までの `docs/decisions.md` historyを走査します。[stage2-plan.md:62](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage2-plan.md:62) 現行入口では `repository_root` は caller が選び、`measurement_head` はそのローカル checkout HEADです。[_binding.py:220](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/_binding.py:220)
- 具体的失敗:

  1. 攻撃者が正規 D282 を含む clone/forkを作る。
  2. ローカル `docs/decisions.md` に successor fence、偽 manifest、偽 index を1組だけ追加する。
  3. D282 ancestry、一意 tip、cycleなし、digest一致を全部満たす。
  4. resolver が偽 payload を sealし、writerが受領証を発行する。

  root inode の固定は「同じforkである」ことしか証明せず、その HEAD が canonical 台帳であることを証明しません。

- 成果物影響: D574 決定(4)の payload trust edgeが、caller選択のローカル履歴へ置換されます。
- 推奨対処: P が別waveで canonical foldされた後、その exact `docs/decisions.md` BlobRefを固定 discovery anchorとしてロードしてください。vector digestはsourceに置かず、固定されたPの中から取得します。将来の自動追従が必要なら、署名済みtipなど別の外部authority設計が必要です。

### F4. 二段 root は汎用 successor chain を今すぐ必須にしない

**real / must-fix**

- 根拠: D574 決定(5)が要求するのは、固定baseと現在有効foldの意味分離です。[decisions.md:23190](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/decisions.md:23190) D626 はartifact不在時の汎用resolver実装を明示的に却下しています。[decisions.md:25102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/decisions.md:25102)
- 具体的失敗: plan はD574の意味契約から、任意の将来successorをローカル履歴から自動発見する実装を導出しています。この discovery algorithm は裁定されていません。
- 成果物影響: 不要な履歴走査面と偽authority経路が増えます。
- 推奨対処:
  - D282固定のまま作れるのは非canonical正例だけです。D282にはvector authorityがないため、production writer正例へ読み替える案は非同値です。
  - Pが別途承認・fold済みなら、Pのexact BlobRefだけを読む固定resolverは、現在履歴に対して同値で、将来P2にはfail-closedです。
  - 自動chain追従まで必要なら、その要否とcanonical tipの認証方法を追加裁定へ戻します。

### F5. 型、seal、cycle検査だけではD626/D563を満たさない

**real / blocker**

- 根拠: plan はmissing、cycle、複数successor、disconnected、mutation/removalを列挙しますが、何を候補authorityとして列挙してよいかを固定していません。[stage2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage2-plan.md:64)
- 現行D282 parserは固定BlobRef、exact D282 heading、対象fence exact 1件、section所属を全部要求します。[approval_payload.py:191](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/approval_payload.py:191) proposed resolverの「headingと自己申告decision_idが一致」は外部authorityではありません。
- 具体的失敗:
  - 任意text fenceが自分のheading IDを申告すれば候補になります。
  - illustrative fenceや重複headingが誤候補となり、偽受理または恒久DoSを起こします。
  - mergeを含むhistoryで「初出commit」がcanonical fold commitとは限りません。
  - predecessorがsuccessor導入commitのstrict ancestorであること、過去payload節のappend-only性、trusted tipまでの不変性が未定義です。
  - D563 sealは「このmoduleが発行したobject」を示すだけで、入力履歴がcanonicalであることを示しません。
- 成果物影響: seal済みだが無権限のauthorityが生成されます。
- 推奨対処: 固定P方式を採るか、少なくともtrusted tip、exact section/fence grammar、重複heading拒否、strict ancestor、append-only transition、merge規則、graph closureのseal束縛を仕様化してください。

### F6. receipt publish はD292の投入禁止を直接は迂回しない

**refuted / nit**

- D292が禁止しているのはpilot/mainの投入と、その禁止状態の暗黙解除です。[decisions.md:13583](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/decisions.md:13583)
- `_publish_receipt()` の境界はparse、binding/schema/semantic/authority検査、固定namespaceへのcreate-only書込みまでです。[_writer.py:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/_writer.py:53) qsub、driver、計算資源投入はありません。
- qsub投入境界は将来の `submit_pilot(*, binding)` またはdriver呼出しです。D264に従い今回それらをexportせず、planも作らないとしています。[stage2-plan.md:220](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage2-plan.md:220)
- 条件: 正例テストはtemp repositoryだけへpublishし、実receipt、4名前export、qsub注入境界を追加しないこと。

### F7. raw CMake実装との一致は、この射影から検証不能

**unclear / must-fix**

- D574の契約は明確です。raw `CMakeCache.txt`、schema `argv`、実compile argvが正の三者で、申告値は不一致拒否にだけ使います。[decisions.md:23184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/decisions.md:23184)
- planの文言自体はこの契約と一致しており、「申告一致を正の根拠にする」記述は見つかりません。[stage2-plan.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage2-plan.md:8)
- ただし `_semantic_validator.py` は必読射影に含まれておらず、読める4 production fileから確認できるのはwriterがvalidatorを呼ぶ事実だけです。[_writer.py:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/_writer.py:68)
- 成果物影響: 「production predicate変更不要」を正の根拠として採用できません。
- 推奨対処: author/review段で cited箇所を実読し、申告値を期待値生成、early return、positive legのいずれにも使っていないことを条件式単位で固定してください。不一致ならcomment修正ではなくmust-fixです。

### F8. `test_spool_fold.py` とentry 874 no-touch違反は現plan上は見えない

**refuted / nit**

- planは両面を明示的にno-touchとしています。[stage2-plan.md:224](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage2-plan.md:224)
- index更新と新vector追加は、既存42 vector JSON bytesを維持する限り、それ自体はentry 874本文/digestの編集ではありません。
- ただしplanの「`docs/decisions.md`へ追加」はspool fold規律と不整合で、これはF2のblockerです。
- author段では変更file一覧、entry 874 bytes/digest、旧42 vector path/digestを別々に検査する必要があります。今回はread-onlyで未実走です。

### F9. 「投入経路完成」という成果物名が過大

**real / must-fix**

- D597はT-338側が担うのはgateだけで、driver/collectorは外側と明記します。[decisions.md:24049](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage2/inputs/decisions.md:24049)
- 親briefのDW-G05はreceiptから材料report/試行台帳へ到達するように読めますが、planはdriver、collector、sink、4名前exportを全部除外しています。[stage1-brief.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage1-brief.md:18)
- 成果物影響: gate publication正例を「T-139投入経路完成」と誤認させます。
- 推奨対処: 完成条件を「private receipt admission/publish gateの結線」へ縮め、submission、collector、report/ledger到達は未完成と明記します。

## 親briefへの直接攻撃

親briefは次の三点でGO根拠になりません。

- entry 874の「実装可」を、exact payload bytesを新しいcanonical authorityとして承認する権限へ拡張しています。
- durable vector-bearing payloadが未発行だと認識しながら、その同じwaveで外部pin済みauthorityを成果物に要求しています。[stage1-brief.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage3/inputs/stage1-brief.md:10)
- manifest/resolver/writer結線だけのscopeを「投入経路」と呼び、未実装のqsub、collector、sinkまで到達したように見せています。

したがって brief のGOは撤回し、少なくとも「canonical P発行」と「gate実装」を別authority段へ分ける必要があります。

## planへの直接攻撃

planの致命点は、Pを通常のauthor commitとして扱っていることです。canonical fold時点、authority承認時点、テスト時点が混同されています。

また、`canonical path history` という名前でローカルGit historyをauthority化しています。固定D282を祖先に持つことは内容の連続性を示しますが、ユーザー承認やcanonical branch所属を示しません。

採用可能なのは次の部分です。

- writerの3引数signature維持
- fixed namespace、exact raw-byte publish、create-only
- bindingへのsealed authority運搬
- manifest宣言とpayload内vector refの一致検査
- D292、D264 export面のno-touch
- raw CMake三者と申告値reject-onlyという説明

Pの作成、local historyからの自動successor discovery、production writer正例は現planのまま採用できません。

## 採用可能な最小authority境界

現waveで許容できる最小境界は次です。

1. production authorityはD282固定のままとし、writerは引き続きfail-closedにする。
2. 正例は新規 `orchestrator/tests/fixtures/t139_effective_approval/` 配下のsynthetic payload、manifest、historyだけに限定する。
3. vector JSON/indexは既存 `orchestrator/tests/fixtures/t338_submission_gate/conformance/` を使えるが、「live test assetでありauthorityではない」と固定する。
4. fixture正例はtemp repositoryとtest-only sealed capabilityだけで実行し、`docs/decisions.md`、実receipt namespace、production loaderのauthority発行へ接続しない。
5. I/Mがcanonical commitとして安定した後、exact P bytesをユーザーへ提示して裁定・foldする。
6. 次waveは固定されたPのexact BlobRefからpayloadを読み、P内のVをauthority、M内のVを照合対象とする。local HEADはancestry/freshness検査にだけ使い、authority discoveryには使わない。
7. 将来P2を自動追従させる設計は別裁定までfail-closedにする。

## scope外

実装せず、次へ記録すべきreal所見です。

- exact P bytes、decision grammar、I/M/V三つ組の承認: 新規 rulings 記録、推奨先は `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-24-t139-exact-payload-authority.md`。entry 874は修正しません。
- arbitrary local forkを除外できる汎用canonical-history認証: 本段3所見とvector-authority designの後続packageへ記録し、T-139 writer実装へ混ぜません。
- `submit_pilot`、qsub、driver、collector、D292解除: D597およびland2 packageのK2/K3追跡へ戻します。
- entry 874へ記録が必要な場合は、874のamendではなく新しいworklog entryをappendします。

## 総括

現planは **NO-GO** です。blockerは、Pのexact bytesを発効させる権限不足、land-lock foldとC受入の循環、ローカルhistoryをcanonical authorityと誤認するtrust edgeの三件です。

非canonical fixtureによるparser、seal、graph拒否、writer内部経路の正例までは着手可能です。production writerを開くのは、I/M land、exact Pのユーザー裁定とcanonical fold、その固定Pを入力にした別waveの受入後に限定すべきです。pytestは実行しておらず、緑とは判定しません。