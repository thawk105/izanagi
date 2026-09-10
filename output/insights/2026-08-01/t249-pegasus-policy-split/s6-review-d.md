結論は **NO-GO** です。pytest は実行していません。read-only で AST helper だけを直接評価し、実走結果を「緑」とは扱っていません。

### 1. Major / real — live consumer 検査は一般的な読み方で迂回できる

- 場所: [test_pegasus_policy_registry.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:86)、[同:131](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:131)、[同:242](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:242)、[同:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:259)
- 攻撃入力: 次はいずれも shared policy の live read だが検出結果は `[]` だった。
  - `KEY = "certify_walltime_s"; p[KEY]`
  - `p["certify" + "_walltime_s"]`
  - `Path("tools") / "pegasus" / "policy.json"` 経由の load
  - shell の `KEY=certify_walltime_s; jq -r ".$KEY" "$POLICY"`
  - suffix のない tracked executable（走査対象が `.py` / `.sh` 限定）
- 成果物影響: task policy 更新後も旧 shared 値を読む consumer が残り、`qsub.elapstim_req_s`、予約 deadline、試行の成功/timeout 判定がずれて、試行台帳と certified 候補の受理集合を変えうる。
- 最小 fix: shared policy 読みを単一 accessor に集約し、返せる key を閉集合化する。現 scanner を維持するなら、少なくとも定数伝播、文字列結合、jq、suffix なし executable を fail-closed にし、それぞれ positive control を追加する。

完全な恒真ではありません。直書き入力は `[(3, "certify_walltime_s")]`、base `7b24f81` の M5 形は `certify_walltime_s` と `finalize_reserve_s` の 2 件を検出しました。したがって Critical の「何も検出できない」は refuted ですが、保証範囲の主張は実装より広いです。

### 2. Major / real — subdirectory は未登録のときだけ素通りする

- 場所: [test_pegasus_policy_registry.py:310](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:310)
- 攻撃入力: tracked な `tools/pegasus/policies/task/new_v1.json` を作り、registry は変更しない。`iterdir()` が見る `task/` は `is_file() == False` なので nested file は発見されない。逆に正直に registry へ登録すると `extra` として拒否される。
- 成果物影響: nested policy を consumer が読むと、予約値は試行・選択へ効く一方、inventory から所在参照が欠落し、材料レポート／試行台帳から支配設定を辿れなくなる。
- 最小 fix: flat layout が契約なら registry 以外の directory/special entry を明示拒否する。nested を許すなら recursive regular-file 集合と exact 一致させる。

### 3. Major / real — registry 自身と symlink ancestor が無検査

- 場所: [test_pegasus_policy_registry.py:275](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:275)、[同:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:291)、[同:321](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:321)
- 攻撃入力:
  - tracked registry の worktree 実体を同内容の外部 symlink に置換すると、read は追従し、registry は entry 検査対象外、tracked 検査も index path だけなので素通りする。
  - `tools/pegasus/policies/` 自体を外部 directory への symlink にし、同名 3 file を置く。子 file の `is_symlink()` は false、`is_file()` は true、index 上の path は tracked のため素通りする。
- 成果物影響: 外部 calibration/floor 値が `requested_s`、`deadline_epoch`、receipt の予約値へ入り、試行台帳と timeout による certified 受理集合を変えうる。
- 最小 fix: registry を読む前に registry と `_POLICY_DIR` を `lstat` し、repo root から対象まで全 path component の symlink を拒否して、strict resolve 後の repo containment も確認する。

### 4. Major / real — tracked 検査が literal path ではなく Git pathspec

- 場所: [test_pegasus_policy_registry.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:44)
- 攻撃入力: untracked regular file を文字どおり `tools/pegasus/policies/*.json` という名前で作り、その文字列を registry に登録する。`git ls-files --error-unmatch -- tools/pegasus/policies/*.json` は既存 tracked JSON に pathspec match して rc=0 になる。現 checkout でも `_git_tracks("tools/pegasus/policies/*.json") == True` を確認した。
- 成果物影響: dirty checkout では config が存在して gate を通る一方、clean checkout では file が欠落して consumer が exit 2 となり、certified 選択・材料レポート・試行台帳が生成不能になる。
- 最小 fix: `git ls-files -z` を一度取得し、decoded path の exact set membership で判定する。少なくとも `:(top,literal)` pathspec を使う。

### 5. Major / real — M6 は殺せない

- 場所: [test_pegasus_tools.py:126](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:126)、[calibration_v1.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/policies/calibration_v1.json:5)、[submit_certify.sh:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_certify.sh:70)
- 攻撃入力: `certify_walltime_s: 7200 → 7199`。既存 node は PBS header と文字列 `certify_walltime == "02:00:00"` しか照合せず、秒値との相互変換一致を検査しない。新 registry node も policy 内容を読まない。
- 成果物影響: scheduler は `#PBS` の 7200 秒を使う一方、receipt の `qsub.elapstim_req_s`、job の `reservation.requested_s` と `deadline_epoch` は 7199 となり、試行台帳が実予約と不一致になる。
- 最小 fix: calibration node に `HH:MM:SS → 秒` の照合を追加し、smoke/certify の文字列値と `_s` 値をそれぞれ一致させる。

### 6. Minor / real — task policy の正当な read を過剰拒否する

- 場所: [test_pegasus_policy_registry.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:157)、[同:336](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:336)
- 攻撃入力: shared file の `with ... as handle` 内に、同じ変数名 `handle` を使う task-file の nested `with` を置く。外側の `ast.walk()` が内側の `json.load(handle)` まで shared handle load と誤認し、task の `certify_walltime_s` readを finding にした。
- 成果物影響: certified 選択・レポート・台帳の値や参照は変わらず、等価な consumer refactor の開発受理集合だけを縮めるため nit。
- 最小 fix: handle 名でなく AST binding/scope ごとに provenance を追跡し、nested binding を shadowing として扱う。

なお、コメント／通常の docstring だけの言及は AST 上 read にならず、誤検出しませんでした。この攻撃は refuted です。

### 7. Minor / real — dead file 登録は通る（既知 nit）

- 場所: [test_pegasus_policy_registry.py:290](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:290)
- 攻撃入力: consumer のない tracked `dead_v1.json` を直下へ追加し registry に sorted 登録する。内容/schema/consumer は検査されないため受理される。
- 成果物影響: live consumer がなく、certified 選択・材料レポート・試行台帳はいずれも変わらないため nit。
- 最小 fix: なし。所在 inventory という裁定どおりであり、owner/consumer 対応検査への拡張は別裁定。

反証できた点として、dotfile は `iterdir()` に含まれ、registry 以外の file は名前によらず列挙されます。directory 不在は registry read で例外となり赤、registry 除外も exact path 一件だけです。通常の Git 非 zero rc は finding または例外になり、cwd は `_REPO` 固定です。node も [pytest.ini:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/pytest.ini:13) の `testpaths`、`test_*` file/function、自走 harness を満たします。ただし収集・実行は未実測です。registry 自身も「所在 inventory」以上の再導出元を名乗っていません。

## 総括

must-fix: #1 live scan 回避、#2 nested 閉集合穴、#3 registry/ancestor symlink、#4 pathspec tracked 偽陽性、#5 M6 生存。nit: #6 過剰拒否、#7 dead file。refuted: 完全恒真、dotfile、directory 不在、緩い registry 除外、cwd/rc 握り潰し、コメント/docstring、registry の過大な名乗り。
| 変異 | 静的 kill 判定 |
|---|---|
| M1 | kill 可 — discovered に calibration が残り missing |
| M2 | kill 可 — 直下 tracked file が discovered に増える |
| M3 | kill 可 — registry 自身の `_git_tracks` が false |
| M4 | kill 可 — leaf `is_symlink()` が finding |
| M5 | kill 可 — base 形で移設 key 2 件を検出 |
| M6 | **kill 不可** — 秒値と walltime 文字列の一致検査なし |
| M7 | 正例受理可 — 直下 regular・tracked・sorted 登録なら赤条件なし（未実走） |