# [T-1328] perf 候補全滅で較正認証を止めず、canonical probe の結果だけで分岐する

wave = `dev-wave-t1328-certify-perf-optional`、branch = `worktree-dev-wave-t1328-certify-perf-optional`。
着手時の local main = `9d52ef145`。実装 commit = `b8e2e06dd`、fixture 修正 = `5d4cc3ff1`、
main 取り込み = `9253f79bf`。

台帳正本 = `docs/archive/worklog-phase3-0817-637.md:615` の [T-1328] 本文
(P2・新規、段 6 レビュー B が real・scope 外と判定した項)。

## 何が壊れていたか

`tools/pegasus/certify_calibration.sh` は policy の perf 候補が 1 本も version smoke /
event smoke を通らないとき、`write_failure 2 perf` + `exit 2` で認証 attempt を
**測定に入る前に**捨てていた。D352 は「性能測定 (床値・**calibration**・oracle を含む) は
perf の可用性を前提にしない。preflight は可用性を検出して環境タグへ記録し、**実行を止めるためには
使わない**」と定めており、この分岐は正面から反する。

## 依頼の前提は現況と食い違った。根拠を差し替えて続行した

依頼文は「この計算ノードに perf は無く、perf 不在が較正認証を止めるのは実害である」を起点にしていた。
**親が一次資料を実測すると、計算ノードについてこれは現在成り立たない。**

- `output/env/pegasus/calibration/job-staging/` の 19 attempt のうち、**perf 段で失敗したものは 0 件**。
  失敗 10 件の段は allocation / shell / calibrate / gflags / source_identity。
- 直近 2026-09-15 の `0:998860` / `0:998863` / `0:998864` はいずれも
  `/usr/lib/linux-tools-5.15.0-135/perf` (perf version 5.15.178) を選び、LLC 実カウンタを得て
  `calibrate_rc = 0`。
- login node には policy 候補 2 本とも不在だが、本 script は `PBS_JOBID` 必須で login では走らない。

**この一般化の射程は限定する。** 母集合は保存済み attempt、観測 regime は各実行時のノード・kernel・
PATH・権限である。言えるのは「**観測範囲では perf 段の失敗を確認できない**」までで、
別ノード・kernel 更新・linux-tools の撤去・counter 権限変更が反例条件になる。

**続行の根拠は実害ではなく D352 違反の是正へ差し替えた。** 入力を「全 policy 候補不在 +
literal perf 不在 + 他の準備条件は正常」とすれば現行コードは測定前に停止する。これは裁定に反する。
発火頻度が未確定でも是正根拠は消えない (段 3 の 2 レンズとも同意)。
発火条件が仮想でないことの根拠は 2 つある — D352 自身の根拠実測が「2026-08-12 に計算ノード 8/8 で
現行 kernel 用 linux-tools 不在」、および親の本日の実測で login node の候補 2 本が実行不可。

## 何を変えたか

D494 が既に定めた形を適用した。先例実装は `tools/pegasus/t126_qualification.sh:625-670`。

1. 候補解決 (version smoke と event smoke) は従来どおり行い、**通った候補があるときだけ**
   `perf-selection.json` と `$TMPDIR/bin/perf` の symlink を作る。
2. その後で確定した `CALIBRATE_PATH` の下で `probe_perf_availability` を **1 度だけ**呼び、
   receipt を `perf-preflight.json` へ保存し、`use_perf_from_receipt` の結果**だけ**で分岐する。
   「候補が全滅したか」は selection の生成にしか使わない。判定入口は 1 本のまま。
3. `probe_error` は `unavailable` へ変換せず、従来どおり rc=2 で停止する。
4. unavailable のときだけ `calibrate_argv` へ `--perf-preflight-json` を足す。
5. `use_perf` を CLI から `sweep.calibrate` の closure を経て `runner.measure_point` へ伝播させた。
   `runner` の counter 必須検査だけを `if use_perf:` の内側へ移し、
   **throughput 検査・maxrss 検査・rep 失敗処理は 1 行も動かしていない。**
6. no-perf では `saturation=None` を返して noise へ進まない。sweep の測定点は保持する。

`analyze.py`、`report.py`、`schema_v2.py`、`perf_preflight.py`、`submit_certify.sh`、
`t126_qualification.sh`、`t141_region_profile.sh` は 1 バイトも変更していない。

## perf が本当に要る判定は通していない

レコード数の飽和選択は LLC miss 率を要する。`analyze.py:48-57` は `miss_rate` 欠損点を候補から
外し、全欠損なら「飽和判定不能」を返す。下限基準 (L3 倍数) も `usable` にしか効かない。

**no-perf 成果物が `accepted` になれないことは、新しい gate ではなく既存の多層の判定が保証する。**
`sweep.py:272` (saturation を None にして noise 前に戻る) → `report.py:106/115/121`
(counter・selection・noise の欠損から拒否理由を作る) → `cli.py:1039/1055` (rejected を決め、
登録前に rc=1) → `schema_v2.py:529/531` (accepted は saturation 非 null と非空 sweep/noise_floor を
要求)。**段 6 の焦点再レビューが「schema が唯一の保証」という親の記述を訂正させた。**
schema は追加の防壁であり、通常経路の rejected 判定は report / CLI にも存在する。

## 受理集合の変化 — 「ちょうど」とは書けない

親は当初 commit message に「増分は候補全滅 + literal perf が canonical probe を通るちょうど、
減分は従来 smoke は通るが canonical probe だけ失敗する候補ちょうど」と書いた。
**段 6 の焦点再レビューがこれを不正確と判定し、親が受け入れた。正しくは次のとおり。**

- **到達可能性と最終受理は別である。** 「候補全滅 + canonical available」は perf 有り経路へ
  *到達できる*条件であって、`accepted` の十分条件ではない。品質理由が残れば
  `cli.py:1036-1057` で rejected になる。増分を言うには「その後の既存品質・登録条件も満たす」
  という限定が要る。
- 減分も「旧版で実際に accepted になる入力との交差」で書くべきで、旧 smoke 成功だけでは
  旧版 accepted を保証しない。
- **第三の縮小経路がコード上に存在する。** policy の候補配列に同一文字列を重複させると、
  shell の読込みと選択は通るが、全候補の evidence を作った後に
  `perf_preflight.py:237` の重複検査が失敗し、wrapper は rc=2 で argv 未生成になる。
  **現行 policy の 2 候補は重複していない** (`tools/pegasus/policy.json`) ので現行設定での
  発火を主張するものではない。
- 追加 probe と candidate evidence のぶん所要が増えるため、**予約期限近傍の完走可能性まで
  不変とは言えない。**

**この縮小は隠さない。** D494 の順序 (候補解決を済ませた PATH の下で probe) を守る以上、
「旧 smoke は通るが canonical probe だけ失敗する候補」で従来 accepted になりえた走が
rejected になる。第二の probe や fallback を足して隠す是正は採らない。

## login node の緑が隠していた欠陥 — 計算ノードで初めて出た

**変異 harness の baseline を Pegasus 計算ノードへ dispatch して初めて 2 件の赤が出た。**

```text
FAILED orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_perf_preflight_argv[probe_error]
FAILED orchestrator/tests/test_pegasus_tools.py::test_perf_stage_all_candidates_failed_uses_canonical_receipt[probe_error]
```

どちらも `assert 0 == 2` = production 断片が `exit 2` へ入らなかった = receipt が `probe_error` に
ならなかった。原因は fixture 側にある。偽の計測コマンドが `os.kill(os.getpid(), signal.SIGTERM)` で
自分を殺し、`perf_preflight` の `rc < 0` → `probe-signal` → `probe_error` を作ることに依存していたが、
**SIGTERM の無視設定は exec を越えて継承される。** その設定を持つ環境では kill が何も起こさず、
fixture は次の行へ進んで正常な CSV を書き rc=0 で終わる。receipt は
`status=available / reason=available / rc=0` になる。

**このとき test は緑のままだが、意図した `probe_error` の経路を 1 度も検査していない。**
login node の実行だけで閉じていれば、効いていない検査を効いていると数えたまま land していた。

fix は login node でこれを**再現した** — 親 Python に `SIGTERM=SIG_IGN` を設定すると修正前の
2 件が同じ本文で赤になり、receipt も `status=available` だった。修正後は同じ条件で 2 件とも緑。
自己終了を SIGKILL へ替えて閉じた (SIGKILL は無視・捕捉・ブロックのいずれもできない)。
production コードと他 parameter の期待値は変更していない。

## 変異 — 10 件事前登録、probe で観測 node を集めてから本走

probe (全件 SURVIVED 登録) で観測 node を集め、それを完全集合として焼き直して本走した。

**baseline PASSED・10/10 KILLED・期待 node 完全一致 (`matching=10`)。**

| ID | 変異 | 観測 node 数 |
|---|---|---:|
| M1 | 候補全滅で `exit 2` を復活 | 8 |
| M2 | canonical probe を解決後 PATH でなく base PATH で呼ぶ | 2 |
| M3 | `probe_error` を `unavailable` として扱う | 3 |
| M4 | 候補全滅でも selection / symlink を作る | 9 |
| M5 | `--perf-preflight-json` を常に付ける | 6 |
| M6 | CLI が receipt を無視して常に `use_perf=True` | 7 |
| M7 | sweep の closure が `use_perf=False` を伝播しない | 6 |
| M8 | 飽和判定不能でも noise を実行する | 3 |
| M9 | counter 必須検査を常時有効化 | 7 |
| M10 | maxrss 検査まで `use_perf` の内側へ入れる (過剰緩和) | 2 |

**段 3 レビュー A の静的予測との差 (実測が予測を修正した):**

- レビュー A は M3・M4・M7・M8 を「別層が先に拒否するので帰属しない」と予測し、親は
  erratum で再照準を指示した。**実測ではいずれも狙いどおり新規テストが捕まえた。**
  とくに M8 は懸念された `holdout_observation` ではなく
  `test_cli_no_perf_preserves_all_sweep_reps[20/50/80]` が検出した。
- **M9・M10 は過剰決定である。** 挙動で捕まえているのは `test_cli_no_perf_*` だが、
  `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`
  という**構造検査も同時に赤になる**。冗長 gate として明記し、単独変異の挙動証拠からは外す
  (DW-M03)。

## 実機で確かめたこと (DW-O16 が名指しする型)

本 wave は PATH 構築・interpreter 解決・外部 command 選定に触れる。レビュー通過だけでは
closed にしない型なので、親が login node で実走した。

1. **PATH 構築の実値.** 全滅時 `CALIBRATE_PATH` = `/usr/bin:<元 PATH>`、
   選択時 = `<TMPDIR>/bin:/usr/bin:<元 PATH>`。意図どおり。
   注記: 全滅分岐では `dirname(CALIBRATE_PYTHON)` = `/usr/bin` が前置され、この機体には
   `/usr/bin/perf` が実在する。従来はこの分岐が存在しなかったので新しい観測面である。
2. **interpreter と import.** `/usr/bin/python3.10` が版数 smoke rc=0、
   `sys.path.insert(0, REPO_ROOT)` 後に `orchestrator.calibrator.perf_preflight` の import rc=0。
3. **ホスト perf の非依存.** 常に成功する偽 `perf` を PATH 先頭へ置いて再走しても
   `test_pegasus_tools.py` 72 / `test_pegasus_calibration_workload.py` 79 /
   `test_calibrator_certify.py` 86 と**素の環境と完全に同数**。ホスト環境はテストへ漏れない。

**未実施:** canonical probe 自体の実走は login node では不可 (guard が `perf stat` 直叩きを拒否する)。
計算ノードへの認証 job 投入も本 wave では行っていない。

## 本 wave が達成しないこと

- **認定較正取得は perf 不在では回復しない。** 全 sweep を終えても
  `required-metrics-missing` / `selection-invalid` / `within-run-cv-invalid` により
  `quality.status = rejected`、`calibrate_rc = 1`、未登録である。
  「取得の回復」「予約浪費の解消」を完了扱いにしない。
- **no-perf 走の実費用は残る。** 既定値で 100 万・200 万・400 万・800 万・1600 万 records の
  5 点 × 3 rep = 15 subprocess。全点 miss rate 欠損なので早期飽和打ち切りは成立せず、
  正常完走なら 15 回すべて走る。`extime=3` の指定合計は 45 秒だが実時間には初期化等が加わる。
  予約は 7200 秒のまま。
- **perf 無しの測定証拠を正式較正として使えるようにするか**は本 wave の scope 外。
  `analyze.py:48-57` が飽和点を選べず、`report.py:106-123` と
  `orchestrator/campaign/env_contract.py:606-631` (content-addressed registered path と accepted を
  要求) が登録・利用への道を閉じる。昇格には「perf に依存しない較正が何を保証するか」という
  新しい認証契約が要る。**裁定へ返す。**
- [T-1329] (`tools/pegasus/floor_scoping.sh` の同型) は certified consumer へ繋がっていない
  別系統なので scope 外のまま。`t141_region_profile.sh` の `fail 2 perf_select` は
  perf record のサンプル取得が目的そのものなので**正しく、変えない**
  (段 3 レビュー B が `t141:1451-1487` で検算)。

## 記録の訂正

段 5 実装報告の「既存テスト期待値の変更なし」は無限定には成り立たない。裁定で指定した
閉包 inventory への CLI・sweep 追加と、runner guard 期待値の
`("not use_perf",)` → `("not use_perf", "use_perf")` は行っている。正しくは
**「裁定で指定された閉包・guard の期待値のみ更新。その他の既存期待値は変更なし」**。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief (親)
- `verbatim/s4-ruling.md` — 段 4 裁定 + プラン v2 + 変異事前登録 (親)
- `verbatim/s4-ruling-erratum-1.md` — 変異登録の erratum (レビュー A の帰属判定を反映)
- `verbatim/s-plan.md` — 段 2 プラン
- `verbatim/s-consult-a.md` / `s-consult-b.md` — 段 3 敵対相談 2 レンズ
- `verbatim/s-author.md` — 段 5 実装報告
- `verbatim/s-review-a.md` / `s-review-b.md` — 段 6 敵対レビュー 2 レンズ
- `verbatim/s-focus1.md` — 段 6 焦点再レビュー
- `verbatim/s-fix1.md` / `s-fix2.md` — 段 6 fix 2 巡
- `mutation/final-spec.json` — 本走の変異 spec (親が authored)
- `mutation/ledger.json` — 変異台帳 (probe と本走の派生形)

## 変異台帳を派生形にした理由 (受入の赤で判明した erratum)

初版は harness の生出力 `final-out.json` (418,586 bytes、
sha256 `f702794ab971c240ce7070dc8dffbc2f3bebb6d48cbcb052fef25ee8af19c16e`) と
`probe-out.json` (466,299 bytes、
sha256 `7f261a9bd2dfe4310c4a20e78d00d30754580d9e619aa39ea7c51bfb53073843`) を
そのまま収容した。**これが受入全走で 45 件の赤を出した。**

生出力は pytest の収集一覧を丸ごと抱えており、その中の test 関数名
(`test_cli_rr50_...` / `test_cli_rr80_...` が各 2 件) が
`orchestrator/campaign/s8b_holdout_freeze._assert_search_pass` の conjunction に当たる。
同関数は holdout の `conjunction_hits` が空であることを要求するので、
`test_s8b_oracle_driver.py` と `test_s8b_floor_campaign.py` の 45 件が
`FreezeError: holdout hit 2 件` で落ちた。

**生出力は repo へ入れず、repo 外の `/work/1/SFC/tanab/mutation-scratch-t1328/` に残し、
上記の sha256 と byte 数で引用する。** `mutation/ledger.json` は同じ生出力から派生した台帳で、
baseline の status / rc / failed_nodes / collection_sha256、各変異の id / 期待 status /
実 status / rc / 期待 node / 観測 node、および `repo_head` / `spec_sha256` / `runner_sha256` /
`tool_sha256` を保持する。派生台帳自身に検出語が残っていないことを機械で確認している。

**段 7 の三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=0 だった。**
同 CLI の候補集合と、t080 e2e が走らせる `_assert_search_pass` の候補集合は同じではない。
**走査器 1 本の緑を全 gate の緑と読んではならない。** 検出者は受入全走だった。
