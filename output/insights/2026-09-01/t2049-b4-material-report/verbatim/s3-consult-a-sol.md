## 総括

最大の欠陥は、planned artifact が 1 件でも欠けると report 自体が生成されず、§7.1 が禁じる file-drawer を再現できる点である。  
加えて、完全射影検査は埋込み source bytes の存在しか保証せず、Markdown と行フィールドの誤変換を検出できない。  
`floor=None` は値の捏造ではないが、正規コマンドからは `protocol_violation` 以外の 3 分類が到達不能であり、brief の 4 分類要件と両立しない。  
凍結 5 file、prereg、producer、`layer3_report.py` の変更は計画にないが、`--output-root` の path alias により campaign へ書き込む経路は残る。

## 所見

### 1. planned artifact 欠落または producer rejection で report が丸ごと消える

深刻度: Critical

根拠:

- `s2-plan.md:43-46` は `assemble_b4_raw_analysis()` の rejection を partial report にせず `B4MaterialReportError` にする。
- `p3_b4_raw_record_producer.py:1908-1917` は planned leaf が 1 件欠けただけで assembly 全体を拒否する。
- 同 `:2047-2057` は assembly rejection の `attempt_id` を `None` にして返す。
- 実在する producer 経路でも rejection 後に artifact が作られない。`test_p3_b4_raw_record_producer.py:1101-1115` がその positive control である。
- これは `prereg-s7.md:5-9` の「未到達・crash・protocol violation を含め全件報告」と正面から衝突する。

壊れ方の具体例:

1. manifest に 201 block がある。
2. 200 planned artifact は存在する。
3. attempt 17 は producer が `B4RawRecordRejection` を返し、planned leaf は存在しない。
4. assembler が `INCOMPLETE_SET` で全体を拒否する。
5. プランは report error に変換し、`report.json` も `report.md` も作らない。

この場合、走らせた可能性のある 200 block と欠落した block の双方が報告から消える。計画中の `test_required_row_fields...` は terminal-absent や ABORT の「artifact が存在する行」しか扱わず、この経路を検査しない (`s2-plan.md:166-170`)。

最小修正案:

- assembly 成功を report 作成の前提にしない。
- manifest と planned mapping から先に全 201 block、402 arm の枠を作り、欠落 leaf は `artifact_availability=absent` と assembler rejection を伴う fail-closed report にする。
- raw 値や元の producer rejection 理由を推測せず、取得不能と明記する。

なお、元の `B4RawRecordRejection` の全値は永続化されないため、producer 無変更かつ publication-root-only のまま完全に復元することは不可能である。これは実在する契約不整合であり、単なる仮想リスクではない。

### 2. 完全射影検査が表示値の改変を検出しない

深刻度: High

根拠:

- `s2-plan.md:77-83` の検査対象は source UTF-8 の SHA-256 multiset、件数、順序である。
- 表示行の個別フィールドと source/ledger の値との一致検査は規定されていない。
- mutation test も drop、duplicate、source UTF-8 rewrite に限られる (`s2-plan.md:184-193`)。
- producer source は `terminal_reason`、throughput、各 receipt hash、evidence issues、non-guarantees まで持つ (`p3_b4_raw_record_producer.py:1354-1434`)。
- D829 は raw bytes をどこかへ残すだけでなく、view 側で値を削除・正規化しないことを要求する (`decisions-extract.md:111-125`)。

壊れ方の具体例:

producer の `terminal_reason="diff-quarantine"` を、行と Markdown では `null` または「不在」に変え、`source_artifact_utf8` だけ元のまま残す。計画中の multiset、件数、順序、source hash はすべて通る。読み手が通常見る表は誤りなのに「完全射影検査済み」となる。

最小修正案:

- exact UTF-8 に加え、producer source object を無加工の構造化値として report に置く。
- 行の派生フィールドごとに、その source/manifest/registry 上の出所と値を照合する。
- terminal reason、campaign id、hash、anomaly class などの一値 mutation を、実際の public document builder 経路で拒否する。

これは中央契約を証明するための検査であり、仮想リスク向けの一般 gate 追加ではない。

### 3. 正規コマンドから 4 分類のうち 3 分類が到達不能

深刻度: High

根拠:

- 正規経路は常に `floor=None` を渡す (`s2-plan.md:49-52`)。
- evaluator はその時点で必ず `FLOOR_DOMAIN_ERROR` の `protocol_violation` を返す (`p3_b4_analysis_path.py:349-353`)。
- renderer の 4 分類テストは合成した verdict を直接渡すだけである (`s2-plan.md:172-182`)。
- プラン自身も成立・不成立・判定不能の report は現在作れないと認める (`s2-plan.md:270-273`)。

したがって sanctioned command の実装が実際に生成できるのは `protocol_violation` だけである。成立、不成立、判定不能は renderer-only fixture にしか現れない。これは規律 3 の観点でも、正規経路の性質を後段の合成 fixture で代用する検査になっている。

非有意を「不成立」へ吸収する既存 evaluator の欠陥は見つからない。到達できる正当な floor があれば、片側 off 有意だけが `not_established` となり、それ以外の非有意は `indeterminate` になる (`p3_b4_analysis_contract.py:712-737`)。

最小修正案:

- CLI floor や既定値は追加しない。
- 「現 wave は prereg 未発効状態の protocol-violation material report だけを生成する」と brief、schema、受入条件を狭めるか、4 分類が必須なら権威的 floor artifact が実在するまで完成扱いにしない。
- renderer-only 4 分類テストを、正規コマンドが 4 分類を生成できる証拠として扱わない。

`floor` の値自体や model hash、予算消費については、計画は `availability=absent,value=null` とし、0 や空文字を捏造していない (`s2-plan.md:67,103,231-236`)。この点は値 0 と不在を区別できる。

### 4. output-root 非交差検査が path alias と祖先方向を閉じていない

深刻度: High

根拠:

- 指定された output root は「そのまま使う」とされる (`s2-plan.md:118-120`)。
- 拒否条件は output root が arm campaign 自身または配下の場合だけである (`s2-plan.md:121-124`)。
- symlink component、realpath、output root が campaign の祖先である場合は規定されていない。
- `layer3_report.py:193-198` は campaign 配下の全 file を artifact refs に含めるため、campaign 内への report 混入は成果物 digest を実際に変える。

壊れ方の具体例:

- `/tmp/report-link -> <arm-campaign-root>` を用意し、`--output-root /tmp/report-link/reports` を渡す。lexical 比較では campaign 外だが、実書込み先は campaign 内になる。
- または `--output-root <...>/output/exploration/campaigns` とし、arm campaign の祖先へ `report.json` と `report.md` を置く。計画された片方向比較では拒否されない。

最小修正案:

- output root と全 arm campaign root を canonical な実体 path で比較し、symlink component を拒否する。
- `out == campaign`、`out` が campaign 配下、campaign が `out` 配下の三方向をすべて拒否する。
- 書込み時も no-follow の directory handle に束縛する。

これは新規 writer が現に作る path alias 欠陥への限定修正であり、一般化した official-root gate の追加ではない。

### 5. 凍結 file と既存 inventory 検査

深刻度: 凍結 file への直接波及なし

計画どおりなら `_SOURCE_CLOSURE_PATHS` の 5 file、prereg、producer、`layer3_report.py` の bytes は変わらない。新規 module が既存 API を呼ぶだけでは closure receipt の hash も変わらない。

該当する既存検査は次である。

- `test_p3_b4_analysis_path.py:596-635`  
  `test_private_closure_assembler_is_stable_and_binds_consumer_result`
- 同 `:637-649`  
  `test_closure_receipt_fails_closed_when_a_member_is_absent`
- `test_p3_b4_analysis_prereg_consumer.py:442-453`  
  `test_missing_source_closure_member_fails_closed`
- `test_p3_b4_analysis_path.py:357-371`  
  `test_public_evaluate_analysis_production_caller_inventory_is_pinned_not_closed`

最後の検査は `evaluate_analysis` の直接 caller を固定するが、計画は外側の `evaluate_b4_artifacts` を呼ぶため赤にならない。

新規 `campaign/*.py` を走査する検査として、以下も確認したが、file 追加だけを拒否する exact inventory ではなかった。

- `test_p3_exploration_namespace.py:124-140`
- `test_p3_build_authority_cli.py:1191-1197`
- `test_s8b_floor_campaign.py:6364-6477`
- `test_s8b_oracle_manifest_contract.py:39-104`

ただし CLI test が `env=` 付きで `subprocess.run([sys.executable,...])` を使う場合は、`tools/check_subprocess_bytecode_guard.py:315-335` により `-B` または `PYTHONDONTWRITEBYTECODE` が必要になる。

## 親 brief への所見

- **(P1): 条件付きでのみ成立。** publication loader が固定 3 leaf だけを読むことは `p3_b4_prerun_issuer.py:1015-1033` で支持される。ただし任意 output root の安全性は parent では証明されず、plan の非交差検査にも前記 alias 欠陥がある。
- **(P2): 採用不可。** brief は publication root だけを入口とし判断値を caller から受けないとする一方 (`s1-brief.md:58-62`)、`--floor` 必須入力を provisional 採用している (`:73-75`)。これは自己矛盾であり、D1060 の「1 欄も埋めない」決定 (`decisions-extract.md:227-244`) を caller 自己申告で迂回する。plan が P2 を拒否した点は必要な修正である。
- **(P3): 静的には成立。** qsub、build、性能測定を起動しない file 直起動 CLI なので sanctioned-path allowlist 変更は不要である。
- **(P4): 不在値には成立するが、producer rejection には成立しない。** model hash、初期 snapshot hash、予算消費を null/absent にする方針は適切。ただし永続化されない producer rejection は publication-root-only consumer から取得できない。

不変条件 1〜4 と 7 は計画上維持される。不変条件 5 は所見 1、2で破れ、不変条件 6 は所見 3の到達不能問題を持つ。

46 passed からの一般化は限定が必要である。

- `test_p3_b4_raw_record_producer.py:1550-1628` は production producer、assembler、evaluator を実際に合成しているため、「fixture 上の producer→analysis API 経路が生きている」ことは支持する。
- ただし fixture は 1 block の real seed と 200 block の replica である (`:881-917`)。
- さらに evaluator には test caller が `floor=0` を注入している (`:1576-1583,1620-1627`)。正規 report command の `floor=None` 経路とは異なる。
- したがって 46 passed は、正式 publication、planned artifact 欠落、producer rejection、report generator、4 分類到達性までは支持しない。「producer から分析判定まで一般に生きている」は広すぎる。

現在の worktree では `output/campaigns/` に B-4 名を持つ artifact は静的に見つからず、producer は実際に 2076 行、HEAD は brief 記載の `24014bdb2`、worktree は clean だった。28.44 秒と qsub request 自体は再実測していない。

## scope 外として返すもの

- certified-selection connection の実装は要求しない。
- 元の producer rejection 全値を後から完全射影するには、producer 変更または durable rejection ledger が必要であり、現 wave の不変条件 3を越える。これは実在欠陥だが、実装拡張はユーザー裁定へ返すべきである。
- 正当な floor artifact の生成・接続も本 wave で捏造してはならない。4 分類を必須にするなら後続 prerequisite である。
- 一般化した official-root admission、仮想リスク用 inventory、certifying validator の追加は所見に含めていない。

## 検査できなかったこと

read-only sandbox のため pytest、CLI subprocess、writer の実走は行っておらず、緑とは判定していない。  
28.44 秒、request `963546.nqsv`、他 branch 3 本の現時点の状態は再検証していない。  
新規 module は未実装のため、その実 line 番号ではなく `s2-plan.md` の計画行を検査した。