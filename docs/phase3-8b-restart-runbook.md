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
| floor campaign の official 拒否 | 設計どおり | core と CLI の二重拒否が生きている |

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
読んではいけない。** 生死の判定は次の 1 本で行う。

```
PYTHONPATH=orchestrator python3 orchestrator/campaign/s8b_oracle_driver.py \
  gate-check --freeze output/s8b-freeze/holdout_freeze.json
→ rc=2、refusals が floor-null と budget-null の 2 件だけであること
```

`holdout-freeze-verify:` で始まる拒否が混ざったら、そのときは本物の破損である。

---

## 2. 毎回の preflight (どの段へ入る前にも実行する)

1 コマンド 1 値で確かめ、複合 shell の判定器を作らない。

| # | コマンド | 期待 |
|---|---|---|
| P1 | `git ls-tree HEAD external/ccbench` | `160000 commit 511c9538…` (2026-08-12 [T-816] 手順 4 で前進。`d706650c…` 期の床値を歴史再開するなら、その旧 commit を明示 checkout する) |
| P2 | `python3 orchestrator/tests/test_frozen_artifacts.py` | `2 passed, 0 failed` / rc=0 |
| P3 | 上記 gate-check | rc=2 かつ拒否 2 件 exact |
| P4 | `qstat -u <user>` | T-139 の pilot / 本走 job が走っていない |

P1〜P3 のいずれかが期待と違えば、その段へ進まず原因を先に切り分ける。

---

## 3. 再開の順序 — 何が塞いでいるか

**床値の実測は [T-748] 裁定 (c) の固定 pilot 経路で先行する。** 投入 script は
`--mode pilot` を固定で渡すようになり、pilot 経路の欠落 (旧 blocker 3) は解消した。
ただし pilot の成果物は `eligible_for_refreeze=false` なので、
**再凍結 → oracle → certified は official 解禁まで閉じたままである。**
official mode の guard は変更していない (受理集合は空のまま)。

### W-1. [T-088] 段階 3・4 の実装 (承認済み・着手可)

- **現状:** `s8b_floor_campaign._assert_official_permitted` が official を無条件で拒否し、CLI も
  同じ判断を二重に返す。段階 1 は 2026-07-28 に実機で閉じている (job 873225 = rc=2)
- **残:** 段階 3 = 単一 admission predicate + 実行 revision 束縛 + spool bytes 照合、
  段階 4 = CLI rc 翻訳。2026-07-28 (36) で 3 項とも推奨採用済み
- **塞いでいた 3 点のうち 2 点は「維持する側」だと [T-748] 裁定 (c) で確定した
  (2026-08-12)。** 現況は次のとおり。
  1. `s8b_floor_campaign._assert_official_permitted` (`:209-219`) が `official` を無条件拒否する。
     **維持する** (official は空集合のまま)
  2. `assemble_result` (`:2572-2575`) は `eligible_for_refreeze=True` を `mode == "official"` に
     限定する。**維持する。したがって pilot で測った床値は再凍結に使えない** — 測定値としてのみ使う
  3. `tools/pegasus/floor_campaign.sh` が `--mode official` を固定で渡していた点は
     **解消済み**。裁定 (c) により `--mode pilot` 固定へ変更した
- **「投入できない」ではなく「完遂できない」である。** `submit_floor.sh` に mode の分岐は無く、
  `--dry-run` を付けなければ `qsub` は実行され scheduler は job を受理する。
  倒れるのは計算ノード上であり、**キュー資源は消費されうる。**
  完遂できないのは再凍結適格な artifact である
- **成果物への影響:** **再凍結適格な**床値が採れないので freeze v2 の floor/budget は null のまま
  となり、oracle gate は 2 件拒否を返し続ける (certified 選択の結果が 1 件も出ない)。
  **測定値としての床値は W-2 の pilot 経路で採れる** — 再凍結へ渡せないだけである

### W-2. 床値実測 (Pegasus 単独・pilot) — **W-1 の完了は前提ではない**

- **[T-748] 裁定 (c) (2026-08-12、authority: user) が順序を変えた。** 固定 pilot 経路で
  W-2 を先行させる。W-1 (official 解禁) は W-2 の前提ではない。
  **ただし pilot 成果物は再凍結へ渡せず、official 解禁 → 再凍結 → oracle の順序は閉じたまま**である。
- **R-4 (B) の toolchain 束縛検査は実装済み** ([T-747]、worklog 455)。
  **pilot でも無条件に発火する** — `build_cells` が `_bind_current_toolchain` を呼ぶ経路に
  mode 分岐は無い。**拒否されたらそれは正しい fail-closed であり、緩めて通してはならない** (§5 R-4)。
- **実投入で判明した停止点 (2026-08-12)。** 投入経路の欠陥 4 件は修正済みで、
  admission・attestation・toolchain 束縛・実体化はすべて通過する。
  **残る停止点は測定そのもの** — 計算ノードに現行 kernel 用の perf が無く、
  `perf stat` の下で走る測定が 1 点も取れない (8/8 ノードで実測)。
  **これは環境手番であり、perf を外す回避は採らない。**
  campaign は `driver_rc=0` / `status: completed` を返しつつ床値が全 null になるので、
  **rc だけで成功と判定してはならない。** `floors` が実数を持つことまで確かめる。
- 投入手順は次の順で行う。**順序を崩さない。**
  1. pilot 経路と docs の**全 tracked 変更を commit する** (未 commit の変更があると
     `submit_floor.sh` の drift 検査が qsub 前に rc=2 で止める)
  2. `tools/pegasus/submit_floor.sh --dry-run` で submission record を確認する
  3. 同 script を明示実行する。投入インタフェースは同 script が正本で、
     `qsub -v VAR=value <script>` 形を自分で発明しない (runbook §8)
- 背景 job セッションからの投入は F49 (ii) の例外で許されるが、投入直後に有効性検査 3 点
  (計算ノード側 marker の実在 / `qstat` 可視 / 会計痕跡) を必ず行う
- **成果物を repo へ commit しない。** driver は `out_root = repo_output_root()` で repo の
  `output/` 配下へ書き、`output/env/pegasus/calibration/s8b-floor-pilot/…` は gitignore されない。
  holdout clean-scan の除外は `output/s8b-freeze/` だけなので、pilot result を repo に置くと
  **将来の official 床値 job の起動証明 (`clean_scan_digest` の hit 0 件要求) が止まる**
  (worklog 131-132 が同じ性質を記録している)。使い捨ての作業木で走らせ、repo 外へ退避する。
  **退避は run directory だけでは足りない** — 次を 1 つの bundle にまとめ、構成 manifest と
  各 hash を残す。run directory / content-addressed の binary store
  (`output/env/<env>/binaries/<sha>`。manifest と result はここを `store_path` で参照する) /
  submission receipt / job staging。**run directory だけを残すと参照が dangling になる。**
- **途中で死んだら救出しない。** wrapper は `--resume` を渡さず、reservation 再検査は余裕不足を
  `reservation-lost` terminal として numeric values を不適格にする。**新規 job で最初から再実行する。**
- 完了後、記録された `cmake.path` を期待値と照合する。**cmake は version body だけが照合対象で
  realpath は束縛されていない**ため、実体同一性は gate では証明されない
  (§5 R-4 の「束縛していない量」に既記)。
- cygnus は使わない (frozen/standby)

### W-3. freeze v2 の生成側 — **producer が存在しない**

- **現状:** `s8b_ratified_freeze.py` は**検証側だけ**である。承認束縛・世代連鎖・launch 検証の
  機構は揃っているが、`generation_number` を持つ v2 document を**書く経路が repo に無い**
  (`generation_number` の非テスト出現は同 module の検証コードのみ)
- `s8b_holdout_freeze.py generate` は v1 用で、floor/budget を埋める引数を持たない
- **path 規約は決まっている:** `output/s8b-freeze/holdout_freeze.v2.g{N}.json`。
  同一 path への上書きは凍結の履歴不変条件 (式 2) を破るため、**別 path への一度きりの追加**で行う。
  承認・世代 pointer の namespace (`approvals/`, `active/`) は未作成であり、これは設計どおり
  (ファイルを作ること自体が「発効」)
- **必要な wave:** v2 候補 document の producer + 人間承認の受領証発行

### W-4. oracle manifest の production 配線

- `s8b_oracle_manifest.build_manifest` は実装済みだが、**呼び出しているのはテストだけ**である。
  CLI も production caller も無い
- `s8b_oracle_driver.py run-block` は `--manifest` を必須で取るため、manifest を作る経路が
  無いままでは oracle 実走に入れない

### W-5. oracle 実走

- `gate-check` が `allowed: true` を返すことを確認してから `run-block` を block 単位で回す
- rc の意味: 0 = completed、1 = internal-error、2 = gate-refused / budget-refused、
  3 = protocol_violation

---

## 4. 順序の争点 — [T-657] 世代交代との衝突 (**裁定済み**)

> **決着 (2026-08-10 [T-748] 裁定、2026-08-12 裁定 (c) で投入経路まで確定)。**
> **W-2 は第 1 世代のうちに固定 pilot 経路で走らせる。** 恒久機構 ([T-657] の世代交代) が
> 先に発効した場合の作り直しリスクは受容する。以下の争点記述は決着の背景として残す。

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
| R-3 (W-3 + W-4 の分割) | **未裁定。** [T-750] として再裁定待ち。統合 wave の段 3 が producer identity と budget authority の 2 点を新たに出した |
| R-4 (toolchain 前提) | **決着 = (B) ([T-747])、実装済み (2026-08-11、[T-783])。** 束縛検査は pilot / official を問わず build 前に発火する。残る穴は下記「束縛していない量」 |

以下は検分 wave 時点の記述である。本 wave は本番コードを編集していない。
修理・設計択一は実装せず、次を裁定へ返す。

- **R-1 (順序の択一、上記 §4):** 8b 床値実測を pegasus 第 1 世代のうちに走らせるか、
  [T-657] の世代交代を先に通すか
- **R-2 (罠の解消):** `s8b_holdout_freeze.py verify` 単体 CLI が T-080 受領証を参照せず恒常的に
  赤を返す。(a) CLI を受領証参照へ寄せる / (b) supersede を明記して手順から外す / (c) 現状維持
- **R-3 (欠けている producer):** W-3 (freeze v2 生成側) と W-4 (oracle manifest 配線) を
  1 wave にまとめるか分けるか
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
