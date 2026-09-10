# [T-564] 段 4 裁定 — plan v2 と変異事前登録

段 3 は 2 レンズとも **NO-GO**。所見 10 件をすべて real/refuted に裁定した。
**「実装しない」ではなく、scope を広げて実装する。**

## 段 4 で追加実測した事実

計算ノード可視性 probe (request `892394.nqsv`、bnode004、`0:892394.nqsv`)。
一次資料 = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t564-dependency-source/s4/probe-result.txt`。

| 表記 | 見えるか | realpath | 非 symlink dir | HEAD | porcelain |
|---|---|---|---|---|---|
| `/work/SFC/tanab/github/gflags` | 見える | `/work/1/SFC/tanab/github/gflags` | yes | pin 一致 | 0 行 |
| `/work/1/SFC/tanab/github/gflags` | 見える | 同上 | yes | pin 一致 | 0 行 |
| `/work/SFC/tanab/github/glog` | 見える | `/work/1/SFC/tanab/github/glog` | yes | pin 一致 | 0 行 |
| `/work/1/SFC/tanab/github/glog` | 見える | 同上 | yes | pin 一致 | 0 行 |

**射程限定**: これは 1 job・1 host (bnode004)・1 時刻の観測である。「全 bnode で常に両表記が見える」
という普遍命題ではない。言えるのは、可視性を理由に一方を退ける根拠が**この観測には無い**ことである。

## 裁定表

| # | 出所 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | 変異が「推奨」止まりで必須実走に無い | real | 採用 | 内 |
| A2 | 波及確認の collect test が monkeypatch で検知力ゼロ | real | 一部採用 | 一部外 |
| A3 | 「6752 件で pin 閉包」の一般化過大 | real | 採用 | 内 |
| B1 | 実ジョブ受理手順が無い | real | 採用 | 内 |
| B2 | P4 が「復旧」と T-529 の射程を混同 | real | 採用 | 内 |
| B3 | 規範文書 2 本が変更と矛盾したまま | real | 採用 (fold 手順のみ修正) | 内 |
| B4 | consumer 棚卸しが qualification 2 本欠落 | real | 採用 | 内 |
| B5 | submitter の `--repo-root` と `PBS_O_WORKDIR` が分離しうる | real | 一部採用 | 一部外 |
| B6 | P5「結合の種類は増えない」は過小評価 | real | 採用 (P1 を覆す) | 内 |
| B7 | CCBench FetchContent 以降の停止点は予測不能 | 疑い | 記録として採用 | 内 |

### B6 — (P1) を覆す

**policy に書く文字列を `/work/SFC/tanab/github/{gflags,glog}` とする。** 段 1 の (P1) は撤回する。

理由: probe で両表記の可視性・HEAD・clean が同値だと実測できたので、可視性はもはや決定理由にならない。
残る差は `/work/1` が storage shard の `1` を固定することだけで、これは runbook §6 が規範形として
`/work/<project>/<user>` を挙げているのと逆向きである。certify の receipt は source path 自体を
束縛しないので、段 1 が (P1) の根拠にした「realpath witness と表記が割れる」は実害を伴わない。

**(P5) の「結合の種類は増えない」は削る。** 機体固有の絶対 path を repo に書く結合は残り、
その除去は択一 (c) の verified hydrate へ送る (裁定パッケージ)。

### 現行 policy bytes の oracle は親が独立に決める

**`bfb9069b5bbf75f7e6c462f3fa5bc31da5d000fc3f537e22670e8d5aeb27ccb1`**

親が `git show HEAD:tools/pegasus/policy.json` の bytes に対して 2 箇所の置換だけを適用して算出した。
**実装子が自分の書いたファイルから hash を取ってはならない** — それでは誤った編集にも一致する
自己成就 pin になり、恒真と同じである。この値を定数として与え、実装子の編集が 1 byte でも
違えば赤くなる形にする。

### A2 — 一部採用

`test_collect_fixture_bundle_publishes_without_self_rejection` は
`orchestrator/tests/test_silo_ladder_rung1_driver.py:2488` で production validator を monkeypatch
しているため、current/history 境界の証拠にならない。**波及確認リストから外す** (採用)。

production の `validate_current_bindings` が凍結 evidence を現行 bytes と等値比較して拒否する状態は、
`driver` binding が歴史値になった時点で**既に存在する**。本 wave が新たに作る回帰ではないため、
production 境界の直接テスト新設は **scope 外** とし、裁定パッケージへ返す。

### B3 — fold 手順だけ修正

規範文書 2 本の更新は採用する。ただしレンズ B の「同一 commit で `docs/decisions.md` へ fold する」は
本 repo の運用と食い違うので**その部分だけ refuted**。`DW-S07` により 3 台帳は直接編集せず
spool fragment として wave branch へ commit し、canonical への追記・採番は段 9 の land が lock 内で
一度だけ行う。D96 の「同じ変更単位」は fragment commit で満たす。

### B5 — 一部採用

運用手順の固定は採用する (下記「certify 受理手順」)。`submit_certify.sh` に
`cd "$REPO_ROOT"` を足す / 物理 path 不一致を拒否する恒久対応は **scope 外** → 裁定パッケージ。

## plan v2 — 実装子の所有と編集内容

所有は次の 4 ファイルだけ。docs・fragment・commit・job 投入は親。

1. **`tools/pegasus/policy.json`** — 14 行と 16 行の値を
   `/work/SFC/tanab/github/gflags` / `/work/SFC/tanab/github/glog` へ。他 field・整形は触らない。
2. **`orchestrator/tests/test_pegasus_tools.py`** — 351 行と 385 行の literal を新 path へ。
   同 test の他の検査 (expected HEAD、path 不在、HEAD 不一致、dirty、stage 順序) は一切緩めない。
3. **`orchestrator/tests/test_silo_ladder_rung1_evidence.py`** — 段 2 プランどおり。
   `HISTORICAL_SILO_EVIDENCE_IDENTITY` を 5 要素へ伸ばし index 4 = `b1c42e49...` (旧 policy binding)。
   1205–1210 行の tuple assert に `binding["policy"]["sha256"]` を足す。
   1231–1238 行の分岐を `historical_sha256_by_key = {"driver": [3], "policy": [4]}` の形にする。
   `pbs_job` / `submitter` / `verifier_module` は現行 bytes 等値のまま (例外集合を広げない)。
4. **`orchestrator/tests/test_t126_pegasus_tools.py`** — 現行 bytes の唯一の定数として
   `_EXPECTED_SHARED_PEGASUS_POLICY_SHA256 = "bfb9069b5bbf75f7e6c462f3fa5bc31da5d000fc3f537e22670e8d5aeb27ccb1"`
   を module 冒頭に置く。`test_shared_pegasus_policy_owns_no_t126_qualification_keys` を
   「現行 bytes == 定数」「凍結 binding != 現行 bytes」の 2 本立てにする。
   歴史値 `b1c42e49...` を**この file へ重複記載しない** (第二正本を作らない)。docstring を実態へ直す。

## 変異事前登録 (`DW-M01`)

baseline = 実装 + fix 完了後の統合 commit。harness = `tools/mutation_harness.py`。

| ID | 変異 | 期待赤 node | 単一理由性 |
|---|---|---|---|
| M1 | `policy.json` に意味を変えない空白 1 byte を足す (値は不変) | `test_t126_pegasus_tools.py::test_shared_pegasus_policy_owns_no_t126_qualification_keys` のみ | **単一**。path literal は値を読むので緑、evidence test は歴史値 pin と `!=` なので緑 |
| M2 | `gflags_source_path` を旧 home path へ戻す | `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench` + 上記 t126 | **冗長 (2 層)**。`DW-M03` により path oracle の単独証拠には数えない |
| M3 | `glog_source_path` を旧 home path へ戻す | `test_pegasus_tools.py::test_certify_glog_stage_is_pinned_fail_closed_and_precedes_ccbench` + 上記 t126 | **冗長 (2 層)**。同上 |
| M4 | `HISTORICAL_SILO_EVIDENCE_IDENTITY[4]` を現行 hash へ書き換える (歴史値を現行値へ流す誤修正の模擬) | `test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` のみ | **単一**。凍結証拠の歴史値が現行値へ流されたら赤くなることの直接証拠 |

登録時の注記:
- M2 と M3 を**同時に**当てると `policy.json` が元の bytes へ完全に戻るため、evidence test の
  `!= current_sha` も追加で落ちる。単独適用ではこれは起きない。この union は登録済みの期待として記録し、
  harness では単独適用する。
- `DW-M08` の新旧両走は、本 wave が「テスト強化だけ」ではない (設定値の変更が主) ため必須ではない。
  ただし検出力の主張は **「増加」ではなく「保存」** である — 変更前も変更後も
  `policy.json` の任意の byte 変更は赤になる。M1 がその証拠になる。
- 受理集合を縮小する wave ではないので過剰拒否の正例は登録しない。正例は baseline 全緑とする。

## certify 受理手順 (B1・B5 採用分)

1. 実装 fix 完了 → 変異 matrix → 受入全走の順に閉じ、**docs と fragment まで commit して
   tracked/untracked とも clean** にする。
2. worktree root で `pwd -P` を確認し、**既定引数のまま** `tools/pegasus/submit_certify.sh` を実行する。
   `--repo-root` は使わない (submitter が検査した木と job が走る木を分離させない)。
3. nonce・request ID・job ID・host・source commit・job script hash を記録する。
4. **原則として自然終了まで走らせ、`qdel` はしない。** wave の時間内に終わらない場合も中止せず、
   到達段と receipt を記録して報告する。
5. 受理条件 = gflags / glog の head・status・configure・build・install ログが揃い、
   制御が CCBench 段へ到達したこと。
6. job 終了後に両 source の porcelain が空であることを再確認する
   (job が pinned source を汚していないことの事後確認)。

## 名乗りの段階 (B2 採用)

| 段階 | 名乗ってよいこと |
|---|---|
| 実測前 | 新しい path を指す設定へ変更した |
| CCBench 段到達 | job X / host Y で gflags・glog 段を通過し、旧 blocker を除去した |
| `calibrate_rc=0` | certify job が完走した |
| receipt 検収 | accepted calibration を取得した |
| [T-529] 後 | 較正を活性化・登録した |

**本 wave が名乗る上限は 2 段目まで。** T-529 は活性化・登録の blocker であって
certify 完走の blocker ではない、というレンズ B の是正を採る。

## 親が更新する docs (B3・B4 採用分)

- `tools/pegasus/README.md` — 「共有 `policy.json` は編集しない」を、D96 手続きに従う条件付きへ直す。
- `docs/pegasus-runbook.md` — 依存 source の所在 `~/github/gflags` / `~/github/glog` を新 path へ。
- 新しい D の spool fragment — 理由、consumer 全 10 本、旧/新 singleton、凍結 evidence の扱い、
  T-126 series identity が変わること、却下案 (a)(c)、名乗りの段階を記録する。
- worklog fragment。

**consumer 全 10 本** (レンズ B の棚卸しを採用):
shell = `certify_calibration.sh` / `floor_campaign.sh` / `floor_scoping.sh` / `silo_ladder_rung1.sh` /
`t126_qualification.sh` / `t141_region_profile.sh`、
Python = `fetch_third_party.py` / `orchestrator/campaign/silo_ladder_rung1.py` /
`orchestrator/qualification/identity.py` / `orchestrator/qualification/submission.py`。

## 表現の是正 (A3 採用)

段 1 brief の「全 6752 件を走らせて赤はこの 4 件だけであり、これが pin 閉包の実測である」は、
**「受入 test が観測した pin 閉包」** へ限定する。PBS job script、手動 CLI、実 source path を読む
production 経路の閉包は示していない。計算ノードでの実効性は certify 再投入の実測へ帰属させる。

## 裁定パッケージ (scope 外の real 所見、ユーザーへ返す)

1. **production の current/history binding 境界に直接テストが無い** (A2)。`driver` binding が
   歴史値になった時点から既に存在する状態で、本 wave の新規回帰ではない。
   current-only が意図なら直接テストを、歴史 artifact も受理すべきなら production の scope 拡張を要する。
2. **`submit_certify.sh` の `--repo-root` と `PBS_O_WORKDIR` が分離しうる** (B5)。
   submitter が qsub 前に `cd "$REPO_ROOT"` するか、物理 path 不一致を拒否する恒久対応。
3. **機体固有の絶対 path を repo へ書く結合そのものの除去** (B6)。択一 (c) の
   verified hydrate は可搬性と [T-443]/[T-444] の source proof を同時に改善しうる。
