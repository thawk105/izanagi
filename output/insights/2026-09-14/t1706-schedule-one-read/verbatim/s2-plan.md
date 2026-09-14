## 修正プラン

行番号は確認した現行ファイルのもの。編集対象は production と対応テストの 2 ファイルだけとし、docs・commit は扱わない。

### 共通 helper — `tools/codex_reasoning_ab.py:8971`、`:9033` 直後

**descriptor 検査と JSON 解析の順序を保ち、取得済み bytes を渡す。**

1. `:9033` の `_artifact_path` 終了後に姉妹 helper を追加する。

   ```python
   def _artifact_path_with_bytes(
       manifest_path: Path,
       descriptor: Any,
       label: str,
       *,
       root: Path | None = None,
   ) -> tuple[Path, bytes]:
   ```

   `_artifact_path` の既存検査を同じ順序・rc・reason で実装し、読み取り部分だけ次の形にする。

   ```python
   data = path.read_bytes()
   actual_sha = _sha256(data)
   # 既存と同じ expected_sha 比較
   return path, data
   ```

   元の `_artifact_path` は変更しない。姉妹 helper から元の helper を呼ぶ実装も、再読になるため不可。

2. `:8971` の JSON loader に取得済み bytes を受け取る省略可能引数を追加する。

   ```python
   def _load_json_object(
       path: Path, *, data: bytes | None = None
   ) -> dict[str, Any]:
   ```

   `:8973` だけを以下へ変更する。

   ```python
   value = json.loads(path.read_bytes() if data is None else data)
   ```

   `except`、非 object 判定、rc、reason はそのまま残す。既存 caller の変更は不要で、引数省略時の動作も変わらない。`b""` を再読扱いしないよう、判定は必ず `is None` とする。

これは「bytes 返し helper 1 個の追加＋既存 parser の局所拡張」であり、全 caller の移行を伴わない。既存の `_load_json_object_with_sha256` を使うと、descriptor 照合前に JSON 解析を行う構成になりやすく、拒否理由の優先順位が変わるため採用しない。

### `supervise_pair` — `tools/codex_reasoning_ab.py:7632`

`:7632–7637` の source 読み取り、既存 frozen との比較、新規 frozen への書き込みは維持する。`:7638–7639` を置き換える。

```python
schedule_sha = _sha256(source_schedule_bytes)
schedule = _load_json_object(
    frozen_schedule, data=source_schedule_bytes
)
```

| 現行 read | 効いている検査・用途 | 修正後 |
|---|---|---|
| `:7632` source | frozen に保存・比較する原 bytes | 維持し、SHA と解析の共通入力にもする |
| `:7634` frozen | source との完全一致。相違時 `run-root schedule bytes changed`／`RC_ROUTING` | 維持 |
| `:7638` frozen | launch／ledger へ渡す schedule SHA | source の取得済み bytes から計算 |
| `:7639` frozen、loader 内 | JSON object 判定、manifest digest、schedule 検証 | 同じ source bytes を解析。エラー表示の path は引き続き frozen |

`:7641` 以降の manifest digest、`:7647` の schedule 検証、block・snapshot・prompt 検査は変更しない。

**新規 run は source 1 read、既存 run は source 1 read＋frozen 比較 1 readになる。** 「総 read 数を常に 1」にすると既存の一致検査を失うため、ここで一本化するのは SHA／解析の根拠となる観測である。

再 serialize せず元 bytes を `write_bytes` するので、非攻撃時の frozen 内容と `schedule_sha256` は変わらない。

### `_replay_manifest` — `tools/codex_reasoning_ab.py:11137`

`:11137–11138` を置き換える。

```python
schedule_path, schedule_bytes = _artifact_path_with_bytes(
    manifest_path, manifest.get("schedule"), "schedule"
)
schedule = _load_json_object(schedule_path, data=schedule_bytes)
```

`:11152` を置き換える。

```python
schedule_sha = _sha256(schedule_bytes)
```

| 現行 read | 効いている検査・用途 | 修正後 |
|---|---|---|
| `:11137` → `:9024` | descriptor SHA の照合 | 姉妹 helper が取得した bytes で同じ照合 |
| `:11138` → `:8973` | JSON object、task manifest digest、schedule 検証 | helper が返した同じ bytes を解析 |
| `:11152` | `manifest.schedule_sha256` 比較、後続の launch SHA 比較 | 同じ bytes の SHA を使用 |

以下もそのまま残す。

- `:11148` の `_ValidatedScheduleSlots` への descriptor／material digest 情報設定。
- `:11153` の `manifest schedule_sha256 mismatch`。
- `:11162` の supervisor-frozen path 検査。
- `:11364` の mtime 検査と `:11366` の launch SHA 比較。

SHA 計算の重複は許容する。ファイルの再読をなくすことが本件の目的である。

### `make_packets` — `tools/codex_reasoning_ab.py:11700`

ファイル descriptor 枝の `:11700–11703` を置き換える。

```python
schedule_path, schedule_bytes = _artifact_path_with_bytes(
    manifest_path.resolve(), schedule_descriptor, "schedule"
)
schedule = _load_json_object(schedule_path, data=schedule_bytes)
```

| 現行 read | 効いている検査・用途 | 修正後 |
|---|---|---|
| `:11700` → `:9024` | descriptor SHA の照合 | 姉妹 helper の取得 bytes で照合 |
| `:11703` → `:8973` | JSON object、manifest digest、schedule／cardinality／slot 集合検査 | 同じ取得 bytes を解析 |

`:11697` の **Mapping かつ `slots` を持つ inline 枝**と、descriptor なしの旧 packet-only 枝は変更しない。`:11710` の legacy view、価格、cardinality、slot 集合の検査も維持する。

### 拒否動作を保つ条件

姉妹 helper では以下の順序を厳守する。

1. descriptor が `dict`。
2. path の解決。
3. 指定された場合の root 包含。
4. SHA が長さ 64 の文字列。
5. read の `OSError`。
6. SHA 不一致。
7. JSON 解析と object 判定。
8. 各入口の既存検査。

SHA の文字種検査、UTF-8 限定、duplicate-key 拒否、canonical JSON 強制などは追加しない。現行の `json.loads(bytes)` の受理範囲を維持する。

## 負例テストの設計

全 nodeid の prefix は `orchestrator/tests/test_codex_reasoning_ab.py::`。

### 差し替えの発火方法

依存関数を stub せず、**`sys.settrace` で実関数の実行境界を観測し、実ファイルを A→B→A と書き換える**。

- supervisor：`supervise_pair` 直下で schedule の `_sha256` が正常 return した瞬間に frozen を B へ変更。
- replay／packets：`label == "schedule"` の `_artifact_path` または新姉妹 helper が正常 return した瞬間に B へ変更。ここでは descriptor SHA 照合が実際に完了している。
- 対象 schedule の `_load_json_object` が正常 return した瞬間に A を復元する。
- replay の既存 freshness 検査を別原因で落とさないよう、保存した mtime も復元する。
- code object、呼出元、対象 path で限定し、発火回数を assert する。trace は `finally` で元へ戻す。

関数の戻り値・引数を変更しない。read 回数の観測も trace で行い、read 自体は本物を実行する。

### 1. supervisor：不正 A を正当 B で検証させる窓

Nodeid 案：

```text
test_supervise_pair_schedule_swap_restore_keeps_hashed_bytes[fresh]
test_supervise_pair_schedule_swap_restore_keeps_hashed_bytes[existing-frozen]
```

再利用：

- `benchmark_snapshots`（`:861`）
- `_schedule`（`:739`）
- `_make_fake_codex`（`:344`）、`_make_executable`（`:338`）
- `_supervisor_pair`（`:1271`）の呼出設定

手順：

1. `_schedule` が生成する正当 schedule を B とする。
2. B の 2 行目の `slot_id` を `s01` にしたものを A とする。他の値は変更しない。
3. source に A を保存。既存 frozen ケースでは frozen にも A を置き、空の attempt ledger を用意する。
4. SHA 計算直後に frozen を B に差し替え、JSON loader の return 後に A を戻す。
5. 実際の `supervise_pair(..., dry_run=True)` を通す。

修正後は `RC_ROUTING`、`duplicate slot_id: s01` で拒否し、launch receipt を生成しないことを確認する。旧コードでは B が検証されて実際の dry-run pair が進むため、この拒否 assertion が失敗する。

既存 frozen ケースでは、source／frozen 一致比較を通過したことも確認する。

### 2. replay：SHA が A のまま B の slots が返ることを検出

Nodeid 案：

```text
test_replay_manifest_schedule_swap_restore_returns_hashed_slots
```

再利用：

- `_full_manifest`（`:1678`）
- `benchmark_snapshots`
- `_full_manifest(..., memoize_construction_snapshots=False)` とし、snapshot 検証も実関数を使う。

手順：

1. 完全な実験 fixture の frozen schedule を A とする。
2. B は A の先頭 slot に未知の補助 field、例えば `observation_marker: "replacement"` を加えたものとする。
3. descriptor 照合後に B、JSON loader の return 後に A と mtime を復元する。
4. 実際の `_replay_manifest` の返した slots と reasons を調べる。

この field は現行の `dict(slot)` による正規化（`:3041`、`:3060`）と検証時のコピー（`:9354`）に残る。一方、既存の routing dimensions は変えない。

修正後の期待：

- replay の reasons が空。
- 戻された slots は非攻撃時の A の replay と一致。
- replacement marker が存在しない。
- descriptor 検査から schedule 解析までの対象 read は 1 回。

旧コードでは B の marker が実際の戻り値に残るため落ちる。これは read 数だけのテストではなく、**SHA に対応しない B の内容が replay に受理されたことを直接検出する**。価格・model を変更した場合の最終 certified 通過までを、このテストで実証したとは主張しない。

### 3. packets：不正 A が正当 B にすり替わって公開される窓

Nodeid 案：

```text
test_make_packets_schedule_swap_restore_rejects_hashed_invalid_schedule
```

再利用：

- `_bound_packet_manifest`（`:15029`、`leak_literal=False`）
- `_canonical`（`:180`）、`_descriptor`（`:200`）

手順：

1. fixture の正当 schedule を B とする。
2. supervisor テスト同様、2 行目の `slot_id` を重複させた A を保存する。
3. packet source の schedule descriptor を **A の SHA** に更新する。attempts は B の正当な集合を維持する。
4. descriptor 照合後に B、JSON loader return 後に A を復元する。
5. 実際の `make_packets` を通す。

修正後は `RC_AGGREGATE`、`duplicate slot_id: s01` で拒否し、packet directory／custodian root が作られないことを確認する。旧コードでは B の検証・slot 集合照合が通り、packet が生成されるため落ちる。

### 互換性確認

新規テストで、以下も固定する。既存期待値は変更しない。

- descriptor 不正・read 失敗・SHA 不一致・malformed JSON・非 object の rc／reason と優先順位。
- 非 canonical な空白・末尾改行を持つ正当 schedule の frozen bytes と SHA。
- 既存 frozen が source と異なる場合の元の拒否。
- packets の inline descriptor は schedule ファイルを読まない。
- legacy schema 省略、all-null、bound price の既存動作。

### 影響を受けうる既存テストの静的列挙

以下はすべて `orchestrator/tests/test_codex_reasoning_ab.py` の **テスト定義開始行**。直接呼出しに加え、fixture 経由、CLI、parameterized entrypoint を含む。

| 系統 | 定義開始行 |
|---|---|
| supervisor／直接の fixture 利用 | `8952`, `8983`, `12308`, `12334`, `13558` |
| replay／verify／aggregate | `9007`, `9121`, `9187`, `9213`, `9239`, `9284`, `9587`, `9713`, `9881`, `13590` |
| CLI・profile・slice 経由 | `9839`, `10080`, `10145`, `14194`, `14223`, `14256`, `14294`, `14318`, `14352`, `14390`, `14441` |
| adjudication fixture／replay 接続 | `14472`, `14550`, `14593`, `14639` |
| packets と後続の freeze／reveal | `13611`, `13687`, `14678`, `14734`, `14804`, `14845`, `14957`, `15095`, `15117`, `15137`, `15203`, `15222`, `16887` |

特に `:9587`、`:9713` は `_artifact_path` を観測する既存テストなので、新 helper への切替後も snapshot artifact の観測対象が維持されることを確認する。

## 取り残しの証明

production を AST 解析した結果、`_validate_schedule` の `Name` 参照は以下の **3 件のみ**だった。alias への代入・別関数への引渡しはなかった。

| 呼出元 | 行 |
|---|---:|
| `supervise_pair` | `7647` |
| `_replay_manifest` | `11145` |
| `make_packets` | `11711` |

これに加え、schedule 関連参照と `read_bytes`／`read_text`／JSON loader／artifact resolver の箇所を調べ、次の経路を確認した。

```text
CLI supervise-pair :12519 ──────────────→ supervise_pair
CLI verify :12588付近 → verify_manifest :11610 → _replay_manifest
CLI aggregate :12581付近 → aggregate_manifest :11654
                                      └→ verify_manifest → _replay_manifest
CLI make-packets :12595 ───────────────→ make_packets
```

- `--schedule` は `:12299` で `Path` として受け取り、CLI 内では読まず supervisor へ渡す。
- `normalize_schedule`、`normalize_legacy_schedule`、`expected_schedule_from_manifest` は渡された mapping／rows を処理する。別の schedule ファイルを読む入口ではない。
- `_supervise_one` は schedule SHA を引数で受け取る。schedule ファイルを読んで再検証する経路ではない。
- replay の `:11364` は metadata の `stat` であり、schedule 本文の第四の読み取りではない。
- `tools`／`orchestrator` の検索では別モジュールにも同名 `_validate_schedule` があったが、それぞれ独立した定義で、本件の関数への追加呼出しではなかった。

したがって、**本 production の schedule ファイル取込・検証経路は指定された 3 入口で全数**。ただし、packets 内にはファイルを使わない inline schedule 経路もあるため、「schedule の処理方法も全部で 3 通り」とは言わない。

## 親 brief への反論

- **P1-a：賛成。** 今回必要なのは hash と解析の入力同一性。読み取り後の immutable bytes を共有すれば成立し、descriptor の保持や inode 固定は不要。
- **P1-b：条件付き賛成。** 新規 frozen の書込み後に再読せず source bytes を authority にしてよい。ただし、既存 frozen と source の bytes 比較は必ず残す。
- **P1-c：結論は確認できたが、元の根拠は不十分。** validator の呼出数だけでは、validator を経由しない読込経路を除外できない。今回、I/O 箇所と CLI dispatch も確認して補強した。
- **P1-d：「3 入口だけが使う」は修正が必要。** descriptor を持つ replay／packets の 2 入口が姉妹 helper を使い、supervisor は直接取得した source bytes を使う。supervisor 用に人工的な descriptor を作る必要はない。
- **P1-e：読取不整合の存在には賛成、影響の断定には留保。** 別 bytes を hash／validation に使える構造は確認できた。ただし、model・price・slot 集合の任意変更が他の ledger／launch／adjudication 検査まで通ることは、複数 read の存在だけでは証明できない。負例で実証した範囲と最終 certified 判定への影響を分けて報告すべき。

## 総括

- 提案は姉妹 helper 1 個、JSON loader の省略可能 bytes 引数、3 入口の局所置換。
- SHA／解析は同じ取得 bytes に統一し、既存 frozen 一致検査は残す。
- descriptor・JSON・schedule の検査順序、rc、reason、非攻撃時の出力 bytes を維持する。
- 負例は実ファイルの A→B→A 差し替えと実関数で発火させる。
- 本 production の検証経路は AST・I/O・CLI の確認で 3 入口と確認した。
- ファイル編集・pytest 実行はしていない。旧コードでの失敗と修正後の成功は親での実測事項。