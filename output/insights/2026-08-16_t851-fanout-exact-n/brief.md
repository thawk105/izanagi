# 段 1 brief — [T-851] fan-out exact-N 本走の採用可否

wave `t851-fanout-exact-n` / branch `worktree-dev-wave-t851-fanout-exact-n` / base = local main と同一の `ab3feb0443a213dbbb3053dce8b07f40de70e759` (08:00 JST 時点、ff 済み)。

## scope

`tools/mutation_fanout.py run` を **既存 A/B 変異集合・N=2** で **1 回だけ本走**させ、fan-out を
今後の変異本走の既定にしてよいかを実測で決める。採る計測は cgroup `memory.current` の 3 反復、
Git admin burst、`df -Pi`、全 request 対応、fair-share、最終 `git worktree list`。
変異集合は増やさない。

**scope 外:** [T-852] (legacy `tools/mutation_worktree.py` が reservation を取らない件) は
段 4 で「既存逐次経路を変えない」と裁定済み。触らない。既存逐次経路の挙動も変えない。

## 段 1 で実測した事実 (brief 前提の裏取り)

1. **admission receipt の producer は repo に存在しない。** `validate_admission_receipt` は
   `producer_identity` / `sampler_identity` の両方が `_execution_identities()["driver"]` =
   **`tools/mutation_fanout.py` 自身の固定 HEAD blob 同一性**と一致することを要求する
   (`tools/mutation_fanout.py:282-338, 468-474`)。よって receipt を作れるのはこの tool 自身だけだが、
   CLI の subcommand は `run` / `cancel` / `_launch` の 3 つしかなく、**certify する経路が無い**
   (`tools/mutation_fanout.py:1808-1836`)。既存テストは receipt を捏造し
   `measurement_attestation` を stub で置換しているため、**実 kernel に対する admission 経路は
   一度も走ったことがない** (`orchestrator/tests/test_mutation_fanout.py:150-230`)。
2. **certification は「3 反復」を実 exact-N 実行として要求する。** measurement log は
   `outer_argv` (= N 本の `mutation_worktree.py ... --runner-mode dispatch --detached` 全 argv) と
   `child_returncodes` (長さ N、値は 0/1 の terminal のみ) を持ち、`outer_argv_sha256` で投入へ
   束縛される (`tools/mutation_fanout.py:452-460, 528-536`)。**同一 argv の反復 = 同一 group_root
   path の反復**であり、`run_fanout` の `root.mkdir(mode=0o700)` は create-only
   (`tools/mutation_fanout.py:1457`)。
3. **attestation は測定 scope が生存中であることを要求する。** `_attest_measurement_cgroup` は
   scope の `memory.peak == max(samples)`、`memory.max == user slice の memory.max`、
   `cgroup.events` が `populated 1` を同時に満たすことを要求する
   (`tools/mutation_fanout.py:401-419`)。
4. **bounded scope は login ノードで生きている (DW-G01 生死確認)。** 意図的に不正な receipt で
   `run` を起動したところ、`systemd-run --user --scope` 経由の再 exec に成功し、**scope の内側の
   process** が親 spec hash 不一致で rc=2 を返した。残渣なし。raw `systemd-run` は hook が拒否する
   (D211 / hooks/README.md) が、tool 内部からの生成は sanctioned 経路。
5. **投入枠は足りる。** user slice `memory.max` = 16 GiB、`admission_bytes` = 6.15 GiB、
   実効天井 14 GiB、固定予約 2 GiB → 見積もりに使える残りは **5.85 GiB** (08:05 JST 実測)。
   `memory.current` は 15.2 GiB だがうち 7.05 GiB は clean file cache で、判定は
   `admission_bytes` (回収不能分) で行われる (`orchestrator/campaign/login_headroom.py:240-262, 865-890`)。
6. **harness の flock は競合しない。** 鍵は repo 絶対 path の sha256 (`tools/mutation_harness.py:430-434`)。
   稼働中の t523 wave は自分の worktree path で握る。fan-out shard は各自の scratch checkout で走る。
   **真の競合は計算資源 (dispatch queue / fair-share) だけ。**
7. **凍結 pin なし。** `tools/mutation_fanout.py` の bytes を pin する manifest / trust root は
   py・docs 双方の全文検索で 0 件 (自己 hash する自テストのみ)。DW-O09 の閉包はここで閉じる。

## 不変条件

- 正しさゲートを緩めない。admission の受理集合を広げる変更 (attestation の緩和、`{0,1}` 以外の
  rc 受理、反復数の引き下げ、stub の production 混入) は**採らない**。
- 既存逐次経路 (`mutation_worktree.py` 単発、`mutation_harness.py`) の挙動を変えない。
- 本走中は自分以外の worktree へ書かない。計測前にノードの単独性を確認する
  (`docs/pegasus-runbook.md`)。
- 親は実装面を書かない。producer の実装は Codex `role=author` (D95)。

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- **(P1)** 本走を成立させるには `tools/mutation_fanout.py` に certify 経路を足すしかない。
  producer identity が同 tool の固定 HEAD blob へ束縛されている以上、別 tool・手書き receipt・
  repo 外 script はいずれも構造的に不可能である。
- **(P2)** certification の 3 反復は **exact-N の実 mutation 実行 3 回**を意味し、admitted 本走と
  合わせて計 4 セットの qsub を要する。反復の間に group_root を毎回全消しする必要がある。
  「もっと安い certify」は `outer_argv` 束縛がある限り作れない。
- **(P3)** 測定 scope 3 本は admitted 本走の validation 時点まで `populated 1` で生存していなければ
  ならないため、producer は各 scope に sleeper を残して本走終了まで保持する必要がある。
- **(P4)** 採用可否の判定は「4 セット分の資源と scope 保持の運用負荷に見合うか」で決める。
  本走が構造的に成立しないと判明した場合、それ自体が採用可否の答えであり、
  gate を緩めて成立させることはしない。

## 成果物の形

- `tools/mutation_fanout.py` の certify 経路 (Codex author) + その負例テスト。
- 本走の実測記録 (6 項目) と採用可否の裁定を worklog fragment / insight へ。
- 変異 matrix (新設する certify の gate を撃つ)。

## 成果物影響 (DW-G05)

certify 経路が無いままなら、fan-out は**永久に一度も本走できない**機構として repo に残り、
変異本走は逐次経路のみ = 台帳の試行 wall-clock が N 倍のまま。採用可否を決めた結果は、
以後の変異台帳がどの経路で作られるか (proof chain の材料の出所) を決める。

## 並列分割方針

段 2 plan 1 本 → 段 3 敵対 2 本 (レンズ A: certify 設計の正しさ防壁、レンズ B: 資源・運用と
本走の実行可能性) → 段 4 裁定 → 段 5 author 1 本 (certify + テスト) → 段 6 review 2 本 + 本走。
