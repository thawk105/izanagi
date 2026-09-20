## レビュー結果と範囲

**must-fix 1件。現状は NO-GO。** 認可による受理集合の逸脱は、指定された production 経路の静的読解では発見しませんでした。ただし、driver の行移動に追随していない既存検査が、親の焦点走で失敗しています。

指定資料を読み、patch と適用後の現物を照合しました。pytest・変異・書込みは実行していません。以下の行番号は適用後の現物です。`driver`、`paired test`、`job test` は指定された3ファイル、`追補`は指定READMEを指します。

## must-fix

**MF1 — deferred gate の sink 行番号が古いままで、関連検査が失敗している。**

- **根拠:** 親の [焦点走ログ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-rerun-auth/focus/selfharness-post-s5.log:155) は、`run_measurement` の登録位置を7428行として照合し、`test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` が一致件数0で失敗しています。適用後の該当呼出しは [driver の7549行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2792-a1-sized-rerun-auth/orchestrator/campaign/paper_story_a1_paired.py:7549) です。
- **放置時の影響:** 実在する campaign sink と登録台帳の対応が壊れ、関連テストが失敗した成果物になる。
- **是正案:** 親の変更範囲へ必要な追随修正を加え、登録側と期待値側の該当位置を最終コードに同期する。検査の削除・緩和は不要。修正後に関連検査を再走する。登録定義そのものは射影外なので、具体的な修正箇所の確定は親へ返します。

同ログのもう1件、`test_existing_a1_non_touch_manifest_is_empty_from_base` は、未commitの今回3ファイルが `git status` に出たことによる失敗です（ログ114〜130行）。これは凍結物変更の証拠ではありません。固定範囲の検査を変更せず、成果物をcommitした清浄なtreeで再確認する対象です。

## should

**S1 — 追補のrecord仕様と拒否範囲を、実装どおりに限定する。**

- **根拠:** [追補55〜61行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2792-a1-sized-rerun-auth/output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md:55) に次の不一致があります。
  - 「record自身のcanonical JSONのdigest」では、digest fieldを含むように読めます。driver 2993〜3000は `authorization_sha256` を除いて計算します。
  - recordが先行attempt名を含むtupleと「完全一致」としていますが、recordに先行attempt名はありません。これは定数の第3要素から得ます。
  - 「それ以外はすべて従来どおり拒否」「attempt-0001以外の先行attemptがbenchに到達している場合」は広すぎます。正常な**別study**の先行証拠は従来どおり拒否理由になりません。また、先行bench到達のない初回投入はrecord不在でも通ります。
  - 「完全性検査はrecordの有無に関係なく実行」は、不正recordをreaderで先に拒否する経路には当てはまりません。
- **放置時の影響:** 追補から読み取れるrecord生成仕様とgateの受理集合が、実装と異なる。
- **是正案:** digest対象から自身のfieldを除くこと、先行attemptは定数だけで固定することを明記する。拒否の説明を「同studyの先行bench到達を解除できない」に限定し、完全性検査は「認可成功を理由に省略しない」とする。

**S2 — M14の固定値と対象caseを本走前に確定する。**

- **根拠:** 段4のM14は固定値が未指定です。job test 3215のHEADは `"a" * 40`、3371のsource負例は `"b" * 40`。authorの自己判定どおり、前者を固定値にすると、このfixtureでは正常な配線と同じ動作になります。
- **放置時の影響:** 変異の具体化によって検出可否が変わり、M14の検出力を評価できない台帳になる。
- **是正案:** gate呼出しの引数だけを `"b" * 40` に替える変異と、配線負例 `[source]` を対応づけて固定する。この場合、reader通過後にもintent作成は元の `expected_head` を使い、source不一致を再拒否する層はありません。狙ったcaseは例外が出なくなって赤になる構造です。

## nit

**N1 — §6.4追補の見出しが、本文の「例外追加」を弱めている。**

- **根拠:** 追補39行の「『再走』ではなく」に対し、47〜50行はbench後の同一配置反復に例外を追加すると明記しています。
- **放置時の影響:** gate・record・公開先は変わりませんが、名称の区別だけで元規則を回避した説明と誤読され得ます。
- **是正案:** 見出しも「将来のattempt-0002一件に対する例外追加」に揃える。本文が例外を明示しているため、裁定違反とは判定しません。

## 受理集合・保存条件・裁定適合

**認可による新しい解除は、定数1件と一致recordを前提に、同じbaseのattempt-0001だけへ限定されています。**

| 検査面 | 確認結果 |
|---|---|
| recordの型・shape | driver 2699〜2711でexact keys、文字列fieldの厳密型、decisionのdict型・exact keys、itemの厳密int型を検査。boolもfloatもitemとして通りません。`_read_json` は重複key・非object rootも拒否します。 |
| attemptの照合 | 2716でrecordの文字列をcurrent pathとexact比較。submitは3530、materialize helperは8409でcanonical absolute・base直下を検査します。reader単体はこのcaller側前提に依存します。 |
| tupleの照合 | 2724〜2728はstudy・current名・裁定ID・項・日付を照合。sourceは2718でcallerの値と比較。先行名はrecord入力で変えられません。 |
| 解除対象 | 2796の `prior == base / authorization[2]` により限定。解除が使われるのは2968・2976の末尾2条件だけです。 |
| 完全性・study differs | intent、root、barrier、ready、bench-go、bench-startの検査は認可成功後も残ります。study differsの2872・2915・2965も無条件のままです。 |
| namespace保存 | 3298〜3310のintent・attempt root・受領証namespace拒否はdiff上不変で、認可readerより先に実行されます。 |
| 公開先保存 | 8419〜8422の既存destination拒否・親directory実在要求は不変。既存のno-replace公開処理にも変更はありません。 |
| anomaly保存 | materializeのobservation consumerは8859〜8861に残り、認可を読むdestination gateの8868より前です。認可による早期returnはありません。 |
| producer | 3474〜3514で定数照合、namespace不在、既存baseを要求し、実 `_exclusive_write` とfsyncを使用。CLI名・必須引数は追補と一致します。 |

D2172項2が名指すstudy、attempt名、source SHA、裁定日、D番号はrecordに保持されます。attempt名はabsoluteな `attempt_root` に含まれ、定数とのbasename照合もあります。

提示patchはdriverと2テストだけです。policy・base設定・先行証拠を移動／削除する変更、formal昇格、非認証属性の変更はありません。D2156の停止を旧認可のまま再試行する実装ではなく、D2172の新しいexact入力を追加する形です。

追補の将来一件限定、凍結本文の保存、attempt-0001とL-A1S-4への非遡及、非認証lane維持、erratumによる正当化の否定、性能値を見た後の選択を防ぐ装置とは称さない点は確認できました。ただし、凍結物すべての現物hashを独立再計算したとは報告しません。

## テストの実体性と実測の限界

新規paired testは、実file、独立に計算したdigest、実reader、実gate、実公開先helperを使っています。producer testがstubするのはpolicy loaderであり、CLI dispatch・生成・排他書込みは実処理です。

job test 3334〜3354の正例も、実 `run_submit` → reader → rear gate → intent作成 → `_run_qsub` 捕捉3回を通します。consult B1の「intent前で停止する」問題は解消されています。fixtureのstubはpolicy loader／ready、CCBench、durable base、git、hostnameと、qsub・qstat境界で、author報告と一致します。**実環境の全前提成立や実scheduler投入の証明ではありません。**

受理／拒否docstringの説明は対象条件下の実装と整合します。ただし、正例関数の「拒否」文を同じ関数で必ず検証する構造ではなく、対応する負例との組合せです。

被覆の限界もあります。

- 新規先行証拠fixtureにはintentがなく、認可ありのstudy differs各分岐を個別に実証してはいません。ここはdiffによる保存確認です。
- malformed recordの`duplicate` caseは必要keyも欠けているため、重複key拒否だけの検出力には数えられません。
- `item-bool`は型検査で拒否されますが、`True != 2`でもあるため、item型制約だけの受理集合への効果を示す入力ではありません。厳密int検査の独立評価なら、digestを再計算した `2.0` が適切です。いずれもM1〜M14の成立判定とは分けます。

親ログは **1695 passed、2 failed、6 skipped**。受入全走とは明示されていません。replicaログはgateで「不在拒否・一致受理・各不一致拒否」を示しますが、qsub到達やmaterialize全工程を示しません。authorの「未実走」とは実施時点が異なり、矛盾ではありません。

## M1〜M14の1理由性

以下は静的判定です。KILLED実績は提示されていません。

| 変異 | 対象caseと検証結果 | 再照準 |
|---|---|---|
| M1 | `rejects_absent_record`。正常なattempt-0001のbench-goがあり、不在時にtupleを返すと末尾拒否が消える。 | 不要 |
| M2 | `rejects_other_attempt[attempt-0003]`。filename・current・recordが一致し、定数側attempt照合だけが拒否理由。 | 不要 |
| M3 | 同 `[attempt-0002]`。定数側は一致し、record rootだけが0003。digestも再計算済み。 | 不要 |
| M4 | `rejects_other_study[pilot]`。caller・record・先行証拠をpilotに揃え、定数側studyだけを狙う。 | 不要 |
| M5 | 同 `[sized]`。callerと先行証拠はpilot、recordはsized。caller比較除去後、他の層は再拒否しない。 | 不要 |
| M6 | `rejects_other_source`。別の有効SHAと再計算digestを使い、source比較だけを狙う。 | 不要 |
| M7 | `rejects_other_decision[id]`。itemと日付は正常。ID比較だけを除去すれば通る。 | 不要 |
| M8 | `rejects_bad_digest`。形式が正しい別digestを使用し、形式検査によるmaskなし。 | 不要 |
| M9 | `preserves_prior_integrity`。readyのepochだけ0。認可候補を検査前にcontinueすれば、固有のcorrupt拒否が消える。 | 不要 |
| M10 | `rejects_other_prior_reached_bench`。0001と0003の正常なbench-goを併置。全候補解除にすると0003の拒否が消える。 | 不要 |
| M11 | `rejects_existing_sibling`。exact pathと親directoryは正常。helperを直接呼ぶため、後段no-replaceはmaskしない。 | 不要 |
| M12 | `rejects_sibling_without_record`。不在recordの兄弟指定を先に検査するので、従来leaf側のassertで先に落ちない。 | 不要 |
| M13 | `authorize_rerun_is_create_only`。事前record存在検査の除去とproducer呼出しの上書き化、両方が必要。片側だけでは二重拒否にmaskされる。 | 登録済み2 hunkなら不要 |
| M14 | job testの配線負例 `[source]`。固定値をrecord側の `"b" * 40` にすれば、狙う拒否が消える。HEADと同じ値では検出不能。 | **具体値の確定が必要** |

M11はdestination helperの拒否保存を検証するもので、公開処理全体のno-replaceを解除した変異の検証ではありません。M13もproducer局所の2 hunkとして扱い、共有 `_exclusive_write` 全体の変更に広げないことが必要です。

## 総括

**must-fix：1件。NO-GO。** sink行番号の追随修正が必要です。受理集合の逸脱、I3の緩和、非認証laneの変更は、指定範囲では発見しませんでした。consult A1・B1は実装上解消されています。

**M1〜M13は登録どおりなら再照準不要。M14は `"b" * 40` と配線負例 `[source]` への具体化が必要です。** 変異本走の成立は未確認です。追補の仕様説明を修正し、関連検査と変異の実測を揃えてから完了判定してください。