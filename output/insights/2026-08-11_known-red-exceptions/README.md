# 既知の失敗・依存物不在を緑に化かしていた 4 箇所 — 実測と変異台帳

wave: `dev-wave-known-red-exceptions` / 実装 commit `d4d1e82c`、受入 tip `34255bba`。
経緯は同日の worklog エントリ、失敗の型は failures の
「依存物ガードの疑似スキップと防壁配線欠落の skip が、受入全走を緑のまま素通りしていた」。
裁定へ返した択一は `package.md`。

## skip の全数実測 (診断走行。受入形ではない)

計算ノード request `900952.nqsv`、`python3 tools/run_tests.py orchestrator/tests -rs --force-dispatch`、
**8037 passed / 20 skipped / 514.28 秒 / rc=0**。wave 前の HEAD に対する測定である。

| 件数 | 理由 | 分類 |
|---:|---|---|
| 5 | C++ toolchain 不在 (g++-13 が PATH に無い) — source_digest preprocess は実 g++-13 が要る | 外部依存物の不在 |
| 1 | 同上 (本番 source_digest.resolve の identity 検査) | 同 |
| 1 | g++-13 不在 — preprocess 実測は計測ホスト限定 | 同 |
| 3 | slow real-build canary / oracle control: initialized ccbench + pinned toolchain が必要 | 同 |
| 1 | pinned Codex runtime 不在 (D60 の理由付き skip) | 同 |
| 3 | bundled Codex/bwrap/busybox required | 同 |
| 1 | gnuplot 無し | 同 |
| 1 | no real Silo sample (`output/runs/silo-sample` は git 追跡外) | 同 |
| 4 | template patch 未適用 | **条件付き未実走** — repo 内で満たせるが開けていない (`package.md` R1) |

**失敗を skip に化かしたものは無い。** ただし「発火している skip はすべて具体的な依存物不在」
ではない — 最終行の 4 件は依存物不在ではなく**条件付き未実走**である (末尾の erratum 参照)。
規約違反は静的走査の側だけに出た (下記)。

## 静的全数走査で出た規約違反

`orchestrator/tests/README.md` の「依存物不在時の skip (可視化)」と「二重 runner」が正本。

| 箇所 | 形 | pytest での見え方 |
|---|---|---|
| `test_calibrator.py` の実プロセス番人 2 本 | `if shutil.which("pgrep") is None or not os.path.isdir("/proc"): return` | **PASS** |
| `test_hooks.py::test_settings_json_wires_all_hooks` | `hooks` key 欠落で `skip(...)` | SKIP |
| `test_dev_waves_isolation_contract.py` | conftest import の全 `ImportError` を「pytest 不在」skip | SKIP |
| `test_p3_s4_loop_trigger_gating.py::_pinned_clean_sub_or_skip` | git の全例外を「submodule 未取得」skip (呼び出し元 0 件) | 到達しない |

## 変異 matrix

`tools/mutation_harness.py`、runner-mode=dispatch、対象コマンドは
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_calibrator.py orchestrator/tests/test_hooks.py -q -rf`。
spec = `mutation-spec.json` (生成器が anchor の一意性を assert する)、台帳 = `mutation-ledger.json`。

| ID | 変異 | 期待 | 実測 |
|---|---|---|---|
| M1 | `runner.py` の pgrep パターンを旧 F3 形 `build-variants/.*ycsb_.*\.exe` へ巻き戻す | KILLED / 3 node | KILLED / 同一 3 node |
| M2 | 直した guard 1 本を `return` へ巻き戻す | KILLED / 1 node | KILLED / 同一 1 node |
| M3 | `hooks` key 欠落時に helper が黙って return する形へ巻き戻す | KILLED / 1 node | KILLED / 同一 1 node |

baseline PASSED。**SURVIVED / TIMEOUT / MISMATCH はゼロ。**

M1 は本 wave の変更で F3 の検出力が落ちていないことの pin である。M2 / M3 は新設した
positive control 2 本に歯があることの実証で、どちらも「変異を入れると新設 node だけが赤くなる」。

### 新旧両走 (`DW-M08`) を走らせていない理由

M2 / M3 の「旧側」= wave 前の HEAD は、**変異後の状態そのもの**である
(guard が `return`、helper が hooks 欠落で skip)。その状態で受入全走が
8037 passed / 20 skipped / rc=0 だったこと (上記の診断走行) が、
「旧テストはこの退行を検出しなかった」という差分の直接の証拠になる。
同じ spec を旧 HEAD へ当てても anchor が存在せず、走行そのものが成立しない。

## 受入全走

lease 取得後に local main を取り込み (`34255bba`)、受入形のまま投入。
**8277 passed / 20 skipped / 522.35 秒 / rc=0。** skip 件数は診断走行と同じ 20 で、
本 wave が skip を増やしていないことの確認になる (疑似 PASS 2 件は依存物が揃う環境では
従来どおり実検査が走るため skip にならない)。

## 測れなかったこと

template patch を一時適用して 4 node の実挙動を測ろうとしたが、submodule への patch 適用が
権限層に拒否された。迂回はしていない。`git apply --check` が現行 pin に対して rc=0 で
当たることだけは確認済みで、それ以外は静的判断である (`package.md` の事実 6)。

## erratum (2026-08-11、wave `dev-wave-t8b-restart-residue`)

[T-770] の裁定 (R1 = (b) + (c) 起票、R2 = (a)) に従い、分類語を訂正した。本文の
「発火している skip はすべて具体的な依存物不在」は、表の最終行 4 件について誤りである。
4 件の前提は repo 内で満たせるため、外部依存物の不在ではなく**条件付き未実走**に分類する。

**実測値 (件数・rc・request ID・変異結果) は 1 つも変えていない。** 訂正したのは分類語と、
それに基づく本文 1 文だけである。

分類の正本は `orchestrator/tests/README.md` の
「条件付き未実走 (repo 内で満たせるが開けていない)」節であり、同節と
`skiputil.skip_conditional_unrun()` / `test_skip_classification.py` による機械固定は
並行 wave `dev-wave-t770-conditional-unrun` が実装・land した ([T-770] 完了、変異 4/4 KILLED)。
本 erratum はその land が触れなかった census 側だけを揃えるものである。
4 node を実際に走らせる経路 (R1 (c) の隔離 checkout を含む) は [T-790] が持つ。
