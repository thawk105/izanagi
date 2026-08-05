あなたは izanagi の開発 wave の**実装子**である。コードとテストだけを編集する。
**docs は編集しない。commit もしない。** cwd は wave の worktree である。

## 必読 (読めなければ即停止し、その旨だけを出力する)

- 裁定 (これが正本): `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s4-adjudication.md`
- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/brief.md`
- 段 2 プラン (**参考。scope は裁定が上書きしている**):
  `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md`
- `orchestrator/campaign/env_contract.py` 全文
- `orchestrator/tests/test_env_contract.py` 全文

**段 2 プランの `CurrentContract` / `HistoricalContract` / `lookup()` 削除 / consumer 21 箇所の移行は
裁定で全面撤回された。実装してはならない。** 実装するのは裁定の「plan v2」6 項目だけである。

## 実装するもの (裁定 plan v2)

`orchestrator/campaign/env_contract.py` に次を足す。**既存の
`ExecutionEnvironmentContract` / `IsolationPolicy` / `CalibrationRef` / `_canonical_obj()` /
`contract_sha256` / `lookup()` は 1 文字も変えない。**

1. `GenerationEntry` — `frozen=True` dataclass。field は `generation: int` と
   `contract: ExecutionEnvironmentContract` のちょうど 2 つ。`generation` は bool を除く正整数、
   `contract` は `type(...) is ExecutionEnvironmentContract` を要求する。
   **これは data であって権限ではない。** docstring にそう書く。
   issuer の型 gate として使う API を作らない。

2. `GENERATIONS` — `MappingProxyType` で公開する
   `Mapping[str, tuple[GenerationEntry, ...]]`。env 固有 literal (env_tag / clocks_per_us /
   numactl / calibration path / calibration sha256) は **`_build_registry` の単一 FunctionDef の
   内側にだけ**置く。`_build_generations` のような literal を持つ別関数を新設しない。
   生の backing dict を module 属性へ束縛しない (既存 `REGISTRY` と同じ規律)。

3. `is_valid_successor(predecessor, successor) -> bool` — 純関数。
   両者の `_canonical_obj()` を leaf-level の JSON Pointer へ平坦化して差分を取り、
   次を**すべて**満たすときだけ True。
   - 差分が非空である (no-op successor を拒否する)
   - 差分が `frozenset({"/calibration_ref/path", "/calibration_ref/sha256"})` の部分集合である
   - **path が変わらないなら sha256 も変わってはならない** (path と sha256 は対で動く)。
     すなわち差分が `{"/calibration_ref/sha256"}` だけの successor は False にする。
   `calibration_ref` object を丸ごと除外して比較する実装にしない (将来 field が増えたとき
   暗黙で可変化するため)。

4. `validate_generations(mapping) -> None` — **候補 mapping を引数に取る純関数**。
   module の `GENERATIONS` を直接読まない。違反は `EnvContractError`。検査する性質:
   - 各値が非空 tuple で、要素が `type(...) is GenerationEntry`
   - `generation` が各 env 内で 1..N の連番 (順序どおり)
   - mapping の key と内包 `contract.env_tag` が一致
   - `contract_sha256` が全 env・全世代を通じて一意
   - 隣接世代が `is_valid_successor(前, 後)` を満たす
   - **bootstrap fuse**: 各列の長さがちょうど 1 である。拒否 message には
     「活性化権限 (activation record / activation receipt) が未実装のため、
     2 世代目の登録を fail-closed で拒否する」旨を書く
   module 初期化時に、実際の `GENERATIONS` に対してこの関数を呼ぶ。

5. `resolve_by_contract_sha256(contract_sha256, *, expected_env_tag=None) -> GenerationEntry` —
   **全世代**から作った逆引き index を使う (current だけから作らない)。
   非 str / 64 桁小文字 hex でない / 未知 / 非一意 / `expected_env_tag` 不一致は
   `EnvContractError`。index も `MappingProxyType` で公開するか、module 属性に生 dict を残さない。

6. `REGISTRY` — `GENERATIONS` から導出する (fuse により各列は 1 本なので一意)。
   calibration pin や env 値の literal を二重定義しない。
   **`REGISTRY` の外部から見た型・内容・`lookup()` の挙動は現行と完全に同じでなければならない。**

## 絶対に変えてはならないもの

- `contract_sha256` の値。基準値は pegasus =
  `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`、linux-baremetal =
  `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`。
  `ExecutionEnvironmentContract` に field を足す・型を変える・`asdict` の受け手を変えると壊れる。
- `lookup()` の存在・関数名・シグネチャ・挙動 (`orchestrator/campaign/s8c_preregistration_evidence.py:591-593`
  が関数名 `lookup` と call の実在を AST で要求しており、凍結 evidence contract が参照している)。
- `orchestrator/campaign/` 配下の他の production module。**1 file も編集しない。**
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` (1 件のまま)、`LEGACY_CALIBRATION_ALLOWLIST`、
  `V2_ENV_NEUTRAL_MODULES` の免除 region 名と件数。
- `orchestrator/tests/test_env_contract.py` の既存 assert のうち、
  裁定と段 2 プラン §7「書き換えてはいけないもの」に挙がったもの。
- 凍結成果物 (`output/` 配下)、calibration の bytes と pin。

## 新規テスト (`orchestrator/tests/test_env_contract.py` に足す)

性質で書く。既存テストが既に覆う性質は足さない。各テストは**狙った欠陥のときだけ**落ちること。

- 独立 golden `EXPECTED_GENERATION_HASHES` (test 側が所有する literal) と `GENERATIONS` の
  exact key-set・各列非空・g1 の hash を照合する。自己申告 key-set から期待を導出しない。
- `GENERATIONS` が `MappingProxyType`、各列が tuple、生 backing dict が module 属性に無い。
- `REGISTRY` の内容が `GENERATIONS` 末尾と一致し、`lookup()` の返り値が現行 golden と同一。
- **synthetic 2 世代 mapping** に対する `validate_generations` の正例・負例。
  (production の世代列は全 env 1 本なので、隣接検査は純関数側でしか発火しない。
  この事実を test の docstring に書く。)
  負例: 連番でない / key と env_tag 不一致 / hash 重複 / 隣接が successor でない。
- `is_valid_successor` の表: no-op / path+sha 対で変更 (True) / sha だけ変更 (False) /
  path だけ変更 (False) / `attestation_mode` も変更 (False) / `clocks_per_us` も変更 (False)。
- bootstrap fuse: 2 世代の mapping が `EnvContractError` になり、message に活性化権限の語が入る。
- `resolve_by_contract_sha256`: 全 g1 hash が引ける / malformed / 未知 / 大文字 hex /
  `expected_env_tag` 不一致が拒否される。**synthetic 2 世代 index で非 current 世代が引ける**
  (current だけの index 実装を殺す)。
- **loader 制約の pin**: `attestation_mode="none"` の env で calibration を差し替えた successor は
  `is_valid_successor` を通っても `env_attestation.load_verified_calibration` が拒否する
  (`GRANDFATHERED_V1_SHA256` 由来)。この非対称を明示的に固定する。

## 検査と報告

- **pytest を実走してはならない** (login node で重い処理を走らせない規律)。
  よって**緑だと主張してはならない**。完了報告では「実装済み・未実走」と書く。
  受入全走と変異走行は親が計算ノードで行う。
- 静的には `python3 -c` 程度の import 検査もしない。編集と静的読解だけで完結させる。
- テストを甘くして通す方向 (fixture へ現行 hash を差し込む、期待件数を緩める、
  xfail 化する) は禁止。
- 期待値に working tree の hash など揮発する診断 payload を焼き込まない。
- **指示にない受理集合の拡大・縮小をしない。** scope を書く前に、
  現行の受理・拒否挙動を報告へ明記せよ。
- 完了報告に、所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙せよ。
  特に `test_env_contract.py` の既存 19 箇所の `ec.lookup()` 呼び出しに影響が出ないことを確認せよ。

## 総括

出力の末尾に `## 総括` 節を置き、変更した file と足した API・テストを 10 行以内でまとめる。
