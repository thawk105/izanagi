# [T-1998] balanced stock-inline precheck
- 目的: 同一 env・同一 source の stock-inline 対照が既存機構だけで成立するかを、結果を見る前に判定する。
- 状態: 中断
- 最終更新: 2026-08-28 01:42 JST
- 基準コミット: f34e19be94a3608099773ac6c1a12a98ae992048

## 完了した中間成果

- クラス3起動手順、dev-wave dispatcher、DW-C00/C01/STOP/O08、Skill自己改善契約を読了。
- 専用 worktree `worktree-dev-wave-t1998-balanced-stock-inline-precheck` を作成し、submodule を再帰初期化した。
- 稼働 T-1905 の所有 path は `tools/pegasus/b10_backoff_shape_campaign.sh` と
  `orchestrator/tests/test_b10_backoff_shape_sweep.py`。今回の read-only precheck との既知コード path 衝突は 0。
  将来 launcher/consumer の非コード資源を含む重複は、予定 path 未確定のため未証明。正式測定は起動しない。
- 裁定控えは T-1998 を含まず、かつ自身を「裁定の証拠ではない」と明記する。canonical は
  worklog (1034)、D20、D1137 とする。

## 段1 brief

- scope: 専用 prereg、同一 source/env stock-inline build、launcher、result consumer、正式測定認可を
  `rg` と既存 artifact で棚卸しし、既存機構だけで閉じる場合に限り最小 prereg を作る。
- 確定裁定: 診断 build/perf 下 throughput は headline 非適格 (D20)。既存 balanced profile は
  headline 利得を説明しない (D1137)。正式測定の人間認可は代行しない。
- 不変条件: trace-disabled の variant/baseline を別走で揃え、verifier を性能値から分離する。
- 不変条件: 診断 build 値を headline に流用せず、絶対規律2を緩めない。
- 成果物: 成立時は結果を見る前の専用 prereg と worklog fragment。不成立時は欠ける最小部品と
  ユーザー手番をこの handoff に記録して停止する。
- 分割方針: 実装差分ゼロを前提とする軽量版。実装が必要なら本 wave では作らず、別変更単位の
  D95 Codex author へ送る。
- 実測環境: precheck は Pegasus login node 上の read-only 検査だけ。build・benchmark・正式測定は行わない。
- (P1) 既存 `backoff_profile.py` の build/launcher は診断 profile 専用で、headline 用 stock-inline
  対照を直接生成しない可能性が高い。親の provisional 裁定であり、コードと artifact で攻撃する。
- DW-G05: consumer が無ければ値が headline 主張へ正しく束縛されず、prereg だけ作っても成果物は成立しない。

## 未完の作業と次の一手

- 別変更単位で下記の最小欠落を実装するかをユーザーが判断する。
- 欠落が landed した後に fresh `$dev-wave` で closure を再棚卸しし、成立時だけ prospective prereg を作る。

## 落とし穴・気づき

- worktree checkout 中に clean-tree 確認を走らせると一時的に全削除扱いが見える。checkout PID 終了後は clean。
- output/s8b-freeze、campaign WAL、external/ccbench へ直接書かない。Codex hook の開いた面は手動で守る。

## dev-wave 改善候補

- **なし。** 初回 plan の token-cap 全損は、DW-O02 が既に義務づける「必読裁定を job dir へ逐語で
  取り出して渡す」を親が初回 prompt で守らなかったためで、手順の欠落・曖昧ではない。
  既存 reference の重複強化や command 入口への追記は行わない。

## 段4裁定

### 結論

**既存機構だけでは T-1998 の正式測定 closure は成立しない。** 本 wave では prereg を作らず、
実装・build・launcher・campaign・正式測定へ進まない。実装面の差分ゼロなので段5/6と変異 matrixを省略する。

### exact pair の狭い確定

- 旧 headline の balanced contrast は `BACK_OFF=0` の no-backoff control と
  `BACK_OFF=1, BACKOFF_FIXED=5` の fixed-5us variant。`backoff_sweep.py:58,63-67,91-97` と
  `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md` の表・式が一致する。
- `patches/silo-backoff-fixed.patch` は `CCBENCH_BACKOFF_NOINLINE=0` を inert default とする。
  `backoff_sweep` の両 genome は同 knob を 1 にしないので stock-inline 側である。
- `BACKOFF_NOINLINE=1` の balanced profile と perf 下 tps は D20 により headline へ流用しない。

### 5 要素の実在裁定

| 要素 | 裁定 | 根拠・限界 |
|---|---|---|
| 専用 prereg | **不在** | canonical T-1998、D1137、既存 diagnostic artifact 以外に T-1998/stock-inline prereg は無い |
| same-source/env stock-inline build | **producer 部品は実在** | `backoff_sweep` に exact pair、`pipeline` に trace/perf 別 build と verifier-before-COMMIT がある。ただし pair 間 identity を headline consumer が検証する closure は無い |
| launcher | **不在** | sanctioned `backoff_sweep` compute launcher/registry entry は現行 repo に無い。landed job body は diagnostic `backoff_profile.py balanced` 専用 |
| result consumer | **不適格な既存物だけ** | `backoff_sweep_report.py` は certified view を読むが、結果後の static argmax、選択バイアス未補正、`linux-baremetal` 固定であり、T-1998 prereg-fixed pair consumer ではない |
| formal human authorization | **確認不能・推定禁止** | runtime `AuthorizedContract` は環境 admission として実在するが、人間の正式測定認可ではない。rulings 控えは T-1998 を含まず、自身を裁定証拠でないと明記する |

### real / refuted

- **real:** launcher 不在、prereg-bound consumer 不在、human authorization 未確認、既存 diagnostic 値流用不可。
- **real:** producer の COMMIT/certified view から pair consumer が必要とする source/env/build-mode evidence の
  到達性は追加監査が要る。足りなければ result schema の限定拡張が launcher/consumer より先の最小部品になる。
- **real:** T-1905 との非コード資源・将来予定 path の重複ゼロは未証明。将来 author 前に再検査する。
- **refuted:** exact pair 自体が未定という所見。既存 headline 正本と現行 genome/default knob から上記2点へ狭く確定できる。
- **refuted:** runtime authorization が全く無いという強い断定。コード上の環境 admission はあるが、人間認可の代用にはならない。
- **不採用:** D20/D1137 から専用 architecture を直接導くこと。必要なのは下記の最小 closure で、専用追加か既存拡張かは別変更単位で選ぶ。

### 欠ける最小部品とユーザー手番

1. **producer evidence 到達性の read-only 監査**: exact pair 間の source commit/token、env contract digest、
   trace-disabled performance build、diagnostic knob off、toolchain、別 verifier receipt を consumer が再検証できるか確認する。
   不足時だけ既存 result schema を限定拡張する。
2. **薄い sanctioned launcher**: 既存 `backoff_sweep` の non-screening official 経路を Pegasus 計算ノードで
   起動し、exact workload と測定 mode を固定する。新しい汎用 driver は作らない。
3. **prereg-fixed pair consumer**: post-result argmax を使わず、no-backoff と fixed-5us の exact pairだけを
   受理する。片側欠損・unstable・identity不一致は inconclusive/reject とし、診断 tps を拒否する。
4. **ユーザー手番**: 1〜3 が別 D95 author change unit で landed した後、prospective prereg と正式測定の
   認可を人間として確認する。本 wave はその認可を代行しない。

## 検査

- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0 (`check_docs: 違反なし`)
- `python3 tools/spool_fold.py --dry-run --show-diff`: rc=0 (`status=planned`)
- pytest / build / benchmark / formal measurement: 未実走。コード変更が無いため緑とは報告しない。
