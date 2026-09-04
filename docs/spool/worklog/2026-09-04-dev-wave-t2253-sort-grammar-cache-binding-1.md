---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2253-sort-grammar-cache-binding
seq: 1
title: [T-2253] sort 軸の campaign 由来の契約 ID を build cache の鍵へ局所束縛した (コード + テスト + insight、branch worktree-dev-wave-t2253-sort-grammar-cache-binding、変異 17/17 KILLED + 等価 1 SURVIVED)
---

## 本文

- D1548 の裁定どおり、段 5 sort loop の唯一の `run_campaign` 呼出しへ単一 producer
  `_require_sort_oracle_contract(cfg)` が返す `ORACLE_CONTRACT_ID` を keyword-only 引数で渡し、
  `loop` → `pipeline` → `source_digest.resolve_evidence` → 非 stock `src_token` のドメイン分離 hash
  (`sort-src-token/v1`) → `buildcache` の legacy / v2 両 API と四出口の再照合まで届かせた。
  既定 `None` で引数を渡さない campaign の bytes は不変。一次資料 = `output/insights/2026-09-04_t2253-sort-grammar-cache-binding/`。
- **段 4 で親の provisional 裁定 1 件を撤回した。** 親は `run_campaign` 入口に campaign 宣言・引数・実行中 module の
  三者 exact gate (backoff の `loop.py` gate の写し) を置く側だったが、段 3 の lens A が「単一 producer が identity
  束縛より前に照合する限り、gate が無いことで変わる in-scope 成果物は無い」ことを実コードで示し、さらに `loop.py` への
  `sort_swo_oracle` import が import 時の失敗面 (`inspect.getsource` の fail-closed) を全 campaign へ広げると指摘した。
  command 引数の「仮想リスク向け gate は scope 外」に従い gate と import を実装しなかった ({{D:sort-contract-binding-without-entry-gate}})。
- **brief の誤りを段 3 が 6 件訂正した。** 最重要は 2 件: (1) 不変条件に挙げた既存 lock `...-3be89e0d` は oracle 導入前の
  歴史成果物で、現行 ID は `p3-s5-sort-loop-s5-sort-autonomous-6f6a8cf1` (lens B)。(2) 「変わるのは src_token と cache key だけ」は
  不足で、`verification_variant`・WAL の variant id・`BUILD_START` の `src_token`・build admission receipt の digest・cache path も変わる
  (受理集合と campaign identity は不変)。また lens A は、束縛する `ORACLE_CONTRACT_ID` の checker hash が列挙 hash であって
  挙動の閉包でない (`sort_swo_oracle.py` 自身が明記) ことを real と判定した。束縛値は identity・WAL が既に使う同じ値であり、
  閉包の改善は契約設計の変更で campaign identity を動かすため本 wave では実装せず裁定パッケージ候補へ送った ({{T:sort-oracle-contract-id-closure}})。
- **段 6 レビューの must-fix は 2 件で、両方 fix した。** lens A: 実装子が `p3_s4_loop_sort.py` に module-level の
  `sort_swo_oracle` import を足していた (裁定は関数内 import を明示していなかった)。B-4 launcher 等が driver を先に import するため
  失敗面が広がる。関数内 import へ戻した。lens B: T12 が借用 fixture `test_buildcache_v2._fake_build_environment` の
  `resolve_evidence` 代役 (固定 keyword の lambda) で `TypeError` になり目的箇所へ到達しなかった。T13 と同じ代役を足した。
  lens B の残る所見「probe spec が全件 SURVIVED 期待」は DW-M07 の probe 規約で refuted。
- **変異は事前登録 14 件に段 6 後 4 件 (M15〜M18) を足して 18 件で走らせ、本走は 17/17 KILLED (期待 node と完全一致) +
  等価変異 1 SURVIVED、harness rc=0。** M15 は再照合の resolver 転送、M16〜M18 は lens B が「M8 / M11 は過剰決定」と
  予測したことを受けた単一理由の再照準 (NUL 拒否、v2 fresh 出口、legacy hit 出口)。単一理由と確認できたのは 10 件
  (M1, M2, M9, M10, M12, M13, M15〜M18)。M8 (binder が raw を返す) と M11 (build_v2 wrapper の欠落) は予測どおり 3 node の
  過剰決定で、単独変異の証拠から外した。
- **`loop.py` の変異は contract-loader drift の冗長 gate に完全に吸収された。** M3 / M4 は 58 node が赤になるが固有 node は空で、
  owner のはずの T5 も mask の中にある。`loop.py` は HEAD blob 束縛 file なので、どんな 1 行変更も `run_campaign` 内の drift
  検査で先に止まり、T5 の単独帰属は変異では示せない (静的論証のみ)。`pipeline.py` の M5〜M7 は同じ mask 58 node に加えて
  固有の owner node (T6 の legacy / v2) が出た。等価変異 M14 は SURVIVED で harness の正例。mask の node 一覧は insight の
  `mutation-drift-mask.json`、分類は `mutation-ledger.md`。
- **実装子は pytest を 1 件も実走できなかった** (Pegasus dispatch preflight rc=16)。「実装済み・未実走」と正直に申告した。
  テストの実測はすべて親が行った: commit 前の焦点走 (sort test 単独) 11 failed のうち 9 件は未 commit の `loop.py` による
  contract-loader drift、1 件が T12 (上記)。commit 後の焦点走 7 file = 1213 passed / 1 failed (T12)。fix 後の焦点走 11 file
  (collection pin、duration ledger、B-4 launcher、trigger を追加) = 1472 passed / 3 skipped / 0 failed。
- **セッション異常 2 件。** (1) 親が段 1〜5 の時刻を推定で handoff に書き、file mtime と約 50 分ずれていた (記録は mtime 基準に
  訂正)。(2) fix 後の単独走で runner が login node の bounded local を選び MemoryMax に当たったうえ、走行中に親がレビュー逐語を
  worktree の insight へ写したため tree の状態が変わり、自動 fallback せず rc=16 で止まった (F106 型の再発、実害は再走 1 回)。
- **main の取り込み。** 起動時に 10 commit、段 4 前に 4 commit、いずれも docs のみで `--ff-only`。段 6 中に peer から
  着地通知 (`e1850cf3`) が届いたが、変異走行中は HEAD を動かせないので本走後に `--no-ff` で取り込んだ (その時点で 18 commit、
  所有 path と受入 runner への incoming 変更は無し)。
- **受入全走は本記録 commit を含む最終 tip に対して 1 回だけ投入し、land は `child-green` の receipt でのみ進める。**
  結果は receipt (job dir の `acceptance-receipt-1.json`) と land の出力を正本とし、本 entry へ後から書き足さない
  (書けば tip が動いて receipt が無効になる)。
- **段 8 (自己改善)**: 候補 1 件 — 「HEAD blob 束縛 file (`loop.py` 等) への変異は contract-loader drift の mask が owner ごと
  吸収するので、事前登録の段で owner 証拠に数えない」。`docs/dev-wave/mutation.md` の DW-M03 へ 1 文を仮追記して実測したところ
  L1.5 予算 9696 bytes に対し 9804 bytes (108 bytes 超過) で入らず、復元して memory へ寄せた。予算のために他の義務は削らない。
- **agent 工数**: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1)。焦点走 4 回 (うち 1 回 rc=16)、
  変異走 probe 1 + 本走 1 (各 20 走、dispatch)。

## 次の一手差分

### 完了

- [T-2253] sort 軸の cache 束縛を D1548 どおり局所適用した。単一 producer + keyword-only 引数 + `sort-src-token/v1` の
  ドメイン分離で `src_token` と legacy / v2 cache identity が契約 ID に束縛される。入口 gate と `resolve()` / `src_token()` は
  段 4 裁定で scope 外。変異 17/17 KILLED + 等価 1 SURVIVED。
  remaining: none
  base: f1d0ff642ee130ad759ad14af265a59723e94d78ebfdcbf87e83512dc09bf027

### 新規

- {{T:sort-oracle-contract-id-closure}} **P3・ユーザー裁定待ち**: `ORACLE_CONTRACT_ID` の権威境界。checker hash は列挙 hash で
  挙動の閉包ではないため、列挙外の判定 (top-level `check_materialized_sort_swo`、timeout 定数) が変わっても ID が変わらない。
  択一は (a) 列挙 hash を維持し、列挙外変更では `CONTRACT_VERSION` の手動 bump を運用正本にする、(b) top-level 判定と
  semantic constants まで manifest へ含め、現行 ID と campaign ID の移行を受け入れる。compiler path/version を realized contract に
  含めるかも同じ裁定で決める。成果物影響 = (a) を選ぶまで「契約が変わっても同じ ID で cache hit する」窓が仕様上残る。
  一次資料 = `output/insights/2026-09-04_t2253-sort-grammar-cache-binding/verbatim/s3-lens-a.md`。
- {{T:s1-direct-comparison-contract-binding}} **P2・新規**: `s1_direct_comparison.py` は config に `sort_swo_oracle` 契約 ID を持つが
  `resolve()` / `evaluate()` へ渡さないため、T-2253 と同種の identity / cache 分断が残る (段 3 lens B が実コードで確認)。
  D1548 の局所適用は段 5 sort loop に限ったので、s1 系 producer への適用は独立の裁定と task にする。
  成果物影響 = 契約改版時に新 campaign の event / report が旧契約と同じ variant / cache binary を参照しうる。
- {{T:sort-build-start-plaintext-contract}} **P3・新規**: `BUILD_START` payload に平文の契約 ID を再掲しないため、record 単体からは
  契約 ID を復元・照合できず campaign.lock との併読が要る (段 3 両レンズ)。per-attempt 監査が要るなら別裁定。
  成果物影響 = 監査性のみ、certified 値・受理集合・参照は変わらない。
