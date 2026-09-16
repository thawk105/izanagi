# 段 4 裁定 追補 2 (erratum-2) — 単位 B / C の順序と所有の移管

**正本の関係:** `stage4-ruling.md` と `stage4-erratum-1.md` を追記で訂正する。
衝突したら**番号の大きい追補が優先**する。

**発生:** 単位 B (shell consumer) の実装子が編集前に fail-closed で停止した (差分 0)。
**裁定 §5 の「B と C で同じ test file を触る必要が出たら、その file は C の所有とし、
B は報告して止める」に正しく従った結果である。子の判断は正しい。**

停止理由 (B が静的に確認した波及):

- `tools/pegasus/t126_qualification.sh` (B 所有) を staging root 経由へ切り替えると、
  `orchestrator/tests/test_t126_pegasus_tools.py` (**C 所有**) の共有 fixture が成立しない。
- 具体的には `_attempt` / `_submit_fixture` が **staging root の外**に依存 source を作り、
  **旧 policy locator を設定**している (`:4573` 付近)。
- `_install_job_dependency_marker` は**旧 locator に対する `git rev-parse HEAD`** を監視する。
- `test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value[canonical]` が
  その監視 marker と旧 path の診断文を要求する。

## 追補の決定

### (1) 単位 B と C を**直列**にする。B は C の後。

裁定 §5 は「A を完了させてから B と C を並列投入する」としたが、**B と C の所有は素集合ではなかった**。
T-126 は shell (`t126_qualification.sh`) と Python (`submission.py` / `identity.py`) の両方から
同じ fixture 群へ結合している。

- **C を先に完走させる** (実行中のものをそのまま使う)。
- C の所有 path 限定 patch を B の worktree へ展開する。
- **その後に B を投入する。**

### (2) `orchestrator/tests/test_t126_pegasus_tools.py` の所有を C から B へ移す (C 完了後)

C は Python 側 (`submission.py` / `identity.py`) の付け替えに必要な範囲だけを直す。
**C 完了後、同 file の所有は B へ移る。** B は shell 側の結合 —
`_attempt` / `_submit_fixture` の依存 source 配置、`_install_job_dependency_marker` の監視対象、
`[canonical]` node の診断文 — を staging root 基準へ直す。

**二重所有にはしない。** 時点で切り替える。C が触った後の版を B が受け取る。

### (3) 検出力を落とさない

fixture を staging root 配下へ移すとき、**次の検出力を 1 つも落とさない。**

- 依存 source の HEAD が pin と一致することの監視 (`_install_job_dependency_marker` の目的)。
- pin 不一致・dirty・不在の fail-closed とその診断文の exact 検査。
- `[canonical]` node が検査している reservation policy の受理・拒否集合。

**「旧 path の診断文を要求する assert を消す」だけで緑にしてはならない。**
新しい path に対する同じ強さの assert へ移すこと。移せないなら報告して止める。

### (4) 期待赤の更新

C 完了〜B 完了の間、`orchestrator/tests/test_t126_pegasus_tools.py` は赤でよい。
B の完了をもって、単位 A / B / C すべての期待赤が解消していなければならない。
解消しない赤は**回帰**として段 6 の must-fix に上げる。

### (5) 親の手順の誤りとして記録する (段 8 候補)

**所有を素集合に割る判断を、file 名の重なりだけで行った。**
実際の結合は test の**共有 fixture**を経由しており、file 一覧を見るだけでは出ない。
段 4 で分割を決めるとき、各単位が触る production file の**consumer test を fixture 単位まで**
辿るべきだった。luna §7 が「素集合に割れる」と言ったのも同じ粒度の見落としである
(親はそれを採用した)。
