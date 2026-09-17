## 総括

- **must-fix 3件、nit 3件。確認できた事実誤りは4件**。
- 段3レンズAの未反映は0件。ただし **F3の転記誤り、F5の歴史的留保の現状への誤適用**がある。
- §0・§1・§5に「合格したので前進可能／承認済み」と読める断定はない。
- 候補差分・GCC report・分岐表の数値は一致。clang の比較未完了という分類も妥当。
- **「直接区間は本waveが初めて」は過去の生reportに反する。**
- 以下、`README`・`verbatim/` はレビュー対象ディレクトリ内、`checker` は `tools/check_trace0_preprocess_identity.py` を指す。再実走・書込みは行っていない。

## 1. 候補表・4 commit・来歴

数値 **+141、+31、+2 −1、+111、+7 −9**、日付、author／committer、trailerの要約、trace.hh blob `570e35e3…` は `candidate-commits.txt`・`candidate-diff.txt` と一致する。現pinのGitHub branch名2本も `github-ls-remote.txt` と一致する。gitlink前進・revertの日時も両commitの現物と一致した。

### A1：直接区間の「初実走」は誤り

- **所見：** README §2:59 の「本 wave が初めて実走した」は事実と異なる。
- **根拠：** `output/insights/2026-08-28_t1943-mocc-g2-discriminator/RESULT.md:12` が指す保存先の `raw-staging-0_956466.nqsv/trace0-preprocess-identity.json` を確認した。`old_oid=511c9538…`、`new_oid=e9e477ca…`、GCC 11.4、16 context、schema v2、`result=pass`。隣接する `.rc` は0。report SHA-256は `3bbda8db4596296ce45d0250607d15ed27837579419016aa7b74b7bf23d86079`。
- **分類：** 整合・実効性／**must-fix**。
- **是正案：** 59行を次に置換する。

> 区間別検査に加え、T-1943 の2026-08-28実走にも現pin→候補の直接区間のpass reportが残る。本waveでは現行checkerで直接区間を再検査した。過去実走はcompleted pilot receiptの公開に失敗しており、当時のreportの存在と正式な証拠化は区別する。

### A2：ref一覧の不在から取得不能まで断定している

- **所見：** §2:43・§5:184の取得不能断定は、保存された証拠より強い。特に「origin経由」は、このworktreeのlocal originを含めると不適切。
- **根拠：** `github-ls-remote.txt` が示すのは候補OIDを先端とするref・候補branchの不在。履歴内到達性やOID指定fetchの失敗は記録していない。一方、現物の `remote.origin.url` はprimary module storeで、`refs/remotes/origin/izanagi-t1943-mocc-g2-readfrom-witness` は候補OIDを指す。
- **分類：** 整合・実効性／**nit**。
- **是正案：**

> GitHubの広告ref一覧に候補OID・branchは無い。GitHubだけを取得元とするfresh cloneで候補を取得できることは未確認であり、移行前に人間による公開と取得確認を要する。このworktreeのoriginは候補を保持するlocal storeである。

## 2. §3.1のreport・索引との一致

**訂正必須の不一致はない。**

- rc、schema、16 context、compiler version、report各33,036 bytes、SHA-256先頭は保存物と一致。
- `include_line_count=10` は**old側のinclude総数**を記録するfield。活性marker数は別途old／newとも10である。new側include総数まで10という意味ではない。
- 全contextのpolicyは追加index 10・非活性・accepted。生marker列の一致も成立する。
- define mapは `BACK_OFF={0,1}` × `GLOBAL_VALUE_DEFINE`有無の4種。固定defineの列挙、正規化digest2種、活性digest `c0fdab05…` は一致。
- GCC両reportを構造比較すると、差はcompiler fieldだけだった。

§3.1:88の `b713e6ab…` はpolicyのgcc／g++両期待値と一致し、D1487の37 receiptという記録とも一致する。全文versionからの再計算は本レビューでは行っていない。末尾がtoolchain全体の同一性を明示的に否定しており、保証の言い過ぎはない。

## 3. §3.2の保証範囲・裁定との整合

「必要条件の一つ」、TU／binary／完全除去を証明しないこと、include特例、checkout依存、不在証明の限界は、checker冒頭および `source_digest.py:1567,1647` と整合する。

現物照合では、D774（`docs/decisions.md:29866`）は間接値を拒否しない方針、D780（`:30015`）はその据置、D986（`:34724`）は3穴の修理要求、`docs/phase3.md:1113` はT-1644据置を記す。READMEは全面閉塞を主張しておらず、この点は妥当。ただし、**D774はD986より前の日付であり、D774によってD986が後から緩和されたとは説明できない**。現状の留保を維持すべきである。

### A3：「reportはproof chain外」を現行一般の限界として書いている

- **所見：** §3.2:98はT-1584当時の状態を現行実装に一般化している。
- **根拠：** 現行 `tools/pegasus/mocc_trace_pilot.sh:1821` はreportをhash化、`:2871` は改変を照合、`:2905`付近でpath・sha256・schema・guaranteeを構成、`:3224`でreceiptへ格納、`:3360`以降でjob-resultへ転記する。D779・D813もこの束縛と旧値の測り直しを規定する。
- **分類：** 正しさ境界／**must-fix**。
- **是正案：**

> 本waveの単独実行reportはruns.jsonに保存した判断材料であり、計測pilotのreceipt／job-resultへ組み込んだ証拠ではない。T-1584当時のR1に対して、現行pilotにはreportのpath・SHA-256・schema・guaranteeを束縛する実装がある。今回の保存物だけで、その経路の実行を主張しない。

これは段3 F5の**反映漏れではなく、歴史的留保を無限定に転記した誤り**である。

## 4. 分岐被覆表の検算

候補blobを `git show` で確認した。表の出現数と両枝検査の判定は一致する。

| 指令 | 現物の出現数 | 両枝 |
|---|---:|---|
| `#if TRACE` | 8 | 否 |
| `#if ADD_ANALYSIS` | 17 | 否 |
| `#ifdef RWLOCK` | 15 | 否 |
| `#ifdef MQLOCK` | 11 | 否 |
| `#if TEMPERATURE_RESET_OPT` | 1 | 否 |
| `#if BACK_OFF` | 2 | 是 |

有効な `#else`・`#elif`・`#ifndef` はない。

### A4：GLOBAL_VALUE_DEFINEについて転記が誤っている

- **所見：** §3.2:112の「実供給define mapに残らず」「実効構成を増やさない」は、`GLOBAL_VALUE_DEFINE`まで含めると誤り。
- **根拠：** `trace0-gcc11.report.json`・gcc12 reportのoverlay contextには、old／newとも `GLOBAL_VALUE_DEFINE=1` がある。`checker:579`付近でowner definesにoverlayを追加する。README:87自身もこれによる4構成を記載している。段3 `consult-A.md` F3は、残るgenome軸とこのoverlayを区別していた。
- **分類：** 正しさ境界／**must-fix**。
- **是正案：** 112行を次に置換する。

> 残るgenome軸3種はmoccの実効define mapに残らず、異なる構成を増やさない。一方、GLOBAL_VALUE_DEFINEはoverlayとして追加され、define mapを2種から4種に増やす。ただし、このsourceには対応する条件指令がなく、今回のinclude非展開の正規化出力ではdigestを増やさない。

## 5. clang原因説明

**保存probeとの不一致はない。**

`clang-probe-empty.txt`／`one.txt` はともに405行で、末尾が空行から `int x;` に置き換わる。空入力はprefixにならない。GCCは423行／424行でprefixになる。`source_digest.py:1704`付近の拒否条件とも整合する。

README:79には「clangでの同一性は未確認」、:116には「候補の拒否ではない」と、必要な両方の限定がある。「候補の拒否」はここでは**候補差分の不一致による拒否ではない**という意味で読める。

なおprobeは列挙された簡略flagでの再現であり、実checkerのBUILD_FLAGS・context defines込みの出力を保存したものではない。その全argvでの末尾差の逐語確認は**未検証**。

## 6. §0・§1・§5の承認境界

**「前進可能」「承認済み」「合格したので進める」と読める断定はない。**

README:13・:31・:79・:181で判断材料と承認を分離している。§5の承認・clang未完了・較正流用はいずれも未決事項として記載されている。

候補のlocal保管という帰結も記載済み。ただし取得不能の断定はA2のとおり修正が必要。今回reportが計測receiptへ未組込みであるという境界は、A3の形で明確にすべきである。

## 7. 親の一般化・その他の現物検算

### A5：registered較正recordの総数が誤り

- **所見：** §4.3:155は「6件」としながら、内訳が2＋2＋2＋2＝8件になっている。
- **根拠：** `registered/*.json` の現物は8件。現pinのsilo／mocc／tictocが各2件、d706650のsiloが2件。旧pinの2件は `calibration-753f535a8d024727.json:40` と `calibration-94a4b79fa31bba3c.json:40`。`env_contract.py:261,274`にも両参照が残る。
- **分類：** 整合・実効性／**nit**。
- **是正案：**

> 既存較正recordは全8件。このうち現pinを含む文字列検索集合は6件で、別にd706650のsilo 2件を保持する。

§4.2:141の6件は文字列集合内の件数として正しい。§4.3:161の「6件」も同じ集合を指すと明記する。

### A6：「head_shaを読むconsumerは無い」は検証範囲が曖昧

- **所見：** §4.3:156の主旨である「現行pinとの直接一致検査ではない」は支持できるが、「読むconsumerは無い」は広すぎる。
- **根拠：** `orchestrator/campaign` 内に当該keyの直接参照は見つからない。一方、`calibration_verify.py:118` はschema validatorへrecord全体を渡し、`orchestrator/calibrator/schema_v2.py:404,410` は `head_sha` を受け取り40桁hexを検証する。間接consumerまで不存在とはいえない。
- **分類：** 整合・実効性／**nit**。
- **是正案：**

> 確認した環境契約の検証経路では、acquisitionのhead_shaはschema検証対象だが、CURRENT_PINとの等値照合には使われない。

d706650のsilo 2件が保持される先例は現物で確認できた。ただし、その保持は新pinへの較正流用の許可を意味せず、README:158・:165の留保は適切である。前回pin前進の23箇所・校正pin4件という要約も `fb5e74a17` のcommit本文と一致した。
