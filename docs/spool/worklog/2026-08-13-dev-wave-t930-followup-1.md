---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t930-followup
seq: 1
title: [T-996] の残余を fail-open として書き直した — 「印が残る」ではなく「以後すべての読み込み時拒否が無効化される」 (docs のみ、branch worktree-dev-wave-t930-followup)
---

## 本文

[T-930] land 後、別 wave ([T-990]/[T-991]、conftest 面) が当方の残余記述を読んで
**「実際より軽く書かれている」と指摘した。親が一次資料で検算し、指摘は正しいと確定した。**

`orchestrator/tests/growth_test_holds.py` の import 時 enforcement 判定は

```python
if _ENFORCING_PYTEST_CONFIG_IDS:
    return function_names
```

であり、**特定の config が集合に居るかではなく、集合が空でないかだけを見ている。** したがって
`pytest_unconfigure` に到達しなかった session の印が 1 個でも残ると、その config と無関係な
**同一 process 内の以後すべての保留 module で、読み込み時拒否が無効化される (fail-open)**。
`id()` の再利用が起きるかどうかはこの形では論点にならない — 集合が非空でありさえすれば通る。

[T-930] の記述は「異常終了で整数が残る」「入れ子 session で先払いが復活する」という
**発生経路の書き方**になっており、性質が fail-open であることが読み取りにくかった。
**後から読む人が「整数が残るだけ」と読んで優先度を下げるのが最も危険**なので、[T-996] の
本文を性質ベースへ書き直す。

### 親が入れた補正 — 無効化されるのは読み込み時の層だけである

指摘元は「bypass 拒否の送出が止まる」と書いていたが、**実行そのものは止まり続ける**。
call-time wrapper (`_wrap_held_function`) は
`os.environ.get(RUN_GROWTH_HELD_TESTS_ENV) != RUN_GROWTH_HELD_TESTS_TOKEN` だけを見ており、
印の状態に依存しない。失われるのは「保留対象の高コスト fixture / helper を先払いしない」という
**コスト回避性**であって、保留 node の本体は exact token が無い限り実行されない。
両者を混ぜると逆に「実行も通る」と誤読され、二層設計の意味が失われる。

### 提案された所属検査は現状の形では実装できない

指摘元は `id(config) in _ENFORCING_PYTEST_CONFIG_IDS` の所属検査を提案した。性質は確かに
縮むが、**import 時の消費者は config を持てない** — テスト module の import 時点で「今どの
config が走っているか」を取る公開 API が無く、非空検査はその制約から出ている。直すなら
current config と照合する fail-fast autouse fixture を高コスト fixture より先に走らせる形になり、
正規経路の受理集合に触る。[T-996] の scope に残す。

### 受入の要否判定 (docs のみの wave)

実 repo の `docs/worklog.md` 本文を pin するテスト node は**不在**。判定手順は
`grep -rn "worklog.md" --include=*.py orchestrator/tests/` の全 hit を追い、`test_spool_fold.py`
(308 箇所が `tmp_path` / `_init_repo` の合成 repo)、`test_dev_wave_land.py`、
`test_dev_waves_checker.py` がいずれも合成 repo 経路であることを確認した。

**実測: 文書機構の焦点走 568 passed / rc=0** (`test_spool_fold.py` + `test_check_docs.py`、
計算ノード dispatch)。`tools/check_docs.py` rc=0、fold dry-run rc=0。

**同じ焦点走で `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が
赤になったが、docs fragment からは到達しえない面である。** 失敗は
`CertifiedWriterAuthorizationError: Pegasus compute では receipt state 内で一意な required
authorization_contract だけを受理する` で、実行認可の環境契約層である。同 node は当 wave の
受入全走 (02:00 JST) では緑であり、その後 20 分の間に環境側の条件が変わったことになる。
**並行 wave の receipt が output/ 系検査を赤にする既知の族** (受入全走の隣で子 process を
走らせない、の反対側から見た現象) と同型と判断し、当追補の帰属からは外す。
未 commit の fragment が原因という仮説は、commit 後の再走でも赤が残ったため反証済み。

## 次の一手差分

### 更新

- [T-996] **P3・fail-open の残余 (性質を書き直し)**: `growth_test_holds.py` の import 時
  enforcement 判定は集合の非空だけを見るため、`pytest_unconfigure` に到達しなかった session の
  印が 1 個残ると、**同一 process 内の以後すべての保留 module で読み込み時拒否が無効化される**。
  入れ子 `pytest.main(["--noconftest", ...])` はその一例にすぎず、`id()` 再利用は論点でない。
  **実行そのものは call-time wrapper (env token のみを見る) が止め続けるので、失われるのは
  コスト回避性である。** 所属検査 (`id(config) in ...`) への単純置換は、import 時の消費者が
  config を持てないため不可。直すなら current config と照合する fail-fast autouse fixture を
  高コスト fixture より先に走らせる形になり、正規経路の受理集合に触るため独立の裁定と
  敵対レビューが要る。指摘は [T-990]/[T-991] wave から。
  base: b3d0cc43e9b8d7970df9870f9fa0de350dad8e7f83accc00e60453f5668fd530
