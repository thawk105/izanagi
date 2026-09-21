# [T-2812] 新 pin main から旧系列 4 本を再開・再投入するための整合 — 設計と read-only 実測 (裁定パッケージ)

- wave: `dev-wave-t2812-old-series-realignment` (branch `worktree-t2812-old-series-realignment`、起点 local main `5efd69367`)
- 依頼の逐語は `verbatim/origin.md`、段 1 brief は `verbatim/s1-brief.md`、段 2 plan は `verbatim/s2-plan.md`、段 3 相談は `verbatim/s3-consult-A.md` (正しさ境界) と `verbatim/s3-consult-B.md` (既裁定整合・費用)、段 4 裁定は `verbatim/s4-adjudication.md`、probe の逐語は `verbatim/probe-script.md`
- **実装 0 行。** 本 wave は設計と read-only 実測だけで、実装・reseal の実行・候補 file の削除・認可改訂・再投入は行っていない (依頼の指定)
- 上流: D2150 項 1 (②③⑤ は各新系列の着手時)、D2184 (射程限定と却下 4 種)、D1777 (submodule を PIN へ checkout する投入手順)、D2187 (K2 pair の claim)、D2194 項 2 / 3 / 4 / 5、D2196 (g1 validator)

## 0. 結論 (先に書く)

1. **期待 admission policy の変更を提案する対象は g1 だけである。** K2 と A-1 sized v3 は既存の正規手順 (D1777: gitlink を変えず submodule だけ系列の pin へ checkout。以下**経路 H**) で境界と pin 照合を通る (実測 `K2-PIN-H` / `A1-BOUNDARY-H` / `A1-SOURCE-H`)。ただし両系列にも pin 以外の未了がある — K2 は pair の claim 修復 (D2187) と旧 lock の codec epoch (下の 5)、A-1 は attempt-0003 の認可 (§5 項 3)。B-4 床値 f1 は窓 JSONL の `loaded_head == HEAD` により同じ submit-tree に固定されており、移行の対象ではない。
2. **g1 の live launch で観測された最初の拒否は manifest 内 binary の admission policy 不一致だけである** (12 cell とも同一文言)。段階 4 と同じ期待値のまま `expected_policy=None` による個別の歴史検証にすると 12/12 が通る (`G1-BIN-HIST`)。**ただしこれは段階 4 全体の通過を意味しない** — 段階 4 の残部 (journal・共有 admission 台帳・result・床値選択) と段階 5 以降は未観測であり、protocol は現行 env 契約の `contract_sha256` も要求する (`s8b_ratified_freeze.py:3167–3176`)。
3. **「現行 registry + 系列自身の pin」で policy を組み直すと、記録値 `949ddcc2…` に exact 一致する** (`POLICY-SERIES-PIN`)。g1 の 12 receipt・B-4 の record・A-1 attempt-0002 の identity preimage 3 件すべてに一致し、対照 (現行 pin) は `db6bc9ea…` = 現行 policy になる。**択 S' の要求値は到達可能** (DW-O13)。
4. **旧 binary の再 admission だけでは解消しない (D2184) は実測で裏付いた。理由は class の導出ではない。** 記録済み receipt に stock-baseline は 1 件も無く (g1 12 cell と B-4 は human-reviewed、review_id `s8b-floor` は現行 registry に登載)、receipt を出し直すと receipt bytes が変わり manifest → floor_source → 批准世代の sha 束縛が崩れる = D2184 が却下した「receipt の張り替え」に当たる (静的帰結。receipt の再発行は実施していない)。
5. **pin とは別の epoch も旧 campaign の live な再開を止めている (新事実)。** K2 pair の `campaign.lock` は現行 codec が decode を拒否し (`campaign_lock.py:491`、T-2344 の enforcement closure 63 → 85)、歴史 codec でだけ読める。
6. **⑤ の AI reseal は 1 file の追加で B-10 grid の凍結木 pin を動かす。** 発行先は `output/s8b-freeze/floor-protocols/` で、`tools/pegasus/b10_backoff_grid.sh:22,585` が `output/s1-freeze` + `output/s8b-freeze` 全体の sha を pin している。commit 前は resolver が拾わない (`s8b_floor_campaign.py:983`)。

## 1. 実測 (login pegasus02、新 main `5efd69367`、gitlink = submodule = `e9e477ca1b55348ab4530de0b1cf663ce4555290`)

権威は `evidence/probe-2.json` (probe-1 は `POLICY-SERIES-PIN` と歴史 codec 縮退を足す前の走)。probe は Codex `role=author` + fix1 が書き (`verbatim/probe-script.md`、sha256 `6e280172…`)、repo 外 (job dir) に置いて親が login で実行した。production の読取り検査関数だけを呼び、書込み経路 (reseal / store / place / produce / submit / claim) は 1 つも呼んでいない。

| check id | 観測 |
|---|---|
| `K2-PIN-NEW` / `K2-PIN-H` | 新 main = `patchharness: HEAD (e9e477ca1b55) が pin (511c9538…) と不一致` / 経路 H = 通る |
| `POLICY-CURRENT` | 現行 policy sha `db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a`、`repo_stock_pin` = `e9e477c`、generator registry 7 種 / review registry 3 種 (`s1-known-axes`, `s8b-floor`, `s8b-oracle`)、`p3_s4_loop.PIN` と `paper_story_a1_paired.CANONICAL_CCBENCH_OID` はともに `511c9538…` |
| `K2-LOCK-PAIR` | 現行 codec = `authority.contract_loader_blob_sha256s の exact key 集合が不正` で拒否 (`campaign_lock.py:492–496`) / 歴史 codec (`decode_historical_campaign_lock`) = 読める。lock の admission preimage は現行 policy と同値 (`repo_stock_pin` = `e9e477c`)、`identity_preimage.ccbench_commit` は `511c9538…` |
| `A1-BOUNDARY-NEW` / `-H` | 新 main = `CCBench login-submit: canonical HEAD mismatch` / 経路 H = 通る |
| `A1-SOURCE-NEW` / `-H` | 新 main = pinned-clean 不一致 / 経路 H = 通る |
| `A1-IDENTITY` | attempt-0002 の `result.json` の 3 workload の campaign identity preimage は `repo_stock_pin` = `511c953`。現行 preimage との差は**この 1 field だけ** (campaign 全体の同一性は示していない) |
| `G1-LOAD` | 批准 loader 成功 (generation 1、sha `7e1114…`、G `32ba8cae4`) |
| `G1-LAUNCH` | `[manifest-invalid] binaries[rr20::backoff_fixed_best] admission receipt が不正: receipt admission policy が現行 policy と不一致` (cause `binary-admission`) |
| `G1-BINARIES` | 12 cell (rr20 / rr80 × backoff_fixed_best / ident_all / p2_2_flag_opt / sort_best / stock_common / system_gate) すべて class = human-reviewed、policy `949ddcc2…`、source `511c9538…`、protocol = `…--511c9538….json` (`ccbench_pin` = `511c9538…`、`contract_sha256` = `e576e9cd…`) |
| `G1-BIN-HIST` / `-CURRENT` | 段階 4 と同じ kwargs で `expected_policy=None` = **12/12 通る** / 現行 policy = **12/12 拒否** (同一文言) |
| `POLICY-SERIES-PIN` | 現行 preimage の `repo_stock_pin` を `511c953` (g1 protocol / `p3_s4_loop.PIN` / A-1 canonical の先頭 7 桁、3 者同値) に差し替え production の正規化 (`decode_historical_build_admission_policy`) で sha を取ると `949ddcc2…` = g1 12 receipt の集合と exact 一致、B-4 record と一致、A-1 identity preimage 3 件と dict 一致。対照 (`e9e477c`) は `db6bc9ea…` = 現行 policy sha・K2 pair lock preimage と一致 |
| `B4-PROTOCOL` | `resolve_current_floor_protocol` = `現行 env 契約の floor protocol を一意に解決できない: current_count=2 head_exact_count=0` (候補 = anchor `d706650…` と versioned `511c9538…`、現行契約 `e576e9cd…`、HEAD gitlink `e9e477ca…`) |
| `B4-RECORD-HIST` / `-CURRENT` | 記録 policy = 通る (class human-reviewed、review `s8b-floor`) / 現行 policy = 拒否 |
| `B4-W1-HEAD` | w1 JSONL 3 本の `loaded_head` = `2ba4000870c63254132410b3002b5298c0c6a210` = t2288 submit-tree の HEAD。新 main とは不一致 |
| `READMIT-STOCK` | 記録済み receipt に stock-baseline は 1 件も無い。g1 12 件と B-4 は human-reviewed で review_id は現行 registry に登載 (= registry membership の確認であって再 admission の実測ではない) |
| `READONLY` | 3 木の porcelain 出力・submodule HEAD・観測対象 store の存在判定が前後一致 (`binary_store_before=false` / `after=false`)。**bytes 全体の不変や測定時 source の不変を示すものではない** |

親が既存 CLI で直接測ったもの:

| 経路 | 観測 |
|---|---|
| `b4_binary_record place` (`evidence/b4-place.err.txt`) | `binary store preflight admission 不一致: cell=rr20::stock_common: receipt admission policy が現行 policy と不一致` (rc=1、書込み 0) |
| `floor_pair_driver --validate-only` (rr95、期待 sha は D2138、`evidence/b4-validate-rr95.err.txt`) | `binary b4-candidate を lstat できない: …/output/env/pegasus/binaries` (rc=1) = policy 判定より手前の未配置で停止 |
| `s8b_oracle_driver gate-check --freeze …holdout_freeze.v2.g1.json` (`evidence/g1-gate-check.json`) | rc=2、`allowed: false`、拒否 2 件 (未知性層 2 の hit = rr20 / rr80 それぞれ同じ 4 path + launch-validate の policy 不一致)、held checks 3 件 |

rc は親が shell で観測した値で、保存した JSON / stderr からは復元できない (`evidence/cli-rc.txt` に別記)。`place` の「書込み 0」は、観測 (`output/env/pegasus/binaries` が前後で不在) と、preflight の admission 照合が書込みより前にある静的事実 (`s8b_floor_campaign.py:5825–5836`) の両方による。

## 2. 経路の定義と系列ごとの可否

- **O** = pin 前進前の固定 checkout (submit-tree) で継続する。
- **H** = 新 main の superproject に、submodule だけ系列の pin を checkout する (D1777、`tools/pegasus/README.md` §7)。gitlink の差は commit しない。
- **O'** = `fec4a8187` (pin 前進直前の main、A/X を含む) に必要な修正を移植した別 branch。
- **S'** = live の期待 admission policy を「批准 protocol の pin + 現行 registry」で組み直す (consumer 限定)。
- **N** = 新 pin の新系列 (新登録・reseal・再 build・再測定・再凍結)。

O と N は排他ではない (旧系列を O で閉じつつ、新 pin の新系列を別に始められる)。

| 系列 | O | H | O' | S' | N |
|---|---|---|---|---|---|
| K2 の巡 | 成立 (旧条件の継続) | **成立** (T-2795 の pair 投入が HEAD `6a3e158` で候補を certified まで通した実績。ただし pair 全体は claim で不成立、stock は build 未到達) | 可能だが pair 修復の移植が要り保守費用に見合わない | 不要 (旧 lock の復活は codec と claim も絡む) | 新 pin の別系列としてなら可能。旧巡の継続にはしない |
| A-1 sized v3 | 成立。ただし attempt-0003 は**現行コードで未認可** | 境界・source は成立 (実測)。認可は同じく未整備 | 認可改訂を旧 base へ移植する案。保守費用増 | 推奨しない (build context・identity・WAL まで旧 epoch へ揃える必要があり g1 限定案の射程外) | 新 study・新登録が要る (D2096 項 5 の「3 study 目は作らない」の改訂が別途必要) |
| 凍結 v2 g1 の launch | `fec4a8187` は policy が合うが T-2810 の修正を持たず journal / lineage で止まる → 無修正 O は解決しない | submodule を戻しても `_new_policy()` は新 main の `CURRENT_PIN` を使うので段階 4 の拒否は不変 | **解決候補** (T-2810 の 3 commit + 候補削除の移植。現行相当を主張するなら `cfab7a2f2` / `65e94a3a7` も移植) | **推奨候補** | 可能だが `s8b_ratified_freeze.py:3273` が generation 1 以外を拒否するので g2 の契約設計と裁定が別途要る |
| B-4 床値 f1 | **正規の継続** (w2 / finalize) | 解決しない (resolver は HEAD gitlink を見る) | HEAD が変わるので f1 の継続不可 | place の policy だけ直しても w1 の HEAD 一致を満たさない | 新 pin の**新 campaign** としてなら成立 (f1 は移行しない) |

## 3. 系列ごとに要る ②③⑤ と source / admission

| 系列 | ② 新登録・identity | ③ driver の pin | ⑤ successor floor protocol | source / admission |
|---|---|---|---|---|
| K2 | 経路 H では現行 policy を持つ**新 campaign ID・新 lock**。旧 lock は張り替えない (そもそも現行 codec が拒否) | `p3_s4_loop.py:116` の full OID は `511c9538…` 据え置き (系列の比較可能性) | 不要 | 候補は coder-authored、stock は `_stock_capability_resolver` (`p3_s4_loop.py:2005,2089`) が generator receipt を供給して machine-generated になるので `CURRENT_PIN` に依存しない。**ただし `src_token == STOCK` の成立は未観測** |
| A-1 sized v3 | study を保持して新 campaign ID・lock・認可 record。attempt 間で campaign ID の一致を要求する述語は rerun 判定に無い (今回の cfg / lock / WAL / materialization 内の一致は要る) | canonical full OID は `paper_story_a1_paired.py:211` ほかと source 契約とも `511c9538…` 据え置き | 不要 | 両 arm とも machine-generated (`CURRENT_PIN` 非依存)。境界は submodule HEAD と superproject status (submodule 除外) だけ |
| g1 | S' では新登録なし (既存の批准世代をそのまま live 消費する)。N では新世代・新証明書の契約が要る | 変更しない (chain 側の protocol pin を権威にする) | S' では不要。N では reseal + 再 build + official 再測定 | S' = 期待 policy の権威を「現行 repo の pin」から「批准 protocol の pin + 現行 registry」へ移す。source pin・contract・cell・binding の外部期待値は維持 |
| B-4 床値 | f1 は変更なし。N では新 campaign / spec、artifact・receipt sha、測定窓・出力 identity を新登録 | floor-pair に K2 型の PIN 更新だけで済む入口は無い (spec の artifact / provenance 束縛ごと) | N で必要。`reseal_protocol()` → **commit** → resolver が新 pin を一意に選ぶ | N では現行 policy で新 binary を build・place する。旧 record の再配置は現行 policy が拒否 |

## 4. g1 を解く択

### S' (推奨候補)

- **やること:** `build_admission.py:499,510` の policy 構築を、通常呼出しは `CURRENT_PIN` のまま、批准系列 consumer だけ検証済み full OID の先頭 7 桁を使う形に限定改訂する。schema・coder authority・generator / review registry は必ず現在のコードから取る。receipt や歴史 preimage を policy の入力にしない。返すのは既存の exact 型 (`HistoricalBuildAdmissionPolicy` を live authority に流用しない — `s8b_binary_admission.py:369` が exact 型を要求する)。
- **射程 (3 入口):** ① launch 段階 4 (`s8b_ratified_freeze.py:3394` → `:1905`。pin は `:3330` の raw hash 照合と `:3369` の protocol 検証を通った `protocol["ccbench_pin"]`)、② W-5 の store 消費 (`s8b_oracle_driver.py:1003,1026`。pin は検証済み floor artifact の document)、③ **記録済み binary を消費 checkout へ配置する経路**。③ を欠くと W-5 は `s8b_oracle_driver.py:1043` の実体照合で止まる (相談 B の real 指摘)。
- **③ は入口名を足すだけでは閉じない (独立レビューの real 指摘)。** 現物の `b4_binary_record.py:169–173` は **receipt 自身から期待 pin と contract を取り**、批准済み object や manifest を受け取る引数を持たない。したがって S' の「receipt 由来の pin を期待値にしない」と現状の入口は両立しない。実装 wave への要求は次のとおり: (i) 期待 pin・contract・対象 record を**検証済み chain (批准世代 → protocol → manifest)** から束縛して渡す経路にする、(ii) 既存 12 binary の取得元 (現状は `/work/1/SFC/tanab/izanagi-b4-floor-binaries` の store)・配置先 root・manifest の `store_path` と `binary_sha256` の対応を明記し、欠落は拒否のままにする、(iii) **一般の B-4 place と floor producer / resume (`s8b_floor_campaign.py:4836,5884,6495,8149`) は現行 policy のまま据え置く**。この (i)〜(iii) を満たす設計が S' 採択時の実装範囲であり、本 wave では設計しない。
- **保つもの / 失うもの** (相談 A):

  | 性質 | S' の扱い |
  |---|---|
  | generator / review の名前集合の変更による失効 | 保持 (追加でも sha が変わる) |
  | coder authority 種別の epoch | 保持 |
  | policy schema 世代 | 保持 |
  | 現行 repository の stock pin と同じ epoch であること | **失う** (系列 pin の epoch へ置き換える) |
  | 測定 source と批准 protocol の対応 | full OID の別検査で保持 (`s8b_binary_admission.py:434–435`) |
  | admission 実装・意味論全体の同一性 | **元からこの policy sha の保証外** (実装・review の意味・closure は preimage に入らない) |

- **攻撃の検査 (相談 A、refuted):** 別 full OID の source、先頭 7 桁だけ同じ別 OID、別 contract の receipt、名前集合の違う registry、store 内 binary の差し替え、coder-authored receipt の混入はいずれも既存検査が拒否する (`s8b_binary_admission.py:362–365,371,434–438`、`s8b_ratified_freeze.py:3173–3176`、`s8b_oracle_driver.py:1043–1052`)。正しく実装した S' に固有の不正受理例は見つからなかった (全攻撃の不存在や live 成功の証明ではない)。
- **誤実装で静かに通る形:** resolver 失敗時に `None` へ落とす (live 拒否にする)、receipt 由来の pin を期待値にする (caller のデータ経路を検査する)。
- **D2184 との関係:** policy 照合の除去・曖昧 fallback・receipt 張り替え・live への `expected_policy=None` の**いずれでもない**。ただし「現行 repo の `repo_stock_pin` への依存を切り離す」効果では D2184 が「必要なら別の裁定」と書いた択と実質同じなので、**無裁定で実装しない**。

### O'

`fec4a8187` を base に、T-2810 の実装 3 commit (`dc5b0f39b` / `0d943f9cb` / `083a45ee9`) と候補 file 削除 (D2194 項 5 の裁定どおり、削除 commit は未実施) を移植する。現行 main と同じ検査を主張するなら `cfab7a2f2` (意味 witness 21 → 22) と `65e94a3a7` (exact-85 enforcement closure) も移植して閉包を検査する。validator は branch 名 main を要求せず、O' 自身の root で load し `activation_head` と launch 時 HEAD を一致させる (`s8b_ratified_freeze.py:3268`)。別 root で得た validated object の流用は `t080_freeze_migration.py:2234` が拒否する。

### N

新 protocol (reseal + commit)・再 build・official 床値の再測定・新世代の凍結と批准に加えて、**g2 を扱う launch 契約の設計と裁定**が要る (`s8b_ratified_freeze.py:3273` が generation 1 以外を `certificate-generation-scope` で拒否)。generation 制限だけを削除する案は採らない。

**N には official 再測定側の停止条件も付く (独立レビューの real 指摘)。** D2120 項 2 (a) は当該 holdout 集合の official 走行を打ち切っており、chain を含む main と継承 checkout では `s8b_floor_campaign.py:5515–5540,5616–5636` の zero-hit clean scan が赤になるため、後続の official は別 branch から起動すると定めている。したがって N を採るときは、g2 契約と予算だけでなく **(a) 同じ rr20 / rr80 を再測定する認可と D2120 項 2 (a) との関係、(b) clean scan を満たす測定 checkout、(c) その checkout へ移植する現行修復の範囲、(d) 新成果物の取り込み順序**を同時に裁定する必要がある。scan 除外を広げて通す解決は採らない (D2120 項 2 (a) が却下済み)。

## 5. 裁定を要する点 (択と推奨)

1. **g1 の経路: S' / O' / N。推奨 = S'。** live の受理集合を「現行 repo pin 由来の policy」から「検証済み系列 pin + 現行 registry 由来の policy」へ広げる変更であり、D2184 が別裁定へ返した択に当たるので承認が要る。射程は §4 の 3 入口に限定し、他系列・他 consumer へ広げない。
2. **K2: 次巡を新 main から (経路 H で) 走らせる採択と、pair 1 job + 4 巡目 1 job の予算。推奨 = 経路 H。** 手順そのものは D1777 で既定であり、ここで裁定するのは「旧系列の継続を固定 checkout に留める現行の既定を、K2 については新 main の経路 H へ移すか」と予算である。source PIN は据え置き、epoch 差 (campaign ID・receipt・cache identity・enforcement closure) を記録に開示する。予算の再提示は D2187 の修復後 (D2172 項 3 の元の認可は撤回されていない)。
3. **A-1 sized v3: 3 本目を走らせるか。走らせるなら経路 H。** attempt-0003 は現行コードでは未認可 (`paper_story_a1_paired.py:228` の列挙は 0002 のみ、解除できる prior は 1 件)。再走の目的・**解除する prior 集合**・予算を裁定する。証拠の削除や全 prior の無条件除外は不可。
4. **g1 の残手番は S' で代替されない。** 候補 file の削除 (D2194 項 5、並走 wave が実施)、W-4 の spec 承認 (`s8b_oracle_spec.py` の承認 sha は `None` = `no-approved-spec`)、held checks 3 件、W-5 の store・環境・reservation・予算はいずれも別に残る。
5. **N を選ぶ場合の追加契約と費用** (下の 6 も参照) (g2 launch 契約、再 build 約 7 分 + official 測定約 71 分 = job 全体 約 1.33 node-hour の参考値、再凍結・批准、B-10 の `EXPECTED_FREEZE_TREES_SHA256` 更新) を一括で提示する。reseal の完了を条件達成と読まない。

6. **択は将来を縛らない。** ここで S' / H を採ることは、後で新 pin の新系列 (N) を始めることを禁じない (O と N は排他ではない)。§5 の N は「今回の旧系列再開の代替として選ぶか」の意味である。

**受入 (実装 wave 側) への申し送り:** D2196 決定 4 の `_ACTIVATED_G1_REFUSALS` は policy 不一致が解けた時点で追随が要る。負例として残すもの = 通常 consumer (floor producer / resume、oracle の新 build context) が現行 policy のままであること、配置入口が receipt 由来の期待値を拒否すること、A-1 で 0001 と 0002 の両 prior が残るとき 0002 だけの解除では止まること。

**裁定に返さない (親の確定事項):** B-4 床値 f1 の w2 (2026-09-29T00:00Z 以降、`now + 24h ≤ 2026-10-07T00:00Z`) と finalize は t2288 submit-tree のまま継続する — 依頼と D2184 の既定どおりで、新しい択ではない。B-4 **本走**は D2194 項 3 (base driver の carrier 実装・定義発効・caller の lock 読取り修復) の着地に依存する。

## 6. 費用と順序 (参考値。計算資源の認可ではない)

| 択 / 対象 | 計算費用の根拠 | wave・人間手番 | 動かす研究と順序 |
|---|---|---|---|
| g1 S' | 床値の再 build・再測定は不要 | 整合実装 1 wave 以上 + 受理集合の裁定 | S' → (独立した候補削除) → launch 再観測 → W-4 承認・store・環境 → W-5 → certified 選択 |
| g1 O' | 再測定不要。移植と受入は未見積り | 移植検証 1 wave 以上 | S' と同じ研究へ進むが、現行相当を主張するなら移植閉包が増える |
| g1 N | 12 cell build 438 秒、96 session 約 4,284 秒、job 全体 4,769 秒 (約 1.33 node-hour、T-2698 の実測) | 世代契約の実装・測定・再凍結・発効 | successor commit → build・official → 新凍結・批准 → W-4 → W-5 |
| K2 H | pair 失敗 job 74 秒、候補 build 15 秒 (stock 未到達なので完走時間へ外挿不可) | D2187 修復 wave → 予算再提示 → pair 1 job → 4 巡目 1 job | D2194 項 2 の派生入力を使う 4 巡目 |
| A-1 H | attempt-0002 の 3 job elapsed 合計 2,218.79 秒 (約 0.62 node-hour) | 0003 の目的・prior 解除・予算の裁定 → 認可実装 → 投入 | 次 attempt (既存 2 attempt の記述更新はこれを待たない) |
| B-4 f1 (O) | w1 の 3 job = 4,182 + 4,145 + 4,607 秒 (約 3.59 node-hour) | 新しい経路裁定は不要 | 09-29 以降の窓で w2 → 同 checkout で finalize |
| B-4 N | 3 spec × 2 窓なら測定の参考量は約 7.19 node-hour + finalize 等 | successor・新 record / spec・凍結の準備 | 必要が生じた時点で具体化 |

## 7. 並走 wave との関係 (着地で変わる事実)

- g1 候補 file の削除 (D2194 項 5): 未知性層 2 の hit 列挙と held の期待値、`reverify_published_freeze` の段階 8 到達が変わる。本パッケージはこれを前提にしない。
- K2 pair の修復 (D2187): 認可の所有範囲と stock arm の到達が変わる。stock の admission は修復後の再投入で初めて観測できる。
- enforcement closure の前進 (T-2344): 新しい lock の identity に影響する。旧 lock の歴史読取りは D2194 項 4 のとおり現状維持。
- D2196 決定 4 の `_ACTIVATED_G1_REFUSALS` は、policy 不一致が解けた時点で追随が要る (受入への影響)。

## 8. 限界・言わないこと

- 本 wave は launch を成功させていない。S' は**未実装**で、適用後に段階 4 の残部や段階 5 以降で別の拒否が出ないことは観測していない。
- 「段階 4 を塞ぐのは policy だけ」とは書かない。観測したのは最初の拒否と、個別 12 receipt の歴史検証の成功まで。
- `READONLY` が示すのは status・submodule HEAD・store の存在判定の一致だけで、全 bytes の不変ではない。
- `POLICY-SERIES-PIN` の一致は「値が一致する」ことであって、registry が途中で変更・復元されていないこと、admission の意味が不変であることは示さない。
- `READMIT-STOCK` は registry membership の確認であり、receipt の再発行は実施していない。
- 経路 H の可否は境界検査と pin 照合の観測までで、実走 (build・測定) を含まない。H の測定 source は記録される (lock の `identity_preimage.ccbench_commit`、receipt の source) が、**親 HEAD を通常 checkout するだけでは測定木を再現できない**。
- 記録済みの判定・測定・凍結 bytes は本 wave で 1 つも変えていない (規律 7)。probe は書込み経路を 1 つも呼んでいない。

## 9. 段 3 / 独立レビューの所見と採否

- 段 3 相談 A (正しさ境界): real 3 件 = 「段階 4 を塞ぐのは policy だけ」が広すぎる / `READONLY` の射程 / S' の失効保証は policy に符号化された値に限る → **全採用** (§0-2、§1 の `READONLY` 行、§4 の性質表、§8)。S' が別 pin・別 contract・失効 registry の artifact を通すという攻撃は **refuted** (§4 の攻撃表)。
- 段 3 相談 B (既裁定整合・費用): real 3 件 = B-4 f1 の継続を不要に裁定へ返している / S' の配置経路が未了 / B-4 本走の D2194 項 3 依存 → **全採用** (§5 の「裁定に返さない」、§4 の ③、§5 項の B-4 行)。S' が D2184 の却下 4 種と同じという批判は **refuted**、ただし `repo_stock_pin` 依存の切離しという効果では別裁定が要ると明記。
- 独立 read-only レビュー (docs-only の必須 1 本、DW-C00): real 3 件 = S' 第 3 入口の権威・取得元が未確定 / N の official 再測定が D2120 項 2 (a) の停止条件を落としている / K2 の裁定区分が本文と決定 fragment で食い違う → **全採用** (§4 の ③ と N、§5 項 2)。相談 A の 3 限定が本文に反映済みであること、S' が却下 4 種に当たらないことはレビューでも **refuted** として確認された。逐語照合は 24 項すべて一致 (`verbatim/s6-review-A.md`)。

## 10. 工数

- codex 子 5 本: probe author 1 + probe fix 1 + plan 1 + 相談 2。
- 親の login 実走: 既存 CLI 3 回 (B-4 validate-only / B-4 place / g1 gate-check) + probe 2 回。計算ノード job は 0 (read-only 実測のみ)。
- 変異 matrix は免除 (実装面の差分 0、DW-S04)。受入全走は記録 commit の tip で実施する。
