# [T-293] ユーザー裁定パッケージ — 共有 policy `perf_candidates` をどうするか

本 wave は**実測だけを行い、恒久対応は実装していない**。恒久対応は identity (受理集合) の変更に
あたるため D96 手続であり、ユーザー裁定へ返す。実測値の詳細は同 dir の `README.md`。

## 裁定してほしいこと

**T-126 qualification の submit 経路が壊れている状態を、どう直すか (あるいは直さないか)。**

## 前提が変わった (裁定の土台)

T-293 の起票文は「`perf_candidates` が stale で、指す 2 本の perf はログインノードに存在しない」
だった。**この前提は実測で覆った。** 破綻は 3 因の重なりである。

| # | 原因 | 実測 |
|---|---|---|
| 1 | 候補 path が**ログインノードには無い** | login は `101/136/173`、候補は `135/100` |
| 2 | 候補 path は**計算ノードには在り動くが、symlink** なので `_executable` が拒否する | `is_symlink: true`、`version` と smoke は rc=0、実物 `_executable` は `resolved: false` |
| 3 | `prepare_toolchain` は **perf に到達しない**。`gcc-13` が両サイトに無く `cc` で落ちる | `failure_stage: "cc"` |

**したがって `perf_candidates` の値を書き換えても、3 因のうち 1 つも解けない。**
値を変えれば凍結証拠 2 テストが赤になり identity も変わるため、**代償だけを払うことになる。**

## 値を変えた場合の具体的な代償 (再掲・実測済み)

- `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` と
  `test_shared_pegasus_policy_owns_no_t126_qualification_keys` の **2 node が赤**になる
  (D115 が request `876519` で実測。本 wave でも同じ pin を静的に確認)。
- `tools/pegasus/policy.json` は `REQUIRED_CODE_IDENTITY_PATHS` に入るため、
  **T-126 の series identity (受理集合) が変わる。**
- 本 wave を通じて policy の sha256 は `b1c42e49…961ac` のまま**不変**である。

## 択一

### (a) 何もしない — サイト依存性と 3 因を記録だけして閉じる

- **利点:** 凍結 bytes も identity も動かさない。D115 決定 (2) と完全に整合する。
- **欠点:** T-126 qualification は動かないままである。ただし
  **`toolchain-manifest.json` / `submission-intent.json` / `series-identity.json` は repo 内に 0 件**で、
  この経路は一度も完走した実績がない。**現時点の実損は 0。**
- **成果物影響:** なし。

### (b) `_executable` の symlink 拒否を見直す (原因 2 だけを直す)

- 現状 `_executable` は `not Path(found).is_symlink()` を要求し、その後 `resolve(strict=True)` で
  実体へ解決している。**実体へ解決するなら symlink 候補を拒む必要があるのか**を再検討する。
  shell 側は既に `[[ -x ]]` で symlink を通しており、**Python と shell で受理集合が違うこと自体が欠陥**である。
- **利点:** policy bytes を変えずに原因 2 が消える。両経路の受理集合が揃う。
- **欠点:** **受理集合の変更そのもの**なので D96 手続。symlink 拒否は「path を pin したつもりが
  差し替えられる」ことへの防御でもありうるため、その意図を確認せずに緩めてはいけない
  (規律 2: 正しさゲートを緩める変異を許さない)。
- **成果物影響:** perf の identity 記録が「symlink の実体」になる点は現状と同じ (`resolve` 済み)。
  受理する候補集合が広がる。

### (c) submit 前処理を計算ノードへ移す (原因 1 だけを直す)

- **利点:** policy も候補列も変えない。必要な実行資源がある場所で解決する。
- **欠点:** **原因 2 と 3 が残るので単独では動かない。** series identity を「submit 時点」でなく
  「job 開始時点」で決めることになり D96 手続にあたる。
- **成果物影響:** identity の確定時点が変わる。

### (d) `gcc-13` / `g++-13` の入手を先に決める (原因 3)

- 両サイトに無い以上、原因 1 と 2 を直しても `prepare_toolchain` は `cc` で止まる。
  module 提供の有無、site への導入可否、あるいは `cc` 候補列の見直しを**先に**決める必要がある。
- **これが最上流である。** (b) と (c) を先にやっても qualification は動かない。

### (e) `perf_candidates` の値を広げる — **本 wave は推奨しない**

- 実測は「値は計算ノードでは正しい」を支持しており、この案は**覆った前提の上に立つ**。
- 凍結証拠 2 テストを赤にし identity を変える代償を払って、**3 因のうち 1 つも解けない。**

## 親の推奨

**(a) を既定とし、着手するなら (d) → (b) の順で裁定する。**

理由は 3 つである。(i) 現時点の実損が 0 である (この経路は一度も完走していない)。
(ii) 最上流は compiler の不在 (原因 3) であり、そこを決めずに下流を直しても動かない。
(iii) 原因 2 (Python と shell で受理集合が食い違う) は**それ自体が独立した欠陥**であり、
T-293 の枠を超えて他の consumer にも影響しうるので、別 ID で扱う価値がある。

**(e) は採らないことを推奨する。**

## 併せて記録した新事実 (裁定不要、参考)

- 計算ノードの既定 `python3` は Intel oneAPI 版 (3.10 未満) であり、bare `python3` で
  orchestrator を import できない。既存の正規手順 (`t126_qualification.sh:13-25` の版検査ループ、
  `dispatch_compute._INTERPRETER_CANDIDATES`) を使えば回避できる。本 wave の probe はこれを踏んだ。
- `perf_event_paranoid` は login が `4`、計算ノードが `0`。
