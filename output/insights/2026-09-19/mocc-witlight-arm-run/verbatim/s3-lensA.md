## 判定と検査範囲

**条件付き GO。W の逐語設計に、正常完走時の S の値・件数・照合を壊す欠陥は見つからない。** ただし、測定用合成 source の identity 保証範囲と、親 brief の成果物影響の定義は修正が必要。

以下、行番号の略記は次を指す。

- **B**: [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/s1-brief.md)
- **P**: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/codex/s2-plan.md)
- **F**: [operational-facts.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/operational-facts.md)
- **M**: [mocc-transaction-e9e477ca.cc](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/mocc-transaction-e9e477ca.cc)
- **R**: [t2779_probe-v5.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/t2779_probe-v5.py)
- **G**: [mocc_g2_discriminator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/orchestrator/campaign/mocc_g2_discriminator.py)

指定資料の読解に加え、P の W diff をメモリ内で適用して独立検算した。結果は以下。

- e9e477ca と W の include 列が一致。
- `#if TRACE` ブロックを除いた文字列が一致。
- 各 hunk の旧文脈が一意に存在。
- `modify(e9e477ca + X/P) == modify(e9e477ca) + X/P` が byte 一致。
- M に直接の `__LINE__` 使用なし。

**実 `git apply`、identity checker、build、測定は未実施。ファイル変更なし。**

## real — must-fix

**MF1：測定用合成 source の TRACE=0 identity は、予定された検査では確認されない。**

P:337–366 の検査対象は W の OID 比較、patch 適用、`#line` 除去後の同内容性、TRACE=1 build である。`e9e477ca + X/P + witlight.patch` の TRACE=0 binary 比較は入っていない。

OID checker は commit の source を読む（`check_trace0_preprocess_identity.py:528–529`）。一方、F:35 が挙げる既存 `_trace0_record` は、渡された二つの binary の `nm`・`strings`・正規化 objdump を比較する検査である（`s3_mocc_lock_coverage.py:444–470`）。**旧 X/P の検査結果は、新しい witlight 合成 source を自動では被覆しない。** R:543–578 にも、その比較を呼ぶ処理はない。

段4で親の責任として、次のいずれかを明記すること。

- 今回の合成 source に対する TRACE=0 比較を、対象 source・compiler・defines と束縛して実施する。
- 本 wave ではその比較を実施せず、**「測定用合成 source は TRACE=1 専用の観測 build。性能値には使用しない。W 単体の OID identity と合成 source の binary identity は別」**と明記する。

後者でも本観測の目的は満たせる。W の必須 identity 2本は省略しない。

**成果物影響：放置すると、W または旧 X/P の検査結果が新合成 binary の保証として過大に引用される。**

**MF2：B:18 の「非 certifying だから成果物影響なし」は DW-G05 の評価範囲を狭めすぎる。**

受理集合を変更しなくても、witness の欠落・束縛誤り・結論の読み替えは、B:3 が成果物とする k/m、識別件数、insight の主張を変える。P:322–333 自身も、S の不一致が `contradicted` ではなく blocker になるという、成果物上の重要な区別を認めている。

「受理集合は変更しない」と「観測結果・主張への影響は所見ごとに評価する」に分けること。

**成果物影響：放置すると、認証に直結しない観測・解釈の欠陥が、影響なしとしてレビューから脱落する。**

## refuted — S 遅延の意味論

**R1：unlock 後の他 writer の上書きで、既に採取した S の値が変わる。**

この疑いは P の設計では反証される。

M:105 の共有 body decode を publish 直後の呼出側へ移し、その値を vector に保存する。unlock 後の helper は共有 record を読まず、保存値、ローカル `maxtid`、`write_set_` の key を使う。key は借用 view ではなく `std::string` 所有値である（`external/ccbench/include/op_element.hh:20`）。

helper の `<< "S "` 以下は不変であり、5値・区切り・改行は保存される。G:373–384 の mismatch／duplicate は identity と保存値を検査し、S の到着時刻を検査しない。G:580–620 の lineage 照合も全入力を読んだ後の identity lookup である。

ただし保証は、**同じ採取結果についての出力保存**である。計器変更前後の別実行で txid・採取値・G2 件数まで同一になるという保証ではない。

**成果物影響：正常完走・同じ採取結果という条件下では、出力遅延だけによる discriminator 結論の変更は認められない。**

**R2：L と S の間に E が入ることで witness parser が壊れる。**

E は標準 trace の stream（M:1204）、L/S は witness stream（M:47–60）。E が witness ファイルに混入する経路はない。

G:334–385 は H の先行を要求するが、L→S の時間順や transaction の閉じ位置は要求しない。同一 worker は遅延 S を書き終えてから次 transaction に進み、worker 間は別ファイルである。

**成果物影響：正常完走時の witness 行順変更による parse 失敗・照合変更は認められない。**

**R3：TLS vector の残留値が abort 後の transaction に混入する。**

通常の validation 失敗は `writePhase()` を呼ばない（M:1215–1221）。採取開始時に clear し、正常出力後にも clear する（P:95–97）。INSERT/DELETE は有効時にプロセス abort（M:1174–1183）、decode 失敗も同様であり、その後の transaction はない。

`reserve(write_set_.size())` 後、各完走要素に一度だけ push するため、当該ループ内での再確保は不要。unlock は `CLL_` を消すだけで、再走査前の `write_set_` は変更しない（M:1094–1113）。

**成果物影響：指定経路に残留混入は見つからない。ただし異常終了時の出力 prefix は変わるため、P:97 の限定は必須。**

**R4：再走査に INSERT/DELETE が含まれ、保存配列と対応しなくなる。**

witness on でそれらに到達すれば再走査前に abort する。正常完走する対象 workload の write は UPDATE で、`maxtid.epoch/tid` は共通。UPDATE が変更する `absent` は S の出力項目でもない（M:1163–1183）。

**成果物影響：正常完走時の一要素一保存・一 S の対応は維持される。**

## identity・測定 patch の検算

**W に `#line` が必須という疑いは refuted。**

`source_digest.py:1686–1687` は include を除去し、`-E -P -dD` で処理する。今回の W は include 列と TRACE 外の文字列が不変で、M に直接の `__LINE__` 使用もない。P:101–103 の限定付き説明は妥当である。

ただし、これは checker 通過の静的見込みであり、実ヘッダ展開後の命令列一致の証明ではない。`--old 511c9538` と `--old e9e477ca` の実行結果は未実測のまま残す。

**成果物影響：不要な `#line` を W に要求する根拠はない。未実行の checker を合格扱いしてはならない。**

**P2 の同内容性検査は、その限定された目的には十分。**

両辺に同じ X/P を適用するので、X/P の `<set>` 追加は両辺に残り、比較から除去されない。`#line 17` だけが指令除去の対象になる。私の独立メモリ検算でも、W と X/P の適用順は byte 一致した。

測定 patch の指令位置も整合する。

| 指令 | 復元する位置・条件 |
|---|---|
| `#line 115` | helper の行数減少後の元115行 |
| `#line 1136` | TRACE=1 の C 行。後続の既存 R/L/W 位置も戻る |
| X/P の `#line 1158` | TRACE=0 でも有効で、追加ブロック後を復元 |
| `#line 1201` | 採取部分後の write loop 閉じ括弧 |
| `#line 1208` | 遅延出力後の `RLL_.clear()` |

`#line` 除去比較だけでは指令の正しさを検証できないが、P:187 はその限界を明記しており、この点は欠陥ではない。

X/P 文脈を含む witlight hunk は、**固定された X/P を前提とする依存関係**である。R:547–554 は適用順と patch SHA を記録するが、`patch_files == [SOURCE]` 自体は内容同一性を検査しない。P:362–365 の逐次 apply と最終 byte 比較を実行して初めて確認が閉じる。

**成果物影響：計画どおり実検査すれば W と測定物の対応を示せる。touch set 検査だけを代用すると、その対応は未確認になる。**

pin=W＋runner v6 を採らない判断にも異議なし。今回の W に必然的な X/P 文脈衝突はないため B:9(a) は訂正対象だが、R:335–338 の pin 制限は実在する。既存 v5 と追加 patch の束縛で目的を達成する方針は成立する。

## real — should と観測の上限

**S1：off の保証は、P:105 の限定を最終 insight にも保持する。**

false 時に TLS vector の構築・clear・reserve・push・decode・S 出力を実行しないことは、逐語設計から成立する。一方、ポインタ初期化・分岐まで完全 dead とは言えない。

以下は**未実測**である。

- 旧 off binary に対する命令列・インライン化・配置の変化。
- TLS 領域や guard を含む binary 構造の変化。
- それらによる cache、分岐、スケジューリング、commit 曝露量への影響。
- 別々に build する今回の on/off binary の命令列同一性（R:568–578、P:265）。

**成果物影響：限定を落とすと、率差を「実行時 env だけの純粋な介入」と過大に解釈する。**

**S2：窓の短縮は処理構成の説明まで。短縮量・G2 到達改善は未実測。**

要素 j の publish から当該 lock 解放までには、j 以降の decode/push、後続要素の stamp・memcpy・X/P 検査・publish、E 出力、CLL の解放順が残る（M:1160–1207）。移動するのは主に S の stream 取得・hex 化・書式化・出力であり、窓が memcpy だけにはならない。

初回・容量増大時の reserve は publish 前でも write lock 保持中である。L 出力とともに他 transaction の abort や曝露量を変えうる。P:95 と T-2779:65–87 の限定は妥当。

**成果物影響：省略すると、陰性結果を「観測者効果なし」、陽性結果を「窓短縮の因果的実証」と読み違える。**

**S3：規律2/7の最終記述を具体化する。**

P:3、326–335 は verifier／discriminator／X/P 不変、識別の限定、非 certifying を保持している。次を成果物に明記すれば、T-2779:141–142 の書き方を踏襲できる。

> 個別 verifier の `certified=true` と arm 属性 `observational_only=false` は、本 wave・MOCC・軽量 witness の認証を意味しない。T-1892 5/42、T-1943 no-g2、T-2774、T-2779 は各旧束縛のまま保持する。

P:308 の旧結果との非合算も維持する。`supported` は先頭8 byte の producer 照合までであり、G:648–653 の writer version・store順・commit順・根因の未検証を越えない。

**成果物影響：省略すると、観測上の分類が認証や過去結果の再判定へ読み替えられる。**

**S4：P6 の方針は妥当。trailer 例は寄与者一覧の上限にしない。**

指定 branch、e9e477ca の子、親による fetch・bundle、既存 ref の非強制上書き、gitlink 据置きは P:470 と D16 に整合する。fetch に gitlink 更新は不要。

P:107–117 の author trailer は形式上妥当。ただし、採否・内容へ実質的に寄与した manager/reviewer 等も、`docs/ai-provenance.md:65–72` に従って記録する。e9e477ca の値を流用せず、表示されない属性は規約どおり扱う。

**成果物影響：author だけを固定テンプレートとして使うと、実質的寄与の provenance が欠落する。**

## nit — 親の運用事実の誤記

**N1：F:29 と依頼本文の「abort 経路の unlockCLL は1248」は誤り。**

M:1247–1253 は `reconnoiter_end()`。通常の `abort()` は M:1059、unlock は M:1069 である。`commit()` の失敗分岐は M:1220 の `return false`。

**成果物影響：今回の TLS 生存期間の結論は変わらないため nit。ただし誤った abort 被覆の引用は修正する。**

**N2：行番号の軽微なずれ。**

R の `patch_files(...) != [SOURCE]` は548行、549行は例外送出。実行順序の説明は正しい。

**成果物影響：値・主張・受理集合の変化なし。参照精度のみ。**

## 総括

**判定：条件付き GO。** W の実装着手は可能。正常完走時の観測意味論に blocking defect は見つからない。成果物確定までに次を修正し、P§7 の未実行検査を完了すること。

**must-fix**

1. **MF1：合成 source の TRACE=0 identity の担当・検査、または TRACE=1 観測専用／性能利用不可を明記する。影響：identity 保証の過大引用を防ぐ。**
2. **MF2：B:18 の「成果物影響なし」を撤回し、観測値・識別結果・主張への影響も評価する。影響：非 certifying な成果物の欠陥を取りこぼさない。**

**should：** off binary の未実測範囲、窓短縮量の未実測、個別 `certified=true` の限定と旧束縛保持、実質的寄与者の trailer を明記する。

**nit：** abort の参照を M:1069 に訂正する。runner の条件式は548行。

**親 brief への異議：** P2(a) の文脈衝突は今回の W では再現しない。P3 の W に対する `#line` 必須説は成立しない。P4 は旧 off binary との実行同一性を含意しない。DW-G05 の「非 certifying ⇒ 成果物影響なし」は成立しない。
