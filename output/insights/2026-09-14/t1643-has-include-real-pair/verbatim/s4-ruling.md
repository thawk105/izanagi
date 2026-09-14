# [T-1643] 段 4 裁定

親が段 3 の所見を real/refuted で裁定し、plan v2 と変異事前登録を確定する。
所見は **すべて real** と判定した。refuted はゼロである。以下は採否と、それが段 5 以降を
どう変えるかだけを書く。

## 1. 所見の裁定

### sol (レンズ: 実測が実測になっていない経路)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| S-1 | stdin 列から実 header 内の真偽は結論できない (`source_digest.py:1662`,`:1666`) | real | **採用** |
| S-2 | `-I S/include` を便宜的に追加しない判断は正しい | real | **採用** |
| S-3 | 再構成列は生成 command を得た場合よりさらに限定される | real | **採用** |
| S-4 | 正負・反転対照には探索環境の取り違えを検出する歯がない | real | **採用** |
| S-5 | 抽出対照の成立は compiler 起動を証明しない | real | **採用** |
| S-6 | `_assert_conditional_macros_covered` は実際に駆動されるが、直呼びは全経路実走ではない | real | **採用** |
| S-7 | fixture の `#define` が目的の拒否より先に `_dump_macros` を走らせ、拒否分類を誤らせる | real | **採用** |
| S-反1 | legacy 分岐 (`common is None`) は `cc/cxx` を渡さず既定 `g++-13` を使う | real | **採用** |
| S-反2 | `g++` は名前であって `/usr/bin/g++` の保証ではない (PATH 解決) | real | **採用** |
| S-反3 | 既存被覆として引いた一式は「当時の guard が受理した反例」であり、現行拒否の発火実測ではない | real | **採用** |
| S-反4 | 純増 (b)(c) は一部過大、既測式の再測定価値は一部過小 | real | **採用** |

### luna (レンズ: 結論の射程・scope・運用制約)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| L-1 | blanket reject の走査範囲は `EVOLVE_BLOCK_SOURCES` の 3 file で非再帰 (`source_digest.py:85`,`:1895`) | real | **採用** |
| L-2 | compute の system `g++` は manifest 不在時の条件付き選択結果 | real | **採用** |
| L-3 | 式の列挙数や compiler 数から族全体の安全性へ一般化できない (`DW-G03`) | real | **採用** |
| L-整1 | **既登録の `generic` 経路で compute 実測は可能。F660 を理由に login 限定へ落とす必要はない** | real | **採用** |
| L-整2 | `generic` の compute 環境 (`env_mode="clean"`、cwd=repo root) は本番 admission 環境ではない | real | **採用** |
| L-整3 | runbook §7.0.0 の自動判定は `run_tests.py` / `check_ai_provenance.py` の配線で、一時 probe には効かない | real | **採用** |
| L-整4 | 4 種の観測を 1 つの「admission 成功」へ畳むと完了主張が過大になる | real | **採用** |
| L-整5 | 規律 6 違反の具体的な指示経路は現プランに無い | real | **確認** |
| L-反1 | 既存被覆を「1 式だけ」と総称するのは過小 | real | **採用** |
| L-反2 | D30 系の g++-13 実測は `#ifdef __x86_64__` であって `__has_include` ではない | real | **採用** |
| L-反3 | 過去の compute 不在観測を、今日の不可能性へ昇格させている | real | **採用** |

### 親が現物で検算した結果

- **L-整1 は裏が取れた。** `docs/pegasus-runbook.md:607-614` が D895 で「任意コマンドは `generic`
  task で送る」「渡された argv 自体を `shell=False` で実行する」「`generic` も計算ノードでしか
  子を起動しない」と定める。`tools/pegasus/admission_registry.json` の main 側現物で
  `tools/pegasus/dispatch_compute.py` は `class="local-ok"` で登録済み。
  probe は `tools/t1643_*.py` であり `tools/pegasus/` 配下の新規実行体ではないので F660 に当たらない。
- **L-1 は裏が取れた。** `source_digest.py:85-86`
  `EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc", "cc/mocc/transaction.cc")`。
- **L-反1 は裏が取れた。** `output/insights/2026-07-28/t148-review-verbatim/review-B-codex-layers-and-test-teeth.md:59`
  に literal 間接形 (`#define IZ_HAS_LOCAL __has_include("atomic_wrapper.hh")`)、同 `:101` に
  **「g++12 では `-nostdinc` + `<atomic>` 自体が preprocess error になり、blanket guard 以外の
  理由でも赤」**という記録がある。後者は S-7 と同型の「前段の失敗」であり、設計に直接効く。

## 2. 親 brief の訂正 (段 3 の反論を受けて)

以下は段 1 brief の記述を**撤回・限定**する。成果物はこの訂正後の記述に従う。

1. **「この食い違いは g++-12 で 1 式だけ実測済み」を撤回する。** 正しくは
   「**明示的な真偽 pair (0/1) の記録として確認できたのは 1 式**であり、同じ review 群には
   literal 間接形と `<atomic>` の preprocess error の記録もある。既存記録から族全体の
   完全な pair 実測済みとは断定できない」。
2. **「純増 = (a)(b)(c)」を限定する。** 純増は**式名や compiler 列数ではなく、今回新しく確定した
   exact な環境 (argv・cwd・env・入力位置)・文脈・拒否箇所・compiler 対応**として数える。
   `#define` 間接形の一部と g++-13 不在は既記録であり、新規性は今日の環境での再確認にある。
3. **「(P1-c) g++-13 は compute にも無い」を撤回する。** 親の今日の探索は login に限る。
   compute は**未探索**である。probe が compute で compiler 探索を行い、その結果で記録する。
   compute のセルへ login の `compiler_missing` を転記してはならない。
4. **「(P1-d) checker は blanket reject するので真偽差は受理集合に到達しない」を限定する。**
   拒否は `EVOLVE_BLOCK_SOURCES` の 3 file の**字句走査**に対して働き、include 先は非再帰である。
   また normalize と `-dM` は `#include` 行を除去する。したがって「届かない」と言えるのは
   走査対象 file の条件指令と `#define` 本体に限る。
5. **「(P1-a) admission toolchain = compute の system `g++`」を限定する。** manifest 優先経路
   (`pipeline.py:1792`,`:1947`) と legacy 分岐 (`common is None` → 既定 `g++-13`) がある。
   対象 admission の分岐を記録しない限り断定しない。
6. **「受入・実測環境: runbook §7.0.0 の自動判定に従う」を訂正する。** §7.0.0 の配線は
   `run_tests.py` / `check_ai_provenance.py` であり、一時 probe には効かない。
   probe の実行場所は本裁定が明示的に決める (下記 3-(6))。

## 3. plan v2 — 段 5 実装子への確定指示

段 2 プランを土台に、次を確定する。**プランと本裁定が食い違う場合は本裁定が優先する。**

1. **probe の置き場所**: `tools/t1643_has_include_pair_probe.py` (worktree 内)。
   **repo へ残さない。** 親が実行後に job dir へ退避し、段 7 の commit には含めない。
   `tools/pegasus/` 配下へは置かない (F660 の新規 Pegasus 実行体にしない)。
2. **列 (環境)**: `checker-normalize` / `checker-dM` / `build-search` / `build-header`。
   各列に hostname・cwd・実 argv・実効 env・compiler の requested/found/realpath/version/sha256 を
   記録する。**`CPATH` / `CPLUS_INCLUDE_PATH` / `C_INCLUDE_PATH` 等を勝手に消さない。**
3. **compiler**: `g++` / `g++-9` / `g++-11` / `g++-12` / `g++-13` を requested name のまま列挙する。
   不在は `status="compiler_missing"`、`value=null`、`rc=null` と、実際の探索結果・起動例外を記録する。
   **rc を `127` と創作しない。** 不在を `0` で埋めない。
4. **行 (式)**: 段 2 プランの行群をそのまま使う。ただし S-7 に従い
   **fixture の結果取り出しが目的の拒否より先に preprocess を起こす構造を避けるか、
   起きた場合は `other_error` に分類する**こと。`<atomic>` 型の preprocess error は
   既存記録 (`review-B:101`) にあるので、**エラー本文を保存し、真偽値に昇格させない。**
5. **実 build の compile command**: `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` での取得を試みる。
   取れなければ `build-search-reconstructed` 列として区別し、未解決の推移的 include・順序・
   暗黙 system path・生成 header の有無を `limitations[]` に記録する。
   **再構成だけを admission の実 build 実測と認定しない。**
   `-I S/include` を便宜的に追加しない (S-2)。
6. **実行場所**: **login と compute の両方で走らせる。**
   - login: 親が worktree 内で直接実行する。
   - compute: `python3 tools/pegasus/dispatch_compute.py --task generic -- python3 tools/t1643_has_include_pair_probe.py ...`
     を親が実行する。**絶対 path で防壁を迂回しない。**
     runbook:625 は「`generic` gateway の内側 argv を綴りによって拒否したりしなかったりする」と
     記録しているので、**拒否されたらその事実を記録し、迂回しない。**
   - compute 側の結果は `generic の compute 環境での観測` と明記する。
     `env_mode="clean"`・cwd=repo root 固定を `limitations[]` に書く。
7. **対照**: 正の対照・負の対照・反転対照・抽出対照・guard 対照を実装する。
   **S-4 と S-5 に従い、対照成立を「列の探索条件が実 build と対応した」証拠にも
   「compiler が起動した」証拠にも数えない。** `value` は今回の subprocess の rc/stdout から
   導出された場合だけ実測値とする。対照が不成立なら raw 表を残し、**結論を出さない。**
8. **(P1-d) の確認**: `source_digest._assert_conditional_macros_covered` を実関数で呼ぶ。
   `_lex_normalize` / `_dump_macros` / `_environment_macros` / subprocess を stub にしない。
   拒否分類は**発生箇所に従う** (S-7)。前段の失敗は `other_error`。
   診断に `__has_include` の文字列が含まれるだけで `reject_condition_operator` と数えない。
   結果は「渡した fixture に対する拒否」と限定し、**「実 variant が resolver でこの拒否点へ
   到達した」とは書かない** (S-6、L-1)。
9. **JSON schema**: 段 2 プランの schema をそのまま使う。`cells.status` の列挙に
   `environment_unavailable` を含め、compute 未実行時に使う。

## 4. 変異事前登録 (`DW-M01`)

**変異 matrix は免除する。** 理由は `DW-S04` の「実装面 (D95 決定 2) の差分ゼロの wave だけ
変異 matrix を免除する」に該当するためである — 本 wave が段 9 で local main へ入れる実装面差分は
**ゼロ**である (probe は repo へ残さず、成果物は insight = docs のみ)。

**免除しないもの:**
- **受入全走は免除しない** (`DW-S04` 明記)。段 6 で実走し、結果を worklog へ書く。
- **probe の歯は対照で担保する。** 正・負・反転・抽出・guard の 5 対照が probe の壊れ方を
  検出する役目を負う。対照が不成立なら結論を出さない (上記 3-(7))。
  これは変異 matrix の代替ではなく、**一時 probe に対して取れる範囲の裏取り**である。
  この限界を成果物に明記する。

## 5. 成果物の主張範囲

**言ってよいこと:**
- 記録した compiler・argv・cwd・env・入力位置で、この式がこの値・この診断になった。
- 今日の login node pegasus02 で `g++-13` を探索し、不在だった。
- (compute で実行できた場合) `generic` の compute 環境で探索し、compiler がこうだった。
- 渡した fixture に対して、checker の実 guard 関数がこの箇所で拒否した。

**言ってはいけないこと:**
- stdin 列の一致をもって「実 build と一致」と読むこと (S-1)。
- 再構成列を admission の実 build 実測と呼ぶこと (S-3)。
- login の結果を compute の admission toolchain の結果へ読み替えること (L-反3)。
- `__has_include` 族一般、または別 compiler・別探索順への一般化 (L-3、`DW-G03`)。
- 「checker が blanket reject するから安全」と読める書き方 (L-1 の走査範囲外を隠す)。
- 4 種の観測を 1 つの「admission 実 pair 実測完了」へ畳むこと (L-整4)。
- 実 variant が resolver でこの拒否点へ到達した、と書くこと (S-6)。

**結果を見る前に「欠陥がある」と決めない。** 対照表が食い違いを示しても、それが
偽 cache hit や受理集合の破れへ到達するかは本 wave では未証明である。

## 6. scope 外の real 所見 (裁定パッケージ候補)

実装せず、段 7 で裁定パッケージとして記録し、ユーザーへ返す。

- **(R-1) legacy 分岐の compiler 引数の非対称。** `pipeline.py:1790` が site 選択した compiler を
  checker へ渡す一方、`common is None` の legacy 分岐 (`:2002`、`buildcache.py:3140`) は
  `cc/cxx` を渡さず既定 `g++-13` を使う。静的に確認できる非対称であり、到達可能性と
  既存防壁との関係の評価は別裁定。
- **(R-2) 走査範囲外の include 先の一般安全性。** `source_digest.py:85`/`:1895`/`:1662` の
  非再帰な走査境界は実在するが、そこから許可された variant が実際に別挙動・stock identity 継承へ
  到達するかは未証明。今回は安全性主張の除外範囲として記載するに留める。

## 7. 運用上の注意 (段 5・6 で踏む)

- **compute へ dispatch すると worktree に残骸が出る。** 裁定済み inbox
  `2026-08-13-t1027-probe-fingerprint-vs-dispatch-residue.md` が
  「計算ノードは同じ共有ファイルシステム上の probe worktree へ書くため、残骸が出る」と実測記録
  (`output/pegasus-dispatch/`、各種 `__pycache__`)。受入と land の前に clean tree を確認する。
- **main が wave 開始後に進んだ** (`7dc4ecc39` → `c2a28d67d`)。段 9 の land で取り込む。
- probe が未 commit のまま compute へ dispatch できるかは未検証。できなければその事実を記録し、
  probe を wave branch へ commit してから再試行する (実装面の一時 commit は wave branch 内に留め、
  段 9 の land 前に取り除く)。
