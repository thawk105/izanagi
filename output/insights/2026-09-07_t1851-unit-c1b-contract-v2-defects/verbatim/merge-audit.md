## 監査結果

1. [推測] **判定: 干渉なし。**

   - [実測] main 側の変更は `_parse_genesis` 内の29行だけで、`p3-8c-attempt-registry/v3` に同一の正の事前登録世代を要求し、8c の v1 / v2 に同 field があれば拒否する (`main-current.attempt_registry_core.py:733-761`)。
   - [実測] wave 側の v2 profile は別名の `s8b-floor-attempt-registry/v2` だけを読む (`orchestrator/campaign/s8b_attempt_profile.py:24,495-504`)。slot は Mapping ではなく `S8BV2AttemptSlot` へ正規化される (`orchestrator/campaign/s8b_attempt_profile.py:155-255`)。
   - [推測] schema 名が完全に異なるため、8b v2 genesis は main 側の v3 分岐にも legacy 8c 分岐にも入らず、新しい拒否経路へ誤投入されない。
   - [実測] wave 側の binding は3つの digest を保持する独立 codec である (`orchestrator/campaign/s8b_attempt_profile.py:258-348`)。terminal 検査は genesis 解析より後の lifecycle replay にあり (`orchestrator/campaign/attempt_registry_core.py:1332-1409`)、v2 の旧 writer も明示的に閉じている (`orchestrator/campaign/s8b_attempt_registry.py:2536-2658`)。main 側の追加はこれらへ触れていない。

2. [推測] **判定: 干渉なし。**

   - [実測] main 側は `_parse_genesis` の1 hunkだけを変更し、関数・定数を新設していない (`main-side.attempt_registry_core.py.diff:5-39`)。wave 側は同関数を変更せず、profile の既定値付き拡張、予算集計 replay、terminal validator、prefix proof 検査を別位置へ追加している (`orchestrator/campaign/attempt_registry_core.py:30-47,183-216,1074-1104,1402-1408,1455-1556`)。
   - [実測] wave 側の追加 field は keyword-only で、既定値は既存挙動を維持する `True` と `None` である (`orchestrator/campaign/attempt_registry_core.py:192-216`)。main の 8c profile は両 field を指定していない (`f2cca136a:orchestrator/campaign/trial_registry.py:2170-2202`)。
   - [実測] main 側が狭めるのは8c genesis の世代整合性 (`main-current.attempt_registry_core.py:733-761`)。wave 側が狭めるのは8b v2 terminal と次 attempt の許可条件 (`orchestrator/campaign/attempt_registry_core.py:1217-1221,1402-1408`; `orchestrator/campaign/s8b_attempt_profile.py:639-684`)。
   - [推測] 同じ関数、定数、schema、profile の受理集合を片方が広げ片方が狭める箇所はない。

3. [推測] **判定: 干渉なし。静的には相互に落とす test は見当たらない。**

   - [実測] main 側差分には新しい `test_` 関数定義は0件である。既存の `test_s8c_genesis_requires_manifest_contract_and_preserves_exact_row` を v3 と事前登録世代へ更新し、共用 helper `_s8c_slot` に同世代を追加している (`main-current.test_attempt_registry_core_s8b_profile.py:511-562,1547-1563`)。
   - [実測] main の8c slot parser は旧形と世代付き形の両方を正規化し、世代付きの場合は正の整数を要求する (`f2cca136a:orchestrator/campaign/trial_registry.py:1968-2023`)。更新後の test は正の同一世代を1 slotへ与えるため、main の genesis 検査条件を満たす。
   - [実測] wave 側は旧ファイル末尾へ18個の test 関数を追記している (`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2066-2558`)。そのうち8c profileを直接参照するのは `test_profile_extension_fields_are_keyword_only_and_preserve_legacy_defaults` で、追加 field の既定値だけを確認する (`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2219-2248`)。
   - [推測] main の既存8c test は wave の既定値付き拡張で変化せず、wave の8b v2 test は main の8c限定 schema 分岐を通らない。pytest は実行していない。

4. [推測] **判定: 干渉なし。**

   - [実測] main 側は `DW-O01` だけを編集し、起動前の引数検査と記述整理を行っている (`main-current.operations.md:6-17`)。
   - [実測] wave 側は `DW-O08` の初期化再試行手順 (`docs/dev-wave/operations.md:55-60`) と `DW-O26` の private symbol を含む consumer 探索 (`docs/dev-wave/operations.md:184-193`) を編集している。
   - [推測] 両側が編集した節は重ならず、起動前検査、初期化失敗への対応、関連 test 探索という意味も独立している。

5. [推測] **総合判定: 干渉なし。**

   - [実測] genesis は最初に各 profile の readable schema 集合で版を検査する (`orchestrator/campaign/attempt_registry_core.py:517-523`)。8b v2 の readable 集合は8b固有の1版だけである (`orchestrator/campaign/s8b_attempt_profile.py:495-504`)。
   - [実測] main の世代検査は正規化済み slot に対する8c固有の追加条件である (`main-current.attempt_registry_core.py:726-763`)。wave の terminal 検査は lifecycle の terminal 行に対する別段の条件である (`orchestrator/campaign/attempt_registry_core.py:1332-1409`)。
   - [推測] schema 識別子、適用 profile、処理段階の三点が分離され、既存 profile向けの追加 fieldにも互換な既定値があるため、意味上の合成は健全である。この結論は差分と現物の静的照合によるもので、無競合という事実には依存していない。

## merge message

```text
merge(main): f2cca136a の変更を T-1851 C1b ブランチへ取り込む

固定した main の変更一式を、T-1851 C1b の作業履歴を保ったまま取り込む。

両親が共に変更した3ファイルを意味単位で監査した。試行台帳の共通処理では、main側が加えた8c台帳先頭行の事前登録世代検査は8c固有の版だけを対象とし、wave側の8b v2台帳には適用されない。wave側が加えた試行位置の読み書き、束縛、予算集計、終了行の検査とも処理段階が分かれており、同じ受理条件を逆方向へ変更する重なりはない。

対応するテストでは、main側は既存の8cテストを新しい世代へ更新し、wave側はファイル末尾へ8b v2のテストを追加している。テスト関数の上書きはなく、8cで使われるwave側の追加設定には既存挙動を保つ既定値がある。

運用文書では、main側は子プロセスの起動手順、wave側は初期化の再試行手順と関連テストの探索手順を変更しており、同じ節の編集はない。

静的監査では3ファイルに意味上の干渉は見つからなかった。テストはこの監査では実行していない。

AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=xhigh; role=author; scope=t1851-c1b-acceptance-merge
AI-Agent: product=claude; model=claude-opus-5; reasoning=default; role=manager
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 総括

[推測] 両親の変更に意味上の干渉はない。  
[実測] 共通3ファイルでは適用 schema、処理段階、文書節が分離されている。  
[推測] 静的監査上は merge 可。pytest は未実行である。