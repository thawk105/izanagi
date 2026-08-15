検査基準は clean な現 HEAD `330f67d09eade8d556ab672e08b33d5694228887`。`pytest` は非実走で、コード読解、`jq`、`sha256sum`、directory 実査だけを行った。以下の「設計案」はすべて未実装・未確認であり、承認済み値ではない。

## A. canonical path への設置形の再検証

- `producer-design.md:169-212` の所在・生成順: 一致。現 HEAD の対応箇所は `s8b_oracle_spec.py:18-23,105-179,258-275`、`s8b_oracle_manifest.py:221-270,396-537`。
- `producer-design.md:214-223` の compact bytes 専用 writer: 一致。参照元 writer は `s8b_oracle_manifest.py:895-987`、pretty JSON と末尾 LF は同 `:903-905`、reviewed spec の canonical bytes 要求は `s8b_oracle_spec.py:258-269`。
- `producer-design.md:225-245` の bytes・authority・pin の同時設置: 一致。ただし現在も未実装で、pin は `None` (`s8b_oracle_spec.py:21-23`)。`output/s8b-oracle-spec/` と producer module は実測で不存在。外部 trust root 不在も `docs/decisions.md:15565-15587` から不変。

食い違い・陳腐化・欠落は次のとおり。

1. **単一 block 検査が手順上閉じていない。** `producer-design.md:190-194` は exact 1 block を要求するが、後段 `:206-210` が通す `validate_reviewed_spec` は `build_schedule` と schedule hash だけを検査する (`s8b_oracle_spec.py:123-137`)。`build_schedule` は複数 block を許し (`s8b_oracle_manifest.py:221-270`)、exact 1 検査は未呼出しの `_validate_schedule` にしかない (`:278-305`)。  
   **設計補完案・未確認:** install 前に `_validate_schedule(schedule)` 相当を必須化し、spec 層でも `:302-305` を発火させる。

2. **fixed parent の生成規則が未確定。** 現在 `output/s8b-oracle-spec/` 自体が存在しない。参照 writer は fixed candidate prefix だけを作成可能にする (`s8b_oracle_manifest.py:926-942`)。  
   **設計補完案・未確認:** spec writer も `output/` と fixed `s8b-oracle-spec/` だけを no-follow で生成し、任意 subdirectory を許可しないことを明記する。

3. **file:line の陳腐化のみで意味は一致する箇所がある。**
   - `_assert_user_commit`: `producer-design.md:26-29` の `:537,:1113,:1128,:1143,:1156` は現 HEAD では `s8b_ratified_freeze.py:538,1114,1129,1144,1157`。
   - spec の single-load: `producer-design.md:44-47` の driver `:1213-1237` は現 HEAD では `s8b_oracle_driver.py:1242-1266`。
   - marker と binding 比較: `producer-design.md:142-143` の `:1333-1345,:1440-1448` は現 HEAD では `s8b_oracle_driver.py:1362-1380,1462-1474`。marker が先という所見自体は一致。

## B. contract test を「承認済み 1 件」形へ改訂する設計

### 受理集合の署名

設計案・未実装・未確認。`NS(D)` は `D` 配下の全 entry を no-follow `lstat` で再帰列挙した集合とし、directory 不存在は空集合と同一視する。regular file だけでなく directory、symlink、broken symlink、FIFO、socket も数える。

```text
accept(
    pin: None | lower_sha256,
    spec_ns: NS("output/s8b-oracle-spec"),
    candidate_ns: NS("output/s8b-oracle-manifest-candidates"),
    authority: None | AuthenticatedApproval
) -> bool

U :=
    pin = None
    ∧ spec_ns = ∅
    ∧ candidate_ns = ∅
    ∧ authority = None

A(B, P, R) :=
    verify_external_authority(R) = true
    ∧ R.path = "output/s8b-oracle-spec/reviewed_spec.json"
    ∧ R.sha256 = P
    ∧ pin = P
    ∧ spec_ns = {
         ("reviewed_spec.json", type=regular-no-follow, bytes=B)
       }
    ∧ sha256(B) = P
    ∧ B = strict canonical UTF-8 JSON bytes
    ∧ validate_reviewed_spec(B) succeeds
    ∧ _validate_schedule(regenerated_schedule) succeeds
    ∧ candidate_ns = ∅

X := { U } ∪ { A(B, P, R) }
accept(...) ⇔ state ∈ X
```

したがって現行受理集合 `X0={U}` に対し、**0 件状態 `X0 ⊊ X`**。広がるのは authenticated approval に束縛された fixed-path regular file exact 1 件だけである。

### 各検査の担保箇所

| 検査 | 担保 |
|---|---|
| fixed path と code pin | `s8b_oracle_spec.py:18-23,182-200` |
| pin と file bytes の一致 | `s8b_oracle_spec.py:196-200` |
| strict parse、canonical bytes、全 spec validator | `s8b_oracle_spec.py:258-275` |
| exact 1 block | 新たに `s8b_oracle_manifest.py:278-305` を明示発火。現状は未接続 |
| namespace exactness | `test_s8b_oracle_manifest_contract.py:130-146` を no-follow 全 entry 比較へ置換。現行 `:137-142` の `is_file()` 限定では不足 |
| 独立 approval authority | 新設が必要。現状不在であり `docs/decisions.md:15565-15587` がその限界を固定 |
| candidate 0 件 | 同じ改訂箇所で `candidate_ns == ∅` を独立 assertion にする |

### 通る正例

形だけの正例であり、実際の承認ではない。

- authenticated authority `R` が `P = 6f587f7772612d97f03334a23ea4e5b1a0bc99465f3db8fa25d812300a8899a3` を署名済み。
- `APPROVED_SPEC_SHA256 == P`。
- `output/s8b-oracle-spec/reviewed_spec.json` の bytes は exact `PIN_GATE_SPEC_RAW` (`orchestrator/tests/test_s8b_oracle_manifest.py:61-100`)。
- spec directory の entry はこの regular file 1 件だけ。
- candidate directory は空または不存在。
- 同 bytes が現在の loader を通ることは `orchestrator/tests/test_s8b_oracle_manifest.py:1078-1099` の既存 fixture が静的に示す。

この値は test golden であって、ユーザー承認済み spec ではない。

### 落ちる負例

| 負例 | 状態 | 落とす検査 |
|---|---|---|
| pin `None` なのに file がある | `pin=None`, spec exact 1, candidate 0 | `U` の namespace 条件。loader も `s8b_oracle_spec.py:184-185` で拒否 |
| file SHA が pin と不一致 | `pin=P`, `sha256(B)=Q`, `P≠Q` | `s8b_oracle_spec.py:196-199` |
| 同 directory に想定外 entry | reviewed spec に加え `notes.txt`、empty dir、symlink、FIFO のいずれか | 新しい no-follow `spec_ns` 完全一致 |
| 2 directory 間が矛盾 | pin/spec が未承認状態なのに candidate 1 件、または approved spec と candidate が同時存在 | `candidate_ns == ∅` |
| pin と file が一致するが authority が無い | 実装者が file と pin を同時更新 | `verify_external_authority(R)` |
| 複数 block の canonical spec | loader の現行検査だけなら通りうる | 新たに発火させる `_validate_schedule` の `s8b_oracle_manifest.py:302-305` |

### 恒真化を避ける方法

`expected = APPROVED_SPEC_SHA256` として `sha256(file) == expected` だけを検査してはならない。fixture が行う「file を書き、その hash を monkeypatch する」形 (`orchestrator/tests/s8b_oracle_spec_fixture.py:102-112`) は unit test には使えても durable approval authority にはならない。

設計案・未確認では、順序を次に固定する。

1. repo 外 trust root で authenticated approval `R` を検証する。
2. `expected = R.sha256` とする。
3. `APPROVED_SPEC_SHA256 == expected` を検査する。
4. `sha256(file bytes) == expected` を別に検査する。
5. bytes の内容を再導出検証する。

test-local literal も同じ実装者が変更できるため、それ単独では人間承認を機械強制しない。外部 trust root が決まらない限り、正例 branch は有効化せず `U` のみを緑に保つ。

### manifest candidate の lifecycle

**spec と同じ lifecycle にはしない。**

- reviewed spec は fixed path と approval pin を持つ (`s8b_oracle_spec.py:18-23`)。
- candidate は caller 指定 path を candidate root 配下で受ける (`s8b_oracle_manifest.py:882-892`)。fixed canonical leaf も独立 pin もない。
- candidate は active ratified freeze と approved spec の両方から後段で生成される (`s8b_oracle_manifest.py:1170-1232`)。人間承認対象そのものではない。

したがって今回の `X` では candidate は 0 件のまま固定する。将来 candidate を許可する場合は、canonical leaf、exact 1 件、active freeze SHA、approved snapshot、`verify_manifest` (`s8b_oracle_manifest.py:991-1138`) を束縛した別の受理集合 `Y` として、改めて受理集合拡大の裁定を要する。

## C. 事前登録値候補と決定者

### `n=8` 根拠への攻撃

実測上、M4 と P1/P2 は `n` の導出根拠にならない。

1. a12 の `J` は別 study の cluster 数である。統計量定義は `output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:686-704`、選択規則は同 `:738-750`。さらに `J` は a10 が pilot から決めると明記される (`:795-797`)。8b oracle の `build_schedule.n` と同一視する一次資料はない。
2. M4 の「U は J とともに単調増加」は実測 artifact と不一致。`stress-check-simulation.json:1` の cells には、例えば W1/H が `J=9: 0.0016691623` から `J=10: 0.0016291211` へ低下し、W2/G も `J=12: 0.0039004393` から `J=13: 0.0038125182` へ低下する。
3. `q(J)/sqrt(J)` は `J=8` の `1.4842` から `J=13` の `0.9569` まで下がり続ける。事前固定された elbow 規則はなく、「8 以降で平坦」は未確認の評価判断。
4. floor の `n_sessions=8` は floor session 数 (`s8b_approved.py:21-23,51-53`)。oracle `n` は完全ブロック replicate 数 (`s8b_oracle_manifest.py:221-270`) であり、数値一致だけでは継承できない。
5. `n=8` の有効な根拠として残るのは費用見積りだけ。12 cell、`reps=5`、`extime=5`、1 round なら driver の reservation 式 (`s8b_oracle_driver.py:1382-1392`) は 2400 秒。ただし wall time・検出力は未確認。

結論として `n=8` は導出値ではなく、ユーザーが費用と未整備の検出力根拠を見て選ぶ AI 草案である。

| 項目 | 候補値 | 導出根拠 (file:line または実測 artifact) | 決定者 = ユーザー承認 / validator 固定 / freeze 継承 / 本走目的依存 / 導出不能 |
|---|---|---|---|
| `n` | `8`。AI 草案・未承認。validator の実際の範囲は正整数一般 | `s8b_oracle_manifest.py:221-239`。40 分は同 `:243-263` と driver `:1382-1392` からの静的算出。検出力は未確認 | **ユーザー承認** |
| `master_seed` | 承認手番で逐語固定する ISO-8601 JST。形の例 `"2026-08-15T00:00:00+09:00"`。実値は未確認 | validator は非空文字列のみ (`s8b_oracle_manifest.py:211-228`)。ISO 形式は floor artifact の `"2026-07-18T17:16:12+09:00"` という先例だけで、oracle の必須形式ではない | **ユーザー承認** |
| block ID | `"b0"`。AI 草案・未承認 | block ID は非空文字列 (`s8b_oracle_manifest.py:232-237`)。exact 1 block は `:302-305` | **ユーザー承認** |
| `block_sizes` | `{"b0":8}` | exact 1 block と `sum(block_sizes)==n` (`s8b_oracle_manifest.py:302-307`) から、`n=8` と block ID 固定後は一意 | **validator 固定** |
| `campaign_ids` | `{"b0":"s8b-oracle-v2-b0-t987"}`。AI 草案・未承認。repo 全体の衝突は未確認 | block と一対一、値重複なし (`s8b_oracle_spec.py:147-158`)。global uniqueness validator は当該箇所にない | **ユーザー承認** |
| `holdout_ids` | `["rr20","rr80"]` | 実測 artifact `output/s8b-freeze/holdout_freeze.json:40-306,307-599`。spec は sorted freeze 全集合を要求 (`s8b_oracle_manifest.py:1192-1201`) | **freeze 継承** |
| `configuration_ids` | `["backoff_fixed_best","ident_all","p2_2_flag_opt","sort_best","stock_common","system_gate"]` | 実測 artifact `holdout_freeze.json:119-268,386-550`。sort と各 holdout の完全一致は `s8b_oracle_manifest.py:1202-1213` | **freeze 継承** |
| `generator_versions` | 下記 5 組 | key/path は `s8b_oracle_manifest.py:53-62`、実 byte hash 検査は `:430-470`。HEAD `330f67d0` で `sha256sum` 実測 | **validator 固定** |
| `binding_identity` | 12 entry の shape まで確定。`entry_sha256`、genome、token、variant、binding SHA の実値は導出不能 | schema は `s8b_oracle_manifest.py:63-66,487-537`。導出は `s8b_materialization.py:98-146`。`LaunchValidatedFreeze.binaries_by_cell` は `s8b_ratified_freeze.py:766-778`。active v2 世代 file は実測で不存在 | **導出不能**。前提成立後は freeze 継承 |
| run contract: fixed 5 値 | `verify="legacy+s2"`, `screening="off"`, `bench_max_rounds=1`, `reps=5`, `extime=5` | `s8b_oracle_manifest.py:396-427`、`s8b_experiment_numbers.py:14-15` | **validator 固定** |
| run contract: `env_tag` | `"pegasus"` 候補。active v2 不在のため最終値は未確認 | floor protocol 実測 artifactは `pegasus`。runtime は active freeze と一致を要求 (`s8b_oracle_driver.py:862-869`) | **freeze 継承** |
| run contract: `clocks`, `contract_sha256` | `2100`, `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` | registry `env_contract.py:245-260`、active authority `env_contract_activations/00000001.json:1`、runtime 完全一致 `s8b_oracle_driver.py:870-889` | **validator 固定** |
| run contract: `ccbench_pin` | 旧 floor protocol 継承なら `d706650cdb31e442bef45b9b4216951d4fb40969`。current gitlink で floor を再測定するなら `511c9538e4e8efa54b45cda62e72389ed3b706ec` | 前者は `floor_protocol.json` 実測、後者は `s8b_approved.py:65-67` と `git ls-tree HEAD external/ccbench` 実測。binary record との一致は `s8b_oracle_driver.py:929-958` | **本走目的依存** |

現 HEAD で実測した `generator_versions` は次のとおり。

```text
artifacts:
  path = orchestrator/campaign/s8b_oracle_artifacts.py
  sha256 = b29f3dd6d989044a39f568f9e3621d93a66101b038e9a1913c3500c5e522f614
judge:
  path = orchestrator/campaign/s8b_oracle_judge.py
  sha256 = 6e90a77532e7ea68c14c2076268e38783180c6c142d23ed9ae7d09466201a0b2
materializer:
  path = orchestrator/campaign/s1_direct_comparison.py
  sha256 = 38ed8790807e3f1aa7516fd286b365dfe2dc45c18f05fb4566970a587db75e7f
outcome_stage_contract:
  path = orchestrator/campaign/s8b_outcome_stage_contract.py
  sha256 = f8a0bb2237dcaf3c643a78c04ca6b8cea2a8f83e3d306d85c781716b165c73af
report:
  path = orchestrator/campaign/s8b_oracle_report.py
  sha256 = cc28c86074aead3747eadcaaf1a09a2eaf4bdaae0ca72cca4a9d4f32bfd5acbf
```

表外だが `allowed_excluded_reasons` も spec の必須 field (`s8b_oracle_spec.py:25-34,171-177`) である。oracle 用の値は validator 固定されておらず、未確認・未承認のままなので、上表だけでは exact reviewed spec を完成できない。

## 総括

- A: 設置手順の意味は概ね一致するが、line anchor の陳腐化、単一 block 検査、fixed parent 作成規則に差分がある。
- B: 新受理集合は `X={未承認 0 件}∪{外部 authority に束縛された spec exact 1 件}`。candidate は別 lifecycle とする。
- C: 軸・generator・固定 run 値は導出可能だが、binding は導出不能。`n`・seed・campaign はユーザー選択、ccbench pin は本走目的依存。
- 倒した前提は M4 の U 単調増加、P1/P2 の `a12.J = oracle n`、および pin と file だけで「承認済み」を判定できるという P6 の暗黙前提。