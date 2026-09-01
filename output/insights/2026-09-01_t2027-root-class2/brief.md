# 段 1 brief — [T-2027] 消える根の第 2 クラスの根相対化 / [T-2043] 赤の解消確認

- wave: `dev-wave-t2027-root-class2`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2`
- branch: `worktree-dev-wave-t2027-root-class2`
- 基準 (着手直前の local main): `2bf9cf387643bf7ac087c31f5c38cfcc5539de68`

## scope

D1322 (ユーザー裁定) の実装。compiler input manifest の根相対化を、着地済みの根クラス 1
(build cache の `.staging-<PID>-<nonce>/_deps/masstree-src/…`、31 件) に加えて
**根クラス 2 (job 専用作業領域 `/scr/0_<jobid>.nqsv/{gflags,glog}-install/include/…`、7 件)**
へ広げる。あわせて [T-2043]「床値 job の再投入で第 2 クラスが閉じるか」を同じ wave で判定する。

編集面は `orchestrator/campaign/{buildcache,s8b_compiler_input,s8b_binary_admission}.py` と
その test。`orchestrator/campaign/s8b_floor_campaign.py` の呼び手 2 箇所 (4221 / 4389 行) は
配線上必要になりうるので候補に含める (scope 判断は段 4)。

## 確定済みユーザー裁定

- **D1322** — 根相対化は実測した 2 クラスへ広げる。ただし束ねる前に D1192 の統合条件
  (同一 cache entry・同一拒否述語・同一 descriptor・同一是正 3 択) を実測で示すこと。
- **D1192** — manifest は根の分類と根相対 path を持ち、cache hit と receipt 発行の時点で
  現在の canonical base へ束縛し直す。run 間の cache 再利用は失わない。
- **D1338** — manifest schema 文字列を descriptor-bound cache の preimage へ pin し、
  旧 v1 completion は移行しない。遷移の 1 回だけ再 build になる。
- ユーザー指示 — 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。
  Codex `role=author` (D95) が実装面を書く。規律 2 を緩めない。

## 親が実測した事実 (brief 前の前提検査)

一次資料は
`/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2027-root-class2/probe-d1192-conditions.out`。
対象は落ちた job `952631` が残した実 completion
(`…/contracts/e576e9cd…/87aa2e6a…/completion.json`、`compiler_input_manifest` 588 件)。

**(M1) D1192 の統合条件は 4 つとも満たす。**

| 条件 | 実測 |
|---|---|
| 同一 cache entry | **満たす。** 両クラスは同一 completion (`contract=e576e9cd…`、`entry=87aa2e6a…`) の同一 manifest の入力である |
| 同一拒否述語 | **満たす。** v1 では両クラスとも `external compiler input is unavailable`。根タグを `filesystem` に揃えた v2 形でも両クラスとも `compiler input is unavailable or cannot be hashed` |
| 同一 descriptor | **満たす。** `target=ycsb_silo.exe`、`input_policy=snapshot-and-external-hashes/v1`、`contract_sha256`、`full_build_digest` がいずれも同一 |
| 同一是正 3 択 | **満たす。** D1192 が列挙した 3 択 (根相対化 / base 絶対 path を cache identity へ / 消えた entry を cache miss へ降格) は、どちらのクラスにも同じ形で適用できる。拒否述語が根タグだけで決まり、クラスでは決まらないことを上表の 2 行目が示す |

**(M2) 内訳は一次資料と一致した。** `/usr/include` 415、`/usr/lib` 96、snapshot 相対 39、
クラス 1 が 31、クラス 2 が 7、合計 588。現存しないのは 38 件で、その全部がクラス 1 と 2 である。

**(M3) 承認済み裁定の前提を覆しうる新事実 — クラス 2 の再束縛には現状 発火条件が無い。**
一次資料は
`/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2027-root-class2/probe_identity_jobid.py` の出力。

- 実 completion の cache identity preimage は
  `dependency_prefix: ["/scr/0_952631.nqsv/gflags-install", "/scr/0_952631.nqsv/glog-install"]`
  を持つ。**クラス 2 の根そのものが cache identity に入っている。**
- entry directory 名 `87aa2e6a…` = preimage の SHA-256 であることを再計算で確認した
  (`full_build_digest` とも一致)。
- jobid だけを `0_999999.nqsv` へ差し替えて identity を再計算すると
  `a479f596…` になり、**同一 entry は選ばれない。**
- `validate_compiler_input_manifest` の呼び手は 3 箇所しかない — cache hit 検証
  (`buildcache.py:1694`)、fresh build 検証 (`buildcache.py:2637`)、receipt 発行
  (`s8b_binary_admission.py:231`)。いずれも build を行った job の中で走る。
  `validate_portable_binary_record` は manifest の bytes を再 hash しない。
- したがって **クラス 2 の記録 path が再解決される場面では、その path はまだ生きている。**
  job 952631 が落ちたのはクラス 1 (build 自身が `_discard_build_dir` で staging を捨ててから
  受領書発行へ進む) が理由であって、クラス 2 ではない。
- 一次資料 (2026-08-29 insight §4) の「クラス 2 の 7 件は現存しない」は、**job 終了後の
  現時点で**測った値である。job の中で消えるという測定ではない。

**(M4) 追記 (段 2 実行中に親が測った) — cache identity は jobid をもう 3 箇所で持っている。**
一次資料は
`/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2027-root-class2/probe-cross-job.out` と
`/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2027-root-class2/probe-admission.out`。
母集合は `/work/1/SFC/tanab/dev-wave-jobs/` 配下に実在する build cache completion 20 件
(列挙は `completions.txt`) で、うち同一 genome
`silo|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`
を持つ 5 件が 5 つの別 job (`940170` / `944884` / `945229` / `952615` / `952631`) に対応する。

- `preimage.admission.source.source_root` = `/scr/0_<jobid>.nqsv/izanagi_wt_<乱数>/wt`
  で、**5 job すべてで異なる**。`review_receipt.source.source_root` も同じ。
- `preimage.admission.receipt_sha256` と `review_receipt.receipt_sha256` も 5 通りで、
  上の source_root を含む値を hash している。
- 一方、内容由来の field (`src_token`、`source_bytes_sha256`、`tracked_diff_sha256`) は
  job をまたいで**一致する** (940170/944884/945229 が同値、952615/952631 が同値)。
  すなわち job ごとに変わっているのは path であって内容ではない。

**帰結:** `dependency_prefix` から jobid を外しても、`admission` 側が job 専用 checkout の
絶対 path を 3 箇所で identity に入れているので、cross-job の cache hit は依然として起きない。
つまり (M3) は 2 つの独立した機構によって成り立っており、**形 B (identity から
`dependency_prefix` の jobid を外す) だけでは根クラス 2 の再束縛は発火しない。**
発火させるには admission 側の identity まで変える必要があり、それは
D1322 が名指ししておらず、正しさ防壁 (受領書の provenance) に触れる。

## (P1) 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1-a) クラス 2 を根相対化しても、identity が jobid を持ち続ける限り再束縛は発火しない。**
  (M4) を測った後の親の provisional 裁定は次のとおり。**D1322 が裁定した根相対化は実装する。
  ただし「これで床値の主経路が緑になる」とも「再束縛が発火する」とも主張しない。**
  発火させるには admission identity まで変える必要があり、それは D1322 の射程外かつ
  正しさ防壁に触れるので、本 wave では実装せず裁定パッケージでユーザーへ返す。
  段 3 はこの裁定を攻撃対象とする。発火路が別にあるなら (M3)/(M4) が誤りなので、
  そちらを優先して探すこと。
- **(P1-b) 根タグ集合を増やすとき schema を v3 へ上げるか。** D1338 は schema を identity へ
  pin しており、identity から jobid を外すと旧 v2 entry が cross-job で選ばれうる。
  親の provisional 裁定は「(P1-a) を採るなら v3 へ上げる、採らないなら据え置き」。
- **(P1-c) 新しい根の「現在の canonical base」の出所。** 親の provisional 裁定は
  `dependency_prefix` の要素列 (実在が M3 で実測済み)。CMakeCache の `CMAKE_PREFIX_PATH` から
  読む案もあるが、floor driver は `-DCMAKE_PREFIX_PATH` を渡さず環境変数で渡す
  (`tools/pegasus/README.md:237-238`、`floor_campaign.sh:1158`) ので CMakeCache に残らない。
- **(P1-d) 2 要素の根 (gflags と glog) を 1 つの根タグで扱うか、要素ごとに分けるか。**
  親の provisional 裁定は「順序つき要素列の index ではなく、要素の basename でも位置でもなく、
  prefix 要素の集合として照合する」— 段 2 で file:line 粒度に落とす。

## 不変条件 (緩めない)

- **規律 2** — 受理集合を広げる是正をしない。根タグを増やすことは受理形の追加なので
  `DW-O13` の gate 新設扱いとし、正例・負例を対で登録する。
- 既存 v1 manifest の bytes と受理面は変えない (D1338)。v1 は read-only 互換のまま。
- 既存 v2 の 3 根 (`snapshot` / `fetchcontent-masstree` / `filesystem`) の受理・拒否挙動を
  変えない。`filesystem` は記録時の絶対位置で bytes を検査する現行の限界を保つ。
- 既存テストの期待値を変えない。赤なら実装側が誤り。
- 凍結成果物の bytes 変更なし — 編集面 3 file に whole-file SHA-256 pin も generator source
  hash pin も無いことを `git grep` で確認済み (`FROZEN_MANIFEST` は該当 0 件)。
- `orchestrator/tests/test_s8b_floor_campaign.py` は稼働中 wave
  `dev-wave-t2074-a1-estimand-realign` (main+7、未 commit なし) が +89/-10 で所有しているので
  **本 wave は編集しない** (`DW-O26`)。

## 成果物の形

1. 実装 — 根クラス 2 を根相対で記録し、使用時に現在の canonical base へ束縛し直す。
2. テスト — 正例 (再束縛が効いて緑) と負例 (別根の bytes 差・根タグの偽装・根の不在) を対で。
3. insight — `output/insights/2026-09-01_t2027-root-class2/` に統合条件の実測、裁定、
   レビュー逐語、変異の証拠。
4. [T-2043] の判定 — 床値 job の再投入が必要かどうかを含め、段 4 で決める
   (M3 が正しければ再投入なしでも「第 2 クラスは赤を出さない」と言える。ただし
   「閉じた」と書けるかは別問題なので裁定する)。
5. spool fragment (worklog / decisions / failures) — canonical 台帳は段 9 の land が畳む。

## 分割方針

producer (`buildcache`) と consumer (`s8b_compiler_input` / `s8b_binary_admission`) は
1 つの根タグ契約を跨ぐので **段 5 の実装子は 1 本**にする (並列 fix が producer/consumer 契約を
壊す型を避ける)。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ A = (M3) の発火条件と親の実測への攻撃、
レンズ B = 受理集合と正しさ境界)、段 6 敵対レビュー 2 本 + fix + 焦点再レビュー。
