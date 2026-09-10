静的照合と read-only の Git 実測だけを行った。テストは実走していない。

## 所見 1: fixture 更新により主要な land 負例が偽の緑になる

所見: `_Repo._acceptance_receipt` の digest を一律 tested-main 基準へ変えると、改稿予定の `test_land_rejects_child_green_runner_blob_divergence` は旧実装でも通る。

再現または根拠:

- 現 fixture は tip digest を作る: `orchestrator/tests/test_dev_wave_land.py:350-354`
- 旧 land も tip digest と照合する: `tools/dev_wave_land.py:1079-1082`
- divergence fixture は main と tip の runner が異なる: `orchestrator/tests/test_dev_wave_land.py:1519-1535`
- テストだけを変更し fixture を main digest にすると、旧 land は main/tip equality が無くても「main digest != tip content」で拒否する。期待値を拒否へ反転したテストはそのまま緑になる。

同じ masking は `test_land_runner_gate_uses_tested_main_after_main_reaches_tip` (`:1618-1636`) にも生じる。誤実装が `tested_main` でなく `locked_main` を引いても、digest 不一致による拒否が先に成立し、正しい revision 選択を証明できない。

影響: プランの中心負例が「変更前は赤、変更後は緑」を満たさず、main/tip equality や exact tested-main 束縛を実装しなくても通る。

scope 内か外か: scope 内。

推奨対応: fixture を一律変更せず、runner digest の基準 revision を引数化する。上記2テストでは旧 launcher 相当の tip digest を明示し、拒否理由を digest 不一致から独立させる。さらに `_runner_tree_entry` の revision 呼出しを spy し、`tested_main` と `tested_tip` の exact な組を確認する。

## 所見 2: v5 据置きは可能だが、過去 v5 の再検証経路が未処理

所見: `runner_executed_sha256` という field 名自体の意味は「実行 bytes の digest」のままであり、v5 据置きは整合可能である。一方、v5 verifier の受理集合は変わるため、過去 receipt の再検証について明示的な移行判断が要る。

再現または根拠:

- land は毎回 receipt を再検証する: `tools/dev_wave_land.py:5038-5046`
- その検証は active fold の recovery 分岐より前にある: `:5058` 以降
- `already-landed` でも receipt が必須であることを既存テストが固定する: `orchestrator/tests/test_dev_wave_land.py:1784-1797`
- 現在は child-green の runner divergence が受理される: `:1519-1535`
- 新 land は同じ v5 receipt を拒否するため、verifier 更新前後で同一 receipt の結果が変わる。
- tracked output 内で見つかった実 receipt は1件で、tested-main/tip の runner blob はともに `714b971b...` だった。実在する divergent receipt は今回確認していない。

据置きが誤りになる条件:

- schema version を JSON shape だけでなく検証方針の世代として扱う場合。
- 外部 consumer が「v5 は tip digest の検証」を契約として解釈する場合。
- 過去の child-green divergence receipt が active fold recovery や再 land に残っている場合。

逆に、root field と field 自体の意味を変えず、producer の exact `launcher_blob_sha` で実装世代を識別する契約なら v5 据置きは妥当である。新 launcher は main/tip equality 成立時しか発行しないため、新 receipt の digest は旧 land が見る tip digestとも数値上一致する。

影響: 過去に受理済みの divergent v5 receipt があると、already-landed の再実行が失敗し、active fold recovery は receipt 検査より先へ進めない可能性がある。これは「runner を編集する新しい wave が受入不能」という D838 の直接費用を超える。

scope 内か外か: 移行方針と回帰テストは scope 内。v6 と dual-reader の導入は現プランを広げるため追加裁定相当。

推奨対応: 保存済み v5 receipt を調査し、divergent receipt の有無を記録する。拒否を意図するなら、legacy divergent v5 の `already-landed` と active fold recovery の期待結果をテストと runbook に固定する。v6 は自己締め出しが必然ではなく、限定的な v5 migration reader を用意すれば回避できるため、「v6なら必ず自己締め出し」は根拠にしない。

## 所見 3: main 進行時に、runner を触っていない wave も一時的に拒否される

所見: 通常の main 進行は runner equality を壊さないが、claim 後に別 wave が runner 更新を land し、待ち手がその main を取り込む場合は、当該 runner を編集していない wave も受入前に拒否される。

再現または根拠:

- claim した main SHA は `tools/dev_wave_wait.py:2854-2861` で固定される。
- その後、待ち手は現在の main を merge/commit する: `:3633-3689`
- launcher へ渡る tested-main は claim 時 SHA、tested-tip は merge 後 HEAD: `:3746-3764`
- 新 launcher はこの2 revision の runner equality を要求するため、この間に main の runner が変われば不一致になる。

運用条件別の結果:

| 条件 | equality | D838 の費用範囲 |
|---|---|---|
| wave 自身が runner を変更 | 破れる | 明示受容済み |
| main に runner が無く tip で初追加 | main 読取で停止 | 明示費用の延長。bootstrap 不採用 |
| unrelated な main 進行 | runner blob が同じなら維持 | 新しい痛みなし |
| claim 後、merge 前に runner 更新が main へ land | 破れる | runner を触っていない wave の再受入が必要。明示費用を超える一時的痛み |
| receipt 後の clean forward-main merge | 検証は receipt の tested pair を使うため維持 | 過剰拒否なし |
| submodule 更新 | root の runner blobには影響しない | 過剰拒否なし |
| fold commit | fold 対象は docs で、runner blobは不変 | 過剰拒否なし |
| 複数 wave の並行 land | runner 更新 winner が上記 race を作る場合のみ破れる | loser 側の再起動・再受入が追加費用 |

影響: runner 更新の着地時に、無関係な稼働 wave が full acceptance を再実行する可能性がある。「当該 file を直す wave だけ」という説明より広い。

scope 内か外か: equality を緩めることは D838 外。運用説明と回帰テスト追加は scope 内。

推奨対応: trust-root epoch 更新時は稼働 wave の再起動・再受入が必要になり得ると runbook に明記する。claim 後の main mergeで runner が変わる負例と、unrelated main mergeなら通る正例を waiter integration test に追加する。

## 所見 4: テスト計画の静的な赤緑判定

所見: launcher の4新規テストと land の大半は旧実装で赤になるが、所見1の divergence テストだけは現プランどおりでは偽の緑になる。

再現または根拠:

| テスト | テストだけ追加した旧実装 |
|---|---|
| `test_matching_main_and_tip_runner_blobs_execute_tested_main_source` | reader 順を main, tip, main と assert すれば赤。旧実装は tip, tip |
| `test_main_tip_runner_blob_mismatch_is_rejected_before_execution` | 赤。旧実装は tip runner を起動する |
| `test_m3_runner_digest_mismatch_is_rejected` | 3回の revision/call 順と main 再取得 drift を固定すれば赤 |
| `test_missing_tested_main_runner_is_rejected_before_execution` | 赤。旧実装は main を読まない |
| `test_land_rejects_child_green_runner_blob_divergence` | fixture の一律 main digest変更により偽の緑 |
| `test_land_accepts_child_green_matching_main_and_tip_runner_blobs` | main lookup の spy assertion があれば赤。旧実装は child-green で main を引かない |
| `test_land_child_green_runner_path_absence_is_permanent_rejection` | プラン記載どおり tip digest を明示すれば赤。明示しないと偽の緑 |
| `test_land_child_green_runner_lookup_process_failure_is_retryable` | failure を tested-main lookupだけに限定すれば赤。tip lookupまで失敗させると旧実装でも拒否する |
| `test_land_rejects_non_attributable_runner_blob_divergence` | 既存の旧実装緑ではなく既存負例。共通化の変異検出用 |
| 改稿後の real waiter E2E | runnerをmainへ移せば旧実装でも新実装でも緑。互換正例であり実装差の検出テストではない |

また、matching positive は内容が同じ bytes だけでは「main由来 bufferを実行した」ことを証明しない。reader が返す同内容の別 object を用意し、`blob_runner` が main 側 object identity を受けたことまで見る必要がある。

影響: テスト名が主張する tested-main source の実行や exact revision 選択を、呼出し回数だけでは完全に固定できない。

scope 内か外か: scope 内。

推奨対応: fixture に revision 選択引数を追加し、digest・equality・lookup revision を互いに独立な assertion にする。実装差を検出しない E2E は「既存互換正例」と分類する。

## 所見 5: semantic consumer の実装取り残しは無いが、テスト consumer がプラン本文から落ちている

所見: exact field/path 検索では、production の receipt semantic consumer は launcher、wait、land の3 fileだけで、追加の実装編集面は見つからなかった。ただしテスト consumer と運用境界の列挙が不足している。

再現または根拠:

- `tools/dev_wave_wait.py:3001-3015` は launcher outcome の runner digest を読むが、値は `_runner_executed_sha256` として捨てる。
- `tools/wave_land_window.py:587-615` は land 結果の `status` と `main_after` だけを読むため変更不要。
- `tools/dev_waves/checker.py:69-73`、`cli.py:188-195`、`git_state.py:1051-1081` は runner path を trust-root/check path として使うだけ。
- hooks は `hooks/guard_bash.py:195` で path literal を admission に使うだけ。
- mutation 面は `tools/mutation_fanout_contract.py:35-41` と `tools/mutation_harness.py:761-796` で固定 HEAD runner identity を扱うだけ。
- 未列挙の receipt consumer は `orchestrator/tests/test_dev_wave_wait.py` と `test_resume_gate_acceptance_boundary.py:342-463`。後者は実 launcher を通す有効な matching 正例。
- `test_dev_wave_wait.py:226-302` の fake launcher は任意の `b"runner source"` digest から receipt を直接作るため、新しい main/tip equality の証拠にはならない。
- clean forward-main merge の既存正例 `test_receipt_survives_clean_forward_main_merge_chain` は `test_dev_wave_land.py:6607-6633` だが検証順に明記されていない。

影響: production の変更面は適切だが、waiter配線、forward merge、fold、submodule、並行 land の過剰拒否回帰が焦点 nodeid から漏れる可能性がある。

scope 内か外か: テスト選定は scope 内。`tools/dev_waves/`、hooks、mutation本体の変更は scope 外かつ不要。

推奨対応: waiter integration の main進行2条件、forward-main merge、既存 fold正例、既存 submodule正例を検証一覧へ明記する。

## 所見 6: 母集合の file 数は再現したが、hit 数が2箇所一致しない

所見: 39 file の母集合と除外 file 数は再現した。一方、plan の2つの hit 数は現 HEAD で再現しない。

再現または根拠: `git grep -n -F` と path分類を独立に実行した結果:

- `runner_executed_sha256`
  - code: 3 file / 13 hit。plan は 3 / 15
  - test: 4 / 13。plan と一致
  - docs: 2 / 5。plan と一致
- `resolved_runner_path`
  - code: 3 / 4、test: 3 / 9、docs: 0。すべて一致
- `tools/run_tests.py`
  - code: 12 / 22、test: 20 / 95。一致
  - docs: 7 / 103。plan は 7 / 105
  - `pytest.ini`: 1 hit。除外扱いは一致
- union母集合: code 12 + test 20 + docs 7 = 39 file。一致
- 除外 union: `output/**` 911、`docs/archive/**` 107、`docs/spool/**` 0。一致
- v5 literal は production code 3 fileだけだが、tracked 全体では test 3 file / 8 hit、docs 2 file / 3 hitもある。

影響: consumer の file集合は妥当だが、「独立再計算した exact hit 数」という証拠としては不整合が残る。

scope 内か外か: plan/docs 修正は scope 内。

推奨対応: code hitを13、docs path hitを103へ直し、使用した分類順と除外 pathspec を記録する。

## 所見 7: file:line は1箚所以外一致し、削除対象の兼用もない

所見: plan の参照位置はほぼ正確である。唯一の範囲ずれは waiter の tip束縛関数末尾である。

再現または根拠:

- `tools/acceptance_launcher.py:173-196`, `:425-446`, `:440-446`, `:347-398`, `:22`: 一致。
- `tools/dev_wave_land.py:1065-1067`, `:1073-1084`, `:1085-1113`, `:1089`, `:1106-1108`, `:1114-1133`, `:1126-1129`, `:834-835`, `:902-904`: 一致。
- `tools/dev_wave_wait.py:2521-2559`, `:3746-3764`: 一致。
- `tools/dev_wave_wait.py:2158-2234`: 関数の最終比較と閉じ括弧は `:2231-2237`。正しい全範囲は `:2158-2237`。
- launcher test `:83-112`, `:170-228`: 一致。
- land test `:350-354`, `:673-687`, `:1519-1535`, `:1538-1555`, `:1558-1582`, `:1585-1615`, `:1800-1881`, `:1813-1825`, `:1884-1981`: 一致。
- runbook `:879-900`, 特に `:881`, `:895-900`: 一致。
- decisions `:21650-21694` は D524、`:31681-31697` は D838で一致。

削除対象の `main_runner_entry` は `dev_wave_land.py:1089,1106-1108,1126-1129` だけで使われる。外へ移す際に削除してよい。`tip_runner_entry` は共通 digest検査 `:1079-1082` にも使われるため、変数自体は残す必要がある。枝内 `:1128` の重複 type検査だけの削除なら安全である。

影響: 実装位置の取り違えはない。waiter 範囲だけ末尾3行が資料から落ちている。

scope 内か外か: plan修正は scope 内。

推奨対応: waiter 範囲を `2158-2237` に直す。

## 所見 8: 親の実測は snapshot としては概ね正しいが、現在値や一般則ではない

所見: runner blob と初回追加履歴の実測は再現したが、`HEAD == main` は既に stale であり、hit件数にも上記不一致がある。

再現または根拠:

- 読取実測:
  - `HEAD = bb7753fa36daf7af4a47303858af573ecbeda4b0`
  - `main = a068b7f5f459b92868aeb1ad047095ba30a6fe4e`
  - 両 revision の runner は現在も `100755 blob b1b1b374dbd68bd3c7b5e8087b04db2fda5e9769`
- したがって `s3/plan.md:97` の blob equality は現在も成立するが、`HEAD == main == bb7753fa...` は現在値ではない。
- 初回追加 commit `af829260...` と親 `b03fb9d6...` は再現し、親への `git cat-file -e ...:tools/run_tests.py` は rc=128だった。よって「mainに存在しない歴史上の状態があった」は実証済み。
- この1点から言えるのは歴史上の不在だけであり、将来の bootstrap要否や現行 main 常在を一般保証するものではない。
- runner blob equality は特定2 revision の値であり、waiterが実際に claim・mergeして確定する tested pair の equality を事前には保証しない。plan自身の最終再実測方針は正しい。

影響: `HEAD == main` や一度の blob equality を受入投入時の証明として引用すると staleになる。親の「常在」根拠を撤回した修正は正しい。

scope 内か外か: 証拠表現の修正は scope 内。

推奨対応: SHA付き観測には観測時刻と「snapshot」を付け、最終確認は waiterが確定した tested-main/tested-tip、または発行 receipt に対して行う。

## 総括

- 最重大は、fixture の main digest一律変更が child-green divergence 負例を旧実装でも緑にする点である。
- 過去 v5 receipt は already-landed と active fold recovery で再検証され、同じ schemaでも結果が変わる。
- v5据置き自体は可能だが、legacy divergent receipt の移行方針と回帰テストが必要である。
- runner更新が claim後の main mergeへ入ると、runnerを編集していない並行 waveも再受入を要する。
- production semantic consumer の追加漏れは見つからなかったが、waiter/forward merge等の回帰選定が不足する。
- 母集合39 fileと除外911/107/0は一致し、code hit 15→13、docs hit 105→103は不一致だった。
- file:line は waiter の `2158-2234` を `2158-2237` に直す以外は一致する。
- テスト実走は行っておらず、赤緑判定はすべて静的検査である。