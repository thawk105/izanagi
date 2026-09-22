## 所見

対象 HEAD は `23acbfa60756e9460a66c9a018e8b6279c9a6fac` と一致。以下は静的レビュー結果であり、build・pytest・変異実走の結果ではない。

1. **must-fix — condition gate の証拠が build sink に到達したと既存検査が認定できない。**

   根拠: `orchestrator/campaign/silo_policy_coverage.py:334`〜348。gate 呼出しが `for macro in gate_macros` 内にあり、build はその外にある。既存解析は `orchestrator/tests/test_ccbench_spawn_sites.py:1988`〜2010 でループをゼロ回通る経路を残し、内部の gate 証拠を後続へ伝播しない。

   反例となる検査入力は、新規 `_build_variant` の AST そのもの。通常の `stock=False, macros=()` では実際の tuple に軸 macro が入るが、解析上は gate 未通過で348行の sink に到達する。C2 の自己申告と一致する。**実行時の gate 迂回を発見したという意味ではない。**

   影響: define/build-sink 交差検査を満たせず、登録追随と統合完了を主張できない。

   修正案: 必須 gate の呼出しと成功確認が sink を支配する構造に driver を変更する。検査の緩和や無条件の除外登録では解消しない。

2. **must-fix — prefix unlock の上限出口を独立に検証していない。**

   根拠: `patches/broken-silo-policy-no-prefix-unlock.patch:12`〜22 と41〜46は、上限出口と action-abort 出口の unlock を同時に削除する。一方、`orchestrator/campaign/silo_policy_coverage.py:67` は方策を `abort0` に固定し、211〜212行は timeout だけで成功判定する。段4裁定§3の `maxwait` の用途にある prefix unlock 変異への接続がない。

   反例: prefix を取得済みで次 tuple がロック中なら、`abort0` は最初の競合で action-abort 出口に入り、その漏れだけで timeout を起こせる。上限側の unlock を正常に戻した変異でも同じ結果になる。現在の成功結果から上限出口の検出力は導けない。

   影響: レポートが「両出口の prefix unlock を検証済み」と扱うと、実際の動的検証範囲を超える。

   修正案: 出口別の変異と対照に分け、上限側は `maxwait` 等で prefix 保持・上限到達を確認してから timeout を判定する。単一変異を維持する場合も、両出口を個別に検証したとは報告しない。

3. **must-fix — M-CHK-EMPTY は後段に隠され、事前登録どおりの単一理由変異にならない。**

   根拠: `orchestrator/campaign/silo_policy_coverage.py:242`〜257、`orchestrator/tests/test_silo_policy_coverage.py:77`〜89。必須集合の一致判定に加え、必須 case を参照する到達検査と `checks == derived` が残っている。

   反例:
   - 正常な全 `runs` と空の `checks`：集合判定を除去しても、`checks == derived` が偽になる。
   - 空の `runs` と空の `checks`：集合判定を常時真にすると、到達検査の `runs[c]` が `KeyError` になる。

   影響: 変異後も受理されない入力について、test の例外失敗を「空集合の誤受理を検出した KILLED」と誤集計しうる。DW-M01・DW-M03の証拠にならない。

   修正案: 冗長 gate と明記して単独変異の証拠から外すか、実効的な集計境界へ再照準する。複数箇所を変異するなら事前登録を更新し、誤受理まで変化することと失敗 node の完全集合を確認する。

4. **should — 成功通知後の状態継続について、観測機会の正の到達条件が不足している。**

   根拠: `patches/instr-silo-function-policy-probe.patch:126` は abort 時に commit 回数の下位3 bitを比較する。`orchestrator/campaign/silo_policy_coverage.py:161`〜176 は commit 数と比較回数がそれぞれ正であることを要求するが、**成功 commit 後に比較した回数**を要求しない。

   反例: worker の事象列が「競合・abort を複数回 → 成功 commit → 終了」なら、成功前の `0 == 0` の比較で `commit_match > 0` を満たし、終了時には `commits > 0` も満たせる。成功後の状態を次 txn から読んだ証拠はない。

   影響: `focus/focus:commit` 単体の緑を、成功通知後の状態継続の実証として過大評価できる。これは coverage 全体が必ず偽陽性になるという指摘ではない。

   修正案: 同一 worker で成功通知後に到達した観測を別計数し、その正の到達と符号の一致を要求する。

骨格では、周回先頭の上限・CAS失敗を含む計数・retry後の再読込・両abort出口のprefix unlockを確認した。`max_wset_`、absent出口、既存TRACEブロックは保存され、成功通知は `writePhase()` 後にある。wrapperの完全修飾、worker寿命の状態、64bitでのcycle換算にも、このレビューで修正必須の問題は見つからなかった。

受理検査器では、指定された字句・型・自己初期化・署名・呼出しDAGの規則を追ったが、**4段検査を通過する契約外の合法C++本文は今回発見していない**。単独TUの固定argvと指定環境変数の除去、timeout・compiler不在・例外からbuildへ進まない接続、検査本文とmaterialize本文の照合も確認した。

登録簿の既存entry・期待値を弱める変更は見当たらない。診断buildは `NON_ADMISSIBLE` のままである。probeは独自macroで制御され、`TRACE=0`だけでは消えないが、通常buildの局所的な不混入検査は存在する。その結果を環境一般の遮断保証へ拡張してはならない。

## 再発している失敗の型

- **[ドリフト]**: prefix unlock の方策・検証範囲が段4裁定からずれている。gate呼出しの形と既存sink解析の契約も未接続。
- **[恒真ゲート]**: 成功前の `0 == 0` が成功後の状態継続の証拠になりうる。またM-CHK-EMPTYは、対象判定を壊しても別判定が拒否を維持するF820型の過剰決定。
- **[捏造/幻覚]・[権限逸脱]**: 今回の差分・報告から再発を認定する根拠はない。未実走は各報告で区別されている。

## 変異の kill 点の単一理由性

| 変異 | 静的評価 |
|---|---|
| M-LEX | 二項の代替綴りを正規演算子へ写像してから拒否しており、拒否除去後に構文が残る形。適切。 |
| M-TYPE | bool算術fixtureは数値規則を狙っている。変異時に式全体の型がU32へ流れることを実走で確認する必要がある。 |
| M-SELFINIT | 宣言済みsymbolの自己参照拒否を狙える形。入れ子・helper版もある。 |
| M-RETURN | 全枝returnの末尾if等を使い、通常C++のreturn欠落と分離している。適切。 |
| M-ASSIGN | メンバ代入を部分式に置き、代入先自体は合法。狙いは適切。 |
| M-RHSLIT | `/=`・`%=`の変数右辺でliteral要求を狙っている。適切。 |
| M-TU-GLOBAL / M-TU-MACRO | `compile_policy`を直接呼ぶ負例なので、grammarの先行拒否で隠されない。 |
| M-CHK-EMPTY | **不成立。所見3の再照準が必要。** |
| M-CHK-NORW | 他条件を満たしてexit codeだけ2にする負例。適切。 |
| M-SMOKE-SKIP | `return true;`は直接TUで受理されることを確認してから実smoke入口へ渡す構成。適切。 |
| M-API-SYNC | 同長1byte変更をbyte比較だけで拒否する構成。適切。 |

以上は実走KILLEDの認定ではない。manifest横断testも同じfixtureを扱うため、失敗nodeは名指しの専用testだけに限定せず、実測した完全集合を登録する必要がある。

機構変異のhook解除では、固定戻り値への置換により複数の符号が失われる。C2の赤集合 `{abort, lock, commit}`／`{abort, lock}` は実装と整合するが、段4の「対応する照合だけが赤」という主張はそのまま維持できない。複数照合への波及を明記すべきである。no-limitを非検出対照とする扱いは適切。

## 総括

**NO-GO。静的レビューでのmust-fixは3件。**

1. gate証拠がbuild sinkを支配すると既存交差検査で確認できる形にする。
2. prefix unlockの上限出口を独立に検証する。
3. M-CHK-EMPTYの過剰決定を解消し、変異登録を再照準する。

成功通知後の観測到達条件も強化を推奨する。
骨格の直列化可能性条件の弱体化や、4段検査を通る契約外C++本文は今回発見していない。
統合焦点走・coverage/smoke・変異matrixの未実測分は、合格として扱っていない。