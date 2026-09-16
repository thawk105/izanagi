## 総括

**6 所見は静的読解ではすべて closed。新たな実装回帰は確認できませんでした。ただし M10 は fix 後の現物に対して成立しません。** 登録文の変更先が現行の解決先そのもので、B1 を再現しないためです。取り下げ済みの M2・M7 も不成立です。

HEAD は `b9187e920`、親は `99c9b9222` と確認しました。編集・commit・テスト・変異実行はしていません。以下の `file:line` は指定 worktree 内の相対表記です。closed は実走の緑を意味しません。

## 1. 所見ごとの対応表 (closed / partial / regressed)

| 所見 | 判定 | 根拠 file:line（fix 後の現物） | 残る穴 / 新しく開いた穴 |
|---|---|---|---|
| B1 silo | **closed** | `tools/pegasus/submit_silo_ladder_rung1.sh:6,165,175,205`、`tools/pegasus/silo_ladder_rung1.sh:17,362,372,379,385,386,392,452` | 新2依存も既存3本と同じ関数を通り、実 directory・非 symlink・HEAD 完全一致・dirty 拒否を受ける。永続側とコピー後の双方を検査。scratch に2本が届いてから env を上書きし、そこから解決する。新規の穴は確認できない。 |
| B3 mocc | **closed** | `tools/pegasus/mocc_trace_pilot.sh:1528,1534,1538,1556,1560,1564,1608,1612`、`orchestrator/tests/test_pegasus_tools.py:496,499,522,523,526,530,533` | hydrate は1回で存在・HEAD 検査より前。移動部分は旧ブロックとバイト一致。旧 env／checkout 解決行は残っていない。契約テストの指定された検出力も維持。 |
| B2 T-126 | **closed** | `orchestrator/qualification/submission.py:99,163,215,231`、`orchestrator/qualification/identity.py:228`、`orchestrator/qualification/t126_driver.py:1332,1377`、`orchestrator/qualification/collector.py:1464,1516` | CLI の root が依存解決まで渡る。非空 env 優先は従前どおり。`_dependency()` は変更前とバイト一致。後続3ファイルにも helper の `__file__` を依存 root にする同型の誤りはない。 |
| P-1 | **closed** | `orchestrator/tests/test_pegasus_thirdparty_fetch.py:925`、`tools/pegasus/fetch_third_party.py:119,724,730,751` | 本物の `tool.main` を使い、未指定時の rc=2・stdout 空・stderr 1行・env 名を検査。env 指定時の rc=0・root 一致も維持し、stderr 空も追加。 |
| E3-1 fixture | **closed** | `orchestrator/tests/test_t126_pegasus_tools.py:3394,4025,4030,4031,4032,4035`、`tools/pegasus/submit_t126_qualification.sh:287` | `output/env` 自体が symlink のまま、両依存へ到達可能。移動は当該負例内だけで、共通 `_submit_fixture()` は変更されていない。他 node の fixture を変える波及はない。全走結果は未確認。 |
| E3-2 probe | **closed** | `tools/pegasus/probes/t293_perf_site_probe.py:576,587,694,783,945,1010` | 既存の CLI→run→probe の checkout root を渡す。policy 読取り・submission 読込みにも使う同じ root。新引数・env はない。 |

補足：

- **B1 の FetchContent 集合は3本のまま。** `orchestrator/campaign/silo_ladder_rung1.py:66,875,883,885` と両 shell の `-eq 3` を維持し、gflags/glog は別の2本として合流しています。追加 inline Python（submit `:167`、job `:364`）は `json, sys` のみです。既存の orchestrator import を新規追加と数える攻撃は不成立です。
- **B3 の契約テストは、解決行の欠落・重複を `:496`、assignment の欠落・重複を `:530`、解決→assignment の順序を `:531` で引き続き拒否します。** hydrate→root 読取り→解決の順序は `:523`、assignment→存在検査→HEAD は `:533`。旧解決行の併存も `:526–527` で拒否します。
- B2 の探索で想定した `orchestrator/campaign/t126_driver.py` は不在でした。停止せず、実在する `orchestrator/qualification/t126_driver.py` を確認しました。

## 2. 派生値の検算

**提示された3つの量化は、いずれも一致しました。**

| 量化 | 原データからの再計算 |
|---|---|
| 15本中、env 上書きは silo だけ、自己 hydrate は mocc だけ | `test_pegasus_tools.py:470` の列挙を読み取り、実ファイル15本を走査。対象 env への代入は silo `:392` の1件、hydrate 呼出しは mocc `:1534` の1件。 |
| F1・F2・F3・F4 のテスト関数削除0 | 指定された差分全文を再集計。F1+F3、F2+F4 とも削除された `def test_…` は0。F3 の evidence テスト、F4 の既存負例も関数を維持。 |
| evidence の8 path 中、wave が変えたのは4つ | 凍結 JSON の `binding` にある直接の `path` 付き8項目を列挙し、wave 初期差分と fix 差分を照合。変更は下表の4つ。 |

| binding key | 本 wave の変更 | wave 開始前から歴史値か |
|---|---|---|
| `calibration` | なし | いいえ |
| `driver` | あり | はい |
| `ledger` | なし | はい |
| `patch` | なし | いいえ |
| `pbs_job` | あり | いいえ。本 wave で歴史化 |
| `policy` | あり | はい |
| `submitter` | あり | いいえ。今回の fix で歴史化 |
| `verifier_module` | なし | はい |

比較には `d97c423bd→0165027e0` と `99c9b9222→b9187e920` を使い、途中の main 統合に含まれる別 wave の変更を混ぜていません。

現行 bytes の SHA256 も追補2と一致しました。

- `pbs_job`: `99687368a1fdf10d8f699be3a32afd2814f51d98bcad5fbdf6a1862ca72b456f`
- `submitter`: `6990ad4470aba09b8c62224f33a453c330a0be4fbb913cf1e477bb882659412b`

現行 SHA の完全一致と歴史 binding の一致・現行との不一致は、`test_silo_ladder_rung1_evidence.py:1288,1295,1302,1303` に残っています。

## 3. 変異 M1〜M11 の単一理由性 (fix 後)

「成立」は静的に登録可能という意味です。KILLED の実証ではありません。

| 変異 | 判定 | 前後・内側の拒否層との照合 |
|---|---|---|
| M1 `.git` 終端要求除去 | **成立** | `test_pegasus_thirdparty_fetch.py:946` は `_build_dependency_sources()` を直接呼ぶ。`fetch_third_party.py:85` を除けば、URL の他条件は通る。`_load_policy()` や origin 照合 `:440` に入らず、以前のマスクは解消。 |
| M2 `fullmatch→search` | **不成立・取り下げ維持** | CLI 経路は `fetch_third_party.py:102` から `_dependency_pins()` に入り、`silo_ladder_rung1.py:859,862,863` が形式／上位 pin 不一致を別に拒否する。 |
| M3 `_verify_cache` で `allow_shallow=True` | **成立** | 対象は `fetch_third_party.py:546`。`verify` は `:751` の1回だけ。shallow gate は `:358` で、残る HEAD・dirty・origin 検査は同じ正常 pin の入力を拒否しない。期待 node は `test_m03_shallow_cache_is_rejected`（`:282`）または新2依存の `verify/shallow` case（`:839`）。fetch／hydrate case は単一理由の証拠に数えない。 |
| M4 gflags を列挙から落とす | **成立（main の合流列挙が対象）** | `fetch_third_party.py:729` で gflags を落とせば `:751` の検証対象からも落ちる。別層による gflags 不在拒否はない。`test_pegasus_thirdparty_fetch.py:744,768` の exact JSON と `:916` の欠落負例が直接検出する。 |
| M5 p3_s4 の解決を固定 path にする | **成立（静的契約）** | `test_p3_s4_loop_job_contract.py:319`、`test_pegasus_tools.py:491,496` が解決文字列を直接検査する。shell を実行しないので、実 job の存在検査にマスクされない。 |
| M6 現行 golden を旧値へ戻す | **成立** | `pegasus_policy_expected_goldens.py:5` の定数を、`test_silo_ladder_rung1_evidence.py:1281` が現行 bytes の SHA と直接比較する。歴史値比較 `:1302` とは別の検査。 |
| M7 使用直前検証の除去 | **不成立・取り下げ維持** | 除去対象の `_verify_source` 相当は追加されていない。例えば silo の使用段は `silo_ladder_rung1.sh:475,477,479` の既存 HEAD・status 検査。裁定§2に従い追加要求はしない。 |
| M8 cache env を無視 | **成立** | `fetch_third_party.py:122` が対象。復元 node の env 指定成功側 `test_pegasus_thirdparty_fetch.py:939–943` は正常 cache を使い、変異で `:124` の未指定拒否に変わる。別の不正入力による拒否ではない。 |
| M9 `repo_root` を `__file__` 基準へ戻す | **成立** | `submission.py:164` が対象。`test_t126_pegasus_tools.py:3402` の **hydrated case** は checkout に正常依存、helper 側には staging なし（`:3410`）。変異後は `_dependency()` `:100` が誤った場所を拒否する。missing-gflags case は元から拒否なので主証拠にしない。 |
| M10 scratch 上書き後の env へ「戻す」 | **不成立・登録訂正が必要** | 現物は既に `silo_ladder_rung1.sh:392→452→453` のその解決。fix は解決先を変えず、`:372–386` で scratch に2本を追加した。登録文どおりでは変更も受理集合の差も生じない。新契約 node `test_silo_ladder_rung1_driver.py:2734` も、この順序を正しいものとして要求する。 |
| M11 hydrate を gflags 段より後へ戻す | **成立（静的契約）** | `test_pegasus_tools.py:523,531,533` が hydrate→解決→assignment→存在検査を直接要求する。ブロックだけ後送しても、assignment ごと後送しても順序違反になる。実 shell の先行失敗に依存しない。 |

M10 を B1 の回帰検出として残すなら、対象は解決行ではなく、**job のコピー列挙から `build_dependency_rows` を除く変更**への再登録が必要です。これは今回追加した接続そのものを戻す変更で、新しい検査層の提案ではありません。

## 4. 新しく開いた穴

**新しい実装上の穴は確認できませんでした。残件は M10 の登録不整合です。**

M10 を現在の記述で実効変異数や KILLED 件数に含めると、B1 の再発を検出したという証拠を過大評価します。現行実装は正しい scratch 解決を維持しているため、B1 自体を partial に戻す理由にはなりません。

## 5. 攻めたが成立しなかったもの

- **silo の新2依存だけ検査を迂回する：不成立。** 既存3本と同じループ・検査関数を通る。
- **mocc の移動に検査の削除・緩和が混ざる：不成立。** hydrate ブロックはバイト一致し、1回だけ。
- **mocc の期待値変更で欠落・重複・順序違反を見逃す：不成立。** 指定された各拒否条件を維持。
- **T-126 の一時 helper root 誤認が後続検証に残る：不成立。** identity は渡された root、driver／collector は attempt namespace から得た checkout root を使う。
- **E3-1 が symlink 成分を検査対象外へ逃がす：不成立。** `output/env` が実際の symlink 成分として残る。
- **歴史化によって現行 shell の byte 変更を見逃す：不成立。** 両 shell の現行 SHA pin と歴史 binding の検査を維持。