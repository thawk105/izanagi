## レンズ A

**A1 — must-fix：呼び手表の閉包は、certified 経路と直接 build 経路を分ける必要がある。**

根拠：親の 25 件＋手確認 3 件に加え、pipeline を経由せず、cc/cxx を省略する呼び手が存在する。

| 呼び手 | 事前 evidence | 判定 |
|---|---|---|
| `s1_verify_extime_calibration.py:382,390` | 既定 compiler | build と対称 |
| `s2_verify_calibration.py:352–357` | 既定 compiler | build と対称 |
| `s3_lock_coverage.py:257–261` | 既定 compiler | build と対称 |
| `s5_permutation_coverage.py:292–296` | 既定 compiler | build と対称 |
| `between_run_floor.py:327–340` | Pegasus は site compiler、それ以外は既定 | build にも対応する compiler を渡すため対称 |

さらに `pegasus_floor_scoping.py:214–224`、`backoff_profile.py:847–863`、`tools/pegasus/probes/t1683_rr5_cost_probe.py:248`、`t2187_adaptive_const_probe.py:3941,4334`、`manual_probes/test_t2000_legacy_build_probe.py:1876` は compiler を明示する直接経路である。

これらは非対称への到達の反例ではない。しかし、直接 build API には `env_contract` 引数がなく、親の条件 (A) をそのまま適用できない。条件は「事前 evidence の compiler と build の compiler が異なること」で個別に確認する必要がある。

**成果物への影響：** 放置すると「全 production 呼び手」の到達条件表が、直接 build 経路を未検査のまま完全扱いする。
**是正案：** certified 入口の表に上記の直接経路表を併記し、「直接経路では同じ非対称を発見しなかった」と閉じる。

別名 import、関数参照の代入、`getattr` / `partial`、指定された Python ディレクトリと shell 内の対象名を再走査した範囲では、対象 3 API への追加の production 呼び出しは発見しなかった。ただし、これは検査範囲内の静的閉包であり、任意の動的 Python 呼び出しの不可能性の証明ではない。

**A2 — must-fix：R-b を全計算ノード・将来にも成立する障壁として使えない。**

根拠：T-1643 §3 が示す不在は `bnode009` と `pegasus02` の当該実測環境である。今回の login 観測も計算ノード全体の PATH を証明しない。

**成果物への影響：** 放置すると P1 の「到達したとしても R-b で拒否」が、未観測 node や compiler 導入後にも成立する裁定になる。
**是正案：** R-b を「観測した node・日時・PATH における拒否」と明記する。`g++-13` が解決可能になっても現在の呼び手に対する R-a は変わらないが、仮想的な旧分岐到達後の不在拒否は消える。以後は evidence の不一致拒否などを個別に評価する。

**A3 — should：「発生記録なし」は検索した記録の範囲へ限定する。**

根拠：worklog / failures の検索は実 run の WAL 検索ではない。`layout.py:202–209` は campaign root 配下の `runs/wal.jsonl` を使用する。

**成果物への影響：** 放置すると、文書に未記録という観測が実 run に発生していないという履歴上の主張に変わる。
**是正案：** 現状は「worklog / failures に記載を発見せず、WAL は未調査」とする。追加調査する場合の対象は以下。今回は検索を実行していない。

- `output/campaigns/*/runs/wal.jsonl`
- `output/exploration/campaigns/*/runs/wal.jsonl`
- driver の `output_root` で指定した保存先にある同形式の WAL
- 対応する job の stdout / stderr、保存された configure 診断

`abort` の `build-error` と payload 内の `g++-13` を調べ、`identity-error`、`eval-exception` も補助検索する。該当記録があっても、compute 実行・legacy 分岐だったかは execution receipt、host 記録、build argv と照合する。診断の末尾切り詰めもあるため、文字列不在だけでは未発生を証明できない。

**A4 — nit：site 条件と R-a の読みは支持する。ただし前提を明記する。**

根拠：

- `site_policy.py:30–46` は環境値を分類条件にせず、`bnode[0-9]+` を NQSV marker に関係なく compute とする。
- `require_evidence` による差は hostname 不明や Pegasus 名の証拠不足側であり、通常の bnode を compute 以外へ変えない（`:66–84`）。
- 両 p3 driver の `_current_site` は同じ関数を参照する。注入された site / contract にも対応関係の検査がある（`p3_s4_loop.py:2479–2494`、trigger 側 `:1034–1049`）。OTHER に対応する linux 契約で compute に進めば R-a が拒否する。
- screening の既知の Pegasus 対応 caller は contract を渡し、省略する s6 / s8a は `linux-baremetal`。
- `loop.py:177` と `pipeline.py:1738` は同じ認可関数を呼ぶ。
- 登録世代では linux が `attestation_mode="none"`、Pegasus が `"required"`（`env_contract.py:253–311`）。認可時は active rows を検査し、required が一意でなければ拒否する（`execution_guard.py:137–161`）。

特に linux の拒否は「required が必ず一つ」という前提に依存しない。ゼロ・複数でも拒否され、一つでも linux はその required 契約ではない。Pegasus 正例の成功には有効な activation state が必要である。

**成果物への影響：** 現在の到達判定は変わらない。
**是正案：** (A)(B) は「通常の未注入経路、site 観測中の hostname が安定、manifest 無し」における compiler 選択名の非対称として記述する。manifest は `pipeline.py:1661` で contract 無しとの併用を拒否する。

**A5 — nit：25 件の数え方と production の分類を直す。**

根拠：AST の 25 件には loop 内 2 件と screening 内 1 件が入り、手確認 3 件を足すと 28 呼び出し箇所になる。親の分類表の 25 件は、その中継 3 件を除いた別の集計である。また `manual_probes/test_t2397_a1_source.py:80,96` は monkeypatch を伴う手動テストである。

**成果物への影響：** 到達判定は変わらないが、検査範囲の件数を再現しにくい。
**是正案：** 「28 箇所＝中継 3＋外側 25、外側には手動テスト 1 を含む」と表記する。

## レンズ B

**B1 — must-fix：P2 の「reason が変わるだけ」は consumer の動作で反証される。**

根拠：

- 実際の reason は「pre-build evidence 確定不能」ではなく `identity-error`（`pipeline.py:1858–1860`）。
- `model.py:207–214` は `identity-error` を retryable に含め、`build-error` を含めない。
- `loop.py:589–606` はこの差により、再開時の再評価と permanent skip を分ける。
- `s1_direct_comparison.py:1005–1018` は逆に `build-error` を retryable に分類し、`identity-error` はその集合に含めない。
- WAL でも source が null の abort を認める reason 集合が異なる（`wal.py:83–85`）。

**成果物への影響：** 放置すると、再試行・最終的な評価機会・材料レポートの分類が変わる変更を「成果物不変」として裁定する。
**是正案：** P2 の根拠を撤回する。「現行の確認済み production 呼び手では変更対象の非対称経路へ到達せず、変更の必要性を確認できない」ことと、reason の意味が同じであることを分ける。

受理集合の不変も一般には導けない。両 compiler が存在し、両者の evidence が異なる入力では、現行は R-c で拒否する。事前 evidence を build compiler に合わせれば、この不一致拒否を取り除く。他の gate も通るかは別途必要だが、「必ず同じ受理集合」の証明にはならない。また loop 等が渡す既存 evidence との照合（`pipeline.py:1812–1819`）も変更後の挙動に影響する。

**B2 — must-fix：R-c の保証は compiler 同一性ではなく evidence の一致である。**

根拠：`source_digest.py:2450–2463` の evidence は compiler 名を持たず、`src_token` に加えて `source_bytes_sha256` などを持つ。`buildcache.py:3656` 以降は evidence と runtime binding を比較する。

したがって：

- 同じ `src_token` だけでは通過条件にならない。stock 同士でも source bytes の digest が異なれば拒否する。
- 異なる compiler が同じ **evidence 全体**を返せば、この検査は通る。
- fresh build の binary hash は実際に生成・コピーした binary から取る（`buildcache.py:3557–3575`）。
- v1 の cache key に compiler 名は入るが（`:640–643`）、v2 の toolchain manifest 束縛（`:1301–1329`）と同等ではない。

**成果物への影響：** 放置すると「compiler 差はすべて拒否する」という、実装より強い安全主張が README に残る。
**是正案：** 「build compiler で再計算した source evidence が事前 evidence と異なれば拒否する」へ限定する。

同じ正規化 source identity を返す二 compiler の通過は、この identity 検査の意味では自然であり、それだけで誤った source の受理を示さない。一方、同じ identity・異なる toolchain で性能値を作る問題は別に残る。D293 は単なる provenance 表示の問題ではなく、床値を介して certified 選択の判定境界へ影響すると説明している。本調査でその性能契約まで保証したとは書けない。

**B3 — should：R-b の例外順序を条件付きに訂正する。**

根拠：`buildcache.py:3791–3821` の `_run` は、まず heavy-work site gate を呼び、その後の `subprocess.run` の `OSError` を捕捉していない。

- compute で cmake が起動し、compiler 不在を非ゼロ終了として返す場合は、親の通り `RuntimeError` → `build-error`。
- cmake 自体の不在・起動不能では `FileNotFoundError` 等がそのまま出て、`pipeline.py:2024` の except には入らない。
- `loop.py:795` 以降には `Exception` 隔離があり、通常の loop 経路では別の abort になる。直接 evaluate の caller まで同じ隔離を保証するわけではない。
- cache hit の evidence 再計算では、compiler 起動の `OSError` は `source_digest.py:1693–1698` 等で `RuntimeError` に変換され、pipeline の except に入る。ただし sidecar 検証等を先に通る必要がある。

**成果物への影響：** 放置すると、拒否することと、必ず `build-error` として campaign を継続することを混同する。
**是正案：** 拒否順序表に site gate、cmake 起動失敗、cmake 非ゼロ終了、cache evidence 失敗を分けて記載する。今回このための例外処理変更までは要求しない。

**B4 — must-fix：probe の前提と、実測できる主張を修正する。**

根拠：親 brief 末尾 4 項目、`buildcache.py:3433–3449,3797–3798`、`build_admission.py:656–698`。

**成果物への影響：** 放置すると、admission や login gate で止まった結果を compiler 不在の実測として数え、未実行の cache-hit / R-c まで実測済み扱いする可能性がある。
**是正案：** probe を次の範囲へ限定する。

| 項目 | 必要な修正 |
|---|---|
| site / compiler 観測 | host、日時、PATH と実解決先を保存する。全 node へ一般化しない。 |
| R-a | 実 `authorize` と実 guard を使う。activation 読込失敗と guard の拒否を分離する。Pegasus 正例は「認可関数が通る」であり full attestation 成功ではない。 |
| evidence | login の site compiler は既定 `g++-13` なので、不在なら site 側も失敗する。site 側成功を全 site の期待値にしない。同じ compiler を二度呼ぶ重複 cell は統合できる。 |
| fresh build | compute で site evidence を取得できた場合に実行する。login では compiler 失敗より先に site gate が拒否するため、R-b の configure 実測には数えない。 |

production API からの admission 導出は可能。ただし「stock genome＋submodule HEAD」だけでは不十分で、receipt 無しの stock admission には `src_token == STOCK`、tracked clean、`ccbench_commit == CURRENT_PIN` が必要である（`build_admission.py:675–678`）。これを満たした source、登録済み `GeneratorId` による context、実 evidence、derive / require の順を明記する。

job dir の cache は設計上可能である。`_require_secure_fs_contract` は POSIX/Linux の機能検査であり、job dir を禁止する検査ではない。`assert_worktree_within_allowlist` の対象は cache root ではなく CCBench source の `sub`。ただし cache は source と別の専用実ディレクトリにし、fresh を主張するなら既存 entry がないことを確認する。

この構成なら 100〜150 行は現実的な目安だが、未実装なので保証はできない。行数のために前提不成立を期待拒否へ混ぜないこと。

この probe は fresh-build の例外を測るもので、pipeline の WAL abort 変換、cache-hit 拒否、異なる compiler 間の R-c 不一致を実測しない。それらは静的確認として明記すればよく、今回の閉包判断を変えない人工的な cache 作成や追加ビルドは足さなくてよい。

**B5 — should：D293 を一般的な旧分岐変更の全面禁止として引用しない。**

根拠：D293 の決定対象は「床値 campaign の compiler 解決」であり、toolchain 束縛との同時 land を条件にしている。

**成果物への影響：** 放置すると、対象と条件が限定された裁定が、全 legacy build への無条件禁止という別の裁定になる。
**是正案：** 床値への変更は D293 の条件に従い、本件では変更の必要性が未確認であるため採用しない、と分ける。

修正候補の成果物への影響は次の通り。

| 案 | 採用時／放置時の違い |
|---|---|
| (i) build に site compiler を渡す | compiler 不在障壁を外し、build・性能材料の生成可能範囲を変え得る。床値では D293 の同時束縛条件が必要。 |
| (ii) 事前 evidence を既定 compiler にする | failure stage、WAL reason、再試行・集計を変え、条件次第で R-c の拒否範囲も変えるため、成果物不変とは言えない。 |
| (iii) compute の旧分岐を新 gate で拒否 | compiler の有無に依存しない明示拒否となり到達条件表は変わるが、D2044 と依頼の scope 外。 |
| (iv) 実装せず限界として閉じる | certified 選択の実装は変えず、呼び手範囲・観測環境・evidence と toolchain の保証境界を材料レポートと裁定に残す。現時点の推奨。 |

## 総括

**must-fix は 5 件**：A1、A2、B1、B2、B4。必要なのは主に brief・probe 設計・裁定根拠の修正であり、production 実装の変更を要求するものではない。

- **P1：条件付き支持。** 確認した certified 呼び手から非対称へ到達する反例は見つからず、修正しない方針は妥当。ただし直接 build 経路の補記と、R-b / R-c の保証範囲の限定が必要。
- **P2：反証。** reason の変更は再試行や集計に作用する。「実装しない」という結論は維持可能だが、成果物不変という根拠では支えられない。
- **呼び手閉包：欠落あり。** 親の全 production 範囲には、`s1_verify_extime_calibration`、`s2_verify_calibration`、`s3_lock_coverage`、`s5_permutation_coverage`、`between_run_floor` 等の直接 build 経路が欠ける。対象 3 API の production 呼び出しについては、追加の非対称到達経路を発見しなかった。

指定資料とコードの静的読解のみを行った。pytest、probe、過去 WAL の実走査、ファイル書込みは行っていない。