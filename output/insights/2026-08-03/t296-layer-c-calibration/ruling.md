# [T-296] Pegasus 層 C 量 (環境束縛) の取得 — 段 1 前提実測・段 3 敵対レンズ・段 4 裁定

wave = `dev-wave-t296-layer-c-calibration` / base main `1a3604b` / 2026-08-03

起票時の T-296 本文 (実体 = worklog (103)):

> Pegasus での**層 C 量 (環境束縛) の取得が未起票**。登録済み calibration は certification の 1 点のみで、
> rr80 / rr20 の較正点と between-run noise floor が無い。roadmap §5 の 3 層分類で層 A / B は転移するので
> 焼き直さないが、層 C は主張を立てる env で取得が要る。[T-277] が Pegasus 計測パスを開いた直後が最短の着手点

**結論: 「層 C 量の取得」は実測すると性質の違う 2 つに割れる。較正点は 8b H1/H2 系列に限り
設計が継承を決めており、between-run floor は [T-011] の重複で [T-088] 段階 3・4 が塞いでいる。
本 wave では取得を行わない。ただし floor の取得義務は畳まず、依存へ繋ぎ替えて保持する。**

段 3 の敵対レンズ (codex `gpt-5.6-sol` / reasoning=max / read-only) は **NO-GO** を返した。
親 brief の結論 (今は取得しない) は支持されたが、**scope の一般化と holdout の根拠づけが誤り**と
指摘された。親は全指摘を file:line で裏取りし、下記のとおり 4 件を採用して裁定を修正した。

---

## 1. 前例が 2 つの半分を分ける

正本環境 `linux-baremetal` の既存成果物が、この 2 つを歴史的に別扱いしている。

|層 C 量|既存成果物|rratio ごとに取っているか|
|---|---|---|
|較正点 (飽和点 / 下限)|`output/env/linux-baremetal/calibration/calibration_t48_skew0_rr50_rmw0.json`, `..._skew0p9_rr50_rmw0.json`|**取っていない** — 分けたのは skew (0 と 0.9) のみ、rratio はすべて 50|
|between-run noise floor|`between_run_noise_t48_skew0p9_rr5_rmw0.json`, `..._rr50_...`, `..._rr95_...`|**取っている** — rr5 / rr50 / rr95 の 3 点|

ただしこれは**慣行であって契約ではない** (§2 の裁定修正を参照)。

## 2. 較正点 — 8b H1/H2 に限った継承であり、汎用の恒久却下ではない (段 4 で修正)

### 2.1 8b H1/H2 が継承する根拠 (real)

`docs/phase3-8b-descriptor-design.md:6-10` の 2026-07-16 ユーザー承認記録:

> holdout はユーザー承認により **H1 (`rratio=80`) と H2 (`rratio=20`)** … H3 (skew 変更)・H4 (rmw 変更) は
> **校正動作点 (skew=0.9, rmw=0 で確定した records/threads) の前提が変わり**、descriptor 効果と校正の
> ずれが交絡するため次サイクル以降に回す

H1/H2 は同 :115-116 で `skew=0.9, rmw=0, 1m records, 48 threads`。**H1/H2 が H3/H4 より選ばれた理由が
「校正動作点を動かさないこと」そのもの**である。レンズもこれを real と判定した (所見 1) —
read ratio はキー選択を変えず、登録済み 1M 点は working-set 下限を満たすため、
H1/H2 に独自の records/threads 較正が物理的に必須という反論は成立しない。abort 率や分散の変化は
scale 較正ではなく**対象別 floor** が受け持つ。

### 2.2 段 1 の (P2)「恒久に却下」は refuted (レンズ所見 2 を採用)

汎用の calibration 契約は較正点を `(env, thread, **代表 workload**)` でキーすると明記している。

- `docs/decisions.md:180-186` (D13) の改訂注記: 「当初は『入力完全非依存』としていたが、
  **飽和点が skew (アクセス局所性) に依存することが実測で判明したため (D15)**、env スコープ内で
  代表 workload 署名付きファイル名に分けて持つ」
- `docs/roadmap.md:309` (D15 補強): 「**飽和/下限点は skew (局所性) に依存する**ので calibration は
  (env, thread, 代表 workload) でキーする (D13 改訂)」
- 実装のファイル署名も rratio / rmw を含む (`orchestrator/calibrator/cli.py:135-149`)

つまり「rratio では分けない」は**これまでそう必要にならなかったという慣行**であって、
契約が禁じているわけではない。したがって §2.1 は **8b H1/H2 系列に限定した例外**として記録し、
「rr80/rr20 の較正点は恒久に不要」という一般規則にはしない。

**構造上の注記:** 実行環境契約は calibration を単一 `calibration_ref{path, sha256}` で束縛し、
`env_tag` と `clocks_per_us` は照合するが workload を鍵にしない
(`orchestrator/campaign/env_attestation.py:643-692`)。将来 rratio ごとの較正点を正式に持たせるなら、
契約側の構造をどう扱うかを併せて決める必要がある。

## 3. holdout — 危険は「永久汚染」ではなく「launch certificate の clean scan 失敗」(段 4 で修正)

段 1 の初出主張「rr80/rr20 で calibration を回すと holdout を壊す」は**強すぎた**ので訂正する。
また段 1 が最初に出した件数 (rr80=2 / rr20=2 / rr50=316) は**行数であって規約の hit 数ではなかった**
(レンズ所見 3)。規約は file-level conjunction である。

- 規約どおりに数え直した結果 (freeze 宣言の `match_convention`、`excluded_paths=["output/s8b-freeze/"]`、
  git 管理下 + untracked + `external/ccbench` の 4932 ファイル):
  **H1 rr80 = 0 / H2 rr20 = 0 / positive control rr50 = 67。**
  凍結時点の記録は rr80/rr20 が conjunction=[]、rr50 が 41 files
  (`output/s8b-freeze/holdout_freeze.json`)。段 1 が数えた 2 行は除外対象の freeze 自身だった。
- 0 件要求は v1 までである。`orchestrator/campaign/s8b_ratified_freeze.py:1403-1406` は
  **v2 世代では holdout hit の 0 件要求を課さない**と明記し、理由を「post-floor は closure と完全一致」
  とする。post-floor 成果物は `measurement_closure` で束縛される。
  → **「永久に汚染される」は refuted。**
- **しかし後続測定が無関係というわけでもない (レンズ所見 4、BLOCKER)。**
  official floor の launch certificate は `clean_scan_digest`
  (`orchestrator/campaign/s8b_floor_campaign.py`) で**発行時点の clean scan** を証明する —
  docstring は「holdout hit 0 件 + 列挙 digest を返す (fail-closed)」であり、
  `_holdout_freeze._assert_search_pass(report)` を現在の repo 列挙に対して走らせる。
  **したがって closure の外で rr80/rr20 の実測値を repo に置くと、official floor の起動自体が
  fail-closed で止まる。** これが危険の正確な機序である。
- **`frozen_at_head=2e20d441` を生きた anchor として引いてはいけない。** 履歴書換え (Claude-Session
  trailer 廃止) により dangling であることが実測記録されており
  (`docs/archive/worklog-phase3-0717-0718.md:467-469`)、[T-068] の裁定 (2026-07-21) で
  fail-closed 検査から参考情報へ格下げ済み (`docs/archive/worklog-phase3-0721-0722.md:284-285`)。
  v2 は v1 を bytes 定数 (`315b1eb8…`) で束縛する。

## 4. between-run floor — [T-011] の重複であり、[T-088] 段階 3・4 が塞いでいる

取得のための資産はすべて実在する。

- 事前登録 protocol: `output/s8b-freeze/floor_protocol.json`
  (`env_tag=pegasus`, `n_sessions=8`, `reps=5`, `extime_s=5`,
  `schedule_algorithm=round-permutation/v2`, `session_cv_max=0.10`, `cell_cv_max=0.15`,
  `contract_sha256=e576e9cd…`, `master_seed=2026-07-18T17:16:12+09:00`)
- driver: `orchestrator/campaign/s8b_floor_campaign.py`
- 人間手番は**すべて済**: protocol 実凍結をユーザーが 2026-07-24 に実行 (`c8cbd17`)、
  予測封印実走と [T-011] §5-(viii) 受諾も 2026-07-24 完了 (`docs/phase3.md:116`)

塞いでいるのは official guard である。

- 実機の一次資料: `output/env/pegasus/floor/job-staging/0:873225.nqsv/floor-driver.stdout`
  = `{"status": "refused", "reason": "official mode は承認束縛方式が §8 未裁定のため現時点で拒否する (pilot のみ実行可)"}`
- 実装 = `orchestrator/campaign/s8b_floor_campaign.py:194-204` (core) と `:3435-3444` (CLI) の二重拒否
- 解禁は **[T-088]**。設計は 2026-07-25 にユーザー承認済 (D86)、Pegasus PBS floor wrapper は
  実装完了 (D87)、段階 1 は 2026-07-28 に実機閉鎖。**未着手 = 段階 3・4 (単一 admission predicate +
  CLI rc 翻訳) → 実行 revision 束縛** (`docs/phase3.md:118-124`)
- **pilot mode は代替にならない。** pilot artifact は `eligible_for_refreeze: false` と定義されており
  (`s8b_floor_campaign.py:43`、強制は `:2330-2333`)、floor/budget を充填する再凍結に使えない
- **優先度はユーザーが意図的に下げている。** 2026-07-27 改訂 (2)「8b selector 側の残作業 … の
  優先度を下げる。**床値実測は他候補にも要る測定土台なので廃止ではなく順序の後退**」(`docs/phase3.md`)

### 4.1 T-296 の floor 半分は [T-011] とほぼ同一の既起票である

`docs/archive/worklog-phase3-0727-20-25.md:105-106`:

> [T-011] **裁定済み = 前提の鎖を短縮せず維持**。科学レーン floor 実測。
> 残 gate = [T-096] → [T-088] → 段階 3・4 → 実行 revision 束縛。変わらず

本 wave が §4 で独立に辿り着いた gate 連鎖と一致する。**T-296 の between-run floor 半分は
[T-011] の重複起票**である。連鎖の各項は現在も active — [T-096] (driver 側 timeout を予約式と
整合させる、裁定済み)、[T-088] 段階 3・4、実行 revision 束縛。ただし [T-088] は (36) の 3 項裁定により
**段階 3 の設計は着手可**と記録されている
(`docs/archive/worklog-phase3-0728-33-37.md:487-490`)。同記録によれば床値実測後まで塞がった
条件待ちが 8 件 ([T-085]/[T-112]/[T-114]/[T-011]/[T-122]/[T-103]/[T-089]/[T-090]) ぶら下がる。

### 4.2 floor の取得義務は畳まない (レンズ所見 6、BLOCKER を採用)

`docs/phase3-8c-preregistration.md:93-124` の実走前提 12 項のうち**第 7 項が
「対象別 between-run floor が H1 / H2 について再実測され §5 に記入されている」**であり、
同書 §5 の表にも「対象別 between-run floor (H1 / H2)」が未記入欄として残っている。
8b 正本も対象別 floor を明示義務としている (`docs/phase3-8b-descriptor-design.md:199-208`)。
**したがって T-296 は「不要になった」のではなく「依存の下流へ移った」項目である。**
項自体を削除・完了扱いにしてはならない。

## 5. 派生所見 — between-run floor の既定が env 盲目 (既起票 [T-333] に統合)

`orchestrator/campaign/screening_driver.py:31-32` の `_default_calibration_dir` は
`output/env/linux-baremetal/calibration` を返し、`load_between_run_floor` の既定になる。
Pegasus 側に `between_run_noise_*.json` は 0 件。sweep driver 群
(`backoff_sweep.py:97`, `s6_sort_sweep.py:260`, `s8a_trigger_sweep.py:307` が実 caller) が
floor dir を渡さなければ、**linux-baremetal の floor が compare の丸め閾値として黙って適用される**。
D59 (2) の env-tag 束縛に対して fail-open である。

**新規起票はしない (レンズ所見 8 を採用)。** 同じ欠陥は **[T-333]**「critic digest と screening に
env 次元が無い。`GenomeLI` / `WorkloadDigest` は env を持たず **loader も `env_tag` を読まない**。
… 実 consumer に環境が伝わっていない」(`docs/archive/worklog-phase3-0802-117-121.md:300`) が既に
起票済みだった。親は記号名 (`load_between_run_floor` / `floor-dir`) で台帳を検索したため、
概念で書かれた既起票を取り逃がした。既存 3 caller の COMPUTE 閉鎖は [T-331] (裁定済み択 (a)) が持つ。

発火する計測 ID は現存しない。レンズが `output/campaigns/` と `output/exploration/` を含めた
静的検索でも Pegasus 発火 0 を確認した (親が `output/env/pegasus/` だけを見た検査は、campaign 出力が
`output/campaigns/` に置かれる D13 の分割に照らして不十分だった)。

**成果物影響 (DW-G05):** 放置して Pegasus で sweep を回すと、compare の丸め閾値が別 env の noise で
決まり、selected/tie の判定がその閾値で変わる。

## 6. 8b 非依存の一般用途 floor は「実在するが Pegasus 未対応」

`orchestrator/campaign/between_run_floor.py:45-62` は `p2_2.py:40-47` から
`ENV_TAG="linux-baremetal"` / `CLK=1800` / `NUMA=["numactl","--interleave=all"]` を定数で継承し、
動作点も rr5/rr50/rr95 固定、書き出しも `env_scope_dir(ENV_TAG)/calibration` 固定 (:112-120)。
Pegasus は TSC 2100 (登録 calibration の `clocks_per_us`)、単一 NUMA
(`attestation_profile.numa` len=1) なので、時間基準もトポロジも合わない。

---

## 7. 段 4 裁定 (real / refuted と採否)

|# (レンズ所見)|裁定|扱い|
|---|---|---|
|1 — H1/H2 の 1M/48 継承は 8b 固有設計として成立|**real**|採用。§2.1 として記録|
|2 — 「rr80/rr20 較正を恒久却下」への一般化は契約にない|**(P2) を refuted**|採用。§2.2 で 8b 限定の例外へ縮小|
|3 — 親の件数 2/2/316 は規約違反の行数|**refuted (件数)**|採用。§3 を 0/0/67 に訂正済み|
|4 — 永久汚染は誤りだが未申告の先行測定は launch を壊す|**BLOCKER・real**|採用。§3 の機序を `clean_scan_digest` に置換。`frozen_at_head` の dangling も記録|
|5 — 直近 blocker は [T-088] 段階 3・4|**real**|採用 (親裁定と一致)|
|6 — floor 義務まで畳むなら refuted|**BLOCKER・real**|採用。§4.2 を新設し、項を残す方針を明記|
|7 — P4 は「Pegasus を正式 claim env にするか」だけを返すべき|**(P4) を部分 refuted**|採用。§8 (4) で問いを縮小|
|8 — F-4 は実欠陥だが新規起票は [T-333] と重複|**新規起票を refuted**|採用。§5 で [T-333] へ統合、新規 T を起こさない|
|9 — 引用値は行番号 1 件を除き一致|**NIT**|採用。`screening_driver.py` を :31-32 へ訂正|

## 8. 裁定の帰結 (ユーザー確認を求める項を明記)

- **(1) 本 wave は取得を実装しない (親裁定・実行済み)。** 段 4 で「実装しない」と裁定し `4→7→8→9`。
  実装差分がないため変異 matrix と受入全走は射程外。
- **(2) T-296 を依存へ繋ぎ替え、項は残す (親裁定・実行済み)。** floor の取得義務は 8c 事前登録 §6 項 7 と
  8b 正本が課しており、畳まない (§4.2)。
- **(3) 較正点の継承は 8b H1/H2 系列限定の記録とする (親裁定・実行済み)。**
  段 1 の「恒久却下」案は取り下げた (§2.2)。汎用契約は `(env, thread, 代表 workload)` キーであり、
  将来 rratio 別較正が要る系列が出たら契約 (§2.2 の `calibration_ref` 構造) ごと設計し直す。
- **(4) ユーザー裁定へ返すのは 1 問だけに縮小する — 「Pegasus を正式計測の claim env へ昇格させるか」。**
  D59 (1) は正本 env-tag を `linux-baremetal` に据え置いており、昇格には roadmap §5 の 4 条件
  (専用 env-tag / その env-tag での calibration・noise floor 取り直し / 単独性・静定確認 /
  toolchain・pin の成果物追跡) が要る。**「floor を取るか」自体は既裁定 (廃止せず順序後退) なので
  択一に戻さない。**
- **(5) §5 の穴は新規起票せず [T-333] へ統合する (親裁定・実行済み)。**

## 9. 本 wave の手続き上の逸脱 (正直な記録)

- **段 2 (プラン起草) を行わなかった。** 実装面が無く、成果物が docs 本文と裁定だけであるため。
  代わりに段 3 の敵対レンズ 1 本を立て、親 brief の事実主張そのものを攻撃させた。既起票タスクの
  前提を覆す wave であり、`DW-C00` の「独立の敵対検証子を省かない」に該当すると判断した。
  結果として NO-GO が返り、scope の一般化 2 件と重複起票 1 件を止めた。
- 段 3 の逐語 = 同ディレクトリの `lens-a.md`、親 brief = `brief.md`。
- レンズは read-only の静的検査のみで pytest を実走していない。
- 親の受入 = `tools/check_docs.py` 違反なし + 影響テスト (`test_check_docs.py` / `test_spool_fold.py`)
  を Pegasus gen_S 計算ノード request `881854` で **350 passed**、provenance full-history 監査を
  request `881853` で **813 件・違反なし**。実装差分がないため変異 matrix と受入全走は射程外。
- **段 8 の改善候補 1 件は不採用で閉じた。** 候補 = 背景 job から codex 子を投げるとき `&` と
  harness の `run_in_background` を併用すると子が親 shell 終了で落ち `.done` が出ない。
  実際に 1 回目の投入で起きた。ただし `DW-O01` の既存規則 (完了は `.done` と exit code だけで判定)
  が効いて truncated log を完了と扱わずに済んでおり、**壊れたのは投入方法であって規律ではない**。
  単発事故は局所修復が既定 (`DW-G03`)、`docs/dev-wave/operations.md` の余裕も 44 bytes
  (ディレクトリ合計 2 bytes) しかなく予算上限は上げない方針なので reference を変更しない。
- **投入前の判断ミスを 1 件記録する。** `qstat -Q` の「gen_S 177 件待ち」を見て受入を
  `check_docs.py` だけに絞ると決めたが、実際の待ちは 13 秒だった。キュー長を待ち時間の代理に
  使った推定が外れたので、絞る前に 1 本投げて実測する。
