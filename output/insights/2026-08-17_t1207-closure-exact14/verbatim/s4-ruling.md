# 段 4 裁定 + プラン v2 — [T-1207] enforcement source closure exact 14

確定: 2026-08-17 01:45 JST。親 (manager) の裁定。段 2 プラン + 段 3 レンズ A / B の全所見を処理した。

## 0. 親が撤回する自分の主張 (最重要)

**段 1 brief §7 の「certified 選択の受理集合が epoch 診断に現れずに変わる」を撤回する** (A-05 real)。

- M2 が実証したのは「`__init__.py` の 1 行で dispatch の解決先が変わる」ことと
  「exact 12 の閉包検査はそれを見ない」ことまでである。実際に差し替えた `parse_trace_dir` は
  `expected_commits` keyword を受けないので `pipeline.py:1106` の呼出しは例外になり、
  `loop.py` の abort へ落ちる。**gate の無効化 (anomaly のある run が certified になる) は
  実証していない。**
- M3 が実証したのは rejection payload の `certified` field の偽装までである。棄却判定
  (`pipeline.py:1133` の `vr.certified`) は `core.py` 由来で閉包内にあり、守られている。
  現行 consumer が abort payload の `certified` を採否に使う証拠は無い。

以後、本 wave の全文書 (新 D、worklog、テスト docstring) はこの狭い形だけを名乗る。

## 1. 所見の裁定

### 採用 (real・scope 内・実装する)

| id | 判定 | 採否 | 対応 |
|---|---|---|---|
| A-01 | real / must | 採用 | 名乗ってよい逐語を新 D に固定する (§4) |
| A-02 | real / must | 採用 (test-only) | verifier package の file 集合 census テストを新設する (§3-4) |
| A-05 | real / must | 採用 | §0 の撤回。新 D と worklog は狭い形で書く |
| A-06 | real / must | 採用 | 変異事前登録を親が作り直す (§5)。プランの表は破棄 |
| A-07 | real / should | 採用 | 新設テストの Git を config 隔離する。F357 の切り分けは §7 |
| B-02 | real / should | 採用 | 費用クラスを宣言し実測する (§6) |
| B-03 | real / should | 採用 | [T-819] の再訪条件が発火。本 wave へ相乗りさせ §5 に作法を書く |
| B-04 | real / should | 採用 | excluded scope の逐語は実 path 列挙にする (§4) |
| B-05 | real / should | 採用 | clean node に独立 `git cat-file` digest assert を足す (§3-3) |
| B-01 | real / nit | 採用 (文言のみ) | M1 の一般化範囲を「この checkout の physical `output/**/campaign.lock`」に限定して記録 |

### real だが scope 外 (実装しない・裁定パッケージへ)

| id | 内容 | 返す先 |
|---|---|---|
| A-03 | certified sink の支配点が無い (`wal.py` 直書き、`pipeline.evaluate` の COMMIT) | 新規タスク。D268/D442 の継承制限として新 D にも明記 |
| A-04 | 弱化してから作る fresh lock は 14 でも拒否しない | 同上 (D442 の継承制限。新 D で再掲) |
| A-08 / X-1208 | detached な旧 E1 が judge で受理される | [T-1208] (未裁定のまま) |
| X-1209 | T126 qualification の code identity が追随しない | [T-1209] (未裁定のまま) |
| A-09 / X-DOMAIN | 同じ `/v1` domain が 12-path grammar と 14-path grammar を指す曖昧さ | [T-1208] と同じ束へ |
| A-02 の後半 | 新 module を commit してから fresh lock を作る経路 | A-04 と同じ束 |

**却下は 0 件。** レンズの所見はすべて real と判定した。

## 2. 拘束 (変えない)

- exact 14 = 既存 12 + `orchestrator/verifier/__init__.py` + `orchestrator/verifier/report.py`。
  **既存 12 path の順序と綴りは 1 byte も変えない。新 2 path はこの順で末尾へ append。**
- hash domain `campaign-verifier-epoch/v1` は据え置き。
- `contract_loader_*` 識別子・wire key は不変。
- `orchestrator/verifier/__init__.py` と `report.py` の**実 bytes は変更しない**。
  最終 diff にこの 2 file が入っていたら事故として止める (Silo ladder の別 pin を壊す)。
- 検証の意味論・停止点・fail-closed は不変。

## 3. プラン v2 (段 2 プランからの差分だけを書く。それ以外はプランどおり)

### 3-1. 採用する編集面

段 2 プランの「完全な編集面」表をそのまま採用する。ただし次を上書きする。

- `artifact_admission.py` の scope 逐語は §4 の**逐語ちょうど**にする (プランの案は却下、B-04 を採る)。
- テストの配置はプラン §P5 の限定形を採る:
  source mutation の対照は `test_t671_source_binding.py`、旧 exact-12 wire 拒否は
  `test_campaign_lock_codec.py`、epoch 順序 / scope 逐語 / drift param は
  `test_artifact_admission.py`。全部を T671 へ集めない。

### 3-2. 発火実証テスト (対照形)

段 2 プラン §5 の設計を採用する。ただし A-06 に従い次を追加する。

- `_PRE_WAVE_ENFORCEMENT_SOURCE_PATHS` (exact 12) は**独立 literal**で持つ。
  ただし復元は必ず `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の**実オブジェクト**へ戻し、
  test literal へ戻さない。戻した後に production tuple と一致することを assert する。
- 対照 node は 2 つ (`[verifier-init-dispatch]`, `[verifier-report-payload]`)。
  各 node で **capture と live verify の双方**が exact 12 では通り exact 14 では
  `ContractLoaderBindingError` / `contract-loader-drift` / 対象 path で止まることを assert する。

### 3-3. clean 正例 (B-05)

`test_exact_fourteen_clean_closure_capture_and_live_verify` に次を足す。
tuple 一致と object identity だけでは、「capture が HEAD blob でなく現在 disk を hash する」形に
壊れていても緑になる。

- 一時 repo の各 path について、**test 側で独立に `git cat-file blob <commit>:<path>` を取り**、
  その SHA-256 が `binding.contract_loader_blob_sha256s[path]` と一致することを assert する。
- 期待 key 集合と tuple 順が独立 exact 14 literal と一致することを assert する。

### 3-4. census テスト (A-02、新設)

`orchestrator/verifier/` 直下の `.py` file 集合が exact に既知 8 件であり、そのうち
6 件が閉包 member、2 件 (`__main__.py`, `cli.py`) が意図的除外であることを assert する。

- 実装は実 package directory を走査する (合成 directory では恒真になる)。
- `__pycache__` は除外する。
- 新しい module が verifier package へ追加されたら**赤になる**こと自体がこのテストの目的である。
  赤になったら「閉包へ入れるか意図的除外か」をユーザー裁定へ返す、と docstring に書く。
- **成果物影響 (DW-G05):** 実装しないと、将来 verifier へ module を 1 つ足して
  `__init__.py` の 1 行でそれを読ませるだけで、epoch を変えずに dispatch 先を丸ごと
  差し替えられる。exact 14 でも新 module は永久に閉包外だからである。

### 3-5. Git 隔離 (A-07)

新設テストが起動する `git` は、production の `_run_git`
(`contract_loader_binding.py:257-267`) と同じ env 隔離を使うか、少なくとも
`-c core.autocrlf=false -c core.fileMode=false` と `GIT_CONFIG_GLOBAL=/dev/null`
相当を明示する。Git 不在・timeout・非ゼロ終了は infra failure として product failure と
区別できるメッセージにする。

## 4. 成果物に載る逐語 (これちょうど。1 文字も変えない)

`CAMPAIGN_VERIFIER_EPOCH_SCOPE`:

```
enforcement source closure (exact 14 path; witness gate 本体 pipeline.py、verifier dispatch __init__.py、verifier 実装 core/dsg/model/parse/report.py を含む)
```

`CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE`:

```
verifier package のうち orchestrator/verifier/__main__.py と orchestrator/verifier/cli.py、および package 外の orchestrator/verify.py の implementation bytes は束縛しない
```

新 D に載せる**名乗ってよい範囲** (A-01 を親が刈り込んだ形):

> `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が
> 実際に完了した呼出しについて、**各 path を検査が読み取ったそれぞれの時点の** enforcement
> source closure exact 14 path の disk bytes は、その呼出しが authority に採用した
> `contract_loader_commit` の同 path Git blob と一致した。
> exact 12 から増えた保証は、後続の source 検査が `orchestrator/verifier/__init__.py` と
> `orchestrator/verifier/report.py` の**記録後 drift** も拒否することに限る。
> 実行済み code object、import state / cache、fixed-list 外 module、CLI / wrapper、
> bootstrap と runtime、全 certified sink の支配、弱化してから作る fresh lock、
> cross-version の E1 認証は保証しない。

## 5. 変異事前登録 (DW-M01。段 2 プランの表は破棄し、親が作り直した)

**[T-819] の作法をここで適用する** (B-03: 再訪条件「同一ファイルを触る wave への相乗り」が発火)。
閉包 member を変異させると `contract-loader-drift` の共通核で無関係 node が広く赤くなる (F358)。
したがって:

- **変異対象は原則として閉包 member でない file に限る** (`campaign_lock.py`,
  `contract_loader_binding.py` はいずれも閉包外)。
- 閉包 member (`artifact_admission.py`) を対象にする変異は 1 件だけ登録し、
  runner を drift 非感受 node へ絞り、drift control を 1 件置く。
  drift 非感受であることを**実測で確認できなければ登録を取り下げる** (DW-M01)。

| # | 変異 | 位置 | 期待 failed node の完全集合 |
|---|---|---|---|
| M-1 | tuple から `orchestrator/verifier/__init__.py` を除く (exact 13) | `campaign_lock.py` の新 2 行 | 対照 node `[verifier-init-dispatch]` + tuple 一致 node + census node は**赤にならない** (census は package 側を見るため)。完全集合は段 6 で `--junitxml` から実測して固定する |
| M-2 | tuple から `orchestrator/verifier/report.py` を除く (exact 13) | 同上 | 同上 (`[verifier-report-payload]` 側) |
| M-3 | **両方を除く (= wave 前の実コードの形、exact 12)** | 同上 | 対照 2 node + tuple 一致 node + 旧 wire 拒否 node。**この変異の登録は必須** |
| M-4 | live verify の `disk = _read_regular_file_no_follow(...)` を `disk = blob` にする (`if disk != blob` は残るが発火不能) | `contract_loader_binding.py:355-356` | 対照 2 node の**両方** (A-06: 同一構造の 2 parameter はどちらも落ちる。singleton にしない) |
| M-5 | capture 側を `disk = blob` にする | `contract_loader_binding.py:331-332` | 対照 2 node の**両方** |
| M-6 | v2 の exact key 検査を弱め旧 exact-12 map を受理させる | `campaign_lock.py:171-184` | 新設 `test_v2_rejects_pre_wave_exact_twelve_source_blob_keys` |
| M-7 | epoch preimage の tuple を `[:-1]` にして最後の digest を落とす | `artifact_admission.py:742-745` | **閉包 member 変異。** runner を drift 非感受 node へ絞り drift control 1 件を併置する。段 6 で drift 非感受を実測してから採用する |

**正例 (過剰拒否の検出。DW-M01「受理集合を縮小する wave」に該当):**

- `test_exact_fourteen_clean_closure_capture_and_live_verify`
- `test_campaign_lock_codec.py::test_v2_exact_shape_and_canonical_encoding`
- `test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture`

**census テストの発火実証 (変異 harness では file 追加を作れないため、親が段 6 で実測する):**
使い捨て worktree で `orchestrator/verifier/_probe_new_module.py` を作り census node が赤になることを
確認し、削除して緑に戻ることを確認する。結果は変異台帳へ「file-addition firing」として記録する。

**scope 文字列だけを旧文言へ戻す変異**は受理集合を変えないため kill 対象にせず、
DW-M08 に従い diagnostic sensitivity pin として別枠に記録する。

## 6. 費用クラスの宣言 (B-02。test-time-regression-rule が要求)

- 本 wave が新設する検査の費用は **O(1)** である。対照 2 node と clean 1 node と census 1 node は、
  それぞれ一時 repo を 1 つ作るだけで、repo 履歴にも commit 数にも比例しない。
- 既存の path 単位 parameterized test は closure size N に対し **O(N^2)** である
  (N cases × N files/case)。N は repo の成長ではなく**裁定でしか動かない設計量** (8→12→14) なので
  「開発するほど遅くなる」構造ではない。ただし今回 N が 12→14 になる分の実測は必須とする。
- **基準値 (親が本 worktree・clean tree・exact 12 で実測、2026-08-17 01:44 JST):**
  `python3 tools/run_tests.py orchestrator/tests/test_t671_source_binding.py -q`
  → **51 passed / 3.19s (pytest 内部)、wall 6.02s**。
- **閾値:** 実装後の同 command が pytest 内部 **3.51s (= 3.19 × 1.1)** を超えたら、
  段 6 で `_committed_loader_repo` を module scope の共有 fixture へ変える等で O(N) へ戻す。
  戻せなければ land せず裁定へ返す。

## 7. F357 の切り分け手順 (統合 commit 前後)

本 wave は `artifact_admission.py` (閉包 member) を編集するので、**統合 commit 前**の焦点走では
`contract-loader-drift` 由来の偽赤が機械的に出る。

1. 焦点走の赤の理由行に `contract-loader-drift` があれば実装差分へ帰属しない。
2. 統合 commit の**後**に同じ範囲を再走し、消えた赤を偽赤、残った赤を真の赤として帰属する。
3. 過去の「26 件」という数値を今回へ一般化しない。件数は今回実測する。

## 8. 実装単位

**単位は 1 つ**とし、Codex `role=author` 1 本で production とテストを同時に書く。
理由: production の逐語 (§4) とテストの逐語が二重管理であり、別々の子に書かせると
1 文字の食い違いで受入 1 本を失う。並列化の利得より整合の risk が大きい。

## 9. 記録 (段 7)

- worklog fragment: 実測 M1/M2/M3 と**その撤回** (§0)、費用実測、変異 matrix、受入結果。
- decisions fragment: D442 の**決定 1・3 と「dispatch/report は未閉包」という制限だけ**を
  supersede する新 D。決定 2 (domain 据置き)、D268 の継承制限、A-03/A-04 の残る穴は明記して継承する。
- failures fragment: F357 の「12 path」を「14 path」へ読み替える supersede 追記。
- phase3.md: [T-819] を本 wave で消化したものとして更新する。
