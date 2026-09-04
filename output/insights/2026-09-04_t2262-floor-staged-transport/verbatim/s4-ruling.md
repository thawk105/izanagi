# 段 4 裁定 — [T-2262] 床値 staged transport の driver 内部既定化

親が段 2 プラン、段 3 の 2 レンズ、および親自身の独立実測をもとに裁定する。
確定済みユーザー裁定 D1562 の枠は動かさない。

## 0. 親の実測 (裁定の根拠。子の主張をそのまま採らず自分で確かめた)

| # | 実測 | 出典 |
|---|---|---|
| M1 | `reservation_binding = reservation.read_binding(os.environ)` は core の `:7253`。`build_cells` の呼出しは `:7463` と `:7529`。**順序として reservation binding は staging より前に確定する** | `s8b_floor_campaign.py` |
| M2 | `:7265-7277` が `receipt_path(repo_root, env_tag=contract.env_tag, nonce=reservation_binding.nonce)` で submit receipt を選び、`job_id` / `job_script_sha256` / `nonce` の一致を要求する | 同上 |
| M3 | `receipt_path` は `repo_root/output/env/<env_tag>/floor/attempts/submissions/<nonce>/submit-receipt.json` を返す。**submission directory を作る canonical 関数が既にある** | `floor_submit_receipt.py:39-48` |
| M4 | `pegasus` 契約は `isolation_policy=IsolationPolicy(single_process=True, ...)`。`is_reservation_required` は `single_process` を返す。**production 床値経路では reservation binding が必ず存在する** | `env_contract.py:260`, `reservation.py:278-282` |
| M5 | 床値の materialization は `_build_cells_impl` の `:4127-4144` で `fetchcontent_base_dir is None` を分岐している。**床値側の None 分岐はこの 1 箇所** | `s8b_floor_campaign.py` |
| M6 | `s8b_oracle_n_pilot.py:822-828` が `_canonical_floor_fetchcontent_base(None)` を呼び、結果を `_prepare_floor_oracle_dependency` へ**非 None で**渡す。**共有 helper の別 consumer が実在する** | `s8b_oracle_n_pilot.py` |
| M7 | `measurement-generation-claims` directory は repo 内に**存在しない**。`output/env/pegasus/floor/attempts` 配下は `submissions/` の 3 件だけ。**生きた部分 claim は 1 件も無い** | `find output -type d -name "*generation-claims*"` が 0 件 |
| M8 | 現 main の `tools/pegasus/floor_campaign.sh` の sha256 は `f49a44e8…`、歴史 submit receipt の記録値は `48ef153a…`。**既に不一致で main は緑**。したがって現 bytes を receipt へ照合する生きた検査は存在しない | `sha256sum`、`submissions/e587c22d…/submit-receipt.json` |
| M9 | 稼働中の `worktree-dev-wave-cross-protocol-search-20260903` が commit `aeafac37b` で `orchestrator/tests/test_ccbench_spawn_sites.py` に 2 件追加済み (未 land)。**process 起動点の目録は他 wave が編集中** | `git log --all --not main` |
| M10 | `floor_liveness.py:255-290` は journal record を **exact key 集合**で検証する。新しい event の追加は既存 validator を割りうる | `floor_liveness.py` |

## 1. 所見の裁定

### sol

| 所見 | 裁定 | 理由 |
|---|---|---|
| S1 ambient `IZANAGI_SUBMISSION_NONCE` が検証済み `reservation_binding.nonce` と束縛されない | **real・採用・scope 内・must-fix** | M1/M2 のとおり順序上も可能で、既存の検証済み束縛を使うだけで閉じる。raw env を authority にすると「発見による暗黙の入力経路」を作らないという D1562 の要件を満たさない |
| S2 固定 prefix の ancestor symlink が未検査 | **real・採用・scope 内・must-fix** | 正規 shell が全 component を検査している (`floor_campaign.sh:299`)。driver へ移す以上、移した先で再現しなければ検査が消える |
| S3 `test_default_staged_transport_is_not_counted_as_refreeze_seam` は恒真 | **real・採用・scope 内・must-fix** | classifier に default 引数を渡せば必ず空になる。実効 gate へ再照準する |
| S4 nested FetchContent の offline 挙動 (疑い) | **疑いのまま・不採用** | 静的に top-level 3 依存で閉じており、失敗しても preflight で fail-closed。実測は計算ノードでの official 実走が要り本 wave の scope 外 |

### luna

| 所見 | 裁定 | 理由 |
|---|---|---|
| L1 部分 claim の resume が basis 混在で拒否される | **real・機構は作らない・記録だけ** | M7 のとおり生きた claim が 0 件で、直る対象が存在しない。回復機構の新設は仮想リスク向けの台帳追加にあたり scope 外 (`DW-G05`)。**「本変更をまたぐ resume はできない。新しい `campaign_run_id` で投入し直す」を worklog と decisions へ記録する**。加えて `s8b_holdout_admission.py` は locked な T-1851 / T-2107 が所有中で、触ると編集面が交わる |
| L2 staging 失敗の liveness 診断が generic へ退化する | **real・must-fix にしない・記録** | 変わるのは診断の粒度であり certified 値・受理集合・参照ではない (`DW-G05`)。M10 のとおり journal へ event を足すと exact key 検証を割る危険があり、失う診断より持ち込む危険が大きい。worklog の既知帰結と次の一手へ置く |
| L3 driver 内 `cp -a` が process 起動点目録を変える | **real・採用・ただし方針を変えて回避する** | M9 のとおり同目録を他 wave が編集中。**subprocess を使わない in-process copy を既定とする**。symlink を symlink のまま保つ、mode bit を保つ、`.git` を含む木全体を漏れなく複製する、という現行 `cp -a` の意味のうち後段検証が依存する分は保つこと。保てない意味があると分かった場合は**握り潰さず停止して報告**する (そのときだけ `cp -a` + 目録更新へ戻す) |
| L4 `[source-missing]` の予定手順が成立しない | **real・採用・scope 内** | 新 staging が先に拒否するため、後段 diagnostic の発火点を明示的に分ける |
| L5 `s8b_oracle_n_pilot` の nonce 不在 (疑い) | **real へ格上げ・ただし対処は「壊さない」だけ** | M6 のとおり共有 helper の実 consumer である。**`_canonical_floor_fetchcontent_base` の `None` 分岐は削除しない**。n_pilot 自体の transport 修復は scope 外 |
| L6 detail code の未指定 | **採用・実装時に決める** | 許可集合は `:215-268`、未知 code は `:1985-1990` で `ValueError`。既存 code の再利用を既定とし、足す場合は許可集合へ同時登録する |
| L7 repo 外検査をコピー前に行うか未明示 | **採用・コピー前に行う** | repo 内へ書いてから拒否するのは副作用を先に作る。destination の外部性はコピー前に確定させる |

### 親 brief への反証 (すべて受け入れる)

- 「`ATTEMPT_DIR` と `SUBMISSION_DIR` は互いに導出できない」→ **path 式としては正しいが runtime では誤り。**
  submit receipt が両者を持つ。sol が正しく、これは S1 の修正方向を裏づける。
- 「凍結 bytes pin は不在」→ **言い方が不正確。** 歴史 submit receipt が job script の path と sha256 を持つ。
  ただし M8 のとおり現 bytes を照合する生きた検査は無く、**更新対象の凍結 pin は不在**という結論自体は保つ。
  記録では「更新対象の凍結 pin は不在。歴史記録としての receipt には bytes が載るが規律 7 により書き換えない」と書く。
- 「pilot の `nondefault_seams` が結果から消える」→ **public result schema にその field は無い。**
  値は private な measurement-generation claim にある。
- file:line のずれ (A4/A5/A6、`_assert_official_permitted` は `:463-473`、`run_campaign` の呼出しは `:7044`、
  CLI 定義は `:8234-8237`) → すべて luna の値を正とする。

## 2. プラン v2 (実装する内容)

1. **payload 所在の導出は検証済み束縛から行う。**
   `floor_submit_receipt.receipt_path(repo_root, env_tag=contract.env_tag, nonce=reservation_binding.nonce).parent / "masstree-payload"` を payload root とする。
   path 式を自分で組み立て直さず既存 canonical 関数を使う。
   raw な `os.environ["IZANAGI_SUBMISSION_NONCE"]` を authority にしない。
   検証済み束縛が無い場合 (reservation 不要な env) は **fail-closed** で拒否し、ambient env にも外部取得にも落ちない。
2. **staging 先は repo 外の固定 leaf** とする (`<canonical TMPDIR>/izanagi-floor-fetchcontent`)。
   外部性はコピー前に確定させる (L7)。destination は事前不在必須、排他作成。
3. **移す検査**: payload root と 3 source の非 symlink directory 検査、destination の事前不在、
   排他 mkdir、3 依存の存在、コピー後の destination 再検査、**および固定 prefix の全 ancestor component の
   非 symlink 検査** (S2)。
4. **copy は in-process で行う** (L3)。新しい subprocess 起動点を作らない。
   保てない意味が判明したら停止して報告する。
5. **床値側の `None` 分岐 (`:4127-4144`) を、導出した base を渡す形へ一本化する。**
   `_prepare_floor_oracle_dependency` 内の `None` / base-only 分岐は、床値呼出し側の一本化後に
   production caller が居なくなるので削除してよい。**`_canonical_floor_fetchcontent_base` の
   `None` 分岐は削除しない** (M6 の n_pilot が使う)。
6. **`floor_campaign.sh`** から staging function・`fetchcontent-staging` phase・`--fetchcontent-base-dir` の
   argv 追加を削除する。`submit_floor.sh` の payload 発行は変更しない。
7. **18 名集合と判定式は literal 無変更。** 既定経路は raw 引数 `None` のまま分類されるので
   seam ゼロの意味は変わらない。
8. **CLI `--fetchcontent-base-dir` は pilot 専用 seam として残す。**

## 3. scope 外 (実装しない。裁定パッケージとしてユーザーへ返す)

- §8 の `_assert_official_permitted` と CLI 無条件拒否の解除、承認束縛の実装。
- `floor_campaign.sh` の `--mode pilot` 固定を official mode へ結線する作業。
- official 実走と床値の性能測定。
- `s8b_oracle_n_pilot` の FetchContent transport の独立修復。
- 部分 claim の移行・backfill 機構 (M7 により対象が存在しない)。
- prebuild への `FETCHCONTENT_FULLY_DISCONNECTED=ON` の一般 hardening。

**本 wave 完了後も床値 official は起動できない。** 外れるのは 2 本ある関門のうち transport 側 1 本だけである。

## 4. 変異事前登録 (DW-M01。実装前に登録する)

各変異は実装後に「同じ入力を拒否する層が前後にも内側にも無い」ことを確認する。
確認できない変異は登録から外し、実効 gate へ再照準して erratum を残す。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| MU1 | payload nonce の導出元 | `reservation_binding.nonce` を `os.environ["IZANAGI_SUBMISSION_NONCE"]` へ置換 | KILLED。2 つの nonce を食い違わせた負例だけが赤にする |
| MU2 | ancestor component の非 symlink 検査 | 検査を無条件 True へ | KILLED。固定 prefix の ancestor を symlink にし payload leaf は実 directory にした負例 |
| MU3 | 検証済み束縛不在時の fail-closed | 拒否を ambient env へのフォールバックへ | KILLED。束縛不在の負例 |
| MU4 | 床値既定経路の pin 検査呼出し | `_verify_pristine_floor_dependency_sources` の呼出しを削除 | KILLED。dirty または pin 不一致 payload の負例 |
| MU5 | 床値既定経路の transport | 既定で 3 つの source-dir を渡さない形へ | KILLED。既定経路が `transport_mode="source-dir"` と 3 source-dir を持つことの正例 |
| MU6 | seam 分類へ渡す raw 引数 | 導出した base を raw `fetchcontent_base_dir` 引数として渡す | KILLED。**恒真でない**実効 gate — 既定 staging が実際に起きたうえで claim の seam basis が空であることを同時に見る正例 (S3 の再照準) |
| MU7 | destination の事前不在検査 | `lexists` 検査を削除 (排他 mkdir は残す) | 登録するが**帰属要確認**。luna が二重拒否を指摘。単一理由にできなければ外して erratum |

## 5. 所有と分割

- 編集面: `orchestrator/campaign/s8b_floor_campaign.py`、`tools/pegasus/floor_campaign.sh`、
  `orchestrator/tests/test_s8b_floor_campaign.py`、`orchestrator/tests/test_pegasus_floor_tools.py`。
- **`orchestrator/tests/test_ccbench_spawn_sites.py` は触らない** (L3 の方針により不要。M9 の他 wave と交わらない)。
- **`orchestrator/campaign/s8b_holdout_admission.py` と `s8b_oracle_n_pilot.py` は触らない** (L1/L5)。
- producer/consumer 契約が 1 本 (staging → 検証 → prebuild) を跨ぐため、Codex `role=author` **1 単位**で実装する。

## 6. 裁定 inbox の再走査 (wave 開始後に main へ着地した裁定の取り込み)

wave 開始時の main (c7ed5658) 以降、main は 10 commit 進み、decisions に D1573〜D1592 が着地していた。
本 wave の編集面 (`s8b_floor_campaign.py`、`floor_campaign.sh`、対応 test 2 本) と anchor file は
**main 側で 1 byte も変わっていない**ため、§0 の実測と本裁定は有効なままである。
新着裁定のうち本裁定に効くものは次の 2 件。

- **D1580 (候補集合から恒真になる述語を正しさ防壁として新設しない)** — S3 の裁定と同じ向きである。
  恒真な検査を防壁として数えず、**変異事前登録にも入れない**と明記されている。
  したがって MU6 は「classifier に default を渡せば空になる」ことを見る形では登録できず、
  §4 に書いたとおり「既定 staging が実際に起きたうえで claim の seam basis が空である」ことを
  同時に見る実効 gate へ再照準する。この形にできなければ MU6 は登録から外す。
- **D1586 (判定器が環境から解決した実体の identity は green record へ束縛する。ただし束縛は拒否ではない)** —
  本件も判定器が環境から実体を解決する設計である。ただし D1586 が「承認済み identity の権威が repo に無い」
  と書いた状況と異なり、**本件には権威が repo 内に存在する** (検証済み `reservation_binding` と
  submit receipt)。したがって記録に留めず拒否できる。これは §2-1 の裁定を補強する。
  provenance の記録も新設不要である。submission nonce は既に reservation-preflight の journal record が
  持っており、新しい field を足す必要はない。**新しい承認権威を wave が自分で定義しないこと。**

- D1581 (repo 外入力の guard は要求 file 集合で判定する) は、テストが git 管理外の絶対 path を読むときの
  skip 判定の話であり、本 wave の test は自前 fixture を作るため非該当。
- D1583 (repo 外束縛の全数走査 gate は新設せず局所修復に留める) は §3 の scope 外方針と同じ向き。
