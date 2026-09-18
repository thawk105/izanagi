## 所見 (B-1 …)

指定資料は読めた。以下は静的検査と Git 読取りの結果であり、編集・pytest・fixture 構築は行っていない。両木の緑は未確認。

**B-1 — must-fix／plan：統合 fixture は、既存 builder の後ろへ emitter を足すだけでは成立しない。**

具体的な障害が二つある。

- chain 有り木では `_copy_git_visible_output` が既存 `holdout_freeze.v2.g1.json` を複製する。plan の削除集合 S はこのファイルを残す。これが T-080 basis commit に入り、emitter が別 bytes の g1 を同じ path に発行すると、`s8b_ratified_freeze._immutable_introductions` の全履歴検査が `history-mutated` を返す。後から削除しても直らない。
- 両木とも既存 `selector_predictions.json` と selector journal を複製する。`_install_emitter_selector_prediction` は predictions が存在すると即 return する。新規 init した T-080 repo に元の `pre_oracle_head` の履歴は無く、実 launch の selector 祖先検査を満たさない。

**放置時の影響：接続正例が fixture 構築・load・launch の段階で赤になり、A-3 の着地証拠を作れない。**

**B-2 — must-fix／plan：memo 登録簿変更には、名指しされた二つの配線テストの追随が必要。**

`test_real_repo_serialization.py` の次の二本は、削除予定の `test_success_wal_order_budget_and_evaluate_contract` を consumer として固定している。

- `test_receipt_memo_prewarm_wiring_is_controller_only_and_lazy`：4963 付近。
- `test_receipt_memo_real_xdist_order_has_no_worker_payer`：5485 付近の生成テスト名。

前者は prewarm 呼出し期待、後者は controller prewarm の実 xdist 観測が成立しなくなる。残存 consumer の具体名へ置き換え、削除した consumer だけを選ぶ対照は prewarm 不発火として残す。

**放置時の影響：6 file の焦点走が緑でも serialization を含む通常受入が赤になる。**

**B-3 — should／plan：consumer 数の削減は、全走の receipt prewarm 費用を除去しない。**

残る driftguard の memo 機構テスト二本は非 held で、登録簿にも残る。したがって通常全走でも selected-consumer 条件が成立する。テスト本体が fake verifier を使うことと、collection barrier が先に実 receipt を prewarm することは別である。

**放置時の影響：29 node の切り離しを根拠に5分達成を予測すると、直列 prewarm 費用を取り落とす。**

**B-4 — should／plan・brief P3：初回解決維持より、launch 判定後の一回解決を推奨する。**

成功時は委譲付きで一回、失敗時は委譲なしで一回解決し、各 refusal return へ必ず渡す。campaign-start 前の再解決は維持する。これは初回の全検証一回を節約し、既存の成功時 `call_count == 2` と epoch drift の二要素列を維持できる。

**放置時の影響：正常な issued receipt 経路で不要な全走査・履歴検査が一回増え、oracle gate 到達が遅くなる。**

**B-5 — should／plan：T-2776 の完了条件を「両木受入全走」へ広げない。**

台帳の T-2776 原文は floor 二経路、削除差分、三負例、既存対照、変異実証、**両木の焦点走**を要求する。oracle 40 node は当初その scope 外であり、今回同じ wave に同梱された別の変更面である。

**放置時の影響：chain 有り scratch の全走まで必須と誤読すると、本 wave の land と T-2776 完了を不要に止める。**

**B-6 — nit／brief・plan：opt-out は「2 node」ではなく2関数／3 node。**

observation 伝播テストは `[False, True]` の二例、epoch drift は一例。既定の合成化で active-valid の WAL 契約が消えるという疑いは、この opt-out を維持する限り反証できる。

**放置時の影響：実装の可否は変わらないが、実行件数と被覆報告が不正確になる。**

**B-7 — nit／plan・brief：runbook の条件文と未実測状態を分ける。**

A/X 後の条件付き判定規則を書くこと自体は §6 と矛盾しない。「production 未実測」という可変状態や将来の結果欄を runbook に置く必要はない。未実測の事実は worklog／insight に記録する。

**放置時の影響：コードの緑は変わらないが、runbook が手順と状態の二重正本になる。**

## 正例 fixture の実現可能性と代替

**production の要求同士に、同じ repo では絶対に両立しない矛盾は確認できなかった。一方、現行二 fixture の合成手順には B-1 の確定した障害がある。**

| 材料 | T-080 側の要求 | emitter／v2 側の要求 | 判定 |
|---|---|---|---|
| ccbench | basis の gitlink は known_axes の legacy pin。current 検査も hold 解除時はその pin | 現行 emitter は独自の小さい ccbench を作り、その pin を protocol に入れる | 独自 submodule 作成を使わず、既存 pin を protocol に渡す必要 |
| known_axes／holdout | 固定 artifact bytes、basis blob、source closure の分類を維持 | v1 bytes を継承し、known_axes の hash を維持 | 両立可能 |
| design／generator | receipt の closure は migration basis の blob を参照 | G の親にある blob と g1 の hash が一致 | basis と G の親は同じ commit でなくてよい |
| selector | output 複製で実 repo の文書が入る | 合成 repo 内に実在する祖先、source blob、protocol／journal 束縛が必要 | 現行 no-op は使用不可 |
| calibration／protocol | receipt の固定履歴を壊さない | calibration、固定 source、selector seal と整合する protocol が必要 | 追加材料として構成可能だが未実証 |
| certificate／run_dir | receipt 発行前は実 zero-hit を通す | clean preflight → certificate commit C → official artifact → G | R 後に C/G を作る順序は整合 |
| `frozen_at_head` | receipt は独立した migration basis を記録 | `G^ == frozen_at_head` | `basis → R → … → C → G → A → X` で両立 |
| g1 履歴 | chain 木からの複製で basis に既存 g1 が入る | 同じ generation path は全履歴で不変 | **現行複製結果の上書きは不可能** |

最小の修正方針は、既存45 node 用の削除集合 S を拡張せず、**新しい接続正例の初期材料を最初の commit 前に確定すること**である。T-080 に必要な basis／artifact／source を保持し、g1 をまだ導入していない履歴と、その repo 自身に束縛した selector 材料を作る。既存 g1 を commit 後に撤去する案では履歴検査を通らない。

また、既存 selector 文書を上書きするだけでなく、対応する journal・source pin・protocol・`pre_oracle_head` を一組として構成する必要がある。`_prepare_emitter_base` の repo 初期化と `_make_fixed_ccbench` を再実行するのは不適切。

接続が間に合わない場合の最小の分離は次のとおり。

- 実 emitter の load／launch token で、委譲 predicate、root／HEAD／世代／列挙／doc 束縛の正負境界を検査する。
- stub-free T-080 fixture で、receipt 履歴・静的検査・非層2 refusal の維持を検査する。
- driver の既存注入 seam で、token 転送、失敗時の refusal 集約、campaign-start 再検査、WAL observation を検査する。

これで各責務の境界は示せる。しかし、**発行済み receipt と実 v2 launch を接続して active-valid へ到達した証拠にはならない**。接続障害が実際に見つかっている以上、分離テストだけで A-3 の全体同等性を確認済みとするのは不適切で、plan の着地条件を満たしたとは報告できない。

費用は未実測。plan の base 20〜60秒、clone 検査1〜10秒を保証する根拠は無い。既存コメントの15〜22秒は旧構築条件の記録であり、統合 emitter 全体の測定値ではない。例えば plan の数字をそのまま使っても、base 一回＋10境界で **30〜160秒**の予算を消費する。再構築、worker ごとの重複、残存 prewarm を加えると300秒以内とは結論できない。共有 base は完成後に clone し、clone ごとに root に束縛された token を取り直す必要がある。

## memo consumer と floor clone の検算

AST を読取り専用で集計した結果は次のとおり。

| 集合 | 関数 | parameter 展開後 node |
|---|---:|---:|
| `_run` 経由の通常 consumer | 23 | 26 |
| driver の直接 memo consumer | 7 | 7 |
| driftguard の直接 consumer | 4 | 4 |
| 現登録簿合計 | 34 | 37 |
| 削除予定：通常 `_run`＋直接3関数 | 26 | 29 |
| 残存 | 8 | 8 |
| 別集合の opt-out | 2 | 3 |

残る8関数は plan の列挙どおり。

- driver：`test_real_freeze_gate_lists_floor_and_budget_null`
- driver：`test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`
- driver：`test_nonnull_floor_without_active_generation_is_refused`
- driver：`test_active_resolution_and_manifest_structure_refusals_are_aggregated`
- driftguard：`test_run_block_broken_binding_manifest_refuses_and_writes_nothing`
- driftguard：`test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal`
- driftguard：`test_receipt_memo_delegates_to_production_verifier_exactly_once`
- driftguard：`test_receipt_memo_patches_the_driver_module_the_tests_import`

serialization の導出は `elif run_calls or direct` を変えない限り旧集合を数える。直接 memo 呼出しを数える形へ追随し、opt-out 検出は独立して維持する。

`memo_barrier_probe` は golden から代表を選ぶため、新集合に自然に追随する。一方、B-2 の二本は literal の追随が必要。残存8のうち先頭6は growth hold に登録されているが、最後の2本は非 held。全走の実 prewarm は残る。

active-valid の耐久 observation は、`test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result[True]` が result と campaign-start の双方で明示検査する。これを opt-out のまま残せば、通常 `_run` の never-issued 化によってその契約は失われない。ただし「委譲された実 receipt の observation」まで実証するには新接続正例が必要である。

floor は二経路への適用が必要で、plan の訂正は正しい。履歴 assertion は次の三段を分離する。

1. source HEAD を捕捉する。
2. gitlink 修正 commit の親が source HEAD、diff が `external/ccbench` 一件であることを検査する。
3. S が非空なら削除 commit の親と `D` 集合、残存 tree の mode／OID を検査する。空なら HEAD 不変。

既存の post-seal protocol 削除 commit の assertion は、その直前の HEAD を親として引き続き検査する。単純な `HEAD^^` への変更ではない。

`git ls-tree` による S の検算結果：

- `HEAD=24ede1d11`：空。
- `229982652`：同一 official run_dir の `journal.jsonl`、`launch_certificate.json`、`manifest.json`、`result.json`、`result.md` の5件。
- candidate exact file：両者とも無し。
- g1：chain 木に存在し、S には含めない。

新負例の配置は次に固定できる。

- official：`output/env/pegasus/calibration/s8b-floor-official/synthetic-chain/result.json`
- candidate：`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`

両方とも scan の prefix 除外外。通常ファイルとして Git-visible にし、`_holdout_hit_text` の合成 bytes を置く。`output/s8b-freeze/holdout_freeze.v2.g1.json` に置くと prefix 除外されるため、目的の負例にならない。

`_CHAIN_RECORD_PATTERNS` は freeze namespace の被覆・hash 記録用で、official／candidate の scan 免除ではない。残した g1 はこの既存規則で被覆されるので、それ自体は harmless 対照の blocker にならない。ただし `clean_scan_digest(root, freeze_allowlist={})` では既存固定ファイルが undeclared になる。既存 fixed／selector scope と必要な selected protocol の正しい allowlist を使うことが必要。「無害 bytes で通る」は静的には成立可能だが、未実行なので成功済みとは言えない。

## P3' の費用対効果

**P3' を推奨する。ただし launch 失敗時にも receipt を解決し、既存 refusal 集約を保持する実装に限る。**

| 正常 issued receipt 経路 | plan | P3' |
|---|---:|---:|
| gate 到達までの receipt 全検証 | 2回 | 1回 |
| campaign-start までの receipt 全検証 | 3回 | 2回 |
| full scan：gate／campaign-start | 2回／2回 | 1回／1回 |
| 成功時 count pin | 2→3へ変更 | 2を維持 |
| drift side effect | `[initial, initial, changed]` 等へ変更 | `[initial, changed]` を維持 |

P3' は失敗分岐ごとの解決漏れに注意が必要だが、新しい拒否 return を増やす必要はない。現在の15 refusal-return を保ったまま各 factory へ resolution を渡せる。

費用を `R=receipt 全検証`、`L=full launch`、`D=委譲付き receipt 再検証` とすると、

- plan の gate 到達：`R + L + D`
- P3' の gate 到達：`L + D`
- campaign-start 前は双方にさらに `D`

差は初回 `R` 一回。G wave の407秒を同条件の参考値として当てれば、**約407秒分を節約するシナリオ**になる。407秒を scan 単体とは置けず、計算ノードや合成 repo の所要へも転用できない。plan の `D` には receipt 履歴検査と追加の世代再解決・列挙が残り、ゼロ費用ではない。

したがって「407×3秒」と断定するのも、「scan を保持済みだから十分安い」とするのも根拠不足。分解計測すべきなのは receipt 履歴・静的検査、通常 scan、v2 launch、委譲 predicate の世代再解決である。

## chain 有り木で残る赤の予測表

標準の growth hold を適用する全走と、held node を明示実行する場合を分ける。

| 集合 | 修正後の予測 | 根拠・限界 |
|---|---|---|
| 既知45 node＝T-080構築10＋floor5＋memo29＋g7の1 | 両木で緑になるべき | S、合成 resolution、exact refusal 維持が条件。未実測 |
| 新しい統合 active-valid 正例 | 現 plan の単純接続では赤 | B-1 の既存 g1 履歴と selector 祖先参照 |
| serialization の literal consumer 二本 | 追随漏れなら両木で赤 | B-2 |
| validated 型の直接構築7箇所 | field 追随漏れなら両木で赤 | constructor 引数不足 |
| driver sink の1788行 pin | 行番号追随漏れなら両木で赤 | 同じ evaluate sink を再確認して追随 |
| 残存 driver memo 4関数 | 標準全走では held。解除実行では赤を予測 | receipt が invalid、既存 exact refusal／active-valid 期待と不一致 |
| driftguard の実 binding 2関数 | 標準全走では held | 解除時の成否は各 assertion に依存。一括で赤と断定しない |
| driftguard の memo 機構2関数 | 緑を予測、ただし prewarm 費用は残る | 本体は fake verifier による配線検査 |
| 実 repo scan invariant、8c の wave-files scan | held。解除時は既知 hit で赤 | 既裁定どおり |
| `test_s8c_preregistration_invariant` の非 held node | chain hit 起因の赤は特定できず | 関数名 pin、文書、合成 repo、legacy schema 等。全件赤とする根拠なし |
| その他の実 root consumer | 未確定 | 45件のログは全走の網羅証拠ではない |

受入設計は、変更面と consumer の追加焦点走、両木の既定6 file 焦点走、**chain 無し land 木の通常受入全走**とする。chain 有り全走をこの wave の必須条件へ追加しない。後続 G wave は X2 を含む実際の land 木で別途受入する。

追加探索では、直接 constructor 7箇所以外に `dataclasses.replace`／`replace` の token 派生を確認した。driver の5922・5956、gate-core test の205付近などで、既存 token から追加 field を継承するため、field 追加だけによる引数不足は起きない。追加の kwargs 展開 constructor や当該 dataclass の field 数 pin は確認できなかった。

root-only verifier seam は driftguard の `fake_verify(*, root)` に実在する。token なし resolver 呼出しは既存の `verify_receipt(root=...)` を維持すれば通る。driver の v1 count pin は一回のまま。return 数の AST pin と official perf closure の呼出し pin は存在するが、新 return や既存呼出しの移動を避ければ数を緩める必要はない。driver の追加の数値行 pin、runbook 旧文の literal pin は検索範囲では見つからなかった。

## brief と plan の食い違い

P1〜P5 のうち、plan が訂正した以下は現物と整合する。

- P1：列挙 digest は root identity を証明しない。
- P2：report 保持なら production は3 file。
- P3：初回 receipt 解決は全走査を含む。
- P4：29 node は登録簿全体ではなく、その部分集合。
- P5：指定 chain commit に X2 は無い。

追加訂正は、B-1 の統合 fixture 障害と B-6 の opt-out 件数。brief の floor アンカーも、1経路5 node ではなく二経路である。candidate の「exact path」に directory を書いた箇所は、単一 JSON path に直す必要がある。

main の状態も更新されている。本読取り時点では `main=302b94796`、作業 HEAD は `24ede1d11`。plan の `386fc515c` は当時の観測として扱う。現 main 差分には t2613 の production／test が含まれる。今回の予定編集 file との直接交差は見つからなかったが、「file が交差しない」は統合後の受入不要を意味しない。t2627 の未 commit 編集状態まで確認したとは主張できない。

runbook の推奨文は、未測定の将来結果を表へ置く形ではなく、次の判定規則でよい。

> active v2 を使用するときは当該世代ファイルを指定する。同一 root・HEAD・世代の full launch validation が成功した場合に限り、receipt の未知性層2を委譲する。その他の拒否条件は独立に評価し、gate が拒否した場合は次段へ進まない。v1 指定では委譲しない。

chain 無しの2件、chain＋G・A/X前の4件は、観測した固定木とログへ結び付けて記載する。A/X 後の production 実測が無い事実は worklog／insight に残す。

T-2776 は、台帳原文の floor 二経路、宣言 S の独立差分検査、既存対照、三負例、search 拒否除去変異、両木焦点走が揃えば完了判定できる。同 wave 全体の land には、別途 A-3 の境界実証と chain 無し受入緑が必要。T-2724 全体の完了にはしない。

## 総括

**plan の方向は維持できるが、そのまま author へ渡すには B-1 と B-2 の具体化が必要。** 特に接続 fixture は、既存 g1 と selector 履歴を初期 commit に持ち込む問題を先に解くべきである。

P3' は検査を省略せず、成功経路の重複 receipt 解決を一回減らせるため推奨する。34／37→8／8は正しいが、全走の prewarm 一回は残る。両木の焦点緑、chain 無し受入緑、production の A/X 後 oracle 到達は、それぞれ別の未実証事項として扱う。