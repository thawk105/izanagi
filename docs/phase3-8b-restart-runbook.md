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
拒否を返す。再開を塞いでいるのは腐りではなく、**未実装の段** (§3) と、**未解決の toolchain 前提**
(§3 の W-2) である。

### 1.2 新たに判明した前提の欠落 — Pegasus に固定要求の compiler が無い

床値 driver は CCBench のビルドで `cc="gcc-13"`, `cxx="g++-13"` を**固定で渡す**
(`s8b_floor_campaign` の build 呼び出し)。`buildcache` はこれを `shutil.which` で解決し、
PATH に無ければ `toolchain cxx が PATH に存在しない: 'g++-13' (fails-closed)` で倒れる。

一方 Pegasus には `g++-13` がログインノードにも計算ノードにも無い (計算ノードは `g++-12`、
ログインノードは 11.4.0 を実測)。Pegasus 用の較正証明 (`certify_calibration.sh`) と floor job
script の依存ビルド段は、いずれも `command -v gcc` / `command -v g++` で**system の既定 compiler**
を解決して記録する設計であり、driver 側の固定要求とかみ合っていない。

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
| P1 | `git ls-tree HEAD external/ccbench` | `160000 commit d706650c…` |
| P2 | `python3 orchestrator/tests/test_frozen_artifacts.py` | `2 passed, 0 failed` / rc=0 |
| P3 | 上記 gate-check | rc=2 かつ拒否 2 件 exact |
| P4 | `qstat -u <user>` | T-139 の pilot / 本走 job が走っていない |

P1〜P3 のいずれかが期待と違えば、その段へ進まず原因を先に切り分ける。

---

## 3. 再開の順序 — 何が塞いでいるか

床値実測を塞いでいるのは official mode の guard である。実測 → 再凍結 → oracle は、
**次の 3 つの未実装段を順に埋めない限り開かない。**

### W-1. [T-088] 段階 3・4 の実装 (承認済み・着手可)

- **現状:** `s8b_floor_campaign._assert_official_permitted` が official を無条件で拒否し、CLI も
  同じ判断を二重に返す。段階 1 は 2026-07-28 に実機で閉じている (job 873225 = rc=2)
- **残:** 段階 3 = 単一 admission predicate + 実行 revision 束縛 + spool bytes 照合、
  段階 4 = CLI rc 翻訳。2026-07-28 (36) で 3 項とも推奨採用済み
- **これが無いと:** `tools/pegasus/floor_campaign.sh` は `--mode official` を渡すため、
  投入しても計算ノードで rc=2 に倒れる。**投入する意味が無い**
- **成果物への影響:** 床値が採れないので freeze v2 の floor/budget は null のままとなり、
  oracle gate は永久に 2 件拒否を返し続ける (certified 選択の結果が 1 件も出ない)

### W-2. 床値実測 (Pegasus 単独) — **toolchain の裁定 (R-4) が先に要る**

- §1.2 のとおり、driver が固定要求する `g++-13` は Pegasus に無い。**R-4 の裁定なしに投入しても
  ビルド段で fail-closed に倒れる。** W-1 と W-2 の間に処置を挟む
- W-1・R-4 完了後に `tools/pegasus/submit_floor.sh --dry-run` で submission record を確認し、
  明示実行する。投入インタフェースは同 script が正本で、`qsub -v VAR=value <script>` 形を
  自分で発明しない (runbook §8)
- 背景 job セッションからの投入は F49 (ii) の例外で許されるが、投入直後に有効性検査 3 点
  (計算ノード側 marker の実在 / `qstat` 可視 / 会計痕跡) を必ず行う
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

## 4. 順序の争点 — [T-657] 世代交代との衝突 (裁定待ち)

現行 floor protocol は pegasus **第 1 世代**の契約 hash を焼き込んでおり、いま有効な env 契約も
第 1 世代なので整合している。しかし registry には**未発効の第 2 世代**が既に登録済みである。

`docs/calibration-freeze-authority-bundle-design.md` §2 が示すとおり、環境の世代交代は
凍結の世代交代なしには完了しない (式 1)。したがって:

- **[T-657] の世代交代が先に発効すると**、現行 floor protocol は current と食い違い、
  §2 の live 照合 (P3 相当の preflight) が赤になる。床値実測は新世代の protocol を作り直してから
  でないと走らない
- **floor を作り直すと**、selector の予測封印が結び付いている protocol と食い違い、campaign launch が
  拒否される (式 3)。これは事前登録性を守る正しい挙動であって、迂回してはならない

**したがって W-2 (床値実測) を第 1 世代のうちに走らせるか、第 2 世代へ交代してから
protocol と封印を作り直すかは、8b 側では決められない順序の択一である。** [T-657] 側にも
「floor protocol 復元のユーザー確認手番」が残置されている。裁定は §5 のパッケージで返す。

---

## 5. 裁定へ返す項目

本 wave は本番コードを編集していない。修理・設計択一は実装せず、次を裁定へ返す。

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
