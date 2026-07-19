# 2026-07-19 テストスイート衛生調査

状態: 完成 (実行証跡を含む)

## 位置づけと結論

本書は、基準 commit `d4cbf91` で実施した read-only のテストスイート調査と、その後の敵対相談による再裁定を正本化する。調査対象は Izanagi のテストスイートであり、**Izanagi 内部監査であって CCBench 還元候補はない**。

調査時点のスイートは健全だった。`1573` tests を収集し、全走の記録値は約 `66` 秒だった。重複疑い、恒真 assertion、skip の常態化を広く調べたが、いずれも系統的な汚染はほぼ認められなかった。確定所見は、重複 `1` 組、強化候補として抽出した弱テスト `10` 件、意図の説明を要する契約 pin `1` 件に限定された。

テスト増加は独立した水増しではなく、機能実装に伴う増加と裁定する。2026-07-14〜18 の `5` 日間に `orchestrator/tests/*.py` へ追加された行は調査時集計で累積追加行（added-line churn）`23030` 行（報告上は「約 `+23000` 行」）であり、純増ではない。削除 `1501` 行を差し引いた純増は `21529` 行だった。追加 churn の `84.44%` は件名が `feat` の commit に同梱され、同じ feat commit 群におけるテスト追加行／非テスト Python 実装追加行の期間 aggregate は `19446 / 26461 = 0.7349`（報告上 `0.74`）だった。commit 別の同じ比率には `0.00`〜`1.95` の幅がある。増加の主因は feature wave と同梱された契約・拒否経路の固定であり、テストだけが単独で肥大した兆候ではない。

## 確定所見

### 重複 1 組

`orchestrator/tests/test_s8b_selector_freeze.py` の次の組を重複候補として確定した。

- `test_selector_basis_ignores_floor_budget_but_binds_variant_entries`
- `test_selector_basis_preimage_is_versioned_and_backward_compatible`

後者は floor/budget の非束縛、variant binding の束縛、preimage version をまとめて扱う。ただし敵対相談で、前者だけが一度取得した固定 baseline と比較しており、後者は呼び出しごとに再計算するため、字義どおりの上位集合ではないと判明した。統合は後者へ固定 baseline の pin を加えたうえで前者を削除する裁定とし、単純削除にはしない。

### 弱テスト候補 10 件

初回調査は「妥当入力を渡し、例外が出ないことだけを見る」形を `10` 件抽出した。敵対相談 C2 でテスト本体と SUT の契約を再読した結果、`6` 件は未検査の契約や戻り値を強化し、`4` 件は raise-only validator の正常系契約どおり、または入力 fixture の自己確認しか追加できず恒真化するため変更不要と再裁定した。詳細は「弱テスト 10 件の再裁定」に記す。

### 契約 pin 1 件

`orchestrator/tests/test_s8b_oracle_driver.py` の `test_layer3_strict_consumer_accepts_optional_bench_wall_s` は削除しない。これは `layer3_schema.json` の `runs` 定義について `bench_wall_s` の型と非必須性を構造として固定する唯一の契約 pin である。テスト本体は `layer3_report._validate_schema` / `build_report` を呼ばないが、collection 時の production module import まで「実装コードを一切通らない」と表現するのは過度に広いため、説明は schema pin の範囲に限定する。

## 指標 provenance

調査時基準と現基準を同一の「現在値」に混ぜない。`d4cbf91` 行は当初調査の再現、`240d1cc` 行は test-hygiene 着手基準の再導出である。

| 指標 | 値 | 基準 | 再導出 | 環境・扱い |
|---|---:|---|---|---|
| 調査時 collected | `1573` | `d4cbf91` | P1 | 2026-07-19 に clean archive で再確認。`pegasus02`, Python 3.10.12, pytest 9.1.1。collect-only |
| 調査時全走 | 約 `66 s` | `d4cbf91` | P2 | 当初調査の記録値。元記録には node / xdist 内訳が残っていないため参考値。今回ログインノードでは再実行しない |
| 7/14〜18 のテスト追加 churn | added `23030`（約 `+23000`）、deleted `1501`、net `21529` | `d4cbf91` | P3 | Git object の numstat 集計。`23030` は累積追加行（added-line churn）であり純増ではない。host 非依存 |
| feat 同梱率 | `19446 / 23030 = 84.44%`（約 `84%`） | `d4cbf91` | P4 | commit 件名が `feat(` または `feat:` のテスト追加行を分子とする、追加 churn に対する比率。Git object の集計 |
| feat 群のテスト／実装比 | `19446 / 26461 = 0.7349`（約 `0.74`） | `d4cbf91` | P4 | 分母は同じ feat commit 群の、tests 外の Python 追加行。行数比は品質目標には用いない |
| 現基準 collected | `1976` | `240d1cc` | P5 | 2026-07-19 に clean archive で再確認。`pegasus02`, Python 3.10.12, pytest 9.1.1。collect-only、exit 0 |
| 7/14〜19 (240d1cc 到達分まで) のテスト追加 churn | `28967` | `240d1cc` | P6 | `2026-07-19` の後続 `12` commit（`d4cbf91..240d1cc`）を含む指定 pathspec の numstat 集計。7/14〜18 窓の現基準再導出値は `23030` で調査時と一致。host 非依存 |
| 確定所見 | 重複 `1` 組・弱テスト候補 `10` 件・契約 pin `1` 件 | `d4cbf91` | P7 | read-only 調査の静的照合結果。consultations C1/C2 で再検算 |
| 弱テスト再裁定 | 強化 `6` 件・変更不要 `4` 件 | `240d1cc` | P7 | consultations C2 の全 `10` 件裁定と親裁定を数え上げ |
| 施策裁定 | 全 `9` 件、採用／条件付き `7` 件・棄却 `2` 件 | `240d1cc` | P8 | 本書「施策 9 件の裁定」の表を数え上げ |

P1〜P6 の再導出コマンドは次のとおり。P1/P5 の `REV` はそれぞれ `d4cbf91` / `240d1cc` とする。archive は共有 worktree の未コミット差分を混ぜないために使った。

```bash
# P1 / P5
tmp=$(mktemp -d /tmp/izanagi-test-survey.XXXXXX)
git archive "$REV" | tar -x -C "$tmp"
(cd "$tmp" && python3 -m pytest --collect-only -q orchestrator/tests/)

# P2（計算ノードでのみ再実行可能。今回のログインノードでは実行しない）
python3 tools/run_tests.py

# P3
git log --since='2026-07-14 00:00:00 +09:00' \
  --before='2026-07-19 00:00:00 +09:00' --numstat d4cbf91 \
  -- 'orchestrator/tests/*.py' |
awk '/^[0-9-]+[[:space:]]+[0-9-]+[[:space:]]+/ && $1 != "-" && $2 != "-" {
       added += $1; deleted += $2
     }
     END { printf "added=%d deleted=%d net=%d\n", added, deleted, added - deleted }'

# P4
git log --since=2026-07-14 --until=2026-07-19 \
  --format='@@@%s' --numstat d4cbf91 -- '*.py' |
awk '
  /^@@@/ { feat = ($0 ~ /^@@@feat(\(|:)/); next }
  feat && /^[0-9-]+[[:space:]]+[0-9-]+[[:space:]]+/ && $1 != "-" {
    if ($3 ~ /(^|\/)tests\//) tests += $1; else impl += $1
  }
  END { printf "tests=%d impl=%d ratio=%.4f\n", tests, impl, tests / impl }
'

# P6
git log --since='2026-07-14 00:00:00 +09:00' \
  --before='2026-07-20 00:00:00 +09:00' --numstat 240d1cc \
  -- 'orchestrator/tests/*.py' |
awk '/^[0-9-]+[[:space:]]+[0-9-]+[[:space:]]+/ && $1 != "-" { added += $1 }
     END { print added }'
```

P7/P8 はコマンド集計ではなく、本書および consultations insight の該当表を目視で数え上げた。

`240d1cc` の `1976` collected と、7/14〜19 (240d1cc 到達分まで) の追加 churn `28967` 行は、`d4cbf91` の `1573` collected と7/14〜18の追加 churn `23030` 行を更新した別時点の値である。`5937` 行の差は、2026-07-19 の後続 `12` commit（`d4cbf91..240d1cc`）の追加分である。7/14〜18 窓を `240d1cc` で再導出しても `23030` 行となり、調査時集計と一致する。両者を接合して単一時点のスイート像にはしない。

## 弱テスト 10 件の再裁定

### 強化実施 6 件

4. `test_transition_gn_to_gn1_allows_floor_change_unit`: raise-only の正常系だけでは、コメントが主張する許可 field 全体を固定できない。承認済み遷移表に floor protocol / measurement closure 等が含まれ、`/env_tag` が含まれないことを pin する。

5. `test_manifest_mode_100755_accepted_when_g_h_worktree_match`: `LaunchValidatedFreeze` の型 assertion は既に意味があるが、この正例が実際に mode `100755` を作ったことを局所確認していない。topology の mode と validated object の ratified identity を pin する。

6. `test_off_stock_check_accepts_valid_static_default`: 正常系への入力自己確認は足さず、未検査だった off row の `decision_method != static_default` を拒否する負例を追加する。

7. `test_snapshot_accepts_valid_per_pair_floor`: 正例 fixture の値を再 assert しても validator を no-op にした変異を殺せない。未検査の `oracle_shared=False` 拒否を負例で固定する。SUT が拒否しない場合は実装せず所見に落とす。

8. `test_snapshot_accepts_explicit_null_pair`: null pair の shape を再確認するだけでは恒真化する。pair が null なのに `scalar_alt` が非 null の不整合を拒否する負例を追加する。

10. `test_run_contract_accepts_bench_max_rounds_one`: `10` 件中、意味ある戻り値を実際に捨てていた唯一の例。戻り値を捕捉し、`bench_max_rounds == 1` と入力とは別 object の deep copy であることを固定する。

### 強化不要 4 件

1. `test_between_run_floor_admission_passes_when_no_competitor`: 被検証関数は競合時だけ拒否する `-> None` validator であり、競合なしで例外を出さないことが正常系契約そのもの。stub が空 list を返すことや `is None` を足しても no-op validator を検出できず、fixture／return convention の自己確認にしかならない。

2. `test_assert_machine_pin_accepts_matching_env_tag`: env tag 完全一致なら受理し、不一致なら例外という raise-only 契約で、不一致側も別テスト済み。正例 fixture の env tag や `None` return を assert しても guard を `pass` にした変異が生き残るため、実効的な強化にならない。

3. `test_value_literal_consistency_accepts_match`: 整数 `20` と浮動小数表記 `20.0` の正常境界を既に通し、不一致と literal 不在の拒否も別テスト済み。literal を再抽出して比較すれば SUT と同じ計算の自己参照になり、`is None` は validator の実効性を強めない。

9. `test_snapshot_accepts_all_null_holdout`: stock 未確定時に pairs / `scale_ref` / `scalar_alt` が全 null である入力を受理する重要な境界正例。入力直前の代入を assert しても validator の早期 return 変異が緑のままなので、内容 assertion 追加を強化とは認定しない。

## 施策 9 件の裁定

| # | 施策 | 裁定 | 理由・条件 |
|---:|---|---|---|
| 1 | 確定重複 `1` 組の統合 | 採用 | 固定 baseline の検査を吸収先へ移してから統合する |
| 2 | 弱テスト候補 `10` 件の再裁定 | 採用 | `6` 件を実効的に強化し、恒真化する `4` 件は変更しない |
| 3 | schema 契約 pin の保持と意図明記 | 採用 | optionality を固定する唯一の pin を残し、呼ばない validator の範囲を正確に記す |
| 4 | collected node-ID 集合差分を完了 gate にする | 採用 | 固定件数では意図した削除と無関係な増減を相殺できないため |
| 5 | 事前登録 mutant による red→green matrix | 採用 | 期待値を壊すだけでなく、追加 assertion／新負例だけが対象回帰を殺すことを示す |
| 6 | ratified_verify の git fixture 共有化 | 条件付き | スイート全走が `3` 分を超えた場合にのみ発火。現状は抽象化コストを正当化しない |
| 7 | coverage と差分 mutation の衛生監査 | 条件付き | coverage は観測値に留め、差分 mutation は弱テストを疑う監査手段として標準化候補にする。達成率 gate にはしない |
| 8 | テスト／実装行比の目標化 | **棄却** | `0.74` は増加機序を説明する記述統計で、重複・拒否経路・assertion の実効性を測らない。目標化すると低価値な行追加による gaming や、必要な短いテストの抑制を招く |
| 9 | 全変更でのフル CI 化 | **棄却** | 調査時スイートは健全で、頻度を上げても重複や恒真 assertion は検出できない。ログインノード負荷と待ち時間だけを常設せず、変更対象の検査＋収集差分を通常 gate、計算ノードの全走を wave 完了 gate とする |

したがって、比率は監視用の説明変数であって達成目標ではない。また「フル CI 化」の棄却は最終全走を省く意味ではなく、全変更への常設を棄却するものとする。本 wave の最終全走は親が計算ノードで行う。

## プロセス逸脱

- 着手条件の「本プラン群以外の handoff が空」は字義上未充足だった。`2026-07-19-ai-development-observability.md` が残存していたが、稼働セッションがないことを確認し、ユーザーの包括的ループ実行指示を本 handoff の着手 GO と解釈して逸脱を記録し、続行した。個別の明示 GO ではない。
- Pegasus の共有ログインノードではテストを実行しない。並列 worker は collect-only / compile 確認までとし、targeted red→green mutant matrix と最終全走は親が確保した計算ノードで実施する。

## 実行証跡 (red→green mutant matrix — 親が完了時に追記)

- 実行環境: Pegasus gen_S 計算ノード bnode097 (48 cores)、`/usr/bin/python3` 3.10.12、PBS ジョブ `868017` / `868018` / `868019`。ログインノード側は collect-only と単発再現のみ (runbook §7 準拠)。`PYTHONDONTWRITEBYTECODE=1`
- node-ID 集合 gate (868018): 基準 `240d1cc` = `1976` → 最終ツリー `1978`。消失 = 削除予定の `test_selector_basis_ignores_floor_budget_but_binds_variant_entries` 1 node のみ、追加 = 新設負例 3 node のみ。件数でなく集合差分で判定 (相殺検出可能)
- mutant matrix 10 件 (事前登録の逐語は consultations insight 追補 2。判定 scope = 対象 node 内、各件とも復元後 green を確認):

| mutant | 変異対象 | red | 第一失敗アサート |
|---|---|---|---|
| M1 stale-cache | selector_freeze SUT | OK | `selector_basis_sha256(binding_changed) != baseline` (追加した固定 baseline 検査のみが検出) |
| M2 floor 誤包含 | selector_freeze SUT | OK (非判別と事前明示) | 既存 checksum アサート (追加アサートには未到達) |
| M3 遷移表から /floor_protocol 除去 | ratified_freeze SUT | OK | 追加した部分集合 pin (env_tag 拒否テストは緑維持) |
| M4 fixture chmod 無効化 | ratified_freeze fixture | OK | `topology["mode_map"][...] == "100755"` |
| M5 decision_method 検査無効化 | verdict SUT | OK | DID NOT RAISE (正例テストは緑維持) |
| M6 deepcopy 除去 | oracle_manifest SUT | OK | `validated is not source` |
| M7 oracle_shared 検査無効化 | oracle_manifest SUT | OK | DID NOT RAISE |
| M8 scalar_alt 相関検査無効化 | oracle_manifest SUT | OK | DID NOT RAISE |
| M9 遷移表へ /env_tag 混入 | ratified_freeze SUT | OK | `"/env_tag" not in M._TRANSITION_GN_TO_GN1` |
| M10 返却 copy の bench_max_rounds 改変 | oracle_manifest SUT | OK | `validated["bench_max_rounds"] == 1` |

- 非判別の明示 2 件: M2 (上記)。また `validated.ratified is freeze` (E3 #5) は別テスト :677 の既存 pin と重複する追加であり、専用判別 mutant を持たない (強化件数には数えない)。selector :489 の floor 側固定 baseline アサートは単独判別 mutant を実用的に構成できず、binding 側 (M1) が固定 baseline 検査の判別を担う
- 全スイート: 868017 = `1958 passed / 20 skipped` rc=0。868018 = `1957 passed / 1 failed` — 失敗は `test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged` で、単発再現せず (login で 2 条件とも緑)、868019 の連続 2 走は `1958/20`・`1957/21` の全緑。当該テストは `git status --porcelain` の前後比較で xdist 並列下の untracked 出入りに構造的に脆弱 (今回 4 走中 1 flake)。本 wave の diff から独立した既存脆弱性として worklog 次の一手に登載
- 環境所見 (Pegasus): 計算ノードの既定 `python3` は Intel oneAPI 3.9.13 で本リポジトリを collection 不能 (`/usr/bin/python3` = 3.10.12 の明示指定が必要)。pytest 9.1.1 の pygments 依存はノード画像に無く `pip install --user --ignore-installed pygments` で共有 `~/.local` に導入。selector テストの単独 node 実行には `PYTHONPATH=orchestrator` が必要 (conftest 経由の全走・他テストファイルは自前 path 挿入で不要)

