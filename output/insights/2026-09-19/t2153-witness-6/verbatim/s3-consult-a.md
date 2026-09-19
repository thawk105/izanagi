## 総括

**P1 は実測を条件に進められます。P2 は shared build root 化による受理拡大を先に検証すべきです。P3 の不採用は維持できますが、「既存機構では不可能」という説明は成立しません。**

指定資料、gate・test、対象 patch、4 driver、実 patched TU、親の `pre-*.stdout.jsonl` を静的に確認しました。pytest・compiler・probe は実行していません。

### 1. REPORT の登録前後比較が正常入力だけでは、規律2を証明できない

**［real／scope 内／must-fix］** 実行形が変わる経路は確認済みです。実入力での受理反転は未実測です。

[G:1892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/condition_meaning_gate.py:1892) は登録簿会員であることを理由に、REPORT の supply 対照を別 build root から要求側と同じ root へ変更します。宣言を渡さない呼出しにも及びます。

静的に構成できる反例候補は、REPORT の初回 configure 値から補助値を `CACHE` に保存し、その値を別の compile define にする CMake です。

- 登録前：要求 root では補助値1、既定 root では0となり、supply は `compile-command-drift`。
- 登録後：要求値1で初期化した cache が既定 configure に残り、補助値は両方1。REPORT 自体の供給・枝選択が正常なら、旧拒否を失う可能性がある。

plan の「同じ正常入力で登録前後を比較」だけでは、この経路を攻撃していません。**cache 履歴依存の拒否対照を事前登録し、旧 red → 新 admit が出たら REPORT を保留する**条件が必要です。機構修正は本 wave の実装として紛れ込ませず、裁定パッケージへ回してください。

**放置時の影響：旧 supply が拒否した入力を新 family が受理し、REPORT を未確立一覧から除去する経路が残ります。**

### 2. P2 と P3 は「複合式かどうか」で区別できない

**［real／scope 内／must-fix］**

D1490 の限定された主張なら、両者は同じ基準で評価できます。

| 宣言式 | 他方の固定条件 | 試験 macro による枝選択 |
|---|---|---|
| `A && REPORT` | `A=1` | REPORT に依存 |
| `IMPL == 1 || WFG` | WFG=0 | IMPL に依存 |
| 同上 | IMPL=0 | WFG に依存 |

[G:2937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/condition_meaning_gate.py:2937) が要求するのは**宣言した逐語の一意性**です。他の異なる条件式の存在を禁止していません。したがって SS2PL の複合行は観測候補になり得ます。意味 arm に dependency closure の比較がない、という親の読みも正しいです。

P3 の妥当な不採用理由は、次の区別です。

- **観測能力：** `currentAttempt()` を囲む特定枝の選択は観測可能。
- **採用範囲：** その枝を SS2PL macro の代表として採る判断は今回行わない。
- **consumer：** 現行 supply 拒否を meaning green で救済できない。

REPORT についても、証明するのは companion 条件下の footer 枝選択だけです。footer の実行、出力内容、RUNG1 本体の意味まで確立したとは書けません。

**放置時の影響：6件の判定台帳が「観測可能だが採用しない」を「機構上不可能」と誤分類し、後続の裁定対象を変えます。**

### 3. REPORT の companion 保証は公開 driver に限定される

**［real／scope 内／must-fix］**

`_effective_companions` は空の request からも spec の `RUNG1=1` を補完し、gate 自身が再注入します。したがって gate の green は、別に行われる実 build に RUNG1 があった証明ではありません。

一方、公開 driver については反証材料があります。

- liveness の gate と実 build はともに `[RUNG_MACRO, REPORT_MACRO]` を指定。
- [silo_ladder_rung1.py:2380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/silo_ladder_rung1.py:2380) は実 compile argv を検査。
- `validate_compile_argv` は RUNG1 と REPORT の各1回の供給を要求。

よって「公開成果物経路で欠落を防ぐ」という説明は支持できます。ただし **factory／CLI 全体の保証へ一般化できません**。登録追加だけで CLI にも REPORT witness が発行されます。

追加すべき対照は、gate の注入条件を操作するものだけでなく、**実 liveness compile argv から RUNG1 を落とすと成果物作成が拒否されること**です。

**放置時の影響：gate の条件付き green が、実 build の供給証明としてレポートや台帳に過大転記されます。**

### 4. 変異候補には拒否理由の競合が残る

**［real／scope 内／must-fix］**

plan の各候補は次のように事前登録してください。理由名は以下では接頭辞を省略しています。

| 候補 | 帰属上の条件・問題 |
|---|---|
| SORT 直前の `#undef` | `#undef` **より前**に値参照を置き、supply green を実測して初めて meaning の `not-discriminating` に帰属できる。 |
| REPORT owner 内の companion `#undef` | footer が両値で消え、supply も bytes identical になり得る。独立した REPORT 値参照で supply 差を残す必要がある。 |
| compile argv の companion 除去 | supply も拒否し得る。meaning 単独の `companion-define-mismatch` 対照として扱う。 |
| 登録 directive だけ反転 | source と一致しないので `start-not-unique`。期待極性検査の対照ではない。 |
| source と shadow 登録を同時反転 | `selection-mismatch` 候補。**宣言 object だけ**反転すると factory 不一致で `unestablished` になる。 |
| driver の宣言を `None` に戻す | 他の全 supply・meaning が拒否しない入力が必要。正常版 reject → 変異版 admit を確認する。 |
| tuple 順序変更 | pin の対照。受理集合の変異には数えない。 |

特に REPORT driver は BACKOFF_FIXED と RUNG1 も評価します。REPORT 以外の赤が残れば、宣言を外しても driver は拒否し、配線 assert が実質発火していないことを見逃します。

承認外の過剰拒否を検出する正例も必要です。

- REPORT の正しい複合枝＋両 argv の RUNG1=1。
- SORT の実構造にある `#else`、および活動中の外側条件を持つ正例。
- 枝本文の変更だけでは witness が赤にならない正例。
- REPORT の意味確立後も、他 macro の未確立項目が残る正例。
- 新2件の非対値は factory が `None` のまま、という境界。family admit まで一律に期待しない。

なお現行の非対値テストは PERMUTATION 固定なので、新2件へ**明示的なパラメータ追加**が必要です。

**放置時の影響：変異台帳が別層による拒否を新 witness の防御として数え、配線欠落による受理拡大や過剰拒否を見逃します。**

### 5. 親の実測値は支持できるが、official／計算ノードへの一般化は未成立

**［判定不能／scope 内／must-fix］**

確認できた範囲では、親の supply 結果と directive 件数は一致しています。KIND に所有 TU 内の対象 directive がないことも一致します。ただし「KIND はどこにも指令がない」は誤りで、patch の `wfg.cc` にあります。

一方、既存 SORT receipt の configure argv には SOURCE_DIR 3本がありますが、**`FETCHCONTENT_BASE_DIR` はありません**。これは official helper の同形供給 cell ではありません。

[s8b_floor_campaign.py:3480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/s8b_floor_campaign.py:3480) から S1 への引数到達は追えます。しかし独立 meaning build での `config.h` 可用性、今回の新 owner／条件式での計算ノード同等性は、過去の S2 bytes 一致からは導けません。

必要なのは plan が予定する exact な official 同形 cell と、採用後の production evaluator／consumer record です。計算ノード再走を省くなら、結果の適用範囲を今回観測した環境に限定してください。

**放置時の影響：official sort_best が環境要因で拒否される可能性を残したまま、台帳には未確立縮小・official 対応済みと記録されます。**

「output/ に SORT gate record がない」は **［判定不能／scope 内／nit］** です。探索対象、形式、ignored／外部成果物、権威ある manifest の範囲が示されておらず、権威閉包にはなりません。本確認でも SORT を含む JSON／JSONL は存在しますが、それだけでは gate record の存在証明にもなりません。

**影響：検索結果を全成果物の不在証明に昇格させると、履歴・参照閉包の記述が不正確になります。**

### 6. 旧宣言経路と shadow 分離への攻撃は、設計上は反証された

**［refuted／scope 内／nit］**

- 旧 `MeaningWitnessDeclaration` は BACKOFF_FIXED 固定。
- CLI の `--meaning-case` も他 macro を拒否。
- factory 不一致の枝宣言は green にならず `unestablished`。
- companion の空指定は補完され、異値指定は拒否される。

登録追加だけで D1491 の旧数値復号経路が広がる根拠はありません。

段5 probe も、固有 module 名、同一 shadow module 内の object、許可追加だけの bytes 照合、production 認証への非流用という設計は妥当です。ただし probe 本体は未確認です。**shadow green を登録候補の診断に使う段階と、採用後の production record を得る段階を分ける**必要があります。

**影響：設計どおりなら旧経路の受理集合・正準 module 参照は不変です。shadow record を production record の代わりに使えば、認証の参照先が変わります。**

scope 外へ返す候補は、shared-root 反例が成立した場合の機構対応、SS2PL の代表枝採用方針・patch 改訂・owner 拡張です。S2 固定値変更も含め、本 wave で実装済みとは扱えません。