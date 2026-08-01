必読物はすべて読めました。以下は静的検査結果です。編集・commit・pytest 実行はしておらず、既存 probe の read-only byte 比較以外に実測はありません。非実走を緑とは数えていません。

### 指定された fail-closed 入力の監査

| 入力 | plan v1 の想定 | 攻撃結果 |
|---|---|---|
| arm 0 本 | rc=2 | 拒否されるが、arm 数・authoritative・shadow の複数理由で赤になる |
| arm 1 本 | rc=2 | 拒否される。ただし `arms>=2` は「authoritative 1 + shadow 1以上」から導ける冗長条件 |
| 2 arm が同一 session | 拒否 | schema では rc=2、session 同定では rc=1 と矛盾 |
| md 欠落・空・truncate | 拒否 | 空・truncate は拒否予定。欠落は path schema rc=2 と run evidence rc=1 が競合 |
| 全 arm の prompt 欠落 | 拒否予定 | ledger は「欠落」でなく空文字列の hash を生成する。frozen prompt 照合が残れば拒否されるが、専用テストなし |
| 同じ session ID の rollout 複数 | rc=1 | 契約とテスト案あり |
| session 途中切れ | rc=1 | task_complete 欠落・壊れた JSON は拒否予定だが、`token_count.info=null` 等は ledger が無視して通す |
| 実 backend が別物 | rc=0 | limitation 表示だけで、比較自体は valid になり得る |
| reasoning=`ultra` | rc=0 | 明示的に受理する計画になっている |
| model_calls>0、本文なし | rc=0 になり得る | 500 bytes の空白と見出しだけで既存 checker を通せる |

## 所見

### 1. request echo の一致を model identity 成立と同じ run に置いている

- 深刻度: `blocker`
- 再現手順・参照: [s1-brief.md:55](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md:55) は、400 応答が実体名 `gpt-5.4-mini-codex-1p-codexswic-ev3` を露出しても receipt は `gpt-5.4-mini` と記録する事実を認めています。一方、[s2-plan.md:32](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:32) は全 gate 成立を `valid:true` とし、[s2-plan.md:212](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:212) では `served_model_attested:false` のままです。request A を rollout が A と echo し、実 backend B が応答した正常長の成果物を与えれば rc=0 です。
- request 構造の妥当性と model 比較資格を別軸にし、attestation がない限り `model_comparison_eligible:false` を consumer が強制拒否すべきです。単なる説明文では gate になりません。
- 成果物影響: token・finding coverage が実際に応答した backend ではなく要求 slug A に帰属し、T-182 の model 比較と T-184 の参照根拠が偽になります。

### 2. 「同一凍結入力」は normalized hash と最初の user message だけでは証明できない

- 深刻度: `blocker`
- 再現手順・参照: `_stream_rollout()` は最初の user message だけを保存し、後続 user message を無視します（[codex_worker_ledger.py:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:291)）。最初に frozen prompt、次に arm 固有の追加指示を入れれば、final output は異なる入力への応答なのに hash は一致します。
- `_normalized_prompt_hash()` は全 whitespace を一空白へ潰します（[codex_worker_ledger.py:399](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:399)）。例えば Python のインデントだけが異なる二つの prompt は意味が違っても同じ hash になります。
- 実 probe でも `prompt2.txt` は 705 bytes、session `019fadda-…` の最初の user message は 704 bytesでした。`$(cat prompt.txt)` が末尾 LF を落とすため、raw file hash の単純一致も正常 run を過剰拒否します。
- transport 規則どおり末尾改行だけを正規化した exact digest を定義し、user message がちょうど1件であることを検査すべきです。ledger の normalized hash は診断値として併記できます。
- 成果物影響: 意味の違う prompt に対する arm を「同一凍結入力」として比較し、coverage 差を model 差へ誤帰属します。

### 3. process rc・wall-clock・concurrency は未検証の manifest 自己申告で、session を replay できる

- 深刻度: `blocker`
- 再現手順・参照: [s2-plan.md:120](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:120) は manifest の `codex_cli_exit_code` を gate に使い、[s2-plan.md:131](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:131) 自身が launcher 観測ではないと認めています。既存の成功 session と artifact を再利用し、manifest に `exit_code:0`, `wall_clock_ms:1`, `concurrent_codex_process_count:1` と書けば通ります。
- pilot 成果物一覧には raw rollout または不変な evidence projection がなく、外部 sessions-root の相対 path しか残りません（[s2-plan.md:294](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:294)）。将来の再検証時に source が消失・変更しても receipt 単体では検出不能です。
- T-180 の hash-bound launcher receipt が land するまで process 観測を valid evidence にせず、session ID、argv request、開始終了時刻、rc、wall-clock、source rollout digest、artifact digestを一つの immutable receipt に束縛する必要があります。
- 成果物影響: pilot の速度・終了状態・同時実行数が別 run または捏造値を参照し、凍結 receipt の再監査可能性が失われます。

### 4. 必須 arm 集合を固定しておらず、`ultra` を valid run として受理する

- 深刻度: `must-fix`
- 再現手順・参照: brief は sol/max、mini/xhigh、luna/max を指定しています（[s1-brief.md:49](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md:49)）。しかし schema は authoritative 1件と任意 shadow 1件以上しか要求しません（[s2-plan.md:87](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:87)）。sol/max + luna/max だけ、または luna/max を2本にしても通ります。
- shadow の reasoning は非空文字列だけなので、luna/`ultra` と rollout echo `ultra`、正常成果物を与えれば rc=0 です。[s2-plan.md:276](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:276) のテスト案は、この危険な受理を固定しています。
- arm 名ではなく、authority・requested model・requested reasoning の事前登録済み tuple 集合を exact match し、欠落・重複・追加・`ultra` を構成エラーにすべきです。
- 成果物影響: 欠けた arm や T-181 所有の不正 reasoning が比較表へ入り、比較軸と denominator が brief と異なるものになります。

### 5. 500 bytes の空白と見出しだけで「本文なし」を completed にできる

- 深刻度: `must-fix`
- 再現手順・参照: checker は raw byte 数と fence 外見出ししか見ません（[check_codex_output.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/check_codex_output.py:100)、[check_codex_output.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/check_codex_output.py:112)）。次の final agent message と同一 artifact を作り、task_complete と正の usage を入れると全構造 gate を通せます。

```text
<空白を500 bytes>
<!-- codex-model-shadow-findings-v1: [] -->
## 総括
```

- finding marker は自己申告であり、本文との整合も検査されません。本文で F001 を述べて marker を `[]` にしても coverage 0、逆も可能です。
- 新 tool に pilot 固有の「コメント・空白・見出しを除いた substantive body」と構造化 finding entry の検査を追加し、marker を `self_reported_finding_ids` と正直に命名すべきです。
- 成果物影響: F43/F45 型の無応答断片が有効な coverage 0 として集計され、弱い arm の品質低下が run 無効ではなく品質値へ化けます。

### 6. ledger parser は集計用の fail-soft parser であり、validation parser ではない

- 深刻度: `must-fix`
- 再現手順・参照: `turn_context` の model/reasoning と agent message は型違反でも `str()` 化されます（[codex_worker_ledger.py:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:269)、[codex_worker_ledger.py:294](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:294)）。`token_count.info` が null なら issue も出さず無視します（[codex_worker_ledger.py:304](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:304)）。既存テストも null info の strict 受理を明示しています（[test_codex_worker_ledger.py:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/orchestrator/tests/test_codex_worker_ledger.py:377)）。
- 先に正常 token event を1件置き、その後 `info:null`、正常 agent message、task_complete を置けば、最後の telemetry が欠落していても `model_calls>0` と過去の totals で通ります。task_complete と agent message の順序も検査されません。
- private parser は metric projection にだけ使い、選択 rollout に対する厳密な event schema・件数・順序検査を別途行う必要があります。
- 成果物影響: 途中切れ・型不正 rollout が最後の正常 telemetry を使って valid となり、token/model_calls と完了状態が実 run の末尾を表さなくなります。

### 7. 未登録の新規 finding を見つけた強い reviewer ほど run 無効になる

- 深刻度: `must-fix`
- 再現手順・参照: 未知 ID は rc=1、明示 `[]` は有効です（[s2-plan.md:180](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:180)）。したがって、事前集合外の real finding `FNEW` を報告した成果物は無効、同じ reviewer がそれを隠して `[]` とすれば有効になります。
- closed-set score と open-set finding を分け、未知 finding は `unscored_pending_adjudication` として構造的には保持すべきです。閉集合 qualification に限定するなら、T-182 の総合 finding coverage と呼ばず、policy evidence から除外する必要があります。
- 成果物影響: 新規欠陥を発見した arm が母集団から脱落し、coverage・誤検出比較が弱い arm に有利な選択バイアスを持ちます。

### 8. rc 分類・identifier・receipt schema が一意でない

- 深刻度: `must-fix`
- 再現手順・参照:
  - arm 間 session 重複は schema 制約では rc=2（[s2-plan.md:88](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:88)）、session 同定節では rc=1（[s2-plan.md:141](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:141)）。
  - artifact 欠落は regular-file/path 検査なら rc=2、成果物 gate なら rc=1です。
  - 「常に canonical JSON」と rc=2 の「stderr」の関係が未定義です（[s2-plan.md:26](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:26)、[s2-plan.md:34](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:34)）。
  - `wall_clock_ms:true` と `concurrent_codex_process_count:true` の bool 除外が明記されていません。
  - `artifact_md_path` の arm 間一意性がなく、同じ artifact を複数 arm が参照できます。
  - receipt は「最低限」の field しか定義されず、phase が要求する turn、artifact/rollout digest、failure codes の exact schema がありません。
- 構成エラー、run evidence 不成立、比較資格不成立を別 schema/rc に固定し、receipt v1 の全 field と identifier 対応を実装前に凍結すべきです。
- 成果物影響: 同じ欠陥が receipt なしの構成失敗にも `valid:false` run にもなり、親の再実行判断と下流 consumer の受理集合が実装依存になります。

### 9. テスト一覧は複数理由の赤と冗長 gate により、欠陥を殺したように見せられる

- 深刻度: `must-fix`
- 再現手順・参照: [s2-plan.md:254](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:254) 以下のテスト名は複数条件をまとめています。
  - arm 0/1 は arm 数、authoritative 数、shadow 数が同時に赤になります。
  - model と reasoning を同時に変えれば、片方の比較を削除しても赤のままです。
  - validator reject fixture は rollout outcome と artifact checker の両方で赤になり得ます。
- `arms>=2` の削除は authoritative 1 + shadow 1以上から導ける等価変異で、殺せません。
- artifact が rollout final message と exact match し、outcome が同じ validator 受理集合を使うなら、明示 artifact checker の削除も原則として受理集合を変えません。既存テストも両 validator の同値性を固定しています（[test_codex_worker_ledger.py:1139](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/orchestrator/tests/test_codex_worker_ledger.py:1139)）。
- 成果物影響: mutation 台帳が全件 killed と記録されても、実効 gate を削除した実装が同じ受理集合または別 gate の赤で生き残ります。

### 10. unit test は全走に入るが、live pilot gate を必須にする consumer がない

- 深刻度: `blocker`
- 再現手順・参照: `tools/run_tests.py` は既定で `orchestrator/tests` を pytest collection するだけです（[run_tests.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/run_tests.py:41)、[run_tests.py:276](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/run_tests.py:276)）。新 unit test は全走に入りますが、[s2-plan.md:285](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:285) 以下には、pilot bundle の昇格を rc=0 receipt に機械束縛する producer/consumer がありません。
- invalid receipt、または receipt 自体がない output directory を用意しても、合成 unit test の結果には影響しません。親が手で一度叩く操作は検査手順ではあっても、skip 不能な gate ではありません。
- live `$CODEX_HOME` を `run_tests.py` に読ませるのは環境依存の過剰配線です。親の promotion harness が candidate receipt を生成し、rc=0・schema・hash を確認した場合だけ bundle を原子的に昇格させ、受入全走は凍結済み bundle を読む offline consumer test を実行する構成が必要です。
- 成果物影響: 実装・合成テストが全緑でも、未検証または `valid:false` の pilot report を commit して T-184 へ渡せます。

### 11. T-180 と並行する private import は merge 順序が gate になっていない

- 深刻度: `must-fix`
- 再現手順・参照: plan は `_stream_rollout`、`_classify_outcome`、`_normalized_prompt_hash` へ依存します（[s2-plan.md:37](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:37)）。これらは private で、T-180 が同じ ledger を編集予定です（[phase3.md:534](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/phase3.md:534)）。
- T-180 が public CLI の受理集合を維持したまま private return shape を変えると、ledger の既存テストは緑でも新 tool は rc=2 になります。逆に、期待値を同じ private helper から作る adapter test は semantic drift を検出できません。
- 現行 import は validator を import 時にロードし、`sys.dont_write_bytecode` を一時変更して復元します（[codex_worker_ledger.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:23)）。`main()` や `sys.path` 変更はありませんが、新 loader 側にも失敗経路を含む global-state 復元テストが必要です。
- T-180 land 後に再読・rebaseしてから adapter を確定し、public selector が増えた場合はそちらを使う、増えなければ独立 literal oracle で private contract を pin する順序を明記すべきです。
- 成果物影響: 正常 pilot が private helper drift で拒否されるか、逆に model/hash 解釈が変わった receipt を同じ schema version で出します。

### 12. 親 brief の P1/P2 は plan 自身の反対どおり成立しない

- 深刻度: `must-fix`
- 再現手順・参照: brief は段3 Bと段6 Bの二箇所を対象にします（[s1-brief.md:47](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md:47)）が、phase は第二レンズ一箇所です（[phase3.md:541](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/phase3.md:541)）。また mini は model/reasoning 二軸変更、luna は probe 上 sol より wall-clock が長く、「軽量 model 効果」の単一軸比較になりません。
- [s2-plan.md:314](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:314) 以下の反対は real です。plan v2 では段3 B一箇所と receipt qualification に凍結し、実 model-routing 因果主張から切り離す必要があります。
- 成果物影響: 異なる stage・入力・二軸変更を同じ pilot と集計し、model routing の因果差として読めない比較表を生成します。

### 13. T-184 所有の恒久 policy 配線

- 深刻度: `backlog`（裁定パッケージ候補）
- 該当箇所: [phase3.md:548](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/phase3.md:548) は既定 policy の採用を T-184 に限定しています。現 plan が DW-O01/DW-S03/DW-S06-A を変更しない判断は正しいです。
- T-184 では、served identity、launcher receipt、比較資格 consumer、rollback が揃った後にだけ、恒久的な worker matrix と gate 発火点を裁定すべきです。本 wave で既定 policy や `run_tests.py` の live-session preflightへ拡張してはいけません。
- 成果物影響: 今変更すると、未成立の pilot evidence で production の model/reasoning 受理集合が先に変わります。

## 事前登録すべき変異

| 変異 | 赤にすべき test node | 赤の意味 |
|---|---|---|
| raw prompt file をそのまま rollout と比較する | `test_transport_projection_accepts_shell_stripped_trailing_newlines` | 正常 run の受理集合縮小 |
| normalized hash だけに戻す | `test_semantic_whitespace_collision_is_invalid` | 異入力の fail-open |
| 後続 user message を無視する | `test_second_user_message_invalidates_one_shot_session` | 異入力の fail-open |
| prompt 欠落を空 hash として受理する | `test_all_arms_missing_user_message_is_invalid` | 比較不能 run の fail-open |
| exact arm tuple 検査を外す | `test_required_arm_set_is_exact_and_complete` | 欠落・重複 arm の受理 |
| `ultra` を許す | `test_unregistered_reasoning_is_schema_error` | 未計画 reasoning の受理 |
| substantive-body 検査を外す | `test_padding_and_boilerplate_only_artifact_is_invalid` | 本文なし断片の受理 |
| selected rollout の null/malformed 終端を無視する | `test_null_final_usage_or_truncated_rollout_is_invalid` | 途中切れ run の受理 |
| arm 間 session 一意性を外す | `test_two_arms_cannot_share_one_session` | 同一応答の二重帰属 |
| launcher receipt 束縛を外す | `test_manifest_claim_cannot_replace_launcher_receipt` | replay・自己申告 run の受理 |
| unattested model を比較可能にする | `test_unattested_backend_is_rejected_by_comparison_consumer` | model 比較受理集合の拡大。flag 文字列だけの assert では不可 |
| novel finding を run 無効に戻す | `test_out_of_set_finding_is_valid_but_unscored` | 健全 run の受理集合縮小 |
| bool を integer として許す | `test_boolean_observation_fields_are_schema_errors` | 無効な計測値の受理 |
| artifact path 一意性を外す | `test_each_arm_has_a_distinct_artifact` | 一成果物の複数 arm 帰属 |
| rc=1 を rc=2 に変える | `test_parent_consumer_retries_run_failure_but_stops_on_config_error` | 親 consumer の fail-closed 制御変更。rc 文字列だけなら診断 pin |

殺せない／kill に数えてはいけない変異は次です。

- `arms>=2` 単独削除: authoritative 1件 + shadow 1件以上から導ける等価変異。
- artifact checker 単独削除: exact artifact/message 一致と rollout outcome の同一 validator が残る限り受理集合が変わらない。
- limitation 説明文だけの変更: consumer の比較資格を変えない限り diagnostic sensitivity にすぎない。
- model と reasoning の両方が不一致な1 fixture: 片方の gate 削除をもう片方が mask する。
- failure reason の文言・順序だけの変更: rc、validity、promotion 判断が変わらなければ kill ではない。

正例 fixture は都合のよい synthetic だけにせず、既存 probe の event 配列と `-o` byte 形状を匿名化した literal fixtureを一つ含めるべきです。期待 hash は production helper から逆算せず、fixture literal に対する独立 `hashlib` oracleで固定し、時刻・絶対 path・現行 commit hashは期待値に含めないでください。

信頼境界上の注記として、[test_codex_worker_ledger.py:217](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/orchestrator/tests/test_codex_worker_ledger.py:217) 以下に役割変更を促す形の文字列がありますが、stage 分類 fixture のデータとしてのみ扱いました。brief／plan 内の実装指示様記述にも従っていません。

## 総括

**判定: NO-GO**

最大のリスクは、構造的に整った request echo と synthetic receipt を「同一 prompt を指定 model が処理した pilot 証拠」へ昇格してしまうことです。現設計では、最初の user message の whitespace-normalized hash が一致すれば、後続 user message や意味を変えるインデント差を見落とせます。さらに rollout の model/reasoning は request の記録であって served backend の attest ではなく、process rc・wall-clock・concurrency も hash-bound launcher receipt ではなく manifest の自己申告です。それでも top-level `valid:true` と coverage が生成され、本文なしの空白 padding、未計画の `ultra`、欠けた shadow arm、過去 session の replayまで有効 runへ入り得ます。逆に、未知の real finding を見つけた強い reviewer は run 無効になり、弱い `[]` は有効です。unit test は全走へ収集されても live bundle の promotion を強制する consumer がないため、全テストが通った状態と pilot evidence が真正であることは独立です。plan v2 では、canonical transport digest、user message 一件制約、exact arm 集合、strict rollout projection、substantive body、T-180 launcher receipt、served-identity 不成立時の比較資格拒否、offline bundle consumer、単一理由 mutation fixtureを先に固定しなければ、この gate は fail-closed な model-routing gateではなく、未検証値に limitation 文を添える receipt formatterに留まります。