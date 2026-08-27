---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1981-holdout-oneshot-removal
seq: 1
---

## {{D:measurement-generation-replaces-cell-oneshot}}. 予約の一回性は測定世代へ置き換える — 効果 key は座標として残す

**決定 (D1124 の実装):** 過去の観測を理由に予約を拒否する関門を撤去し、
**予約ごとに発行する測定世代 (measurement generation)** へ置き換える。

1. **cell の効果 key は不変のまま残す。** `freeze_sha256` / `freeze_holdout_key` /
   `configuration_id` / `ccbench_pin` / `env_tag` / `observation_role` の 6 field で、
   D434 のとおり protocol hash を含めない。key は**座標**であって予約の可否を決めない。
2. **測定世代 ID は決定的に導出する。**
   `sha256({observation_role, campaign_run_id})` だけを入力とし、時刻・乱数・PID・host・
   絶対 path・環境変数を含めない。`campaign_run_id` は fresh では開始時刻と protocol hash から
   作られ、resume では元 run と同じ値になるため、**resume は自動的に同じ世代へ戻り、
   別 run は必ず別世代になる。**
3. **`O_EXCL` と attempt 一回性を世代の内側へ限定する。** 同一世代の同一 attempt の
   二重消費は引き続き拒否する。別世代からは同じ論理 attempt を消費できる。
4. **名前空間を分ける。** 新世代は `measurement-generation-claims/` と
   `measurement-generation-consumed/` へ書き、旧 `claims/` / `consumed/` と混ぜない。
   旧 v1/v2 の exact reader は **read-only の historical decoder として温存**する。
5. **承認 flag を撤去する。** 不可逆な消費が無くなるので承認すべき対象が無い。

**理由:**

- **乱数発行では 3 つが同時に壊れる。** 実測で確認した — 成果物の決定性テストが落ち、
  resume が元の世代へ戻れず、世代 claim の `O_EXCL` が通常経路で衝突しないため恒真になる。
  決定的導出はこの 3 つを同時に解き、**`O_EXCL` を実際に発火する防壁へ戻す。**
- **旧 reader を消すと proof chain の受理集合が狭まる。** ratified 側の consumer は
  選択済み floor source の bytes を live inspector で再検証する。台帳には旧 claim 36 件・
  marker 228 件・ledger 36 行が現存しており、読めなくすることは撤去ではなく破壊である。
- **識別子は namespace 付きにする** (D197)。無修飾の `generation` は既に却下されており、
  同 repo に `activation_generation` が実在する。

**この決定が変えないもの:** 同一世代の attempt 二重消費の拒否、resume の run identity 照合、
未知 `observation_role` の fail-closed 拒否、freeze 由来 signature の exact 集合一致、
gflags 型意味論と間接 flag 拒否、保護比率の admission 要求、canonical JSON bytes 検査。
**正しさゲート (規律 2) と観測者効果の分離 (規律 1) には触れていない。**

**却下した選択肢:**

- **拒否する 1 行だけを外す** — finalize 側の効果 key 一意化と旧 claim の run identity 照合でも
  止まる。さらに台帳には旧 attempt marker が 96 件あり、予約が通っても最初の attempt 消費で
  同じ inode に当たる。実測で棄却した。
- **attempt 一回性ごと撤去する** — 同一世代の二重実行を許すことになる。
  D1124 が撤去を命じたのは測定の反復を拒否する関門であって、二重実行の防壁ではない。
- **旧 claim を新予約で再利用する** — 旧 claim は `campaign_run_id`・`run_relpath`・mode・
  protocol・attempt 集合まで含むため、別 run が再利用すると identity 照合と矛盾する。
- **世代 ID を乱数で発行する** — 上記のとおり決定性・resume・防壁の 3 つを同時に壊す。

## {{D:oracle-npilot-identifier-removal-deferred}}. R33 事前登録が pin する file の identifier 撤去は見送り、裁定へ返す

**決定:** `--confirm-irreversible-pilot-holdout` の identifier 撤去のうち、
`orchestrator/campaign/s8b_oracle_n_pilot.py`、`tools/pegasus/oracle_n_pilot.sh`、
`tools/pegasus/submit_oracle_n_pilot.sh` からの撤去は**行わず、ユーザー裁定へ返す**。
承認**要求**そのものは admission 側で撤去済みであり、これらに残るのは
**何も gate しない引数**である。True でも False でも admission の挙動が exact に同じであることを
テストで固定した。

**理由:**

- R33 事前登録 protocol が `source.driver_sha256` と `source.job_script_sha256` で
  前 2 file の bytes を pin しており、**現在の bytes と exact に一致している**。
- **R33 campaign は未実行である** (共有台帳に該当 role の claim が 0 件)。
  したがってこの pin は歴史記録ではなく、これから走る campaign への生きた束縛である。
- 1 byte でも変えると `load_inputs()` が hash 不一致で拒否し、回復には
  **successor 事前登録の発行**が要る。事前登録の再発行は D1124 が命じていない新しい設計行為であり、
  事前登録という機構の趣旨からしてユーザー裁定に属する。

**却下した選択肢:**

- **既存 protocol の pin を書き換える** — 事前登録文書の上書きであり、事前登録の意味が消える。
- **successor 事前登録を wave の判断で発行する** — 上記のとおりユーザー裁定事項である。
- **admission 側の引数を消して呼び手を壊す** — pin 対象 file の編集を強制する。
