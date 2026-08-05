---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t481-pegasus-admission
seq: 3
title: [T-481] Pegasus 実行体の一律判定を三値 admission registry へ再設計した — 狭める作業の途中で、その一律判定自体が 6 通りの綴り替えで抜けられていたと判明した (コード + docs、branch worktree-dev-wave-t481-pegasus-admission)
---

## 本文

- **ユーザー裁定 (2026-08-05 /rulings、[T-481] 択 (b)) をそのまま実装した。** [T-482] は (a) を
  実装し (b)(c) の比較を決め、[T-483] は設計入力として同じ判定経路で閉じた。設計は
  {{D:pegasus-admission-registry}}。
- **本 wave 最大の発見は「狭める前の壁が既に穴だらけだった」ことである。** 段 1 と段 4 で
  実 hook を subprocess として起動して測ったところ、ログインノードで拒否されるはずの綴りのうち
  6 系統が実際には通っていた (逐語 = insights)。詳細と恒久対応は
  {{F:pegasus-blanket-rule-porous}}。一律 prefix 判定を明示 registry へ置き換える作業は、
  この 6 系統のうち 4 系統を同時に閉じた。残る 4 系統 (cwd/symlink・`env -S` 文法・
  shell `-c` ネスト深さ・`systemd-run` 等の未解析 launcher) は scope 外として裁定へ返す。
- **[T-481] の起票前提が実測で覆った。** 「land 済み login 手順が機械拒否される過剰拒否」
  という理解だったが、`collect_receipt.py` は scheduler stderr を全文メモリへ読むため
  runbook §7.0 の規範では `unknown` = 計算ノード行きに当たる。**拒否している hook の方が
  規範に忠実で、食い違っていたのは手順書の方**だった ({{F:norm-procedure-barrier-three-way-drift}})。
  この事実は段 2 起草の後に判明したので、追記として段 3 のレンズへ渡し段 4 で再裁定した。
- **したがって本 wave では許可へ反転させた entry が 1 つも無い。** 族の仕組み (三値 registry・
  証拠 field・未登録は fail-closed・悉皆 meta-test) は入れたが、症状である
  `collect_receipt.py` の拒否は解いていない。無界入力の entry を実測なしに `local-ok` と
  記録するのは防壁を緩める方向の変異だからである (規律 2)。入力 cap と実測は裁定へ返す。
- **分類の実測が構造的に塞がっていることを実測で確定した。** 計算ノードでは §7.0 の測定手順が
  成立せず、wave 自身の worktree で hook を書き換えても Bash 面には効かない (支配するのは
  main checkout の hook)。`DW-O19` に従って一時変異・即復元して測った。迂回はしていない。
  詳細は {{F:classification-bootstrap-deadlock}}。ユーザーに 1 回の実測を依頼する
  スクリプトを用意したが、本 wave の完了条件からは外した。
- **段 3 の敵対 2 レンズは両方 NO-GO を返し、real 19 件を出した。** うち親が real・scope 内と
  裁定したのは 8 件で、7 件を裁定パッケージへ返した。レンズ A の「`-m` の後続を一律 data に
  すると `cProfile` 系の実行対象が消える」は、親が独立に導出していた「1 規則で 3 症状が閉じる」
  という結論を**反証**した。裏取りしたところ `python3 -m cProfile <pegasus path>` は
  **変更前から既に通っていた**。
- **段 6 は fix を 3 巡した。** 1 巡目は親の prompt が「既存テスト」を tracked 限定と書かず、
  子が同 wave の新設 assert を保護対象と解釈して正しく fail-closed で停止した (F112 の再発)。
  2 巡目で実装、焦点再レビューが regressed 2 件を含む real 7 件を出し、3 巡目で単調性
  (変更前の受理集合を緩めも狭めもしない) を不変条件として揃えた。3 巡目は復元を過大に適用して
  land 済みテスト 2 本を赤くしたので最小是正を 1 回入れた ({{F:fix-prompt-restore-without-exceptions}})。
- **親は実装子・レビュー子の申告を実測で置き換えた。** 実装子も fix 子も計算ノードへ dispatch
  できず (codex sandbox から `NQSconnect: [API EACCTAUTH]`)、pytest を 1 node も実走していない。
  テスト実測と受理集合の照合はすべて親が行った。
- **変異は 6 本を事前登録し、初回で M4 / M5 が KILLED、M1 / M3 / M6 が MISMATCH、M2 が SURVIVED
  だった。** M2 の生存は等価変異ではなく他層の mask で、fix で入った残余走査が同じ入力を先に
  拒否していた。`DW-M02` に従い初回結果を erratum として残し、実効 gate へ両層変異 (M2b) として
  再照準した v2 で M1 / M3 / M6 が KILLED、M2b は期待 node 3 本のうち 2 本が赤で MISMATCH。
  赤になった 2 本は借用保護の pin そのものであり kill の意味論は成立している。3 本目は
  非拒否 site の検査で重量判定が走らない場所であり、親の過大登録だった。
- **`probes/` の 4 実行体を実装子が発見した。** 親の inventory は直下 18 本だったが、再帰条件では
  22 本だった。4 本は証拠が無いので `unknown` で登録し現行の拒否を維持した。さらに焦点再レビューが
  mode 0644 の `.pbs` 2 本を inventory 条件が取りこぼすことを指摘し、`.pbs` と shebang と
  `stat` mode を条件へ加えた。

## 次の一手差分

### 完了

- [T-481] 族再設計を実装した。一律 prefix 判定を三値 admission registry
  (`local-ok` / `dispatch-required` / `unknown` + `reason` / `primary_gate` / `evidence`) へ置換し、
  未登録は fail-closed、`_SANCTIONED_PATHS` は registry から導出、悉皆 meta-test で inventory を
  同期する。設計は {{D:pegasus-admission-registry}}。**許可へ反転した entry は無く**、
  残件は下記の新規 5 件へ分割した。
  remaining: none
  base: 584fc3ecaa65a1520201b8867225abd1160733387625bf908e2ddc24f75c2074
- [T-482] (a) を実装した。`docs/pegasus-runbook.md` §7.0 に「測定が保証するのは記録した argv と
  入力だけであり、path 粒度の admission は任意 argv を保証しない」を明記した。(b)(c) の比較は
  {{D:pegasus-admission-registry}} 却下節で (b) を退け、(c) の実装単位を
  {{T:collect-receipt-input-caps}} として起票した。
  remaining: none
  base: 8b0268a8b86cbb8e90735fb983ed896bed10b57052ae57c87150ee6b8c14d590
- [T-483] `-m <module>` の実行体を module に固定する規則で sanctioned 借用を閉じた。
  同じ判定経路にあった変更前からの迂回 (`-m cProfile|pdb|trace|runpy|pydoc|doctest|unittest`、
  `pytest.__main__` / `_pytest.main`、interpreter option の値による script 隠し) も同時に閉じた。
  remaining: none
  base: 0121f52529be60e679bca1cb1098d37700895df5984fae8688d689e309b4d164

### 新規

- {{T:guard-bash-residual-bypasses}} **P2・新規 (ユーザー裁定待ち)**:
  本 wave が実測で確認した、変更後も残る重量処理防壁の迂回 4 系統をどう閉じるか裁定する。
  (a) `cd hooks && python3 ../tools/pegasus/<compute-only>` — 重量判定経路が cwd を追跡しない
  (防護 tree 側には cd 追跡が既にある)。(b) `env -S 'pytest\_-q'` — GNU `env -S` の文法と
  `shlex.split` の差。(c) `bash -lc` の 3 段ネスト — 再帰が `depth < 2` で打ち切られ許可へ倒れる。
  (d) `systemd-run --user --scope -- pytest -q` — wrapper 集合に無く子を解析しない。
  **(d) は runbook §7.0 の測定手順そのものの綴りである**ため、閉じ方は測定経路の裁定と同時に決める。
  いずれも変更前から通っており本 wave が作った回帰ではない。逐語 = 本 wave の insights
- {{T:collect-receipt-input-caps}} **P2・新規**:
  [T-482] 択 (c) の実装単位。`tools/pegasus/collect_receipt.py` の入力を有界にする。
  対象は scheduler stderr の bytes と保持行数、3 つの JSON の bytes、manifest の file 件数、
  path 総 bytes と個別 path 長、receipt の推定 bytes。`stat` 後・materialize 前に fail-closed で
  拒否し、cap 上限の入力で §7.0 の実測を取ってから registry を `local-ok` へ昇格する。
  cap 境界と `cap+1` のテストを同時に置く。`collect_t126_qualification.py` も同型だが
  実 artifact が無いため代表入力を作れず、別立てとする
- {{T:pegasus-measurement-surface}} **P2・新規 (ユーザー裁定待ち)**:
  資源分類の恒久的な測定経路を決める。現状は「計算ノードでは §7.0 の手順が成立しない /
  wave の Bash 面は main checkout の hook に支配される」ため、ユーザー端末が唯一の正規経路である
  ({{F:classification-bootstrap-deadlock}})。択は (a) 現状追認し測定をユーザー手番として明文化、
  (b) 測定専用の bounded surface を設ける、(c) 計算ノードで動く測定手順へ §7.0 を改訂する
- {{T:dev-wave-fix-prompt-contract}} **P3・新規 (ユーザー裁定待ち)**:
  `docs/dev-wave/workers.md` の `DW-S06-B` へ 2 点を追記する。(a) 既存テストは
  `git show HEAD:<path>` に在るものに限り、同 wave の未 land テストは fix の編集対象だと書く
  (F112 の再発防止)。(b) 変更前挙動の復元を指示するときは、拒否側の再現だけでなく変更前の
  許可側の例外も同じ粒度で列挙する ({{F:fix-prompt-restore-without-exceptions}} の恒久対応)。
  **段 8 で実装を試みたが `docs/dev-wave/**` の byte 予算 25200 を 208 bytes 超過して取り消した。**
  予算引き上げも他節の安全義務削減も規約が禁じ、外出しは dev-wave 系では読み込み削減 0 なので
  採れない。裁定は (a) 予算の独立審査、(b) 既存節の縮約先の指定、(c) 追記見送りのいずれか
- {{T:pegasus-admission-registry-authority}} **P3・新規 (ユーザー裁定待ち)**:
  admission registry の正本配置を決める。現在は `hooks/guard_bash.py` 内にあるが、
  runbook §7.0 の実測表・`tools/pegasus/README.md` の手順・`dispatch_compute.py` の TASKS との
  ドリフトを止める機械検査が無い ({{F:norm-procedure-barrier-three-way-drift}})。
  択は (a) 現状維持 + 人手同期、(b) `tools/pegasus/` 側の machine-readable registry を hook と
  `check_docs.py` が投影する。**現行 sanctioned 5 本のうち §7.0 実測があるのは
  `fetch_third_party.py` だけで、残り 4 本は `legacy-admitted (未実測)` である。**
  規範を厳格適用して 4 本を落とすか grandfather を追認するかも同時に裁定する
