# 段 1 brief — [T-930] 保留テストの迂回封鎖 ({{D:hold-no-bypass}})

wave: `dev-wave-t930-hold-no-bypass` / branch: `worktree-dev-wave-t930-hold-no-bypass`
起点 main: `6331284e` / 作成 2026-08-12 20:43 JST / brief 確定 21:00 JST

## 裁定 (確定済み、authority: user)

逐語「保留したテストを素の pytest 直叩きが実行できるのは許さない。それは izanagi として保留では
なく、あなたが回避してるだけ。そのようなごまかしは認めない」。T-930 の rulings 容認推奨は**棄却**。
控え = `rulings-inbox/2026-08-12-rulings5-batch.md`。fragment 正本 = 未 land branch
`worktree-rulings6-20260812` (`6d4223cb`)、記録段で `cherry-pick -x` 相乗り。

## 親が段 1 で実測した事実 (すべて本 worktree tip `6331284e`、2026-08-12 20:47〜20:57 JST)

probe: `dev-wave-jobs/dev-wave-t930-hold-no-bypass/probe-*.sh`、log は同 `log/`。

| 経路 | 実測 | 保留 |
|---|---|---|
| A: repo root から `python3 -m pytest <held node>` | 0.29s `1 skipped` | **発火する** |
| B: 同上 + `--noconftest` | 34.78s `1 passed` | **迂回成立** |
| C: `cd orchestrator/tests` して pytest | rc=3 INTERNALERROR (`No module named 'orchestrator'`) | 走らない |
| D: repo 外 cwd から絶対パス pytest | rc=3 同上 | 走らない |
| E: `python3 orchestrator/tests/test_campaign_import_invariant.py` | 36s `30 passed` | **迂回成立** |
| F: `--confcutdir=orchestrator` | 0.22s `1 skipped` | 発火する |

- **ユーザーの言う「素の pytest 直叩き」は A ではない。** A は既に塞がっている。実在の穴は B と E。
- **1 seam で判別できる** (実編集 + 即時復元で実測、`git checkout --` で復元・tree clean 確認済み):
  held module の import 時点で A は `sys.modules` に `conftest` と
  `orchestrator.tests.growth_test_holds` の**両方が既に載っている**が、B と E は**どちらも空**。
- 二重 runner は `_run()` が file ごとに自前実装 (共通 helper 無し)。保留 8 file のうち
  `__main__` を持つのは **5 file** (campaign_import_invariant / codex_reasoning_ab /
  env_attestation / s8b_binding_driftguards / s8b_repo_scan_invariant)。残り 3 file
  (ruleops / s8b_holdout_freeze / s8b_oracle_driver) は `__main__` 無し = E 経路で 0 件実行。

### 訂正 (21:30 JST、段 2 の指摘を親が実測して確定。brief 初版の誤りを撤回する)

**E 経路で迂回するのは 5 file ではなく 2 file・7 node だけである。** `__main__` を持つ 5 file は
harness の種類が 2 つに分かれ、片方は E 経路でも保留が正しく効く。

| file | harness | E 経路の実測 | 保留 |
|---|---|---|---|
| `test_campaign_import_invariant.py` (held 6) | 自前 `_run()` (:1654-1708) | `30 passed` 36s | **迂回** |
| `test_s8b_repo_scan_invariant.py` (held 1) | 自前 `_run()` (:38-55) | `PASS <held node>` rc=0 | **迂回** |
| `test_s8b_binding_driftguards.py` (held 1) | `pytest.main([__file__, "-q"])` (:536) | `17 passed, 1 skipped` 64.6s + 保留マーカー 1 行 | **効く** |
| `test_env_attestation.py` (held 1) | `pytest.main([__file__, "-q"])` (:1360) | `103 passed, 1 skipped` 0.76s + 保留マーカー 1 行 | **効く** |
| `test_codex_reasoning_ab.py` (held 16) | `pytest.main([__file__, "-x"])` (:4270) | 未実測 (実 repo clone で高コスト)。静的には上 2 件と同形 | 効く見込み |

`pytest.main([__file__])` は rootdir 検出で conftest を読むため、E 経路でも A と同じ enforcement が
働く。**したがって「module 冒頭で `__main__` なら一律 refuse」する設計は、現に正しく効いている
経路を壊す** (`17 passed` / `103 passed` が rc=2 の拒否に変わる)。段 2 プランの案 alpha は
この事実を持たずに書かれており、そのままでは受理集合の不要な縮小になる。

B 経路 (`--noconftest`) は harness の種類に関係なく **8 file / 30 node すべてが迂回する。**
本 wave の主戦場は B であり、E は 2 file・7 node である。
- `test_plain_runner_coverage.py` は「`__main__` 内に harness signal が有るか」しか見ておらず、
  **どの関数を実行するかは縛っていない**。保留 node を `_run()` が飛ばしても緑のまま。
- 二重 runner を repo 内から起動する tool / script は**ゼロ** (hit は docs と output/insights のみ)。
- 編集予定 file を bytes/sha で pin する台帳は**ゼロ**。ただし
  `test_pytest_failure_digest.py` が実 conftest を temp dir へ**コピーして走らせ、走行後に
  bytes 同一を assert** する。conftest 冒頭の `ModuleNotFoundError` fallback はこの probe の
  fail-open 契約のために存在する。

## scope

1. 保留の enforcement を「conftest だけが持つ」形から「**held test module 自身が import 時に持つ**」
   形へ広げ、B と E を封鎖する。
2. 解除口は**既存の env token 1 本だけ** (`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command`)。
   新しい env・CLI flag・設定ファイルを作らない。
3. registry と guard 実装の binding をメタテストで機械強制する
   (`test_growth_test_holds_contract.py`)。台帳に file を足したのに guard を付け忘れたら赤。
4. 封鎖の実挙動を subprocess で実測する検査を置く (B と E を実際に起動して「走らなかった」ことを見る)。

## scope 外 (段 4 の裁定パッケージでユーザーへ返す)

- C / D の INTERNALERROR。**保留は破られていない** (1 件も実行されない) が、診断不能な壊れ方。
  直そうとすると「repo 外 cwd からの走行を成立させる」= 迂回口を増やす方向になりうるため触らない。

## 不変条件 (破ったら停止)

- **A 経路の挙動は bit 単位で不変。** 受入全走 (`run_tests.py`) の受理集合を変えない。
- **同一 node の保留印は 1 つ** — conftest 経由では新 guard は no-op でなければならない。
- **production 側に env の解除口を作らない** (本 wave は test 層のみを触る)。
- `release_condition` literal は `explicit-user-command-only` のまま。
- テスト削除・正しさゲート緩和は不可 (規律 2)。保留の**追加**も本 wave では行わない (台帳の行は不変)。
- `test_pytest_failure_digest.py` の conftest copy 契約 (bytes 同一 + plain-import fail-open) を壊さない。
- `test_plain_runner_coverage.py` の自走 harness 契約を壊さない。
- 実装は Codex `role=author` (D95)。親は実装面を直接編集しない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 対象は B と E の両方。ユーザー逐語は「素の pytest」だが、A は実測で既に塞がっており、
  逐語どおりに読むと執行対象がゼロになる。裁定の趣旨は「runner を替えれば走る」状態の封鎖であり、
  同性質の穴を全部塞ぐ。
- **(P2)** 部分保留 module (`test_codex_reasoning_ab` は保留 16 / 全 node は多数) を B・E 経路で
  どう扱うか。案 α = module 全体を refuse (単純・完全 fail-closed、非保留 node の plain 実行も止まる)、
  案 β = 保留 node だけ refuse し他は走らせる。**親の provisional = β**、実装が
  `_run()` 5 本への侵襲を強いるなら α へ落とす。
- **(P3)** 発火時の挙動。plain runner (E) は「印字して非 0 終了」、`--noconftest` (B) は
  `pytest.skip(allow_module_level=True)` を **provisional** とする。B を赤 (collection error) に
  するか skip にするかは受理集合の性質が変わるので段 3 で攻撃させる。

## 成果物影響 (DW-G05)

実装しない場合: 保留 30 node のうち plain runner を持つ 5 file 分が `python3 test_x.py` と
`pytest --noconftest` で走り続ける。certified 選択の値は変わらないが、**「保留」の受理集合が
runner 依存になり**、`growth_test_hold_inventory()` がユーザーへ提示する台帳 (30 件保留) が
実行事実と食い違う。受入の床 (worklog 483 で崩した 142.3s→2.56s 等) も「経路を替えれば復活する」
状態のままになる。

## 成果物の形

- `orchestrator/tests/growth_test_holds.py`: enforcement API 追加 (台帳の行は不変)。
- `orchestrator/tests/conftest.py`: enforcement 有効化の印を 1 箇所。
- 保留 node を含み実行経路を持つ test file: guard 呼び出し (最小行数)。
- `orchestrator/tests/test_growth_test_holds_contract.py`: binding 検査 + B/E の subprocess 実挙動検査。

## 並行 wave

`dev-wave-freeze-hold-residual` ([T-913]/[T-914]) が同じ `growth_test_holds.py` 面で稼働中
(20:40 時点で段 5、[T-913] は「実装せず据置」裁定済みなので台帳行の追加は無い見込み)。
**land 順は先方優先。** 当方は land 前に main を再取り込みして衝突を解消する。

## 分割方針

面が密結合 (台帳 API ↔ conftest ↔ test file ↔ contract test) のため実装子は 1 本。
受理集合が変わる wave なので**軽量版でも段 2/3 の敵対子と段 6 の敵対レビュー 2 本を省かない**。
