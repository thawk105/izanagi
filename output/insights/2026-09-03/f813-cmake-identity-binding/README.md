# F813 恒久対応 — condition gate の green record へ CMake の実体と実効 configure argv を束縛する

**wave:** `dev-wave-f813-cmake-identity` / branch `worktree-dev-wave-f813-cmake-identity`
**anchor commit:** `f8694a55a` (実装統合)、`a6305047f` (段 6 fix 1)、`70edef258` (段 6 fix 2)
**計測機:** Pegasus。テスト実走は計算ノードへ dispatch。build / benchmark は行っていない。

---

## 1. この wave が主張できること

green record は、gate が実行した CMake の実 path・内容 SHA-256・stat identity・実行した
configure argv を保存する。これにより **5 つが新たに拒否される。**

1. cmake 証拠を持たない旧形式の green record (exact schema の欠落 reject)。
2. 2 つの arm が異なる CMake 実体で作られた green record。
3. 1 回の configure の前後で CMake 実体が入れ替わった走行。
4. configure argv が記録された cmake path に束縛されていない record。
5. symbol 表が空の calibration binary (`--strip-all` / `--strip-unneeded` 経路)。

## 2. この wave が主張してはいけないこと

**「F813 の穴を塞いだ」とは書けない。** 記録することと拒否することは別である。

- **安定した (自分を書き換えない) CMake wrapper は、変更後も green を返す。**
  拒否するには「承認済み CMake identity」の権威が要るが、repo に存在しない
  (`admission_registry.json` に 64hex pin ゼロ、`FROZEN_MANIFEST` に該当エントリなしを実測)。
- **保存する argv は「この gate が実行した argv」であり、wrapper の内側 argv ではない。**
  wrapper が委譲先へ渡した argv は観測していない。ただし wrapper が compile entry を
  書き換えた効果は既存の `requested_replay_argv` (compile_commands 由来) に現れる。
- **`objcopy --strip-symbol=` による狙い撃ちの symbol 除去は捕まえられない** (下記 §3 で実測)。
- CMake identity は path の before/after snapshot であり、kernel が実際に exec した image の
  attestation ではない。capture 間の swap-and-restore、capture 後の
  `compile_commands.json` 差し替えは検出しない。

限界は主張せず明記する (規律 7、D387)。

## 3. 親の strip 実測 — anchor symbol 検査を入れなかった根拠

Pegasus login node、GNU `nm` (`/usr/bin/nm`)、`gcc` で作った実行体
(`izanagi_trace_probe` と `main` を持つ) に対する実測。

| 加工 | `nm -C` の rc | stdout 行数 | `izanagi_trace` | `main` | 現行検査 |
|---|---|---|---|---|---|
| なし | 0 | 30 | 1 | 1 | 正しく検出 |
| `strip --strip-all` | 0 | **0** | 0 | 0 | **素通りしうる** |
| `strip --strip-unneeded` | 0 | **0** | 0 | 0 | **素通りしうる** |
| `strip --strip-debug` | 0 | 30 | **1** | 1 | 既存 grep が検出 |
| `objcopy --strip-symbol=izanagi_trace_probe` | 0 | 29 | 0 | **1** | **素通りしうる** |

- strip 済み binary でも **`nm` の rc は 0** である。`set -Eeuo pipefail` では止まらない。
- stderr の文言は locale 依存 (この機体では「シンボルがありません」)。**文言一致で判定してはならない。**
- **`main` は `objcopy` の狙い撃ちで残る。** したがって anchor symbol の存在検査を足しても
  この経路は捕まらない。恒真な検査を増やさないため、入れていない。
- この実測は 1 機体 1 binary である。実 `ycsb_silo.exe` で strip が成功すること、strip 前に
  trace symbol が存在することまでは証明していない。「素通りする」ではなく「**素通りしうる**」。

## 4. 受理権威と層

CMake identity の検査は 4 箇所にあるが、**受理を決めているのは record validator だけ**である。
`_arm_record` は生成した record を `require_issuer=False` で validator へ通すため、
公開 field から手組みした record にも同じ validator が適用される。

| 検査内容 | production 層 (冗長 gate) | record validator (受理権威) |
|---|---|---|
| arm 内の before/after drift | `condition_meaning_gate.py:1596` | `:3260-3262` |
| supply の requested/control 不一致 | `:1782-1785`, `:1891-1897` | `:3360-3362` |
| meaning の requested/default 不一致 | `:2964-2972` | `:3605-3608` |
| configure argv が cmake_path に束縛 | producer が構築 | `:3273-3274` |

production 層の単独変異は受理集合を変えない。kill として数えず、
diagnostic sensitivity pin として別枠に置く (`DW-M08`)。**恒真だから消してよいという意味ではない** —
fail-fast と診断の質のために残す。

## 5. 変異結果

最終 (attempt 3、`mutation-final-report.json`): **10 / 10 KILLED、期待 node 完全一致。**
MISMATCH 0、SURVIVED 0、PARSE_ERROR 0、TIMEOUT 0。

| # | 変異位置 | 殺したテスト | 単一理由 |
|---|---|---|---|
| N1 | supply validator の `required` + CMake 検証ブロック (2 点累積) | 21 件 | **否 (構造変異)** |
| N2 | supply の arm 間 identity 比較 `:3360-3362` | `test_green_supply_rejects_different_arm_cmake_identity` | 是 |
| N3 | arm 内 before/after 比較 `:3260-3262` | `test_green_supply_rejects_cmake_identity_drift_within_arm` | 是 |
| N4 | argv の cmake_path 束縛 `:3273-3274` | `test_green_supply_rejects_configure_argv_for_different_cmake_path` | 是 |
| N5 | meaning の requested/default 比較 `:3605-3608` | `test_compile_time_green_rejects_different_requested_default_cmake_identity` | 是 |
| N6 | shell の empty-symbol reject | `test_certify_trace_symbol_stage_rejects_real_empty_stripped_binary` | 是 |
| N7 | shell の `izanagi_trace` grep | `test_certify_trace_symbol_stage_rejects_real_unstripped_trace_binary` | 是 |
| N8 | `configure_argv` の `"$CMAKE_PATH"` を bare `cmake` へ | `test_certify_cmake_paths_derive_from_colon_free_job_tmpdir` | 是 |
| N9 | 両層: `:1596` + `:3260-3262` | 2 件 | 両層変異 |
| N10 | 三層: `:1782-1785` + `:1891-1897` + `:3360-3362` | `test_green_supply_rejects_different_arm_cmake_identity` | 三層変異 |

**N6 と N7 を別々のテストが殺したことが重要である。** strip 前 (trace symbol あり・symbol 表非空) と
strip 後 (symbol 表が空) の 2 段負例が、「grep を消す変異」と「empty-check を消す変異」を
分離して殺す。1 本の負例で両方を殺していたら単一理由性が壊れていた。

**N1 は過剰決定である。** CMake 証拠の契約を丸ごと削るので 21 件が赤になる。
単一理由の証拠としては使わず、個別述語の帰属は N2 / N4 / N5 が担う。

### erratum — 3 attempt の経緯 (消さずに残す)

| attempt | spec | 結果 | 何が起きたか |
|---|---|---|---|
| 1 (probe) | `mutation-spec-probe.json` | 8 killed / **1 SURVIVED** / **1 PARSE_ERROR** | 下記 (a)(b) |
| 2 | `mutation-spec-attempt2.json` | 8 KILLED / **2 MISMATCH** | 下記 (c) |
| 3 (最終) | `mutation-spec-final.json` | **10 KILLED、完全一致** | — |

- **(a) N3 が SURVIVED した。** record validator の arm 内 before/after drift 検査を無効化しても
  赤になるテストが 1 本も無かった (rc=0、199 passed、失敗ノード 0 件)。**実際の検査漏れ**であり、
  段 6 fix 2 (`70edef258`) で負例を 1 本足して塞いだ。probe が無ければ気づかなかった。
- **(b) N10 が PARSE_ERROR になった。** 親が書いた spec の span が閉じ括弧を 1 行落としており、
  `SyntaxError: unmatched ')'` で全テストが collection error になった。**コードの欠陥ではない。**
  span を修正し、spec 生成器へ「削除する span は括弧が均衡していること」の検査を足した。
  この型のバグは、放置すると全件が偽の KILLED になる。
- **(c) N1 と N9 が MISMATCH になった。** 観測 node が期待より 1 本多く、その 1 本は
  **fix 2 が probe の後に足した負例**だった。欠落はゼロで、両変異とも殺されている。
  検出力の問題ではなく、probe (fix 2 以前) の観測から期待集合を pin した登録のずれである。
  2 件の集合を訂正し、他の 8 件は 1 byte も変えずに独立な attempt 3 で完全一致を確認した。

## 6. 段 3 / 段 6 が返した所見のうち、実装しなかったもの

裁定パッケージとしてユーザーへ返す。

1. **承認済み CMake identity の権威を作り、未承認の CMake を拒否する。** §2 の穴を実際に閉じる
   唯一の道だが、登録簿・更新手順・機体差の扱いの新設が要る。
2. **`nm` の内容 hash を receipt へ束縛する。** 本 wave は絶対 path 固定と `nm.path` / `nm.version` の
   記録までで止めた。それ以上は新しい台帳項目になる。
3. **capture 後の `compile_commands.json` 差し替えと swap-and-restore の検出。**
4. **`objcopy` 狙い撃ちの symbol 除去の検出。** 名前ベースでは原理的に不可能 (§3)。
   期待 symbol 数の下限や section 単位の検査など別の手段が要る。

## 7. 検査

| 検査 | 結果 |
|---|---|
| 焦点走 (22 file、fix 前) | 1 failed / 1483 passed — 落ちたのは本 wave の正例 1 件 |
| 焦点走 (22 file、fix 後) | **1486 passed, 1 skipped, rc=0** (73.3 秒) |
| 変異 (10 件、attempt 3) | **10 KILLED、完全一致** |
| 全史 AI provenance 監査 | rc=0、7886 件、**新規違反なし** |
| baseline (実装前、2 file) | 141 passed, rc=0 — 既存赤なし |

build / benchmark / 正式測定は行っていない。本 wave は性能値を新規取得していない。
