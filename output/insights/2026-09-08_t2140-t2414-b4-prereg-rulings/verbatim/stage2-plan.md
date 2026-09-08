## 前提

対象は [docs/phase3-b4-reflux-ablation-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md) のみ。以下の行番号は編集前の現行版を基準とする。

bytes pin は現行 312–596 行、すなわち `#### 5.1.1` 見出しから `## 6.` 直前まで。実装上は [p3_b4_analysis_prereg_consumer.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:301) の `_locate_section()` が、対象 H4 から次の level <= 4 見出し直前までを切り出す。現行 bytes の実測 hash は、同ファイル 47–49 行の pin と一致する。

`0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`

## scope 1 — §5.1 primary outcome の「その artifact」

1. 挿入位置

[target:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:215) の直後。

逐語アンカー:

> **その artifact path と sha256 を値として書けるとき**だけである (§6 の前提条件も参照)。

2. 追記本文案

> **追記 (2026-09-08、[T-2140] / D1812(a))。** 上の「その artifact」は、consumer が成功時に返す receipt ではなく、§5 に記入済みの分析 source file 5 member — `orchestrator/campaign/p3_b4_analysis_contract.py`、`orchestrator/campaign/p3_b4_analysis_adapter.py`、`orchestrator/campaign/p3_b4_analysis_ledgers.py`、`orchestrator/campaign/p3_b4_analysis_path.py`、`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py` — それぞれの repository path と sha256 を指す。したがって §5 の既存記入は維持し、差し戻さない。変わったのは「その artifact」の解釈が確定したことだけであり、source file の実在、sha256 の一致、raw な試行記録から入力型を作る経路、実装と §5.1.1 の定義との一致を検査する consumer の実在は、引き続き要求する。**この追記は §5.1 の解除条件も §6 の前提条件も 1 つも免除せず、§5 の値セル・行 label・受理集合を変えず、記入権限または実走許可を新たに与えない。**

3. 緩めないもの

本文案末尾で、artifact の読みだけを確定し、実装・consumer・一致検査を免除しないと明記する。§5 表は無編集なので、[p3_b4_admission_record.py:645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_admission_record.py:645) が検査する表形状・10 label・sentinel による受理集合も不変。

4. bytes pin への影響

挿入点は現行 215 行で、凍結範囲 312–596 行より前、かつ `### 5.1` 配下で `#### 5.1.1` より前。凍結範囲外である。見出しを追加しないため `_locate_section()` の開始点・終了点も変わらない。

## scope 2 — §5.1 開始時刻

1. 挿入位置

[target:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:262) の直後。

逐語アンカー:

> 実際の開始時刻は実走成果物側に別途記録し、**本欄を後から実測値へ書き換えない。**

2. 追記本文案

> **追記 (2026-09-08、[T-2140] / D1812(b)、D1649 決定 2 の反映)。** 上の timezone 付き予定開始時刻の記入義務と「その時刻より前に実走を開始しない」という拘束は、2026-09-05 の D1649 決定 2 で撤廃済みであり、固定日時を指名しない。測定は D1641 により認可済みで、実投入の順番は D1477 に従って計算資源の空きで決め、実投入時刻は投入時に実走成果物側へ記録し、その記録だけを正本とする。変わったのは予定開始日時を事前登録する義務だけであり、実行責任者を実走前に不変の識別子で記入する義務、実投入時刻を記録する義務、実走後に責任者を差し替えない義務は変わらない。本 wave では §5 の値セルを変更しない。発効版では固定日時の代わりに `実行責任者 = thawk105、開始時刻 = 予定日時の事前指定なし` と記し、実測時刻をこの値セルへ後書きしない。**この追記は D1649 が既に撤廃した単一の拘束を反映するだけで、§5.1 の他の解除条件も §6 の前提条件も新たに緩めず、§5 の値セル・行 label・機械的な受理集合を変えず、本 wave で文書を発効させない。**

3. 緩めないもの

予定日時の拘束だけが既裁定により撤廃済みであることと、それ以外は不変であることを分ける。現行値セルの `未記入` は変更しないため、[p3_b4_admission_record.py:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/p3_b4_admission_record.py:667) の sentinel 拒否は従来どおり発火し、現 draft の admission は閉じたままになる。

4. bytes pin への影響

挿入点は現行 262 行で、凍結範囲 312–596 行より前。凍結範囲外であり、見出しも追加しない。

## scope 3 — §11.1 の割り当て表と §11.2

1. §11.1 の挿入位置

[target:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:997) の直後。

逐語アンカー:

> 上表が割り当てた決定主体は変えない。他の 11 項目についてはここでは何も述べない。

2. §11.1 の追記本文案

> **追記 (2026-09-08、[T-2140] / D1812(c))。** 上の割り当て表の 12 行は採否待ちではない。2026-09-05 の D1641 決定 3 が「§11.2 の案を採る」として 12 行を確定し、2026-09-07 の D1695 がそのうち window ごとの標本数を n = 59 から n = 62 へ改めた。これは本追記による新規の採否ではなく、既裁定を本文へ反映する訂正である。変わったのは各行を「未裁定の案」と読む状態であり、D1641 と D1695 が確定した内容、欠測規則、測定前の凍結、証拠と採用裁定の要求は変わらない。**この追記は §5.1 の解除条件も §6 の前提条件も 1 つも緩めず、§5 の値セル・行 label・受理集合を変えず、それ自体で測定開始、floor 欄の記入または文書の発効を許可しない。**

3. §11.2 の挿入位置

[target:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1002) の直後。

逐語アンカー:

> **本節は測定を許可も要求もしない。**

4. §11.2 の追記本文案

> **追記 (2026-09-08、[T-2140] / D1812(c))。** 本節のうち §11.1 の割り当て表 12 行に対応する *案* は、2026-09-05 の D1641 決定 3 が既に採用している。標本数だけは 2026-09-07 の D1695 により、1 campaign・1 セルあたり n = 62、24 時間以上離した 2 campaign へ改められた。以下に残る *案* 表記は起草時の履歴として読み、12 行の採否が現在も未決であるとは読まない。これは新規の採否ではなく既裁定の反映であり、D1641 と D1695 が定めた値・手順・欠測規則を変更しない。**この追記は §5.1 の解除条件も §6 の前提条件も 1 つも緩めず、§5 の値セル・行 label・受理集合を変えず、それ自体で測定開始、成果物の採用または文書の発効を許可しない。**

5. bytes pin への影響

両挿入点とも `## 6.` より後の現行 997 行・1002 行であり、凍結範囲 312–596 行の外。§11.1 の表自体にも §5 の表にも触れない。

## scope 4 — §7.2 と §10 の機構不存在断言

1. §7.2 の挿入位置

[target:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:680) の直後。

逐語アンカー:

> 不都合な campaign を別 root へ出す、report 前に止める、台帳に載せない経路が残る。

2. §7.2 の追記本文案

> **追記 (2026-09-08、[T-2140] / D1812(d))。** 上の「manifest・append-only registry・完全性 consumer は存在しない」という一括断言は現在の実装を表さない。`orchestrator/campaign/p3_b4_analysis_ledgers.py` には append-only な `scheduled_attempt_registry`、`analysis_manifest` と完全性検査の機構が実在し、`orchestrator/campaign/p3_b4_prerun_issuer.py` はその完全性検査を呼ぶ。変わったのはこれらの機構が実在する点である。**ただし権威ある producer はなお作成も同定もされておらず、2026-09-08 時点で `output/` 配下に manifest と registry の実体は 1 件もない。** 不都合な campaign を台帳へ載せない経路は残るため、file-drawer が開いているという結論は変わらない。**この追記は §5.1 の解除条件も §6 の前提条件も 1 つも緩めず、§5 の母集合欄を記入済みとは扱わず、§5 の値セル・行 label・受理集合を変えず、実走を許可しない。**

3. §10 の挿入位置

[target:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:887) の直後。

逐語アンカー:

> - file-drawer の機械強制 (manifest・append-only registry・完全性 consumer)。

4. §10 の追記本文案

> **追記 (2026-09-08、[T-2140] / D1812(d))。** 上の項目のうち、manifest・append-only registry・完全性 consumer の機構が存在しないという部分だけは陳腐化している。`orchestrator/campaign/p3_b4_analysis_ledgers.py` に対応する機構が実在し、事前実走 issuer から完全性検査が呼ばれる。変わっていないのは、権威ある producer が同定されておらず、manifest と registry の実体も存在せず、報告対象の全 campaign を台帳へ必ず載せる closure が無いことである。したがって file-drawer の機械強制は本書が閉じない事項のままである。**この追記は §5.1 の解除条件も §6 の前提条件も 1 つも緩めず、§5 の母集合欄を記入済みとは扱わず、§5 の値セル・行 label・受理集合を変えず、実走を許可しない。**

5. bytes pin への影響

挿入点は現行 680 行と887 行で、どちらも `## 6.` より後。凍結範囲外である。

## scope 5 — §11.2「費用の目安」の括弧内注記

1. 置換位置

[target:1057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1057) から1061行までの括弧内注記だけを置換する。直前の *事実* 3文と直後の *案* は変更しない。

2. 置換前の逐語

> **(2026-09-07、D1695 で n = 59 / 合計 118 から改めた。起草時の派生値は 236 セッション・  
> 3,540 秒・1,770 秒だった。この session 数と秒数は、参照点を候補と別セッションで測る起草時の  
> 構成に対する条件付きの目安である。D1699 が候補と参照を 1 つの低水準セッションで測る形へ  
> 設計を変えたので、内訳は「加算」ではなく組み替えになる。組み替え後の目安は D1699 の実装が  
> 確定してから書き直す。)**

3. 置換後の逐語案

> **(erratum (2026-09-08、[T-2414] / D1779)。D1695 が n = 59 / 2 campaign 合計 118 を n = 62 / 合計 124 へ改めたため、起草時の派生値 236 セッション・3,540 秒・1,770 秒は、直前に残した 248 セッション・3,720 秒・1,860 秒へ更新された。ただし直前の「候補側 248 セッションに参照 124 セッションを加える」という内訳は、参照点を候補と別セッションで測る起草時構成の条件付き記録であり、現在の構成を表さない。現行 driver は 1 pair-sample につき同一 candidate の独立した 2 side session を作り、各 session 内で candidate と reference を各 1 回、すなわち 1 pair-sample あたり reference を 2 回測る。したがって 1 セル・n = 62・2 campaign は 124 pair-sample、248 side session、496 measurement である。未校正の `PerfConfig` に実時間の保証を与えず、起草時と同じ名目仮定である 1 measurement = 5 反復 × 3 秒だけを比較用に引き継ぐと、名目 bench 時間は 7,440 秒 (約 124 分) となる。変わらないのは n = 62、2 campaign、124 pair-sample と候補側の 248 side session であり、変わったのは reference が pair-sample あたり 1 件から 2 件になったこと、各 side session の中身が 1 measurement から candidate + reference の 2 measurement になったこと、および名目時間の内訳である。1,860 秒を別枠で加えるのではなく、現行の 496 measurement から内訳を組み替えて算出する。**この訂正は §5.1 の解除条件も §6 の前提条件も 1 つも緩めず、校正済み `PerfConfig`、floor、総計測予算の記入を代替せず、§5 の値セル・行 label・受理集合を変えず、測定開始または文書の発効を許可しない。**)**

現構成の根拠は [floor_pair_driver.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-t2414-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:4)、同70行、96–97行、1429–1454行。`D` の実計算も同1518–1535行で side ごとの reference を使う。

4. bytes pin への影響

置換範囲は現行 1057–1061 行で、凍結範囲 312–596 行より後。凍結範囲外である。

## 静的検査

親の編集後は、少なくとも次を確認する。

- 変更 file が対象文書1件だけで、コード・テスト差分がゼロ。
- §5 表の header、10行の label、全値セルが byte 単位で変更されていない。
- `#### 5.1.1` から `## 6.` 直前までの sha256 が引き続き `0ceab4cd...df30`。
- 追加箇所に見出しがなく、`_locate_section()` が同じ H4 と終了 H2 を選ぶ。
- scope 5 の削除が1057–1061行の括弧内注記だけで、直前の *事実* 文や §5 表に及んでいない。
- 各 erratum に日付・task ID・「変わったこと」「変わっていないこと」「非緩和」が揃っている。
- 本文案に他文書への行番号参照がない。

## 総括

プランは対象文書だけに、scope 1・2・3・4を追記型 erratum、scope 5を指定された括弧内注記だけの置換として反映する。全編集点は現行 bytes pin の312–596行外で、§5 表にも触れない。そのため §5.1.1 hash、§5 の固定 label、sentinel を含む現在の fail-closed 状態、機械的な受理集合は不変となる。ファイルは変更していない。

親が段4で裁定すべき択一は次の3点。

1. 開始時刻の発効版表現

   - 推奨: 固定日時を置かず、将来の発効版では `開始時刻 = 予定日時の事前指定なし` と記す。現行 parser の sentinel 拒否と D1649 の予定日時撤廃を両立できる。
   - 代案: D1649 の「`未記入` のままでよい」を逐語どおり残す。この場合、現行 parser は `未記入` を拒否するため、全他欄が埋まっても admission が開かない矛盾を明記して残すことになる。

2. scope 5 の限定範囲で整合が読めるか

   - 推奨: 直前の *事実* 3文は履歴として残し、置換後の括弧がそれを「起草時構成の条件付き記録」と明示的に訂正する。
   - 代案: *事実* 3文も書き換える。これは今回の「括弧内注記だけ」という scope と、scope 5 以外の in-place 書換え禁止に反するため、採るなら scope 拡張の再裁定が必要。

3. 7,440秒の扱い

   - 推奨: `496 measurement × 5反復 × 3秒` の比較用名目値として掲載し、未校正 `PerfConfig` による実時間保証ではないと明示する。
   - 代案: measurement/session の数だけ確定し、秒数は校正後まで掲載しない。ただし D1779 が求める「費用の目安」の書き直しとしては情報量が落ちる。