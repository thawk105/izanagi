# [T-066] stock_common / system_gate・ident_all flags golden 化 — 逐語・変異台帳 (2026-07-23)

対象 wave: `worktree-dev-wave-ruling-ac`。設計判断の正本は `docs/decisions.md` D81。
worklog 該当エントリ = 2026-07-23 (3)。

## 0. 生死実験 (brief 前、実測)

`campaign/s1_known_axes_freeze.py::_stock_common()` の戻り値 (`"flags": defaults,` → 999 破壊) を
一時編集し、`campaign/`・`s1`・`s8b`・`oracle` 関連の全テストを実走した。

- `test_s1_measurement_freeze.py` (16 tests): **0 件赤** — `K.build_document` の monkeypatch echo に
  完全に吸収され、意味内容の破壊を一切検出しなかった
- 他ファイルは 12 件赤 — ただし原因は大半が「ファイルを編集した」ことによる generator sha256
  自己ハッシュ不一致であり、stock_common の意味内容が検査されて落ちたわけではない
  (`test_verify_rejects_tampered_source_copy` は無関係な regex 不一致で落ちた)
- 直後に `git checkout` で復元し、96 passed / 1 skipped (submodule 起因) に戻ることを確認した

## 1. 敵対相談 (段3、codex max、並列2レンズ)

### 相談A (正しさ境界レンズ) — 5件 real
1. P3 (system_gate/ident_all は golden 保護済みだから対象外) は誤り。両者の flags は
   `axis_trigger_gating._BASE` と `s8a_trigger_sweep._genome(1)` の相互一致だけで、外部固定 golden
   が無い。`_BASE["WAL"]` を 0→1 に変異させても両者が一致したまま `build_document()` が成功する
   ことを in-memory で実測した
2. dict 等価は型を固定せず、`BACK_OFF=True` でも `True == 1` により false green になる (bool は
   int のサブクラス)
3. submodule 未 init 環境では対象テストごと skip し、既存 assertion も含め何も検出しない
   (対象テスト全体の既存性質であり、追加固有ではない)
4. 事前登録変異の「単一理由」は対象テストだけを選んだ結果であり、production ファイル一時編集中は
   generator hash 起因の別失敗が同時に起きている (最終 diff には影響しない)
5. mutation 検証時の一時編集と並行 process の race は理論上あるが、親が単独直列で実施する限り
   発生しない

### 相談B (整合・実効性レンズ) — NO-GO 判定
- stock_common 4値だけの pin は D73(6) が定義した「実 extractor + 独立全文 golden 比較」を実現しない
- sort comparator 差替え (`sp_dd` の名前を保ったまま実装だけ変える) が測定に直結する実例で検出
  不能なままである
- P3 は相談Aと同じ理由で否認
- test-local 定数は production の `EXPECTED_*` と実効契約が違う (production 側は生成時 fail-closed、
  test-local は regression pin) ため、その非対称性を「閉じた」と過大に書いてはいけない

## 2. 親裁定 v1.2 (段4)

stock_common に加えて system_gate/ident_all の flags も同じ性質の欠落と認め scope に含めた
(test-local `EXPECTED_STOCK_COMMON`/`EXPECTED_TRIGGER_FLAGS` + 型厳密 helper)。
sort/backoff/p2 の comparator・predicate・source 集合の独立 golden 化は scope 外とし、根拠を
「dangling `frozen_at_head` (D71(7)(a) 参照) により到達不能」と記録した。

**この根拠は誤りだった (下記段3で訂正)。**

## 3. 実装 (段5、codex high) と受入 (段5.5、親)

`orchestrator/tests/test_s1_known_axes_freeze.py` のみへ 32 行追加 (production ファイル無変更)。
親が M1〜M3 を1件ずつ直列で実測 (一時編集 → 対象テスト単体 → 復元):

| 変異 | 対象 | 結果 |
|---|---|---|
| M1 | `_stock_common()` の `"flags": defaults,` → `{**defaults, "BACK_OFF": 999}` | 単一理由で red、復元後 green |
| M2 | `axis_trigger_gating._BASE` の `"WAL": 0` → `1` | 単一理由で red (system_gate.flags で捕捉)、復元後 green |
| M3 | `_stock_common()` の `defaults[flag] = int(...)` を `bool(int(...))` へ | 単一理由で red、復元後 green。naive `==` 版の反証も実測 (`True == 1` → helper 無しなら green のまま) |

M2 は最初に `system_gate.flags` の assertion で落ちるため、`ident_all.flags` 側の検査が独立に
効いているかを別途 in-memory で確認した — `system_gate` だけ正しいまま `ident_all.flags["WAL"]`
だけを壊すと `ident_all` 側の assertion 単独で red になることを確認済み。

親の受入全走 (repo root から): **2815 passed / 18 skipped / 0 failed** (baseline と一致、退行 0)。
凍結成果物 sha256 (`known_axes_freeze.json` = `354f4b87…`、`measurement_freeze.json` = `203de36b…`、
`holdout_freeze.json` = `315b1eb8…`) は実装前後で不変。

事故: 最初の受入全走を `orchestrator/` を cwd にして実行し、`test_run_tests_task_run.py` の2件が
無関係な cwd 依存 (nested pytest subprocess の plugin import パス) で偽赤になった。repo root から
再実行して解消したことを、reverting の git stash 経由で確認した (差分を stash → repo root 実行で
green 確認 → stash apply で復元 → drop)。

## 4. 敵対レビュー (段6、codex max、並列2レンズ) — 両方 NO-GO

両レビューが独立に同一の core 所見へ到達した:

**Blocker: 「dangling frozen_at_head のため全文 golden は到達不能」という親裁定の根拠は誤り。**

- 引用 decision 番号の誤り: 該当は **D71(7)(b)** (親は誤って (a) と記載。(a) は holdout freeze の
  design_source drift で別件)
- `if doc != expected_doc` の行番号誤り: **765行目** (親は761と記載)
- 現行 worktree で `M.verify()` (canonical file) を実走すると、ancestry 検査 (747行目) より**先に**
  source hash 検査 (729行目) が `s8a_trigger_sweep.py` の drift で失敗する。ゆえに「ancestry が
  先に止める」は現状に当てはまらない (実測: `source sha256 不一致: ...s8a_trigger_sweep.py
  recorded=3e94735a... actual=8c3abd48...`)
- より重要な点: canonical file の状態に関わらず、**test-owned な `build_document()` (引数なし、
  実HEAD/実ccbench_pin を使用) は `verify_document()` に自己無矛盾で通る** ことを実測で確認した
  (`doc = M.build_document(); M.verify_document(doc)` → 例外なし)。dangling ancestor は
  canonical file 固有の問題であり、test-owned な自己検証を妨げない

レビューはさらに、上記の self-consistency 経路が「build_document() の抽出ロジック自体のバグ」は
検出しない (二重生成の一致は自明に成立するため) こと、真の regression 検出には comparator/
predicate/source を含む**外部固定** golden が別途必要であることも指摘した (親が追加で確認・
整理: self-consistency は tamper/drift 検出であり、抽出ロジックの正しさの独立検証ではない —
両者を混同しない)。

## 5. fix ラウンド (段6.5)

親が上記3点 (D71(7)(a)→(b)、761→765、「ancestry が先に止める」という誤り) を自分で再検証した上で、
低コストで実装可能な positive control を追加した:

```python
def test_build_document_is_self_consistent_and_detects_tamper():
    _require_submodule_sources()
    doc = M.build_document()
    M.verify_document(doc)
    tampered = copy.deepcopy(doc)
    tampered["what"] = "TAMPERED"
    with pytest.raises(M.FreezeError, match="機械再構成と不一致"):
        M.verify_document(tampered)
```

fix 後の親の受入全走: **2816 passed / 18 skipped / 0 failed** (baseline+1新規テスト、退行0)。
凍結成果物 sha256 は不変。

## 6. scope の最終確定 (T-066 は未完了)

**閉じたもの:** stock_common (4 flags) と system_gate/ident_all (5 flags) の golden 欠落。
実 build_document() の自己無矛盾性 + 単一フィールド改竄検出の positive control。

**閉じていないもの (T-066 の本体が未消化):**
- `test_s1_measurement_freeze.py` の `K.build_document` monkeypatch echo は無変更のまま
  (このテスト自体は隔離目的として温存する判断は据え置き — 変更していない)
- comparator (`sort_best.comparator`)・predicate (`gate_predicate`)・source record の path/
  sha256/key/lines・p2_2/backoff_fixed/sort の flags・label・reference fields は、いずれも
  外部固定 golden が無いまま残っている。両レビューは in-memory 変異で以下がすべて現行の
  全 assertion (今回追加分を含む) を通過することを実測した: sort comparator の破壊、
  system_gate/ident_all predicate の破壊、全 source record の偽装、P2 flags の破壊、
  backoff flags の破壊
- 現行の `test_verify_rejects_one_byte_freeze_tamper` (canonical file 対象) は、S-1 source drift
  (`s8a_trigger_sweep.py` 他、既知の未解決事象) により**現状は無改竄でも同じ理由で red になる
  可能性が高い** — positive control として false green になっている疑いがある。本 wave では
  検証・修正しない (別件)

## 7. 裁定パッケージへの追記 (D71(9)/D72(11) 系への新事実)

- sort comparator 差替え攻撃 (名前 `sp_dd` を保ったまま実装だけ変える) の具体シナリオが、
  現行の全 golden 検査 (今回追加分を含む) を通過することを実測した。将来 T-066 を本体まで
  消化する wave では、この攻撃を外部固定 golden で塞ぐことを要件に含めること
- `test_verify_rejects_one_byte_freeze_tamper` の positive control 疑義 (S-1 source drift による
  false green の可能性) を棚卸し対象として追記する

## 8. 復元検査の記録

M1〜M3 いずれも `git diff --stat` で1行変更のみを確認 → `git checkout --` で復元 →
`git status --short` で空を確認、という手順を直列で実施した (並行 process 無し)。
一時バックアップに使った `/tmp` ファイルが共有ジョブ環境で他プロセスに削除される事故が
一度発生したが、対象ファイルは git 管理下だったため `git diff --stat` の1行差分確認と
`git checkout --` で問題なく復元できた (教訓: production ファイルの一時変異は `/tmp` バックアップに
頼らず、tracked ファイルなら `git diff`/`git checkout` を復元経路の正本とする)。
