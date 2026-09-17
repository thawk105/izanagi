## 前提の検算

指定資料はすべて読めました。静的検査のみで、ファイル変更・テスト実行はしていません。

以下、ADC／CBR は対象の `tools/audit_dangling_commits.py`／`tools/check_branch_rescue.py`、TA／TR／TD は対応する `orchestrator/tests/test_*.py`、author は指定の `s5-author.md` を指します。

- **refuted：差分と現物の不一致。** 保存された `s5-implementation.diff` は、所有7ファイルの現在の `git diff` と完全一致しました。追加303行・削除19行も一致します。
- **real／nit：焦点走を「login node の緑」とする前提は不正確。** `focus-1.log:4–14` は local scope の OOM 後、計算ノードへの dispatch と child rc=0 を記録しています。放置すると検証場所と失敗履歴の報告が誤ります。

## 受理集合

**refuted：off に抑止を増やす経路が混入している。**

ADC:1713 の off 分岐は requested／accepted／rejected をすべて空にし、1733 の既存走査なし分岐へ進みます。1762 の返却は次のとおりです。

- findings は `core.findings` そのもの。
- suppressions／unreferenced_copies は空。
- blob_failures／scan_failures は0、reference_failure は None。
- regenerable 関係の値は core から維持。

`_validate_offrepo_roots` は else 側だけです。metadata・列挙・cat-file は返却後の経路にあり、core 処理にも該当する走査呼出しはありません。API off＋非空 roots も無視されます。したがって、変更によって掃除対象の findings が抑止される問題は認めません。

**refuted：full の既存判定経路が変わった。**

差分上、ADC:1716 の検証呼出しは従来どおりで、1779 以降の走査・照合・抑止処理に変更はありません。明示 full＋同じ root は省略＋root と同じ経路です。追加 field と full＋roots 空の拒否は裁定済みの差です。TA:4272 は report と非時間依存出力の一致も検査します。

## fail-closed の位置

**refuted：full＋roots 空の拒否が遅い。** ADC:1702 の RuntimeError は `_checked_git`（1710）、`_audit_snapshot`（1725）より前です。未知 API mode も1700で拒否し、CLI の未知値は1996の choices で拒否します。

**refuted：実行不能時の rc／terminal 契約違反。** ADC:2042、2057、2060、2098–2107 により stderr に「実行できません」、stdout に terminal 行1本、rc=2になります。ただし stdout **全体が1行になるわけではなく**、既存の進捗行と、必要なら超過行も出ます。

**refuted：off＋CLI root が計測開始後に拒否される。** ADC:2023–2025 は parse_args 直後、started（2041）より前です。usage error には terminal 行が付きません。

## 開示行

**refuted：off が未指定・否定結果と混同される。** ADC:1925–1928 は「未確認」「抑止されうる」「triage」を含み、「探索を未実施」「が未指定」は含みません。env 指定の無視も明示しています。

**real／nit：句読記号の文体不統一。** ADC:1926 の `（）`／`；` は周辺の半角括弧と不統一です。半角へ揃えるだけで十分です。

CBR:1813–1825 の commit・件数・terminal の各 parser に、この開示行は一致しません。**findings・rc・掃除判断への影響はありません。**

## test の殺傷力と両層 stub

**refuted：新設テストが production 経路を丸ごと stub している。**

TA は実 `audit_with_offrepo`／実 `main`／実 argparse を通ります。usage テストだけは監査到達を禁止する trap、full の入力検査テストは snapshot 到達を禁止する trap を置いています。

TR:1639 は実子プロセスを呼ぶ argv spy、1653 は実処理に env spy と fake landed checker を組み合わせています。1678 は子の出力だけを fake にして実 `_audit` の parser・summary を検査します。1699 は実 ADC 子を通します。なお `_run_tool`（TR:182–189）は実 parser＋`assess` を呼び、CBR の `main` 自体を実行するものではありません。

**refuted：env trap が無効。** TA:4211 の instance attribute 差替えは、ADC:2039 の `os.environ.get` を捕捉します。読むだけで値を捨てる変異も4207で赤になります。

依頼文の「`os.getenv` 経由は捕まらない」は、この環境では成立しません。`/usr/lib/python3.10/os.py:772` の getenv は `environ.get(key, default)` に委譲します。ただし添字アクセスなど、すべての読出し形式を捕捉する trap ではありません。

**refuted：存在しない cat-file 関数への monkeypatch。** `_start_cat_file_batch` は ADC:638 に実在し、TA:4221 と一致します。

**refuted：M1 の API 条件不足。** TA:4253、4262 は off＋非空 roots を渡し、full の抑止と off の再表示を比較しています。

**refuted：TR の fixture が D247 条件5を満たさない。** TR:1707–1709 は外部ファイルの絶対 path を独立行として main に commit します。行頭・改行の境界があり、探索根そのものへの参照でもありません。`_write`／`_commit` の戻り値の使い方も正しいです。

**real／nit：full 拒否テストの snapshot trap は削除変異時に先行 Git エラーに隠れます。** TA:4311 は Git repo を作らず `tmp_path` を渡します。M3 では ADC:1710 の Git 失敗が先に rc=2 を返します。ただし4314の**専用エラー文言 assert が赤になるため、M3 は生存しません**。最小の改善は `_checked_git` にも禁止 trap を置くことです。現状でも production の拒否位置は正しく、must-fix にはしません。

## 変異の帰属

author:133–144 の anchor は、対象ファイル内でそれぞれ一意に存在します。M5 の `"GIT_CONFIG_NOSYSTEM",` は1件、M8 の全文3行も各1件でした。

以下の生死は**静的予測**です。実測結果は全件 unknown です。

| ID | 判定・予測 | 帰属、成果物への影響 |
|---|---|---|
| M0 | refuted：非等価化の疑い。SURVIVED予測 | ADC:1699 の docstringだけなら判定・出力に影響なし。 |
| M1 | refuted：killer不足。KILLED予測 | ADC:1714 を roots 検証に置換し、1733から off 条件も除く必要あり。TA:4256で、再表示すべき finding の消失を検出。片方だけの変更では登録した変異にならない。 |
| M2 | refuted：env 防壁による masking。KILLED予測 | ADC:2034 の off 分岐で `os.environ.get` を実行すれば TA:4207 が赤。APIが roots を無視しても捕捉する。 |
| M3 | real／nit：先行 Git エラーあり。ただしKILLED予測 | ADC:1702–1706を削除すると TA:4314の専用文言不一致で赤。rc=2だけなら見逃すが、現テストは見逃さない。 |
| M4 | refuted：env防壁による masking。KILLED予測 | CBR:1797から flag pair を除くと TR:1648の argv比較で赤。findings が変わらなくても検出。 |
| M5 | refuted：anchor重複・argvによる masking。KILLED予測 | CBR:220にenvを戻すと TR:1674で赤。off が走査を防いでも継承違反を検出。 |
| M6 | refuted：開示退行の見逃し。KILLED予測 | ADC:1924–1929を旧2行へ替えると TA:4236以降で赤。未指定との混同を検出。 |
| M7 | refuted：usage拒否削除の見逃し。KILLED予測 | ADC:2024–2025の**ブロック全体**を除けば TA:4297の監査到達 trap で赤。parser.error行だけの削除は構文エラーとなり、意味的変異に帰属できない。 |
| M8 | refuted：summary分岐の被覆不足。KILLED予測 | CBR:1803／1809／1840から field を落とすと TR:1691で全5 parameter が赤。JSON mode 欠落を直接検出。 |
| M9 | refuted：digest復元の見逃し。KILLED予測 | check_docs:789を旧値へ戻すと TD:9934で直接不一致。command pin の退行を検出。 |
| M10 | refuted：metadata到達の見逃し。KILLED予測 | ADC:1733の返却前に正しい引数で `_load_blob_metadata(root, original_findings)` を挿入すれば TA:4222の trap で赤。 |
| M11 | refuted：列挙関数到達の見逃し。KILLED予測 | 同位置で `_enumerate_offrepo_candidates(accepted, [])` 等を呼べば同 trap で赤。ただし空候補は実関数なら1125で返るため、これを「実 walk を起こした変異」とは報告できない。 |

**unknown／nit：最終 patch と観測 node 集合。** author:129 は予想と明記しており、具体 patch の全量・変異ログはありません。特に M1 の二箇所変更、M7 のブロック削除、M10／M11 の呼出し形を凍結しないままでは、構文エラーや引数エラーを契約違反の検出と誤帰属しえます。最小是正は既存の変異登録へ exact patch を確定することです。

## 既存 test の弱体化

**refuted：既存期待値の削除・skip・緩和。** TAは150行追加、TRは102行追加のみです。p04（TR:349–350）も2 assert の追加だけで、既存rc=0を維持しています。

TDの変更は581のdigest、663のsynthetic本文、9948／9953のbaseline、9954の超過fixtureだけです。上限6,204 bytes、超過6,205 bytes、期待rc=1は維持されています。

command は実測で6,181 bytes、最長105文字、指定SHA-256と一致しました。予算検査の弱体化はありません。

## 報告と実体

**refuted：差分規模の誤申告。** author:17 の ADC46行＝39追加＋7削除、CBR10行＝5追加＋5削除、TA/TR252追加＝150＋102はいずれも一致します。

**refuted：314件の算術誤り。** author:29–32 の166＋88＋38＋22＝314です。ただし pytest node と関数直接呼出しを合算した件数で、統合runnerの314 passedではありません。

**real：親の焦点走はTDを含め成功しています。** `focus-1.log:31–36` は **872 passed、3 skipped**。hold は次の実repo検査3関数に限定されています。

- `test_dev_wave_model_pins_accept_current_docs_contract`
- `test_normative_exact_section_pins_accept_real_repo`
- `test_real_repo_clean`

TD全体がholdで止まったわけでも、赤だったわけでもありません。authorのcleanup関連22関数は、このskip一覧に含まれません。

**unknown／nit：focusログだけでは裏付けられない緑主張。**

- author自身の166／88／38／22という個別実走履歴と直接呼出し方式。
- growth-hold解除tokenを使った実走の正当性。
- 独立した `python3 tools/check_docs.py` のrc=0。
- author時点の `git diff --check` のrc=0。

根拠は author:29–34、89 と、focusログの集計形式・3件holdです。親の872 passedをこれら別コマンドの実行証拠へ転用すると、検証記録が過大になります。author:91、164は統合走・変異・性能受理を親へ残しており、wave全体の完了を偽ってはいません。

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| 所見 | 判定・重要度 | 根拠／放置時の影響／最小是正 |
|---|---|---|
| 開示行の全角記号 | real／nit | ADC:1926。判定影響なし。周辺の半角表記へ統一。 |
| M3のsnapshot trapが先行Gitエラーに隠れる | real／nit | TA:4310–4314、ADC:1710。M3は文言assertで殺せるが、入口順序の被覆説明が過大になりうる。`_checked_git`にもtrap。 |
| 焦点走の場所の誤認 | real／nit | focus:4–14。OOM後の計算ノード成功をlogin成功と記録しない。 |
| exact mutation patch／観測node未確定 | unknown／nit | author:129–144。変異の赤を別理由へ誤帰属しうる。既存登録のpatchを確定。 |
| author独自実走の履歴・単独checker緑 | unknown／nit | author:29–34、89、focus:31–36。親の焦点走で裏付けられる範囲と分けて記録。 |
| 受理集合退行、fail-closed不備、trap名誤り、既存test弱体化 | refuted／修正不要 | 上記該当箇所。成果物を壊す変更は確認できず。 |

## 総括

**U1の静的レビューではmust-fixなし。** offのcore保持、fullの既存経路、rc契約、二重防壁、新設テストの主要killerは成立しています。

残る注意点は、M3の被覆説明、変異patchの正確な帰属、焦点走の実行場所・証拠範囲です。変異の実測生死とwave全体の受入完了は、このレビューでは認定しません。
