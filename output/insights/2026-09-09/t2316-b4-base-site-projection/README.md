# [T-2316] base の B4 launcher へ site 射影を入れる — 一次資料

wave: `dev-wave-t2316-b4-base-site` / branch `worktree-dev-wave-t2316-b4-base-site`
基点 main: `cbcdb6c91bd2eced76bd6a82650204c357c1b299`
実装 commit: `db95ffb3bd0b585a702ecbd9523a5aba790652f4` (launcher + test)
fix commit: `fe1724fe9875176bee33fe06d10bb49b61342da0` (test のみ)
main 取り込み: `9063b577198880f6c57fa5812febb927683ec078` (`2a68ac36f` を取り込み)

---

## 1. 欠陥と機序 (実測で確定)

`orchestrator/campaign/p3_b4_launcher.py` の `_driver_configs` は `driver_kind == "trigger"` の
ときだけ site 射影していた。base の driver (`p3_s4_loop.main`) は `default_cfg` の直後に必ず
`_campaign_cfg_for_site` を掛ける。したがって `PEGASUS_COMPUTE` では

- launcher が context へ束縛する campaign ID (未射影) と
- driver が `require_b4_production_context` へ渡す `expected_campaign_id` (射影済み)

が食い違い、最初の授権境界 (`p3_s4_loop.py` の `boundary="base drive_iteration"`) で
`B4LauncherAuthorizationError` になって正式 B4 経路が build へ到達しない。
launcher が sidecar を書く campaign dir も driver が見る dir と分裂する。

`OTHER` では `_campaign_cfg_for_site` が `measurement_env` を足さないので ID が変わらず、
現に動いている経路の回帰ではない。

## 2. 親が実測した site 別の挙動

`site_policy.socket` を差し替えて `p3_s4_loop` の helper 3 点を直接呼んだ結果
(逐語は `verbatim/parent-measurements.md`)。

| hostname | 解決 site | `_admit_env_contract` | campaign ID |
|---|---|---|---|
| `test-host` | `OTHER` | `linux-baremetal` | 不変 (`4e54b9ea` / `7a8e044f`)、`measurement_env` なし |
| `bnode116` | `PEGASUS_COMPUTE` | `pegasus` | 変化 (`c510996c` / `f33bb5d8`)、`measurement_env='pegasus'` |
| `pegasus02` | `PEGASUS_LOGIN` | `ExecutionGuardError` | — |
| `pegasus-mystery` / 解決不能 | `PEGASUS_SUSPECT` | `ExecutionGuardError` | — |

射影は冪等 (二重適用で ID 不変)。`classify_site` は 4 値を返す — 親 brief が当初これを
2 値と読み違えていたのを段 3 が指摘し、訂正した。

この wave が走ったホストは `pegasus02` = `PEGASUS_LOGIN` である。pytest 下では
`orchestrator/tests/conftest.py` の autouse fixture が `socket` と `_has_nqsv` の両方を
中立化するため site は `OTHER` に解決される。

## 3. 変更

`_driver_configs` の射影分岐を `if base / elif trigger` にし、base は `p3_s4_loop` の
`_current_site` → `_admit_env_contract` → `_campaign_cfg_for_site` を trigger と同じ順で呼ぶ。
`sort` はどちらの分岐も通らない ([T-2318] の scope)。実装差分は 10 行。

授権境界の比較は 1 bit も緩めていない。射影を足して一致するようにしたのであって、
比較を弱めたのではない。

**受理集合の変化** (段 6 レビュー B が表で確認、`verbatim/s6-rb.md`):
base の `PEGASUS_COMPUTE` が拒否→受理へ、`PEGASUS_LOGIN` / `PEGASUS_SUSPECT` は
拒否位置が driver から launcher へ前倒しされる。`OTHER`・`sort`・`trigger` は不変。

## 4. 段 3 が実装前に潰したもの

段 2 プランの test 設計は 2 レンズが独立に否定した。

- 負例が `_driver_configs` を通らず、修正の有無に感応しない。しかも既存
  `test_production_validator_requires_exact_campaign_and_arm` と重複していた (レンズ A)。
- そもそもその負例に要る「未射影の production context」は、`_production_launch_context`
  helper が実 launcher を呼んでから ID を assert する構造のため作れない (レンズ B)。

このため段 4 で test を N1〜N5 へ再設計した。

## 5. 段 6 が見つけた生存変異 3 件

実装後、両レンズが N1〜N5 を**全部通過する非等価変異**を独立に指摘した。

| # | 変異 | 何が壊れるか |
|---|---|---|
| F1 | 射影を `context.arm == "on"` に限定 | off arm が build へ届かず、B-4 の on/off 対が揃わない |
| F2 | `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` を `OTHER` へ丸める | 計測できない site で `linux-baremetal` 契約を束縛した config が作れる (fail-close の弱体化) |
| F3 | sort へ contract bind だけ足す | `bound_environment_contract` は campaign ID の正準 preimage に入らず N5 の ID 比較を通る |

F2 の test は `conftest` が `_has_nqsv` も中立化するため、`socket` だけ差し替えると
site が `OTHER` へ落ちて**恒真に緑になる**。両方を差し替えて初めて機構を通る。

3 件とも test 側だけで閉じ、実装は 1 byte も変えていない。

## 6. 変異走行

runner argv は `orchestrator/tests/test_p3_b4_launcher.py` 単独。理由は
**`p3_b4_launcher.py` が contract-loader の enforcement source であり、変異で dirty にすると
`contract-loader-drift` という同じ理由で無関係な test が大量に赤くなり単一理由性が壊れるため**。
commit 前の焦点走 (10 file) で 128 赤が出たが、その内訳は全部 drift で、
同 test file だけは赤 0 件だったという実測に基づく。

probe を 3 回まわしてから本走した (`mutation/`)。

- probe1 (`db95ffb3b`): 事前登録した期待 node が M1 と M4 で不完全 (N2 / N3 の取りこぼし) と判明。
- probe2 (`fe1724fe9`): 新 3 変異が狙いどおりの node だけを単一理由で殺すことを確認。
- probe3 (`fe1724fe9`): fix で node が増えた分、M1 / M4 の death set が 3 → 6 に成長。全 8 件を確定。

本走 spec は probe3 の実測から**機械生成**した (転記事故を避けるため)。

**本走結果** (`mutation/mutation-ledger.json`、baseline PASSED / rc=0 / 赤 node 0):

| 変異 | 結果 | 殺した node 数 |
|---|---|---|
| m1 射影ブロック削除 | KILLED | 6 |
| m2 marker のみ (contract bind なし) | KILLED | 1 |
| m3 分岐を `{"base","sort"}` へ拡大 | KILLED | 1 |
| m4 site を literal `OTHER` へ | KILLED | 6 |
| m5 base helper を trigger の同名 helper へ差し替え | SURVIVED | 0 |
| m6 射影を `arm == "on"` に限定 | KILLED | 1 |
| m7 未許可 site を `OTHER` へ丸める | KILLED | 2 |
| m8 sort へ contract bind だけ足す | KILLED | 1 |

`matching 8/8`、`MISMATCH 0`。

**F358 が課す共通核の検査 (実測)。** 全 KILLED 変異の `failed_nodes` の交差を取ると
**核は 0 件**である。したがって「ファイルが 1 byte 変わったこと」だけで発火する
`contract-loader-drift` 由来の node は 1 つも kill に数えられていない。
核を差し引いた delta は m1=6 / m2=1 / m3=1 / m4=6 / m6=1 / m7=2 / m8=1 で、
4 変異は delta=1 = その node が唯一の killer である。

F358 の恒久対応は「核を取って差し引く」だが、本 wave は**核が空になる runner scope を先に選ぶ**
経路を採った (上記のとおり `test_p3_b4_launcher.py` 単独)。結果として核は事後にも 0 件だった。

**m5 は等価変異である。** `p3_s4_loop._campaign_cfg_for_site` と
`p3_s4_loop_trigger_gating._campaign_cfg_for_site` は signature・docstring・body が逐語同一で、
参照する `_SITE_ENV_TAGS` / `_CAMPAIGN_ENV_KEY` / `_lookup` も同じ値である
(段 6 レンズ A が逐語比較で確認)。gate としては数えない。

**erratum (DW-M02):** 事前登録の death set は M1 と M4 で不完全だった。probe1 が N2 を、
probe3 が N3 と fix 後の追加 node を検出して訂正した。初回登録も probe ledger に残してある。

**wrapper の rc=125 と、その解消。** 上の 4 走 (probe 3 本 + 本走 1 本) はすべて
`mutation_worktree.py` が `rc=125` を返した。内訳は `child_rc=0` (harness 本体は成功) かつ
`shared_snapshot_matches: false` で、失敗したのは wrapper の「source/main 共有木の観測 bytes が
不変」という事後検査だけである。本走の窓 (10:12:22–10:33:14 JST) の中、10:31:52 に別 session が
commit `2a68ac36f` を main へ着地させたことを実測した。wrapper は主 checkout と wave worktree の
両方で `git status` と `git submodule status --recursive` の bytes 一致を要求するため、
main へ並行して land する session がある限りこの事後検査は通らない。

これは F300 の既知型で、同エントリの恒久対応追補が回避策まで書いていた
(`--source-repo` へ独立 clone を渡すと観測点が clone 1 点へ畳まれる)。
**親がそれを読まずに 4 走させたのが手順漏れである。** 読んだ後、
`git clone --shared` した clone で main 取り込み後の tip に対して本走を取り直した
(`mutation/mutation-ledger-clone-run.json`)。

| 走行 | repo_head | wrapper rc | `shared_snapshot_matches` | 結果 |
|---|---|---|---|---|
| 本走 1 (wave worktree を source) | `fe1724fe9` | 125 | false | KILLED 7 + SURVIVED 1、matching 8/8 |
| 本走 2 (独立 clone を source) | `9063b5771` | **0** | **true** | KILLED 7 + SURVIVED 1、matching 8/8 |

**独立した 2 走が別 commit・別 source で同一の結果を再現した。**
launcher と test の blob は `fe1724fe9` と `9063b5771` で byte 一致しており
(merge は docs しか動かしていない)、変異 anchor は両走で同一である。

## 7. scope 外で real と裁定した所見 (ユーザー裁定へ返す)

段 6 レンズ B が実測した。段 2 プランは公開 `p3_s4_loop.run_one_iteration` の授権境界について
「直接 caller は将来正式化された場合だけ」と書いたが、**事実と異なる**。
`orchestrator/tests/test_p3_s4_loop.py` の 9 箇所から現に直接呼ばれており、
うち 1 箇所は B4 marker 付き config を公開関数へ渡す明示的な負例である。

この境界は射影**前**の cfg で `expected_campaign_id` を作るため、直接 caller が未射影 config を
渡すと条件付きで不一致が残る。ただし正式 launcher 経路は `main` → `drive_iteration` へ進んで
この境界に到達せず、現存 caller は境界が拒否することを検査する負例である。
`p3_s4_loop.py` や授権境界を変更する理由にはならないので**実装しなかった**。
射影前境界を残すか否かは裁定へ返す。

## 8. 段 6 が付けた証拠の射程限定

N3 (`test_base_launcher_pegasus_context_passes_real_authorization_and_g4`) は
実 `launch_bootstrap` を通し、spy 内で実物の `require_b4_production_context` と
`verify_b4_launch_context` (G4) を呼ぶ。ただし registry の base entry は spy に置換されるため、
`p3_s4_loop.main` / `drive_iteration` の実走証明ではない。
また m1 / m4 では前段の production validator が先に例外を投げるため、
**N3 は G4 固有の mutation-red 証拠ではない** (段 6 レンズ A)。正系列の証拠としてだけ数える。

## 9. 凍結成果物への影響

`p3_b4_launcher.py` の blob sha と file の sha256 を tracked file 全体へ検索して pin 0 件を実測した。
ただし `p3_b4_closed_critic.projection_closure_manifest` は driver 分岐より**前**に
`p3_b4_launcher.py` を全 driver 共通で含むため、launcher の 1 byte 変更で
base・sort・trigger の `projection_sha256` がすべて変わる。「sort の**挙動**は不変」は正しいが
「sort / trigger の **proof bytes** も不変」ではない。
現時点でその 3 値を pin している凍結記録は存在しない
(事前登録の該当欄は `未記入`、production の admission record JSON も不在) ので、
同時更新すべき凍結成果物はない。

## 10. 検査

- 実装 commit 後の焦点走 (consumer 10 file): **1290 passed / rc=0**
- 変更した test file の単独走: 実装時 39 passed、fix 後 42 passed (fix 子の自走 harness 実測)
- 全史 AI provenance 監査: **rc=0 / 9202 件・新規違反なし**
- 変異 matrix 本走: **KILLED 7 + 等価 SURVIVED 1、MISMATCH 0** (独立 2 走で再現、
  うち clone 経由の 1 走は wrapper も `rc=0`)
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: rc=0、`conjunction_hits` null
- `python3 tools/check_docs.py`: 違反なし
- `python3 tools/spool_fold.py --dry-run`: rc=0 (`status: planned`)

受入全走はこの記録 commit を含む最終 tip に対して投入する (本 README 作成時点では未実施)。

## 11. 逐語

`verbatim/` に段 1 brief、段 2 plan (prompt 込み)、段 3 敵対相談 2 本、親の実測値、
段 4 裁定、段 5 実装子、段 6 敵対レビュー 2 本と fix 子を全文で置いた。
`mutation/` に 4 本の spec と 4 本の ledger を置いた。

## 12. 段 8 自己改善の裁定

候補 4 件を評価し、1 件を routing、3 件を見送った。

1. **routing 済み — 変異 wrapper の `rc=125` (F300)。** 既存 F への再発追記として
   `docs/spool/failures/` へ書いた。同型の既存エントリがあるので新規 F は採らない。
   恒久対応追補 (独立 clone を `--source-repo` へ渡す) の有効性を独立 2 例目として確認した。
2. **見送り — 変異 runner scope と `contract-loader-drift` の関係。** F357 と F358 が
   既にこの型を扱い、F358 の恒久対応 (共通核の集合演算) は本 wave の台帳で満たしている
   (核 0 件を実測)。本 wave が採った「核が空になる runner scope を先に選ぶ」経路は F358 の
   恒久対応を古くしないので supersede に当たらず、再発でもない。
   `docs/dev-wave/mutation.md` への追記は L1.5 層の byte 予算が満杯であることが
   先行 wave の実測で確定しており (9772 > 9566)、予算のために安全義務を削ることは
   自己改善契約が禁じている。よって記録のみとする。
3. **見送り — 重複編集面検査の偽陽性フィルタ。** 「staged blob が main の HEAD blob と
   byte 一致するだけの古い worktree」を自動で落とす手が無く、毎回 blob 照合を手で書いている。
   ただし `docs/dev-wave/` に重複編集面検査を課す節は存在せず (本 wave の検査は依頼本文が
   指示したもの)、新規 L2 節の登録は D271 の 3 条件を満たさない。見送る。
4. **見送り — orphan hold が 2 箇所にある件。** `orphan-hold.json` と
   `orphan-holds/<request>.json` の両方を消さないと次の投入が hold を再武装する。
   これは既知で、解除手順も既に運用知見として確立している。repo 側の変更は不要。

段構成・実装子権限・正しさ防壁・裁定境界・予算の変更は 1 件も行っていない。

## 13. 受入全走が暴いた 4 件目 — 証拠 fixture のホスト依存

段 6 のレビューと変異を通過した後、**受入全走で 35 件の setup error** が出た。
`orchestrator/tests/test_p3_b4_material_report.py` の全 module fixture 消費者である。
main 単独 (clone を `fdf9c40c8` へ checkout) では同 file が **49 passed / rc=0** なので、
本 wave に帰属する赤である。

### 機序 (実測で確定)

1. 証拠 fixture は **module scope** (`test_p3_b4_material_report.py:146`、
   `test_p3_b4_raw_record_producer.py:1146`)。
2. `conftest.py:239` の site 中立化は **function scope の autouse** である。
   **module fixture の setup はそれより先に走るので中立化が効かない。**
3. テストは Pegasus の計算ノード (`bnodeNNN`) へ dispatch されるため、実 site は
   `PEGASUS_COMPUTE` に解決される。
4. `_evidence_scope` は `_marked_driver_configs()` = `B4L._driver_configs("base", ...)` を使う。
   **本 wave が足した base の site 射影**が `pegasus` 契約を cfg へ束縛する。
5. replica 側の lock writer `_write_campaign_lock_with_writer` は
   `bound_environment_contract is None` のときだけ `L.ENV_TAG` (= `linux-baremetal`) で補う。
   **変更前は base の cfg が契約を持たなかったので常にこの分岐が発火し、seed 側と偶然一致していた。**
   変更後は cfg が `pegasus` を持つのでそれが使われ、seed の `linux-baremetal` と食い違う。

実測値: seed `contract_sha256=1b2ee853...` (`linux-baremetal`)、
replica `contract_sha256=e576e9cd...` (`pegasus`)。
`L.ENV_TAG='linux-baremetal'`、
`_SITE_ENV_TAGS={'OTHER':'linux-baremetal','PEGASUS_COMPUTE':'pegasus'}`。

### 直し方と、直さなかったもの

直したのは **fixture のホスト依存性**である。`_evidence_scope` の最外周で conftest と同値の
中立化 (`site_policy.socket` と `site_policy._has_nqsv` の**両方**) を掛け、seed と replica の
双方が同じ契約を使うようにした。`ExitStack` が証拠 scope 全体を覆うので正常終了でも例外でも復元する。
raw-record producer と material-report が共有する経路なので両 consumer が同時に直る。

**実装 (`p3_b4_launcher.py`) は 1 byte も変えていない。** 本題の射影は正しく、
壊れていたのは fixture が実ホスト名に依存していたことである。
`_assert_replicas_match_real_except_identity` の比較は緩めていない。`conftest.py` も触っていない。

### この wave の手順の失敗

段 6 の consumer 列挙を module 名の参照検索
(`git grep -ln "p3_b4_launcher\|B4L\."` on `orchestrator/tests/`) で行ったため、
`_marked_driver_configs` 経由でしか触らない `test_p3_b4_material_report.py` を取り逃がした。
`DW-O26` は「名前の推測でなく参照関係で引く」と課すが、**間接参照 (helper 経由) まで辿らないと
同じ取り逃がしが起きる**。焦点走に入っていれば受入 1 走 (約 30 分) を使わずに見つかっていた。
