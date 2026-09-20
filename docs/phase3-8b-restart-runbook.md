# phase3 8b 再開手順書 — 床値実測 → freeze v2 再凍結 → oracle 実走

スコープ B 部分再開のユーザー裁定 (2026-08-10、Q1 = (a)) を受けて、7 月に実装を終えた 8b の
機構が現行 main で生きているかを検分し、再開の順序と各段の合否判定を固定する。

**この文書は手順の正本であって状態の正本ではない。** 進捗と残課題は worklog 末尾が正本、
設計の経緯は `docs/phase3.md` の 8b 節が正本であり、ここへ再掲しない。

---

## 0. 不変事項 (再開しても変わらないもの)

- **8b の証拠価値は限定されたままである。** 「selector 実験は descriptor-conditioned synthesis の
  証拠には数えない」(`docs/phase3-8b-descriptor-design.md` の自己申告) は 2026-07-27 裁定でも
  今回の部分再開でも変わらない。床値実測は他候補にも要る測定土台として残る
- 絶対規律 1〜6、T-139 追補 A 段階 2 の凍結・blob 束縛に変更はない
- roadmap 本体の改訂は含まない

### 並走ガード (B 系 wave の起票文へ必須記載、Q3 = (a))

1. ノード同居なし — 単独性確認と静穏 preflight を計算ノード上で行う
2. T-139 の pilot / 本走 job が走行中はキュー投入を控える
3. 裁定帯域は A (T-139 本走線) 優先 — B 系の裁定要求は A の後ろに並べる

**「投入ゼロの wave」を名乗るときは検査系の自動 dispatch も数える。**
`tools/check_ai_provenance.py` と受入全走は login では完走せず計算ノードへ dispatch する。
計測を 1 件も投入しない wave でも、この 2 つは queue を使う (2026-08-11 に
「キュー投入ゼロ」と記録してから訂正した)。

---

## 1. 検分結果 — 現行 main で生きているもの

2026-08-10 に base main `44e35c8b` で実測した。値は実物から採り、既存 docs を根拠にしていない。

| 対象 | 判定 | 実測 |
|---|---|---|
| s8b 系テスト | 緑 | 1327 passed / 3 skipped / rc=0 (計算ノード job 900515、268.01 秒) |
| ↑ skip 3 件 | 検出力なし | 実ビルド canary 3 本。`cmake`/`gcc-13`/`g++-13`/`nm` が揃わないと skip し、Pegasus には `g++-13` が無い (runbook §7)。**実ビルド経路はこの緑に含まれない** |
| 凍結成果物 manifest | 緑 | `test_frozen_artifacts.py` 自走 2 passed / rc=0 (15 path が exact 一致) |
| floor protocol の ccbench pin | 一致 | `d706650cdb31e442bef45b9b4216951d4fb40969` = 現行 gitlink |
| floor protocol の env 契約 pin | 一致 | `e576e9cd…` = 現行 active (pegasus 第 1 世代) |
| floor protocol の freeze pin | 一致 | `315b1eb8…` = `holdout_freeze.json` の実 bytes |
| protocol × 現行 env 契約の live 照合 | 緑 | `validate_protocol_against_current` が OK を返す |
| selector 封印の 5 source pin | 全一致 | builder / role md / input schema / output schema / holdout freeze |
| `pre_oracle_head` | 健在 | `77664079…` は現行 HEAD の ancestor (rc=0) |
| T-080 移行受領証 | 健在 | bytes `b84f7832…` 一致、基準 commit `f04ae50b…` は HEAD ancestor |
| oracle gate (実物 freeze) | 設計どおり | rc=2、拒否理由は `floor-null` と `budget-null` の 2 件 exact |
| floor campaign の official 承認 gate | 設計どおり | core と CLI が同じ明示承認を二重に要求する ([T-2324]) |

**結論: 7 月実装分に腐りはない。** pin・封印・受領証はすべて現行 main と整合し、gate は設計どおりの
拒否を返す。再開を塞いでいるのは腐りではなく **未実装の段** (§3) である。
**toolchain 前提は 2026-08-11 に解決した** ([T-747] (B) / [T-783]。§5 R-4 が正本)。

### 1.3 再測 (2026-08-11、main `f4db7036`、wave `dev-wave-t8b-restart-residue`)

| 対象 | 判定 | 実測 |
|---|---|---|
| P1 ccbench gitlink | 一致 | `d706650cdb31e442bef45b9b4216951d4fb40969` |
| P2 凍結成果物 manifest | 緑 | `2 passed, 0 failed, 0 skipped` / rc=0 |
| P3 oracle gate-check | 設計どおり | rc=2、拒否は `floor-null` と `budget-null` の 2 件 exact。`holdout-freeze-verify:` の混入なし |
| 床値 driver source の凍結 pin | 無し | `FROZEN_MANIFEST` 23 件に `.py` は 0 件。`floor_protocol.json` が pin するのは `contract_sha256` / `ccbench_pin` / `freeze` の 3 つのみ |
| ↑ ただし commit pin は在る | 有り | `submit_floor.sh` の submission receipt が `source_commit` を pin し、実行時に imported module bytes を照合する (`floor_campaign.sh:524`、`certified_writer_preflight.py:85`)。「pin が無い」を運用前提にすると availability failure になる |
| 床値 producer の既存出力 | 不在 | `output/calibration/` 自体が存在しない (どの mode でも未実走) |

**P3 は §1 の表の値と同一である** (peer wave の `s8c_preregistration` NUL 検査追加を
取り込んだ後に再測しても変わらない)。

### 1.2 かつての前提の欠落 — Pegasus に固定要求の compiler が無い (**解決済み**)

> **現況 (2026-08-12 訂正)。** 固定要求は撤廃され、compiler は site 解決になった —
> `buildcache.compilers_for_current_site` が Pegasus compute では `gcc` / `g++` を選ぶ。
> **ただし 2026-08-12 の実投入まで、実体化経路 (`prepare_cell` → `source_digest.resolve`) だけが
> 既定値 `g++-13` のまま取り残されていた。** 現在は `cxx` を必須引数として通してある。
> 「解決済み」を build 経路だけで判断しない。
> 認可の根拠は registered calibration の `acquisition_receipt` との束縛検査であり、
> **build 前に fail-closed で照合する** (§5 R-4 が正本)。
> **以下は欠落が判明した当時 (2026-08-10) の記述であり、現況ではない。**

床値 driver は CCBench のビルドで `cc="gcc-13"`, `cxx="g++-13"` を**固定で渡していた**
(`s8b_floor_campaign` の build 呼び出し)。`buildcache` はこれを `shutil.which` で解決し、
PATH に無ければ `toolchain cxx が PATH に存在しない: 'g++-13' (fails-closed)` で倒れていた。

一方 Pegasus には `g++-13` がログインノードにも計算ノードにも無い。Pegasus 用の較正証明
(`certify_calibration.sh`) と floor job script の依存ビルド段は、いずれも
`command -v gcc` / `command -v g++` で**system の既定 compiler** を解決して記録する設計であり、
driver 側の固定要求とかみ合っていない。

**既定 compiler の実測 (2026-08-11 に登録済み calibration から採取)。**
「計算ノードは `g++-12`」は既定ではなく `g++-12` パッケージの存在を指す。
**登録済みの 2 世代の calibration は、いずれも計算ノード上で既定 compiler を
gcc 11.4.0 として記録している。**

- 第 1 世代 `calibration-753f535a8d024727.json`: `assigned_host_qstat=bnode011`、
  `pbs_jobid=0:867876.nqsv`、`compiler_path=/usr/bin/x86_64-linux-gnu-gcc-11`、
  `compiler_version` 先頭行 `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`
- 第 2 世代 `calibration-94a4b79fa31bba3c.json`: `bnode048` / `0:892707.nqsv` / 同じ値
- ログインノード実測: `/usr/bin/gcc` → 11.4.0。`/usr/bin` に `gcc-9/11/12`・`g++-9/11/12` が
  同居し、`gcc-13` / `g++-13` は無い

**これは 2 ノードの観測であって `gen_S` 全ノードの現在値ではない。** PBS 要求にも
vnode / toolchain の制約は無いため、異機種ノードに当たる可能性は残る。
現在値は投入時に実測して確定する。

**version 文字列の形が 2 系統ある (2026-08-11 実測)。** `gcc` は argv0 を先頭 token に出す。

- calibration と job script は `command -v gcc` を叩くので `gcc (Ubuntu …) 11.4.0` になる
- `buildcache._tool_version` は `os.path.realpath` 後の実体を叩くので
  `x86_64-linux-gnu-gcc-11 (Ubuntu …) 11.4.0` になる

**同一 compiler でも両者は逐語一致しない。** 両者を突き合わせる検査を書くなら、
`silo_ladder_rung1.tool_version_body()` と同型の argv0 token 除去が必須である
(逐語一致にすると正規の run が恒常的に赤になる)。realpath 同士は完全一致する。

**この不整合は今まで表に出ていない。** official guard が build より手前で rc=2 を返すため、
実機の floor job (873225) はビルドへ到達せずに終わっていた。**W-1 で guard を解禁した直後に、
W-2 の初回投入がここで倒れる。** env contract には toolchain を束縛する field が無いため、
「どの compiler で床値を測ったか」は現状どの契約にも紐付かない。compiler 差は backoff 級の差を
容易に上回る (`buildcache` 自身の記述) ため、既定 compiler へ黙って倒すのは選択肢にしない。
処置は §5 の R-4 で裁定へ返す。

### 1.1 偽の赤に注意 — 単体 verify CLI は恒常的に赤

```
python3 orchestrator/campaign/s8b_holdout_freeze.py verify output/s8b-freeze/holdout_freeze.json
→ rc=1  design_source sha256 不一致: recorded=1829af7f… actual=5fbdd7ef…
```

これは**壊れているのではない**。v1 freeze が記録する `design_source` と `generator` の hash は、
T-080 移行 (2026-07-22〜23) で受領証へ移し替えられており、live の oracle gate は
`t080_freeze_migration` の adapter 経由で移行基準 commit の blob を見る。単体 CLI だけが
worktree 完全一致を要求する旧経路のまま残っている。

同様に `frozen_at_head` が記録する `2e20d441…` は現行 repo に存在しない commit であり、
受領証が `recorded_frozen_at_head` として受領済みである。**単体 CLI の赤を再開の blocker と
読んではいけない。** 生死の判定は次の 1 本で行うが、期待は checkout の段階で変わる。

```
PYTHONPATH=orchestrator python3 orchestrator/campaign/s8b_oracle_driver.py \
  gate-check --freeze <段階に応じた freeze path>
```

| 段階 | freeze path | 期待 |
|---|---|---|
| chain 無しの基準木 (main が official 床値の run_dir を持たない) | v1 `output/s8b-freeze/holdout_freeze.json` | rc=2、拒否は `floor-null` と `budget-null` の 2 件 exact |
| chain + G を持ち、承認 A / pointer X の無い木 | v1 (同上) | rc=2、拒否 4 件 exact = `holdout-freeze-verify: [holdout.unknownness_layer2] …` (receipt の live scan が official run_dir の 3 file で hit)、`holdout-freeze-verify: FreezeError: …` (v1 verifier の live scan)、`floor-null`、`budget-null`。この 2 件の走査拒否は既知の official 成果物 hit であり、artifact の破損ではない |
| A / X の後 (active v2 が発効した木) | active 世代 `output/s8b-freeze/holdout_freeze.v2.g1.json` | 同一 root・HEAD・世代の full launch validation が成功した場合に限り receipt の未知性層 2 (zero-hit 判定) は完全一致検証へ委譲される。その他の拒否条件 (manifest・spec・budget 等) は独立に評価され、gate が拒否したら次段へ進まない。v1 path を指定し続けた場合は委譲されず前段の期待のまま |

各段階の記録済み exact 集合から外れた拒否が出たら、その段へ進まず原因を調べる。prefix だけで破損と
断定せず、既知の層 2 hit と、artifact bytes・検索規約・closure 等の不一致を reason と対象 path で
区別する。段階ごとの実測値 (rc・件数・log) は worklog と一次資料が持ち、本書は判定規則だけを持つ。

---

## 2. 毎回の preflight (どの段へ入る前にも実行する)

1 コマンド 1 値で確かめ、複合 shell の判定器を作らない。

| # | コマンド | 期待 |
|---|---|---|
| P1 | `git ls-tree HEAD external/ccbench` | `160000 commit e9e477ca…` (2026-09-20 [T-2304] で D2150 項 1 の候補へ前進。値の正本は `orchestrator/campaign/s8b_approved.py` の `CCBENCH_FULL_SHA`。凍結済み floor protocol は自身の `ccbench_pin` (`511c9538…`、2026-08-12 [T-816] 手順 4 で前進した期の値) を保持し、その期の床値を歴史再開するなら旧 commit を明示 checkout する。`d706650c…` 期も同様) |
| P2 | `python3 orchestrator/tests/test_frozen_artifacts.py` | `2 passed, 0 failed` / rc=0 |
| P3 | 上記 gate-check | §1.1 の段階表と照合する (chain 無しの基準木 = rc=2 かつ拒否 2 件 exact、chain + G で A / X 前 = rc=2 かつ既知 4 件 exact、A / X 後 = active 世代 path を指定し全 gate が成立した場合だけ `allowed: true`) |
| P4 | `qstat -u <user>` | T-139 の pilot / 本走 job が走っていない |

P1〜P3 のいずれかが期待と違えば、その段へ進まず原因を先に切り分ける。

---

## 3. 再開の順序 — 何が塞いでいるか

**床値の実測は固定 official 経路で行う** ([T-2324]、方式は D926)。投入 script は
`--mode official` を固定で渡し、実投入に `--confirm-official-floor-run` を要求する。承認は
submission nonce に束ねて運び、job script が exact 一致を確かめたときだけ driver へ承認 flag を
1 個 append する。**pilot 経路は標準投入から外れた** — driver 側の pilot API は残るが、この
wrapper からは起動できない。

**[T-748] 裁定 (c) の固定 pilot 経路は、この wave までの現況記述である。** 当時の W-2 pilot 走行
(request `945229.nqsv`、12 cell 完走) は事実として残るが、`eligible_for_refreeze=false` なので
再凍結には使えない。**再凍結 → oracle → certified を開くのは official 走行である。**
なお **[T-2324] の着地は測定の認可を兼ねない** (D1641)。走行の可否は別に判断する。

### W-1. [T-088] 段階 3・4 の実装 (承認済み・着手可)

- **現状:** `s8b_floor_campaign._assert_official_permitted` は official に exact bool の明示承認を
  要求し、CLI も同じ判断を二重に返す ([T-2324])。**無条件拒否ではなくなった。**
  段階 1 は 2026-07-28 に実機で閉じている (job 873225 = rc=2。当時は無条件拒否)
- **残:** 段階 3 = 単一 admission predicate + 実行 revision 束縛 + spool bytes 照合、
  段階 4 = CLI rc 翻訳。2026-07-28 (36) で 3 項とも推奨採用済み
- **3 点の現況** ([T-748] 裁定 (c) の 2 点は維持、3 点目は [T-2324] で入れ替わった)。
  1. `s8b_floor_campaign._assert_official_permitted` は `official` に **exact bool の明示承認**を
     要求する ([T-2324]、D926)。承認が無い official は core と CLI の両方が拒否する
  2. `assemble_result` は `eligible_for_refreeze=True` を `mode == "official"` かつ fresh かつ
     非既定 seam ゼロに限定する。**維持する。したがって pilot で測った床値は再凍結に使えない**
  3. `tools/pegasus/floor_campaign.sh` は **固定 `--mode official`** に戻った ([T-2324])。
     裁定 (c) の固定 pilot は、承認束縛が実装されるまでの過渡形だった
- **未承認の実投入は成立しない。** `submit_floor.sh` は非 dry-run で承認引数が無ければ
  `qsub` より前に rc=2 で止まる。**キュー資源も submission staging も消費しない。**
  raw `qsub` で承認 env を省いた非標準経路だけは計算ノード上で倒れうる (D926 の保証範囲外)
- **成果物への影響:** 承認付き official 走行が成立すれば再凍結適格な床値が採れ、freeze v2 の
  floor/budget を埋められる。**実装の着地は測定の認可を兼ねない** (D1641) ので、走行の可否は
  別に判断する。走らせるまでは oracle gate は 2 件拒否を返し続ける

### W-2. 床値実測 (Pegasus 単独・official) — **W-1 の完了は前提ではない**

- **承認束縛が着地したので固定 official 経路で走らせる** ([T-2324]、方式は D926)。
  W-1 の段階 3・4 (単一 admission predicate + CLI rc 翻訳) は W-2 の前提ではない。
- **当時の pilot 走行は歴史として残る。** request `945229.nqsv` の 12 cell 完走は事実だが
  `eligible_for_refreeze=false` であり、再凍結・oracle・certified の証拠にはできない。
- **R-4 (B) の toolchain 束縛検査は実装済み** ([T-747]、worklog 455)。
  **pilot でも無条件に発火する** — `build_cells` が `_bind_current_toolchain` を呼ぶ経路に
  mode 分岐は無い。**拒否されたらそれは正しい fail-closed であり、緩めて通してはならない** (§5 R-4)。
- **実投入で判明した停止点 (2026-08-12)。** 投入経路の欠陥 4 件は修正済みで、
  admission・attestation・toolchain 束縛・実体化はすべて通過する。
  かつての停止点は測定そのものだった — 計算ノードに現行 kernel 用の perf が無く、
  `perf stat` の下で走る測定が 1 点も取れない (8/8 ノードで実測)。
- **この停止点はユーザー裁定で解除された (2026-08-12、第 5 束、authority: user)。**
  裁定 `perf-optional-measurement` により **perf は測定の前提ではない**。あれば使い、
  なければ無しで測る。T-920 (linux-tools 導入依頼) は閂ではなくなった。
  実装は設計判断 `perf-preflight-pilot-scoped` に従い、次の形で固定されている。
  - **検出**: 測定開始前・12 セル build 前に 1 回だけ probe する。判定は
    `available` / `unavailable` / `probe_error` の 3 値。**`probe_error` (timeout・
    予期しない OSError・signal 終了) は abort** する。`rc != 0` と perf 不在は
    `unavailable` であって異常ではない。
  - **使う perf は PATH の literal `perf` だけ**である (runner が実行するのと同一)。
    `policy.json` の `perf_candidates` は **evidence として probe 結果を receipt に残すだけで
    選択には使わない** (絶対 path を選ぶには run_cmd・toolchain binding・verifier の
    拡張が要り、F89 が未裁定のため)。**candidate を PATH へ注入する運用をしない。**
  - **分岐**: `unavailable` でも build と測定を続行する (床値は throughput だけを使い
    perf counters を消費しない)。
  - **記録**: receipt を manifest と result へ create-only で残し、`result.md` にも
    perf 条件を出す。**比較は同条件内でのみ行う。**
  - **pilot 限定**: receipt の emit と perf 無し形は `mode == "pilot"` でだけ到達できる。
    official は従来どおり perf あり形だけを期待する。**[T-2324] は承認 gate だけを変え、
    perf 受理形は 1 bit も変えていない** — 固定 official wrapper で走る官製経路は perf あり形である。
- campaign は `driver_rc=0` / `status: completed` を返しつつ床値が全 null になりうるので、
  **rc だけで成功と判定してはならない。** `floors` が実数を持つことまで確かめる。
  この確認は `floor_campaign.sh` が driver 終了後に機械強制する (欠損なら非 0 rc)。
  加えて **job 開始直後に journal を見て、最初の数 session が全滅していないかを確かめる** —
  全滅していれば残り 10 時間を捨てずに止める (`smoke_probe.sh` は perf も ccbench も
  起動しないため direct 実行の canary にはならない。2026-08-12 実測)。
- 投入手順は次の順で行う。**順序を崩さない。**
  1. official 経路と docs の**全 tracked 変更を commit する** (未 commit の変更があると
     `submit_floor.sh` の drift 検査が qsub 前に rc=2 で止める)
  2. **third-party staging root を供給する。** `submit_floor.sh` はこれを消費するが自分では
     作らない。新しい作業木では `--dry-run` が rc=0 でも実投入が
     `floor third-party source root is missing or unsafe` で qsub 前に落ちる。
     手順は `tools/pegasus/README.md` §6 (`fetch_third_party.py hydrate`) が正本
  3. `tools/pegasus/submit_floor.sh --dry-run` で submission record を確認する
  4. 同 script を `--confirm-official-floor-run` 付きで明示実行する。投入インタフェースは
     同 script が正本で、`qsub -v VAR=value <script>` 形を自分で発明しない (runbook §8)。
     **raw `qsub` は D926 の nonce 束縛の保証範囲外である**
  5. **測定の反復そのものに承認は要らない** (D1124)。**同じ cell を何度でも測ってよく**、測定ごとに
     新しい測定世代を発行して台帳へ追記する。official 走行に要るのは D926 の承認束縛だけで、
     予算承認 (結果を freeze へ昇格させる段の閂) は別物である (D1161 / D1398)。
     挙動の正本は `tools/pegasus/README.md` の該当項
- 背景 job セッションからの投入は F49 (ii) の例外で許されるが、投入直後に有効性検査 3 点
  (計算ノード側 marker の実在 / `qstat` 可視 / 会計痕跡) を必ず行う
- **走行フェーズの間は成果物を repo に置いたままにしない。** driver は
  `out_root = repo_output_root()` で repo の `output/` 配下へ書き、
  `output/env/pegasus/calibration/s8b-floor-pilot/…` は gitignore されない。
  holdout clean-scan の除外は `output/s8b-freeze/` だけなので、床値 result を repo に置いたまま
  次の official 床値 job を起動すると **その起動証明 (`clean_scan_digest` の hit 0 件要求) が止まる**
  (worklog 131-132 が同じ性質を記録している)。使い捨ての作業木で走らせ、走行ごとに退避する。
  **退避は run directory だけでは足りない** — 次を 1 つの bundle にまとめ、構成 manifest と
  各 hash を残す。run directory / content-addressed の binary store
  (`output/env/<env>/binaries/<sha>`。manifest と result はここを `store_path` で参照する) /
  submission receipt / job staging。**run directory だけを残すと参照が dangling になる。**
  `s8b_floor_evacuation` が実体として保存するのは run directory の payload だけで、残り 3 種は
  path と hash の参照として記録する。**参照を記録しても実体は復元されない**ので、元の binary
  store・submission receipt・job staging は別途保持する。
- **official result の退避と再配置の順序は [T-2386] で裁定した。順序は一方向である。**
  `s8b_holdout_freeze._validate_floor_inputs` は `_load_repo_object(root, floor_result_path, …)` で
  repo 相対に解決し、`parse_official_run_path` が official run path であることを要求する。
  したがって「走行直後に退避する」と「candidate 生成時に repo 相対で読む」は同じ artifact について
  両方成り立たせる必要がある。**clean-scan の要求は緩めない** (規律 2)。運用順序は次のとおり。
  1. official を走らせ、`floor_campaign.sh` の driver 終了後検査が終わって wrapper が終了するまで
     待つ。書込み中の run directory を退避しない。
  2. `python3 -m orchestrator.campaign.s8b_floor_evacuation evacuate --env-tag <env>` で当該 env の
     official namespace 全体を退避する。run directory と、空になった namespace directory が repo
     から消える。退避先は固定導出で、引数でも環境変数でも差し替えられない (D475 と同じ形)。
  3. 次の official 起動は従来どおり clean scan に従う。**退避が成功したことは起動証明の代用ではなく、
     痕跡を消してよかったことの証明でもない。**
  4. 当該 holdout 集合の official 走行を**打ち切ると決めてから** `restore` で namespace 全体を戻す。
     run・時刻・proto8 を選ぶ引数は無く、部分復元の口は無い。
  5. 戻した成果物を commit する。`_measurement_closure` が captured HEAD の blob 一致を要求し、
     批准側の `_verify_generation_semantics` が「世代 commit の tree に blob 実在 + worktree ==
     HEAD blob」を要求するため、commit は candidate 生成と批准の両方の必要条件である。
  6. candidate を生成する。
  7. **この commit を持つ branch では、以後 official 床値を起動できない。** 成果物が走査に hit して
     clean scan が赤になる。これは弱体化ではなく設計どおりの帰結であり、順序が一方向である理由である。
- **途中で死んだときの扱いは crash 点で分かれる。** wrapper は `--resume` を渡さず、
  reservation 再検査は余裕不足を `reservation-lost` terminal として numeric values を
  不適格にする。**「新規 job で最初から再実行する」が通るのは claim 発行前に死んだ場合だけである**
  — それ以外では admission 台帳の一回性 key が新規 job を拒否する。判定と各点の可否は §3.6 に従う。
- 完了後、記録された `cmake.path` を期待値と照合する。**cmake は version body だけが照合対象で
  realpath は束縛されていない**ため、実体同一性は gate では証明されない
  (§5 R-4 の「束縛していない量」に既記)。
- cygnus は使わない (frozen/standby)

### W-3. freeze v2 g1 候補の生成と人間承認手番 — **producer は実装済み、候補は保存 branch に生成済み**

- **現状 (2026-09-17):** `s8b_holdout_freeze.py generate-v2-candidate --floor-result <official result.json>
  --budget <budget 文書>` が v2 g1 候補の producer である ([T-750] 裁定 (a)+(a)、2026-08-11 着地)。
  official floor result と sibling manifest・journal・launch certificate、共有 admission 台帳
  (v5 attempt registry の evidence を含む)、既承認 budget を検証し、未発効の候補を create-only で書く。
  承認 authority は module 内 pinned literal `BUDGET_APPROVAL_SHA256` で、
  `output/s8b-freeze-budget-approvals/g1.json` (2026-09-05 承認) と一致している。
- **floor protocol は index authority で解決する** (D460 型)。official 走行と同じ
  `resolve_current_floor_protocol` が版付き protocol (`output/s8b-freeze/floor-protocols/…`) を選び、
  固定 `floor_protocol.json` は index の anchor として残る。旧実装の literal read は ccbench pin 前進後の
  official result を `protocol_sha256` 不一致で拒否していた。
- `--budget` には承認文書全体でなく、その `budget` と canonical 一致する budget 本体を渡す。
  本 wave は fixture 規約に合わせ `output/s8b-freeze-budget-inputs/g1.json` に置いた (末尾改行なし)。
- **path 規約は 2 段ある。** 候補 (未発効) は producer が固定 path
  `output/s8b-freeze-candidates/holdout_freeze.v2.g{N}.json` に書く (走査除外ではない)。
  世代文書は `output/s8b-freeze/holdout_freeze.v2.g{N}.json` で、批准側はその導入 commit G が
  「非 merge・親 == 候補の `frozen_at_head`・`AI-Agent` trailer 付き」であることを要求する。
  approvals/・active/ は人間 commit (`AI-Agent: none`、非 merge、X^ == A) で作り、file を作ること自体が発効。
  `output/s8b-freeze/` への直接 Write は hook が誤操作抑止で拒否する。
- **入力の順序は W-2 の一方向順序 (D2077) のとおり** — restore した official result を commit してから
  生成する。成果物を持つ checkout では以後 official 床値の起動証明 (clean scan) が赤になる。
- **候補の所在:** 保存 branch `freeze-g1-chain-t2724` (base = main、fix commit → 入力 commit →
  候補 commit)。main には載せていない (載せる = D2077 step 4 の打ち切り決定であり人間裁定)。
  一次資料 `output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/README.md`、裁定パッケージは同 `package.md`。
- **chain 導入後の注意 (2026-09-20、D2120 項 2 (a)(b) の履行):** X1' / X2 / G を main に載せた木では、official 床値の起動証明 (clean scan) は run_dir 3 file + 候補の hit 4 / 4 で赤になる (設計どおり、走査除外は広げない) ので、後続の official 床値 wave は main からでなく別 branch から起動する。B-10 job script の freeze-tree pin (`EXPECTED_FREEZE_TREES_SHA256`) は同じ版で G を含む tree の値へ更新済みで、この版の job script は G を欠く tree・file の追加・bytes の変更を測定前の digest 検査で拒否する (旧 script と旧 tree を備えた旧 checkout の組は失効しない)。
- **残る手番:** (a) 打ち切り = chain の main 取り込み、(b) 世代導入 commit G → approval A → pointer X の
  人間 commit、(c) 床の採否 (この 1 走行の床は両 holdout とも配線下限 0.03 × stock 中央値で決まった)。
  [T-750] package の残余 (P-1 pinned literal の恒久形、P-3 批准 proof chain に budget authorization field
  が無い構造) は別管理のまま。

### W-4. oracle manifest の production 配線 — **CLI は実装済み、spec 承認で止まる**

- `s8b_oracle_manifest.py build-approved --output <path>` が production の呼出し入口で、active ratified
  freeze と approved spec だけから manifest candidate を作る ([T-750] 単位 B)。実行主体は operator。
  出力先は `output/s8b-oracle-manifest-candidates/` 配下に固定される。wrapper script は新設しない。
- 現在は active freeze が無く `no-active-ratified-freeze` で拒否する。active 成立後も
  `s8b_oracle_spec.APPROVED_SPEC_SHA256 = None` のため、人間が reviewed spec を承認して定数を置くまで
  `no-approved-spec` で fail-closed する ([T-750] P-1 の手番)。
- `s8b_oracle_driver.py run-block` は `--manifest` を必須で取る。CLI の存在は oracle 実走の認可を意味しない。

### W-5. oracle 実走

- `gate-check` が `allowed: true` を返すことを確認してから `run-block` を block 単位で回す
- rc の意味: 0 = completed、1 = internal-error、2 = gate-refused / budget-refused、
  3 = protocol_violation

### 3.6 crash 後の復帰可否 — crash 点で分かれる ([T-1179])

床値 campaign が途中で死んだとき、復帰できるかは **どこで死んだか**で決まる。
`docs/archive/worklog-phase3-0816-595-596.md` の `[T-1179]` 裁定 (2) は
「crash 時の freeze / admission 再生成を必須」と定めたが、**その再生成を実行可能にする経路は
現行 HEAD に存在しない** (下記「再生成が塞がっている理由」)。したがって本節は、
今日できることとできないことを分けて書く。**架空の復帰コマンドを書いてはならない。**

#### 判定手順 (実在 artifact だけで決める)

共有 admission root を `R` とする (`s8b_holdout_admission.shared_admission_root`)。
run directory を `D` とする。次を上から順に見る。

1. `R/claims/` に当該 key の claim が 1 件も無い → **claim 発行前**
2. claim が 1 件以上あるが cell 数に足りない → **部分発行**
3. claim が cell 数だけ揃い、`D/journal.jsonl` に `session-start` / `session` が無い →
   **claim 全件・観測前**
4. `session-start` / `session` はあるが `terminal` が無い → **観測開始後**
5. `terminal` はあるが `D/result.json` が無い → **terminal 後・公開前**
6. `D/result.json` はあるが `D/result.md` が無い、または逆 → **M-finalize-pending**

#### 各点の可否

| crash 点 | 今日の可否 | 根拠 |
|---|---|---|
| 1. claim 発行前 | **fresh 再投入できる** | claim path が未作成なので排他作成が衝突しない。未完 output を隔離し clean な作業木から投入する |
| 2. 部分発行 | resume で残りを補完できる。**ただし公開はできない** | resume は既存 claim を不変に保ち残りを同じ schema で補完するが、run 全体に resume marker が立つため再凍結不適格になる |
| 3. claim 全件・観測前 | 同上 | 同上 |
| 4. 観測開始後 | 同上。**かつ再抽選バイアスの問題が立つ** | 同じ holdout を観測後に測り直す形になる。§5 の裁定待ち項目 |
| 5. terminal 後・公開前 | **admission の再発行が拒否される** | 完了/terminal 済み run は admission を再発行できない |
| 6. M-finalize-pending | **完了できない** | resume は再凍結不適格として result を再構成するため、公開前の staged bytes と一致せず停止する。この挙動は現行 main の検査が固定している |

#### 再生成が塞がっている理由

admission key は freeze の hash・holdout key・configuration・ccbench pin・env tag・観測 role の
6 要素だけで決まる。このうち実質的に動かせるのは freeze の hash だけだが、official 床値では
その hash が固定 v1 に pin されており (`t080_freeze_migration` の raw hash)、下流の
再凍結側もその固定値と一致することを要求する。
pin を外せる v2 freeze の生成器は**入力に完成済みの official 床値 result を要求する**ため、
result を出す前に死んだ campaign の復帰には使えない。

したがって **1 回目の official 床値 campaign が crash 点 2〜6 で死ぬと、その protocol と env の
組では以後 official 床値を出せない。** これは既知の袋小路であり、解消には §5 の裁定が要る。

#### 観測開始後の中断 — semantic core は実装済み、収集器は未実装 ([T-1601] [T-1602])

上表の crash 点 4 (観測開始後) について、**判定と受理の意味論だけ**が現行 main に入った。
運用上の可否は 1 行も変わっていない。両者を混ぜて読まないこと。

**入ったもの (attempt registry core と 8b profile)**

- `recovery` を core の semantic event として追加し、専用の parse / replay 分岐と
  `record_attempt_recovery` API を置いた。profile の許可表だけを増やす形は採っていない。
- 観測開始後の再走を認める理由を exact 2 値
  (`node_failure` / `scheduler_external_interruption`) の閉集合に固定した (D740)。
  `wall_timeout`、process 消失、SIGKILL の自己申告、caller の自由文字列は
  `[attempt-recovery-evidence]` で拒否する。
- 証拠は create-only の `scheduler-accounting-receipt/v1` に限る。core は schema / event /
  source / authority ID / authority policy hash の exact 一致、対象 start-event hash の一致、
  nested receipt の digest 再計算、recoverer identity が start owner と異なることを検査する。
- 同一 slot の terminal と recovery は双方向で排他とし、二重 recovery も拒否する。
  次 ordinal の start は「直前 slot の retryable terminal」か「verified recovery」の
  どちらか一方だけで認可する。
- 通常 terminal の retryable reason 集合は空のまま据え置き、recovery の 2 理由を混載しない。
- 8c 側の schema / event bytes / facade 署名 / 拒否理由 snapshot は 1 bit も変えていない。

**入っていないもの (運用可否が変わらない理由)**

- scheduler accounting を実際に読んで receipt を発行する collector が無い。
- receipt の store、facade、journal、stats consumer が未配線である。
  2026-08-25 に store と adapter の**コードは入った** ([T-1630]) が、
  production caller は作っていないので配線は未了のままである。
- したがって durable な 8b registry / receipt は現時点で 0 件であり、
  **crash 点 4 で死んだ campaign を今日この経路で復帰させることはできない。**
  上表の可否欄は変わらない。
- 収集器と配線は後続タスクへ直列化する。
- **性能出力を読む前に分類を確定させる強制も未了である。** 2026-08-25 の adapter は
  API の形で順序を守らせるが、呼び手は adapter を通さずに出力 file を直接読めるし、
  共通 core を直接 import もできる。D510 決定 4 を閉じるには信頼側の起動器が要る。

#### 権威分担と crash cut の真偽表 ([T-1603])

crash からの復帰可否を決めるとき、**どの記録が真か**が場所ごとに違う。ここを曖昧にしたまま
registry を足すと、同じ事実を 2 か所が別々に主張する。本節はその分担を固定する。

**分担の原則は 1 つ。** admission 側は「誰がその cell を測ってよいか」(実行権) の権威、
attempt registry は「その attempt に何が起きたか」(状態と終端) の権威である。
registry は claim も consumed marker も書かず、「ticket を消費した」という独立の主張を持たない。
admission 側は terminal の理由を持たない。

##### 記録の実体 (共有 admission root を `R`、run directory を `D` とする)

`R` は `s8b_holdout_admission.shared_admission_root` が返す
`<git-common-dir>/izanagi/s8b-holdout-admission-v1` である。

| 記号 | 実体 | 何の権威か | 排他の作り方 |
|---|---|---|---|
| C | `R/claims/<claim_digest>.json` | cell key の一回限りの掴み取り | `O_EXCL` |
| L | `R/ledger.jsonl` | admission の可搬 evidence (`admit` 行) | root lock 内の追記 |
| J | `D/journal.jsonl` の `session-start` / `session` | 個別 attempt の開始認可 | run directory の canonical 検査 |
| M | `R/consumed/<claim_digest>-<marker_digest>.json` | attempt ticket の一回限りの消費 | `O_EXCL` |
| A | `R/attempt-ledger.jsonl` | M の可搬 projection (M と同一 document) | root lock 内の追記 |
| Q | `R/floor-attempt-registry-receipts/` の create-only 受領証 | 観測前分類の内容 | `O_EXCL` |
| F | `R/floor-attempt-registries/<freeze_sha256>/registry.jsonl` | attempt の状態と終端 | root lock + 全体 bytes の atomic 置換 |

**A は M の projection であって独立の権威ではない。** したがって
「M があり A が無い」状態を復帰不能と扱ってはならない (下表 cut 6)。

##### 真偽表

registry の行を `F`(freeze) / `S`(start + pre-observation-seal) / `K`(classification) /
`O`(observation-start) / `T`(terminal) / `R2`(recovery) で表す。

| # | crash cut | C | L | J | M | A | Q | registry | 真を決める記録 | 次に何ができるか |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | claim 発行前 | 無 | 無 | 無 | 無 | 無 | 無 | 無 | C の不在 | fresh 再投入できる |
| 2 | claim 後・ledger 前 | 有 | 欠 | 無 | 無 | 無 | 無 | 無 | C (one-shot) | resume で L を補完できる。公開は不可 |
| 3 | claim 全件・観測前 | 有 | 有 | 無 | 無 | 無 | 無 | F | C と L | resume で残りを補完できる。公開は不可 |
| 4 | registry reserve 後・classify 前 | 有 | 有 | start | 無 | 無 | 無 | F+S | J が開始認可、F+S が状態 | classify できる。落ちたままなら復帰対象 |
| 5 | 受領証後・classification 行前 | 有 | 有 | start | 無 | 無 | 有 | F+S | Q が分類の権威、F は未投影 | **同一内容の exact retry だけ**できる。別内容の再分類は claim が拒否する |
| 6 | consumed marker 後・attempt ledger 行前 | 有 | 有 | start | 有 | 欠 | 有 | F+S+K | **M が消費の権威** (A は projection) | observe できる。A の欠落を理由に止めない |
| 7 | classify 後・observe 前 | 有 | 有 | start | 有 | 有 | 有 | F+S+K | M が実行権、F が状態 | observe できる |
| 8 | observe 後・terminal 前 | 有 | 有 | session | 有 | 有 | 有 | F+S+K+O | F+O が観測開始の権威 | 外部証拠つき復帰だけできる (D740 の閉集合 2 値) |
| 9 | terminal 後 | 有 | 有 | terminal | 有 | 有 | 有 | F+S+K+O+T | F の terminal | 同 slot は再走不可。**8b では次 ordinal も terminal 経由では開かない** (下記) |
| 10 | recovery 後 | 有 | 有 | session | 有 | 有 | 有 | F+S+K+(O)+R2 | F の recovery と外部受領証 | 次 ordinal を 1 つだけ認可する |

##### 8b で次 attempt を開けるのは検証済み recovery だけである

core は次 ordinal の start を「直前 slot の `retryable-failure` terminal」か
「検証済み recovery」のどちらか一方でだけ認可する。前者には条件が 2 つ付く。
(i) terminal の理由が genesis の `retryable_failure_reasons` 集合に属すること、
(ii) 8b は `forbid_retry_after_observation` なので観測開始済みの attempt では使えないこと。

**8b の `retryable_failure_reasons` は空集合である。** したがって 8b では条件 (i) を
満たす terminal を作れず、`retryable-failure` の terminal 自体が存在しえない。
結果として、**8b で次 ordinal を開ける経路は検証済み recovery 1 本だけ**になる。
D739 / D740 の復帰経路は「あれば便利な追加」ではなく、8b の唯一の再走経路である。

##### この表が今日まだ閉じていない 2 か所 (正直な現在地)

- **cut 6 の A 欠落を自動で埋める経路が床値には無い。** `consume_attempt_ticket`
  (`s8b_holdout_admission.py`) は root lock 内で M を `O_EXCL` 作成してから A へ追記する。
  この間で死ぬと A だけが欠ける。n-pilot 経路には `_recover_n_pilot_attempt_ledger_locked`
  があるが、床値経路にはこれに相当する再構築が無い。**本表は adapter 側が A を要求しないことで
  行き止まりを避けるが、A の欠落そのものは残る。**
- **cut 10 の「次 ordinal」を admission 側が認可できない。** `consume_attempt_ticket` は
  retry の trigger を journal 内の失敗した planned session に限定しており、registry の
  recovery event を認可根拠にできない。**verified recovery を作れても次の ticket を
  消費できない。** これは D496 の禁じる行き止まりであり、別タスクで閉じる。

**この 2 か所を上の「recovery 1 本だけ」と併せて読むと、現在地はこうなる。** 8b で
落ちた attempt を測り直す経路は検証済み recovery しか無く、その recovery を作れても
admission が次の ticket を渡さない。つまり **D739 の復帰機構は admission 層で今日まだ
発火しない。** registry 側の意味論と永続化が揃っても、この 1 点が閉じるまで crash 点 8 の
運用上の可否は変わらない。

---

## 4. 順序の争点 — [T-657] 世代交代との衝突 (**裁定済み**)

> **決着 (2026-08-10 [T-748] 裁定、2026-08-12 裁定 (c) で投入経路まで確定)。**
> **W-2 は第 1 世代のうちに走らせる。** 恒久機構 ([T-657] の世代交代) が
> 先に発効した場合の作り直しリスクは受容する。以下の争点記述は決着の背景として残す。
> **2026-09-07 更新: 投入経路は [T-2324] で固定 official + 明示承認へ入れ替わった。**
> 裁定 (c) の「固定 pilot 経路」は承認束縛が実装されるまでの過渡形だった。

現行 floor protocol は pegasus **第 1 世代**の契約 hash を焼き込んでおり、いま有効な env 契約も
第 1 世代なので整合している。しかし registry には**未発効の第 2 世代**が既に登録済みである。

`docs/calibration-freeze-authority-bundle-design.md` §2 が示すとおり、環境の世代交代は
凍結の世代交代なしには完了しない (式 1)。したがって:

- **[T-657] の世代交代が先に発効すると**、現行 floor protocol は current と食い違い、
  §2 の live 照合 (P3 相当の preflight) が赤になる。床値実測は新世代の protocol を作り直してから
  でないと走らない
- **floor を作り直すと**、selector の予測封印が結び付いている protocol と食い違い、campaign launch が
  拒否される (式 3)。これは事前登録性を守る正しい挙動であって、迂回してはならない

**この択一は 8b 側では決められないため裁定へ返し、[T-748] で「第 1 世代のうちに走らせる」と
決着した** (2026-08-10)。[T-657] 側の「floor protocol 復元のユーザー確認手番」は残置のままである。

---

## 5. 裁定へ返す項目

**裁定の状態 (2026-08-11 時点)。** 検分 wave が返した 4 件のその後は次のとおり。

| 項 | 状態 |
|---|---|
| R-1 (順序の択一) | **決着。** [T-748] で第 1 世代のうちに実測する方針を維持 |
| R-2 (verify CLI の罠) | **決着 = (a)。** [T-749] として実装済み (worklog 402) |
| R-3 (W-3 + W-4 の分割) | **裁定済み・実装済み。** [T-750] は producer identity・budget authority とも (a) で裁定し、2026-08-11 に producer と manifest CLI を実装した (worklog 405 / 417)。2026-09-17 に official result から g1 候補を保存 branch へ生成した (W-3)。残るのは打ち切り・候補採用・A/X の人間手番と reviewed spec の承認。[T-750] package の P-1 / P-3 の残余は別管理 |
| R-4 (toolchain 前提) | **決着 = (B) ([T-747])、実装済み (2026-08-11、[T-783])。** 束縛検査は pilot / official を問わず build 前に発火する。残る穴は下記「束縛していない量」 |
| R-5 (crash 復帰の再生成) | **優先順位は決着 (D510 決定4)、reuse 形状も決着 (D672)。共通 core と 8c facade は実装済み ([T-1505] 2026-08-24)。残り 3 点は未裁定。** 詳細は下記「R-5 の技術確認」と「R-5 の実装状況」 |

以下は検分 wave 時点の記述である。本 wave は本番コードを編集していない。
修理・設計択一は実装せず、次を裁定へ返す。

- **R-1 (順序の択一、上記 §4):** 8b 床値実測を pegasus 第 1 世代のうちに走らせるか、
  [T-657] の世代交代を先に通すか
- **R-2 (罠の解消):** `s8b_holdout_freeze.py verify` 単体 CLI が T-080 受領証を参照せず恒常的に
  赤を返す。(a) CLI を受領証参照へ寄せる / (b) supersede を明記して手順から外す / (c) 現状維持
- **R-3 (欠けている producer):** W-3 (freeze v2 生成側) と W-4 (oracle manifest 配線) を
  1 wave にまとめるか分けるか
- **R-5 (crash 復帰の再生成、§3.6、[T-1179] 2026-08-17 追加):** 裁定 (2) は
  「crash 時の freeze / admission 再生成を必須」と定めたが、それを実行可能にする手段が無い。
  択一は 3 つで、いずれも既存の不変条件のどれかに触るため親は裁定しない。
  (a) 復帰用 generation で admission key を salt する。観測後の再抽選を防ぐため
  「session-start 0 件・consumed marker 0 件・attempt row 0 件」に限定する。
  この制約下でも、形式的には今日拒否される run を受理するので受理集合は広がる。
  (b) 新しい未知 holdout freeze を引き直す。本来の意味の「freeze 再生成」だが、
  固定 v1 pin から trust root を外す必要がある。
  (c) 現状維持。crash した official campaign はその protocol / env で terminal と扱う。
  裁定 (2) の「再生成を必須」は満たせないので、裁定 (2) 自体の再裁定になる
  **(2026-08-18/2026-08-22 更新: 上記3択の優先順位争いは決着した。下記「R-5 の技術確認」を正とする。)**
- **R-4 (toolchain 前提、§1.2):** Pegasus に `g++-13` が無く床値 driver は固定要求する。
  (a) env contract へ toolchain を束縛する field を足し、Pegasus 世代は system compiler を
  実体・版数つきで焼き込む / (b) Pegasus に `gcc-13`/`g++-13` を用意できるか先に調べる /
  (c) driver の固定要求を env 依存の解決へ変える。**いずれも計測条件を変えるため、
  既存 `linux-baremetal` の値との混用可否も同時に決める必要がある**

### R-4 の決着 (2026-08-11 実装済み)

床値 build の compiler 解決を site 依存へ寄せ、**同じ land で** registered calibration の
`acquisition_receipt` を derived toolchain authority とする束縛検査を build 前に置いた。
env contract には field を足していないので `contract_sha256` は不変であり、
発効記録・floor protocol・selector 予測封印の 3 pin は生きている。

**混用不可の機械的な固定** — `contract.calibration_ref` の calibration に
`acquisition_receipt` が無い契約では、**receipt 不在で fail-closed に拒否**する。
`linux-baremetal` の calibration は legacy でこの field を持たないため、
**linux-baremetal の較正で床値 build を行う経路は build 前に止まる**。
`output/s8b-freeze/floor_protocol.json` の `env_tag` は `pegasus` であり、
linux-baremetal を指す凍結 protocol は存在しないので production 影響は無い。

**束縛する量** (calibration receipt が authority)。

- `acquisition_receipt.toolchain.compiler_path` = build argv の `-DCMAKE_C_COMPILER` = 実測 cc realpath
- build argv の `-DCMAKE_CXX_COMPILER` = 実測 cxx realpath
- `acquisition_receipt.toolchain.compiler_version` の本体 = 実測 cc version の本体 (**全文比較**)
- `acquisition_receipt.toolchain.cmake_version` の本体 = 実測 cmake version の本体 (**全文比較**)
- 実測 cxx version の本体 = 実測 cc version の本体 (live 側の内部整合)

「本体」は先頭 token (起動名) を除いた残り全部である。同一 compiler でも `gcc` と
`x86_64-linux-gnu-gcc-11` で先頭 token が変わるため、逐語一致にすると恒真な赤になる。

**束縛していない量 (既知の穴。認可の根拠に使ってはならない)。**

- `cxx_version` — receipt に存在しない。live 側の内部整合で部分的にしか塞がっていない
- `cmake_realpath` — receipt に存在しない。version だけを束縛している
- `module_list` — receipt には存在する (`intelpython/2022.3.1`) が、実行時の module 環境を
  観測する経路が無いため**束縛していない**
- 実行ファイルの bytes hash — receipt に存在しない。同一 path・同一 version 表示で
  実体が差し替わった場合は検出できない

### R-5 の技術確認 (2026-08-22 更新。優先順位は決着、実装形状は未裁定、[T-1484])

**優先順位の決着。** D496 決定 3 (「比べる構成ごと測り直す」「設計上の終端は認めない」) と
§9 項 8 (択 (a)、実走後の途中再開は拒否) のどちらが優先するかは、D510 決定4
(2026-08-18、`docs/decisions.md`) が「8b §9項8 の再走全拒否より D496 決定 3 を優先する」と
名指しで既に決着させている。同日付の `docs/phase3-8b-descriptor-design.md` §10.5
(「実走後の途中再開 (§9項8を上書きする)」) が、対応する設計 (freeze-wide の事前割当
attempt registry、消費範囲は落ちた構成の同じ反復に限定) を既に持つ。**§10.5 を本節の
設計正本とする。** 実走マーカー (freeze byte sha256 の排他作成) と novelty search
(`s8b_holdout_freeze.py` の repository 既知性検査) はどちらも維持したまま、その手前に
事前割当 registry 経由の限定的な再走許可を挟む設計であり、両機構を緩めない。

**旧 3 択の扱い。** (a) (復帰用 generation で admission key を salt) は §10.5 とは別設計
(観測ゼロ限定の identity workaround) であり、§10.5 の狭い先行版として履歴に残すが現行
推奨には含めない。(b) (未知 holdout freeze の引き直し) は固定 v1 pin の trust root を
外す、射程のより広い別設計であり、不採用ではないが本節の推奨には含めない。(c) (terminal
と扱う、現行の実装挙動) は D496 決定 3・D510 決定4 が明示的に否定した形であり不採用。

**実装許可と正式測定不許可を分ける。** §10.5 の実装 (8b 側の attempt registry 構築)
自体は §10.6 (epoch 境界) に妨げられない。しかし正式測定の認可は、8c 側の判定器・証拠
契約・attempt registry・結果 judge が発効するまで閉じたままである
(`docs/decisions.md` D649: `s8c_result_judge.judge()` に production caller が存在しない
ため、この gate は当面閉じたまま)。**8b 側の実装が完了しても、この gate が開くまで正式
測定は認可しない。** gate 発効前の run は legacy・exploratory として扱い、後から formal
へ昇格・再解釈しない。

**実装着手前に閉じるべき4点 ([T-1484] 段2/段3 で新たに確認、未解決)。**

1. **reuse 形状。** `orchestrator/campaign/trial_registry.py` の公開契約 (schema
   version・path・`ARMS`/`HOLDOUTS`・`TrialManifest`) は 8c ドメインへ固定されており、
   非互換な変更での 8b 転用はしない。ただし attempt 状態機械の本体
   (`:1818-3555`、genesis/reserve/classify/observe/terminal/accept) の大半はドメイン
   非依存で、8c 固有部分は acceptance (`:3432-3555`) に集中する。8b 専用の新規複製と、
   共通 core 抽出 + 8c 互換 facade + 8b adapter のどちらを採るかは、実際の抽出コスト
   (8c consumer への影響範囲) を測っていないため未裁定。**次のユーザー裁定へ返す。**
2. **既存 admission 機構との束縛。** 8b は既に `s8b_holdout_admission.py` の共有
   root・claim・ledger・consume-ticket 機構を持つ。新設 registry がこれと束縛されない
   第二の「master」になると、それ自体が新しい正しさの穴になる。どちらを master とし、
   どう同一 lock/transaction で束縛するかを実装 wave の段1 brief で明記すること。
3. **失敗分類を出力の前に確定させる設計。** 現行 8b (`s8b_floor_campaign.py`) は理由の
   多くを `measure_fn` 実行後に決定しており、D510 決定4 の「出力を読む前に分類」要件を
   満たさない。`trial_registry.py` 自身も OS レベルの read-first を証明しないと
   docstring で明記しており (8c 側も未解決のまま)、trusted launcher の設計と外部証拠
   由来の閉じた失敗理由集合を別途用意する必要がある。
4. **crash 点4 (観測開始後) の再抽選バイアス。** §10.5 は「落ちた構成の同じ反復の次slot
   だけ消費」と定めるが、観測開始後に crash した場合にどの attempt を主値とするか、
   部分的に露出した WAL をどう扱うか、§10.4 の測定近接性ラベルとどう連動させるかは
   未規定。novelty search (repo 既知性) とは別の、統計的独立性の論点である。

一次資料・段2 plan・段3 敵対2レンズの逐語・段4 裁定は
`output/insights/2026-08-22_t1484-floor-restart-registry/README.md` を参照。

### R-5 の実装状況 (2026-08-24 更新、[T-1505])

**上記4点のうち 1 (reuse 形状) は D672 で決着し、実装した。残り 3 点は決着していない。**

**実装したもの。** attempt 状態機械のドメイン非依存 core を
`orchestrator/campaign/attempt_registry_core.py` へ抽出し、`trial_registry.py` を
実 `def` による 8c 互換 facade にした。8b の domain profile は
`orchestrator/campaign/s8b_attempt_profile.py` にデータとして置き、core を 8b profile で
駆動する状態機械テストで生死を確認した。**8b の production からは import も call もしていない。**
8c の受理集合・拒否理由・凍結成果物の bytes は変えていない (C01–C12 の
`(id, status, reason_code)` snapshot 同値と canonical bytes の差分テストで機械確認)。

**実装しなかったもの。** 8b の production 配線、trusted launcher による出力前分類、
crash 点4 の再抽選規則。いずれもユーザー裁定を要することが実装 wave の段2/段3/段6 で確定した。
返した項目と根拠は
`output/insights/2026-08-24_t1505-attempt-registry-core/verbatim/ruling-package.md`。

**新たに判明した最重要の事実。** terminal を registry へ書けるのは分類を実行した
process・thread だけであり、次の slot を開始できるのは前の slot に terminal がある場合だけである。
したがって **PBS の wall timeout・node 障害・SIGKILL で計測 process ごと死んだ attempt を
別 process が閉じる経路が原理的に存在しない**。§10.5 にもこの引き取り経路の規定が無い。
救出経路を成立させるには、外部証拠を根拠に放棄された attempt を terminal 化する
「引き取り」の設計が要る (上記 4 点の外側にあった穴)。

**併せて判明したこと。** 欠測反復は `s8b_floor_stats.py` の cell 有効性判定
(`n_valid == n_sessions`) を満たさなくするため、**その cell を丸ごと失格にする**。
「観測開始後に落ちた反復を判定不能にする」という保守的な扱いは、D496 決定3 の
「行き止まりを作らない」に正面から抵触する。上記 4 の再抽選バイアスは、
統計的独立性だけでなく estimand の選択そのものの問題である。

実測値・変異台帳・段3/段6 の逐語は
`output/insights/2026-08-24_t1505-attempt-registry-core/README.md` を参照。

### R-4 の束縛していない量について

これらを authority に加えるには calibration の再発行が要る。
**後続の certified 判定で、上記 4 つを「検査済み」と見なしてはならない。**

**初回の実 run で gate が拒否する可能性がある。** 計算ノード側の `gcc` / `g++` の realpath と
version は未確認である (login node と bnode005 の probe で確認できているのは
`gcc-13` / `g++-13` の不在と cmake 3.25.0 だけである)。拒否が出た場合、それは
**正しい fail-closed であって bug ではない** — 実 toolchain が登録済み較正と異なるという
意味なので、較正の再取得か toolchain の是正で解く。**gate を緩めて通してはならない。**

---

## 6. この手順書の更新契約

各段の完了時に、実測値 (rc・job ID・件数) を伴って §1 の表と §3 の該当段を更新する。
値の無い前方参照と placeholder は書かない。状態の正本は worklog 末尾であり、
本書は手順と判定条件だけを持つ。
