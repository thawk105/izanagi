## 総括

- 必読 brief は読了した。S1 は既存の公式発行 CLI を使い、head を serial 2、state hash `398b1920...bed8` へ更新する。
- 現行 main では consumer 配線が未完了なので、S2 をそのまま発行すると admission と実 driver の authority が分裂する。D471 上も発行禁止である。
- 安全な順序は「consumer 配線を先に着地 → activation 発行 → head 更新 → 新 process で reseal」である。
- P1〜P4 自体にコード上の誤りはないが、brief の「create-only なので取り消せない」と「実装子 1 本」は修正が必要である。
- 2 本の直列実装に分割すべきである。この段では pytest を実行しておらず、緑とは主張しない。

## 先行 blocker

現行の admission は resolver が返す現行契約の protocol を検証します。[certified_writer_admission.py:178-224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/certified_writer_admission.py:178)

一方、実際の標準 floor job は legacy path を固定して driver へ渡します。[floor_campaign.sh:954-986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/floor_campaign.sh:954)

したがって S1、S2 後は次の状態になります。

| 状態 | resolver / admission | 実 driver | 結果 |
|---|---|---|---|
| 現在 | legacy g1 を exact 1 件選択 | legacy g1 | 一致 |
| S1 のみ | g2 protocol が 0 件 | legacy g1 | admission が fail-closed |
| S1 → S2 | versioned g2 を選択 | legacy g1 | authority 分裂 |
| consumer 配線 → S1 → S2 | versioned g2 を選択 | 同じ versioned g2 | 安全な最終状態 |

これは既知の残件です。[decisions.md:19610-19616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19610) は実 driver の固定 path による authority 分裂を明記し、[decisions.md:19624-19635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19624) は consumer 配線前の実 artifact 発行を禁止しています。

従って、現行 scope のままなら S1 の準備とテスト追従までは実装できますが、S2 の発行直前で停止すべきです。安全に完遂するには [T-419] (3) の shell・driver・固定 path consumer 配線を先行 scope に追加する必要があります。

## S1: activation record の正確な発行手順

手書きや旧 branch からのコピーではなく、公式 CLI を使います。

| 順 | file:line | 作業 |
|---:|---|---|
| 1 | [issue_env_contract_activation.py:27-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:27) | `--active` で全登録 env を明示する。 |
| 2 | [issue_env_contract_activation.py:179-201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:179) | 現 head 1 を読み、`build_activation_record()` で serial 2 を構築する。 |
| 3 | [env_contract_activation.py:136-164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract_activation.py:136) | serial、predecessor、env 順序を検査し、state hash を算出する。 |
| 4 | [issue_env_contract_activation.py:202-219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/issue_env_contract_activation.py:202) | canonical bytes に LF を 1 個加え、候補 chain 全体を検証して create-only 発行する。 |
| 5 | [env_contract.py:381-387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:381) | CLI が表示した serial と state hash へ head 定数を直ちに更新する。record と同一 commit に入れる。 |

実装時のコマンドは次です。

```bash
python3 tools/issue_env_contract_activation.py \
  --active linux-baremetal=1 \
  --active pegasus=2
```

`canonical_record_bytes()` は LF を含まない ASCII JSON を生成し、CLI 側が `+ b"\n"` しています。[env_contract_activation.py:113-133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract_activation.py:113)

発行される 538 bytes は次の 1 行と末尾 LF です。

```json
{"activation_serial":2,"activation_state_sha256":"398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8","active_contracts":[{"contract_sha256":"1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7","env_tag":"linux-baremetal","generation":1},{"contract_sha256":"1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c","env_tag":"pegasus","generation":2}],"previous_activation_state_sha256":"f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed","schema_version":"env-contract-activation/v1"}
```

追加先は `orchestrator/campaign/env_contract_activations/00000002.json`、head 更新値は次です。

```text
_ACTIVATION_HEAD_SERIAL: int = 2
_ACTIVATION_HEAD_STATE_SHA256 = 398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8
```

注意点は、record 発行後から head 定数更新までの短い間、directory tail=2 と pinned head=1 が不一致になり、`lookup()` は失敗することです。CLI 実行後は別の authority 読み込みを挟まず、直ちに定数を更新します。定数を先に変えると、逆に record 不在で CLI 自体が current state を読めません。

## S2: reseal の手順

consumer 配線が先に着地済みであることを開始条件にします。

| 順 | file:line | 作業・検証 |
|---:|---|---|
| 1 | [env_contract.py:631-662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:631) | 新 process で authority chain が head 2 として load され、`lookup("pegasus")` が g2 を返すことを確認する。 |
| 2 | [s8b_floor_campaign.py:936-989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:936) | fixed HEAD の legacy anchor から 16 field を継承し、g2 contract hash と HEAD gitlink の 2 field だけを更新する。 |
| 3 | [s8b_floor_campaign.py:991-1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:991) | create-only 発行、HEAD 再確認、read-back、full index 再走査を行う。 |
| 4 | [s8b_floor_campaign.py:6566-6570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:6566)・[6689-6701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:6689) | 公式 zero-argument CLI `python3 orchestrator/campaign/s8b_floor_campaign.py reseal-protocol` を使う。caller から path や hash を渡さない。 |
| 5 | [s8b_floor_campaign.py:6702-6723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:6702) | `check-protocol-index` で legacy と versioned の計 2 件、現行 g2 一致が exact 1 件であることを確認する。 |

期待される成果物は次です。

- path: `output/s8b-freeze/floor-protocols/1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c--511c9538e4e8efa54b45cda62e72389ed3b706ec.json`
- byte length: `774`
- SHA-256: `b10b91aa1ec0e63120ab7aaf0531bbc0fa29f6beaa7964e3620593cdb4fbbf13`
- legacy anchor `output/s8b-freeze/floor_protocol.json`: bytes・SHA-256 とも不変
- `FROZEN_MANIFEST`: 更新しない。[decisions.md:19585-19587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:19585)

## S3: 静的に確認した fallout 全列挙

### 確実に赤になる箇所

| file:line | 落ちる理由 | 修正方針 |
|---|---|---|
| [test_env_contract.py:270-282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract.py:270) | current Pegasus の path/hash を g1 に固定している。 | g2 path `calibration-94a4...json`、hash `94a4...5c5a9` を期待する。 |
| [test_env_contract.py:378-384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract.py:378) | 全 env の active を `sequence[0]` と仮定する。 | activation state の generation から期待 entry を選び、Pegasus は `sequence[1]` と確認する。 |
| [test_env_contract.py:618-622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract.py:618)・[913-939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract.py:913) | g2 を never-active と仮定する。 | `00000001.json` だけの test-local authority を使い、never-active の拒否と clock audit を維持する。存在しない g3 へ置換しない。 |
| [test_env_contract.py:1183-1196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract.py:1183) | current lookup と g1 golden を同一視している。 | `test_pegasus_g1_contract_sha256_golden` に改名し、`GENERATIONS["pegasus"][0]` を明示する。既存 g2 golden は維持する。 |
| [test_env_contract_activation.py:524-541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract_activation.py:524) | `00000001.json` の親 directory 全体を head 1 として読むため、新しい tail 2 で失敗する。 | genesis 単体は明示的な 1 record tuple で検査し、別に production chain 2 件・head 2・Pegasus g2 を検査する。 |
| [test_env_contract_activation.py:1738-1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract_activation.py:1738)・[1916-1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract_activation.py:1916) | current serial=1、record 数=1 を期待する。 | predicate 呼び出しが active head 2 と 2 file を変更しないことへ期待を更新する。clock-method test も serial 2 とする。 |
| [test_env_contract_activation.py:2028-2071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract_activation.py:2028) | current g2 から serial 3 の g2 no-op を作り、意図した head mismatch より先に no-op 拒否になる。 | genesis-only authority/head 1 を組み、g1→g2 の valid suffix を発行して head 未更新拒否を試す。 |
| [test_env_contract_activation.py:2384-2390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract_activation.py:2384) | g2 hash を never-active と仮定する。 | genesis-only authority へ隔離する。 |
| [test_env_contract_activation.py:2435-2483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_env_contract_activation.py:2435) | fork child の current hash を g1 に固定する。 | expected hash を active g2 へ更新する。 |
| [calibration_freeze_authority_execution.py:86-172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/calibration_freeze_authority_execution.py:86) | positive invocation digest が head 2 で変わる。negative は current g2 の次世代を探して失敗する。 | positive は current 2-record chain を使う。negative は record 1 を明示的な prefix とし、実 record 2 を足しながら expected head を 1 に据え置く。 |
| [activation-head-consistency.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/fixtures/calibration_freeze_authority/cases/activation-head-consistency.json:1)・[manifest.v1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/fixtures/calibration_freeze_authority/manifest.v1.json:1)・[calibration_freeze_authority_contract.py:179-205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/calibration_freeze_authority_contract.py:179) | 上記 invocation と fixture の独立 digest pin が不一致になる。 | positive digest=`d1e1dc2c52ef7378cfdfdd3b21bad641bb3a84b22f005592d261a123b23f6f34`、case raw hash=`1481a49d247160607c0e039b2d8f55c88e9e19bc7e1a4a4b729a5b2250476ca9`、entries hash=`e02be82ea8f7ee367f8a27d55a51895ef4e2375f616d02f9f87b717eaf378ac2` へ更新する。negative digest `a86a96...caa3` は不変。 |
| [test_s8b_protocol_builder.py:112-122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s8b_protocol_builder.py:112)・[510-525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s8b_protocol_builder.py:510) | approved Pegasus protocol の current contract が g2 になり、hash が変わる。 | length 774 は維持し、hash を `b10b91...fbbf13` へ更新する。 |
| [test_s8b_protocol_builder.py:1001-1024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s8b_protocol_builder.py:1001) | resolver が legacy path と旧 pin を返すと仮定する。 | 導出済み g2 versioned path、g2 hash、`511c9538...` を期待する。 |
| [test_s8b_protocol_builder.py:1087-1116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s8b_protocol_builder.py:1087) | 全固定 path literal が current resolver と同じという暫定 gate。S2 後に意図どおり赤になる。 | test を弱めず consumer 配線を先に実装する。その後、legacy anchor 定数と live resolver consumer を区別して検査する。versioned path を全定数へ焼き付けない。 |
| [test_s8b_floor_campaign.py:6939-7343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_s8b_floor_campaign.py:6939) | 固定 seal の g1 protocol/calibration を current `lookup("pegasus")` と比較する。早くとも 7110、7184 で失敗する。 | 記録済み contract hash を historical resolver で g1 に解決し、private replay の lookup seam も test-local g1 へ隔離する。凍結 anchor は変更しない。 |
| [test_silo_ladder_rung1_evidence.py:1288-1304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1288) | 歴史的 g1 evidence を current lookup と比較する。 | `binding["calibration"]["contract_sha256"]` を `resolve_by_contract_sha256(..., expected_env_tag="pegasus")` で解決して比較する。 |

### 赤にはならないが追従が必要な coverage

| file:line | 問題 | 修正 |
|---|---|---|
| [test_t419_probe_causality.py:1586-1627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_t419_probe_causality.py:1586) | dirty-scope test が `00000001.json` しか試さない。directory scope なので現状でも緑だが、record 2 の回帰を直接捕捉しない。 | `record_name` を `00000001.json` / `00000002.json` で parameterize する。 |

### consumer 配線を追加した場合の別 fallout

[tools/pegasus/floor_campaign.sh:954-1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/tools/pegasus/floor_campaign.sh:954) の固定 `PROTOCOL_PATH` を解消すると、少なくとも次の test helper と期待値が追従対象です。

- [test_pegasus_floor_tools.py:810-816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_pegasus_floor_tools.py:810): shell fragment の終端 marker。
- [test_pegasus_floor_tools.py:1033-1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_pegasus_floor_tools.py:1033): driver argv の固定 legacy path。
- [test_pegasus_floor_tools.py:1349-1380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_pegasus_floor_tools.py:1349): submit 経由の同じ固定 path。
- [test_pegasus_floor_tools.py:2162-2537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/tests/test_pegasus_floor_tools.py:2162): `_driver_tail()` と job-result fixture 群。

固定 path はほかにも [s8b_holdout_admission.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_admission.py:64)、[s8b_holdout_freeze.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_holdout_freeze.py:46)、[s8b_prediction_runner.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_prediction_runner.py:79)、[s8b_ratified_freeze.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_ratified_freeze.py:76) にあります。ただし historical anchor 用か live consumer 用かを区別せず一括置換してはいけません。これは本依頼で指定された読取範囲を超えるため、T-419 用の別 brief で設計するべきです。

### 明示的に変更しないもの

- `test_frozen_artifacts.py` と `FROZEN_MANIFEST`: versioned artifact は登録しない。
- `conftest.py` の synthetic serial 1 authority: test fixture なのでそのまま。
- `test_campaign_lock_codec.py` の serial 1 fixture: codec の合成値なのでそのまま。
- `test_env_attestation.py` の g1 calibration corpus: historical catalog coverage なのでそのまま。
- `00000001.json` と legacy `floor_protocol.json`: bytes を変更しない。

検索は全 213 test Python file を対象に、old state hash、g1 contract/calibration、`00000001.json`、head 定数、Pegasus `lookup` / `REGISTRY` / `GENERATIONS`、protocol path/resolver を照合しました。直接リテラルの網羅性は高いです。一方、pytest を実行していないため、動的 fixture の first-failure masking まで含む実測上の完全性は断定しません。

## 順序依存と create-only の判定

brief の「activation 先」は、正しい target pair を一度で作るためには正しいです。ただし consumer 配線がさらに前に必要です。

逆順で reseal すると current は g1 なので、次を発行します。

```text
(e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01,
 511c9538e4e8efa54b45cda62e72389ed3b706ec)
```

この時点で旧 g1/旧 pin と g1/新 pin の 2 件が current g1 に一致し、resolver は `count=2` で fail-closed になります。[s8b_floor_campaign.py:882-901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:882)

その後 activation すると current は g2 なので一致件数は 0。さらにもう一度 reseal すれば正しい g2 file は作れますが、誤った g1/新 pin file が余分な履歴として残ります。

一方、「create-only だから取り消せない」はコード上は誤りです。

- writer は `os.link(tmp, destination)` により同一 path の上書きを防ぐだけです。[s8b_floor_campaign.py:1177-1213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:1177)
- 発行失敗時の診断自体が exact file の除去を要求しています。[s8b_floor_campaign.py:925-933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/s8b_floor_campaign.py:925)
- D444 も「削除すれば同じ組を再発行できる」と明記しています。[decisions.md:18693-18700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/docs/decisions.md:18693)

従って機械的には削除可能です。ただし、追加のみの凍結運用や commit 済み履歴としては削除を正規の rollback にできないため、逆順発行を禁止する運用判断自体は妥当です。

## P1〜P4 の判定

| 項目 | 判定 |
|---|---|
| P1 | 正しい。registry にある Pegasus 世代は g1、g2 のみで、今回の activation は head 1→2 ちょうどである。[env_contract.py:253-311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-activation-rebuild/orchestrator/campaign/env_contract.py:253) |
| P2 | コードで真偽を決める命題ではないが、旧 branch は現行 main と大きく乖離しており、参考限定が妥当。特に legacy anchor 上書きや `FROZEN_MANIFEST` 更新は現行 D471 と不整合である。 |
| P3 | 正しい。`lookup()`、resolver、live admission の受理集合が変わるため軽量変更ではない。 |
| P4 | brief 作成時点の「未測」は正しい。本段の静的 grep で上表まで具体化したが、pytest 未実走なので動的 fallout はなお未測部分がある。 |

P1〜P4 にコードから誤りと断定できるものはありません。ただし P 群の外にある brief の次の記述は修正が必要です。

- [brief:51-52](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/inputs/s1-brief.md:51): create-only の不可逆性説明が不正確。
- [brief:67-71](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/inputs/s1-brief.md:67): consumer 配線と calibration authority fixture の追従が成果物一覧から欠落。
- [brief:74-76](/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/inputs/s1-brief.md:74): 現行 main では未完了の先行依存を含むため、単独実装子 1 本では安全な閉包にならない。

## 実装子の分割

2 本を直列にします。並列にはしません。

1. consumer 配線実装子

   T-419 (3) を所有し、shell・driver・固定 path consumer と対応テストを配線する。protocol artifact は発行しない。

2. activation/reseal 実装子

   consumer 配線の着地後に、公式 CLI で record 2 発行、head 更新、S3 fallout 修正、新 process で reseal、artifact/index 検証までを一続きで行う。record/head/artifact/test は同一統合 commit に収容する。

先行配線が別 wave ですでに着地した状態なら、2 番の実装子 1 本だけで十分です。現在の tree では着地していないため、親 brief の 1 本構成のまま S2 を実行してはいけません。

この調査は read-only で、既存の未追跡 `output/insights/2026-08-17_t657-activation-rebuild/` にも触れていません。pytest、build、acceptance check は実行していません。