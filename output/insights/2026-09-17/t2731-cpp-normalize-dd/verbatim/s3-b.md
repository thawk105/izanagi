## 所見 (real 候補)

**P1 の実装案と、限定 runner に対する変異署名は静的に整合しています。主な修正点は consumer の説明漏れと再走成果物の配置です。**

**B-1 — 保存済み pre-image を再利用する consumer が plan から漏れている。**

- **根拠:** `orchestrator/campaign/p3_s4_loop_trigger_gating.py:322` は `canonical_source_preimage_bytes()` を呼び、`:348` は既存 artifact と新しい bytes が違えば停止する。`s2-plan-out.md:97` は trace checker を扱うが、この consumer を扱っていない。
- **real と主張する理由:** 指令を含む既存 proposal を同じ artifact path で再 materialize すると、修正前後の pre-image 差で停止し得る。「既存測定を無効化しない」と「旧 artifact を live 実装で再生成できる」は別である。
- **是正案（scope 内）:** consumer 整合の説明にこの停止条件を追記する。既存 artifact の書換えや移行機構は不要。

**B-2 — cherry-pick だけでは再走証拠が旧 T-2630 job に出力される。**

- **根拠:** `e35fb7c4e:orchestrator/tests/test_t2630_scan_boundary_reach.py:25` の `EVIDENCE_ROOT` は旧 job の絶対パス。`:279` がそこへ run directory を作る。plan は `s2-plan-out.md:299` で二つの commit の cherry-pick を指示している。
- **real と主張する理由:** harness の `--out` を今回の job に変えても、`observations.json`、compiler 記録、TU 差分は旧 job に残る。新 wave の台帳と証拠の所在が分離する。
- **是正案（scope 内）:** probe branch に限り出力先定数を今回の job へ変更して commit し、その最終 HEAD を harness に束縛する。新 CLI flag は不要。旧配置を意図的に使うなら、新 insight に実際の所在を明記する。

**B-3 — compiler の環境指定が現物より強い。**

- **根拠:** brief `s1-brief.md:18` は unit compiler を `g++-12 / g++` とするが、`test_campaign.py:11193` の `_any_cxx()` は `g++-13` を最優先する。`buildcache.py:1863` は Pegasus compute で system `gcc/g++` を返す。
- **real と主張する理由:** 今回の検査依頼にある「計算ノードの g++-13 系」は現行選択規則では保証されない。旧実測も system g++ 11.4.0 だった。
- **是正案（scope 内）:** compiler は選択規則と実記録で記述する。別 compiler 間の byte 一致を主張せず、同一 compiler 内の prefix 除去・stock 判定を確認する。

## consumer と pin の連鎖

repo 全体の `git grep` で確認した実行 consumer は次のとおりです。

| API | consumer |
|---|---|
| `_cpp_normalize` | `source_digest.py:1697` の文脈正規化、`:2166`・`:2167` の TRACE 差分、`tools/check_trace0_preprocess_identity.py:583`・`:584`・`:592`・`:595` |
| `_normalize_contexts` | `source_digest.py:2113` の working-tree pre-image、`:2225` の baseline |
| `canonical_source_preimage_bytes` | `source_digest.py:2125` の compute、`p3_s4_loop_trigger_gating.py:322` の artifact 保存 |
| 直接 test consumer | `test_campaign.py:11095`、`:11299`、`:11303`、`:11322`、`:11323`、`:11325`、`:12194`、`test_p3_s4_loop_trigger_gating.py:2588` |
| 静的登録 | `test_ccbench_spawn_sites.py:289`、`test_skip_classification.py:37` |

`hooks/` に直接 consumer はありません。T-2630 probe は main の実行 consumer ではなく、probe commit と `output/insights/.../verbatim/probe-test.md` にあります。

trace checker は old/new の normalized bytes をその場で比較します（`tools/check_trace0_preprocess_identity.py:583`）。一方、`mocc_trace_pair.py:615` は保存された report 全体の hash を receipt と照合します。**凍結 normalized hash と現在の `_cpp_normalize` 出力を live 比較する経路はありません。** `:880` の live 比較は checker 自身の Git blob 束縛です。

文書側では以下を区別すべきです。

- 現行説明の更新対象: `source_digest.py:10` の `-E -P` 説明、F1016 恒久対応（`docs/failures.md:27161`）。
- 歴史記録として保持する箇所: `docs/decisions.md:420`、`:798`、`:13763`、archive、T-2630 insight と逐語資料。今回の結果を追補する。
- `docs/orchestrator-design.md` には、今回検索した `-E -P` の記述はありませんでした。

pin の連鎖は次のとおりです。

| 束縛 | 修正の影響 |
|---|---|
| `campaign_lock.py:99` | enforcement closure に `source_digest.py` を含む |
| `contract_loader_binding.py:516` | capture 時に HEAD blob と live bytes を比較。未 commit の変更は `contract-loader-drift` |
| 同 `:535` | 記録 commit と live bytes を比較。commit 後も旧 binding に対する live 検証は不一致になり得る |
| `qualification/contract.py:70` | qualification の code identity 集合に含む |
| `qualification/identity.py:140` | 記録 commit の blob と記録 hash を比較。source_digest の現在 bytes を一律比較する処理ではない |
| `test_t671_source_binding.py:175` | 多くの test は独立 fixture repo を作り commit するため、修正だけで全 node が赤になるわけではない |
| `test_t126_pegasus_tools.py:24` | fixture 名は残るが、`conftest.py:154` の `ratified_enforcement_source` は現在 no-op |

したがって、**修正 commit 後に T-671/T-126 が必ず赤になる、という静的根拠はありません。** 赤になるのは未 commit の live closure を capture する経路、または旧 binding と新しい live closure を混ぜた経路です。親の「commit 後に焦点走」は妥当ですが、旧記録の hash 更新を意味しません。

再帰案は `subprocess.run` の静的 site を一つに保つため、spawn 登録変更は不要です。skip 登録も既存九関数だけを数えるため変更不要です。

duration ledger は必須登録簿ではありません。`conftest.py:1675` は未登録 node を `None` とし、`:1756` で未知所要として並べます。**新八 test の手動 duration 登録は不要**です。

## 変異登録の帰属 (source-level / recipe v2)

plan の A〜H を runner の全選択 node とする限り、期待集合は整合しています。

| source-level 変異 | 完全な期待集合 | 帰属 |
|---|---|---|
| `-dD` を外す | A・B・F・H | 指令が出力から消え、identity が衝突する |
| `removeprefix` を外す | D・E | working-tree だけの未参照供給が identity に混入する |
| `startswith` 判定を恒真化 | G | 模擬した prefix 不一致を受理してしまう |
| docstring の comment-only 変更 | 空集合 | 挙動不変。注入 diff の確認は必要 |

根拠は `s2-plan-out.md:260` の runner 限定と `:264` の置換表です。

- A/B/H は include 行を変えず、未知の条件式も追加しません。F は既存供給 `BACK_OFF` を使います。新しい拒否層による mask は静的には見当たりません。
- D/E の供給確認は変異しても成立し、赤になるのは digest の等値主張です。
- G は `_cpp_normalize` を直接呼び、他の resolve gate を通りません。cache 隔離も plan にあります。
- prefix 剥がしを外して全 `test_campaign` を走らせる場合、既存 node を含めた再登録が必要です。ただし `test_source_digest_stock_roundtrip` の赤は **template 適用木かどうかに依存**します（`test_campaign.py:11237`）。素の stock checkout なら compute/baseline に同じ prefix が入り、必ず赤とはいえません。

修正前実装に新 test だけを載せた予測は **A・B・F・G・H が赤、C・D・E が通過**で、plan と一致します。DW-M08 末尾の新旧両走義務は「テスト強化だけの wave」に対するものですが、この比較は今回も検出力の有用な証拠になります。

recipe v2 は carrier 内容と probe の assert から、次を独立に導けます。N1a/N1b は stock/variant identity、N2a/N2b は stock/variant TU です。

| carrier 変異 | 期待 node | 理由 |
|---|---|---|
| M0 | 空集合 | CMake コメントだけ |
| M1 | N1b・N2b | synthetic live 枝の本文変更 |
| M2 | 四 node | include 一致拒否が `_pair` の resolve 成功要求に伝播 |
| M3a | N1b・N2b | 指令が variant 枝だけで有効 |
| M3b・M6 | 四 node | top-level 指令が両 identity に残り、実 TU も変化 |
| M4・M4b | 四 node | include 除去後にも挟み込み指令が残り、実 TU も変化 |

M0 は `SURVIVED`、残りは `KILLED`。親・plan の予測と一致します。

根拠は旧 `mutation-spec.json` の各置換と、`e35fb7c4e:.../test_t2630_scan_boundary_reach.py:377`・`:392`・`:404` です。TU node は token **一致**を要求せず、resolve **成功**を要求します。M4 の object compile 失敗は追加観測であり、期待 node の直接根拠ではありません。

## recipe 再走の実効性

- **import:** probe は通常の `orchestrator.campaign.source_digest` を import します（probe `:17`）。二つの cherry-pick は probe test だけを変更し、wave の修正を巻き戻しません。runner は自分の repo を import path と cwd に使います（`tools/run_tests.py:57`・`:1261`）。
- **HEAD/spec:** harness は最終 HEAD、carrier 原本、runner identity、cleanliness を束縛します（`tools/mutation_harness.py:3118`）。spec hash は実 file bytes と比較します（`:3105`）。B-2 の変更も含めて commit を終え、新 spec の hash を登録してから走らせる必要があります。
- **compiler:** prefix は同じ compiler・defines の空入力から取得するため、login と compute の predefined 行数が違うこと自体は問題になりません。ただし、その compiler で実入力が prefix を保持することは再走対象です。不一致なら停止する設計です。
- **時間:** recipe の queue wait 3600 秒＋walltime 3600 秒＋grace 600 秒＝7800 秒に対し、`timeout_seconds=8100` は整合します。`hang_timeout_seconds=3000 < 3600` も満たします。現八変異はすべて `hang_risk=false` です。
- **見積り:** 旧実測は collection を含む十 request、8分34秒。旧 spec の `estimated_run_seconds=300` は一 run の見積りであり、harness は baseline＋八変異に乗じます（`:3169`）。8分34秒を一 run 値として扱わないこと。

plan は再走省略を主張していません。unit test だけでは、実 template、実 configure の供給、実 TU の差、および四 node の署名を再確認できません。P2 の再走を維持するのが妥当です。

## 親 brief への反論

**B-4 — F-2 の「七形」は列挙数と一致しない。**

- **根拠:** `s1-brief.md:9` の括弧内は六形。`verbatim-rulings.md` の実測 script は `plain` を加えた七 case。
- **real と主張する理由:** 実測の欠落ではなく brief の列挙漏れです。
- **是正案（scope 内）:** `plain` を追記する。

その他の照合結果：

- F-1 は提供された逐語実測と整合。ただし「GCC 文書の古い記述」という原因断定までは、この資料だけでは裏づけられません。
- F-3 の例示は正しいものの、`BACKOFF_NOINLINE` も追加供給です（`patches/silo-backoff-fixed.patch:24`）。plan は補っています。
- F-4 の三 file の `#define/#undef` 不在は pin の現物と整合。golden 不変は対象 pin/template に限定した予測として扱うべきです。
- P1 に反対する静的根拠は無し。P2 の期待署名にも反論無し。
- cache の実アンカーは `source_digest.py:404`、`_environment_macros` は `:1738`、fake fixture は `test_campaign.py:11541`。brief の範囲指定は少しずれています。
- 再帰用内部 flag と module cache は P1 の局所実装です。新 helper・registry・CLI・公開 cache API の追加はなく、scope 逸脱とは判断しません。
- 「queue は現在空」は過去の状態記録であり、今回の静的検査では再確認していません。

## 総括

実装案と変異署名は支持できます。親へ返す修正点は **B-1 の consumer 境界、B-2 の証拠配置、B-3 の compiler 指定、B-4 の実測列挙**です。新 gate や台帳機構は不要です。

ファイル変更・commit・pytest・変異走行は行っていません。記載した合否は静的予測です。