静的レビュー判定は **NO-GO**。must-fix 3 件です。pytest は実行しておらず、緑は主張しません。

### C-1 — Major / real：certify 系が新 policy の symlink を受理する

- 深刻度・判定: **Major / real**
- 場所: [certify_calibration.sh:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:110)、[submit_certify.sh:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_certify.sh:56)
- 攻撃入力: `calibration_v1.json` を repo 外の regular JSON への、commit 済み symlink にする。`-f` はリンク先を追う一方 `-L` がないため通過する。commit 済みなら後段の dirty-tree gateも拒否しない。registry test は symlink を検出するが、要求された shell 自身の fail-closed にはならない。
- **成果物影響:** `source_commit` が予約秒・finalize reserve の実 bytes を束縛しなくなり、外部 bytes 由来の deadline・receipt・proof 参照を certification が使用できる。
- 最小 fix: 両方の `CALIBRATION_POLICY` 検査へ `|| -L "$CALIBRATION_POLICY"` を追加し、symlink を明示的に exit 2 とする。

### C-2 — Major / real：certify policy の型不正と Python 失敗を確実に拒否できない

- 深刻度・判定: **Major / real**
- 場所: [certify_calibration.sh:114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:114)、[certify_calibration.sh:136](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/certify_calibration.sh:136)、[submit_certify.sh:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_certify.sh:60)
- 攻撃入力:
  - `certify_walltime_s: "7199"`、`finalize_reserve_s: "500"`という数字文字列を与える。出力行数は変わらず、後段の `int()` と Bash 算術も通るため、型不正なのに exit しない。
  - さらに `certify_walltime_s` を改行入り文字列にして必要な後続値を埋め、`finalize_reserve_s` を欠落させる。Python は途中で失敗するが process substitution の rc は `readarray` に伝わらず、`>= 12` を満たせば欠落を見逃せる。
- **成果物影響:** PBS header は 7200 秒のまま、台帳の `elapstim_req_s`・reservation deadline・finalize window・acquisition receipt の値だけが変わり、予約 envelope と proof chain が食い違う。
- 最小 fix: floor 系と同様に Python stdout と rc を明示捕捉し、両値を `type(...) is int` かつ正値として print 前に検査する。rc 非 0 は行数に関係なく exit 2 とする。

### C-3 — Major / real：事前登録 M6 は期待 node に kill されない

- 深刻度・判定: **Major / real**
- 場所: [test_pegasus_tools.py:126](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:126)、[test_pegasus_tools.py:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:172)、[test_pegasus_policy_registry.py:273](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_policy_registry.py:273)、[s4-adjudication.md:103](/home/SFC/tanab/.claude/jobs/102c8fbd/tmp/t249-wave/s4-adjudication.md:103)
- 攻撃入力: M6 どおり `certify_walltime_s` を整数 `7199` にする。header test が参照するのは `certify_walltime` だけで、registry node も値を検査しない。したがって静的には期待 node のどの assert も変異の影響を受けない。`finalize_reserve_s` の整数 drift も既存の固定 formula 文字列と結び付いていない。
- **成果物影響:** テストで検出されないまま、実 PBS 7200 秒に対して receipt・reservation deadline が 7199 秒となるか、finalize reserve と報告 formula が不一致になる。
- 最小 fix: smoke/certify の `HH:MM:SS` と `_s` の相互変換一致を独立 assert し、`finalize_reserve_s` を既存の独立した 600 秒 formula/budget oracle に結び付ける。その後 M6 の期待 node を実測する。

### 反証済みの攻撃

- **Critical / refuted — 値・型の不一致:** [policy.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/policy.json:5)、[calibration_v1.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/policies/calibration_v1.json:3)、[floor_v1.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/policies/floor_v1.json:3)。7 key は値・`str`/`int` とも完全一致。成果物影響なし。fix 不要。
- **Major / refuted — 正常型入力での行数/index ずれ:** certify job は `3 shared + 2 calibration + 6 shared + perf候補` で index 0〜10、perf は11以降、`>=12`。certify submit は4、floor job は8、floor submit は4で、print順と代入順は一致。C-2 の malformed 入力を除けばずれなし。fix 不要。
- **Major / refuted — floor fail-closed・fixture 取り残し:** [floor_campaign.sh:208](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/floor_campaign.sh:208) と [submit_floor.sh:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/tools/pegasus/submit_floor.sh:134) は `-f/-L`、parse rc、厳密 int、要素数を検査。[test_pegasus_floor_tools.py:169](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_floor_tools.py:169) は新 file を fixture へ複製し、calibration fixture は [test_pegasus_tools.py:1024](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t249-pegasus-policy-split/orchestrator/tests/test_pegasus_tools.py:1024) の `copytree` で包含する。fix 不要。
- **Major / refuted — 共有値・protected path の誤変更:** 共有/site 値は4 shellとも `policy` 側から継続読取。`git diff 7b24f81` と protected path 限定 status に `policy.json`、`output/env/pegasus/**`、`orchestrator/qualification/**` の差分はなく、`policy.json` の現行/base SHA-256 はともに `b1c42e…961ac`。成果物影響なし。fix 不要。

## 総括

- must-fix: C-1 — certify 系2本の新 policy symlink 受理。
- must-fix: C-2 — 厳密型検査なし、process substitution の失敗 rc 消失。
- must-fix: C-3 — 事前登録 M6 は現行の期待 node に静的に到達せず SURVIVE。
- nit: 0 件。
- refuted: 7値・型、正常系 index、floor fail-closed、fixture、新旧 assert、共有値、protected bytes。
- 判定: **NO-GO**。pytest は未実行。