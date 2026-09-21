# 判定と読解範囲

**brief の縮小方針を支持する。候補 mode・新 JSON・可搬 test は必要だが、plan の 21 key・hot 追加走・11 node・16 変異をそのまま採用する必要はない。** 修正が必要なのは、レビュー後に C の message を変更した場合の証拠更新手順である。ほかは束縛の具体化と保証範囲の訂正で対応できる。

**未実走・静的読解。** 指定資料を読み、コードと保存記録を照合した。実装、patch 適用、build、pytest、D297、変異は実行していない。親の測定値は保存資料の記載として扱い、独立再測定済みとはしない。

以下、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch`、`brief` は `J/s1-brief.md`、`plan` は `J/prev/s2-plan.md`。repo 内の相対 path は投入先 worktree 基準。

# 1. 過剰・削除と必要な最小集合

| 所見 | 判定・重大度・根拠・成果物への影響 |
|---|---|
| hot 正負例 2 走を完了条件へ戻す | **不成立／refuted・should** — `brief:17`、`J/verbatim/request-t2844.md:8`。既存 6 走の C 上での再取得が依頼範囲であり、削除してもその受理条件は欠けない。ただし hot-update の再立証は名乗れない。 |
| `.text` bytes 比較を追加する | **追加必須という攻撃は不成立／refuted・should** — `s3_mocc_lock_coverage.py:444`、D1603 逐語 `:5`。D1603 材料は D297 の結果であり、既存 binary 観測を残せば今回の追加要件にはならない。 |
| 「`.text` は objdump＋D297 が担う」という説明 | **real・should** — `brief:17`、driver `:452`。`--no-show-raw-insn` の正規化逆アセンブル一致は section bytes 一致ではなく、D297 もそれを補完しない。放置すると材料レポートの保証を過大にする。 |
| 候補専用 proof-surface check key | **追加必須という攻撃は不成立／refuted・should** — driver `:387,519`。C の source root を verifier に渡し、正例の `certified` を要求すれば gate は通る。別 key は同じ判定の重複になりやすい。 |
| 候補 mode・新 JSON | **必要／refuted・should** — 依頼逐語 `:8`、D2207 `:7,20`。旧 JSON は BASE＋旧 patch の証拠であり、型変更後の C の取得事実には転用できない。新出力は pin 前進の先取りではない。 |
| 親列・差分検査 2 本 | **必要／refuted・should** — 依頼逐語 `:3,6`、`brief:16–20`。単一の子・限定 touch set という候補そのものの契約を検査するため、仮想リスク向け追加 gate ではない。 |
| 旧 14 key の全変異を候補 test に複製 | **real・should** — `test_mocc_proof_surface.py:798`。旧 `compute_checks()` を無変更で再利用するなら既存対照で足りる。複製は材料の受理集合を改善せず維持対象を増やす。 |

候補固有 key は **2 本、合計 16 key** でよい。`candidate_blob_matches_patch` を第 17 key に戻す必要もないが、**C の実測 blob と可搬再構成 source の照合自体は残す**。これは P5 が約束した証拠の接続であり、key 数の縮小とは別である。

最小 test 集合は次の **5 node 案**。必要な対照は各 node 内で parameterize できる。

| node 案 | 保証 |
|---|---|
| `test_candidate_source_contract` | BASE＋候補 patch が旧計装の指定 3 箇所だけを変えた source であり、既存 X/P 構造・include 不変・unordered multiset 2 箇所・供給 header を確認する。 |
| `test_candidate_trace0_logical_rows` | 既存 helper を使い BASE と候補の TRACE=0 論理行列を比較し、`#line` のずれを検出する。 |
| `test_candidate_identity_checks` | 実 Git 照会結果を読む経路を対象に、親 `[BASE]`、通常 file の mode 不変な transaction.cc だけの変更を受理し、孫・複数親・追加 path・mode 変更を拒否する。 |
| `test_candidate_mode_source_routing` | 正例と TRACE=0 候補側は C checkout、負例は C＋既存 3 patch、verifier root はその build source、比較相手は BASE であることを確認する。 |
| `test_candidate_json_is_bound` | 固定 C/tree/blob、再構成 source の blob/hash、patch hash、6 走、旧14＋新2 key、新2 key の観測との整合、NON_ADMISSIBLE を検査する。 |

`test_candidate_trace0_logical_rows` は D297 と完全重複ではない。既存 helper は marker を論理行番号へ畳むため、`#line` 保持の局所回帰検査として残す価値がある（`test_mocc_proof_surface.py:123,162`）。

削れるのは独立した header node、proof-surface node、fixture routing node、旧14 key 全再試験、broken **4** 本の包括契約再試験。実走対象の broken **3** 本の適用・配線は残す。hot patch の適用確認を残す場合も「互換性確認」であって hot 動的実証とはしない。

# 2. P5 の可搬性と patch の置き場所

| 所見 | 判定・重大度・根拠・成果物への影響 |
|---|---|
| 他 wave に C がある保証はない | **支持／refuted・should** — `tools/dev_waves/git_state.py:93,645,697` は local URL を確認して `update --init --recursive --no-fetch`。既存木への C の取得保証はなく、C 必須 test は候補の正否と無関係に受入を赤にする。 |
| 受入時の main merge が C を届ける | **不成立／refuted・should** — `tools/dev_wave_wait.py:2587,3853,3882`。submodule readiness と outer merge・provenance 監査はあるが、候補 branch の fetch はない。 |
| C は絶対に他 wave に入らない | **不成立／refuted・nit** — `J/prev/insight-README.md:104`。主 module store への保存後に初期化する木には含まれ得る。「保証なし」と「取得不能」を分ける。 |
| candidate patch を置けば D16 違反になる | **一律禁止という攻撃は不成立／refuted・should** — D16 `:8,13,19`、`patches/README.md:14,533`。成果物本体を branch C とし、patch を再現用に限定すれば整合可能。ただし試作例外の再利用という説明は成立しない。 |

新 patch の位置付けは「C の再現資料」で固定する。producer に適用する第二の正本にせず、C checkout には重ねない。T-2294 の既存 patch は旧命題の証拠として保持する、という D2207 とも整合する。

patch を repo に置かない対案はある。

| 対案 | 評価 |
|---|---|
| BASE＋既存 T-2294 patch を materialize し、test 内で指定 3 箇所を置換する | **最小の代案**。C object 不要。独立に固定した C の blob/hash と照合する必要がある。新 patch は削れるが、置換処理という候補再現コードは残る。 |
| 候補 source 全体を fixture にする | 可搬だが大きい source 複製になる。今回の patch より縮小とは言いにくい。 |
| test が job dir の bundle を読む、または C を fetch する | job dir・ref・取得操作への依存が残り、通常受入の可搬性を満たさない。採らない。 |

**推奨は P5 維持**。author が作る差分をそのまま検査資料にも使えるため、3 箇所置換 helper を別に維持するより説明しやすい。配置について追加裁定を要求するほどの違反は認めない。

なお既存 `_materialize()` は 4 file しか複製せず、`include/trace.hh` は含まない（`test_mocc_proof_surface.py:35,65`）。header 供給確認は BASE のその blob を別に読む。helper の返す木を完全な CCBench source tree と扱ってはならない。

# 3. C の作成・message・保全

| 所見 | 判定・重大度・根拠・成果物への影響 |
|---|---|
| レビュー後の message amend と証拠更新の順序が未確定 | **real・must-fix M1** — `brief:19,30` は B・compute の後に段6を置く一方、message 確定も段6後。witlight `README.md:35,188` では実際に message amend で OID が変わった。放置すると JSON/test/D297 が旧 C、保全 branch が新 C という材料分裂が起きる。 |
| 一時 worktree で commit する | **支持／refuted・should** — `mk-W-commit.sh:22–30`。author の patch を限定 staging して commit でき、wave submodule の checkout HEAD を動かさない。 |
| bundle だけで公開・他 wave への配布も済む | **不成立／refuted・should** — witlight `README.md:193`、D2150 `:12–14`。bundle は保全であり公開確認ではない。主 store fetch も既存 wave への自動配布ではない。 |
| witlight script をそのまま最終手順にする | **real・should** — `mk-W-commit.sh:31–39`、witlight `README.md:184`。参照型としてはよいが、末尾成功が各証拠検査の成功を集約する設計ではない。放置すると保全完了の誤記を招く。 |

M1 は新 gate を作らず手順で閉じられる。

- B に渡す OID を、その時点の C と明記する。
- 段6で message を変更しなければ、そのまま最終 C とする。
- amend した場合は旧 OID の証拠を保持し、最終 C に対する D297 と Git identity を再取得する。JSON・固定期待値・bundle・fetch を最終 OID に揃える。
- compute を再走せず内容同一性で扱うなら、実行した旧 OID と最終 OID を区別して記録する。JSON の `ccbench_commit` だけを書き換えない。

今回の簡潔な選択は、amend が起きた場合に候補 compute も最終 C で再走すること。変更がなければ追加走は不要。

branch 名 `izanagi-mocc-xp-instrumentation` は候補用途に合う。ただし `brief:11` の「wave の refs に無い」は主 store の現在の非衝突までは証明しない。P4 の fetch 時の別 OID 拒否を維持すれば足りる。

trailer は `docs/ai-provenance.md:18,25,27,65` に従う。実寄与の Codex author、採用された reviewer、判断を行った manager/integrator を記録し、witlight の model 値をコピーしない。機械的 commit 代行を integrator として追加しない。

保全順序は **最終 C → 自己完結 bundle の verify/hash → 主 module store へ非 force fetch → ref/OID 確認 → wave 撤去**。ここで撤去前に必要なのは、C を所有する **wave の submodule git dir が失われる前**の保存である。一時 worktree の削除だけなら branch/object は元の store に残る。掃除・land の道具が C を自動保全するとは数えない。

HEAD/gitlink を BASE のまま clean に保つ設計は受入と整合する。ref/object 追加は checkout の汚れではない。主 store fetch の副作用は後発 clone に候補が見えることだが、pin を C に変更する効果はない。

# 4. 波及表の実効性

**45 件の主分類は、plan の 15 追随・27 据置・1 衝突へ、新規 2 件を据置として足した「15・29・1」でよい。** ただしこれは文字列集合の分類であり、将来変更する file の完全一覧ではない。

| 新規 file | 分類・根拠 |
|---|---|
| `docs/paper-story/2026-09-21c.md` | **据置** — `:122,301–303` は当該版の identity・取得事実。C へ置換すると歴史的主張の対象が変わる。 |
| `docs/paper-story/claim-evidence/2026-09-21b.md` | **据置** — `:193,196,215` は既存観測と証拠対応。新しい C の証拠は新項目で扱う。 |

| 所見 | 判定・重大度・根拠・成果物への影響 |
|---|---|
| plan の据置分類は「新 main でも旧系列が動く」を意味する | **不成立／refuted・should** — t2304 `README.md:15,46,61`。旧証拠保持と live consumer の受理は別。policy epoch が動けば独立 source PIN の系列にも影響する。 |
| 45 件が更新閉包である | **不成立／refuted・should** — t2756 `README.md:133`、`plan:318–337`。文字列を持たない policy golden・floor fixture を漏らすと、移行費用と受理不能範囲を過小報告する。 |
| plan の file:line が全てそのまま現物に当たる | **real・nit** — `brief:12` に対し、T-167 は現物 `docs/phase3.md:2754`、所要時間台帳の該当 node は `:11165`。列挙したコードの不変から他文書の行番号不変は導けない。材料の参照性が落ちる。 |

文字列外依存は plan が主要面を押さえている。次の区別を表に残す。

- **patch preimage**：旧計装・temperature 計装を C に重ねない。template の機械適用成功だけで意味・論理行契約の移行とはしない。
- **temperature axis**：`axis_mocc_temperature.py:21` の `PIN` は動くが、`:22,66` の PROOF_PIN と proof 束縛は BASE 固定。「衝突」は C への接続時に生じ、旧 proof の遡及取消しではない。
- **pilot/receipt**：D2153 `:3–9` は patch/hash・適用後 source・build 配線を束縛する。新 JSON は receipt v2 の代用品ではない。
- **policy epoch**：t2304 `README.md:52–61` の `test_autonomous_trial_completeness.py`、`test_campaign.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_b4_closed_critic.py`、`test_s8b_materialization.py` を集合外の具体例として明記する。「golden に波及」だけより再利用しやすい。
- **生成物形**：`buildcache.py:1062` の再実測義務は残る。今回の P9 build 成功だけで将来 pin 移行時の生成物契約確認を済ませたとはしない。
- **自前 PIN・fixture・凍結**：旧 source pin を維持する driver と、現行 policy に依存する部分を分ける。新 C の取得事実と主張する系列だけ新証拠を用意する。

現在の表に、材料(3)を欠落させるほどの分類逆転は認めない。集合外依存の具体化は **should**。

# 5. scope と束縛の到達範囲

| 所見 | 判定・重大度・根拠・成果物への影響 |
|---|---|
| 候補 mode が pin 前進を先取りする | **不成立／refuted・should** — `brief:26`、`materializer_admission.py:78`。承認定数を変えず NON_ADMISSIBLE の診断として走れば、正式 campaign の受理集合は広がらない。 |
| I 面を同時に閉じる必要がある | **不成立／refuted・should** — 前依頼 `:7`、`brief:21`。不足明記でよい。X/P の成功を I 被覆や第2例完成に読み替えない。 |
| 旧 JSON に旧14 key の全入力が実在する | **real・should** — `brief:39` に対し driver `:425,489,525`。`_other_integrity_clean` は内部値で public JSON から除外される。JSON 単体から14 key全てを再計算できるという保証は成立しない。 |
| C の2 checkだけで可搬 source と実 C の一致も閉じる | **不成立／refuted・should** — `brief:20`、`plan:234–236`。親・path は内容一致ではない。実測 blob と再構成 blob の consumer 照合を残さないと、test が検査した候補と compute の C が別でも通り得る。 |

新設する2 checkの全層は、今回の編集面で閉じられる。

**driver の Git 実測 → JSON の parent/raw diff/tree/blob → consumer の固定 C と再構成 source 照合**を具体化する。parent/path の boolean を `True` と読むだけの consumer にはしない。raw diff は path 名だけでなく通常 file・mode 不変も確認できる形にする。

旧14 keyの全入力再公開や再計算可能な新 schema への一般化は不要。既存内部入力の検査と、保存 JSON の束縛検査を区別して記す。

今回の scope 外に残る層は、正式 build admission、T1943 receipt/job-result、新 pin 用 policy・floor・登録・探索 consumer。これらへ新2 checkが伝播したとは主張しない。必要なら将来の再承認パッケージに「C を正式系列へ接続する作業」として挙げる。

# 6. materializer・spawn inventory・build authority

**既存 helper への委譲だけなら登録簿変更は不要、という P2 の読みを支持する。**

| 面 | 判定・根拠 |
|---|---|
| materializer | `_build_variant` / `_install_dependency` は登録済み（`materializer_admission.py:78,93`）。新 mode から呼ぶだけなら site は増えない。 |
| exact 閉包 | `test_s8b_floor_campaign.py:8086,8157` は関数内の `"--build"` literal を収集して完全一致する。build 実装を新関数へ複製すると追随が必要になる。 |
| spawn inventory | `_run_checked` は既に登録済み（`test_ccbench_spawn_sites.py:217`）。そこへ parent/diff-tree の argv を渡すだけなら site 数は不変。 |
| 新しい直接 subprocess | **real・should** — 同 test `:2842` は exact inventory。read-only Git でも新しい `subprocess.run` site を作れば対象になる。旧 test bytes 不変の方針とも衝突するので、既存 runner を使う。 |
| build authority | `test_p3_build_authority_cli.py:158,177,1227` の manual file/site 集合は、既存関数を維持する限り変わらない。新 authority を発行する必要はない。 |
| condition gate | 同じ3 macro・patch・witnessを使う（`condition_meaning_gate.py:204,276`）。候補 OID だけでは DefineSpec 追加は不要。 |

新候補 patch に新しい macro interface を足さないことも P1 の利点である。登録簿追随を避けるために検査を緩める必要はない。

# 7. 変異の帰属

**「各変異が必ず単一理由で赤になる」は不成立。** plan 自身も複数 killer を挙げている（`plan:361–368`）。必要なのは失敗集合を正直に記録し、hash 不一致と意味検査を混同しないことである。

| 変異群 | 帰属と縮小案 |
|---|---|
| P 恒真化、X 削除、multiset→set | source bytes の最小変換検査・構造検査・blob/hash consumer が併発赤になり得る。構造 node を単独実行した結果を意味上の killer として別記する。 |
| `#line` ±1／削除 | 最小変換・論理行・patch 適用・hash の複数赤があり得る。論理行検査の失敗を直接確認し、hash 赤だけで観測者効果検査成功とはしない。 |
| `<set>` 復帰 | 候補 test の複数赤とは別に、P7 の D297 負例は include 契約で止まる対照として扱える。 |
| JSON OID/tree/blob/hash 改変 | provenance の拒否対照。X/P 意味論の検出力には数えない。 |
| broken patch 省略／旧計装二重適用 | routing node の対象。後段 compile/apply 失敗だけなら「配線検査が殺した」とは書かない。 |
| 親検査・差分検査の緩和 | 新2 checkの独立入力対照を残す。単なる祖先・追加 path・複数親など、他条件は正常な対照にする。 |
| `.text` bytes 恒真化／hot reason 緩和 | **削除**。本 wave で実装しない検査への変異は登録しない。 |
| 正常候補の拒否／docstring 言換え | 正常候補の受理は必須。docstring 等価変更は既存変異工程の対照として使えるが、新 gate や専用 test は不要。 |

全 suite の併発赤を抑えるために hash 束縛を外す必要はない。焦点 node の結果と全体の失敗 node 集合を分ければよい。新しい変異台帳・集計機構の実装は不要。

## 総括

- **must-fix M1:** 段6後の C message amend 時に、D297・compute・JSON/test・bundle/fetch を最終 OIDへ揃える手順を確定する。
- **should S1:** 21 keyを16 keyへ縮小し、hot追加走・`.text` bytes検査・その変異を削除する。
- **should S2:** 「正規化逆アセンブル一致」と「`.text` bytes一致」を区別し、旧14 key全入力がJSONにあるという説明を訂正する。
- **should S3:** 新2 checkの観測→JSON→consumerと、実C blob→可搬再構成blobの照合を具体化する。
- **should S4:** 波及表へpolicy epochの集合外consumerを具体名で補い、旧証拠保持と新mainでの実行可能性を分ける。
- **should S5:** 変異の併発赤を記録し、hash拒否だけを意味検査の成功に数えない。
- **nit N1:** planの現物行番号を更新する。「変更0 commit」から全参照行の不変を一般化しない。

削除・縮小の推奨は、**11 node→5 node案、候補7 key→2 key、8走→既存6走、broken4本の包括再試験→実走3本の配線確認**。候補patchは維持を推奨するが、既存patch＋指定3箇所置換による可搬testも成立する。

| provisional | 結論 |
|---|---|
| P1 | 支持。p4の保存結果はTRACE=1 build・C実走の代用にしない。 |
| P2 | 条件付き支持。縮小を採用し、blob束縛と保証名を明確にする。 |
| P3 | 支持。local候補branch、BASE単一親。 |
| P4 | 条件付き支持。最終OIDへの証拠更新手順を修正する。 |
| P5 | 支持。C objectの取得保証なし、再現patch方式は有効。 |
| P6 | 支持。Iは不足明記に留める。 |
| P7 | 支持。正式Cで実走し、clang未完了を合格に変換しない。 |
| P8 | 支持。45件は15追随・29据置・1衝突、集合外依存を併記する。 |
| P9 | 支持。実flagsでの生死確認は有用。build成功をcompute成功やpin承認に一般化しない。 |

**plan は brief の縮小に合わせて更新し、brief は最終 C の証拠更新順序・束縛の責任範囲・保証表現を修正すればよい。材料3点のために、verifier・D297検査器・正式admission・探索面まで変更する必要は認めない。**