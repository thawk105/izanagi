## 所見 (RA-1 …)

静的レビューと指定ログの照合結果です。編集・pytest・変異注入は行っていません。以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/` です。

**RA-1 — must-fix：再 launch は E3b を破り、親の「走査だけ」案でも同じ test は救えない。**

[C/s8b_oracle_driver.py:1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/campaign/s8b_oracle_driver.py:1532) は campaign-start 前に floor artifact を再捕捉します。両木の `test_v2_floor_disk_swap_after_launch_uses_same_validated_object` は、その再捕捉で `floor-artifact-invalid` になっています。s4 の指示には忠実ですが、既存契約とは衝突します。

親案の `search_repository(root, exempt_exact=...)` も **floor result を disk から読みます**。result は active-chain／selector の exact 免除に含まれません。test が書く置換 bytes は元の conjunction hit を消すため、親案では拒否理由が `closure-hit-mismatch` に変わるだけです。「artifact を構造検証し直さない」と「artifact の disk 内容を観測しない」は同じではありません。

走査だけの再検査が証明できるのは、過去に C2-4 を通った report と現在の hit 集合の一致です。floor／measurement artifact の hash、mode、occurrence、current contract、scan 後の bound artifact 再捕捉を再検証したことにはなりません。同じ path に同じ conjunction hit を残す内容変更は通り得ます。これは保持 object を使う設計とは整合し得ますが、**fresh full validation と同等とは書けません**。

- **成果物影響：** 従来 completed だった非委譲の v2 実行まで拒否し、意図した層2の受理拡大以外に oracle 実行集合を縮小しています。
- **fix 範囲：** `C/s8b_oracle_driver.py:run_block` で、receipt 再解決は維持し、委譲の鮮度義務と非委譲経路の object 再利用を分ける必要があります。特に `never-issued` は `verify_receipt` が scan 前に返す経路であり、委譲のための再走査を必要としません。
- **変更禁止：** disk-swap test の completed／object identity の期待値、走査除外、floor result の exact 免除追加。active-valid の floor 差替えにも E3b を無条件適用するなら、現在の disk 全走査との両立は未解決です。親案をそのまま実装して完了扱いにはできません。

**RA-2 — must-fix：接続8 node は機構に到達していない。**

`T/test_s8b_ratified_freeze.py:_make_emitter_build` は `compiler_input_rel = "fixture.txt"` を固定しています。新しい `receipt_root` 分岐は実 ccbench pin を保存し、`_make_fixed_ccbench` を呼ばないため、その file がありません。両木の8 node は同じ `FileNotFoundError` で停止しています。環境障害として除外できません。

- **成果物影響：** active v2＋実 receipt の受理、および発効・非層2拒否・campaign-start 境界を未検証のまま land することになります。
- **fix 範囲：** `T/test_s8b_ratified_freeze.py:_make_emitter_build / build_production_emitter_g1` と `T/test_s8b_oracle_driver.py:_build_t080_active_v2_repo` の test 入力配線。親の引数化案は妥当です。固定 pin の tracked regular file を指定し、実際に渡す source root の bytes から manifest hash を作ること。
- **変更禁止：** ccbench pin／履歴の作り直し、S の拡大、launch／receipt verifier の代役化、既存期待値の緩和。file 不在を直しても、その後の接続成功はまだ証明されません。

**RA-3 — must-fix：campaign-start の再検証失敗で receipt 再解決を省き、欠落時の epoch refusal を失う。**

`run_block` の再解決は再 launch の `else` 内です。したがって再 launch が失敗すると、campaign-start 境界の2回目の receipt 解決を行いません。

`test_t080_delegated_campaign_start_rechecks_receipt[missing]` は tracked receipt を unlink します。scanner は列挙済み path が file でないとして失敗するため、epoch 比較より先に `v2-execution: launch-validate:` へ入ります。author が報告した潜在失敗は現物から支持できます。現在は RA-2 がこれを覆っています。親の走査だけ案にも同じ問題が残ります。

- **成果物影響：** 欠落 receipt は拒否されますが、要求された再解決・epoch 拒否契約を満たさず、境界 test と変異受入が成立しません。
- **fix 範囲：** `C/s8b_oracle_driver.py:run_block`。鮮度検査の失敗を保持したうえで、失敗時にも token なしで receipt を再解決する。epoch が変われば既存 epoch refusal、変わらなければ鮮度拒否へ閉じるなど、既存1箇所の refusal return 内で優先順位を整合させること。
- **変更禁止：** `[missing]` の期待 prefix、2回契約、15 refusal-return pin、scan 失敗の受理化。

**RA-4 — must-fix：m8b は冗長検査に mask され、m2b の観測 test が確認できない。**

`C/t080_freeze_migration.py:_draft_reconstruct_holdout` の `search_assertion(report)` を除去しても、直後の実 `verifier(...)` は `s8b_holdout_freeze.verify_document` です。同関数は再走査して `_assert_search_pass(report)` を呼び、さらに per-holdout の非空 hit も拒否します。

したがって新 draft 負例は実機構を通していますが、**m8b の単独削除に対する kill 証拠にはなりません**。後段で別理由の赤になった場合も、受理変化の証拠には数えられません。

また、author は m2b の anchor を示していますが、指定 test 群には gate 通過後へ invalid resolution を入れて `_campaign_t080_value` の拒否を観測する具体的な境界 test を確認できませんでした。通常の invalid receipt は先行 gate が拒否します。

- **成果物影響：** 受理境界を弱める変異を検出した証拠がないまま、変異 matrix を完了扱いにするおそれがあります。
- **fix 範囲：** m8b は当該単独変異の受入証拠から外して理由を記録。m2b は `T/test_s8b_oracle_driver.py` の既存 driver seam を使い、対象境界へ到達する負例を補うこと。
- **変更禁止：** kill を作るための後段 verifier 削除、既存負例の stub 化、refusal 文言差だけの kill 認定。

**RA-5 — must-fix：chain 有り floor E2E の digest 不一致は残存する test 入力／期待モデルの不整合。**

親の原因分析は現物と一致します。`clean_scan_digest` は残存する世代文書を chain record として path＋sha256 に含めます。一方、`test_real_seal_protocol_to_floor_official_core_e2e` は `frozen_paths` だけで期待 digest を作っています。G 文書は宣言 S の外なので、削除 helper が残すのは仕様どおりです。

- **成果物影響：** chain 有り受入が赤のままで、T-2776 および後続 chain land の着地条件を満たしません。
- **fix 範囲：** 戻し先は `T/test_s8b_floor_campaign.py:_clone_committed_head_with_ccbench / test_real_seal_protocol_to_floor_official_core_e2e` の入力構成です。ただし、現在の「実 HEAD clone・削除は S のみ・既存期待値不変」をすべて固定したまま、この不一致を消す局所修正は確認できません。
- **変更禁止：** `C/s8b_floor_campaign.py:clean_scan_digest / _assert_freeze_allowlist` から chain record の hash 束縛を落とすこと、G を S に加えること、期待 digest を追随変更すること。親案の(a)(b)だけではこの残存赤は解消しません。

**RA-6 — must-fix：consumer 回帰に別の行番号追随漏れがある。**

`focus-nochain-2.log` は **1574 passed / 1 failed / 25 skipped** です。赤は `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` の `_BuildSink(..., lineno=1775)` に対する `KeyError`。同じ production `pipeline.evaluate` 呼出しは現 commit で1790行目です。更新済みの1803行 pin は別の `evaluate_fn` sink です。

- **成果物影響：** consumer 受入が停止します。これを除外すると define-interface coverage の確認を欠いた land になります。
- **fix 範囲：** `T/test_ccbench_spawn_sites.py:test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` の対象 sink 座標を同じ call へ追随すること。今後の production fix 後に位置を再確認する必要があります。
- **変更禁止：** `Counter({"covered": 38})`、`failures == []`、検査対象集合。座標追随と期待分類の変更を混同しないこと。

## 受理集合の差分 (現物)

| 境界 | 判定 |
|---|---|
| exact 型 | `type(...) is LaunchValidatedFreeze`。Reverified／subclass／duck 型を拒否 |
| root | token の `validation_root` と `Path(root).resolve()` を比較 |
| HEAD | outer activation／validation HEAD／実 HEAD の三重一致 |
| ratified HEAD | inner `ratified.activation_head` も validation HEAD と一致要求 |
| active 世代 | 再解決した HEAD・SHA・番号・導入 commit の4要素を比較 |
| 列挙 | token の `search_digest` と実 `_enumeration_digest(root)` を比較 |
| doc 束縛 | ratified doc に比較後、入力 holdout doc にも候補集合・ID・式・規約を比較 |

`except Exception: return None` は委譲を取り消す向きです。通常走査と `_assert_search_pass` が復活するため、例外を成功扱いにする分岐ではありません。token 不適格でも通常 zero-hit が通る入力は従来の受理集合です。

初回解決について、`gate_check` の全 return 分岐、`run_block` の loader／launch 失敗分岐は token なしで1回解決しています。v2 成功だけ token 付きです。v1 は token なし。`_t080_adapter_refusals` への転送追加はありません。`_gate_check_core` には従来の launch token 引数が残っていますが、adapter 委譲への転送を追加したものではありません。15 refusal return も維持されています。campaign-start 失敗時の例外は RA-3 のとおりです。

意図した追加受理は「実 full validation が成功した同一 root／HEAD／世代の report に限り、receipt 層2の zero-hit を C2-4 に委ねる」です。候補 artifact を新たな期待集合の authority にする変更はなく、規律6の逆転は見つかりません。

ただし全体の差分はこの受理拡大だけではありません。RA-1 の **非委譲 v2 に対する拒否増加**があります。また predicate 単体は同名 file の内容鮮度を証明しません。公開 API の token caller に残る義務を、名前集合一致だけで代替できません。

test 切り離しについては以下を確認しました。

- S は official namespace と候補 exact file から、hit 結果を使わず宣言されています。
- copy は候補の sibling を残し、clone は削除集合・親・残存 mode／OID を検査します。
- 接続 fixture の G／selector 初期材料調整は S と別で、s4 が指定した初期 commit 前の構成です。
- clean scan 3負例と draft 負例は実 report の投入 path の hit を確認します。
- `_run` の合成化後も opt-out 2関数／3 node が残り、active-valid observation の result／campaign-start WAL 伝搬と2回解決を検査します。
- 既存の hash drift、`bypass_drift_gate`、g7 exact refusal を緩める差分はありません。

commit は13 file、+623/−142。走査除外・hold・production allowlist・G／chain artifact bytes の変更は0 byteです。

## 変異の帰属表 (m0〜m11、実装後)

**正式な注入・kill 結果は未確認です。** 以下は anchor と観測経路の静的判定です。

| ID | 実装後の帰属 |
|---|---|
| m0-comment | helper comment の単独変更。SURVIVED 正例として妥当だが未観測 |
| m1-subset | C2-4 の `current != expected`。実 launch の reject→return を見る既存負例は適切。新 failed-launch test は接続障害で未到達 |
| m2a-ignore-receipt | `_make_gate_decision:allowed=not merged`。新 nonlayer2 test は allowed の変化を観測する設計で適切。ただし接続後に他 gate refusal がないことの確認が必要 |
| m2b-accept-invalid | `_campaign_t080_value`。先行 gate が mask する。対象境界を通る具体的 test が不足、RA-4 |
| m3-skip-zero-hit-without-token | `_verify_holdout_live_scan` の**後ろ側**の `if not delegated:` と `_assert_search_pass` が対象。走査取得側を消してはいけない。既存 single-defect は候補、新 unactivated test は未到達 |
| m4a-drop-expressions | 共通束縛 helper の比較削除。正常 token を残し入力 doc の式だけを変える test なので、履歴／bytes 比較に mask されない |
| m4b-drop-match-convention | m4a と同様。入力 doc の規約だけを変更する直接層2 test |
| m5-drop-campaign-start-recheck | 既存2要素 resolution test は driver 境界の候補。新 `[changed]` は実 receipt の候補。`[missing]` は先行 scan 失敗が mask するため単独証拠から外す |
| m6-drop-activation-head | outer token HEAD だけを変更する fixture は適切。置換後も `validation_head == _capture_head(root)` を残す。inner HEAD／世代比較は正常なので mask しない |
| m7-drop-enumeration-digest | namespace 外の通常 file 追加なので適切。active namespace dirty 検査は mask しない。driver の digest 比較とは別に helper を直接観測する |
| m8a-clean-scan-no-assert | 実 clean scan・正常 allowlist・実 hit 確認を通る3負例。author は直接呼出しで `DID NOT RAISE` を報告。正式 matrix の実測とは区別する |
| m8b-draft-no-assert | **単独証拠から外す。** 後段 `verify_document` の `_assert_search_pass` と非空 hit 拒否が残る |
| m9-drop-root-binding | 同 HEAD・同列挙の clone に対する最初の検査が独立した候補。追加 file 後の2回目は enumeration 比較に mask される |
| m10-drop-generation-recheck | 世代文書の namespace dirty を作る fixture。名前集合・token doc は不変なので、この helper 内では再解決が独立した拒否理由 |
| m11-stale-token-at-campaign-start | 既存 `late-hit.txt` を gate 後に内容交換するため、名前集合比較に mask されない設計。実 launch／receipt を使うが現在は fixture 構築で停止 |

m11 の親案への照準変更は「再 launch を gate token に置換」ではなく、**走査による鮮度確認だけを除去し、receipt 再解決・epoch 比較を残す**形になります。late-hit test の実 scan、`closure-hit-mismatch`、evaluate／WAL 未到達の期待は維持すべきです。先に baseline が実機構まで到達する必要があります。

## 焦点走の赤の帰属と fix 指示

| ログ | 実測集計 | FAILED の帰属 |
|---|---|---|
| `focus-nochain-1.log` | 1086 passed / 9 failed / 11 skipped | 接続 fixture 8、production 回帰1 |
| `focus-chain-1.log` | 1085 passed / 10 failed / 11 skipped | 共通9＋floor digest 不整合1 |
| `focus-nochain-2.log` | 1574 passed / 1 failed / 25 skipped | production 行移動に対する test 座標追随漏れ1 |

接続 fixture 起因の8 node は次のとおりです。

- `test_t080_active_v2_delegation_accepts_full_receipt`
- `test_t080_failed_launch_preserves_receipt_refusal`
- `test_t080_unactivated_chain_hit_is_invalid`
- `test_v1_gate_does_not_delegate_with_active_v2`
- `test_t080_active_v2_preserves_nonlayer2_receipt_refusal`
- `test_t080_delegated_campaign_start_rechecks_receipt[changed]`
- `test_t080_delegated_campaign_start_rechecks_receipt[missing]`
- `test_t080_delegated_campaign_start_rejects_late_hit`

修正先は RA-2 の emitter build 入力配線です。production 回帰1件は RA-1、chain 固有1件は RA-5、consumer 回帰1件は RA-6 に対応します。

`focus-nochain-2.log` 冒頭には bounded local の OOM と計算ノードへの再 dispatch があります。これは環境側の実行事象ですが、dispatch 後に列挙された `KeyError` を環境起因へ振り替える根拠にはなりません。**列挙された FAILED に、環境非帰属として除外できるものはありません。**

45 node 対照との FAILED 集合の照合は以下です。

| 区分 | 件数 | 内訳 |
|---|---:|---|
| 解消 | 44 | floor public preflight 4＋driver 40 が変更後 FAILED 集合から消失 |
| 残存 | 1 | `test_real_seal_protocol_to_floor_official_core_e2e`。現在の停止点は clean digest 比較 |
| 新規 | 9 | 接続8＋disk-swap1 |
| 別の consumer 走で判明 | 1 | T2155 production sink 座標 |

親の「44解消・1残存」という集合判定は一致します。ただし指定ログには全 node の個別 PASS 一覧がないため、独立に確認できるのは FAILED 集合からの消失と集計です。焦点走を受入全走として扱うこともできません。

## 総括

7条件、両 doc 束縛、通常検査への fallback、固定 S は現物上妥当です。author の「実装済み・未達」という報告も適切です。

着地を止める理由は、E3b との衝突、接続8 node の未到達、campaign-start 再解決の欠落経路、変異の帰属不足、chain 有り digest 不整合、consumer pin 漏れです。親の(a)は支持しますが、(b)の走査だけ案はそのままでは disk-swap と missing receipt の問題を解消しません。

NO-GO