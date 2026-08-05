# 段 4 裁定 — [T-419] U-2 chain / [T-478] 案 A′

両レンズが独立に **NO-GO** を出し、しかも結論が一致した (A′-3 の型 gate は権限になっていない /
resolver の production 利用 0 件 / scope をさらに縮めよ)。親はこれを **real として全面採用**し、
scope を縮小して plan v2 を確定する。

## 親 brief の訂正 (レンズ A nit、real)

「方式 α は未実装」は広すぎた。K=5・走行 CPU rotation・論理 CPU ごとの累積最小は
`tools/pegasus/probes/t419_probe_causality.py:301-350,4012-4053` に既に実装されている。
正しくは **「production attestation (`env_attestation.probe()`) への方式 α 結線が未実装」**。
同 probe は `:3800-3804` で non-certifying / counterfactual-only と自己宣言しているので、
U-2 の entry condition が未成立である結論は変わらない。

## 所見の裁定

### real・採用・scope 内 (plan v2 に反映)

| # | 所見 | 裁定 |
|---|---|---|
| A-1 / B-1 | `CurrentContract` は public dataclass で再包装により偽造でき、`type(...) is CurrentContract` は生成権限を証明しない | **real。型 wrapper と issuer 型 gate を本 wave から全面撤去する** |
| A-3 / B-3 | history resolver の production 利用 0 件なので元の破断は解消しない | **real。brief の成果物影響主張を「data-layer preparation」まで縮める** (B の表現を採用) |
| A-4 | successor が「同一 path のまま SHA だけ変更」を通し、g1 の calibration bytes を失わせる | **real・採用。「path が変わらないなら SHA も変わってはならない」を predicate に入れる** |
| A-5 / B-6 | 世代列が g1 一本なので production の隣接検査は一度も発火せず、初期化から predicate 呼出しを削除する変異が生存する | **real・採用。validator を候補 mapping を引数に取る純関数へ分離し、synthetic 2 世代で正例・負例・結線削除を kill する。加えて「本 wave では production 発火不能」と明記する** |
| B-5 | `lookup()` 削除は s8c の反射依存を壊す | **real・採用。親が独立に裏取り済み** (`s8c_preregistration_evidence.py:591-593` が関数名 `lookup` と call の実在を AST で要求、凍結 evidence contract v1 の `reachable_from` が `env_contract.lookup` を参照)。**`lookup()` は削除しない** |
| B-9 | 子 A / 子 B の所有分離が成立していない | **real・採用。consumer 移行が消えたので実装子は 1 本にする** |
| A-P1 opt.2 / B-2 | `REGISTRY = 列末尾` は未 activation の g2 を自動 current 化し、設計正本の「直接追加した calibration は activation 不能」と矛盾する | **real・採用。bootstrap fuse `len(sequence) == 1` を production 初期化に置き、活性化権限 wave が来るまで g2 の追加を fail-closed にする** |
| B-8 | `attestation_mode="none"` の env では successor の calibration を loader が読めない | **real・採用。predicate は generic のまま、loader 制約を pin するテストを置く** |

### real だが scope 外 (段 9 で裁定パッケージへ返す。実装しない)

| 所見 | 返す理由 |
|---|---|
| A-2 / B-4 `run_campaign(env_contract=None)` の legacy 迂回で certified が出る | A′-6 (campaign identity) と同じ wave の所有。単独で塞ぐと受理集合を承認外に縮める |
| A′-4 activation record / A′-5 全入口 activation receipt | 対で入れる必要があり、本 wave の 3 倍規模 |
| A′-6 campaign identity への contract hash 束縛 (D13 改訂) | 凍結 layout / WAL に触る。新 D が要る |
| A′-7 versioned predicate dispatch | `historically_verified` の本体。resolver の consumer 結線はここが正本 |
| A′-8 `floor_campaign.sh` wrapper 結線 | shell 層。Python gate の手前 |
| A′-9 の残り (bundle role / 非空 cardinality / literal trust root) | activation bundle が存在して初めて意味を持つ |
| staging resolver、historical retention、T-126 closure、8c/P3 prereg 下流 | 設計正本 §6.2 / §8 が別扱いとしたもの |
| A-8 禁止 literal 集合への calibration path/SHA 追加 | `env_attestation.py` の `GRANDFATHERED_V1_SHA256` と絡み、単独 wave が要る |

### 不採用

なし。refuted に落とした所見はない。

## plan v2 (この wave が実装するもの)

**型 wrapper なし・consumer 移行なし・`lookup()` 温存**。`ExecutionEnvironmentContract` と
`_canonical_obj()` は 1 文字も変えない。

1. **`GENERATIONS`** — `Mapping[str, tuple[ExecutionEnvironmentContract, ...]]`。
   env 固有 literal は `_build_registry` の単一 FunctionDef 内に留め、免除 region を増やさない。
   `MappingProxyType` で公開し、生 backing dict を module 属性に残さない。
2. **`GenerationEntry`** — `(generation: int, contract: ExecutionEnvironmentContract)` の
   frozen dataclass。**これは data であって権限ではない**。issuer 型 gate には使わない。
3. **`resolve_by_contract_sha256(sha, *, expected_env_tag=None) -> GenerationEntry`** —
   malformed / 未知 / 非一意 / env 不一致を `EnvContractError`。
4. **`is_valid_successor(pred, succ) -> bool`** — `_canonical_obj()` の leaf-level JSON Pointer
   差分が非空かつ `{"/calibration_ref/path", "/calibration_ref/sha256"}` の部分集合であること。
   **加えて A-4 の追加条件**: path が同一なら SHA も同一でなければならない
   (= path と SHA は対で動く)。
5. **`validate_generations(mapping) -> None`** — **候補 mapping を引数に取る純関数**。
   非空 exact tuple / `generation` の `1..N` 連番 / key と `env_tag` の一致 /
   全 env・全世代を通じた `contract_sha256` の一意性 / 隣接世代が `is_valid_successor` /
   **bootstrap fuse `len(sequence) == 1`**。fuse の拒否 message は活性化権限が未実装である旨を書く。
6. **`REGISTRY` / `lookup()`** — 現行の意味のまま。ただし `REGISTRY` は `GENERATIONS` から
   導出し (fuse により各列は 1 本なので一意)、literal の二重定義を作らない。
   **production の 21 呼び出しは 1 箇所も触らない。**

## 変異事前登録 (DW-M01)

単一理由性を確認したうえで次を登録する。いずれも「同じ入力を拒否する層が前後に無い」ことを
実装後にコードで確認し、確認できなければ登録を取り下げて実効 gate へ再照準する。

| ID | 位置 | 無効化の内容 | 期待 |
|---|---|---|---|
| M1 | `validate_generations` の隣接検査 | `is_valid_successor` 呼出しを削除する | KILLED (synthetic 2 世代の負例テスト。g1-only データでは死なないので純関数側で撃つ) |
| M2 | `is_valid_successor` の可変 pointer 集合 | `/attestation_mode` を許可集合へ足す | KILLED |
| M3 | `is_valid_successor` の path/SHA 対条件 | 「path 同一なら SHA 同一」の条件を削除する | KILLED |
| M4 | `validate_generations` の bootstrap fuse | `len(sequence) == 1` を落とす | KILLED |
| M5 | `resolve_by_contract_sha256` の index | 全世代でなく current だけから index を作る | KILLED (synthetic 2 世代で非 current g1 を引く) |
| M6 | `validate_generations` の hash 一意性検査 | 一意性検査を削除する | KILLED |
| M7 | `GENERATIONS` の独立 golden | `EXPECTED_GENERATION_HASHES` の pegasus 値を 1 文字変える | KILLED |
| M8 (正例) | — | 変異なしの baseline | PASSED (承認外の過剰拒否がないこと) |

受理集合は縮小しない (production の呼び出しを 1 件も変えないため)。よって過剰拒否の正例は
M8 の baseline 全走で足りる。

## 成果物影響 (DW-G05)

- **実装した場合の受理集合の変化: なし。** `lookup()` / `REGISTRY` / 21 consumer が不変で、
  g1 の `contract_sha256` (pegasus `e576e9cd…` / linux-baremetal `1b2ee853…`) も不変。
- **実装しない場合:** 新較正 g2 を登録する wave が、世代という受け皿の無いまま
  `_build_registry` の calibration pin を上書きする経路しか持たない。それは設計正本 §4.2 が
  禁じた「旧 evidence の binding を新 SHA へ貼り替える」操作そのもので、
  過去の certified 選択・floor protocol・oracle manifest の proof chain が
  「解決不能」になる (T-478 §1)。本 wave はその受け皿と、活性化権限が入るまでの
  fail-closed fuse を先に置く。
- **本 wave が「実装済み」と数えないもの (レンズ要求):** A′-2 の隣接検査は
  **production 世代列では一度も発火しない** (全 env が 1 世代)。純関数として検査可能なだけである。
  A′-3 の型による権限分離は**本 wave では実装しない**。history resolver は
  production consumer を持たない **data layer の準備**である。
