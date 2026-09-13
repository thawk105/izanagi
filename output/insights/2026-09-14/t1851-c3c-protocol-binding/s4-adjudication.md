# 段 4 裁定 — [T-1851] / [T-1946] / [T-2107] 単位 C3c

親が段 3 の 2 本 (レンズ A = 受理集合と正しさ防壁、レンズ B = 閉包と consumer 取り残し) の所見を
real / refuted に裁定し、plan v2 と変異事前登録を確定した。所見はすべて親が現物で裏取りしている。

## 所見の裁定

| # | 所見 | 裁定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | path validator の受理集合が versioned 命名規則ぶん広がる。brief の「受理集合は広がらない」は成立しない | **real (中)** | 採用。**plan より狭い是正へ変更** (下記 裁定 1) | 内 |
| A-2 | legacy entry を自己 hash にすると恒真化する | **refuted** | 文言だけ採用 (下記 裁定 2) | 内 |
| A-3 | versioned を chain から bounded へ移すと被覆が失われる | **refuted** | 不採用 | 内 |
| A-4 | 「hold が結果を 1 bit も変えない」は条件付きでしか真でない | **real (中)** | 採用 (下記 裁定 3) | 内 |
| A-5 | 2 つの負例は先行 bytes gate に必ず遮られる | **refuted** | 「対照は 2 回の scan 両方へ適用」だけ採用 | 内 |
| A-6 | 実測 1 構成の値を versioned 全構成へ一般化している | **real (中)** | 採用 (下記 裁定 4) | 内 |
| B-1 | 新規 nodeid の所要台帳登録が plan から抜けている | **real (中)** | 採用 (下記 裁定 5) | 内 |
| B-2 | 「既存テストへの影響の全列挙」が consumer 全体を覆っていない | **real (中)** | 採用 (下記 裁定 6) | 内 |
| B-3 | brief のアンカー表に範囲漏れと説明の混同がある | **real (低)** | 採用 (下記 裁定 7) | 内 |
| B-4 | job body に legacy 固定 path の読み残しがある | **refuted** | 不採用。親も独立に確認した | 内 |
| B-5 | 既存期待値の強制置換は 0 件という plan の主張 | **維持** | `T:875` の keyword 追加と `T:8053` の `None` stub への配慮を必須条件に付す | 内 |

**scope 外の real 所見は 0 件。** 両レンズとも attempt registry の slot 一意性、B2 inspector の
被覆全単射照合、本番共有 root の fixture 残存、official 投入へ広げる根拠は無いと結論した。
したがって裁定パッケージでユーザーへ返す項目は無い。

### 親が現物で裏取りした点

- `_validate_freeze_allowlist_path` (`C:5407-5411`) は `_PREFLIGHT_FIXED_FILES` と
  `selector-runs/` 以外を「有界範囲外」で拒否する。versioned path は現行では allowlist key に
  できない。**A-1 の前提は正しい。**
- `captured[legacy] == historical_protocol` (`C:5278`) を回避して `C:5347` の return へ到達する
  分岐は無い。**A-2 は refuted。**
- `tools/pegasus/floor_campaign.sh:1177` が `resolve-current-protocol` を呼び、`:1219` で
  `--protocol "$REPO_ROOT/$PROTOCOL_PATH"` を渡す。`:1236,1274-1277` も同じ選択 path を読む。
  **B-4 は refuted。shell の変更は不要。**
- `orchestrator/tests/test_s8b_protocol_builder.py:1606-1641` は `clean_scan_digest(root,
  freeze_allowlist={})` を呼ぶ。`test_clean_scan_accepts_exact_versioned_protocol_chain_record` と
  `test_clean_scan_rejects_overbroad_versioned_protocol_names` の 2 件は、新 keyword の既定が
  `None` である限り期待値を変えずに緑を維持する。
- `_require_supplied_protocol_authority` の stub は `orchestrator/tests/test_s8b_floor_campaign.py:8053`
  の 1 件だけで、`mode="pilot"` である。official 分岐には到達しない。
- 所要台帳の 90% 被覆 gate は
  `orchestrator/tests/test_acceptance_schedule_order.py:660-713` に実在する。**B-1 は real。**
- 段 4 直前の裁定 inbox 再走査: local main は wave 開始後 `f5423e2ff` → `75bea8e5f` へ 1 commit 進んだ
  (T-1525 の docs spool)。裁定の変更は無く、本 wave の前提を覆す新事実も無い。

## 裁定 1 — 受理する path は resolved path の exact 1 件だけにする

plan は `_validate_freeze_allowlist_path()` の有界範囲へ versioned protocol の**命名規則**を
加える案だった。これは allowlist key として受理する path を族ごと広げるので採らない。

**採る形 (署名で書く):**

```
_validate_freeze_allowlist_path(rel: object, *, protocol_relpath: str | None = None) -> str
    rel in _PREFLIGHT_FIXED_FILES
    or rel.startswith(_SELECTOR_RUNS_REL + "/")
    or (protocol_relpath is not None and rel == protocol_relpath)   # ← 追加はこの 1 項だけ
    以外は「有界範囲外」で拒否する。
```

```
_assert_freeze_allowlist(root, freeze_allowlist, *, protocol_relpath: str | None = None)
    bounded_actual へ入れるのは
      rel in _PREFLIGHT_FIXED_FILES
      or rel.startswith(_SELECTOR_RUNS_REL + "/")
      or (protocol_relpath is not None and rel == protocol_relpath)
    それ以外で _CHAIN_RECORD_PATTERNS に一致するものは従来どおり chain_records へ落とす。
```

```
clean_scan_digest(root, *, freeze_allowlist, protocol_relpath: str | None = None) -> str
_official_launch_preflight(root, *, ..., protocol_relpath: str | None = None)
    どちらも受け取った値を下位へ中継するだけとし、自分では導出しない。
```

**禁止 (これを満たさない実装は採らない):**

- 命名規則・正規表現・prefix 一致で allowlist key を受理してはならない。exact 文字列一致だけ。
- `protocol_relpath` を関数内で resolver から導出してはならない。呼び手が渡した値だけを使う。
- 既定 `None` の挙動を変えてはならない。`None` のとき受理集合は現行と 1 bit も違わない。

**通る正例 1 つ:** `protocol_relpath` に resolver が返した
`output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json` を渡し、その file の実 bytes の
sha256 を allowlist へ載せた official preflight は、certificate 発行まで到達する。

これで A-1 が指摘した受理差分は「resolver の権威 (`_require_supplied_protocol_authority` と
`_scan_floor_protocol_index_at_commit` の bytes 一致検査) が既に固定した 1 path」に縮む。
**同じ族の他の path は現行どおり allowlist key として拒否される。** その拒否が残ることを
テストで示す (下記 N3)。

## 裁定 2 — legacy entry の保証は「独立検証」と書かない

`allowlist[legacy]` の期待値は `sha256(captured[legacy])` にする。**これを「legacy bytes を
独立に検証する」とは書かない。** 書くのは次の 1 文である。

> legacy entry は、`pre_oracle_head` の Git blob と一致することを直前に検査した bytes を、
> その後の 2 回の clean scan へ束縛する。capture 前から存在する改竄はこの entry ではなく
> `historical_protocol` 比較が拒否する。

`sha256(historical_protocol)` を期待値にする案は、必須の `C:5278` 比較が残る限り受理条件が
同じなので、検査強化として数えない。権威の出所が読みやすくなる利点だけであり、
**本 wave では採らない** (本題以外の変更を増やさない)。

## 裁定 3 — hold の結論は限定文で書く

D1936 項 11 は「hold 機構全体の効力を証明したとは書かない」と命じている。成果物へ書くのは次に限る。

> capture と scan の間で bytes が不変な fresh official 経路では、この hold の有無で最終受理可否は
> 変わらない。停止位置・marker・bytes が途中で変わる時系列、および hold 機構全体の効力は
> 本 wave の証明対象外である。

`HELD = False` は 21 件の check 全体に作用するので、この局所読解から全体の挙動を結論しない。
hold の解除、`HELD_CHECK_IDS` の変更、hold の射程拡大はいずれも行わない。

## 裁定 4 — 実測値と一般式を分ける

`2c8cf9be…` / `261cec1c…` / 「差は `ccbench_pin` 1 field」は **2026-09-14 に観測した 1 構成の値**で
あり、versioned 全構成の性質ではない。versioned の導出は `contract_sha256` と `ccbench_pin` の
両方を置換しうる (`C:1002-1008`)。一般説明では `H_legacy` / `H_resolved` を使う。

digest 不変性の主張は前提を列挙してからでなければ書かない。前提は
(i) 同一 repository 列挙、(ii) 他 file と chain bytes が同一、(iii) allowlist の値が同一、
(iv) schema と直列化が同一、(v) 旧版・新版の双方が正常到達、の 5 つである。
**修正前の versioned 構成は検査で停止するので、比較できる旧 digest は存在しない。**

## 裁定 5 — 新規 nodeid は所要台帳へ登録する

新規テストは既存 file `orchestrator/tests/test_s8b_floor_campaign.py` へ足す。したがって
新規 test file を理由とする自走 harness・file 集合メタテストの追加要件は発生しない
(`T:15311-15312` の既存 harness が拾う)。

一方 `test_acceptance_schedule_order.py:660-713` の 90% 被覆 gate は collection の分母が増えると
影響を受けるので、**親が受入の成功 JUnit から
`python3 tools/update_acceptance_duration_ledger.py --add-only` で登録する**工程を段 6 に置く。
0.0 の placeholder を書かない。未実測秒を合成しない。

## 裁定 6 — consumer 検証範囲

焦点走の対象へ次を必ず含める。名前の推測ではなく参照関係で引いた集合である。

- `orchestrator/tests/test_s8b_floor_campaign.py` — 直接 preflight 呼出し 10 関数、
  clean scan 12 関数、保存関数経由 1 関数 (`T:11784`)、seam 経由 (`T:802,6897,10170,10245,12492,13430,13460`)
- `orchestrator/tests/test_s8b_protocol_builder.py` — `_clean_scan_with_isolated_repository_search`
  経由の 2 関数 (`:1617`, `:1626`)
- `orchestrator/tests/test_s8b_ratified_freeze.py:1036,1062,988`
- `orchestrator/tests/test_s8b_ratified_verify.py:2197,2209,2212,2216`
- `orchestrator/tests/test_pegasus_floor_tools.py:1373,1380-1393` (source アンカー検査)
- `orchestrator/tests/test_s8b_launch_cert.py`、`orchestrator/tests/test_s8b_freeze_io.py:531`
- `orchestrator/tests/test_frozen_artifacts.py`

## 裁定 7 — brief のアンカー表を訂正する

- `:5285-5292` → **`:5293`** (journal `expected_header.protocol_sha256` の実行行)
- `orchestrator/tests/test_s8b_floor_campaign.py:11550-11700` → **`:11538-11718`**
- アンカー表は 22 行ではなく **21 行**
- 「変更面は 1 file 1 関数に閉じる」→ **同一 file 内の複数関数への配線変更** (wrapper / core /
  preflight / validator / scan / digest / 官製 preflight)。実装子は 1 本のままとする。
- `test_frozen_artifacts.py:48,97,123` の説明 → `:48-49` は bytes の sha256 pin、`:97` は keyset、
  `:123` は held 分類。3 者とも bytes 比較をするわけではない。

## plan v2 (確定)

`C` = `orchestrator/campaign/s8b_floor_campaign.py`、`T` = `orchestrator/tests/test_s8b_floor_campaign.py`。

1. `C:7213-7216` — `_require_supplied_protocol_authority()` の戻り値を保持し、`_run_campaign_core` へ
   内部 keyword `_protocol_authority` (既定 `None`) で渡す。戻り値型は変えない。
   **`None` を無条件に deref しない** (`T:8053` の stub は `None` を返し `mode="pilot"` で通る)。
2. `C:7233-7243` — core に `_protocol_authority=None` を追加。既存の直接呼出しは既定で従来どおり。
3. `C:7507-7516` — official 分岐で `_protocol_authority` が `None` なら fail-closed で拒否する
   (official は必ず公開 wrapper 経由で record を持つ)。`None` でなければ `.path` を
   `protocol_relpath` として preflight へ渡す。
4. `C:5201-5204` — `protocol_relpath: str | None = None` を追加。`None` のとき
   `_FLOOR_PROTOCOL_REL` を実効値とする。
5. `C:5219-5231` — capture 集合を `_PREFLIGHT_FIXED_FILES ∪ {実効 protocol path}` にする。
   追加 path も既存の symlink / regular file 検査と `_read_bytes` を通す。実効値が legacy なら
   重複読取りしない。
6. `C:5245` — hold 配下の比較対象を `captured[実効 protocol path]` にする。比較の強度と hold 分岐は変えない。
7. `C:5313-5318` — `allowlist[legacy] = sha256(captured[legacy])`、
   `allowlist[実効 protocol path] = protocol_sha256`。両者が同じ path なら 1 entry に畳む
   (`protocol_sha256` を採る)。
8. `C:5388-5412` — 裁定 1 の署名。exact 一致だけ追加する。
9. `C:5415-5470` — 裁定 1 の署名。`bounded_actual` の分類に exact 一致を追加する。
10. `C:5492-5530` — 裁定 1 の署名。`protocol_relpath` を `_assert_freeze_allowlist` へ中継する。
    digest の schema (`s8b-clean-scan-digest/v3`) と preimage の構成は変えない。
11. `C:5588-5604` — `protocol_relpath` を受け、**2 回の `clean_scan_digest` 呼出しの両方**へ渡す。
12. `C:5274-5280` の `historical_protocol` 比較と `C:5293` の journal header は**現状維持**。
13. `T:875-878` — `_fixture_floor_preflight` に `protocol_relpath=None` を追加。戻り値は変えない。
14. docstring (`C:5493-5500` ほか) を実装へ合わせる。既存の逐語 pin は無い (レンズ B が別検索で確認)。

**変えないもの:** `_PREFLIGHT_FIXED_FILES` の既存メンバー、`_CHAIN_RECORD_PATTERNS`、
digest schema、`build_launch_certificate` の field、`freeze_verification_hold` の全体、
凍結 23 件の bytes、`FORMULA_ID`、result schema の既定、`launch_floor_attempt()` /
`launch_probed_floor_attempt()` の署名と挙動、shell (`tools/pegasus/*`)。

## テスト計画 (確定 5 nodeid)

接頭辞は `orchestrator/tests/test_s8b_floor_campaign.py::`。

| id | nodeid | 構成と期待 |
|---|---|---|
| P1 | `test_public_official_preflight_accepts_versioned_protocol` | 隔離 repo で実 resolver が versioned を選ぶ。公開入口・実 preflight・実 `_assert_freeze_allowlist` を通し certificate 発行まで到達する。legacy entry は `H_legacy`、resolved entry は `H_resolved` を持つ。digest は独立に構成した preimage と一致する |
| P2 | `test_public_official_preflight_accepts_legacy_protocol` | 同じ経路で resolver が legacy を選ぶ。protocol entry は 1 件で、allowlist と digest は現行と同じ |
| N1 | `test_public_official_preflight_rejects_resolved_protocol_byte_drift` | 実 authority 検証の **return 後**に resolved bytes を 1 byte 変える。`launch certificate: freeze allowlist hash 不一致: <resolved path>` で拒否する |
| N2 | `test_public_official_preflight_rejects_legacy_byte_drift_after_capture` | 実 preflight の **return 後** (`C:5278` より後) に legacy bytes を 1 byte 変える。`launch certificate: freeze allowlist hash 不一致: <legacy path>` で拒否する |
| N3 | `test_freeze_allowlist_path_rejects_unselected_versioned_protocol` | `protocol_relpath` に resolved path を渡した状態で、**別の** versioned 命名規則 path を allowlist key に載せる。「有界範囲外」で拒否する。resolver が選んだ path だけが受理されることを示す |

**負例の帰属条件 (実装後に確認する):**

- N1 は `C:984-988` と `C:7161` の bytes 一致検査より後に注入する。
- N2 は `C:5278` より後、`C:5593` より前に注入する。
- 対象比較を外した対照は **`C:5593` と `C:5603` の両 scan に適用する。** 1 回目だけ外すと
  2 回目が拒否するので帰属が立たない。
- fixture が `C:5506-5508` の検索 gate で赤なら、その走行は対象 gate の実績に数えない。

## 変異事前登録 (DW-M01、実装前登録)

| # | 変異位置 | 変異内容 | 期待失敗 nodeid |
|---|---|---|---|
| M1 | `C:7507-7516` | preflight へ渡す path を常に `_FLOOR_PROTOCOL_REL` へ戻す | P1 |
| M2 | `C:5313-5318` | legacy entry を削除し resolved entry への単純置換にする | P1 |
| M3 | `C:5388-5412` | exact 一致を versioned 命名規則の pattern 一致へ緩める | N3 |
| M4 | `C:5313-5318` | resolved entry の期待値を `protocol_sha256` から `sha256(captured[resolved])` へ変える | N1 |
| M5 | `C:5471-5482` | legacy entry の hash 比較だけを省略する | N2 |
| M6 | `C:5455-5462` | `protocol_relpath` の exact 分類を無効化し、常に chain へ落とす | P1 |

**単一理由性 (F820) は実装後に各変異で確認する。** 同じ入力を拒否する層が前後・内側にも
無いことを確かめ、確かめられない変異は登録から外して実効 gate へ再照準する。
本 wave は受理集合を exact 1 path ぶん広げるので、**M3 が承認外の過剰受理を捕まえる正例**にあたる。
hang 変異は無い。

## 段 5 の分割

実装子 1 本。所有 path は `orchestrator/campaign/s8b_floor_campaign.py` と
`orchestrator/tests/test_s8b_floor_campaign.py` の 2 file だけ。docs・commit・変異・受入は親が担う。
