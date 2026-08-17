## 所見

1. **P7 の発火条件は crafted receipt で抑止できる** `[恒真ゲート] [consumer 取り残し]`

   - **主張:** land は checker receipt 本体を読まず、outer receipt の `red_nodeids` / `flake_nodeids` を信じる。実際には flake だった node を `red_nodeids` へ移し、`flake_nodeids=[]` とした crafted v4 receipt なら runner 不一致検査を起動せず land できる。
   - **根拠:** land は root field 集合を検査するだけ (`tools/dev_wave_land.py:562-572`) で、`checker_receipt_sha256` は 64 桁形式しか見ない (`:671-685`)。checker 本体との等値確認は無い。現行テスト自身が synthetic outer receipt を生成し (`orchestrator/tests/test_dev_wave_land.py:216-273,424-446`)、それを land が受理することを正例化している (`:690-708,899-916`)。プランも runner 不一致の red-only を受理する正例を登録している (`s2b-plan.md:76-81`)。
   - **倒れる向き:** 待ち手を通した正直な `flake_nodeids != []` と runner 不一致は waiter・land の二層で拒否されるので、その狭い攻撃は refuted。v3 receipt も v4 exact parser で拒否される。一方、待ち手を飛ばして分類を red-only に偽装する経路は real。F366 の「全 consumer を通す」を満たしても、分類の独立な値源が無いため F314 型の自己照合になる (`docs/failures.md:7970-7986,9100-9125`)。
   - **推奨対応:** P7 を `flake_nodeids` 自己申告で条件分岐させない。少なくとも全 `non-attributable-only`、本来は T-1283 どおり全受理経路で runner を main 側へ束縛する。加えて land が分類を main-bound checker の実 receipt bytes から再導出できる authority を設ける。負例として「runner 不一致＋実際は flake＋outer では red-only」を必ず reject させる。

2. **同じ runner blob でも main と tip の挙動は大きく異なりうる** `[計測汚染] [テスト代表性]`

   - **主張:** P7 が保証するのは `tools/run_tests.py` 一ファイルの Git blob 等値だけであり、対象 node の実行や pytest の意味論は保証しない。
   - **根拠:** checker は各 worktree の runner を、その worktree を cwd にして起動する (`tools/check_acceptance_reds.py:956-982`)。runner は各 tree の `orchestrator.campaign.site_policy` を import し (`tools/run_tests.py:53-58`)、`tools.pegasus.dispatch_compute` も動的 import する (`:940-950`)。pytest は各 tree を cwd に実行される (`:1907-1916`)。さらに rc=1 だけ FAILED/ERROR の証明を要求し、rc=0 では対象 node の実行証明が無い (`tools/check_acceptance_reds.py:983-994`)。
   - **倒れる向き:** 例えば tip の既存 test または `conftest.py` を「full-suite argv では失敗、`::nodeid` 指定では pass/skip」にすると、初回全走は決定的に赤、main 単独は緑、tip 単独も緑となる。runner blob は同じまま flake として land する。環境面でも waiter が拒否するのは `PYTEST_ADDOPTS` / `PYTEST_PLUGINS` だけ (`tools/dev_wave_wait.py:1808-1841`) だが、checker は `PYTEST_DISABLE_PLUGIN_AUTOLOAD` なども消す (`tools/check_acceptance_reds.py:55-61,709-716`)。初回と再走の意味論は揃っていない。
   - **推奨対応:** rc=0 に、main-bound plugin が出す「exact node が call phase まで実行され PASSED した」receipt を要求する。初回と再走の argv・pytest 選択環境・scheduler を同形にする。runner の import/dispatch 閉包を束縛できないなら、P7 の保証範囲へ明記し、「wave-controlled runner を束縛した」と一般化しない。

3. **P5 は具体的反例を覆っているが、覆うこと自体が規律 2 と既裁定に衝突する** `[恒真ゲート] [検査を消して緑を買う]`

   - **主張:** P5 は `conftest.py`、test、自動 plugin、argv・環境差、決定的な全走限定赤まで明示受容しており、上記構成を記述上は覆う。しかし、これは残余の説明ではなく「full acceptance が決定的に赤い commit を land 可能にする」という新しい受理集合である。
   - **根拠:** brief は決定的な赤も通ると明記する (`brief.md:73-79`)。一方 T-1278 のユーザー裁定は「走行形で結果が変わるテストは正しさシグナルに使えない。揃える」とする (`docs/worklog.md:2909-2911`)。絶対規律 2 と、赤を通すため production gate を外した F116/F162 の恒久対応にも反する (`CLAUDE.md:55-59`, `docs/failures.md:3808-3829,4858-4873`)。
   - **倒れる向き:** この拡大は本 wave 以前には waiter の node exact 検査で拒否されていたため、新設される real な land 経路である。P5 が漏らしているのは crafted receipt、runner の transitive import、Python 実行体/PATH、rc=0 の未実行である。
   - **推奨対応:** P5 をこのまま「明示受容」で確定せず、T-1278 と R2 の優先関係を親裁定へ戻す。決定的な full-suite 赤を除くには、少なくとも同一 tip を同一 full-suite 形で再走し、その全走が緑になった場合だけ flake とする。単独走だけで full-suite 赤を免除しない。

4. **P7 の「初の wave-runner rc=0 経路」という前提は偽で、T-1302 内ではほぼ恒真である** `[恒真ゲート] [手順漏れ]`

   - **主張:** child-green は既に wave 側 runner の rc=0 を受理証拠にしている。したがって brief の「flake が初の経路」は誤りである。また本 wave の scope は runner 非変更なので、適法な T-1302 差分では P7 は常に等値となる。
   - **根拠:** 初回受入は wave cwd で command を実行し (`tools/dev_wave_wait.py:3137-3144`)、rc=0 なら checker 無しで child-green になる (`:3177-3191`)。land の child-green は runner の存在だけを確認し、main/tip 等値を要求しない (`tools/dev_wave_land.py:659-669,700-705`)。これに反して brief は P7 を「初の経路」「受理集合を狭める補償」とする (`brief.md:84-89`)。scope は runner 全経路束縛を明示的に外す (`:17-18`)。
   - **倒れる向き:** runner を直接変えた将来 wave または scope 違反に対して P7 は発火するので、repo 全入力に対する恒真ゲートではない。ただし本 wave の新しい受理拡大を実測上 narrow する gate ではなく、将来 drift への防御深度である。F143/F280 型の過大な単調性主張に当たる (`docs/failures.md:4337-4350,7297-7310`)。
   - **推奨対応:** 文面を「flake 経路に追加する将来・scope 違反向け防御深度」へ修正する。規律 2 の補償として扱うなら、既裁定 T-1283 の waiter・runner 全経路 main binding (`docs/worklog.md:2920-2922`) を先に実装する。

5. **正当な runner wave に対する過剰拒否は遅く、高価で、R2 の空費を再現する** `[受理集合の過剰縮小] [計測汚染]`

   - **主張:** runner を正当に変更した wave で偶発 flake が一件でも出ると、P7 は full acceptance と main/tip 単独再走を全て終えた後に拒否する。再試行で child-green を待つ構造になる。
   - **根拠:** full acceptance 一本の既知費用は 1055〜1273 秒＋queue (`brief.md:111-116`)。各 node は main、必要なら tip の順で再走される (`tools/check_acceptance_reds.py:1354-1396`)。実測コマンド `git log --since=2026-08-01 --format=%H -- tools/run_tests.py` は 17 日間に 12 commit、全史で 20 commit を返し、runner 変更は稀ではない。
   - **倒れる向き:** flake 確率を `p` とすれば、成功までの廃棄走行期待値は `p/(1-p)`。決定的な run-shape 赤なら永久に land できない。T-1283 で runner binding の代償自体は受容済みだが、P7 には早期停止や bootstrap 導線が無い。F161 の正当入力過剰拒否、F367 の runner 自壊型に近い (`docs/failures.md:4838-4856,9127-9145`)。
   - **推奨対応:** runner blob 不一致を full acceptance 前に検出し、通常窓へ投入しない。T-1283 用の main-bound runner bootstrap 経路へ明示的に振り分け、flake 判明後まで待って高価に拒否しない。

6. **現 producer では発火不能な述語が P4 以外にもある** `[恒真ゲート]`

   - **主張:** 非帰属 rc pin、flake の三 rc pin、和集合非空、sorted・unique・disjoint、node exact field は、現 checker が正常に生成した `non-attributable-only` receipt に対して拒否を起こせない。
   - **根拠:** rerun rc は事前に `{0,1}` へ限定される (`tools/check_acceptance_reds.py:1264-1269`)。main rc=1 は非帰属、main rc=0 かつ wave rc=1 は attributable、それ以外だけ flake になる (`:1379-1396,1555-1583`)。node は `sorted(nodeids)` から一件一分類で作られるため、値・順序・一意・排他・field 形が構造的に確定する。
   - **倒れる向き:** これらは crafted receipt と将来 producer drift には効くが、現 producer の narrowing ではない。プランと新 D は rc pin だけを防御深度と明記し (`s2b-plan.md:20,161-162`)、残りと P7 の T-1302 内恒真性を区別していない。
   - **推奨対応:** 新 D に述語ごとの表を置き、「現 producer narrowing」「crafted/drift 防御深度」「将来 wave narrowing」を分離する。防御深度テストを mutation の受理集合 kill と数えない。F143/F170 の再発条件である (`docs/failures.md:4337-4350,5019-5040`)。

7. **runtime consumer のコード閉包は一致するが、D393 の正本更新が一件漏れている** `[手順漏れ] [ドリフト]`

   - **主張:** 二 schema の runtime consumer 数について、プランの outer 一覧にコード上の取り残しは無い。ただし新 D は D371/D389 だけを部分改訂すると書き、schema v3 を決定した D393 を名指しで改訂していない。
   - **根拠:** D393 は今も v3 を決定事項としている (`docs/decisions.md:16627-16655`)。新 D 案の宣言は D371/D389 の部分改訂だけ (`s2b-plan.md:144-160`)。単に後段で v4 と書くだけでは、D393 の schema 文と二つの正本が残る。
   - **倒れる向き:** 実装は v4 exact parser で fail-closed になるが、docs は v3 と v4 の双方を現行決定として読める。F366/F370 の consumer 閉包は refuted、正本住所の手順漏れは real。
   - **推奨対応:** 新 D で D393 の schema-version 部分も明示的に改訂する。D393 本文を歴史記述として残すなら、「schema 値のみ新 D が supersede」と書く。

## 閉包の実測

- `dev-wave-acceptance-receipt/v3`: tracked repo 全体で **26 occurrence / 10 file**、live code・test は **4 occurrence / 3 file**。producer は `tools/dev_wave_wait.py:231,2619-2643`。runtime consumer は `tools/dev_wave_land.py` 一 fileで、共有 exact parser `:562-572`、本検証 `:608-753`、release-authority `:575-589`。call site は `:3023`、`:3392`、`:3427` の三箇所。test literal は `orchestrator/tests/test_dev_wave_wait.py:1758,8224`。プランの「live 4 hit、1 file・2入口・3 call site」と一致する。

- outer の `set(`/`==`: root exact field 集合は `tools/dev_wave_land.py:74-96,570`、schema 等値は `:632`、fingerprint と環境の exact 集合は `:595,648`。land fixture は schema を定数参照するため literal grep に出ないが、`orchestrator/tests/test_dev_wave_land.py:216-267` にあり、プランは捕捉済み。

- `izanagi-acceptance-red-check/v1`: tracked repo 全体で **9 occurrence / 7 file**、live code・test は **5 occurrence / 3 file**。producer は `tools/check_acceptance_reds.py:22,1584-1607`。runtime consumer は `tools/dev_wave_wait.py:240,2720-2822` の一関数、一 call site `:3181`。test literal は `orchestrator/tests/test_dev_wave_wait.py:635,1216,2637`。追加 runtime consumer は無い。

- red receipt の exact 述語は root `tools/dev_wave_wait.py:2762-2783`、collection `:2766-2801`、node `:2803-2815`。producer の三 node 形は `orchestrator/tests/test_check_acceptance_reds.py:560-568,603-611,640-646` で literal pin 済み。プランは red schema の件数を明記していないが、変更対象の runtime 閉包には漏れがない。

- 初回の `rg` 出力は履歴中の巨大一行ログで truncated したため網羅根拠に使わず、上記件数は `git grep -o -F <literal> | wc -l` と `git grep -l -F <literal> | wc -l` で再計数した。F376 の truncated 閉包誤認を回避した (`docs/failures.md:9301-9314`)。

## 総括

最大の blocker は、P7 の発火条件が land で裏取りされない outer receipt の自己申告に依存する点である。  
同一 runner blob でも argv・環境・conftest・test・import 閉包により決定的な full-suite 赤を flake 化できる。  
P5 はその反例を記述上は覆うが、規律 2 と T-1278 の「走行形を揃える」裁定に衝突する。  
runtime consumer のコード一覧はプランどおりだが、新 D は D393 の v3 決定も明示改訂する必要がある。  
静的検査のみであり、pytest は実行していない。