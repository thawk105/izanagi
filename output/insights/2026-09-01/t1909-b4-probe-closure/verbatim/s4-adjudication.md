# 段 4 裁定 — [T-1909] / D1195

## 結論

**実装する。** 段 2 と lens B は「残差なし」、lens A は「残差あり」で割れた。親が一次資料と
コードを直接読んで実測した結果、**lens A が正しい**。ただし lens A の所見のうち、生成が
実際に逃げる経路は 1 件だけであり、残りは成果物の文言の過大表現である。

## 親が自分で実測したこと

1. **反射性は 3 権威点のうち 2 点しか検査されていない。**
   `orchestrator/tests/test_p3_b4_wiring_probe.py:296-320` の 2 本は
   `assert target in baseline` で seed 自身の在籍を拘束するが、
   第一権威点を扱う `同:285-294` は下流の `pipeline.evaluate` しか見ておらず、
   `require_certified_writer_authorization` 自身が遮断目録に在ることを一度も assert しない。
   `同:323-335` の期待集合にも 3 権威点は入らず、`同:1071` は
   `len(generation_seeds) == 3` すなわち証拠 field の要素数しか見ない。
   → **第一権威点を遮断目録から落とす変異は現行検査を生存する。** 生成が実際に逃げる。
2. **`_build_inventory` は閉包に入った symbol の issue しか検査しない。**
   `orchestrator/campaign/p3_b4_wiring_probe.py:1140-1150` は先に `reasons` を作り、
   その中の symbol についてだけ unresolved binding を拒否する。解析集合の内側で
   binding を静的解決できない caller は、実際に seed へ到達していても閉包へ入らず、
   検査もされない。
   → ただし **profile hook は目録該当 code の call で発火し、権威点自身も目録に入る**
   (`同:1107-1111` が seed を `reasons` へ反射的に入れる)。したがって未解決 caller が
   動的に seed を呼んでも seed の入口で遮断される。**生成は逃げない。逃げるのは文言である。**
3. **`test_static_preflight_covers_exact_runtime_import_closure` は恒真である。**
   `同:1183-1187` が `preflight` の各 name を import して `runtime.modules` を作るので、
   `set(runtime.modules) == set(static)` は構成上必ず成立する
   (`orchestrator/tests/test_p3_b4_wiring_probe.py:152-154`)。
   D1171 が却下した「自分で定義した集合との一致にすぎず恒真」が検査名に再発している。
4. **凍結 pin は無い (DW-O09)。** `p3_b4_wiring_probe` を参照する `.py` は全件 22 行で、
   probe 自身と test 以外に無い。`t1769-dogfood` を参照する `.py` は全件 0 行。
   `generation_scope` を含む file は全件 5 本 (probe、test、着地済み dogfood JSON 3 本)。
   着地済み JSON は再生成しないので、凍結成果物の bytes は変わらない。

## 所見の real / refuted と採否

|所見|判定|採否|理由|
|---|---|---|---|
|lens A 5 (反射性の検出穴)|**real**|**採用・must-fix**|放置すると第一権威点を目録から落とす回帰が検出されず、§5.1 (ii) 証拠の受理集合が壊れる。規律 2。|
|lens A 2 (未解決 caller が閉包外へ落ちる)|**real**|**採用 (文言)**|生成は seed 入口で遮断される。過大なのは `generation_scope` の文言。D1195 は「範囲を明示した主張は訂正で済む」と書く。文言を実際の導出へ狭める。|
|lens A 4 (恒真な runtime closure 検査)|**real**|**採用 (文言)**|検査名と主張を「preflight mapping と import 対象の一致」へ狭める。挙動は変えない。|
|lens A 6 (閉包が閉じたと読める文言)|**real**|**採用**|上の 2・4 の修正と、事前登録 §10 の除外列挙の 1 行追記で閉じる。|
|lens A 1・3・7|**real だが含意**|不採用 (独立には)|所見 2・5 の修正に含まれる。|
|lens B 5 (後発 producer が解析集合外)|**refuted (残差ではない)**|不採用|明記済み除外「解析 module 外」の内側。D1195 の完全性非主張の範囲。|
|lens B 3 (台帳の重複持ち越し)|**real**|**採用**|T-1909 は残差を実装したうえで閉じる。重複だから閉じるのではない。|
|段 2 (残差なし)|**refuted**|—|反射性の穴を見落とした。|

## plan v2 (実装面 = Codex author、D95)

1. `orchestrator/tests/test_p3_b4_wiring_probe.py:285-294`
   `test_anchor_seed_alone_load_bears_pipeline_evaluate` を、他 2 本の seed 検査と同形にする。
   第一権威点自身が baseline 目録に在ること、seed 除去後に落ちることを assert に足す。
   既存の `pipeline.evaluate` の assert は残す。
2. `orchestrator/tests/test_p3_b4_wiring_probe.py:152`
   検査名と本文の主張を、実際に検査している内容 (preflight mapping と import 対象の一致) へ狭める。
   assert は変えない。
3. `orchestrator/campaign/p3_b4_wiring_probe.py:2109-2116`
   `generation_scope` を「静的に解決できた call edge に限る」形へ狭め、
   `generation_scope_exclusion` へ「解析集合の内側でも binding を静的解決できない caller」を足す。
   既存 test が pin する部分文字列 `outside the exact analyzed set` は残す。
4. `orchestrator/campaign/p3_b4_wiring_probe.py:4-11`
   module docstring を 3 と同じ範囲へ狭める。

親 (docs) が行う:

5. `docs/phase3-b4-reflux-ablation-preregistration.md` §10 の
   「遮断集合は生成器の完全目録ではない」の項へ、同じ除外を 1 行足す。

**やらないこと。** 新しい gate・検査・台帳・一般化を作らない。遮断機構の挙動を変えない。
未解決 caller を fail-closed にする案 (lens A の直し方 A) は採らない — 受理集合を縮め、
D1195 が選べと書いた「範囲を明示した主張」より重い。事前登録 §5 の欄は 1 つも埋めない。

## 変異事前登録 (DW-M01 / DW-M08)

本 wave は**テスト強化を含む**ので、DW-M08 に従い MW-A は**新旧両走**する。

|ID|位置|変異|期待|
|---|---|---|---|
|MW-A|`p3_b4_wiring_probe.py` `_build_inventory` の `for symbol in sorted(reasons):` 直後|第一権威点 `_GENERATION_SEEDS[0]` を目録から落とす|**修正後 = KILLED** / **変更前 HEAD = SURVIVED**。新テストだけが検出する差分を示す|
|MW-B|同上|第二権威点 `save_loop_state` を目録から落とす|KILLED (既存検査の正例。harness と node 抽出が効くことの対照)|
|MW-C|同上|第三権威点 `project_whiteboard` を目録から落とす|KILLED (同上)|

`generation_scope` の文言変異は、受理集合を変えず構造化シグナルだけを pin するので
DW-M08 に従い kill に数えず、diagnostic sensitivity pin として別枠に記録する。

期待 node は段 6 の fix 後 anchor で確定し (DW-M07)、`--runner-mode dispatch` で本走する。

## 成果物影響 (DW-G05)

放置した場合: 第一権威点を遮断目録から落とす回帰が検出されないまま、証拠 JSON は
`blocked_outcome_attempts: []` を出し続ける。§5.1 (ii) の証拠が「生成しなかった」と読めるのに
第一権威点経由の生成が遮断されていない状態を、受理集合が受け取る。

## 完全性について

本裁定は閉包が閉じたとは主張しない。導出は名前を付けた 3 権威点からの逆到達閉包であり、
解析対象 module 集合の外、3 権威点のいずれにも到達しない生成器、および解析集合の内側でも
call binding を静的に解決できない caller は、この層では覆わない。**閉包の外に経路は残りうる。**
