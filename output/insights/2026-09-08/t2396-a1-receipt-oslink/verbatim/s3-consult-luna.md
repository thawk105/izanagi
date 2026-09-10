## 既存 7 テストの対判定

### 所見 1: M1 の公開境界検査は維持される

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行は `test_paper_story_a1_job_contract.py:2310-2343` で完成済み staging、final 不在、canonical bytes、1 回の公開を検査する。変更案も `s2-plan.md:448-509` で `os.link` の直前に同じ事実を検査し、成功後の staging 不在を追加する。
- 成果物影響: 放置して変更案どおりなら certified な選択結果、材料レポート、試行台帳の値・受理集合・参照は変わらない。
- 提案: `paired.os.link` の monkeypatch と `publish_boundaries == 1` を両方残す。
- 推測か実証か: 静的に実証。

### 所見 2: M2 の create-only 契約は弱まらない

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行 `test_paper_story_a1_job_contract.py:2346-2360` は既存 bytes 不変と空き先成功を検査し、変更案 `s2-plan.md:511-562` はさらに正負両方の staging 不在を検査する。
- 成果物影響: 放置して変更案どおりなら既存 receipt を上書きする入力は引き続き拒否され、3 種の成果物の受理集合は広がらない。
- 提案: bytes 完全一致と空き先正例を残す。英語エラー文の完全一致は所見 18 のとおり外す。
- 推測か実証か: 静的に実証。

### 所見 3: publish failure 後の owned staging 撤去は実際の新例外へ移せている

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行 `test_paper_story_a1_job_contract.py:2492-2526` の `OSError` と helper 由来 `PaperStoryError` を、変更案 `s2-plan.md:587-648` は実際の `os.link` が出す `FileExistsError` とその他の `OSError` に置き換える。
- 成果物影響: 放置して変更案どおりなら公開失敗後の stale staging により次の試行台帳が過剰拒否されることはない。
- 提案: 新しい 2 例外を維持する。旧 `PaperStoryError` 注入は廃止される helper 固有の枝なので削除してよい。
- 推測か実証か: 静的に実証。

### 所見 4: 差し替え staging の identity 保護は維持される

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行 `test_paper_story_a1_job_contract.py:2529-2556` は publish 境界で別 inode に交換し、変更案 `s2-plan.md:650-706` も新しい `os.link` 境界で同じ交換と dev/ino 不一致を検査する。
- 成果物影響: 放置して変更案どおりなら他者の staging を削除して試行台帳の参照元を破壊する入力は受理されない。
- 提案: このテストを identity 変異の単独所有者として残す。
- 推測か実証か: 静的に実証。

### 所見 5: foreign staging の投入前拒否は維持される

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行 `test_paper_story_a1_job_contract.py:2559-2590` は intent と qsub より前の拒否を検査し、変更案 `s2-plan.md:708-727` は helper 名と kind 引数だけを変える。
- 成果物影響: 放置して変更案どおりなら foreign staging がある試行は qsub されず、試行台帳の受理集合は変わらない。
- 提案: intent 不在と qsub 0 回の assertion を削らない。
- 推測か実証か: 静的に実証。

### 所見 6: clean namespace の正例は維持される

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行 `test_paper_story_a1_job_contract.py:2593-2617` と変更案 `s2-plan.md:729-748` は、未使用 namespace で 1 回だけ投入でき、final receipt があり staging がないことを同じく検査する。
- 成果物影響: 放置して変更案どおりなら正当な試行が過剰拒否されず、certified 候補と試行台帳の受理集合は狭まらない。
- 提案: final receipt、qsub 回数、staging 不在の 3 assertion を維持する。
- 推測か実証か: 静的に実証。

### 所見 7: submission の NAME_MAX 境界は維持される

- 深刻度: 問題なし
- 根拠 (`file:line`): 現行 `test_paper_story_a1_job_contract.py:2620-2644` と変更案 `s2-plan.md:750-766` は encoded basename の上限と正例投入をともに検査する。
- 成果物影響: 放置して変更案どおりなら有効な最長 attempt 名が拒否されず、試行台帳の受理集合は変わらない。
- 提案: encoded byte 長の検査を文字数検査へ弱めない。
- 推測か実証か: 静的に実証。

## 波及、caller、consumer

### 所見 8: シンボル参照の変更箇所は揃うが、plan の波及調査は repo 全体ではない

- 深刻度: 中
- 根拠 (`file:line`): `s2-plan.md:984-1050` は「指定された production file と二つの test file」に限定している。repo 全体の参照は以下のとおり。
  - `_publish_submission_receipt`: 定義 `paper_story_a1_paired.py:874`、production caller `:3244,3343`、test caller `test_paper_story_a1_job_contract.py:2355,2359,2518,2523,2551,2555`。
  - `_submission_receipt_staging_path`: 定義 `paper_story_a1_paired.py:836`、production caller `:876,3082,3278`、test caller `test_paper_story_a1_job_contract.py:2510,2537,2568,2602,2633`。
  - `_remove_submission_receipt_staging`: 定義 `paper_story_a1_paired.py:849`、caller `:890` のみ。
  - `_exclusive_write`: 定義 `paper_story_a1_paired.py:816`、production caller `:3056,3105,3190,3314,4177,4203,4242,4260,4350,6051,6095,6120,6277,6950,6975,7198,7231,8199,8279,8280,8289`。外部 test caller は `test_paper_story_a1_job_contract.py:2749,2811,3022`、`test_paper_story_a1_paired.py:577,728,733,776,811,845,2169,2171,2245,2246,3583,3598,3872,3939,3969,3987`、`test_p3_exploration_namespace.py:306`。
  - job body は `tools/pegasus/paper_story_a1_paired.sh:513-519` で final receipt の存在を最大 60 秒待つ。
- 成果物影響: `_exclusive_write` を一般化すると intent、barrier、raw result、材料 bundle まで変わり、試行台帳と材料レポートの値・受理集合が scope 外で変わる。job body を無視すると公開後 cleanup failure 時の実行結果を誤分類する。
- 提案: `_exclusive_write` 自体と一般 caller は一切変えず、completion の `paper_story_a1_paired.py:4260,4350` だけを置換する。波及表へ shell job body を加える。
- 推測か実証か: repo-wide `rg` による静的実証。

### 所見 9: 公開後 cleanup failure の扱いは brief の不変条件と実行経路に矛盾する

- 深刻度: 高
- 根拠 (`file:line`): brief は `s1-brief.md:54` で「失敗時に staging を残さない」とするが、plan は `s2-plan.md:258-260` で final を残したまま command を非ゼロにし、テストも `s2-plan.md:833-841` で staging が残ることを要求する。job body は `paper_story_a1_paired.sh:513-519` で final の存在だけを見て先へ進む。
- 成果物影響: submission では CLI が失敗を返しても 3 job は receipt を読み bench へ進み得る一方、`submission-failure.json` は作られない。completion では完成 receipt が存在するのに CLI 非ゼロで後続 materialize が止まり、raw 結果はあるが材料レポートがない状態になり得る。
- 提案: 親が二択を裁定すること。推奨は、final link とその directory fsync が済んだ時点を成果物上の成功とし、cleanup failure は非致命の診断にする案。非ゼロを選ぶなら、submission と completion の両 caller が final receipt を権威として後続処理を続ける契約とテストを追加する。現案の中間状態では実装してはいけない。
- 推測か実証か: 制御フローは静的に実証。外側の運用が非ゼロで停止する点だけは運用依存の推測。

## テストと変異帰属

### 所見 10: completion の新テストは部分公開禁止を挙動で証明しない

- 深刻度: 高
- 根拠 (`file:line`): `s2-plan.md:773-800` は既存先拒否、最終 bytes、staging 不在しか検査しない。`s2-plan.md:847-871` は helper 名を数える AST 検査である。completion 専用枝が final を `O_EXCL` で直接書き、既存先だけ同じ error prefix に変換しても、この挙動検査を通せる。
- 成果物影響: completion の書込み途中停止で千切れた `completion.json` が完成名を占有し、その attempt の proof chain、certified 選択結果、材料レポートを回復不能にする。
- 提案: AST wiring test は削除し、completion についても `os.link` 呼出し直前に canonical staging が完成し final が不在であることを観測する挙動テストへ置き換える。
- 推測か実証か: テスト assertion から静的に実証。

### 所見 11: 6 変異のうち 4 件は冗長 kill、1 件は survive し、単独帰属が成立するのは identity だけ

- 深刻度: 高
- 根拠 (`file:line`): 変異対象は `s2-plan.md:194-223`、予定テストは `s2-plan.md:935-968`。
  - `os.link` から `os.replace`: literal 置換で keyword を残すと `TypeError` により多数の正例が赤になる。keyword を除く意味的置換でも M1 は link seam 未通過、M2 は既存先上書きでともに赤になる。単独帰属不成立。
  - `os.link` から `os.rename`: 同じく literal 置換では `TypeError`、意味的置換では M1 と M2 がともに赤になる。単独帰属不成立。
  - 公開成功後の staging 撤去削除: M1、M2、clean namespace、NAME_MAX、completion 正例が staging 残存で赤になる。単独帰属不成立。
  - `FileExistsError` の握り潰し: M2 の `pytest.raises` と link-failure test の FileExists case がともに赤になり、共通 helper なら completion 負例も赤になる。単独帰属不成立。
  - identity 検査削除: `test_submission_receipt_cleanup_preserves_replaced_staging` が foreign inode の削除または identity error 不在で赤になる。これは単独帰属が成立する。
  - 宛先 directory fsync 削除: 該当呼出しを観測するテストがなく survive する。
- 成果物影響: 帰属不能な変異はどの検査が受理集合を守るか証明できず、fsync 変異は durable な試行台帳参照を失っても検査が通る。
- 提案: 段 4 では literal 置換か意味的置換かを明記する。単独所有が必須なら重複 assertion を分離するか、所有単位をテスト集合として登録する。現状の 1 変異 1 テスト帰属は登録しない。
- 推測か実証か: テスト本体と予定コードから静的に実証。

### 所見 12: 宛先 directory fsync の変異を殺す検査がない

- 深刻度: 高
- 根拠 (`file:line`): production 案は `s2-plan.md:215-220` で link 後 fsync と cleanup を行うが、予定テスト `s2-plan.md:768-930` は `_fsync_directory` の呼出し順も回数も観測しない。cleanup 自身にも `s2-plan.md:148-150` の同一 parent fsync があるため、単なる「1 回呼ばれた」検査でも mutation は見逃す。
- 成果物影響: crash 後に final directory entry が失われると job body は timeout し、測定値、certified 選択結果、材料レポートが生まれず、試行台帳は failure 側へ変わる。
- 提案: event 列を `link -> final-parent fsync -> cleanup -> cleanup-parent fsync` として検査し、最初の fsync 削除でのみ赤になる focused test を追加する。
- 推測か実証か: mutation survive は静的に実証。実 crash 時の消失は filesystem durability 契約に基づく推測。

## Scope の裁定

### 所見 13: P1 completion receipt の変更は支持する

- 深刻度: 高
- 根拠 (`file:line`): 現行は `paper_story_a1_paired.py:4259-4261,4349-4351` で完成名を直接書く。brief の成果物分析 `s1-brief.md:28-32` と D1732 の部分公開禁止 `verbatim-D1732.md:13-16,21` が同型の危険を示す。
- 成果物影響: 据置きでは途中停止した completion が final 名を占有し、proof chain を閉じられず certified 選択結果と材料レポートが欠落する。
- 提案: P1 は採用する。ただし所見 9 の cleanup 終端と所見 10 の挙動テストを先に確定する。
- 推測か実証か: 直接書込みは静的に実証。途中停止時の partial bytes は故障モデル上の推測。

### 所見 14: P2 materialize 据置きは支持する

- 深刻度: 問題なし
- 根拠 (`file:line`): `_publish_materialization_bundle` は `paper_story_a1_paired.py:8256-8309` で directory staging を公開する。directory hard link はこの file receipt の置換 primitive にできない。既存 fallback は `:8044-8052,8090-8126,8155-8186` で選択機構と制限を材料 result に記録する。
- 成果物影響: `os.link` へ強制すると materialization は受理されず材料レポートが生成されない。据置きなら certified 選択値は変えず、材料レポートの既存 limitation も保たれる。
- 提案: P2 は無変更とし、`test_paper_story_a1_paired.py:2260-2405` の rename probe/fallback monkeypatch を削除しない。
- 推測か実証か: directory publish と既存 evidence は静的に実証。

### 所見 15: P3 submission-failure 据置きには反対だが D1732 の射程外である

- 深刻度: 高
- 根拠 (`file:line`): `_write_v3_submission_failure` は `paper_story_a1_paired.py:3037-3067` で final `submission-failure.json` を `_exclusive_write` へ直接渡す。brief は `s1-brief.md:36-38` で「成功 chain を塞がない」ことだけを据置き理由にしているが、この file 自体が失敗試行の唯一の台帳である。
- 成果物影響: partial failure receipt が final 名を占有すると、その attempt の失敗理由と job status を復元できず試行台帳の値と参照が壊れる。certified 選択値は直接変えないが、再走根拠が欠落する。
- 提案: 本 wave へは混ぜない。D1732 が明示した group submission、completion、materialize の外なので、別の裁定パッケージへ「failure receipt も staging + atomic no-replace にするか」を返す。
- 推測か実証か: 直接書込みは静的に実証。途中停止は故障モデル上の推測。

### 所見 16: main path は D1732 の禁止を復活させていないが、P1 は明示裁定が必要

- 深刻度: 中
- 根拠 (`file:line`): D1732 は `verbatim-D1732.md:3-6` で group submission を `os.link` に決定し、completion と materialize は「棚卸し」としている。plan と brief はともに P1 を変更、P2 を据置きとしており、相互には食い違わない。ただし「棚卸し」は completion の変更まで確定したとは一意に読めない。
- 成果物影響: P1 を無裁定で混ぜると completion receipt の公開失敗集合と CLI 終端が変わる。P2 の `_RENAME_DEFAULT` は既存材料 report の limitation を維持するだけで、submission への素の rename 復活ではない。
- 提案: 親が P1 採用を明示する。staging 作成時の `O_EXCL` は final への直接書込みではないため維持してよい。P3 の final `O_EXCL` だけは所見 15 として別裁定へ返す。
- 推測か実証か: 文言とコードは静的に実証。D1732 の自然言語射程には解釈を含む。

## 実効性と一般化

### 所見 17: 1 回の probe から「Lustre 全般で os.link が通る」への一般化は強すぎる

- 深刻度: 高
- 根拠 (`file:line`): brief は `s1-brief.md:15-23,44-45` で durable base 直下の scratch 1 回から Lustre 全般へ広げる。実際の v3 final は `paper_story_a1_paired.py:2414-2421` の `attempt/receipts` 配下である。
- 成果物影響: 実環境で link が失敗すると、submit 側は failure receipt を書き、3 job は `paper_story_a1_paired.sh:513-519` で timeout terminal を残して bench へ入らない。測定値と certified 選択結果は 0 件、材料レポートは生成不能、試行台帳だけが失敗へ変わる。
- 提案: claim を「当該 client、mount、時点、probe directory で成功」に狭める。code gate や receipt field は増やさず、attempt-0003 前に実際と同じ `attempt/receipts` directory layout で operational probe を再実施する。
- 推測か実証か: 1 回だけの probe と実 path の相違は実証。誤り得る条件は DNE directory striping、client/server version 差、mount policy、ACL、project quota、inode/link limit、MDS failover、transient I/O などの推測。

### 所見 18: exact 英語 message と AST wiring は成果物契約でなく、余分な実装 pin である

- 深刻度: nit
- 根拠 (`file:line`): `s2-plan.md:782-785` は `"File exists"` の英語文面を完全一致で固定し、`s2-plan.md:847-871` は helper 名を AST で固定する。JSON bytes、排他性、公開原子性のどれにも必要ない。
- 成果物影響: 放置しても runtime の certified 値や材料レポートは直接変わらないが、同値な正しい実装をテストが拒否し、実際の部分公開欠陥を AST 合格で見逃し得る。
- 提案: exact message assertion と同一内容の `FileExistsError` 専用 catch は削る。AST wiring test も削り、所見 10 の completion 公開境界テストへ置き換える。schema、gate、台帳、互換層は追加しない。
- 推測か実証か: 静的に実証。直接の成果物影響がないため nit と自己申告する。

### 所見 19: production module を直接参照する consumer test 集合に漏れはない

- 深刻度: 問題なし
- 根拠 (`file:line`): 参照は `test_campaign.py:5358`、`test_ccbench_spawn_sites.py:128`、`test_hooks.py:3051`、`test_official_perf_closure.py:57`、`test_p3_build_authority_cli.py:159`、`test_p3_exploration_namespace.py:37`、`test_paper_story_a1_headline.py:1238`、`test_paper_story_a1_job_contract.py:17`、`test_paper_story_a1_paired.py:24` の 9 test file で、`s1-anchors.md:56-62` と一致する。`materializer_admission.py:58` は test ではない production consumer である。
- 成果物影響: 放置しても焦点走の test 集合不足による certified 値、材料レポート、試行台帳の未検査変更は生じない。
- 提案: 9 test file を焦点走集合として維持し、`materializer_admission.py` は静的 consumer として別枠で扱う。shell job body は module 参照集合ではないが、所見 8 の runtime consumer として追加確認する。
- 推測か実証か: repo-wide 参照検索で静的に実証。

## 総括

親が裁定すべき択一:

- P1: completion も staging + `os.link` に変える案を採用する。これは成果物上必要。
- P2: materialize は既存 directory publish のまま据え置く。
- P3: 本 wave では変更せず、failure receipt の atomic publish を D1732 射程外の別裁定へ返す。
- 公開後 cleanup failure:
  - 推奨: durable final を成果物上の成功とし、cleanup failure は非致命の診断にする。
  - 代案: command 非ゼロを維持するなら、submission と completion の後続 caller が final を権威として続行する契約を同時に決める。
- 変異帰属: identity 検査削除だけは単独帰属可能。他の 4 変異は冗長 kill、directory fsync 削除は survive する。

次を変えなければ実装してはいけない:

- `s2-plan.md:258-260` の公開済み cleanup failure 終端を裁定し、`s1-brief.md:54` との矛盾を解消する。
- completion に M1 相当の公開境界テストを追加し、AST wiring test を削除する。
- `link -> replace/rename` の変異を literal 置換か意味的置換か明記し、冗長 kill を単独帰属として登録しない。
- final directory fsync の順序を直接観測する focused test を追加する。
- 波及表へ `tools/pegasus/paper_story_a1_paired.sh:513-519` の runtime consumer を加える。
- 「Lustre で通る」という一般化を exact probe surface に狭める。
- `_exclusive_write` の一般 caller、materialize、schema、gate、台帳、互換層へ変更を広げない。

以上は read-only の静的検査であり、pytest の緑は主張しない。