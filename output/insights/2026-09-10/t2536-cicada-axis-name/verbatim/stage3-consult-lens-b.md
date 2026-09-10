## 所見 1 — build cache が旧 cicada binary と衝突する

- 判定: real
- file:line: `orchestrator/campaign/buildcache.py:624-642, 1295-1325, 1936, 2565-2603, 3189-3238`
- 反例または変異: 変更前に `Genome("cicada", {"INLINE_VERSION_OPT": 1})` を build すると、旧汎用名が無視され、実体は既定値 0 の binary になる。その cache identity は canonical genome、CCBench pin、source evidence 等だけで、`cmake_defines()` や写像版を含まない。変更後も同じ key / v2 digest で hit し、再計算された `configure_argv` は `_CICADA=1` を表示する一方、binary は旧実体 0 のままになる。
- 成果物影響 1 行: binary hash、configure argv、genome が相互不整合な WAL・受領証・レポートを作り、値 1 の build-errorさえ旧 cache hit で隠せる。
- 必要な修正: legacy `cache_key()` と `_v2_identity()` の双方で、非恒等写像を持つ genome の mapping fingerprint を namespace に入れる。silo / mocc / tictoc の既存 key は不変にし、旧 cicada key と新 key が異なる回帰テストを追加する。

## 所見 2 — 親の「cicada の live build 経路はない」は過剰一般化

- 判定: real
- file:line: `brief.md:18-24`; `orchestrator/campaign/screening_driver.py:507-522, 562-567, 618-621`; `orchestrator/campaign/buildcache.py:1935-1936, 2553-2555, 3183-3192`
- 反例または変異: literal `"cicada"` を持つ専用 driver がなくても、`evaluate_candidate()` と buildcache は任意の `Genome.protocol` から target と binary path を生成し、protocol whitelist を持たない。したがって generic caller から cicada build へ到達できる。
- 成果物影響 1 行: 現在の認定受理集合は変わらないが、raw screening の WAL・build cache・レポートは直ちに写像変更と所見 1 の影響を受ける。

## 所見 3 — 新規 CMake parser 案は既存 parser を重複し、耐久条件も不足する

- 判定: real
- file:line: `plan.md:154-186`; `orchestrator/campaign/source_digest.py:413-862`; `external/ccbench/cmake/ProtocolHelpers.cmake:14-15, 29-43`
- 反例または変異: 既存 `_parse_supplied_macro_details()` はコメント、引用、bracket argument、bare option、universal と protocol OPTIONS を既に扱う。これを使わず同じ解析器をテスト内へ新設すると意味論が二重化する。一方、既存 parser をそのまま使うだけでも次の実測反例がある。
  - `if(FALSE)` 内に旧 `ccbench_add_protocol(... OPTIONS INLINE_VERSION_OPT=${..._CICADA})` を残し、実行される call から同 option を削除すると、parser は旧 mapping を返す。実 CMake は供給しないため false green。
  - `OPTIONS "BACK_OFF=${...};INLINE_VERSION_OPT=${...}"` のように同じ list を quoted semicolon でまとめると、実 CMake の list 展開経路は保てるが parser は未対応 token として停止する。false red。
  - `Options.cmake` の cache 宣言存在を必須にする案も、Izanagi が毎回 `-D` で値を供給し、OPTIONS が参照する構造では必要条件ではない。宣言整理だけで誤って赤になりうる。
- 成果物影響 1 行: false green は値が届かない binary を受理し、false red は実効写像が同じ CCBench pin を拒否して成果物生成を停止する。
- 必要な修正: `source_digest.py` の parser を公開 API として再利用し、実行制御を解釈しない構造は明示的に fails-closed にする。quoted list、コメント・空白変更、inactive call の正負 fixture を同じ検査へ含める。

## 所見 4 — 逆写像が双射であることを検査していない

- 判定: real
- file:line: `brief.md:39-44`; `plan.md:115-135, 179-201`
- 反例または変異: CCBench が同一 protocol の 2 軸を同じ cache 変数へ写し、Izanagi 表もそれに更新した場合、提案された exact table equality は緑になる。しかし逆引きはどちらか一方しか返せず、producer も同じ `-D` key を二重出力して後勝ちになる。
- 成果物影響 1 行: 受領証で一方の軸が欠落または別軸へ帰属し、canonical genome と実 binary の対応が壊れる。
- 必要な修正: protocol ごとに table value の一意性を検査し、逆変換関数も複数一致を必ず拒否する。

## 所見 5 — import 循環懸念

- 判定: refuted
- file:line: `orchestrator/campaign/model.py:16-20, 39-63`; `orchestrator/campaign/genome.py:13-17`
- 反例または変異: 現在は `genome.py → model.py` の一方向で、`model.py` は runtime に `genome.py` を import しない。17 行程度の literal 表と同 module 内関数を追加しても逆辺は生じず、遅延 import も計画されていない。
- 成果物影響 1 行: projected graph では import 順、部分初期化、成果物値への影響はない。
- 限界: `calibrator/cli.py` は射影外なので、その module を含む全 import graph は独立確認できない。

## 所見 6 — 独立組み立て・解析 site の棚卸し

- 判定: 判定不能
- file:line: `orchestrator/campaign/model.py:61-63`; `orchestrator/campaign/screening_driver.py:126-168`; `orchestrator/campaign/condition_meaning_gate.py:1311-1351, 1629-1645`; `orchestrator/campaign/source_digest.py:639-862, 2022-2097`; `orchestrator/tests/test_pegasus_calibration_workload.py:85-110, 252-261`
- 反例または変異:

| site | 独立処理 | 計画 | cicada 評価 |
|---|---|---|---|
| `model.py:63` | 軸名から `-DCCBENCH_` を生成 | 修正 | 本欠陥 |
| `screening_driver.py:143,162` | request 照合と除去集合を局所生成 | 修正 | 現在の domain に cicada 軸はないが、共有化は妥当 |
| `condition_meaning_gate.py:1640` | cache route を局所生成 | 修正しない | `DEFINE_SPECS` に `INLINE_VERSION_OPT` がなく、現状の cicada 誤動作は refuted |
| `source_digest.py:840-862` | CMake 実体を解析 | 修正しない | 独立 oracle 候補。所見 3 の制約付きで再利用すべき |
| `source_digest.py:2022-2068` | cache 名から TU macro 実効値を復元 | 修正しない | 同じ `Genome.flags` を cache override と解釈するため、producer と API 意味論が異なる |
| `test_pegasus...py:85-110,252-261` | shell の raw `-DCCBENCH_` を解析 | 修正しない | whitelist が silo / mocc / tictoc のため projected 範囲では安全 |

`paper_story_a1_paired.py`、`silo_ladder_rung1.py`、`tools/pegasus/`、その他 fixture は射影されていない。単独段規律上、それらを読んだ repo-wide 総数は出せない。

- 成果物影響 1 行: 未確認 site が旧汎用名を生成していれば、対応するレポート・golden・受領証だけが別の genome または既定値を参照し続ける。

## 所見 7 — `source_digest` 内に Genome の二つの意味が残る

- 判定: real
- file:line: `orchestrator/campaign/source_digest.py:902-958, 2022-2068`
- 反例または変異: `_merge_defines()` は `if left in flags: continue` により `Genome.flags["INLINE_VERSION_OPT"]=1` を TU macro 値として優先する。一方 `resolve_effective_defines_from_cmake_sources()` は同じ key を `CCBENCH_INLINE_VERSION_OPT` cache override と解釈し、cicada RHS `_CICADA` の既定値を返す。同じ Genome が API により 1 と 0 の二値になる。
- 成果物影響 1 行: 新 drift test が高位 API の effective value を oracle にすると誤期待を固定し、将来の supply evidence と build identity が食い違う。
- 必要な修正: 本 wave では高位 API を値 oracle にせず、公開した mapping parser の `macro → cache name` だけを利用する。意味論統合を別 gate に拡張する必要はない。

## 所見 8 — projected 既存テストへの波及

- 判定: refuted
- file:line: `orchestrator/tests/test_pegasus_calibration_workload.py:198-265, 318-345, 449-464`
- 反例または変異: D1863 の 3 検査は shell 表と `SPACES` を比較するだけで、shell、軸名、値域はいずれも変更しない。silo argv golden と cicada whitelist 拒否も不変である。projected file 内には cicada の旧 `cmake_defines()` を期待する assertion はない。
- 成果物影響 1 行: このファイルの既存受理集合、shell argv、D1863 参照は変わらない。
- 注意: 実走していないため緑とは判定していない。

## 所見 9 — 未射影の既存テスト・golden 影響

- 判定: 判定不能
- file:line: `plan.md:234-249`; `test_campaign.py:判定不能`; `paper_story_a1_paired.py:判定不能`; s1 goldens: 判定不能
- 反例または変異: `test_campaign.py` の CMake fixture、受領証 golden、s1 goldens は射影されていないため静的列挙できない。計画の「射影された既存テストには期待がない」は repo 全体の無影響を導かない。
- 成果物影響 1 行: 旧 cicada argv を固定した fixture があれば collection/test が赤になり、旧 cache key を固定した golden があれば所見 1 の必須修正で参照が変わる。

## 所見 10 — 親の残る二つの一般化

- 判定: 判定不能
- file:line: `brief.md:14-24`; `parent-measurements.md:7-15`
- 反例または変異: silo / mocc / tictoc の CMakeLists と `Options.cmake` は射影外なので、「全軸が恒等写像」は親 probe の再確認に留まり、独立検証できない。whole-file SHA については projected code に固定期待値との比較はないが、repo 全体の pin site は検索できない。なお `condition_meaning_gate.py:1239-1241,1355-1357` は CMake 全文 hash を evidence 値に含めるが、固定 pin ではない。
- 成果物影響 1 行: 前者が誤りなら既存 3 protocol の argv が変わり、後者に未発見 pin があればコメントを含む編集で既存 reference が赤になる。

## 総括

1. mapping fingerprint を legacy / v2 cache identity に入れ、旧 cicada binary の alias を必ず切る。  
2. CMake parser は既存資産を公開・補強して再利用し、inactive call、quoted list、双射性を正負検査する。  
3. author 前に未射影の producer/parser site と `test_campaign.py`・golden 群の棚卸しを完了する。