## 総括

静的検査では、prune 撤去そのもの、timeout 予算、F660／登録簿の判断は成立している。  
must-fix は、追加する 2 test node の受入所要台帳が変更面から欠落している点と、T-1998 の事前登録 digest への波及が計画されていない点である。  
現行行番号はほぼ一致するが、plan 内に解決不能な file anchor が 2 箇所ある。  
pytest・bash snippet・Pegasus 実測は実行しておらず、緑とは判定していない。

## real 所見

1. **追加する 2 test node が `acceptance_duration_ledger.json` の変更面から欠落している。**

   - 根拠: plan は既存 test file に 2 node を追加する (`s2-plan.md:173-185,187,210`) 一方、「変更ファイルを2件に限定」「台帳不要」としている (`:173,225`)。現行台帳の A-5 node は既存 7 件だけ (`orchestrator/tests/acceptance_duration_ledger.json:35-41`、総数は `:22159`)。
   - repo 正本は、新規 node を `tools/update_acceptance_duration_ledger.py --add-only <JUnit>` で登録することを要求する (`docs/failures.md:23433-23455`)。被覆 gate は実 collection と台帳を照合する (`orchestrator/tests/test_acceptance_schedule_order.py:680-716`)。
   - 何が壊れるか: 新 node が未知所要のままになり、受入 shard の割付台帳が不完全になる。被覆率の余裕次第では同 gate も赤になる。
   - **成果物影響:** plan の「コード1 file＋テスト1 file」は不足し、受入所要台帳を含む3実装 file が必要になる。
   - 修正案: 実走 JUnit 取得後に `orchestrator/tests/acceptance_duration_ledger.json` を `--add-only` で更新し、`test_acceptance_schedule_order.py` を焦点走へ含める。新 test file は作らないため、既存 `_run()` (`test_a5_second_boot_job_contract.py:374-389`) はそのまま利用でき、plain-runner allowlist の変更は不要。

2. **job body digest の T-1998 閉包が plan から落ちている。**

   - 根拠: T-1998 submitter は共有 A-5 body を動的に hash し (`tools/pegasus/submit_t1998_balanced_stock_inline.sh:44-45,91-92`)、submit receipt と qsub binding に運ぶ (`:112-124,172-180`)。job は実行 bytes・commit blob・binding の一致を要求し (`tools/pegasus/a5_second_boot_backoff_sweep.sh:378-388`)、同 digest を reservation へ記録する (`:414,423-449`)。
   - T-1998 consumer はその値を外部の事前登録値と exact 比較する (`orchestrator/campaign/t1998_stock_inline_pair.py:909-919`)。したがって body の1 byte以上の変更で旧 `0ef4d41e…` は必ず無効になる。
   - 何が壊れるか: 旧 digest を使った T-1998 事前登録が存在すれば、新 body が生成した producer root は `launcher-script-identity-mismatch` で拒否される。
   - **成果物影響:** 次回 T-1998 測定の preregistration は、着地後の新 job-body digest で作り直す必要がある。
   - 修正案: code を増やすのではなく、plan／handoff に「着地後 digest の再導出と prospective preregistration」を明記し、焦点対象へ既存 `test_t1998_launcher_contract.py` と `test_t1998_stock_inline_pair.py` を加える。現時点では実値の事前登録も正式測定も未実施 (`output/insights/2026-09-08_t1998-stock-inline-parts/README.md:144-151`) なので、既存の適格 T-1998 測定成果物が壊れる事実はない。

3. **plan の file:line anchor に解決不能な名前が2件ある。**

   - `s2-plan.md:16` の ``rekt:126`` は実在 path でない。正しくは `tools/pegasus/a5_second_boot_backoff_sweep.sh:126` で、逐語 `local remove_rc=0` は一致する。
   - `s2-plan.md:101` の ``test_a5 rospector:249-270`` も実在しない。正しくは `orchestrator/tests/test_a5_second_boot_job_contract.py:249-270`。
   - 何が壊れるか: exact anchor を入力にする author／mutation 手順が対象 file を解決できず、削除箇所または budget 検査を取り逃がす。
   - **成果物影響:** 実装差分または変異台帳が誤った anchor に束縛される。
   - 修正案: 上記2表記を正規 path に直す。その他の現行 anchor、すなわち job `:123-170,126-127,130-169,178,180-184`、A-5 test `:291-303,297-298,374-393`、B-10 先例 `:46-88,1752-1785` は数字・逐語とも一致した。

## 推測

- repo 外で既に旧 `0ef4d41e…` を prospective T-1998 事前登録へ転記している可能性は静的検査では否定できない。repo 内正本は「実値未確定」としているため、これは推測であり real な既存破壊には数えない。
- `collect_receipt.py` は渡された staging を再帰列挙する (`tools/pegasus/collect_receipt.py:76-91`) が、calibration 固有の3 JSONを要求する (`:107-141`)。A-5 からの callsite はなく、今回の三 artifact の consumer とは認定できない。
- repo 外の手動 collector が `env/ccbench-worktree-prune.*` の存在を期待している可能性もあるが、repo 内には根拠がない。

## nit

- `worktree-remove.rc`、`prune_rc`、`ccbench-worktree-prune` の断片検索でも、追加の live な A-5 runtime consumer は見つからなかった。現行は A-5 producer、A-5 の逐語契約、B-10 の別 producer／別 fixture、過去 insight だけである。
- brief の「consumer は2テストだけ」は不正確で、A-5 の直接 consumer は静的契約テスト1件、`test_backoff_extended_sweep.py:1785` は B-10 の別成果物を読む consumer である。変更漏れは生じないが、閉包説明は分けるべき。
- brief は実 git fixture を「1本」とする (`s1-brief.md:49`) が、plan は成功・失敗の2 test functionを提案する。失敗側は receipt と rc 伝播という明示 scope (`s1-brief.md:25-37`) を閉じるため、scope 膨張とは判定しない。
- full hash の検索結果には submit／reservation 以外に T-1998 の過去裁定逐語もある (`output/insights/2026-09-08_t1998-stock-inline-parts/verbatim/s4-ruling.md:148-154`)。歴史記録なので更新対象ではない。

## 親 brief への反証

- **変更面アンカー:** `s1-brief.md:46-49` の現行数値と逐語は実在し、反証できない。ただし plan 側の2つの壊れた表記は real 所見3のとおり。
- **pin／consumer 閉包:** named cleanup artifact の直接 consumer 追加は見つからなかった。一方、job body digest の T-1998 preregistration 閉包を落としている点、および「2テスト」の数え方は反証成立。
- **成果物の形:** `s1-brief.md:72-75` の「コード1＋テスト1」は受入所要台帳を欠くため反証成立。
- **timeout:** `WORKTREE_CLEANUP_CAP_S=120` を据え置く限り、現行 `6150 + 1049 = 7199 < 7200` (`a5_second_boot_backoff_sweep.sh:10-27`) と test (`test_a5_second_boot_job_contract.py:249-270,348-349`) に抵触しない。cap を変えない plan は正しい。
- **F660／登録簿:** 反証できない。registry entry は path と4 metadata fieldだけ (`admission_registry.json:10-15`)、loader に sha256 field はない (`tools/pegasus_admission_registry.py:18-21,97-116`)。hook も target path と class だけで判定する (`hooks/guard_bash.py:1205-1215`)。既存 body の本文編集は新規実行体ではなく、entry 変更不要。
- **D1804:** launcher は変更後も同じ A-5 path を直接再利用するため、契約テスト `test_t1998_launcher_contract.py:56-66` は構造上壊れない。「1 byte も変えず」は T-1998 wave が body を fork／改造しないという変更単位の制約であり、別変更単位としての本 wave を永久凍結する pin ではない。ただし新 digest の事前登録波及は real 所見2へ追加すべき。
- **Pegasus 実測なし:** 反証できない。D1700 は A-5 を再投入しないと明記する (`docs/decisions.md:51805-51806`)。今回の欠陥機序は実 git fixture で直接再現でき、T-1998 の正式測定は別の人間認可手番である。
- **scope:** 汎用掃除機構、新 gate、互換層、登録簿 schema の追加はなく、plan のローカル helper と2挙動 test は本題を閉じる範囲内である。削るべき一般化は見つからなかった。