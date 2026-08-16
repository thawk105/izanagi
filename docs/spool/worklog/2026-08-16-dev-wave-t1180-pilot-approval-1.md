---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1180-pilot-approval
seq: 1
title: 床値 pilot の承認を投入引数で渡せるようにした — 承認値を submission nonce に束縛し、receipt 拡張は 2 レンズの実証で捨てた (コード + テスト + docs、branch worktree-dev-wave-t1180-pilot-approval、変異 matrix = 9/9 KILLED)
---

## 本文

- 変更前は `tools/pegasus/floor_campaign.sh` が driver へ `--mode pilot` と `--protocol` しか渡さず、
  driver の承認 gate によって**標準投入経路から床値 pilot が 1 回も起動できなかった**。
  CLI flag は既に存在しており、欠けていたのは投入経路の運び手だけである。設計判断は
  {{D:pilot-approval-argv-nonce}}。
- 裁定は 2026-08-16 07:1x の一括裁定 #43 §3.3 (authority=user、再裁定不要)。控えは
  `dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full-43rulings.md` §3.3。段 4 直前の inbox 再走査で、
  同日 18:50 の控えが「#43 で決着済み。`flagship-cc-experiment-blockers.md` §4 は台帳反映前の情報で
  あり再裁定していない」と明記しているのを確認した (blockers 側は択 (a) 承認 receipt を推していた)。
- 段 2 プランは「submit receipt に承認 field を足し env と一致を要求する」を推奨したが、
  **段 3 の敵対 2 レンズが独立に同じ致命欠陥を出した** — receipt の exact key 集合は job shell と
  `certified_writer_admission._FLOOR_KEYS` の 2 箇所にあり、後者は driver より前に走るため、
  field を足すと承認付き job が driver 到達前に全滅する。親が `certified_writer_admission.py` を
  読んで裏取りし、P2 を不採用にした。D356 が同型の主張を既に却下していることも根拠に加えた。
- 親は段 4 で**承認 env の値を固定 literal でなく submission nonce にする**追加裁定を置いた。
  scheduler が `-v` 指定外の環境を継承するかは未実測であり、固定値だと投入者の shell に残った
  変数だけで全投入が承認済みになりうる。nonce は投入器が実行時に生成するため ambient 環境には
  構造的に存在し得ない。新しい artifact も schema も増やさない。
- **親の段 1 実測 3 件が敵対レンズに反証された。** (i) 「両 script の bytes を pin する台帳・test は
  0 件」は一括表現として誤りで、正しくは「固定 digest の trust root は無いが、floor job script は
  source commit と per-submission receipt へ**動的に**束縛済み。submitter 自身は未束縛」。
  (ii) 「`certified_writer_admission` は path 束縛のみ」も誤りで、同 module は receipt の
  `job_script_sha256` と commit blob を照合している。(iii) 「floor run 実績 0 件だから実害ゼロ」は
  分解が必要で、正しくは「完了測定と一回性 key の消費は 0 件。投入は 3 件あり queue 資源消費は既発生」。
  いずれも編集面の結論 (再 pin 不要) は変えなかった。
- 段 6 の敵対レビュー 2 本も独立に同じ must-fix へ到達した。追加テストが shell の承認 gate 断片と
  driver 断片を**テスト側で連結**して実行しており、実ファイル上の両断片の間と冒頭 `unset` 行が
  1 度も実行されない。そのため「gate 通過後に承認 env を nonce で再代入する」1 行と
  「冒頭 `unset` に承認 env を足す」1 行が緑のまま通った。親が実コードで裏を取り、
  変異 2 件 (N7 / N8) を追加登録したうえで fix を投じた。
- fix は**実装 bytes を 1 byte も変えず**、承認変数のファイル全体でのデータフロー (出現は 3 箇所だけ、
  代入・`unset`・`export`・`declare`・`local` は 0 件) と、実ファイル上の順序
  (static admission → 承認照合 → receipt 検査 → build → driver) を固定するテストで閉じた。
  fix 後の shell 差分 sha256 は fix 前 snapshot と完全一致することを親が独立に確認した。
- 焦点再レビューは GO。残余の nit 1 件 ({{T:unset-set-pin-too-broad}}) は受理集合も成果物値も
  変えないため次の一手へ回した。
- **この wave が保証しないことを明示する。** 作ったのは「標準投入経路で明示 token を要求する
  運用 gate」であって、承認主体の人間性を認証する gate ではない (D356)。automation が投入器を
  承認引数付きで起動する経路、raw `qsub`、driver 直接起動、Python API 直接呼出し、
  投入器自身の `assume-unchanged` drift は保証範囲外である。実 scheduler への env 到達も
  本 wave では未実測で、最初の実投入時に確認する。
- 変異 matrix は使い捨て worktree (`tools/mutation_worktree.py`、runner=dispatch) で 2 回走らせた。
  権威は 2 回目で **9/9 KILLED、MISMATCH 0、SURVIVED 0、baseline PASSED、wrapper rc=0** (対象 commit
  `2d3fc157`)。台帳は `output/insights/2026-08-16_t1180-pilot-approval/mutation/`。
  1 回目は期待 node を静的に確定できず **probe** とした (KILLED 4 / MISMATCH 5 / SURVIVED 0)。
  ずれはすべて「期待より多く落ちた」側で、原因は (a) fix が新設した構造テストが承認変数の
  出現集合を固定しているため出現位置を変える変異すべてに当たること、(b) ambient 非継承テストが
  driver argv も独立に確認するため job script 側の変異でも赤になることの 2 つである。
- 受入全走の 1 回目は 1 failed / 11866 passed / 92 skipped で赤になった。落ちたのは
  `test_mutation_harness.py::test_sigterm_handler_stops_child_and_restores_active_mutation` 1 件で、
  SIGTERM を送る前に子が rc=1 で終了しており `128 + SIGTERM` を観測できなかった。
  32 並列 (`gw28`) の負荷に依存する競合である。本 wave の差分は `tools/pegasus/` の 2 script と
  その契約テストだけで当該 test へ到達しえず、**同 file を単独実走すると 80 passed** で再現しない。
  帰属せずフレークとして再投入した。
- 背景 job の運用で 2 つ躓いた。(i) `dev_wave_codex.py` の `--lane` は consult 段専用で、
  review 段に付けると起動前 rc=2 になりレビュー 2 本が同時に落ちた。(ii) 背景待ち手の完了通知が
  **7 回連続で偽**だった (存在しないファイルの byte 数と、自分の shell より未来の mtime を出した)。
  成果物実在・完了印・producer 生死の 3 点照合で毎回検出し、Monitor へ切り替えて凌いだ。

## 次の一手差分

### 完了

- [T-1180] 標準投入経路から床値 pilot を起動できるようにした。承認は投入引数で渡し、値を
  submission nonce へ束縛する。receipt 拡張は不採用 (D356 と consumer 実測)。
  保証範囲と残余は本エントリ本文と {{D:pilot-approval-argv-nonce}} に明記した。
  remaining: none
  base: fe1d3ade6bd804ea019228b069ebf6b6f7001a46d2e7cefd08fd45a162a3d064

### 新規

- {{T:submitter-bytes-binding}} **P2・新規 (段 3 敵対レンズ 所見 7)**:
  `tools/pegasus/submit_floor.sh` 自身は commit blob との bytes 照合を持たない。
  job script は動的束縛済みだが、submitter は `assume-unchanged` で隠した変更が clean-tree gate を
  通ってしまう。承認引数なしでも承認 env を生成する submitter を作れる。script 内 self-check は
  同じ編集者が消せるため trust root にならない — 外部起点の束縛が要るかを裁定する。
- {{T:pilot-approval-env-reaches-compute}} **P2・新規 (段 3 敵対レンズ 所見 1)**:
  `qsub -v` の 2 本目の env が計算ノードへ実際に届くことは本 wave では未実測である。
  NQSV が `-v` 指定外の ambient env を継承するかも未確認。最初の実投入時に、
  承認あり / なしの双方で job 側の env と driver argv を確認する。
- {{T:lane-constraint-needs-budget}} **P3・新規 (段 8 の自己改善が予算で止まった)**:
  `dev_wave_codex.py` の `--lane` が段 3 専用であることを `DW-O01` へ 1 文足そうとしたが、
  (a) model 権威行の exact 1 件検査に抵触し、(b) dev-wave の L1.5 予算を 24 bytes 超過した。
  差し戻して緑を確認済み。**予算値を上げる変更は独立審査対象**なので、
  この 1 文を入れるか、入れるなら何と差し替えるかの裁定が要る。
- {{T:unset-set-pin-too-broad}} **P3・新規 (段 6 焦点再レビュー 所見 6)**:
  新設した構造テストが `floor_campaign.sh` の `unset` 対象集合を「ちょうど 3 個」と固定しており、
  将来 `unset LD_PRELOAD` のような正当な hardening を足すと偽赤になる。
  「承認変数を含まない」へ縮めても N8 の検出力は落ちない。
