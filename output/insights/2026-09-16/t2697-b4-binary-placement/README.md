# [T-2697] B-4 凍結 spec の binary 配置規則 — 既存規約の兄弟に収め、ignored 複写で解いた

`authority: none`
`default_effect: no-state-change`

2026-09-16。wave `dev-wave-t2697-b4-binary-placement`、branch `worktree-dev-wave-t2697-b4-binary-placement`。
起点 local main `d97c423bdd14e0b416cb4f585d350e6c2b251287`、実装 commit `33d9b889b`。
可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 依頼と答え

依頼は「B-4 凍結 spec の `artifacts[].binary_relpath` が解決できる場所へ、調達済みの候補・参照
バイナリを配置する規則を決めて実装する。tracked 化・再 build・複写のどれを採るかが未定。
本題の配置規則と実装だけ」。

**答え: 複写を採り、既存規約の兄弟に収めた。**

```
binary_relpath = output/env/<env_tag>/binaries/<binary_sha256>
```

git-ignored (`.gitignore` の `output/env/*/binaries/`)。配置は
`python3 -m orchestrator.campaign.b4_binary_record place --record <r.json> --source-root <durable> --env-tag <tag>`。

## 規則を発明しなかった — 既に production にあった

段 2 plan は新しい namespace `output/b4-binaries/` を提案し、「campaign 軸でも env 軸でもない
campaign 横断の実験補助 store」と位置づけた。**親が段 4 でこれを退けた。**

`s8b_floor_campaign.py:7669` が既に測定用 binary をこう置いている。

```python
store_root = Path(env_scope_dir(protocol["env_tag"], output_root=str(out_root))) / "binaries"
```

`layout.py:600 env_scope_dir` = `<output_root>/env/<env_tag>`、`layout.py:41 repo_output_root` =
`<repo>/output`。親の実測では `env_tag` の実値は `pegasus` と `linux-baremetal` の 2 つだけで
(`env_contract.py:256,296`)、`output/env/pegasus/` には既に `calibration` と `profile` が並ぶ。
**`binaries` はその兄弟である。** 新しい分類を起こす必要はなかった。

この発見は**段 2 の後**に出た。plan 子の prompt には間に合わず、親が段 3 レンズ B の prompt へ
射影して突き合わせさせた。レンズ B は既存規約側を支持し、同時に重要な限定も付けた。

- **B-4 対照対 driver は `s8b_floor_campaign` を通らない。** 親の実測で
  `grep -n "floor_pair_driver" orchestrator/campaign/s8b_floor_campaign.py` は **0 件**、
  `floor_pair_driver` の consumer は `p3_b4_floor_artifact_issuer.py` だけである。
  **規約統一の理由は実行経路の共有ではなく、同種の物に 2 つの置き場を作らないことである。**
- **path の env 成分は検査されない。** 消費側は `binary_relpath` の env 成分と
  `environment.env_tag` を照合しない。**環境整合の gate と説明してはならない。**

## tracked 化しなかった理由と、凍結の限界

消費側の非対称が根拠である。`floor_pair_driver.py:614 _read_tracked_bound` は spec・build
receipt・calibration に loaded HEAD blob との byte 一致まで要求するのに、**binary だけは通らない**
(`:1136` / `:2112` は `_resolve_regular` + `assert_binary_sha256` + `_assert_no_trace_symbols` のみ)。
段 3 レンズ A は repo の tracked executable 58 件の先頭 bytes を読み、**ELF は 0 件**と実測した。

**ただしレンズ A の要求どおり限界を明記する。** ignored 案が凍結するのは
**path・期待 sha256・receipt であって bytes の可用性ではない。** 全複製を失えば消費側は
正しく拒否するが、bit 同一の復旧は保証されない (再 build が bit 一致する保証はなく、
T-2636 は計算ノード 3 回でようやく成功している)。

## 生死確認を最初に置いた (DW-G01)

実装前に、**repo 外の現物 binary へ消費側の検査を直接かけた。**

| 検査 | 結果 |
|---|---|
| `buildcache.assert_binary_sha256` | OK |
| `buildcache._assert_no_trace_symbols` | OK |
| size / mode / `os.access(X_OK)` | 701,760 / 0o744 / True |

**欠けているのは repo 相対 path に在ることだけ**と分かり、依頼の枠組みが実測で裏づいた。

## 実装 — 上流の検査を複製しない

`place_record` の固有責務は 6 つだけとした。**入口で validator を呼び直さない。**

親が現物で確認した上流の実効 gate:

| 検査 | 位置 |
|---|---|
| portable record + admission の検証 | `s8b_floor_campaign.py:5787-5795` |
| source bytes の sha256 照合 | `:5825-5831` |
| 既存 destination の sha256 照合 | `:5833-5839` |
| 書込み後の sha256 照合 | `:5860-5862` |

段 3 レンズ A がこの重複を先に指摘していた — **複製すると変異が上流に mask され、
「検証省略を殺した」という判定が偽になる。** 変異事前登録でも、この 3 つを狙う変異は登録しなかった。

portable record をそのまま `store_binaries` へ渡せない理由も親が検算した。
`:5729-5732` は `binary` の**絶対** path を、`:5774-5781` は `store_path` が絶対かつ
`store_root/<sha>` と一致することを要求するのに、portable record の両 field は
`binaries/<sha>` の相対形である。**メモリ上のコピーで 2 つの path だけを絶対化する**のが
最小の橋渡しになる。元 record は 1 byte も変えない。

実行権限は `store_binaries` ではなく呼び手が付ける (`b4_binary_record.py:142-143` と同型)。

## 段 6 の敵対レビューが受理集合の拡大を 1 件見つけた

レンズ B (API 整合・実行時の現実性・所有境界) は **must-fix 0**。
レンズ A (正しさ・受理集合・恒真化) が **1 件**を出した。

**配置用コピーへ `binary` key を存在確認なしに書き込んでいた。**
`s8b_binary_admission.py:343-346` は portable record の **exact key 集合**を要求するので、
`binary` を欠く record は本来拒否される。ところが補修すると、拒否すべき欠損 record から
配置物と成功 relpath が生まれる。**規律 2 に触れる受理集合の拡大である。**
他の必須 field は既に読まれていて欠落すれば `KeyError` になるのに、`binary` だけが
読まれずに補われていた。**同じ扱いに揃えて閉じた。**

恒真なテストも 1 件見つかった。ignored 判定の untracked 側が、新規 `git init` した fixture repo で
**何もしなくても必ず緑**だった。`git add -A` の後に非追跡を確かめる形へ直した。

レンズ A が反証した筋も記す。現行 policy の迂回は無い (`:5813-5820` が公開 resolver の policy を渡し、
`s8b_binary_admission.py:368-372` が照合する)。元 record の内容変更も静的に追跡して見つからなかった。

## 変異 matrix

`repo_head = 33d9b889b4f92ac624fae9e97d8e43b7861711c0`。runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_b4_binary_record.py -rf`、
`--runner-mode dispatch`。

**baseline = PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0、期待 node 完全一致。**

| id | 変異 | 殺した node 数 |
|---|---|---|
| M1 | destination 導出から `env_tag` 成分を落とす | 3 |
| M2 | owner execute bit の付与を外す | 1 |
| M3 | 返り値を repo 相対でなく絶対 path にする | 3 |
| M4 | source の非 symlink / regular file 解決を外す | 1 |
| M5 | コピーの `binary` を絶対化しない | 7 |
| M6 | コピーの `store_path` を destination に設定しない | 7 |
| M7 | `.gitignore` の `output/env/*/binaries/` 行を消す | 1 |
| M8 | 欠損 `binary` key の guard を消す (段 6 の must-fix 由来) | 1 |

**登録しなかった変異**: 入口での validator 再呼出し (上流 `:5787-5795` に mask される)、
既存 destination の上書き (`:5833-5839` に mask される)、receipt 由来 pin の期待値渡し
(自己一致で恒真。レンズ A が指摘)。

### 単一理由性 (DW-M03) の確認

段 6 レンズ A は「M1/M3 と M5/M6 が同じ node で落ちるので単一理由性を満たさない」と指摘した。
**probe 走の観測で半分は反証された。**

- **M1 と M3 は node 集合が異なる。** M1 = {配置 path, ignore, CLI}、M3 = {canonical, 配置 path, CLI}。
  期待集合の完全一致 (`DW-M08`) で区別できる。
- **M5 と M6 は 7 node で完全一致する。** 区別は赤の理由で行う。probe 走の stdout を親が数えたところ、
  M5 は `record.binary が絶対 path でない` だけで `store_path が content address と不一致` は **0 件**、
  M6 は後者が 14 件だった。**別の上流 gate に当たっている。**

## 変異走行が 6/8 で止まった — 配置物が M7 と干渉する

1 回目の probe 走は `mutation harness aborted: runner/test 実行前に untracked file を検出` で
M7 の手前で中止した。**因果は次のとおり。**

1. 親が実データ 1 走で現物 binary を `output/env/pegasus/binaries/<sha>` へ置いた。
2. M7 は `.gitignore` からその ignore 行を消す変異である。
3. 変異適用後、置いた binary が untracked として現れる。
4. harness の走行前 clean-tree 検査が全体を中止する。

**配置物を退けてから再走して解いた。** 実データ 1 走と変異走行は同じ worktree で重ねられない。
成果物 `mutation-probe-result.json` (M1〜M6 の観測)、`mutation-probe2-result.json` (M7・M8 の観測)、
`mutation-final-result.json` (本走) を本 dir に置く。

## 実走の記録

- 自走 harness (`PYTHONPATH=. python3 orchestrator/tests/test_b4_binary_record.py`): **32 passed / rc=0**。
- 親の実データ 1 走 (fix 後にやり直し): 現物 701,760 byte を `place` で新規配置し、
  `_relative_path` → `_resolve_regular` → `assert_binary_sha256` → `_assert_no_trace_symbols` の
  **4 検査すべて OK**。mode 0o744 / X_OK True / 非 symlink。2 回目も同じ path (冪等)。
  `git check-ignore` は `.gitignore:20` に当たり、`git ls-files` に現れない。
  **700KB を置いても `git status` は実装 3 file しか出さない。**
- provenance full 監査: 実装 commit 後 10,466 件、main 取り込み後 10,497 件、いずれも新規違反なし。
- 受入全走の結果は worklog へ書く。

## real だが scope 外 (裁定パッケージ候補)

1. **policy の時間依存** (段 3 レンズ B)。`s8b_floor_campaign.py:5813-5820` が現行 policy を必ず渡し、
   `s8b_binary_admission.py:368-372` が receipt の policy sha 一致を要求するため、
   **古い policy で発行された record は後から配置できない。** 消費側は `expected_policy=None` で受ける
   (`floor_pair_driver.py:1097-1100`)。**緩めていない** — 主張の射程を「`place` による復旧は
   receipt の policy が現行と一致する record に限る」へ狭めた。現物 record の `policy_sha256` は
   現行と一致する (`949ddcc295…`) ので本件は今日止まらない。
2. **運用手順**。ignored file は merge で他 checkout へ移らないので、測定を投入する担当が
   投入前に使用する各 checkout へ配置する必要がある。CLI help に 1 行入れた。新しい機構は足していない。
3. `store_binaries` の docstring (`:5809-5810`「out_root 相対」) と実装 (`:5863` 絶対 path) の不一致。
   **触っていない** — 同 file は並行 wave t2650 が所有している。
4. ELF テストは `g++` と `nm` の実在に依存する。skip guard は足していない (テストを弱めるため)。
   本環境には両方実在し、32 passed を得ている。
