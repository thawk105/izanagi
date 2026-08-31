## 総括

T-1909 に D1195 実装残差はなく、T-1769 着地後に同内容を再掲した重複持ち越しとして閉じるべきである。ただし §5.1(i) の先行 freeze は T-1769 側の別残件として維持する。

## 所見

### 1. 識別子非依存の全件検索

- **主張:** 権威点からの逆到達閉包とは別の「outcome 非生成の導出・遮断機構」は見つからなかった。
- **根拠:** 実装は解析 root と top-level import 閉包を作り `orchestrator/campaign/p3_b4_wiring_probe.py:952-1022`、callee→caller の逆辺閉包を導出する `同:1099-1120`。その閉包以外に見えるものは、test の手書き期待 subset `orchestrator/tests/test_p3_b4_wiring_probe.py:323-335` と直接遮断負例9本 `同:353-408` だけであり、いずれも `_build_inventory` の入力や別の導出法ではない。
- **残差か否か:** 実装残差ではない。親の P1-4 に同意。ただし「別目録が皆無」ではなく、検査 oracle としての手書き subset は存在する。

### 2. D1195 と T-1909 の対応

- **主張:** D1195 は D1171 と逐語同一ではないが、要求する実装内容は同一である。
- **根拠:** D1171 は3権威点、逆到達閉包、非完全性、閲覧隔離の分担を規定する `docs/decisions.md:39081-39097`。D1195 は同じ逆閉包・非完全性を §5.1(ii) に再適用し、D1171 と別方式を併設しない理由まで明記する `docs/decisions.md:39847-39859`。採番上も T-1909 は先に `T:b4-nonsampling-probe` として割当済み `docs/spool/FOLDED.md:2734`、D1171 は T-1769 wave で採番 `同:2863-2864`、D1195 は後の rulings 採択で採番 `同:2901-2902`。
- **異なる面:** D1171 の方が3権威点と閲覧隔離の責務を具体化している。D1195 は「閉包外に経路が残りうることを明記」と言い直すが、D1171 が既に要求する非完全性開示の範囲内で、新しい実装面ではない。
- **残差か否か:** なし。

### 3. T-1909 が開いたままの理由

- **主張:** T-1769 が満たさなかった D1195 面ではなく、T-1909 の重複持ち越しである。
- **根拠:** 初出時の T-1909 は §5.1(ii) probe の設計・実装そのもの `docs/archive/worklog-phase3-0827-1008.md:893-895`。T-1769 着地後は sanctioned CLI が実在し、残りを §5.1(i) と明記する `docs/archive/worklog-phase3-0827-1044.md:743-748`。同じ版で T-1909 は既に説明なしの持ち越し `同:870`。その後 D1195 採択により同内容を再び「実装待ち」とした `docs/archive/worklog-phase3-0828-1054.md:908-911` が、次版では直ちに参照だけになる `docs/archive/worklog-phase3-0828-1055.md:833`。現在も T-1909 は参照のみ `docs/worklog.md:398`。
- **台帳全体:** `docs/worklog.md` と `docs/archive/` の T-1909 は105件中、実内容2件・参照持ち越し103件だった。新しい未充足面を記した第三の実内容はない。
- **残差か否か:** 台帳の閉鎖残差のみ。コード残差ではない。

### 4. 事前登録が未発効の理由

- **主張:** D1195 機構の不在ではなく、§5.1(i) の先行 freeze が未充足だからである。
- **根拠:** 本文は probe CLI が既に実在すると明記する `docs/phase3-b4-reflux-ablation-preregistration.md:184-185`。そのうえで、候補集合、exact command、証拠 path/hash、0件・複数件規則、記入者・レビュー者を別 commit で先に固定するまで記入禁止としている `同:171-188`。§10 も CLI と遮断機構の実在を確認した後 `同:750-758`、残る §5.1(i) freeze が対象 driver/軸の記入と発効を止めると明記する `同:759-762`。
- **補足:** 人間指名については後に D1266 の実装待ち裁定まで進んでいる `docs/archive/worklog-phase3-0829-1090.md:316-319` が、事前登録本文の freeze はまだ完了扱いになっていない。
- **残差か否か:** T-1909 の残差ではない。T-1769／§5.1(i) 側の別残件。

### 5. 閉包候補集合の陳腐化

- **主張:** 現在の解析集合は完全に固定された39 module のままではなく、top-level import の増加を追って43 module に増えている。しかし、関数内 lazy import と独立した後発 producer は落とす。
- **根拠:** import dependency 探索は関数本体を走査しない `orchestrator/campaign/p3_b4_wiring_probe.py:970-979` 一方、top-level import は再帰追加する `同:985-1019`。2026-08-27 dogfood 証拠は39 module、現行静的展開は43 module・逆閉包19関数だった。
- **具体的な落ち:**
  - 後発の raw record producer は outcome/analysis field を証拠から導出する `orchestrator/campaign/p3_b4_raw_record_producer.py:1-12` うえ、結果を実際に publish する `同:1725-1758` が、現行43 module に含まれない。
  - 後発 consumer は canonical consumer-result bytes と source-closure receipt を生成する `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:19-24,1027-1077` が、現行集合外。
  - 後発 issuer は registry・manifest・receipt を publish する `orchestrator/campaign/p3_b4_prerun_issuer.py:590-625` が、現行集合外。
  - launcher の launch-sidecar writer も `orchestrator/campaign/p3_b4_launcher.py:405-433` にあり、関数内 lazy import のため静的 import 閉包外。
  - 解析集合内でも3 seed に到達しない consumption-record writer は閉包外になる `orchestrator/campaign/p3_s4_loop.py:1372-1446`。
- **判定:** これらは明記済みの「解析 module 外」と「3 seed 非到達 producer」の二分類そのものである `orchestrator/campaign/p3_b4_wiring_probe.py:2109-2116`、`docs/phase3-b4-reflux-ablation-preregistration.md:771-772`。probe の実チェックは digest/config identity に限られ `orchestrator/campaign/p3_b4_wiring_probe.py:1514-1697`、後発 producer を呼んでいない。
- **残差か否か:** D1195 の「完全性は主張しない」の内側。後発 generator の存在は確認したが、現行 probe 実行中にそれを呼ぶ経路はなく、D1195 実装残差にはならない。

## 親裁定への評価

- **(P1-1): 同意。** 解析集合の導出 `p3_b4_wiring_probe.py:952-1022`、逆閉包 `同:1099-1120`、inventory 化 `同:1135-1160`、実行時遮断が一続きで実在する。
- **(P1-2): 同意。** module docstring `同:4-11`、証拠文言 `同:2109-2116`、insight `output/insights/2026-08-27_t1769-b4-wiring-probe/README.md:67-75`、事前登録 `docs/phase3-b4-reflux-ablation-preregistration.md:764-775` に非完全性が明記される。
- **(P1-3): 同意。** D1195 のコード残差はない。必要なのは T-1909 を T-1769 により充足済みの重複として台帳上閉じること。
- **(P1-4): 同意。** 識別子非依存検索でも、別の非生成導出・遮断 probe は検出されなかった。test の手書き期待 subset は同じ閉包の検査 oracle であり、別導出ではない。

## 全件検索の記録

母集合は repository working tree の20,500 path。`rg -uu -g '!.git/**'` により ignored／untracked も含め、`.git/**` だけを除外した。件数はすべて打ち切りなしの一致行数／一致ファイル数。binary は ripgrep の通常規則で非テキストとして除外される。

- `逆到達閉包|reverse[ -](reachability[ -])?closure|non[- ]sample wiring probe|非標本 probe|結果を生成しない配線調査`
  - **29行／16ファイル**
  - 全件が T-1769/D1171/D1195 本体、同一 wave の証拠・逐語、台帳記録。
- `sys\.setprofile|OutcomeGenerationError|outcome generation interdicted|blocked_outcome_attempts|generation_scope_exclusion|generation inventory`
  - **85行／16ファイル**
  - 実コードは wiring probe とその test。残りは同じ T-1769 の証拠・変異記録。
- Python 全件で `(generation|outcome).{0,50}(inventory|catalog|manifest|interdict|producer)` と逆順
  - **132行／29ファイル**
  - B-4 以外の outcome/status 用法を含む。D1195 の非生成遮断を実装するファイルは wiring probe だけ。
- `(生成器|生成経路).{0,50}(目録|一覧|列挙|遮断|閉包)` と逆順
  - **22行／16ファイル**
  - D1171/D1195 系以外は一般的な生成器・列挙の記述で、別 probe ではない。
- `sys\.(setprofile|settrace|addaudithook)|threading\.setprofile`
  - **19行／7ファイル**
  - wiring probe 系以外の1ファイルは過去の line-trace 実測記録で、outcome 非生成機構ではない。
- 台帳識別子全件:
  - `T-1909`: **107行**
  - `D1195`: **4行**
  - `T-1769`: **158行**
  - `D1171`: **3行**
- `docs/worklog.md docs/archive` に限定した T-1909:
  - **105行 = 実内容2行 + 参照持ち越し103行**
- `git log --since='2026-08-27T09:16:15+09:00' --diff-filter=A -- 'orchestrator/campaign/*.py'`
  - **15追加ファイル**。うち1本は wiring probe 自身、14本が同時刻以後。後発 B-4 producer群を個別に静的確認した。
- 静的集合の実測:
  - 2026-08-27 dogfood JSON: **39 module**
  - 現行 `_load_static_modules()`: **43 module**
  - 現行3 seed逆閉包: **19 function**

pytest は実行していない。上記の module／閉包件数は書き込みを伴わない静的 AST 展開のみで得た。