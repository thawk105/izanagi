# [T-437] 凍結済み変異 spec (M01-M12) の実走 — D151 の受理集合の裏取り

- authority: none
- default_effect: no-state-change
- 実施日: 2026-09-01
- 対象 commit: `08a17b3b3271dc6e0db575a7c15afbbbb91f6328` (実走時点の local main)
- ユーザー裁定: 2026-08-25 /rulings 全件、択 (a) — 凍結済み仕様のまま実走する。
  設計判断は不要。正式 harness の実測を正とする

## 0. 実行系と束縛

| 項目 | 値 |
|---|---|
| 凍結 spec | `output/insights/2026-08-04_t407-ruleops-inventory/mutation-spec.json.gz` |
| 同 gz の sha256 | `e6e61440246c29ac7235dab5787ad2baba55f3965fc7c889d37df51090a9b6ab` |
| 展開後 JSON の sha256 | `aa6be6069c265e3365761151e2b9f9c32fa3bbfb1b81364316212abeac655721` |
| harness | `tools/mutation_worktree.py --runner-mode dispatch --detached` |
| runner | `python3 tools/run_tests.py orchestrator/tests/test_ruleops.py -q -rf -n 0 --force-dispatch` |
| 観測 root | 独立 clone `/work/1/SFC/tanab/mutation-src-t437` |
| 台帳 (本ディレクトリ) | `mutation-ledger.json.gz` (原 JSON sha256 `038bfd79e7a679390bd5fc45d112603448e1661bb1cf33ff840d2ff862baa9cd`) |
| 試行台帳 | `attempt-ledger.json.gz` (原 JSON sha256 `60bcf0b78e4b6f337ddac537e9ea14599ecac24a4ee1d64e0e425d54f31da376`) |

`--source-repo` に独立 clone を渡したのは、実走時点で並行 wave が 20 本超動いており、
共有 checkout を観測 root にすると走行前後の `git status` bytes が必ず動くためである。
wrapper receipt は `shared_snapshot_matches: true` / `teardown_completed: true` /
`terminal_ledger: true` / `failure: null` を返した。

runner の `-n 0` は F95 の恒久回避で、並列を切ると実測 node id から `@real_repo` 接尾辞が消え、
preflight と突き合わせの表記が一致する。runner argv 側の `--force-dispatch` は
pegasus-runbook §7.4 の要求で、これが無いと `run_tests.py` の §7.0.0 自動判定が login 実行を
選びうるため dispatch 受領証行が出ず baseline が `PARSE_ERROR` になる。

## 1. 何を測っているか

D151 は「`tools/ruleops.py inventory` は strict UTF-8 として decode できない blob を `items` から
除外し、除外件数を根の `skipped_non_utf8` へ常時出す」と決めた。除外条件は **decode 不能だけ**で、
suffix・path 名・JSON/Python としての妥当性・NUL の有無・size を理由にしてはならない。件数は
`--kind` 適用後の集合の中で path 単位に数え、同じ blob OID が複数 path にあればそれぞれ数える。

12 変異はこの条項へ一対一で対応している。

| 変異 | 攻撃する条項 | 具体 |
|---|---|---|
| M01 | 読み飛ばす | 除外をやめて例外送出へ倒す |
| M02 | 除外条件は decode 不能だけ | 全 blob を強制的に decode 失敗扱いにする |
| M03 | suffix を除外理由にしない | `.raw` だけ読み飛ばし、他は例外 |
| M04 | path/scope を除外理由にしない | insight scope だけ読み飛ばし、他は例外 |
| M05 | 件数を常時出す | 読み飛ばすがカウンタを増やさない |
| M06 | 件数は `--kind` 適用**後**の集合で数える | `--kind` の絞り込みを decode ループの後ろへ移す |
| M07 | 同じ blob OID が複数 path にあればそれぞれ数える | path 単位でなく OID 集合の濃度で数える |
| M08 | suffix を判定に使わない | 件数を「`.raw` で終わる path の数」に差し替える |
| M09 | NUL の有無を除外理由にしない | NUL を含む blob を追加で除外する |
| M10 | 件数は選択集合の中で数える | scope 外の blob を件数へ足し込む |
| M11 (正例) | 全件非 UTF-8 でも成功する | `items` が空なら fail-closed する過剰拒否を入れる |
| M12 | schema は `ruleops-inventory/v2` | 版名を v1 へ戻す |

M11 だけが正例で、`DW-M01` の「受理集合を縮小する wave は承認外の過剰拒否の正例も登録する」に
対応する。**受理されるべき入力 (全件非 UTF-8) が受理され続けること**を守る側の変異である。

## 2. 事前登録の生存検査 (実走前、DW-M07)

事前登録は 2026-08-04、実走は 2026-09-01 で約 1 か月空いた。

| 検査 | 結果 |
|---|---|
| 全 replacement の `old` 逐語が累積適用後も一意出現 | 12/12 OK (`anchor_counts` は全件 1) |
| 期待 node が `test_ruleops.py` に実在 | 7/7 OK (延べ 7 種、欠落 0) |
| `hang_risk: true` の変異 | 0 件 (dispatch 本走で孤児化する型を含まない) |
| wrapper preflight (`--plan-only`) | rc=0、`shared_snapshot_matches: true` |
| `injection_diff_sha256` の一意性 | 12/12 相異なる (同一注入への潰れなし) |

`tools/ruleops.py` は登録後の 2026-08-10 に 2 回変更されている
(`6e59677fe` git timeout を作業量比例予算へ、`5f38b96f8` pickaxe を candidate epoch 窓へ)。
いずれも 12 変異の anchor 領域の外だったため、逐語は無傷で残った。

## 3. 実走結果 — KILLED 9 / MISMATCH 3 / SURVIVED 0

baseline は `PASSED` (rc=0、失敗 node 0、32.4 秒、collection sha256 `fd5470e32ce3…`)。

| 変異 | 種別 | 期待 | 実測 | 判定 | 所要 | 差分 |
|---|---|---|---|---|---|---|
| M01 | negative | 5 | 4 | MISMATCH | 33.2s | 欠落 1 (下記 §4.1) |
| M02 | negative | 6 | 7 | MISMATCH | 32.6s | 欠落 1 (§4.1) / 余分 2 (§4.2) |
| M03 | negative | 3 | 3 | KILLED | 32.4s | — |
| M04 | negative | 3 | 3 | KILLED | 32.4s | — |
| M05 | negative | 4 | 4 | KILLED | 32.8s | — |
| M06 | negative | 1 | 1 | KILLED | 32.6s | — |
| M07 | negative | 1 | 1 | KILLED | 32.2s | — |
| M08 | negative | 4 | 4 | KILLED | 37.4s | — |
| M09 | negative | 3 | 3 | KILLED | 32.3s | — |
| M10 | negative | 4 | 5 | MISMATCH | 32.2s | 余分 1 (§4.2) |
| M11 | positive | 1 | 1 | KILLED | 32.1s | — |
| M12 | negative | 2 | 2 | KILLED | 32.2s | — |

**SURVIVED は 0 件、TIMEOUT 0 件、PARSE_ERROR 0 件。**
事前登録が突いた 12 方向のいずれにも、受理集合の穴は無い。正例 M11 も KILLED で、
受理側 (全件非 UTF-8 を成功として受ける) の防壁も生きている。

MISMATCH 3 件はいずれも「変異が生き残った」のではなく**期待集合と実測集合のずれ**である。
`KILLED` は `failed_keys == expected_keys` の完全一致契約なので、
これらを KILLED と読み替えていない (`DW-M08`)。

## 4. MISMATCH の構造化所見 (規律 3)

### 4.1 期待 node が事前登録の 8 日後に skip されるようになった (M01、M02)

M01 と M02 の欠落は同じ 1 node に集中する —
`test_real_checkout_independent_maximum_package_and_runner_preflight`。

この node は `orchestrator/tests/growth_test_holds.py` に
`hold_axis="tracked_files"` / 理由「Scans the real checkout, so cost grows with tracked files.」
で登録されており、commit `16df3e4e3` (2026-08-12、成長比例テストの恒久保留機構を導入し
30 function を保留) で入った。`orchestrator/tests/conftest.py` の growth hold 機構は、
専用の環境変数が正確なトークン値で与えられない限り当該 node を **skip** する
(`IZANAGI_GROWTH_HOLD_V1` の skip 理由が出る)。

**事前登録は 2026-08-04 なので、殺し手が登録の 8 日後に導入された機構によって黙らされた。**
変異注入そのものは実在し (`anchor_counts` = 1、`injection_diff_sha256` あり)、
production コードの退行でもない。**流れたのは実装ではなくテストの統治層である。**

保留台帳自身が付帯損失を明記している — この node を保留すると、最大パッケージの固定サイズ検査、
`MAX_CANDIDATES` / `MAX_QUERY_COUNT` / `MAX_SIGNAL_TOKENS`、独立 inspect/pickaxe 証拠、
45/60 秒の preflight 境界も同時に失われる。本走はそれに 1 項目を足す —
**「非 UTF-8 blob を実 checkout 規模で読んだときに inventory が fail-closed へ倒れない」という
性質も、現行の既定 runner 形では誰も検査していない。** 合成 fixture 側 (M01 で 4 node、
M02 で 7 node) は生きているので、性質そのものが無防備になったわけではない。
失われたのは**実 checkout 規模での**確認である。

### 4.2 期待 node の登録漏れ (M02、M10)

期待に無い kill が出た。

- M02: `test_inventory_retains_oversize_valid_utf8_blob`、`test_git_read_closed_set_and_environment_scrub`
- M10: `test_inventory_retains_oversize_valid_utf8_blob`

**事前登録 commit `7f767ee87` (2026-08-04) の版で当該 assert の実在を確認した。**

- `test_git_read_closed_set_and_environment_scrub` は当時から
  `assert R.build_inventory(repo)["items"]` を持つ。M02 は全 blob を decode 失敗へ倒すので
  `items` が空になり落ちる
- `test_inventory_retains_oversize_valid_utf8_blob` は当時から
  `assert items[path]["bytes"] == len(payload)` と `assert inventory["skipped_non_utf8"] == 0`
  を持つ。M02 は前者を、M10 (件数へ scope 外 blob を足す) は後者を落とす

いずれも事前登録の時点で同じ形で存在していたので、**当時走らせても同じ余分 kill が出た**。
これは drift ではなく**登録時の漏れ**である。

**素材:** 漏れの構造は名前と性質のずれである。`test_inventory_retains_oversize_valid_utf8_blob` は
名前が「巨大な正当 UTF-8 blob の保持」を指しているのに、本文では件数の不変条件
(`skipped_non_utf8 == 0`) も同時に固定している。期待 node を**名前で選ぶ**と、
性質でしか見つからない被覆を落とす。同型の危険は
`test_git_read_closed_set_and_environment_scrub` にもあり、こちらは git 環境の掃除を見る
テストが `build_inventory` を素通し確認に使っているために巻き添えで落ちる。

**この 2 件は検出力の不足ではなく過剰である** — 期待より多く殺せている。したがって
D151 の防壁は事前登録が見積もったより厚い。ただし `DW-M03` の言う単一理由性は
その分弱く、これらの node は当該変異の**単独証拠には使えない** (冗長 gate として扱う)。

## 5. 凍結 spec を書き換えなかった理由

ユーザー裁定 (択 (a)) は「凍結済み仕様のまま実走する」であり、期待集合の是正は本 wave の scope 外である。
`DW-M08` は期待が確定できない場合の再登録・再走を認めるが、それは probe と明記した初回に対する
規定であって、**裁定で凍結を指定された spec を実測結果に合わせて後から書き換える経路ではない**。
実測結果に合わせて期待を書き換えれば、事前登録は何も拒否しない台帳になる。
よって MISMATCH は MISMATCH のまま凍結し、是正案は裁定パッケージ (§6) として返す。

## 6. 裁定パッケージ (実装せず、ユーザー判断へ返す)

いずれも本 wave では実装していない。

1. **growth hold と変異事前登録の相互作用** — 変異 spec の期待 node に登録された node が、
   後から growth hold / flaky hold に入ると、その変異は永久に MISMATCH になる。
   現状これを検出する経路は「実走して初めて分かる」だけである。
   選択肢: (a) 何もしない (実走時に判明すれば足りる)、
   (b) hold へ node を追加する側で、既存の凍結変異 spec を参照して警告する、
   (c) 変異 harness の preflight で「期待 node が hold 対象か」を検査する。
   (b)(c) はどちらも新しい gate なので `DW-G03` (族一般化には独立 2 例) の対象。
   **本 wave が観測したのは 1 例だけである。**
2. **M02 / M10 の期待集合の是正** — 再登録して再走すれば MISMATCH は解消するが、
   事前登録の意味を弱める。凍結の趣旨を優先するなら、erratum を残して現状のまま置く。
3. **`test_real_checkout_..._preflight` の保留解除の是非** — 保留は費用 (tracked file 数に比例) を
   理由としており、正しさを理由としていない。§4.1 が示すとおり、保留の代償には
   「実 checkout 規模での非 UTF-8 fail-closed 検査」も含まれる。
   費用と失う検査を突き合わせて判断する材料が要る。

## 7. 再現手順

```
zcat output/insights/2026-08-04_t407-ruleops-inventory/mutation-spec.json.gz > <repo 外>/spec.json
python3 tools/mutation_worktree.py \
  --source-repo <独立 clone> \
  --commit 08a17b3b3271dc6e0db575a7c15afbbbb91f6328 \
  --scratch-root <repo 外の既存 dir> \
  --spec <repo 外>/spec.json \
  --expected-spec-sha256 aa6be6069c265e3365761151e2b9f9c32fa3bbfb1b81364316212abeac655721 \
  --out <repo 外>/result.json --attempt-out <repo 外>/attempt.json --wrapper-attempt 1 \
  --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py orchestrator/tests/test_ruleops.py -q -rf -n 0 --force-dispatch
```

`--spec` / `--out` / `--attempt-out` は試験対象 checkout と全 registered worktree の外に置く。
`--detached` を欠くと変異を 1 件も実行せず中止する。
