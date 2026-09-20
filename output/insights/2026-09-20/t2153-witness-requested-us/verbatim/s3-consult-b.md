## 所見

**判定：plan は修正してから author へ渡すべきです。最重要の欠落は、REQUESTED_US fixture の CMake mapping です。** 静的検査のみ実施し、編集・pytest・実 TU 前処理は行っていません。

以下、G＝[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/campaign/condition_meaning_gate.py)、T＝[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/tests/test_condition_meaning_gate.py)、P＝[plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/artifacts/dev-wave-t2153-witness-requested-us/plan.md)、B＝[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/brief.md) とします。repo 内の省略 path は当該 worktree 基準です。

1. **real／must-fix：fixture の供給 mapping が欠落する。**
   P:140–151 は T:241 の builder を拡張するが、その末尾 T:286 が呼ぶ `condition_gate_test_support.py:143–198` は、`define_spec` に対応する cache mapping を生成しません。`:176–177` は固定 `_OPTIONS` を書き、`:17–38` に REQUESTED_US はありません。owner＋header を生成するだけでは実 compile command に define が載らず、G:2295 の `macro-not-supplied` に至る構造です。
   **修正：** 新 fixture 分岐で、installer 呼出し後に `CCBENCH_BACKOFF_REQUESTED_US` の既定0と TU mapping を局所追加する。共通 installer の汎用化や新 fixture directory は不要です。
   **放置時の成果物：正例・CLI fixture が supply red となり、登録の受入証拠を取得できない。**

2. **refuted／nit：NOINLINE 特例 assert の緩和は不要。**
   T:255–258 の条件は「主宣言 file≠owner TU」です。REQUESTED_US の主宣言は `transaction.cc` なので該当しません。P:140 の専用分岐を T:253 より前へ置き、既存 assert を維持できます。
   一方 T:327 の `matches == [pair] * count` は REQUESTED_US 限定で変更が必要です。`patches/silo-backoff-requested-us.patch:29,41,60,178` の現物どおり、**header pair×2、owner pair×2を独立に完全列挙**し、他 macro の式は維持する。集合化や `>=` への緩和は不可です。T:1987 の非対値 parametrize は REQUESTED_US を追加するだけで足ります。
   **放置時の成果物：不要な assert 緩和は成果物を改善せず、patch 束縛を緩めれば部分登録を検出できなくなる。**

3. **real／must-fix：I1 の「21 macro 不変」と検証範囲が一致しない。**
   B:27 の検証例は SORT／NOINLINE の2件です。これは浅い／深い shadow の代表比較として妥当ですが、21件の record 同一性の実証にはなりません。P:218 の全21件比較を実施条件にするか、実証した範囲を2件へ限定してください。
   同じ source roots・toolchain・configure・driver-id を前後で再利用し、一時 root とその派生 ID/digest だけを区別する手順は妥当です。source identity、source hash、dependency closure、前処理 digestまで一括除外してはいけません。
   **放置時の成果物：実測2件を根拠に「21件の bytes 不変」と記した過大な互換性報告になる。**

4. **real／nit：serialization 固定期待の追加は削れる。**
   P:203–207 の全21件への key pin 展開と、偽の `_assert…` 戻り値から固定 canonical record を生成する新 test は重複が大きい。T:1607–1626 の既存 field/key pin、T:1359 の全登録正例、上記の前後比較を使えばよい。必要なら既存 field pin に `CompileTimeBranchSelectionEvidence` を追加するだけにする。
   同様に P:166 の「shadow 後に header を元本文へ戻す注入 test」は、P:165 の shadow 検査＋m2＋正例で代替できます。新 dataclass、別 proof_kind、汎用 validator は不要です。
   **DW-G05：これらを削っても production の certified 選択・レポート・受理集合は不変で、既存検査と比較証拠を残せば新しい固定期待台帳も要らない。**

5. **refuted／must-fix維持：箇所識別は単なる仮想リスク向け一般化ではない。**
   G:3019–3028 は全箇所へ同じ marker を挿入し、G:3191–3198、3356–3376 は合計しか見ません。P:94 の「owner 2箇所を無効化＋headerを二重 include」は、静的には2＋2のまま、観測総数だけ4へ戻せます。実 patch の `#pragma once` は任意の入力本文の一回性を保証しません。
   **宣言した4箇所の識別に限定した補正は残す。** 未宣言 directive の走査、include 専用 gate、N-file framework までは足さない。既存 mismatch reason を利用できます。
   **放置時の成果物：合計は正しいが所有TU側が未観測の入力を green とし、「全箇所」の主張が偽になる。**

6. **real／nit：pin 調査の結論は限定して書き直す。**
   現在のG/Tの SHA256・blob ID の逐語参照は `git grep` で0件でした。しかし path/key hit は多数あり、「pin閉包0件」を検索 hit 全体の意味で書くのは誤りです。B:15 の「probe 2本は import のみ」も不正確で、`t316_sandbox_backend_probe.py:2011–2028` は FIXED の gate を実際に呼びます。今回はその要求が変わらないため追随不要です。
   B-4 の現行件数は **49**（`test_p3_b4_wiring_probe.py:329`）。47は同ファイルの履歴コメントです。
   **放置時の成果物：実装結果は変わらないが、閉包調査の記録が再現不能・不正確になる。**

7. **real／must-fix（完了主張）：研究前進は CLI の観測証拠に限定する。**
   G:19–20 は枝本文・動的到達性・correctnessを明示的に除外しています。4箇所観測は診断 define の枝選択証拠を増やしますが、`requested_us = realized_us` の数値的成立や既存 B-10 成果物を再認証しません。`backoff_requested_us.py:1107–1111` は admission を捨てます。
   **放置時の成果物：CLI の未確立一覧改善を、公開 driver JSON／receipt や B-10 proof chain 全体の改善として過大報告する。**

## pin 表

検索は現在の tracked text に対し、G/T双方の path・SHA256・blob、および指定された全 key を使用しました。`output/` の path hit はGが433 file、Tが202 fileあり、歴史的 insight・変異台帳を含みます。これらを現在の追随対象とは扱いません。

| 対象 | 現物・検索結果 | must／不要 |
|---|---|---|
| Gの bytes | SHA256 `32424d2c013e…`、blob `31bc58d0a5bb…`：逐語 hit 0 | bytes pin追随不要 |
| Tの bytes | SHA256 `a2650bac3090…`、blob `158e2626c429…`：逐語 hit 0 | bytes pin追随不要 |
| `_COMPILE_TIME_BRANCH_MACROS`／tuple順序 | T:33–55、1037 | **must：末尾追加、既存順序維持** |
| `MEANING_SUPPORTED_MACROS` | G:342–344、T:3090–3093 | **must：独立期待側を通じて23へ追随** |
| `CONDITIONAL_BRANCH_WITNESSES` | G:258–341、T:1034–1052 | **must：主2-tuple＋副file独立期待** |
| `_CONDITIONAL_BRANCH_SITE_COUNTS`／`_declared_site_count` | G:324–331、S1 test:719 | **must：主fileの2を登録。helperの意味は維持** |
| MOCC 2-tuple consumer | `test_mocc_mutation_proof.py:177`、`test_mocc_template_proof.py:267`、`test_mocc_proof_surface.py:569` | 編集不要 |
| `BACKOFF_REQUESTED_US` supply集合 | G:147–150、T:3075 | 既登録。変更不要 |
| dataclass／evidence key pin | T:1607–1626、G:817–823 | **must：旧field/keyを維持** |
| docstring逐語 | G:13、T:3305 | **must：両方をTwenty-twoへ** |
| `_run_process` spawn数 | `test_ccbench_spawn_sites.py:123`＝1 | subprocess追加なしなら追随不要 |
| B-4 module数 | `test_p3_b4_wiring_probe.py:324–329`＝49 | import閉包を増やさなければ追随不要 |
| getsource／行数 | G/Tを対象とする固定 source・総行数 pinは未検出。B-4:341以降は現行ASTとの比較 | 数値の付替え不要 |
| probe path | `t2228_driver_gate_liveness_probe.py:207–214`、`t316_sandbox_backend_probe.py:2011–2028` | path維持・FIXED経路不変なら追随不要 |
| duration ledger | `acceptance_duration_ledger.json:6706`等はnode時間 | 内容hash pinではない。手動追随不要 |
| `check_docs.py` | 指定path/keyによる直接pinなし | 編集不要。親の完了検査は別途必要 |
| 凍結manifest | 指定path/key検索で追随すべきmanifestを未検出 | 凍結物更新不要 |

結論は **「現在のG/Tの bytes変更に追随する凍結pinは未検出。集合・順序・schema・docstringの契約pinは存在する」** が正確です。

## driver 表

path は `orchestrator/campaign/` 以下です。「要求」は現在の公開呼出し経路を指します。

| driver | REQUESTED_USを要求するか | admissionが成果物へ載るか | declaration／登録のみの追随 |
|---|---|---|---|
| `backoff_requested_us.py` | する：127–140 | 載らない：1107–1111で廃棄 | `backoff_sweep.py:194–209`経由でNone。追随なし |
| `backoff_sweep.py` | 自身のpreflightはFIXEDのみ：452–460。既定表84は要求ではない | preflight返値を廃棄：452–467 | 非FIXEDはNone。追随なし |
| `screening_driver.py` | genomeに含まれる場合：101–123。66の0は既定値 | 611–619で返値を廃棄 | 231–234で非FIXEDはNone。追随なし |
| `s8a_trigger_coverage.py` | しない。GATING／MISATTR：152–166 | 載る：132–135、349 | factory：120。ただし対象要求なし |
| `s8a_trigger_freq.py` | しない。coverage helperをmisattrなしで使用：134–139 | 載る：148 | helperのfactory。対象要求なし |
| `s8a_trigger_sweep.py` | しない。GATINGのみ：318–322 | helperは返すが408で廃棄 | None：328 |
| `s1_direct_comparison.py` | REQUESTED_USは既定表180–185に無く、202–205で拒否 | receipt機構あり：253–266 | factory：314。ただしREQUESTED_USは到達しない |
| `paper_story_a2_certification.py` | FIXED／NOINLINEに限定：689、729 | receipt収集経路あり：690、681–687 | factory：745。対象要求なし |
| `silo_ladder_rung1.py` | FIXED／RUNG／REPORT：2173–2184 | 2236–2248で返す | factory：2232。対象要求なし |
| `s2_verify_calibration.py`、`s3_lock_coverage.py`、`s5_permutation_coverage.py` | 各既存positive controlのみ：順に131–136、123–128、120–125 | helperがadmissionをJSON化 | factoryあり、対象要求なし |
| `s3_mocc_lock_coverage.py`、`s3_mocc_mutation_proof.py`、`s3_mocc_template_proof.py`、`t152_write_intent_coverage.py` | MOCC／write-intentの各対象macro | 対象経路でgateを評価 | factory：295、147、84、198。REQUESTED_USの公開要求なし |

**現在の公開 driver で、今回の登録だけによりREQUESTED_USの受理が変わるものは確認されませんでした。** 任意macroを取る内部helperへ直接REQUESTED_USを渡すことと、公開driverの自動追随は区別します。

自動追随する公開入口は **CLI**（G:4276–4292）です。親の実 patch 木を読み、次を確認しました。

- `transaction.cc:11,157`、`backoff.hh:109,141` の4箇所。
- `transaction.cc:152` の `BACK_OFF` が後者のTU箇所を囲む。
- `cmake/Options.cmake:20,73` は既定1とそのmapping。
- `transaction.hh:9` の相対include、`backoff.hh:1` のpragma once。

したがって、記載された既定configureなら4箇所活性、BACK_OFF=0なら3箇所という静的説明は整合しています。実観測済みとは扱いません。

## 親 brief への反論

- **P1：採用。** 主2-tupleだけでは副fileを表現できません。小さな副mappingは必要なデータであり、過剰な一般化とは判定しません。副file用dataclassや全登録簿のtuple形式変更は削る。
- **P2：採用。** 副証拠を既存recordへ条件付きで載せる。別proof_kindやoptional dataclass fieldは不要。
- **P3：簡素化。** 既存reasonを再利用し、file名はdetailへ。P:71のようにexpected/observedまで `path:2` に変える必要はなく、B:37どおり数値文字列を維持できる。
- **P4：呼称を訂正。** 「owner TUのN」ではなく「主宣言fileのN」。NOINLINEの主fileはheaderです。
- **P5：採用。** BACK_OFFを同伴defineとして強制すると、検査するconfigureを変えてしまう。0なら拒否する境界を残す。
- **P6：深いshadowは必須、合計だけの全箇所保証は不十分。** 全計装fileをG:3088のsymlink対象から除外する。追加include gateは不要だが、4箇所の識別は残す。
- **P7：変異を絞り、検出箇所を正しく帰属する。** 原m4は後段でも拒否されるため、受理集合変異の成果から削除しm4′へ置換。m5はrequired集合の削除だけでなく、欠落recordが実際に通る誤条件にする。m8は通常schemaで先に落ちるので「bytes比較でkill」と書かない。
- **P8：完了条件として維持。** 最終production登録簿、pin `e9e477ca1`、fixed→requested-us、official同形供給でlogin／計算ノード双方のCLIを実走する。合成TUの緑は代替にならない。

変異matrixは **m0、m1、m2、m3、m4′、m5、m7、m8** を残す案です。m6は既存の独立登録簿・patch束縛と正例が残るため、最小matrixからは削れます。登録削除へのtest耐性自体は維持してください。

新規testも、次の境界へ絞れます。

| 残す境界 | 最小の例 |
|---|---|
| 正例 | 正常2＋2でsupply／meaning／admission、pragma once付き再includeのgreen |
| 宣言数 | owner欠落、header逐語変更の2例 |
| 観測不足・過剰 | header未include、pragma onceなし二重include |
| configure | ownerの1箇所だけBACK_OFFで不活性 |
| 相殺 | owner不活性＋header二重include |
| shadow | 全計装fileが通常file、元bytes不変、中継directory実体 |
| schema | 副key欠落、登録値不一致、digest・identity不一致、余分key |
| 旧契約 | 既存field/key pin＋前後record比較 |

P:159のheader欠落とP:160のheader逐語変更は同じ箇所数判定に入るので、後者へ寄せられます。P:166の計装解除注入はm2と重複します。直接assertの検査は、schemaによる二次拒否に遮られないため残します。

前waveの運用罠への対応も具体化すべきです。焦点走はB:51どおり `tools/run_tests.py --force-dispatch`。S1 fixtureは `test_s1_direct_comparison.py:716–731` がstock側の本文も増やす一方、Options更新は主rootだけなので、未確立例を安易に0/0へ変更しない。今回のREQUESTED_US fixtureでも、本文だけでなくmappingを整える。docstringはG:13とT:3305を同時更新する。

## 総括

**author着手前の必須修正は、fixtureのREQUESTED_US mapping、全箇所識別、I1の実証範囲の明確化です。** driverを配線しない結論は支持します。

研究前進は「最終production CLIで、指定configure下の4逐語箇所の枝選択を確立し、そのCLI admissionの未確立一覧が縮む」と書くのが正確です。公開driver成果物やB-10数値の再認証は、このwaveの成果に含めないでください。