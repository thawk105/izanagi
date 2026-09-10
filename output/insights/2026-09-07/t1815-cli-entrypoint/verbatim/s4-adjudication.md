# 段 4 裁定 — [T-1815] 8c 事前登録 CLI entrypoint

親が段 2 プランと段 3 の 2 レンズ (sol=正しさ境界、luna=整合・実効性) を裁定し、
プラン v2 と変異事前登録を確定した。

---

## 0. 親が段 3 の後に自分で実測したこと

段 3 の争点は親が一次資料で決着させた。以下はすべて親の実測である。

### (M-1) 合成 tiny repo は同じ欠陥を 0.2 秒で踏める — sol 所見 8 は real、親の追補 (P5) は誤り

`orchestrator/campaign/` の 3 module (`s8c_preregistration.py`,
`s8c_preregistration_evidence.py`, `s8c_generation_projection.py`) と証拠契約
`s8c_preregistration_evidence_contract.v1.json` の live bytes を空 repo へ copy し、
1 commit するだけで、三 blob 検査を通過して評価器まで到達する。

| 経路 | 結果 | 所要 |
|---|---|---|
| library (`activation_report_at`) | 12 条件が 8 種類の reason へ分かれる (下表) | 0.27 s |
| CLI file-path | 12 件すべて `ERROR / evaluator-exception` | 0.30 s |
| CLI `-m` | 12 件すべて `ERROR / evaluator-exception` | 0.30 s |
| gate CLI file-path | `ImportError` traceback、rc=1 | 0.20 s |
| gate CLI `-m` | 正しい JSON、rc=1 (現行でも通る対照) | 0.30 s |

library が返す期待値 (証拠契約あり版、tiny repo commit 7c92a93f7e4c…):

```
C01 EVIDENCE_UNDEFINED workload-supervisor-absent
C02 EVIDENCE_UNDEFINED trial-registry-capability-absent
C03 EVIDENCE_UNDEFINED trial-registry-capability-absent
C04 EVIDENCE_UNDEFINED workload-supervisor-absent
C05 EVIDENCE_UNDEFINED schedule-schema-absent
C06 EVIDENCE_UNDEFINED budget-consumer-contract-undefined
C07 UNSATISFIED         result-judge-consumer-incomplete
C08 EVIDENCE_UNDEFINED prereg-binding-capability-absent
C09 UNSATISFIED         layer3-producer-unreachable
C10 UNSATISFIED         cross-binding-verifier-incomplete
C11 EVIDENCE_UNDEFINED workload-supervisor-absent
C12 EVIDENCE_UNDEFINED workload-supervisor-absent
```

**証拠契約を置かない版では 12 件が一律 `ERROR / evidence-contract-missing` になる。**
一律の期待値は壊れた側 (一律 `evaluator-exception`) と形が同じで oracle として弱いので、
**証拠契約を置く版 (非一律 12 組) を採る。**

親の追補 `brief-addendum.md` の「小さな合成 repo を作って安く同じ欠陥を踏ませることはできない」は
**誤りであり、親自身の実測で反証された**。追補の 39〜119 秒という数字自体は real だが、
それは「real repo HEAD を評価すると高い」ことしか言っておらず、
「安い代替が無い」は導けない。この一般化の誤りを段 7 で記録する。

### (M-2) `DECIDER_VERSION` は bump しない — sol 所見 1 (blocker) は refuted

`docs/phase3-8c-preregistration.md`「凍結される範囲」「改訂手続き」を一次資料で読んだ。
規範は「判定器・評価器・射影のいずれかで受理集合・拒否理由・射影された判定入力の意味を
変える変更は bump し、その版を持つ新世代 record を発行しなければならない」と書く。
bump しない裁定の根拠は 3 点。

1. **権威 API の出力が不変である。** 規範自身が「判定は `s8c_preregistration.py` が `C` 時点の
   git blob だけから再計算する」と定義する。その再計算を行う `activation_report_at` /
   `effective_at` の出力は、任意の commit について修正前後で同一である。変わるのは
   `if __name__ == "__main__"` の起動 bootstrap だけで、判定器として import されたときには
   一度も実行されない。
2. **bump は機械的に発行不能である。** 規範は「bump したら同じ commit で次世代 record を発行」
   を要求するが、`s8c_preregistration.py:1498-1500` の `_assert_history_transition` は
   `protected_sha256` が親と同じまま generation を進める record を `spurious-revision` で拒否する。
   本 wave は凍結範囲 (§1〜§4・§6・§7 の規範本文、§5 の欄名集合、当該ブロック、証拠契約の意味内容) を
   1 byte も変えないので、v10 + g16 は**発行できない**。bump を選ぶことは scope 外の文書改訂を
   強制することと同義になる。**規律 2 は「gate を緩めるな」であって「発行不能な儀式を通すために
   保護対象文書を編集せよ」ではない。**
3. **受理集合と拒否理由の集合が不変である。** 修正前後で `effective=true` になる commit 集合は
   空のままであり、判定器が返しうる reason code の集合も変わらない。壊れていたのは
   transport であって、規範がいう「判定器・評価器・射影の意味」ではない。

**sol の懸念は不採用にせず記録する。** 段 7 で decisions へ「CLI transport の復旧は
decider 意味変更ではない」という設計判断として書き、根拠に (2) の発行不能性を含める。

### (M-3) `campaign-direct-bootstrap` 規則 — luna 所見 9 は real、ただし当該テストは hold 下

`orchestrator/tests/test_campaign_import_invariant.py:41-43` は逐語の bootstrap 文字列
`DIRECT_BOOTSTRAP` を定義し、`:931-947` で「main guard と実行時相対 import を両方持つ campaign file は、
その逐語 bootstrap をちょうど 1 つ、最初の相対 import より前に持つ」ことを要求する。

- `s8c_gate_report.py` は main guard と相対 import を両方持ち、bootstrap を持たない。
  **すなわち現在この規則に違反している。** `KNOWN_EXCEPTIONS` (10 件) に
  `BOOTSTRAP_RULE` の項目は 1 件も無く、gate report も載っていない。
- 赤になっていないのは、この test file 全体が growth hold 下にあり
  (`orchestrator/tests/growth_test_holds.py`、解放には `IZANAGI_RUN_GROWTH_HELD_TESTS` と
  明示のユーザー command が要る)、既定の走行に入らないためである。親が in-process で
  import しようとして `GrowthTestHoldBypassRefused` を受けたことで確認した。
- したがって本 wave の修正は、この潜在違反も同時に閉じる。**逐語一致が要件**である。
- `s8c_preregistration.py` は実行時相対 import を持たない (`importlib.import_module` を使う) ため
  この規則の対象外だが、逐語 bootstrap を既に 1 つ持つ。**新しい alias block を別の
  top-level 文として足しても `source.count(DIRECT_BOOTSTRAP) == 1` は保たれる。**

---

## 1. 所見の裁定

### 採用 (must-fix)

| # | 出所 | 裁定 | 対応 |
|---|---|---|---|
| A-1 | sol 7 / luna 1,15 | **real・blocker** 4 case 全評価は 313〜950 秒で 5 分上限に反する | プラン v2 で合成 tiny repo へ全面差し替え。新規 real repo 全評価は **0 回** |
| A-2 | sol 8 | **real** 合成 repo で安く踏める | (M-1) で親が実測確認。証拠契約あり版を採る |
| A-3 | sol 4 | **real** 三 module の共通故障で恒真化しうる | tiny repo の 3 module + 証拠契約は fixture が live bytes を copy して構築する。加えて oracle が一律 `*-blob-mismatch` / `*-absent-at-commit` / `evaluator-exception` でないことを assert する |
| A-4 | sol 5 | **real** CLI が `--commit` を採用した保証がない | `payload["commit"]` (gate は `payload["source"]["commit"]`) の exact 一致を assert する |
| A-5 | sol 9 | **real** `stderr == ""` は過剰 | `"Traceback" not in stderr` へ狭める |
| A-6 | luna 9 | **real** 焦点走に bootstrap meta-test が抜けている | 焦点集合へ `test_campaign_import_invariant.py` を追加する。hold で走らないことも実測して記録する |
| A-7 | luna 4 | **real** 新規 nodeid は所要台帳へ事後登録が要る | 親が最初の post-commit 焦点走の実測を取り、実装子が `--add-only` で登録する |
| A-8 | sol 12 / luna 13 | **P3 は一部 refuted** | `s8c_preregistration.py` のみ enforcement closure 内、`s8c_gate_report.py` は closure 外。記録を訂正し、closure への追加はしない |

### 不採用 (refuted)

| # | 出所 | 裁定 | 理由 |
|---|---|---|---|
| R-1 | sol 1 | **refuted・blocker 解除** `DECIDER_VERSION` bump | (M-2) の 3 点。とくに `spurious-revision` により発行不能 |
| R-2 | 親の追補 (P5) の「安い代替なし」 | **refuted** | (M-1) で親が自ら反証 |
| R-3 | luna 3 | **不採用** `sitecustomize` + `atexit` の identity 観測 | (M-1) により production 入口の**答え**を直接比べる方が安く強い。observer を足す必要がない |

### scope 外 (裁定パッケージ候補・本 wave では実装しない)

| # | 出所 | 内容 |
|---|---|---|
| S-1 | sol 6 | 新設検査は「alias を足す」代わりに「`isinstance` を緩める」実装でも通る。機構を強制する構造 pin は本 wave の scope 外 (ユーザーが「仮想リスク向けの gate・検査の追加は scope 外」と明示)。`_normalize_predicate_results` を不変とする不変条件、段 6 敵対レビュー、変異 matrix で守る |
| S-2 | sol 3,19 | 長寿命 process へ埋め込んだときの canonical alias 上書き。本 wave の契約は **fresh standalone process 限定**とする |
| S-3 | sol 21 / P4 | `_default_registry_results` の例外理由消失 (F631 の「なぜ通らなかったかが消える」) |
| S-4 | sol 20 | `s8c_gate_report.py` を campaign lock の source closure へ追加するか |
| S-5 | (M-3) | `test_campaign_import_invariant.py` の growth hold 解放 |

---

## 2. プラン v2 (確定)

### production 差分 (2 file だけ)

**(1) `orchestrator/campaign/s8c_preregistration.py:36-39`**

既存の bootstrap block は**逐語のまま残す**。その直後に、独立した top-level 文として
次を足す。

```python
if __name__ == "__main__":  # pragma: no cover - direct CLI execution
    sys.modules["orchestrator.campaign.s8c_preregistration"] = sys.modules[__name__]
```

- `if __package__ in {None, ""}` block の**外**に置くこと。`-m` 起動では `__package__` が
  既に設定済みで内側は発火しないため、内側に置くと `-m` が直らない。
- `setdefault` ではなく代入とする (段 2 の理由をそのまま採る)。
- 既存 bootstrap の逐語は 1 箇所のまま保つ ((M-3))。

**(2) `orchestrator/campaign/s8c_gate_report.py:10-16`**

`import sys` を追加し、相対 import の前に **逐語一致**の bootstrap を置く。

```python
if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"
```

`orchestrator/tests/test_campaign_import_invariant.py:41-43` の `DIRECT_BOOTSTRAP` と
**1 byte も違ってはならない** ((M-3))。1 つの top-level 文であること、
`from . import s8c_preregistration as _prereg` より前にあることも要件である。
gate report 側に canonical alias は足さない (直接起動でも core は通常の canonical import になる)。

### 新規 test file `orchestrator/tests/test_s8c_cli_entrypoints.py`

- **module scope fixture `tiny_repo`**: `tmp_path_factory` に空 directory を作り、
  `orchestrator/campaign/` の 4 file (`s8c_preregistration.py`,
  `s8c_preregistration_evidence.py`, `s8c_generation_projection.py`,
  `s8c_preregistration_evidence_contract.v1.json`) を **実行中の repo root から live bytes で
  copy** する。path は repo と同じ `orchestrator/campaign/<name>` にする。
  `git init` → `git -c user.email=... -c user.name=... add -A` → `commit` し、
  (repo path, resolved commit sha) を返す。**literal の sha を焼き込まない。**
- **module scope fixture `oracle`**: `P.activation_report_at(tiny_repo_path, sha)` を **1 回だけ**
  評価する。case ごとに再計算しない (sol 所見 7)。
- **oracle 健全性の事前 assert** (A-3):
  - 3 module それぞれについて `P.read_blob_at(tiny, sha, <PATH 定数>)` が live file bytes と一致。
  - oracle の 12 reason code が一律でないこと、かつ `evaluator-exception` /
    `*-blob-mismatch` / `*-absent-at-commit` を 1 件も含まないこと。
- **4 case を parametrize**: `prereg-path` / `prereg-module` / `gate-path` / `gate-module`。
  - 起動は `subprocess.run([sys.executable, <絶対 path or "-m" 形式>, ...], cwd=<repo root>)`。
  - prereg は `check --json --repo-root <tiny> --commit <sha>`、
    gate は `--repo-root <tiny> --commit <sha>`。
  - 検査: `payload` の commit が sha と exact 一致 (A-4)、
    `(id, status, reason_code)` の 12 組が oracle と exact 一致、
    `effective` が oracle と一致、`returncode == 1`、
    `"Traceback" not in completed.stderr` (A-5)。
  - status / reason の literal は**焼き込まない** (oracle 比較にする)。
- 末尾に `if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))`。

**現行 HEAD で落ちること (恒真でないこと)**: `prereg-path` と `prereg-module` は
12 件 `evaluator-exception` になり oracle と不一致で落ちる。`gate-path` は
`ImportError` traceback で stdout が JSON にならず落ちる。`gate-module` は現行でも通る対照である。
親が実装後に実測して確認する。

### やらないこと

- real repo HEAD に対する新しい全評価 subprocess を足さない (A-1)。
- `_normalize_predicate_results` の型検査・件数検査・id 集合検査を一切変えない。
- `DECIDER_VERSION`、条件凍結成果物、`docs/phase3-8c-preregistration.md` を触らない (R-1)。
- 既存テストの期待値を変えない。`campaign_lock.py` の enforcement closure を変えない (A-8)。
- `sitecustomize` などの observer を足さない (R-3)。構造 pin も足さない (S-1)。

---

## 3. 変異事前登録 (DW-M01、実装前に確定)

**重要な分類**: 本 wave の変異はいずれも**受理集合を変えない** (`effective` は全経路で false のまま)。
`DW-M08` に従い、これらは KILLED ではなく **diagnostic sensitivity pin** として別枠で記録する。
`DW-M03` の「診断文字列だけの赤を kill にしない」に該当するためである。

| id | 位置 | 変異内容 | 期待赤 node (完全集合) | 単一理由性 |
|---|---|---|---|---|
| M1 | `s8c_preregistration.py` の新 alias block | block を丸ごと削除 | `test_s8c_cli_entrypoints.py::test_cli_entrypoint_matches_library_report[prereg-path]` と `[prereg-module]` の 2 件 | 現行 HEAD がこの状態。他層で先に拒否されない |
| M2 | 同 alias block | `if __package__ in {None, ""}:` block の内側へ移動 | `[prereg-module]` の 1 件 | path 側は生き、`-m` だけが壊れる |
| M3 | `s8c_gate_report.py` bootstrap | `__package__ = "orchestrator.campaign"` 行だけ削除 | `[gate-path]` の 1 件 | `-m` は影響を受けない |
| M4 | 同 bootstrap | `sys.path.insert(...)` 行だけ削除 | `[gate-path]` の 1 件 | 同上 |

- 登録しないもの: `setdefault` 化 (fresh process では代入と同値で観測差なし)、
  `_normalize_predicate_results` の型緩和 (本 wave の変更行ではなく、
  alias 修正後は同じ型しか流れないため観測差なし)、新規 test file 自身の変異 (production 欠陥ではない)。
  いずれも sol 所見 18 と luna 所見 18 が一致して「帰属不能」と判定した。
- 期待 node は実装後の実 nodeid で `DW-M07` に従い再検証する。node が空の spec は起動前に中止する。

---

## 4. 段 5 の分割方針

編集 path は 3 file で相互依存するため、**単一の Codex 実装子 (一枚岩)** へ寄せる。
段 6 のレビューだけ 2 レンズ並列にする。
