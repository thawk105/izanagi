## 所見

**S-1・MUST：pipeline の legacy caller の説明を訂正する。P1 自体の変更は不要。**

brief の事実2と plan `s2-plan.md:284` は、pipeline が site 解決した compiler を legacy build に渡すと説明しているが、現物は異なる。

- [pipeline.py:1938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t785-legacy-cache-key/orchestrator/campaign/pipeline.py:1938) の `env_contract is not None` 内でだけ、解決した cc/cxx を `common` に入れる。
- `pipeline.py:2002` の **legacy 分岐は cc/cxx を省略する**。
- `common` を使うのは `pipeline.py:2010` 以降の build_v2 分岐。

したがって legacy pipeline は、s1/s2/s3/s5 と同じく `build()` の定義時既定を使う。新 process で既定変更を読む限り P1 は効く。一方、evidence は `pipeline.py:1790` で site／manifest から compiler を選ぶため、legacy build と一致するとは限らない。食い違いが evidence を変えれば、`buildcache.py:3644–3666` の再検証で停止する。

**放置時の影響：** probe で実証した省略引数経路を、site 解決経路の実証としてレポートへ誤帰属する。P1 後の新 compiler 要求が旧 key に衝突する反例ではないが、「全 caller の compiler/evidence 整合まで確認済み」という受理範囲には広げられない。

**S-2・MUST：`cached` の期待一致と「欠陥再現／修正実証」の成立を、probe の判定で分ける。**

plan `s2-plan.md:78–94` は必要な比較値と「衝突条件不成立」の記録を規定しており、方向は正しい。ただし、明示された終了条件は `--expect` と `cached` の一致が中心で、比較値を実証成立条件へ接続する規定が弱い。

[build_admission.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t785-legacy-cache-key/orchestrator/campaign/build_admission.py:663) の receipt は source 全体を含む。`source_digest.py:256,2410,2425` の compiler 依存 digest が変われば、未修正でも miss になる。さらに `buildcache.py:1605–1617` は sidecar と current admission の完全一致を要求する。

probe の成功判定には少なくとも次を明示すべきである。

- 修正前：異なる実 compiler、同じ source/admission、同じ key、`cached=True`、`_run` 呼出なし、seed と同じ binary SHA。
- 修正後：同じ compiler 対・同じ source/admission 条件で、key が分離し、`cached=False`、実コンパイルが走る。
- receipt 不一致は、修正後に期待どおり miss しても「衝突条件不成立」であり、修正実証には数えない。

**放置時の影響：** admission の変化による miss を P1 の効果と記録し、欠陥を露出させない試行まで完了証拠として受理する余地が残る。検査の stub 化は不要であり、行ってはならない。

**S-3・SHOULD：変異7・8の帰属先テストには、両方とも非省略となる比較組を固定する。**

plan `s2-plan.md:255,273–274` の「cc だけ／cxx だけ違う組」だけでは、指定 node が suffix 欠落変異を殺す保証にならない。

例として歴史的組と `gcc-12/g++-13` を比較すると、suffix から cc を落としても、前者は空文字、後者は `|cxx=g++-13` となり、依然異なる。既存 `test_campaign.py:3184–3202` も、この種の省略境界をまたぐ比較である。

指定 node には、例えば以下を使う。

- cc 欠落：`gcc-12/g++-12` 対 `gcc/g++-12`
- cxx 欠落：`gcc-12/g++-12` 対 `gcc-12/g++`

独立 pre-image テストは suffix 欠落も検出できるため、これはテスト集合全体の無力さではなく、**事前登録した KILLED node の帰属の穴**である。

**放置時の影響：** 指定 node では変異が生存し、変異台帳の予定された検出責任が成立しない。別 node の失敗をそのまま予定 node の実績として扱えない。

**S-4・SHOULD：compiler 候補を替える場合、別名を別 compiler と認定しない条件を追加する。**

plan `s2-plan.md:87` は解決 path と版文字列を記録するが、同一実体の除外を明記していない。本レビューの読み取り確認では、次の二つは同じ realpath だった。

```text
g++     → /usr/bin/x86_64-linux-gnu-g++-11
g++-11  → /usr/bin/x86_64-linux-gnu-g++-11
```

`--version` の先頭は呼出名によって異なるため、その文字列の不一致だけでは不十分。予定された `g++-12` 対 `g++` は実体・版とも異なり、この問題はない。

**放置時の影響：** receipt が一致する対を探す途中で `g++`／`g++-11` を選ぶと、「要求名が違う」という再現を「別 compiler の binary を返した」という証拠へ過大評価する。probe 内で実体を確認する話であり、production key へ realpath/version を追加する提案ではない。

## 親の実測の検算

**P1 と8本の production caller**

`buildcache.py:639` の比較先だけを歴史的 literal 組へ固定すれば、省略対象が既定変更に追随する欠陥は閉じる。

| caller | 現物の compiler 指定 | P1 後 |
|---|---|---|
| s1 `:390` | 省略 | 新 process の定義時既定が非歴史的組なら suffix 付与 |
| s2 `:354–355` | 省略 | 同上 |
| s3 `:258` | 省略 | 同上 |
| s5 `:293` | 省略 | 同上 |
| pipeline `:2002` | **省略** | 同上。S-1 の訂正が必要 |
| backoff_profile `:857` | `runtime.cc/cxx` | 要求組をそのまま key 化 |
| between_run_floor `:316–324` | Pegasus のみ明示、他は省略 | 両経路とも対象。追記の訂正は正しい |
| pegasus_floor_scoping `:214–224` | site 解決組を明示 | 要求組をそのまま key 化 |

`buildcache.py:1861–1865` は compute で `gcc/g++`、その他で module DEFAULT を返す。compute の要求組が既定編集で変わらない場合は、同じ key を維持してよい。

s1/s2/s3/s5、非 Pegasus の between_run_floor は evidence 側に独立した `g++-13` 既定を持つ。P1 はこれを変更しない。既定編集だけで CLI 全体が成功するとの一般化はできないが、evidence 不一致を黙って受理する変更でもない。

**等値比較の別経路**

指定された次の写像は、通常の compiler 文字列についてすべて恒等写像であり、compiler を別値へ潰す衝突を**作らない**。

```python
a if resolved_cxx == a else resolved_cxx
```

- `loop.py:624–638`：evidence → src_token → `:695` の variant id／terminal 判定。
- `pipeline.py:1795–1809`：evidence → admission、`:1894–1914` の variant id／WAL。
- `backoff_sweep.py:307–311`：source token → baseline_ref。
- `p3_s4_loop_trigger_gating.py:317–324`：source pre-image artifact。`:342–356` は既存 bytes と不一致なら拒否する。

import 時に `_DEFAULT_CXX` が束縛されていても、この恒等性は変わらない。なお `pipeline.py:137–143` の stock variant id は元から compiler を含まない。これは今回の条件式による衝突ではなく、P1 が変更する identity でもない。

**現行 key・golden・build_v2**

現行 `DEFAULT_CC/CXX` は literal 組と等しい。したがって、現行の通常の文字列入力すべてについて旧式と P1 の `tc` が一致し、`buildcache.py:640–644` の pre-image と返却 key も一致する。runtime で DEFAULT を変更した状態は、この不変主張から除外する必要がある。

- `_T816_GOLDEN_CK0` は `test_campaign.py:11040–11042` の1要素、値は `silo_2b19d78065_t0`。参照 assertion は `:11193`。P1 はこの計算入力を変えない。
- T2187 の直接 key 呼出 `:3925,:4346` は、対応する build `:3941,:4334` と同じ明示 cc/cxx を渡す。ここも現行 key 不変。
- `_v2_identity` は `buildcache.py:1319–1329` で cc/cxx と toolchain manifest hash を直接含む。P1 の差分は到達しない。
- hit の admission・source evidence・trace diff・symbol 検査は `buildcache.py:3481–3500` に残る。計画上、規律2を緩める変更はない。

golden テストを実行したという意味ではなく、現物の値・参照と式の同値性を確認した。

**probe の実物性と限界**

plan `:45,65` は要求 cxx を evidence と build で揃え、`_run` 以外を差し替えない。これは現物の `buildcache.py:3644` の再検証と整合する。sidecar、source、trace diff、nm、copy/publish の暗黙の迂回は計画上見つからない。

ただし生成する ELF は極小 C++ のものである。実 checkout の証拠と trace diff は検査するが、その checkout をコンパイルした CCBench binary ではない。証明できるのは **production cache 制御が、要求 compiler と異なる compiler 製の実 ELF を返すこと**であり、CCBench 全体のビルド成功・実行・certified 選択・性能差ではない。この限定は plan の記載どおり維持すべきである。

**回帰テストと変異8本**

静的には、変異1・2は DEFAULT 不変性／3組の分離、変異3・4は独立 pre-image、変異5・6は混成 compiler 組で検出できる。変異7・8の指定 node は S-3 の条件が必要。

module global の差し替え＋明示 cc/cxx は、`cache_key` の計算について実編集と等価である。`build()` の定義時既定、caller の省略、別 module の import 時束縛、実 admission の成立までは等価でない。その部分を別 process の実編集 probe が担当する分割は妥当。

**brief の事実1〜7・追記**

| 項目 | 検算結果 |
|---|---|
| 1 | DEFAULT、呼出時比較とも一致。 |
| 2 | between_run_floor の追記は正しい。pipeline はなお誤りで S-1。 |
| 3 | receipt に compiler 名・nonce は直接ないが、compiler 依存 source digest がある。追記は正しい。ただし key 一致だけでは不十分で、sidecar・再検証等の通過も必要。 |
| 4 | 定義時束縛の説明は正しい。global だけの変更は省略 caller の新 compiler 要求を再現しない。 |
| 5 | golden の定義位置は plan の訂正が正しい。既存 fake は commit/source 検査も stub 化しており、今回の代替にはならない。 |
| 6 | `pegasus02`、GCC 9.5／11.4／12.3、Clang 14、`g++-13` 不在を確認。`_run` の site 拒否位置も一致。T2000 RESULT は3投入とも arm 未開始と記載。 |
| 7 | T548 の当初4 worktree と T2237 の対象3ファイルは、brief 基準 HEAD・現在の main の双方と byte 一致。現在は T548 の追加 merge worktree もあり、これも一致。作成時刻は未検証。 |

本 worktree の既定 cache root は現在も不在。「その root の entry は0件」は成立するが、全 root の件数には一般化できない。現 HEAD は brief と同じ `0c292eff6`、一方 main は既に前進しているため、「local main と同じ」は記録時点の事実として扱う。

既定 literal 導入の履歴は `9cde78124`、日付は2026-07-02と一致。`decisions.md`／`failures.md` の `T-785` 検索では該当なしだが、番号を持たない意味的な既存被覆まで「ない」と証明したものではない。

## 総括

**P1 は採用可能。** 現行 key を保ち、8本の legacy caller に共通する省略条件の欠陥を最小差分で閉じる。caller 編集・build_v2 変更・hit gate 追加は不要。

実装前に、pipeline の経路説明と probe の実証成立条件を修正する。変異7・8の比較組も固定する。receipt 一致を伴う修正前偽 hit は依然未実測であり、成立しなければ「再現未成立」と報告する。

本レビューでは編集、pytest、再現 probe、変異実行を行っていない。