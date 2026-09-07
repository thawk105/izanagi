## 検算

- pin 範囲: `312–596 行、285 行、21,833 bytes` → **312–596 行、285 行、21,833 bytes**。
- raw SHA-256: `0ceab4...f30` → **`0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`**。consumer 定数とも一致する。[事前登録文書:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:312) [consumer:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)
- consumer の境界: 「対象 H4 から次の level 4 以下の heading 直前」→ **そのとおり**。開始は 312 行目、次の対象 heading は 597 行目の `## 6` なので、596 行目の改行までを含む。[consumer:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301) [事前登録文書:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:597)
- 変更位置: `161、822 後、905 後、1092 後 → pin 外` → **すべて pin 外**。161 行目は 1 行置換なので開始位置も動かない。
- analysis-path 側の境界一致 → **未実測**。`p3_b4_analysis_path.py` は必読射影に含まれず、厳密な単独段規約上は読めない。consumer が同 file の bytes を別 member として必要とすることまでは確認した。[consumer:1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1038)

§5 parser の行番号は次のとおり。

- `_SECTION5_LABELS 77–88` → **77–88**
- section marker `625–640` → **625–640**
- 表行数・header `645–649` → **645–649**
- pipe/cell 数 `653–657` → **653–657**
- strip・NFKC・重複・集合一致 `658–666` → **658–666**
- default-ignorable/Cf `527–544` → **527–544**
- sentinel 定義・適用 `114–121、667–673` → **114–121、667–673**
- model/prompt/projection 行だけの特殊文法 `674–688` → **674–688**

以上は現物と一致する。[admission parser:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_admission_record.py:77) [admission parser:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_admission_record.py:602)

提案 primary 行の静的結果:

- 内部 cell 数: `2 と想定 → 2`
- 64 桁小文字 hex: `5 件 → 5 件`
- NFKC: `不変と想定 → 不変`
- default-ignorable/Cf: `なしと想定 → なし`
- reserved/whole-value sentinel: `なしと想定 → なし`
- `sha256=` や 64 桁 hex による別文法の誤発火: **なし**。`_EXPECTATION_ROW_RE` は exact な model/prompt/projection label の値だけへ適用され、全行走査ではない。[admission parser:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_admission_record.py:103) [admission parser:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_admission_record.py:674)

hash と順序:

- 提案順序 → consumer の `_CLOSURE_PATHS` と **一致**。[consumer:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98)
- 5 path の実在 → **5/5 実在**。
- consumer 自身の提案 hash `fe3aeb...b31a` → **同値**。
- 他 4 member の提案 hash → **未実測**。射影外 file の bytes は読んでいない。

文書量をプランどおり、余分な空行なしで適用した場合:

- 全体: `94,342 bytes、1,097 行 → 96,591 bytes、1,110 行`
- 161 行目: `33 chars / 55 bytes → 639 chars / 655 bytes`
- 最長文字行: `481 chars → 639 chars`
- 現行の byte 最長行は 797 行目の 657 bytes なので、提案行は byte 数ではそれを 2 bytes 下回る。

`check_docs.py` は対象文書を living doc に含めるが、同文書には `TextLimit` の byte 上限も最長行上限も設定していない。[check_docs.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/tools/check_docs.py:124) [check_docs.py:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/tools/check_docs.py:273) 一般 living-doc 検査では腐敗する行番号参照、現在 Phase、pin literal、D/path 実在性を調べるが、提案文はこれらを新規には破らない。5 source path も実在する。[check_docs.py:6669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/tools/check_docs.py:6669)

## 所見

所見 1: プランの「analysis-path 境界と 5 件の live hash を静的確定」は、この射影では過剰主張である。

プランは analysis-path 側との一致と 5 hash の確定を断言するが、`p3_b4_analysis_path.py` と先頭 4 closure member は射影外である。[plan.md:73](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:73) [plan.md:91](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:91) consumer hash、pin hash、consumer 側の期待順序だけは確認できた。プラン自身が定める編集直前・commit 直前の 5 件再計算は必須のまま残る。[plan.md:28](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:28)

所見 2: §11 の二命題は実装済みだが、「floor 行を埋めるだけ」という旧文全体を偽とする追記は言い過ぎである。

生成器が本書を resolver へ渡して読む接続は存在する。[material report:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_material_report.py:83) [material report:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_material_report.py:211) また、resolver が返した `authoritative_floor.floor` を評価器へ渡し、返らなければ `None` を渡すため、「§5 から floor を渡す」も**有効な pin がある場合に限り真**である。[material report:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_material_report.py:267)

一方、生成器自身の説明は「verbatim sentinel は従来の `None`、valid pin だけが値を供給」と限定し、resolver rejection も fail-closed である。[material report:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_material_report.py:3) [material report:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_material_report.py:214) したがって、プランの追記は「任意の記入だけで経路が変わる」と読めないよう、**検証に通る権威ある artifact pin の場合だけ非 `None` が渡る**という条件を明示すべきである。[plan.md:48](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:48)

所見 3: §10 の追記案は現物と整合し、他の未決事項を解消済みとは読ませない。

対象 driver 行は実際に記入済みで、§5.1.0 は候補・command・証拠・決定規則・記入者／レビュー者を固定している。[事前登録文書:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:158) [事前登録文書:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:264) よって「なお先行 freeze と人間指名が残り、欄は埋められない」は真に stale である。[事前登録文書:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:810)

追記案は「§5 の他の未記入欄と §6 の未充足条件」を明記しており、model snapshot の宣言源・承認主体など後段の未決事項を解消済みとはしていない。[plan.md:36](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:36) [事前登録文書:845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:845)

所見 4: 親 brief の表行数の呼称と parser 行番号が不正確である。

brief は `_SECTION5_LABELS` を「87 行」とするが、定義は **77–88 行**である。[brief.md:41](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/brief.md:41) [admission parser:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_admission_record.py:77)

また「11 欄中 1 欄」とするが、機械的な表は **10 data rows**。11 になるのは「実行責任者・開始時刻」の 1 cell に独立 2 値を数えた場合だけなので、正確には「10 表行・11 独立値のうち、本 wave で埋めるのは primary outcome の1値」である。[brief.md:36](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/brief.md:36) [事前登録文書:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:38)

所見 5: 親 brief の成果物個数は段2プランと不一致である。

brief は「§10 と §11 への追記各 1 か所」とするが、プランは §11 を 905 行目後と1092行目後の **2 か所**で訂正する。[brief.md:53](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/brief.md:53) [plan.md:45](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:45) [plan.md:54](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:54)

所見 6: 161 行目は著しく長くなるが、現行 `check_docs.py` の違反ではない。

639 chars の新しい最長行になるものの、対象文書には line/byte budget がない。提案に含まれる code path は全件実在し、日付 `2026-09-08` や `worklog entry 1336` に対する一般日付 lint もない。[check_docs.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/tools/check_docs.py:128) [check_docs.py:5929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/tools/check_docs.py:5929) ただし worklog entry 1336 自体は射影外なので、その provenance 表示は未照合である。[plan.md:43](/home/SFC/tanab/.claude/jobs/6937f3cc/tmp/t2140-b4-prereg/plan.md:43)

所見 7: scope 外の stale 記述として、§7.2 と §10 の manifest／registry 不存在断言が残る。

§7.2 は「manifest・append-only registry・完全性 consumer は存在しない」、§10 は file-drawer の機械強制を未実装と断言する。[事前登録文書:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:675) [事前登録文書:876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:876)

しかし projected consumer は registry からの manifest 生成、先頭 n 選択、registry violation の全体導出を実際の API で検査し、material report も publication の registry／manifest を読み評価経路へ渡す。[consumer:703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:703) [consumer:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:819) [material report:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_material_report.py:228) 少なくとも「machinery が存在しない」という一括断言は現在地と合わない。ただし file-drawer 全体が閉じたとはこの射影から証明できない。これは**本 wave の scope 外**として列挙するだけに留める。

## 総括

pin 範囲・行数・bytes・raw hash、§5 parser の引用、primary 行の構文受理性、§10 訂正は確認できた。`sha256=` や64桁 hex の横滑り発火もない。

修正が必要なのは主に二点である。

- §11 追記は、非 `None` の floor が渡る条件を「検証済みの有効な artifact pin」に限定して書く。
- plan/brief から、未射影の analysis-path 境界・先頭4 member hashを検証済みとする断言、および brief の行番号・欄数・追記箇所数の誤記を除く。

file 編集、pytest、`check_docs.py` の実走は行っていないため、緑とは報告しない。