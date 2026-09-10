## A-01 — P1: success 応答が path に束縛されていない

**severity:** blocker  
**判定:** real。P1 は refuted。`plan.md:93` は success record に query が含まれないことを認めつつ、後段照合が「必ず」順序入替を拒否するとしているが、これは成立しない。現行は path ごとに個別 query を発行する一方、plan は返された OID を expected path の OID と照合しない（`contract_loader_binding.py:343-345`, `plan.md:73-93`）。

反例は、commit blob が `A=x, B=y`、記録 digest が逆対応、batch 応答も `B,A` の順である場合である。plan の committed verifier は各 digest が一致して受理し得るが、正常な逐次版は A で拒否する。capture でも disk を `A=y, B=x` とすれば同じ誤受理が成立する。計画された逆順 test は正しい digest を使うため、この相殺ケースを検出しない（`plan.md:171-172`）。

**修正案:** 親実測の `ls-tree -r -z` で raw path→OID を exact に取得し、missing・extra・duplicate entry を拒否したうえで OID を batch query に使い、各 success header の OID を expected OID と照合する。要求順と重複は元 tuple から再構成する。完全に悪意ある `/usr/bin/git` まで脅威とするなら body の Git blob OID も再計算する必要があるため、そこまで信頼しないなら信頼境界を明記する。

## A-02 — 10 秒 timeout は同じ契約ではない

**severity:** blocker  
**判定:** real。現行の 10 秒は 62 個の各 subprocess に個別適用される（`contract_loader_binding.py:287-304`, `343-360`）。plan は全 62 blob の生成と転送を一つの process の 10 秒に収めるため、Lustre や 48 worker 競合で batch 全体だけが 10 秒を超えると、逐次版が受理する入力を `contract-loader-git-timeout:` で過剰拒否する（`plan.md:26`）。

親実測の direct batch は login で 0.618〜1.566 秒だが、計算ノードの 48 worker 条件は未測定である（`parent-measurements.md:10,20-21`）。したがって十分という実測根拠にはならない。

**修正案:** timeout を受理集合外の運用契約として変更する裁定を得るか、計算ノード同時負荷で分布を測り、明示的な aggregate timeout を定める。`62 * 10` への単純拡張も先頭 stall の拒否時刻を変えるため、厳密な時間的同値は `subprocess.run` 一回では表現できない。

## A-03 — 例外 prefix の順序と NUL 例外が変わる

**severity:** blocker  
**判定:** real。plan は全 path を subprocess 前に検査する（`plan.md:41`）が、現行は各 path の blob・digest・disk 判定と path 検査を逐次交互に行う（`contract_loader_binding.py:343-345,396-420`）。例えば `relative_paths=(先頭 digest mismatch, 後続 "../escape")` は、現行では `contract-loader-blob-mismatch:`、plan では先に `contract-loader-path-escape:` となる。

また embedded NUL は現行 `_run_git` の捕捉対象に `ValueError` がないため、静的には subprocess の raw `ValueError` が外へ出る（`contract_loader_binding.py:301-308`）。これを `ContractLoaderBindingError("contract-loader-git-error: ...")` にする plan の「同じ種類・prefix」という説明は誤りである（`plan.md:61`）。

**修正案:** 最初の invalid path と例外を事前に記録し、その手前の valid prefix を batch 検査してから保存した例外を送出する。NUL の例外正規化は安全側だが契約変更なので、同値要件から除外する明示裁定か、現行挙動を固定する必要がある。

## A-04 — 親の 12〜15 秒推定は plan の方式を測っていない

**severity:** should-fix  
**判定:** real。親の予測は `ls-tree + OID batch` の 0.071〜0.091 秒を使うが、plan が採るのは 0.618〜1.566 秒だった direct path batch である（`parent-measurements.md:10-20`, `plan.md:45-57`）。同 test は binding 検査を約 10 回行うため、差は無視できない。

さらに fast path の完全な capture には `_validated_root` と `_head_commit` の二つの rev-parse があるので、`ls-tree + cat-file` を足すと 4 process であり、親の「3 process」推定は一つ不足する（`contract_loader_binding.py:97-130,318-326,348-352`）。

**修正案:** direct batch の実測値で予測を更新するか、A-01 の path→OID 束縛を満たす fast path を正式な plan にする。

## A-05 — parser 負例と順序負例の test 計画が不足する

**severity:** should-fix  
**判定:** real。計画には truncated、大小 size、record LF、extra output、ambiguous、tree があるが、明示された攻撃面の負数・非数字 size、unknown status の `dangling`、malformed field 数、空 blob、submodule、symlink、同一 path 二回を固定していない（`plan.md:148-181`）。`* ? [ :` を含む path も未検査である。

逆順 test は、正常な記録 digest に対する拒否だけで A-01 の相殺反例を通す。また public verifier を使う場合、`_validated_root` と `_require_commit` を通過した後、本当に `cat-file --batch -z` fake へ到達したことを示す marker・exact argv assert が計画に書かれていない（`plan.md:171-175`）。

**修正案:** raw bytes を実装 helper とは独立に組み立て、各 malformed 分岐の exact prefix を検査する。逆順 test は digest または disk も同じ permutation にして、それでも拒否することを要求する。`ls-tree` を採る場合は `:(literal)`、raw NUL path、missing・extra・duplicate entry も追加する。

## A-06 — テスト全体が逐次版でも恒真になる懸念

**severity:** nit  
**判定:** refuted。個々の missing、digest mismatch、drift test は逐次版でも通るが、計画全体には `_blob` が exact 一回の batch query を使う検査と、root 検査を固定した capture が exact 二回の Git call だけを行う検査がある（`plan.md:153-154,180-205`）。旧逐次版は後者で 63 call となるため区別される。

期待 digest も独立計算すると明記されており、現行出力の自己焼き込みは避けられている（`plan.md:181,187-193`）。ただし A-05 の fake record を実装側 encoder で作らないことは明文化すべきである。これは静的判断で、test は実走していない。

## A-07 — 通常 Git での object・framing 境界

**severity:** nit  
**判定:** refuted。ただし親実測は現行 62 path がすべて mode 100644/blob の場合だけであり、以下は Git protocol と plan の静的比較である（`parent-measurements.md:4,15`）。

| ケース | 現行と direct batch plan の境界 |
|---|---|
| path 不在 | 現行 nonzero、plan `missing`。同じ `contract-loader-git-error:` |
| directory/tree | 現行 `cat-file blob` 型不一致、plan `type != blob`。同じ拒否方向 |
| submodule 160000 | object type commit のため同じ拒否方向 |
| symlink 120000 | object 自体は blob なので committed 検査は双方受理。capture/live は disk の非 regular 判定で拒否（`contract_loader_binding.py:191-197`） |
| empty blob | size 0 と protocol LF を分離すれば双方受理 |
| blob 末尾 LF なし | size 内 body と後続 protocol LF を分離する plan なので双方受理 |
| size 不一致・途中 EOF・余剰 | `plan.md:82-91` は fail-closed。解析不能から受理へ進む記載はない |

plan 自体は `ls-tree` を使わないため、pathspec magic、C quote、8 進 escape は planned branch には入らない。fast path へ変更するなら、`-z` 出力を decode/unquoteせず raw path と照合し、mode 100644 だけに狭めないことが必要である。100755 や 120000 の blob を mode だけで拒否すると committed の受理集合が狭まる。

## A-08 — spawn site、env 隔離、harden 引数

**severity:** nit  
**判定:** refuted。現行の `subprocess.run` は `_run_git` の一箇所だけで、絶対 `/usr/bin/git`、ambient Git env 拒否、限定 env、`GIT_NO_REPLACE_OBJECTS`、argv の `--no-replace-objects`、timeout が同じ呼び出しに集約されている（`contract_loader_binding.py:251-315`）。

plan はその同じ呼び出しへ `input=input_bytes` だけを追加し、新 wrapper を作らない（`plan.md:11-24`）。したがって静的には隔離の脱落経路はない。timeout の意味の変化だけは A-02 の blocker である。

## A-09 — drift 非対称、exact closure、既裁定

**severity:** nit  
**判定:** refuted。capture は blob→disk→digest、live は blob digest→disk、committed は blob digest のみ、という非対称が明示的に維持されている（`plan.md:97-114`; 現行 `contract_loader_binding.py:348-420`）。clean input では capture/live の全 62 path が disk reader を通る。

closure は exact 62 tuple のまま変更しない計画であり、対象 file 自身も entry に含まれる（`campaign_lock.py:49-112`, 特に `:68`; `plan.md:5`）。D1712 の所有 test 限定は `plan.md:209-227`、D1139 が残した commit/digest・disk 自己整合は `rulings.md:27-35`、D1388 の live resume 非緩和は `rulings.md:104-119` と整合する。D1728 の collection 面には変更がない。

## A-10 — P2: capture 後の verify_live は無条件には冗長でない

**severity:** should-fix  
**判定:** real。P2 は refuted。状態が不変なら、capture の HEAD blob==disk と記録 digest 計算により、直後の live 検査は論理的に重複する（`contract_loader_binding.py:348-383`）。  
しかし両呼び出しの間に disk が変化、記録 commit object が消失・破損、または repository が差し替われば、verify_live の `_require_commit`、digest、disk 分岐が拒否する一方、省略版は binding を返す（`ident.py:280-290`）。  
**修正案:** この wave では計画どおり残す。親 brief の主張は「repository と disk が不変という前提下だけ冗長」と訂正する。

## A-11 — P3: `(root, commit, path)` memo は content addressing だけでは安全でない

**severity:** should-fix  
**判定:** real。P3 は refuted。`--no-replace-objects` は replace ref を止めるが、同一 root path での repository 再作成、object の prune・破損、`.git/objects/info/alternates` の変更、object availability の変化までは固定しない（`contract_loader_binding.py:19-45,275-299`）。  
memo は、本来 Git error となる後続検査で古い bytes を返し、例外再現と fail-closed を壊し得る。content addressing が保証するのは健全で不変な object store 内の同一 OID の内容であり、root identity や可用性ではない。  
**修正案:** plan どおり memo を導入しない。将来採るなら repository/object-store identity と cache lifetime を別途束縛する必要がある。

## A-12 — P4: 計算ノードでも同じ原因か

**severity:** nit  
**判定:** refuted。ただし原因仮説が偽と判明したのではなく、成立済みの主張としては未立証という意味である。login profile の 704 spawn、36.4 秒は強い傍証だが、48 worker 条件は測っていない（`parent-measurements.md:16-21`）。  
plan はこれを未確定と扱い、同一 node A/B と受入の wall・module W を要求しているため適切である（`plan.md:207,240-241`）。実走前に改善済みとは扱えない。

## 総括

blocker 3 件、should-fix 4 件。pytest・性能測定は実走していない。  
最重要 1: success record を expected path/OID に束縛しないため、順序入替と逆対応 digest/disk が相殺して誤受理できる。  
最重要 2: 10 秒を per-path から aggregate へ変えるため、計算ノード遅延時の受理集合が狭まる。  
最重要 3: 全 path 事前検査と NUL 正規化により、例外種・message prefix の優先順位が現行と一致しない。