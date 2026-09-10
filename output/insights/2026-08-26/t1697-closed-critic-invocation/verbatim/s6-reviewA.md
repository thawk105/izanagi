採用不可です。静的検査だけで、certified receipt の自己認証、pair 封印の迂回、snapshot の論理的不整合、5 件の無効な変異事前登録を確認しました。こちらでは pytest を実走していません。

`docs/failures.md` の F9、F28、F255、F366、F536、F564 にある「恒真ゲート」「consumer 取り残し」「説明と実装の食い違い」が再現しています。

## 所見

### 1. [must-fix] A1: certified trust root を呼び手が選べる

- **(a) 何が壊れるか** — `runner is subprocess.run` でも、caller 指定の偽 executable が compliant envelope を出せば certified receipt になる。さらに `_CERTIFIED_RUNNER` と `REPOSITORY_ROOT` は書換可能な module global で、同一 process から equality 自体を差し替えられる。
- **(b) 根拠** — `p3_b4_closed_critic.py:61-66,91,450-459,769-780`、`claude_projected_provider.py:146-155`。試験も certified factory に `sys.executable` を渡して受理している (`test_p3_b4_closed_critic.py:415-426`)。
- **(c) 最小是正案** — certified factory から `repository_root`、`evidence_class`、`runner`、`executable` を除き、注入可能 factory を test-only 名で分離する。certified executable は事前承認済み絶対 path/hash と照合する。
- **(d) 成果物影響** — 偽 CLI の block が certified 候補へ入り、材料レポートと試行台帳が偽の成功 receipt を参照する。

### 2. [must-fix] A1/A5/A13: pair gate は receipt の自己申告を certified として受理する

- **(a) 何が壊れるか** — receipt dataclass は自由に構築・`replace` でき、pair gate は `evidence_class=="certified"` という文字列しか出自確認しない。`status`、schema、tool evidence、identity gate、start receipt hash も検証しない。
- **(b) 根拠** — `p3_b4_closed_critic.py:147-184,833-878`。試験自身が test-only receipt を `replace(..., evidence_class="certified")` して通す (`test_p3_b4_closed_critic.py:484-505,691-703`)。
- **(c) 最小是正案** — terminal receipt bytes を読む verifier を唯一の pair 入力にし、start/payload/envelope/argv hash と全 success 不変条件を再計算する。単なる dataclass を certified authority にしない。
- **(d) 成果物影響** — `status="failure"`、tool evidence=false、捏造 hash の receipt でも certified 受理集合へ入る。

### 3. [must-fix] A2: frozen なのは binding の値であって controller の arm 束縛ではない

- **(a) 何が壊れるか** — `_ArmBinding` は frozen だが、controller は通常 class で `__dict__` を持つため、`_B4ClosedCriticController__binding` を別の frozen instance へ再代入できる。`__evidence_class` も同様に変更可能。
- **(b) 根拠** — `p3_b4_closed_critic.py:201-205,523-549`。試験は invoke signature と公開 `arm` 属性の不在しか見ない (`test_p3_b4_closed_critic.py:444-464`)。
- **(c) 最小是正案** — controller 内属性を認証境界にしない。生成時 commitment を terminal verifier が外部の pair admission と再照合する。少なくとも再代入負例を追加し、文書保証を public API 範囲へ縮小する。
- **(d) 成果物影響** — receipt の arm/campaign/digest が生成時設定と異なる block を on/off 標本として登録できる。

### 4. [must-fix] A3: seal は外から取得でき、別 factory の receipt も混成できる

- **(a) 何が壊れるか** — `_PAIR_SEAL` は import 可能で、公開 controller constructor に渡せる。また receipt に `pair_id` が無いため、pair-1 の on と pair-2 の off が pair gate を通る。共有 tracker の使用も receipt から検証不能。
- **(b) 根拠** — `p3_b4_closed_critic.py:90,526-560,738-830,833-871`。
- **(c) 最小是正案** — factory ごとの pair commitment を両 receipt に焼き、verifier で equality を要求する。tracker/factory admission も同 commitment に含め、module object を seal として使わない。
- **(d) 成果物影響** — 異なる時点・provider 集合の on/off が同一 block として比較され、pair の hash 参照が混成する。

### 5. [must-fix] A4: WAL と loop state の論理的 snapshot 束縛が無い

- **(a) 何が壊れるか** — byte が読取中に不変でも、進んだ WAL と一世代古い `loop_state.json` は受理される。実 venue は iteration 実行後に loop state を保存するため、その間の crash でこの安定した不整合が実在する。
- **(b) 根拠** — `p3_b4_closed_critic.py:479-514,617-624` は各 file の byte equality と whiteboard/state iteration しか検査しない。writer 順序は `p3_s4_loop.py:1240-1243`。
- **(c) 最小是正案** — loop state に admitted WAL prefix hashまたは snapshot epochを保存し、controller が exact equality を要求する。単なる二重読取を同一 snapshot の証明にしない。
- **(d) 成果物影響** — 最新 digest と旧 coarse result の組合せが成功 receipt となり、停止理由と次 synthesis の帰属がずれる。

### 6. [must-fix] A5: argv evidence は事後再検証できない

- **(a) 何が壊れるか** — receipt は argv の hash だけを持つが、canonical argv bytes を保存しない。argv に含まれるランダムな neutral MCP path は `close()` で削除されるため、後から再構成不能。
- **(b) 根拠** — argv 構築は `claude_projected_provider.py:220-241`、削除は同 `246-257`、hash 化だけが `p3_b4_closed_critic.py:672-678`。
- **(c) 最小是正案** — invocation ごとの canonical argv と inline-agent config を exclusive artifact として保存し、その path/hash を receipt に載せる。
- **(d) 成果物影響** — 試行台帳が持つ argv 参照を consumer が再検証できず、certified 選択の輸送条件を監査できない。

### 7. [must-fix] A6: literal manifest は裁定列挙を満たすが semantic closure ではない

- **(a) 何が壊れるか** — admission、canonicalizer、neutral-root writer、session tracker など、payloadまたは閉鎖挙動を変える直接依存が manifest 外。同じ projection hash で別挙動が成立する。
- **(b) 根拠** — manifest は `p3_b4_closed_critic.py:424-443` の6項だけ。一方直接 import は同 `35-55`、provider 側も `claude_projected_provider.py:28-45` にある。
- **(c) 最小是正案** — 少なくとも `artifact_admission.py`、`s8b_prediction_runner.py`、`role_session_isolation.py` と identity renderer の実依存を追加するか、projection 部分を小さい versioned module へ抽出する。
- **(d) 成果物影響** — 意味の違う block が同じ `projection_sha256` 群へ併合され、効果量と比較可能性が壊れる。

### 8. [must-fix] A7: path view に偽陰性、escape view に偽陽性がある

- **(a) 何が壊れるか** — 引用された path に除去可能な空白 componentを入れた `.../x y/../izanagi` は単一の lexical path だが、regex が空白で分断して正規化できない。一方、JSON decode 済み leaf 中の文字どおりの `\uXXXX` も再度 decode するため、単なる説明文を拒否しうる。
- **(b) 根拠** — `_PATH_TOKEN_RE` は `p3_b4_closed_critic.py:89`、二重 decode は `304-314`、token normalization は `331-338`。
- **(c) 最小是正案** — JSON string leaf 全体を引用符込みの path tokenizer で扱い、残存 escape の扱いを明文化する。空白 alias と「escape を説明するだけ」の正負対を追加する。
- **(d) 成果物影響** — 前者は identity 開示 block を受理し、後者は正当な digest を受理集合から落とす。
- 補足: `_unshadowed_literal_present` (`341-368`) 単体では最長 literal が残るため baseline の全拒否を失わないが、短い identity の診断を抑制し、変異位置によっては mask を作る。

### 9. [must-fix] A9: create は排他的だが terminal receipt の必須性は保証しない

- **(a) 何が壊れるか** — terminal file の open 成功後に write/fsync が失敗すると部分 file が残り、failure handler の二度目の `O_EXCL` は必ず既存 file で失敗する。start receipt 書込みも `try` の外で、失敗すると terminal は作られない。
- **(b) 根拠** — `p3_b4_closed_critic.py:228-243,595-600,691-735`。親 directory の fsync も無い。
- **(c) 最小是正案** — invocation directoryを排他予約し、terminal slotを query 前に確保した append-only state遷移にする。storage failureまで保証できないなら、その限界を非保証として明記する。
- **(d) 成果物影響** — 失敗 query が台帳から欠落または部分 receipt になり、片アーム再試行と予算集計が曖昧になる。

### 10. [must-fix] A13: tool-surface 負例は3条件を同時に壊しており、後二つを検査していない

- **(a) 何が壊れるか** — `num_turns=2` が最初に拒否されるため、`permission_denials` と `server_tool_use` の検査を削除しても現テストは成功する。F150/F422 型の恒真な負例。
- **(b) 根拠** — combined fixture は `test_p3_b4_closed_critic.py:770-794`。provider の検査順は `claude_projected_provider.py:304-344`。
- **(c) 最小是正案** — 3 field を1件ずつ、それ以外は正常値にした負例へ分割し、exact reasonと terminal failureを固定する。combined 対照は裁定どおり別に残す。
- **(d) 成果物影響** — 後二 gate の退行が無検出となり、tool event のある block が certified 候補へ入る。

### 11. A12と表示契約が未充足

- **(a) 何が壊れるか** — module docstring の「seals」と「same stable snapshot」は所見3〜5より過大。能力面の非保証が receipt/docs に無い。一方 `identity_non_guarantees` の4分類自体は裁定と一致しており、そこは過大でも過小でもない。
- **(b) 根拠** — `p3_b4_closed_critic.py:2-13,92-95`。brief の成果物影響も裁定指定文へ未更新 (`brief.md:78-82` 対 `adjudication.md:144-174`)。
- **(c) 最小是正案** — mechanics を直すまで docstring を「route-local candidate」に縮小し、unreported/local tool use を証明しない field を追加する。brief は「本 wave では三成果物の値は不変」に更新する。
- **(d) 成果物影響** — 現時点の実値は未配線なので不変だが、材料レポートの参照説明が実装以上の証明を主張する。

### 12. [must-fix] 変異5件が単一理由でない

- **(a) 何が壊れるか** — M6/M7/M8/M9/M11 は、後段 pair gate、前段 tracker/factory、構築側 exact schema、別 view に mask される。現在の node が赤くなっても受理集合の実効 kill ではない。
- **(b) 根拠** — M6 `p3_b4_closed_critic.py:462-469,842-843`、M7 `claude_projected_provider.py:346-377`、M8 `p3_b4_closed_critic.py:822-825`、M9 同 `285-301`、M11 同 `403-408`。
- **(c) 最小是正案** — 5件を登録から外し、公開 invocation の受理集合が変わる実効点へ再照準する。M11 は decoded leaves を正規化 viewにも渡す共通点を同時に変えなければならない。
- **(d) 成果物影響** — mutation 台帳が偽の KILLED 証拠を持ち、certified 選択が実効性未証明の gate を根拠にする。

## A1〜A13 照合

|契約|静的判定|要点|
|---|---|---|
|A1|不充足|caller executable、mutable trust globals、自己申告 receipt。所見1・2。|
|A2|不充足|binding value は frozen だが controller の参照を再代入可能。所見3。|
|A3|不充足|seal取得可能、pair commitmentなし、tracker共有を再検証不能。所見4。|
|A4|不充足|byte stabilityのみでWAL/stateの論理世代を結ばない。所見5。|
|A5|一部のみ|claim名分離、payload/envelope hashはあるがargv再検証不能で、receipt出自も未検証。|
|A6|名目充足、実効不充足|裁定列挙6項はあるが直接依存closureが欠落。|
|A7|一部のみ|3 viewと非保証名はあるが、path tokenizerに偽陰性。|
|A8|充足|exact 5-key parserで返すだけ。LoopState/proposal foldは新moduleに無い (`p3_b4_closed_critic.py:255-274,625-701`)。|
|A9|不充足|`O_EXCL` は実装済みだがvalid terminalの必須性が破れる。|
|A10|機構のみ充足|CLIは存在しdriver未配線 (`p3_b4_closed_critic.py:881-908`)。ただしA1欠陥によりcertified入口としては不採用。|
|A11|判定不能|対象の `test_p3_s4_loop.py` は今回の必読射影に含まれていない。|
|A12|不充足|brief未更新、module表示が過大。prereg/runbook本体は射影外。|
|A13|一部のみ|provider検査はあるが独立負例なし。実CLI負の対照は親の後続作業で、ここでは実走確認なし。|

## M1〜M15 照合

「静的KILL」は現テストが赤になるとのコード上の判定であり、実走結果ではありません。

|変異|判定|単一理由性|
|---|---|---|
|M1|静的KILL|あり。campaign_id kindを除けば当該fixtureを他literalは拒否しない。|
|M2|静的KILL|あり。repository root kindだけの負例。|
|M3|静的KILL|あり。test fixtureのpathはcampaign_id/repo rootを含まない。|
|M4|静的KILL|あり。factory前のroot equalityだけが当該呼出しを拒否。|
|M5|静的KILL|あり。ただし別入力である偽executableは生存する。|
|M6|テストは赤、登録無効|後段のreceipt arm順序検査も swapped pairを拒否する。|
|M7|テストは赤、登録無効|実invocationでは共有trackerが先にsession再利用を拒否。testはreceiptを後加工。|
|M8|テストは赤、登録無効|両identity再利用はfactoryも拒否。testはfactory後にreceiptを後加工。|
|M9|テストは赤、登録無効|controller projectorがexact 2-keyを構築するため、extra-keyは実経路から到達しない。|
|M10|静的KILL|あり。raw critic responseのextra keyを機械的に拒否する唯一のparser。|
|M11|診断だけ静的KILL、登録無効|normalized viewも`decoded_leaves`を使うため拒否は残り、`checked_view` assertionだけが変わる。|
|M12|静的KILL|あり。`..` aliasはraw/decoded viewにexact rootを持たない。|
|M13|静的KILL|あり。receipt schemaのfield存在検査。|
|M14|静的KILL|あり。terminal writeのno-opに対するfile/status検査。|
|M15|静的KILL|field存在については単一。ただしclosure完全性そのものは所見7で未証明。|

## 総括

must-fix は所見1〜10と12です。最優先は、certified receipt の自己認証を廃止すること、certified executableをcallerから切り離すこと、pair commitmentとWAL/state cross-linkを追加することです。その後にA7/A9と変異登録を直す必要があります。

現状の実装は採用してはいけません。A10により正式driverへ未配線なので既存のcertified選択・材料レポート・試行台帳の実値はまだ変わりませんが、このままB-4に使用すると偽または混成されたreceiptをcertifiedとして受理できます。