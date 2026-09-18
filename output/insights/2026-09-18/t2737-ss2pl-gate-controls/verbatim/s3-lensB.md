**44 cell 案は原因の切り分けには使えますが、そのまま「D2120 項12を満たした再提示材料」とはできません。** 特に、KIND の非 inert 比較から T+ を落とすと、companion だけを変えた対照がなくなります。以下の修正後に計算ノードへ進める判断です。

参照略号：`B=s1-brief.md`、`L=s2-plan.md`、`G=orchestrator/campaign/condition_meaning_gate.py`、`R=tools/pegasus/run_ss2pl_lock_study.py`、`P=patches/ss2pl-lock-protocol-study.patch`、`D=tools/pegasus/dispatch_compute.py`。B/L は指定された job dir 内の資料です。本検査は静的読解のみで、ファイル変更・前処理・build・pytest は実施していません。

**1. 分類：裁定充足 — real：44 cell では KIND の固定 target 対照が欠ける**

根拠：L:240 は **T+ と T− の非 KIND 3軸**を重複としています。親案が落とす T+/phase1 の KIND はこれに該当しません。O は YCSB、T+ は TPCC で、YCSB には専用 define が付くため、O と T+ は同一比較ではありません（P:49–51）。revS ではその define が abort・legacy 宣言の経路も分けます（L:92–105、125）。

**放置時の影響：** KIND の結果差を companion の有無に帰属すると、target と workload 条件の差が混入します。

是正案：**revS/T+/phase1/KIND を1 cell 追加し、45 cell**にする。既存の revS/T−/phase1/KIND と固定 target の対にする。この追加組は1軸だけなので、4軸 admission は作らない。family 全体が必要なら4軸追加して48 cellとする。

また、revS/T−/S が通り、revS/O/phase1 が通っても、登録簿が異なる。stock の YCSB target 不在は残ります（G:1781–1811、stock `cc/ss2pl/CMakeLists.txt:1`）。D2120 逐語:5–11 に対しては「成立範囲と残る不足」の材料であり、要求された比較の全面成立とは書けません。TPCC への target 変更の採用も先取りしないこと。

**2. 分類：表 — real：revS に合わせた予測表と変更層の対応表が必要**

根拠：L:202–216、347、380–383 は「8変更群だけなので S は mismatch」という旧試作の記述です。親の revS 案とは一致しません。G:1900–1920、2256–2284、2619–2709 の順序から、revS が実際に S の bytes 一致と非 inert の閉包固定を達成した場合の予測は次になります。

軸順は IMPL / KIND / DLR / WFG。`I` は stock inert の green（完全一致または gate が認める root-location-only）、他の記号は L:206–214 と同じです。

| warm 後 | S | phase1 |
|---|---|---|
| 現行/O | O / C / O / O | D / E / A / D |
| 現行/T− | M / M / M / M | 今回未実施 |
| revS/O | O / C / O / O | E / E / E / E |
| revS/T+ | I / C / I / I | 追加 KIND は E |
| revS/T− | I / I / I / I | E / B / E / E |
| abort 無条件版/T− | M / M / M / M | 今回未実施 |

pristine の現行/O/phase1 と revS/T−/S は、configure 等が成功すれば全軸 `preprocess-failed`。要求側で先に止まるので、pristine receipt 単独では stock 側前処理まで実行した証拠にはなりません。

**放置時の影響：** revS の成功が「予測外」と扱われ、必要な変更層と abort 対照の因果が読み取れなくなります。

是正案：上表を**条件付き予測**として更新し、変更層を以下に分ける。

- inert：patch の bytes 復元＋登録簿 target 変更。KIND は companion 除去も必要。
- IMPL：stock/study header とその依存 include の閉包固定。
- WFG：**owner の `ss2pl_wfg.hh` include 無条件化が閉包差を閉じる変更**。`wfg.cc` 無条件 compile は build graph 側の変更であり、それだけでは owner の閉包差は閉じない（G:2263–2305、P:1340–1342）。
- DLR：marker 固定が argv 差を閉じ、分岐の `SS2PL_DLR` 化が効果を保つ。
- KIND：companion ありでは既に green。今回直す drift はない。

採否を記さない表の構造自体は L:375–385 で適切です。

**3. 分類：runner 契約 — real：inert witness への波及説明が欠ける。ただし「即 red」は refuted**

根拠：R:89–103 は bomb・transaction・util を宣言済み差分とします。revS が transaction や bomb の token 差まで消すと、`observed_differences_match_declaration` は false になり得ます（R:1860–1896）。しかし validator はその false が実体と整合することを検査し、false 自体を拒否しません（R:1735–1747）。`_inert_witness_claim` も観測を acceptance gate としていません（R:1664–1678）。

**放置時の影響：** runner が新たに拒否するという誤説明、または既存の宣言表が試作に合わなくなる事実の欠落になります。

是正案：「未実走。宣言との完全一致フラグが false になり得るが、それ自体は契約例外ではない」と材料に追加する。gate の bytes 比較と witness の token 比較も区別する。witness は同じ compile command で patch を外して比較するため、別木の gate 比較結果から値を断定しない（R:1805–1857）。

**4. 分類：運用 — real：pristine staging の保存と実験用複製が具体化されていない**

根拠：L:261–280 は専用 staging と実行順を指定しますが、原本を保持する複製手順がありません。masstree は source dir で bootstrap/configure/make を実行します（`external/ccbench/cmake/ThirdParty.cmake:58–79`）。

**放置時の影響：** login precheck・再投入・別 job による生成物が混ざると、warm-up の前後差という証拠が失われます。

是正案：保存用 pristine から、attempt 固有の staging を `cp -a` で複製する。**複製した同じ staging**で pristine 8 cell→warm-up→対応する warm cell を取り、stock/current/revS の source 木も途中で替えない。前後で絶対 realpath、config.h の有無と生成後 hash、対応 cell ID を保存する。

warm-up が stock にも効く仕組みは妥当です。各 configure の `FETCHCONTENT_SOURCE_DIR_MASSTREE` が同じ実体を指せば、同じ生成済み config.h を読みます。configure argv/cache でその同一性を確認してください。

**5. 分類：運用 — real：clean env 下の一時領域・出力先の確認が不足**

根拠：D:349–360 の clean env に `TMPDIR` はありません。G:1875 は保存先未指定の `TemporaryDirectory` を使います。D:1082–1135 は dispatch の submission directory を read-only にする隔離を行います。probe の cwd は投入 worktree です（D:1660–1674）。

**放置時の影響：** 容量不足や出力先の権限エラーで、cell の結果ではなく基盤エラーだけが残ります。

是正案：compute 起動時に次を記録する。

- `tempfile.gettempdir()` の実効値、空き容量・inode。通常は `/tmp`。
- job dir 内の scratch・staging・receipt 出力先が書けること。dispatch submission directory とは分ける。
- probe・依存・patch の絶対 path、`c++` と `cmake` の realpath/version。
- login の `g++` と compute の `c++` の対応。login の `cmp` は compute の gate 判定を代替しない。

`TemporaryDirectory` は固有名を作るので、prefix 共通だけによる名前衝突は **refuted**。並行 job との主な共有リスクは容量と、固定名の staging/output です。generic child の stdout/stderr は PBS ログ側へ継承され、probe の結果 JSON が自動生成されるわけではありません（D:1131–1143、1715–1735）。

**6. 分類：運用 — real：打切り優先順位が実行順へ反映されていない**

根拠：L:305–315 では plain build と abort 対照が全主 cell の後です。一方 L:322 はそれらを優先するとしています。G:1600–1610 の120秒制限は subprocess ごとの制限で、job 全体の時間保証ではありません。

**放置時の影響：** 重複 cell を先に消化し、重要な stock 前後対・abort 対照・build 証拠が未完で終わります。

是正案：pristine 8 cell の後、warm-up、対応 warm 8 cell、KIND 固定 target 対、abort 対照、plain build を先に配置し、残りを後段へ回す。cell ごとの `try/except/finally` と atomic 保存を必須にし、予算による未実施と内部例外を gate red から分ける。L:274、318 の意図を実装契約に落とす修正です。

独立検算では、44 cell は **36 warm＋8 pristine**。最大88 configure、前処理は上記予測どおりの早期停止なら約62回です。既に1 cell＝1軸なので、さらに4倍しません。plan の仮定5–20秒/cellなら220–880秒、準備・build等を1–2分として**約5–17分**。45 cellでもほぼ同じです。40分枠は合理的ですが、未計測の staging コピーと診断再実行を含む保証にはなりません。

**7. 分類：再発 — real：hostname が同じ最新 receipt は今回の PBS_JOBID を保証しない**

根拠：L:259 が再利用する前 wave `verbatim/probe.md:101–120` は、同一 hostname の receipt を mtime で選びます。generic の clean env には `PBS_JOBID` がなく（D:349–360）、同じ node の別 job を選ぶ余地があります。dispatcher 自身は今回の ID を marker/result に保存します（D:887–890、1688–1700）。

**放置時の影響：** cell receipt が別 job に結び付き、1 job 内の対照という来歴が誤ります。

是正案：hostname fallback は「候補」として扱い、投入 attempt と対応する dispatch の request/result/compute-visible receipt で最終照合する。照合できない間は unknown とし、最新候補を確定 ID にしない。

**8. 分類：再発 — real：configure-failed の全文診断が残らない**

根拠：G:1617–1628 は rc=0 でも stderr 非空を失敗とし、stderr は末尾500 byteだけを detail に残します。L:301 の canonical JSON 保存だけでは全文を回収できません。

**放置時の影響：** companion 未使用警告、CMake の警告、別の configure 障害を区別できず、予測表の C の根拠が弱くなります。

是正案：CMake の実体/version を保存し、configure 失敗時には同じ引数・入力状態による**別の診断 configure**の stdout/stderr を全文保存する。診断再実行と gate の原判定は明確に分け、原判定を置換しない。特定版で deprecation 警告が実際に出ることは今回未確認です。

path の `wfg` 回避と probe/production 差の明記は L:265、305–310、385 で対策済み。ここは新たな real 所見なしです。

**9. 分類：runner 契約 — refuted：既知の3契約について plan の読みは正しい**

根拠：

- abort の `#if` は token 走査から増分を隠さない。復元版は transaction=1 と数えられて拒否される（R:1049–1085）。L:132–143 は明記済み。
- raw study header 自体を走査するが、それは宣言名の抽出。raw header に名前があることを S の漏出とは判定しない。漏出は前処理済み TU を baseline 校正後に調べる（R:1334–1348、1492–1655）。
- `CACHE_TO_DEFINE` と `_validate_compile_definitions` に DLR marker と軸値の意味的整合検査はない（R:58–67、911–931）。

**放置時の影響：** plan どおり説明すれば誤認は生じません。

是正案：これらは維持する。login では raw source の所有権検査、header 宣言抽出、既存 compile-entry の define 検査、保存済み evidence の validator を pure-Python として実行可能。ただし evidence の取得に必要な前処理や build まで pure-Python 成功として報告しない。

**10. 分類：shadow — refuted：型混在・相対 import・patch root は対策済み。real 所見ゼロ**

根拠：L:151–183 は package 配下の固有 module 名、実行前の `sys.modules` 登録、同一 module での record 生成を指定しています。相対 import は G:50–52、patch root は G:2196–2198、exact-type 拒否は G:4081–4087 と整合します。

**放置時の影響：** plan どおりなら、別 class 混在による `admission-contract-invalid` は回避できます。

是正案：仕様変更不要。module identity、package、patch 解決先を receipt に残す検査を削らない。shadow 間で record を流用しない。

**11. 分類：scope — refuted：計画上の本改修混入はない。real 所見ゼロ**

根拠：B:31–48、L:151–183 は試作と shadow を repo 外に置き、本改修を対象外としています。revS の stock 経路復元も試作の範囲で説明可能です。

**放置時の影響：** この境界を維持すれば、採否未決の変更が production 実装へ混入しません。

是正案：revS の追加 hunk と復元条件を明示し、KIND を IMPL=0 で人工的に効かせる変更を足さない。S の `cmp` だけで変更の妥当性を認定せず、非 inert 側の既存 lock 処理を保ったことも diff で確認する。

## 総括

- **real 所見8件**。shadow・scope は real 所見ゼロ。
- 最重要は、44 cell から落ちた **revS/T+/phase1/KIND**。固定 target の companion 対として追加し、45 cellを推奨。
- 44 cell＝36 warm＋8 pristine。45 cellの総所要も暫定約5–17分、診断余裕込みで20分程度を想定するが未実測。
- walltime 00:40:00 は合理的。全完了の保証にはせず、重要対照を先行させる。
- **現 plan のままの投入は止め、予測表・実行順・staging・来歴保存を修正後に続行してよい。**
- 成功しても、TPCC shadow の成立を production YCSB 比較の成立とは書かない。
- 予算切れ時は、warm-up が除いた拒否、patch が除いた drift、target/companion/runner に残る拒否を分け、未完測を明記する。