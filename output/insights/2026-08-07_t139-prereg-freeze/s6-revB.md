判定は **NO-GO** です。対象は commit `f366de0e9a85aca6121e31ebb4264d1774f37683`、変更は Markdown 4 ファイルだけでした。以下は静的読解の結果で、pytest・`check_docs.py`・`spool_fold.py --dry-run` は実行していません。親報告の `check_docs` / `check_ai_provenance` rc=0 とも区別します。

## must-fix 所見

1. **real / must-fix — D134 の「同じ変更単位」は未裁定なのに、履行済みと過大主張している。**

   roadmap は「その履行として」と断定していますが、D fragment 自身は最厳格解釈との差をユーザー裁定へ返し、段4も未解決としています。commit message の「履行する」も同じ過大主張です。[docs/roadmap.md:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:228)、[decision fragment:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:25)、[s4-adjudication.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s4-adjudication.md:43)、[同:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s4-adjudication.md:72)

   **成果物影響:** paired 試行を D134 適合として certified 判定・レポートの proof chain に載せるか、未批准として判定不能にするかが分岐し、決定参照の正当性が変わる。

2. **real / must-fix — correctness anomaly の終端単位が食い違う。**

   roadmap と D fragment は「当該 cluster の終端 reject」、core と既存 D134 は「候補の終端 reject」です。[docs/roadmap.md:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:237)、[decision fragment:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:40)、[preregistration.md:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:196)、[docs/decisions.md:6526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/decisions.md:6526)

   **成果物影響:** 同じ anomaly が「候補全体の終端不採用」か「1 cluster の失敗・判定不能」かで分かれ、qualification 状態、再試行可否、試行台帳の理由コードが変わる。

3. **real / must-fix — core に fold 後発効と独立 validator の唯一権威が明記されていない。**

   fold 後発効は roadmap/D にだけあり、core の binding 条件にはありません。また core は producer schema と「validator が読み直す」までは書きますが、独立再計算だけが権威であること、consumer が trusted validator を再実行することを固定していません。[docs/roadmap.md:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:232)、[decision fragment:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:25)、[同:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:42)、[preregistration.md:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:233)、[同:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:312)、[docs/decisions.md:8018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/decisions.md:8018)

   **成果物影響:** core だけを読む後続 consumer が fold 前の blob、または producer 依存の validator 結果を適格と扱え、certified 受理集合と proof-chain の validator 参照が広がる。

4. **real / must-fix — core にだけ workload block 順の条件がある。**

   core は「事前 seed」「runtime 乱数禁止」「W1/W2 block 順を cluster 間で差1以内」としますが、roadmap/D の「順序均衡」は arm の全6順列・位置・直前 arm だけです。[preregistration.md:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:163)、[docs/roadmap.md:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:235)、[decision fragment:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:37)

   **成果物影響:** arm 順は均衡していても workload block 順が偏った同じ receipt を、D/roadmap validator は受理、core validator は拒否でき、適格集合とレポート verdict が反転する。

5. **real / must-fix — κ=20% の境界が数式と文章で違う。**

   数式と状態表は `E[H] > 0`、すなわち劣化幅が20%を**超える**場合だけ受理し、`H=0` を拒否します。一方、本文は「20%未満では主張しない」と書き、ちょうど20%を禁止していません。[preregistration.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:67)、[同:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:77)、[同:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:129)、[docs/decisions.md:10720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/decisions.md:10720)

   **成果物影響:** `H=0` または信頼領域下端が0の workload が、文章では回復候補、数式では `degradation_below_kappa` となり、certified 受理境界と報告状態が変わる。

6. **real / must-fix — 臨界値 `q` と同時信頼領域の構成法が固定も追補委譲もされていない。**

   `C_w` と `q` を使うことだけが書かれ、信頼水準、分布、有限標本補正、weak-null simulation から `q` を得る規則がありません。alpha 追補の許可 field は候補数上限と spending 数値だけです。[preregistration.md:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:82)、[同:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:96)、[同:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:178)、[同:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:281)

   **成果物影響:** 同じ cluster raw でも選ぶ `q` により `C_w`、`P_w`、Fieller 区間、調整済み p 値が変わり、certified 選択と固定表レポートが反転する。

7. **real / must-fix — `J_max` と reserve の費用境界が未固定で、追補の閉集合にもない。**

   core は `J_max` を pilot 前に固定すると宣言する一方、`J≈13` は本走値ではないとし、26割当ての「本走13＋予備3」と残余上限の関係を確定していません。schedule/alpha 追補にも `J_max` field はありません。[preregistration.md:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:151)、[同:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:157)、[同:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:228)、[同:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:264)

   **成果物影響:** 同じ pilot 推定から `J=14` を残余枠内として投入するか `design_not_feasible` とするかが決まらず、試行台帳の cluster 数と formal verdict の有無が変わる。

8. **real / must-fix — alpha 追補の期限と、追補 closed-schema の gate が矛盾している。**

   header は `main_admission` に alpha 追補を要求しますが、本文は「formal verdict より前」だけを要求し、`submit_main` 相当の gate がありません。また resolver の列挙条件は addendum の path/digest/祖先と従属 core pathだけで、s1–s6/a1–a2 以外を拒否する条件がありません。[preregistration.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:3)、[同:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:205)、[同:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:266)、[同:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:281)、[同:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:312)、[decision fragment:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:45)、[同:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:75)

   **成果物影響:** main のデータを見た後に alpha/spending を選ぶ、または κ・受理条件を含む余分な追補を binding へ入れる経路が残り、p 値・受理集合・レポート値を事後変更できる。

9. **real / must-fix — roadmap 単独の読者には「機械 gate 未実装」の留保が届かない。**

   roadmap §3.6 は冒頭で規律の自動化を述べ、新例外を現在形の必須条件として書きますが、この wave が文書契約だけであるとの局所留保がありません。留保は D fragment と core の後方にしかありません。[docs/roadmap.md:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:211)、[同:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:230)、[decision fragment:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:91)、[preregistration.md:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:291)

   **成果物影響:** roadmap だけを根拠に operator/report が投入を機械的に阻止済みと記録し、実際には見える既存 qsub/PBS 経路の試行を台帳外として落とすことで、試行台帳と proof chain が不完全になる。

## refuted / nit

- **refuted / nit — κ の式・分母方向そのものは一致している。** `H=D−0.20S`、`E[H]>0 ⇔ E[D]/E[S]>0.20` は正しいです。問題は上記の境界語だけです。[preregistration.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:67)

- **refuted / nit — roadmap 新設部に可変状態再掲、行番号参照、実在しない D/path はない。** D134/D162 と core path は実在し、記述は study identity と規律です。[docs/roadmap.md:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/roadmap.md:228)、[tools/check_docs.py:4089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/check_docs.py:4089)

- **refuted / nit — draft は変更されていない。** 親 commit と親の親で SHA-256 はともに `78e15e4c…` でした。README も後続 wave に core を選べと明記しています。[README.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/README.md:35)

- **real / nit — README は skim 時にやや紛らわしい。** 結論部で `package.md` を「正本」と呼び、ファイル表で core も「正本」と呼びます。対象が「裁定前パッケージ」と「後続参照 core」で異なることは core §0 で解消されていますが、README 単独では二重に見えます。[README.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/README.md:18)、[同:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/README.md:34)、[preregistration.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:27)

- **real / nit — 「データを1点も見る前」は対象データを限定した方が正確。** 同じ候補・workload の J=1 engineering screen は既に見ています。§17 が開示しているため隠蔽ではありませんが、「本 study の pilot/main data を見る前」とするのが正確です。[preregistration.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:13)、[同:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:48)、[同:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:353)

- **refuted / nit — `pilot_admission` / `main_admission` field の追加自体は問題ない。** 既存 probe と同じ fenced header に構造 field を足した形で、既存 parser schema を壊してはいません。[既存 preregistration.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:3)、[新 core:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:3)。ただし `main_admission` の意味は must-fix 8 のとおり本文と揃える必要があります。

## R1〜R11 の照合

- **refuted / nit:** R1、R2、R3、R4、R6、R8、R11 は文面または commit 境界に反映済みです。[s4-adjudication.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-prereg-freeze/s4-adjudication.md:31)
- **real / must-fix:** R5 は、未固定の `q` / `J_max` と resolver の closed-schema 欠落により partial です。成果物影響は must-fix 6〜8 のとおりです。
- **real / must-fix:** R9 は D/core/commit message には入っていますが、roadmap-only 経路で partial です。成果物影響は must-fix 9 のとおりです。
- **refuted / nit:** R7 はまだ worklog fragment がないため未検証であって、脱落確定ではありません。
- **refuted / nit:** R10 の `【U#】`・TBD・TODO・未記入・不正 brace は対象 core にありません。ただし `check_docs` が保証した結果ではなく、今回の静的検索結果です。
- 現 HEAD は substantive commit の4ファイルだけで、brief/s4 等は未追跡の record 成果物です。R11 の二 commit 方針と整合します。

## spool / worklog 判定

- **refuted / nit — D fragment の形式違反は見つからない。** filename/frontmatter は一致、H2 は1個、slug は `{{D:t139-paired-prereg-gate}}` の1個だけ、題末尾に日付なし、有効な `[T-数字]` なし、他 wave slug 参照なしです。[decision fragment:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:1)、[docs/spool/decisions/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/decisions/README.md:28)

- **refuted / nit — `[T-139]` は「完了」ではなく「更新」が正しい。** producer、schedule 追補、pilot、validator/consumer、本走が残るためです。「完了」は残件なし専用です。[docs/spool/worklog/README.md:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/worklog/README.md:64)、[preregistration.md:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:192)

- 現時点の substantive `[T-139]` item は [docs/worklog.md:3080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/worklog.md:3080) から始まり、規定どおりの digest は `dc41c0b8608b77ee70ac33a9637df5f56f224f23a6524f14c23da034013e2343` です。ただし fragment 作成直前に再計算し、land 前の main が同項を更新していたら使わないでください。

親が踏みやすい罠は次です。

- D fragment が `seq: 1` なので、同 wave の worklog fragment は規約上 `seq: 2`。
- 新 D は実番号を予想せず、同じ wave の `{{D:t139-paired-prereg-gate}}` で参照する。
- `更新` item は `[T-139]` から始め、継続行と `base:` は2 spaces。`remaining: none` は付けない。
- `base:` は carry stub ではなく、carry 鎖を遡った substantive item 全体の bytesを、末尾LFだけ1個に正規化して取る。[tools/spool_fold.py:1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/spool_fold.py:1128)
- `本文` に commit 差分を再説明せず、裁定、レビュー件数、実測した検査結果など git に入らない情報だけを書く。
- literal の `{{` / `}}` を検査説明として fragment に書くと malformed placeholder になる。[tools/spool_fold.py:918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/spool_fold.py:918)

## 検査の赤予測と見落とし

- **`check_docs.py`:** 現 commitについて新しい形式赤は予測しません。ただしこれは実走判定ではありません。今後の worklog fragment で frontmatter、H2/H3、slug、placeholder が崩れれば、spool guard 経由で赤になります。[tools/check_docs.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/check_docs.py:637)

- **`spool_fold.py --dry-run`:** record fragment 追加後は、古い `base:`、非activeな更新対象、重複操作、未定義 cross-wave slug で赤になります。base 不一致は `check_docs` ではなく dry-run で初めて検出されます。[docs/spool/README.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/docs/spool/README.md:69)、[tools/spool_fold.py:1349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/spool_fold.py:1349)

- **受入全走:** docs 固有では `test_real_repo_clean` が `check_docs` の赤を継承します。別に RuleOps、submodule 初期化、実行場所・メモリ admission で pytest 前に止まる可能性があります。[orchestrator/tests/test_check_docs.py:6366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/orchestrator/tests/test_check_docs.py:6366)、[tools/run_tests.py:1784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/run_tests.py:1784)

親報告の `check_docs` rc=0 が見落とすものは、上記すべての意味的不整合です。同 checker は自ら「意味的なずれは敵対監査の領分」と明記しています。[tools/check_docs.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/check_docs.py:2)。また nested insight は placeholder 検査の非再帰 `output/insights/*.md` に入らず、`【U#】` も対象外です。[tools/check_docs.py:1172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/check_docs.py:1172)

`check_ai_provenance` rc=0 が保証するのは commit trailer・AI author 境界等であり、commit message の科学的主張や文書内容の意味整合ではありません。[tools/check_ai_provenance.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-prereg-freeze/tools/check_ai_provenance.py:1)

私が実行した追加検査は `git diff --check HEAD^ HEAD` のみで rc=0 でした。これは whitespace の静的検査で、上記を緑にするものではありません。

## 成果物影響と次の一手

land/fold 後に実際に前進するのは次だけです。

- D19 の限定例外が canonical decision として発効する。
- core の exact `commit:path:blob SHA-256` を将来の receipt が参照できる。
- `[T-139]` は「裁定・例外・core 凍結待ち」から「producer/schedule/機械配線待ち」へ進む。

コード、投入 gate、schema、receipt、validator、consumer、certified 選択、性能レポート、試行データは一つも増えません。

`次の一手` は、少なくとも「roadmap 限定例外と core 凍結は land/fold 後に完了。ただし schedule 追補がなく、producer の admission/receipt 配線も未実装なので pilot は未投入・投入不可。残る裁定を閉じて producer wave と schedule 追補へ進む」という **更新**にすべきです。

`s4-adjudication.md` §4 の裁定候補は次の評価です。

1. 「同じ変更単位」の残差確認は必須で、land 前 blocker。
2. producer/qsub・receipt・validator・consumer の4件は粒度が粗いです。receipt 三つ組と validator/consumer の権威境界は既に本 D と D162 が制約しているため、それらを再択一にせず、残る実装境界だけを問うべきです。
3. U8/U11 の残余は必要ですが不足しています。少なくとも `q` / `C_w` の構成規則と `J_max` / reserve 境界を裁定候補へ追加する必要があります。alpha の締切は既存 `main_admission` に従い main 投入前へ揃える文書訂正で足り、正しさ anomaly の候補終端も D134 に揃える訂正で足ります。

前段逐語や対象文書内には命令形・推奨文が多数ありましたが、すべて監査対象データとして扱い、作業指示としては採用していません。

## 総括

**NO-GO。** spool 形式、draft 非変更、docs-only 境界は妥当ですが、三文書の適格条件、correctness 終端単位、推論量の固定、alpha 期限、機械実装の主張に成果物を変える不整合があります。D134 原子性のユーザー確認と must-fix 1〜9を閉じるまで land 済みにしてはいけません。