## レンズ A

以下、`L` は `tools/codex_worker_launch.py`、`W` は `tools/dev_waves/worker.py`、`T` は `orchestrator/tests/test_codex_worker_launch.py` を指す。実走は行っておらず、probe の結果と静的導出を区別する。

### must-fix

**A1. worker の走査は launcher の依存先であり、「scope 外・列挙のみ」では consumer 閉包が閉じない。**

- **根拠:** brief:4、L:1782–1806、1845–1851。`_terminate_verified_group_observed` は W の `_verified_group_exists` と `_group_members` を使用する。W:146–178 は Z を含めて判定する。
- **成果物への影響:** 正常終了の N2 だけでは、F973 が実際に失敗した forced-stop 経路の観測表が欠落する。
- **是正案:** worker の実装変更は scope 外のまま、launcher が呼ぶ部分を検査対象へ含める。N2 に正常終了と `sigterm_ignore` 強制停止の二つの経路を設ける。

同一 PGID に Z が 1 本だけ残り、identity 検証と送信が成功する場合の導出は以下。正常終了側は、ほかの受理条件をすべて満たし、最大 attempt 数 1 とする。

| 経路 | 計数 | residual | termination_verified | accepted | launcher_rc | sidecar |
|---|---|---:|---|---|---:|---|
| 正常終了 | 現行 | 1 | false | false | 1 | final_count=1、停止信号なし |
| 正常終了 | Z 除外 | 0 | true | true | 0 | final_count=0、停止信号なし |
| `sigterm_ignore` 強制停止 | 現行 | 1 | false | false | 1 | final_count=1、停止信号・limit の記録 |
| 同上 | Z 除外 | 0 | true | false | 1 | final_count=0、停止信号・limit の記録 |

強制停止では L:1986–1987 の limit／終了コードが受理を阻む。したがって「Z 除外で accepted が true」は経路共通ではない。

また、L:1783／1798／1824 の検証失敗後に launcher の計数が 0 になると、**`(residual=0, termination_verified=false)` も成立する**。二つの field は同じ意味ではない。一方、正常な Z 残存だけでは worker の検証が必ず失敗するわけではなく、提示 probe も `_verified_group_exists=true` を示している。

**A2. N1/N2/N3 は代表例として妥当だが、三分類の識別能力を証明する集合にはなっていない。**

- **根拠:** D2044 項21、L:1718–1741、W:40、158–162、425–437。
- **成果物への影響:** 「現行なら実行中と回収不全を識別できる」「Z 除外だけが識別を失わせる」という過大な結論になりうる。
- **是正案:** 三語を相互排他的な process 分類とせず、代表的な負例と明記する。現行でも同数の S と Z は receipt の残存 field では区別できない。外部の PID/state 観測を真値として併記し、少なくとも混在例を加える。

コードから導ける境界は次のとおり。

| 状況 | 現行 | Z だけ除外 |
|---|---|---|
| 同一 PGID の生存子 1 本＋Z 1 本 | 2 | 1 |
| 同一 PGID の `T`／`t`／`D` | 数える | 数える |
| 同一 PGID の `X`／`x` が観測された場合 | 数える | 数える |
| 別 PGID へ移動した子孫 | 数えない | 数えない |
| `/proc` から不可視の process | 不可視自体を検知する分岐なし | 同左 |

`_CHILD_EXITED_STATES={"Z","X","x"}` は停止 handshake 用であり、群の残存計数には使われない。PID namespace 全般の保証は提示 probe から導けない。既存の setsid escape test（T:7360–7371）も、子孫全体の包含を保証しない契約を示す。

混在例は「実行中がいる」と「回収不全がある」が同時に成立する点で裁定材料になる。T/D/X の実 process 再現まで本 wave に要求する必要はない。

**A3. N3 は削除すべき重複ではない。ただし「読取不能の e2e」と呼ぶのは誤りで、単一条件の負例にする必要がある。**

- **根拠:** brief:7–8、T:3060–3095、3468–3478、L:3942–3953。
- **成果物への影響:** receipt 改変の拒否を、読取不能から receipt までの伝播実測として報告してしまう。また別条件で拒否されれば M3 の検査にならない。
- **是正案:** 正常な accepted receipt の **`process_group_residual` だけを `null` に変更**する。`termination_verified=true` その他を保ち、変更前の checker 成功と変更後の `attempt.accepted semantic binding` による拒否を確認する。「consumer 入力の合成負例」と明記する。

T:3060–3095 は複数の失敗条件を含む診断 helper の表示検査である。T:3478 は `failure_class` の拒否であり、residual の単独束縛とは重複しない。

読取不能の伝播については別の不足がある。L:606–608、701–707、2431–2433 により、一度 unknown を観測して最終的に 0 になると、`final_unknown_source` は消えるが `unknown_sources_seen` は sidecar に残る。receipt の residual は最終値だけである。T:5172–5192 は `[None,1,0]` の最終結果を検査するが、この診断履歴を検査しない。裁定表には **「最終 unknown」と「途中 unknown→最終0」** を分け、後者の履歴が sidecar にしかないことを示すべきである。

### should

**A4. transient Z のリスクはコード上あるが、「subreaper 無しでも負荷時に赤になった」は未実測である。**

- **根拠:** L:1752–1764、1864、1847、F973:8–16、probe:68–73。
- **成果物への影響:** 現行方式の負荷依存性について、観測済みの範囲を広げて裁定者へ伝えてしまう。
- **是正案:** 以下を分けて記載する。
  - poll 間隔は **0.01 秒**。0.5／1.0 秒は timeout。
  - 一度 Z を拾うだけでは失敗しない。その後 0 を観測すれば通る。期限到達時の走査でも残れば拒否する。
  - Z だけの残存なら Z 除外はこの待機原因を消す。
  - F973 が示す受入赤は subreaper 導入時。以前の受入44走緑は、subreaper 無しの失敗可能性を否定する証明ではない。
  - probe は leader 回収後に **50 ms 待ってから**走査している。短い transient 窓を観測する実験ではない。

brief:6 の「init が即回収」は「この1走では50 ms後に残存なし」へ弱める。init／既存祖先のどれが実際の回収者だったかも、この JSON には記録されていない。

## レンズ B

### must-fix

**B1. N2 は順序を固定すれば Z の保持を決定的にできるが、現 brief は保持期間と終了条件を定義していない。**

- **根拠:** brief:8、probe:60–73、88–98、T:1605–1606、1710。
- **成果物への影響:** 負荷下で正常終了 N2 が timeout の負例へ変わり、Z 除外後にも accepted が false のままになる。
- **是正案:** harness は prctl 成功後に launcher を起動し、fake は対象 PID の Z を確認してから正常終了する。harness は **launcher の receipt 封印・終了まで養子の Z を回収しない**。その後に回収する。launcher 自身を `wait` することと、`waitpid(-1, …)` で養子まで回収することは分ける。

この順序なら Z が保持されるため、0.5 秒窓そのものは不安定要因ではない。残るのは fake の起動・Z 確認までに wall limit が発火すること、無期限 poll、harness 異常終了である。正常終了用は既存の3秒設定を無批判に流用せず、有限の待機上限と、`limit_trigger is None`・終了コード0の前提検査を置く。

独立した harness process を subreaper にしても、同じ pytest worker の**兄弟 test の孤児**を引き取る祖先関係にはならない。pytest worker 自体へ prctl を設定する実装は避ける。なお、提示 probe は prctl の成功と引取り結果を示すが、fork 後の subreaper flag 非継承を読み戻す検査はない。「非継承を現物確認済み」とは報告できない。

**B2. teardown は成功経路だけでなく、変異で assertion が落ちる経路を所有しなければならない。**

- **根拠:** T:1389–1399、2409–2413、1719–1725、probe:82–98。
- **成果物への影響:** 変異の kill 自体が process を残し、後続の受入結果や残存数の観測を汚す。
- **是正案:** 起動直後から `try/finally` で所有し、N1 は PID・identity を登録して TERM 無視の設定完了を確認、finally で対象を KILL する。N2 は launcher 終了後に養子を `waitpid` で回収し、回収完了を確認して harness を終了する。launcher timeout・receipt 不在・期待 rc 不一致でも同じ後始末へ入れる。

`_run_case` は期待 rc の検査で戻る前に失敗しうるため、戻り値取得後だけに finally を置いては足りない。`_assert_pid_gone` は **待つだけで kill／reap しない**。3秒は受入負荷下での保証ではなく、回収しない親が残れば延長しても直らない。48 worker 全走では取り残しが重なるので、cleanup 完了の証拠を負例結果と別に持つ必要がある。

**B3. M1 の test failure と consumer の観測表作成を分離しないと、変異後の結果を取り逃がす。**

- **根拠:** brief:9、T:1719–1725、L:1868、1991–1992、3949–3950。
- **成果物への影響:** 「N2 が赤になった」という記録だけが残り、どの consumer がどう変わったか、どの変異行が kill されたかを説明できない。
- **是正案:** assertion より先に receipt・sidecar・外部 PID/state を収集し、次の単独変異を別々に評価する。

| 変異 | 帰属できる検査 |
|---|---|
| M1: Z 除外 | 保持中の Z を外部確認した N2 で residual 1→0 を直接確認。正常終了／強制停止の帰結を別記 |
| M2: `_normal_reap` の verified を常に true | residual が非0のまま `termination_verified=false` を直接検査 |
| M3: checker の residual 束縛削除 | A3 の「null だけ変更した accepted receipt」が変異後に通ることを確認 |

M2 は accepted の検査だけでは kill できない。L:1991 の residual 条件が残るためである。既存 T:4627–4644 の unknown residual test も M2 を kill するので、「新規 N1/N2 だけが検出した」とは記録しない。

起動 path は T:31–32 の `Path(__file__).resolve().parents[2]` から決まり、`run` は T:1643、checker は T:2426 の `_LAUNCHER` を使う。**pytest 内の `LAUNCHER` への monkeypatch は subprocess に伝播しない。** 変異した worktree の test を起動するか、同じ解決先ファイルを一時変異する必要がある。`repo_root` 引数の変更だけでは launcher は切り替わらない。変異対象の実 path・差分・復元を記録する。

### should

**B4. Z-only 変異は一つの案の代理としては妥当だが、「ゾンビ除外案」全体の代理にはならない。**

- **根拠:** brief:9–11、L:1718–1741、W:40、D464、D705。
- **成果物への影響:** consumer の識別能力を保持できる別案まで、Z-only の結果から否定してしまう。
- **是正案:** 変異は構文長の確認後、PGID 判定・加算へ到達する有効な stat に対して適用する。壊れた stat の処理まで変えた結果を Z 除外へ帰属させない。

裁定パッケージでは、少なくとも次を区別する。

- 在籍数の契約を維持する。
- Z だけを残存数から除外し、回収不全の情報を失う。
- 非Z残存数と Z 数を分けて記録し、どちらを受理条件へ結ぶか別途決める。

`Z/X/x` を除外する案も Z-only とは別物であり、候補注記に置ける。ただし W の定数は、その採用根拠にはならない。

D464 は「生存者による排他」、D705 は「cwd の占有」という別契約の参考例である。特に D705 は **非占有扱いでも zombie 件数を保持する**先例として有用。「本件の採用根拠ではない」と「裁定者の参考にも載せない」は区別する。

### nit

**B5. 行番号と前提の表現を整える。**

- **根拠:** brief:4、6–7、L:701、W:146、probe-result-login.jsonl。
- **成果物への影響:** 結論自体は変わらないが、追跡時の誤読を招く。
- **是正案:** `residual_observation` は L:701、W の `_group_members` は bool ではなく tuple。`hidepid` がないことだけで実 process の読取失敗全般が不可能とは言わず、「本 probe では再現していない」とする。「subreaper 下でだけ決定的に作れる」も、この harness で採用する再現手段という記述に留める。

## 総括

brief は修正が必要。最優先は **正常終了と強制停止の分離、worker 依存の検査対象化、N3 の単一条件化、失敗時 teardown、変異後の観測値回収**である。

N1/N2/N3 は削除せず維持する。追加する価値があるのは、同じ N2 の強制停止経路、実行中＋Z の混在、途中 unknown の診断履歴である。広範な state／namespace 再現は本 wave の必須実装にしない。

現時点で支持できる結論は、**Z-only 除外は正常終了の Z-only 残存を受理へ変えうるが、強制停止では残存値が変わっても不受理が続く。現行 receipt も生存子と Z を直接識別していない**、までである。除外採否は、この限界を明記した観測表とともにユーザー裁定へ返す。