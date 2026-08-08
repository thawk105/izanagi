# 段 4 裁定 — [T-657] + [T-660]

親裁定。段 3 は 2 レンズとも NO-GO。refuted は 1 件、残りは real。
**親自身の実測で brief の前提 1 件を撤回し、scope を縮小した。**

## 0. 親の新実測 (段 3 後に判明。両レンズの A-1 / B-1 を決着させる)

活性化前の現状 (head=1、g1 が current) で committed silo evidence の再検証を実走した:

```
$ python3 -m orchestrator.campaign.silo_ladder_rung1 verify-result \
    --json output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json   → rc=1
{"failures": [{"detail": "raw attestation binding/ordinal set mismatch", "reason_code": "raw_bundle"},
              {"detail": "current binding mismatch: driver", "reason_code": "binding"}], "ok": false}
```

**この経路は g2 活性化を待たずに既に赤い。** `validate_current_bindings` は driver / policy /
verifier_module / runtime_modules を **current bytes** と比較し (silo_ladder_rung1.py:3522-3539)、
driver の歴史 sha256 で先に `DriverError` を投げるため、**contract 検査 (:3540-3548) に到達しない**。
したがって contract 軸だけを historical 化しても、この CLI の受理集合は **1 bit も変わらない**。

T-529 の所見 B5 が実際に指していたのは production CLI ではなく、
`test_silo_ladder_rung1_evidence.py:1262-1272` (テストが独自の再束縛ロジックを持ち、
contract だけを current lookup と比較する) である。**g2 で新たに赤くなる silo 面はここだけ。**

## 1. 所見の裁定

| ID | 要旨 | 裁定 |
|---|---|---|
| A-1 | committed 保全という brief と実受理集合が一致しない | **real・採用 (設計変更)**。§2 のとおり production silo を scope 外へ落とす |
| A-2 | 新受理集合を固定するテスト行列が不足 | **一部 refuted**。production を変えない裁定により新受理集合が存在しないため、提案 5 件のうち (1)(4)(5) は現行 CLI の既存挙動 pin であり本 wave の純増ではない。(2)(3) は §2 の lane と同時に裁定パッケージへ |
| A-3 | 変異行列が片側しか登録されていない | **real・採用**。§4 のとおり 3 件 + 新旧両走を登録 |
| A-4 | floor 17-key 比較が独立 golden でない | **real・採用**。親が独立検算し SHA 一致を確認 (§5) |
| A-5 | 「T126 は影響なし」に反例 (series identity は回転) | **real・採用**。brief を訂正 |
| A-6 | prediction seal も current-coupled | **real・採用**。影響表へ追加 |
| B-1 | P1 の実 artifact admission が未証明 | **real・採用**。A-1 と同一。§2 で決着 |
| B-2 | ユーザー手順 C の guard が fail-closed でない | **real・採用** |
| B-3 | `mv` 退避に復旧がなく DW-O11 に反する | **real・採用**。非破壊 copy + trap 復旧へ |
| B-4 | C commit の provenance preflight 欠落 | **real・採用** |
| B-5 | land lease と tested-main の固定が工程にない | **real・採用** |
| B-6 | B 時点の「受入不能」に実行境界がない | **real・採用**。pre-C / post-C を分離 |
| B-7 | T126/P3 の contract 非依存が過度な一般化 | **real・採用** (A-5 と同型) |
| B-8 | driver test の所有が曖昧 | **real・採用**。§3 の単位再編で消滅 |
| B-9 | mutation の排他・queue が未定義 | **real・採用** |
| B-10 | T660 変異が DW-M08 の検出力を閉じていない | **real・採用**。新旧両走を登録 |
| B-11 | ledger 外置きと D tip-only land が衝突 | **real・採用**。記録 commit を land 対象にする |
| B-12 | isatty / AI-Agent: none は人間性の証明でない | **real・記録のみ**。C を「外部 human trust boundary」と明記し機械認証と主張しない |

親の provisional 裁定: **(P1) 撤回** (§2)、**(P2) 維持**、**(P3) 維持** (ただし §6 のとおり本 wave は
ユーザー手番で終端し land しない)、**(P4) 修正** (空 chain node を追加、変異 3 件)、**(P5) 強化** (§5)。

## 2. scope 縮小 — production silo は変更しない

- `validate_current_bindings` の resolver 分離は **本 wave では実装しない**。
  DW-G05 の成果物影響が書けない (受理集合・値・参照のいずれも変わらない) ため、
  DW-G02/DW-G05 に従い backlog とする。
- 前提 (a)「silo の歴史 evidence を historical 解決へ変える」の**実体を、g2 活性化で新たに
  赤くなる面の除去と定義する**。実体は `test_silo_ladder_rung1_evidence.py:1262-1272` のみ。
  ここを記録 hash の `resolve_by_contract_sha256(..., expected_env_tag="pegasus")` へ変える。
- **裁定パッケージへ返す (本 wave で実装しない)**: literal committed silo evidence の
  full historical 再検証 lane (contract に加え driver / policy / verifier_module /
  runtime_modules / raw bundle も記録 hash から歴史 blob で検証する独立経路)。
  現状この CLI は committed evidence に対して恒常的に赤であり、誰も再検証に使えない。

## 3. 実装単位 (段 5)

production 変更が消えたため **1 単位** に統合する (下記の実行判断)。

- **単位 A (codex, workspace-write, reasoning=high)**: activation 適用・追従・silo テストの
  historical 化・T-660 精密化。所有 = `orchestrator/campaign/env_contract.py` (head 定数 2 行のみ)、
  `orchestrator/tests/test_env_contract_activation.py`、`orchestrator/tests/test_env_contract.py`、
  `orchestrator/tests/test_t419_probe_causality.py`、
  `orchestrator/tests/test_silo_ladder_rung1_evidence.py`。
- **実行判断 (DW-O12: 裁定と実行の差を記録する)**: 当初 2 単位 (activation / silo) に分けたが、
  silo テストは「current が g2 のとき historical 解決する」ことを検証するため head 定数の更新に
  **依存**し、並列化できない。`DW-S05-A` の「単位間に依存があれば先行単位を完了させる」に従うと
  順次実行になり、silo 側の編集面が 1 ファイル 1 箇所と小さいため、worktree を分ける利得がない。
  したがって 1 単位に統合した。所有の素集合性は単位が 1 つになったことで自明に成立する。
  B-8 (driver test の所有の曖昧さ) は、§2 の scope 縮小で driver test を編集対象から外したため消滅。
- `00000002.json` の発行は**親が tool で行い**、実装子の投入前に済ませた (P2 維持、実施済み:
  serial=2 / previous `f7807285…` / pegasus g2 `1346c20b…` / 新 head `398b1920…`、00000001.json 不変)。
  親は record を作るだけで、head 定数とテストは実装子が書く (親は実装面を直接編集しない)。

## 4. 変異事前登録 (DW-M01 / DW-M03 / DW-M04 / DW-M08)

対象 node 集合を明記する。**期待は node 集合に依存する** (A-3)。

| ID | 変異 | node 集合 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `terminal_serial != expected_head_serial` を無効化 | production tail-deletion node 単独 | **SURVIVED** | serial は state hash の入力に含まれる (env_contract_activation.py:130, 406 のコメント)。state-hash gate が同じ rollback を拒否する |
| M2 | `terminal_hash != expected_head_state_sha256` を無効化 | 同上 | **SURVIVED** | serial gate が先に落とす。両単独が SURVIVED であることで対称な mask を示す |
| M3 | M1 + M2 の対変異 (同一ファイル累積) | 同上 | **KILLED** | head pin の実効性はこの対でのみ立証される |
| M4 | M2 単独 | `test_head_pin_rejects_same_serial_state_hash_mismatch` を含む activation suite | **KILLED** | 同一 serial・異なる state hash の node は serial gate に mask されない |
| M5 | 空 chain の**理由文字列だけ**を別文言へ変える (guard 自体は残す) | 新設 empty-chain node + production tail-deletion node | **新設のみ KILLED**。**kill 集計から分離し diagnostic sensitivity pin として記録する** | 段 6 C-1 の裏取り: guard 自体を無効化すると `rows` が未束縛のまま `ActivationState(...)` (env_contract_activation.py:417) へ進み `UnboundLocalError` が漏れるため、変更前 HEAD 版でも production node が KILLED になり「新テストだけが検出」は成立しない。理由文字列変異なら旧版 SURVIVED / 新版 KILLED が成立し、DW-M08 の新旧両走を満たす |

- M1/M2 の SURVIVED は **kill 集計から分離**し、diagnostic sensitivity pin として台帳へ記録する
  (DW-M08)。SURVIVED は `DW-M04` に従い mutated diff で注入実在を確認する。
- 正例 (過剰拒否の検出): 活性化後の実 authority で `lookup("pegasus")` が g2 を返し、
  `resolve_by_contract_sha256(g1)` が成功し続けること。全変異走行で緑を保つ。

## 4b. 段 6 レビューの裁定 (追記)

| ID | 要旨 | 裁定 |
|---|---|---|
| C-1 | M5 は受理集合の kill でなく診断 pin | **real・採用**。§4 の M5 を理由文字列変異へ再設計し kill 集計から分離 (親がコードで裏取り) |
| D-1 | create-only writer と退避手順の衝突 | **real・採用**。fix 子へ非破壊 copy + trap 復元を要求 |
| D-2 | 失敗時停止が実行可能な手順になっていない | **real・採用**。`set -Eeuo pipefail` + 全条件 assert |
| D-3 | provenance preflight 欠落 | **real・採用**。message file → `--message-file` → `commit -F` → full audit |
| D-4 | T-530 未 land のまま activation-only を land する経路 | **real・前提解消**。段 6 の直後に取り込んだ local main `5ffcf3a6` に T-530 の contract hash 束縛 (`ec530e9b` ほか計 15 commit) が **land 済み**であることを実測した。したがって「g1 の WAL COMMIT / campaign identity を g2 実行が再利用する」経路は本 wave の land 前に閉じている。**land 順序の blocking 条件としては不要になった** |
| D-5 | 再開後の land tip 固定が曖昧 | **real・採用**。§6 に再開手順を明記 |
| D-6 | T126 series identity 回転を固定する受入 node がない | **should・backlog**。成果物の値は回転するが、証跡テストの追加は本 wave の scope (活性化 + 前提 2 件 + T-660) 外。裁定パッケージへ |

## 4c. 焦点再レビュー (DW-O16) の裁定

対応表: C-1 / D-3 / D-4 / D-5 = closed、D-1 / D-2 = partial (R-1〜R-3 として再提出)、D-6 = scope 外。

| ID | 要旨 | 裁定 |
|---|---|---|
| R-1 | cleanup 中の再 signal で復元が中断されうる | **real・採用**。fix 2 巡目へ |
| R-2 | `git restore` 失敗時に検証済み backup を使わない | **real・採用**。fix 2 巡目へ |
| R-3 | `PYTHONOPTIMIZE` で全停止条件が消える (再レビューが実測) | **real・採用**。fix 2 巡目へ |
| R-4 | floor test helper が「末尾 = g1」を仮定し 4 node が赤くなる | **refuted (親が実測)** |

**R-4 の反証**: helper が使う `ENV_TAG` は `campaign.p2_2` の **`"linux-baremetal"`** であり pegasus では
ない (test_s8b_floor_campaign.py:61 の import)。linux-baremetal は現在も 1 世代のみなので、合成される
世代列は `(g1, synthetic g2)` = generation (1, 2) となり連番検査を通る。実測でも
`test_s8b_floor_campaign.py` + `test_frozen_artifacts.py` は **211 passed / 2 skipped / 1 failed** で、
赤は `test_real_seal_protocol_to_floor_official_core_e2e` の 1 件だけだった。これはレンズ D が
期待赤として事前予測した floor 未再発行由来のもので、helper 系 4 node は緑である。
helper の docstring にある「bootstrap fuse により単一世代」は撤去済み機構への stale な言及だが、
結論 (linux-baremetal が単一世代) は今も正しいため **nit・backlog** とする。

**この実測は同時に、段 6 レンズ D の期待赤予測が正確だったことを確認した** — 活性化が floor 以外に
壊す面は floor 系 subset には無い。

## 5. floor 再発行のユーザー手順 (B-2/B-3/B-4/A-4 反映)

- **非破壊 copy** (`cp` + 既存 backup 禁止) とし、`mv` による tracked file の消失を作らない。
  失敗時は `trap` で `git restore --source=HEAD --` により原状復帰する (B-3)。
- 全体を `bash -Eeuo pipefail` の 1 script にし、各 guard を停止条件にする (B-2)。
- commit は message file → `check_ai_provenance.py --message-file` preflight → `git commit -F`
  → full-history 監査 (B-4、DW-O17)。
- **独立 golden を事前登録する (A-4、親が検算済み)**: 旧 774 bytes / 旧 SHA `261cec1c…` /
  g1 hash の出現回数 1。期待 new = 旧 bytes の g1→g2 単一置換、
  **期待 SHA `c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d`**、長さ 774 不変。
  この 3 条件を満たさなければ commit しない。
- C は **外部 human trust boundary** として扱い、isatty や `AI-Agent: none` を人間性の機械証明と
  主張しない (B-12)。

## 6. 工程と終端 (B-5/B-6/B-9/B-11、P3 修正)

- **本 wave は floor 再発行 (ユーザー手番) の直前で終端し、land しない。**
  活性化を land すると floor live admission と prediction seal が壊れた窓を main に作るため
  (DW-STOP のユーザー手番待ち)。
- **pre-C で許される検査 (B-6)**: 単位 A/B の統合後に targeted テスト群を計算ノードで実走し、
  期待赤 (certified writer admission / floor / prediction seal = g2 authority + g1 floor 由来) と
  想定外の赤を分離する。期待赤は `blocked/pre-floor` として記録し、受入緑にも回帰赤にも数えない。
- **受入全走・変異本走・land は post-C** (ユーザーが floor を再発行した後)。そのとき
  lease claim → `acquired` のときだけ投入 → 全終了経路で release (B-5)。
- 変異本走は他の子・受入を止めた critical section で行い、ledger 完了・復元・HEAD blob 一致を
  確認してから次へ進む (B-9)。
- **land 対象は変異 ledger を収容した記録 commit の tip** とする (B-11)。D tip-only ではない。
- **変異 spec の実 JSON は再開時 (ユーザー手番後・本走直前) に作る。** 今 spec ファイルを固定すると
  `DW-M07` の anchor (old 逐語) が再開時の tree と一致する保証がないため、設計 (上表) だけを
  本裁定へ凍結し、ファイル化は本走直前に行う。
- 受入 matrix に **T126 qualification driver と P3 gating** を追加する (A-5/B-7)。
  brief を「T126 protocol admission は不変、series identity は回転する (旧 series を継続しない)」
  へ訂正する。prediction seal を独立 consumer として影響表へ追加する (A-6)。
