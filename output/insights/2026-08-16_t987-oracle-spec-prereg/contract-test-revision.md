# contract test を「承認済み 1 件」形へ改訂する設計 — [T-987]

**本 wave では実装しない。** 承認後の別タスクのための設計である。
実測基準 = local main 330f67d0。pytest は非実走 (段 2・段 3 は read-only sandbox)。

## 1. 現状の受理集合

`orchestrator/tests/test_s8b_oracle_manifest_contract.py` の
`test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec` は、
`output/s8b-oracle-manifest-candidates` と `output/s8b-oracle-spec` の 2 directory を
`rglob("*")` で走査し、`is_file()` が真になる path が 1 件でもあれば赤にする。
directory が存在しなければ走査を飛ばす。pin も authority も一切見ない。

```
X0 = { 2 directory 配下の is_file() path が 0 件である状態 }
```

このテストは `APPROVED_SPEC_SHA256 = None` (`orchestrator/campaign/s8b_oracle_spec.py:23`) と
対になった「schema version 据え置きの前提」の見張りである。

## 2. 改訂の骨子 — pin 状態で分岐する 2 状態

分岐の入力は `s8b_oracle_spec.APPROVED_SPEC_SHA256` **ただ 1 つ**とする。
第 3 の状態を作らない。

```
S0 (未承認):  APPROVED_SPEC_SHA256 is None
S1 (承認済み): APPROVED_SPEC_SHA256 が 64 桁 lowercase hex
それ以外の非 None 値 (空文字・大文字・63/65 桁・非 hex・非 str) は無条件で赤
```

`APPROVED_SPEC_SHA256` が `None` である限り、**受理集合は 1 byte も広がらない。**
これが規律 2 に対する本設計の中核的な性質である。

## 3. 案は 2 つある — 拡大だけの案と、縮小を伴う案

段 3 レンズ A が「no-follow 全 entry 比較への置換は、拡大と同時に**縮小**を含む」と指摘した。
現行 `is_file()` 走査では受理されている次の状態が、全 entry 比較では拒否される。

- 空の下位 directory、空の hidden directory、空の `__pycache__`
- directory を指す symlink、broken symlink、FIFO、socket

すなわち全 entry 化を選ぶと `X0 \ X ≠ ∅` となり、新旧は包含関係でなく**交差**になる。
規律 2 が求めるのは「広げる範囲と根拠の明示」なので、未裁定の縮小を同じ変更に混ぜると
**承認された範囲が事後に判別できなくなる。** よって案を分ける。

### 案 B1 — 純拡大 (親推奨、先に行う)

走査規則は現行のまま (`rglob("*")` + `is_file()`)。pin 分岐だけを足す。

```
S0 受理 ⟺ spec_files == [] かつ candidate_files == []
S1 受理 ⟺ spec_files == ["output/s8b-oracle-spec/reviewed_spec.json"]
        かつ sha256(その file の実 bytes) == APPROVED_SPEC_SHA256
        かつ candidate_files == []

X1 = X0 ∪ { S1 受理状態 }
```

`X0 ⊊ X1` が literal に成立する。空 subdirectory や FIFO は現行同様に受理されたままで、
**現行から悪化しない。** 悪化しないことと、安全であることは別である (§6)。

### 案 B2 — 拡大 + 安全側の縮小 (別裁定)

走査を no-follow の全 entry 比較へ置換する。`lstat` で type を判定し、
regular file 以外の entry も数える。root directory 自身の type も検査する。

```
NS(D) = D 配下の全 entry を no-follow lstat で再帰列挙した集合 (D 不在は空集合)

S0 受理 ⟺ NS(spec) == ∅ かつ NS(candidate) == ∅
S1 受理 ⟺ NS(spec) == { ("reviewed_spec.json", regular, bytes=B) }
        かつ sha256(B) == APPROVED_SPEC_SHA256
        かつ NS(candidate) == ∅

X2 = { S0 受理状態 } ∪ { S1 受理状態 }   ただし X0 \ X2 ≠ ∅
```

B2 を選ぶ場合、**拡大部分と縮小部分を別々に承認する**必要がある。
加えて B2 は次を設計に含めなければならない (段 3 レンズ A の指摘)。

- root directory 自身が regular file / broken symlink / directory symlink である場合の扱い。
  root を lstat 対象に含めない実装は fail-open しうる。
- 走査中の `PermissionError` を fail-closed にすること。
- symlink root の拒否。

## 4. 落ちる負例 (最低 6 件を pin する)

| # | 状態 | 期待 | 落とす検査 |
|---|---|---|---|
| N1 | pin=None かつ `reviewed_spec.json` が存在 | 赤 | S0 の 0 件条件。loader も `s8b_oracle_spec.py:184-185` で `no-approved-spec` |
| N2 | pin=64hex かつ file の sha256 が pin と不一致 | 赤 | S1 の hash 一致条件 (`s8b_oracle_spec.py:196-199` と同型) |
| N3 | pin=64hex かつ spec directory に `reviewed_spec.json` 以外の file が同居 | 赤 | S1 の集合完全一致 |
| N4 | pin=64hex かつ spec directory が空または不在 | 赤 | S1 の集合完全一致 (**S0 へ落とさない**) |
| N5 | pin=64hex かつ candidate directory に file がある | 赤 | candidate 0 件の独立 assertion |
| N6 | pin が 64hex でない非 None 値 (`""`・大文字・63 桁・非 str) | 赤 | 第 3 の状態を作らせない |

**N4 が最も重要である。** 「pin があるのに file が無い」を S0 の 0 件条件で緑にすると、
**pin を書いた後に artifact を消すだけで検査が緑に戻る。**

B2 を採る場合は、これに加えて空 subdirectory・directory symlink・FIFO・
broken symlink の各状態を**縮小側の負例**として別に pin する。

## 5. 通る正例 — production 相当の witness でなければ数えない

段 3 レンズ A が、段 2 プランの挙げた正例
(`orchestrator/tests/test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW`) を否認した。
この golden は `configuration_ids` が 2 件しかなく、run contract も
`env_tag="test-env"` / `clocks=1800` / `ccbench_pin="pin"` である。
`validate_reviewed_spec` は freeze product を検査しないので通るが、
`build_approved_manifest` が全 configuration 集合との一致を要求して落とす
(`orchestrator/campaign/s8b_oracle_manifest.py:1192-1213`)。

**したがって正例は次を満たすものだけを数える。**

- active ratified freeze に束縛されている。
- 実 run contract (実 `env_tag` / 実 `clocks` / 実 `ccbench_pin`) を持つ。
- 全 12 cell (holdout 2 × configuration 6) の `binding_identity` を持つ。
- canonical bytes として `validate_reviewed_spec` を通る。

**現時点でこの witness は構成できない。** active ratified freeze が不在であり、
`binding_identity` の authority (`LaunchValidatedFreeze.binaries_by_cell`) が出せないためである。
よって **S1 branch は、正例が構成できるようになるまで有効化しない。**

## 6. 恒真化 — この設計が解けない限界

**危険:** テストが `APPROVED_SPEC_SHA256` を読む以上、pin と file の両方を書ける実装者にとって
S1 は「自分が書いた 2 つが一致する」ことしか証明しない。
production loader が見るのも pin と disk bytes の SHA 一致だけである
(`orchestrator/campaign/s8b_oracle_spec.py:182-200`)。
test fixture も file を書いた直後に同じ hash を monkeypatch する
(`orchestrator/tests/s8b_oracle_spec_fixture.py:102-112`)。

**これは B1 でも B2 でも解けない。** 解くには承認の trust root が要る。
親の実測では `verify_external_authority` / `AuthenticatedApproval` 相当の実装は
`orchestrator/` 配下に 0 件で、署名の trust root (`gpg.format` /
`user.signingkey` / `gpg.ssh.allowedSignersFile`) もすべて不在である。

したがって本設計が主張してよいのは次の 2 点だけである。

- **主張してよい:** 「pin と durable artifact が食い違う状態、および
  pin なしで durable artifact がある状態を機械的に拒否する」。
- **主張してはならない:** 「人間承認を機械強制した」。
  書けるのは「人間が staged diff を review した」までである。

### 恒真化を減らす書き方 (設計として明記する)

1. 期待値に現在の実 bytes hash を差し込まない。テストは
   `sha256(実 bytes) == APPROVED_SPEC_SHA256` という**関係**だけを検査し、
   どちらの値も fixture へ焼き込まない。
2. **`APPROVED_SPEC_SHA256` を monkeypatch して S0 / S1 / N1〜N6 を切り替える meta-test を
   同時に置く。** pin を触らずに S1 側を実行できないと、S1 の分岐は
   **永久に走らないまま緑**になる。これが最も起きやすい恒真化である。
3. 走査中の例外を fail-closed にする。緑の理由が「走査できなかった」になってはならない。

### staged blob 検査が未配線である

段 3 レンズ A の指摘: entry 511 の producer 設計は staged blob の検査を要求していたが、
本 contract test にはそれが配線されていない。filesystem テストからは tracked / untracked /
ignored の区別が見えないため、**untracked な `reviewed_spec.json` でも
bytes と pin が一致すれば S1 は緑になりうる。**
承認後の clone では file が無く pin だけが残り、`no-approved-spec` 系で停止する。
S1 を有効化する際は index / staged blob の検査を併せて設計すること。

## 7. `output/s8b-oracle-manifest-candidates/` を同じ契約にしない

reviewed spec は fixed path と approval pin を持つ単一の承認対象だが、
candidate manifest は `build_approved_manifest` が生成する**複数生成されうる作業物**であり、
caller 指定 path を candidate root 配下で受ける。fixed canonical leaf も独立 pin も無い。

両者に同じ「ちょうど 1 件」契約を課すと、candidate を 2 件作った時点で spec の検査まで赤になり、
逆に candidate の lifecycle を緩めると spec 側の厳しさも緩む。

**よって candidate 側は 0 件条件を維持する。** 将来 candidate を許可する場合は、
canonical leaf・exact 1 件・active freeze SHA・approved snapshot・`verify_manifest` を
束縛した別の受理集合として、**改めて受理集合拡大の裁定を要する。**

## 8. 実装しない理由 (本 wave の境界)

- 受理集合が真に広がる変更であり、規律 2 によりユーザーの明示裁定が要る。
- §6 のとおり trust root が未決のままでは、gate を広げても「承認の機械強制」にならない。
  **trust root の決定と対で裁定されるべきである。**
- §5 のとおり、正例を構成するのに必要な active ratified freeze が不在である。
