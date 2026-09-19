## must-fix

**1. hold／selected 保全テストは実 shard 選択と閉包検査を迂回している。**

- **根拠:** `test_acceptance_schedule_order.py:1977–1984` は `items.remove()` で選択を代用し、`selected` に nodeid ではなく item の identity 集合を代入する。`_izanagi_acceptance_shard_spec` も設定しないため、`conftest.py:2197–2198` の早期 return により閉包検査が動かない。本物は `acceptance_shards.py:901–920` で records 作成・allocate・deselect・nodeid の selected/digest 保存を行う。
- **成果物への影響:** 「hold → 実 shard 選択 → 閉包確認 → suffix 除去 → pairing の統合検査済み」という裁定パッケージの根拠が成立しない。
- **是正:** wrapper の yield 中に実 `acceptance_shards.pytest_collection_modifyitems` を呼び、有効な spec と閉包を満たす fixture を使う。実 selected、records、digest と retained identity を A/B で比較する。現テストは hold・suffix・reorder の局所検査として残せる。

**2. 集計器は「最長 unit の worker の2個目の unit」を報告していない。**

- **根拠:** `t2766_ab_analyze.py:162–165,189–192` は worker の item 列から `sequence[1]` を取り、`second_item` として保存する。`:464–466` の selftest も、3-item unit の内部の2件目を期待している。
- **成果物への影響:** 最長 unit が複数 item の場合、実際の次 unit が partner でも「partner ではない」と読める資料になり、段4で要求した相方の記述を満たさない。
- **是正:** worker の実行 item 列を保持しつつ、scope ごとの実行 unit 列を別に構成し、その2番目を報告する。初期 unit 内の2件目と、次 unit を区別した正負例を追加する。

## should

**3. M2 は変異の書換え箇所によって kill の帰属が変わる。**

- **根拠:** `conftest.py:1804–1817` では候補開始・head・partner 幅を共通の `width` で決める。段4の「`realized[:48]` を47へ」を head slice だけに適用すると、候補は48から始まり、unit 47 が欠落する。`conftest.py:1769–1776` の identity 検査で先に落ちる。
- **成果物への影響:** identity 欠落の検出を「head 境界の検出」として変異表に計上してしまう。
- **是正:** 幅47の変異を `width` の変更として明確化し、被覆を保ったまま `test_g12_pairing_queue_and_all_item_witness` の head assertion で落ちることを記録する。slice 単独変更なら、kill 理由は identity 欠落と記す。

**4. 集計器は投入順・隣接性・置換順を検算しない。**

- **根拠:** `t2766_ab_analyze.py:348–350` は存在するディレクトリだけを番号順に並べ、`:307–315` は隣り合う配列要素が A/B かだけを見る。番号欠落、同番号、事前登録の A,B／B,A／A,B、無効対の同順置換は確認しない。
- **成果物への影響:** 中間走の記録欠落や順序違反があっても、別の走同士を有効な隣接対として中央値に含め得る。
- **是正:** 走番号の一意性・連続性、対ID、投入順と置換元を検証する。違反は除外理由として残す。

**5. cost の再計算は浮動小数点の加算順まで独立に変えている。**

- **根拠:** `t2766_ab_analyze.py:93–107` は selected の辞書順で unit cost を加算する。本番 `conftest.py:1853–1862` は unit 内の collection 順で加算する。集計器 `:170–177` は float の完全一致による Counter 比較である。
- **成果物への影響:** 複数 item unit の丸め差が head／候補境界に影響すると、正しい B を witness 不一致として除外し得る。
- **是正:** 本番が保持する unit 内順を再構成して同じ加算を行うか、丸め差を含めた比較方針を事前に固定する。単に広い許容誤差で partner 選択の誤りを隠さないこと。

## nit

**6. B 環境の隔離は当該テストモジュールに限定される。**

- **根拠:** `test_acceptance_schedule_order.py:1766–1770` の autouse fixture は同モジュール内だけで有効。共通 `conftest.py:765–804` の隔離対象に pairing env はない。ただし、確認した dispatch の exact-env テストは `test_pegasus_dispatch_compute.py:277–290,1087–1095,6265–6269` で明示的な環境を渡しており、外側 B env が直接混入する構造ではない。
- **成果物への影響:** 指定資料内では、これによって赤になる具体的 nodeid は確定できない。したがって現時点では成果物を変える不具合として計上しない。
- **是正:** 全 suite の pytester／環境継承テストを確認する。共通 fixture で隔離する場合も、collection 後の実行時に解除し、外側 B の collection と witness を消さない配置にする。

## A 不変・受理集合・xdist

**A は未設定／空文字について、静的読解上は不変。**

patch の定数追加、helper 追加、reorder 後段、hook 分岐を確認した。A では pairing helper を呼ばず、fresh な unit dict に `pairing_rank` はないため property を追加しない。従来の flatten と同じ順序・identity で `_replace_acceptance_items` を呼ぶ。空 ledger／既知 cost 不在の return と identity 例外も維持される。

二重の opt-in 評価は `os.environ.get()` と比較だけで副作用がなく、間に yield や外部 hook はない。通常の固定環境では不整合は生じない。

`test_g12_off_preserves_literal_collection_and_item_state` は固定 `_PAIRING_A_UNITS` から期待列を作っており、変更後関数同士の自己比較ではない。identity、selected 集合、marker、既存 property も確認する。

**受理集合を変える実装変更は見当たらないが、統合テストの被覆には must-fix 1 が残る。** pairing は既存 unit の並べ替えで、最終 identity 検査も有効である。

**xdist の cardinality 安定 sort と整合する。** `conftest.py:1801,1826` は `loadscope.py:374–379` と同じ cardinality 降順を使う。head 固定、cost 昇順 partner、realized 順の rest、再 sort 検算も設計どおり。96 unit 未満では従来の `ordered_units` をそのまま返し、property を付けない。

実配布反例も正しい。`loadscope.py:238–251,332–336` は完了通知後の pending **item** 数が2以下なら次 unit を送る。`test_acceptance_schedule_order.py:2023–2029` の順で、singleton worker が最後の partner を消費し、3-item worker の次 unit が `u048`、2-item worker の3番目が `u049` になる。

## witness・env 配線

JUnit 到達テストは実 xdist 経路を通る。`_run_live` は `test_acceptance_schedule_order.py:275–277` で subprocess に `-n 1 --dist loadgroup` を渡す。production hook が collection 時に property を付け、実行 worker の report が controller に届く。JUnit は controller 側だけで有効になり、`junitxml.py:490–497` が report の property を保存する。skip も同じ finalize 経路を通る。

`gw0` の検査は1 worker の転送確認であり、複数 worker の配布検査ではない。ただし collection 時に各 worker が自分の ID を付け、実行 worker の item から report が作られるため、worker property の意味は整合する。

env の全段は静的に成立する。

| 段 | 根拠 |
|---|---|
| login → shard dispatch | `run_tests.py:1295–1304,2329–2334` の copy |
| dispatch → request | `dispatch_compute.py:132,3695–3698` の allowlist |
| request → compute overlay | 同 `:1822–1845` |
| compute → shard pytest | `run_tests.py:1509–1532` |
| pytest → local xdist worker | subprocess の環境継承 |

追加 request テストは実 request 生成を検査しており、exact pin だけではない。全3 shard の live 伝播は焦点走ログだけからは確認できない。

## 変異帰属

以下は静的な予測であり、変異実走の kill 報告ではない。

| 変異 | 指定テストと予測される失敗 | 帰属 |
|---|---|---|
| M1 | 正例 `:1823` の固定 partner 列不一致。候補は singleton なので cardinality gate は通る | 可 |
| M2 | 共通幅47なら正例 `:1820`。head slice だけなら先に identity 例外 | **定義の明確化が必要** |
| M3 | off 負例 `:1854` の固定 A collection 不一致 | 可 |
| M4 | infeasible 負例 `:1878–1879` で期待した例外が出ない | 可 |
| M5 | 正例 `:1832` の property 欠落。live JUnit でも `:1924` が不一致 | 可 |
| M6 | exact pin `test_pegasus_dispatch_compute.py:6281` と request 内容 `:6275` が不一致 | 可。全段伝播の検出とは呼ばない |

M4 の49個の double-unit fixture は到達可能であり、head 外の double unit が rest に残って再 sort 検算に掛かる。両層 stub による擬似的な kill ではない。

## 集計器・焦点走

witness の主要な独立検算は成立している。`t2766_ab_analyze.py:89–118,170–177` は selected、runtime scope、台帳から期待 head／partner cost 多重集合を作り、自己申告 rank は観測集合の分類にだけ使う。被覆、全 rank、partner flag、cardinality、worker item 数も検査する。

`junit_key` は `junitxml.py:445–453` と同じ前方変換で、module path、class、parametrize ID 内の `::` を保持する。`split_group` は `]` より後の `@` を suffix と扱う。通常の対象形式では整合し、対応が曖昧なら拒否する。

判定(i)/(ii)/(iii)、ゼロ・全対負、3対未満、3種の中央値、12走上限、最初の有効3対という分岐は段4と一致する。ただし投入順検証は should 4、相方の説明は must-fix 2 が残る。

`focus/focus2.log:18,36` は **972 items、971 passed、1 skipped、failed 0、error 0**。`:10` は child rc=0。赤の nodeid はなく、実装／テスト／環境への失敗帰属対象もない。末尾の `recording-unavailable:series-invalid` は pytest の赤ではない。ログ自身が非受入走と明記しており、B 全受入の緑とは扱えない。今回 pytest は実行していない。

## 総括

**must-fix は2件**：実 shard 選択を迂回する保全テスト、2番目の unit を出さない集計。

- **A 不変:** 未設定／空文字では静的に支持。固定期待列による負例も成立。
- **xdist 整合:** 支持。実 scheduler の配布反例も正しい。
- **env 全段:** 静的に成立。全 suite の B 汚染不在・全3 shard の live 伝播は未確証。
- **M1〜M6:** M1・M3〜M6 は静的に帰属可能。M2 は共通幅変更か slice 単独変更かを確定する必要がある。変異実走は未確認。
- **焦点走:** 971 passed、1 skipped、failed/error 0。