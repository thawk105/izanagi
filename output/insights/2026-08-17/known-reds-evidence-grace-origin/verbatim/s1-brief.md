# 段 1 brief — 既知赤 (受入全走でだけ落ちる非決定テスト) を決定的にする

ユーザー依頼: 「既知赤のテストがあれば、適切に直してください。テストが間違っていればテストを直す。
テストされているものが間違っていればそれを治す。リワードハック禁止」

## 実測した現在地 (2026-08-17 09:04 JST、tip = local main、worktree-dev-wave-known-reds)

- 全走 (Pegasus request 915134.nqsv、113.95s) = **12271 passed / 95 skipped / 0 failed**。
  決定的な赤はゼロ。`tools/check_docs.py` rc=0 (違反なし)、`tools/check_ai_provenance.py` rc=0
  (3853 件、新規違反なし、known-violations=42)。
- 95 skipped はすべて (a) 環境条件 skipif か (b) D335 恒久保留 (`IZANAGI_GROWTH_HOLD_V1`)。
  恒久保留の解除 token は `explicit-user-command` であり本 wave では立てない (解除はユーザー明示命令のみ)。
- `pytest.ini` の `testpaths = orchestrator/tests` = test file 212 本すべてが全走の収集対象。
  全走の外に取り残された test 群は無い。
- したがって **既知赤の実体は「受入全走でだけ落ちる非決定テスト」2 族**であり、
  いずれもユーザー裁定済みで「同一 wave にまとめよ」と明示されている。

## scope

- **S1 = [T-1005]** (P2・裁定済み 2026-08-16 /rulings 全件「切り離しを先に」):
  `orchestrator/tests/test_codex_worker_launch.py` の非決定的な赤。まず共有状態依存を
  **fixture 側で断つ**ことを試み、**不可と判明した場合に限り**受入での直列化へ倒す。
  直列化は受入時間を伸ばすので最後の手段。
- **S2 = [T-1164]** (P3・裁定済み 2026-08-16 /rulings 全件「実測して直す」):
  signal 転送テストが受入全走でだけ赤。**負荷依存かを実測し、タイミング依存を除く。**
  対象 node (台帳既載):
  `test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler`,
  `test_dev_wave_wait.py::test_public_main_real_signal_releases_lease`,
  `test_dev_wave_wait.py::test_public_main_failure_restores_handler_without_release`,
  `test_mutation_worktree.py::test_sigint_and_sigterm_are_forwarded_between_observation_points[SIGINT]`。
- scope 外: 恒久保留 (D335) の解除、既知赤 registry ([T-1116]、trust root 不在で NO-GO 済み)、
  受入の直列化 (S1 で「不可」が実証された場合だけ段 4 で再裁定)。

## 親の provisional 裁定 (= 攻撃対象。子はここを疑ってよい)

- **(P1)** S1 の残存機序は `test_codex_worker_launch.py:1553` の `max_wall: str = "3"`
  (fake normal control の既定 wall 予算 3 秒) である。F57 本文の「fake normal control の既定 wall
  上限は 3 秒」と、再発が一貫して `launcher returncode 1 / stderr 空` (`assert 1 == 0`) である
  ことに整合する。**裁定文が名指しした `~/.codex/sessions` 依存は既に切れている** —
  同 file:1642 が `CODEX_HOME` を tmp へ差し替え、1290 がその env を読む。
  親は `~/.codex/sessions` を実測で除外したが、docs authority snapshot と receipt の 2 経路は未検証。
- **(P2)** S2 の production 側真因は commit `2da49c56` (2026-08-16 22:17、裁定より後) の
  「worker signal mask 汚染を閉じ、mask 復元を非同期例外に耐えさせる」で既に閉じており、
  `test_dev_wave_wait.py` 側の 3 node は前提解消済みの可能性が高い。
  ただし `2da49c56` は `tools/dev_wave_wait.py` と `test_dev_wave_wait.py` の 2 file しか触っておらず、
  **`test_mutation_worktree.py` は射程外**なので S2 の実体はこの 1 node に縮む可能性がある。
- **(P3)** `test_mutation_worktree.py:825` の race は `ready` file の出現を待つが、
  **`ready` の出現が子の signal handler 設置完了を含意しない**ことにある (観測点間の順序未固定)。

## 不変条件 (違反は即停止。リワードハック禁止の実行形)

1. **既存テストの期待値を変更しない。** 反転・緩和・skip・xfail・削除・`pytest.mark.flaky` 等の
   再試行導入をすべて禁じる。赤なら実装側が誤りとする。期待値が誤りと判断したら実装を変えず報告して止める。
2. **production の gate を緩めない。** `--max-wall-clock-s` の production 既定値、
   signal 転送の production 実装、受理集合を変えない。変えたい根拠が出たら段 4 へ返す。
3. wall 予算を上げてよいのは **成功を期待する control case だけ**。
   gate が発火することを主張する case (例: 2570 / 2627 の `expected_returncode=99`) の予算は不変。
   予算を上げる case ごとに「この case で予算は被検査性質ではない」根拠を file:line で示す。
4. 決定性は**待ち合わせの追加**で得る。`time.sleep` の延長、retry、timeout の一律引き上げで
   隠さない。負荷が上がれば再発する対策は不採用。

## 成果物影響 (DW-G05)

放置した場合: 受入全走は赤があると受領証を出さないため、この族が出るたびに緑 1 回分の lease 窓を
捨てる (台帳実測: entry 572 は 2 走を消費)。結果として worklog / decisions / failures の 3 台帳への
記録が律速される。さらに毎回 `DW-O18` の非帰属判定を人手で行うため、**真の回帰を「どうせフレーク」と
誤って非帰属化する経路**が常設され、受理集合が実効的に緩む (規律 2 の面)。

## 成果物の形

`orchestrator/tests/` 配下のテスト・fixture の編集のみ。production コードの変更は S2 で
`2da49c56` の穴が残っていた場合に限り、段 4 の再裁定を経て許す。

## 並列分割方針

S1 (`test_codex_worker_launch.py`) と S2 (`test_dev_wave_wait.py` + `test_mutation_worktree.py`) は
編集ファイル所有が素集合なので段 5 で 2 単位に分けて並列投入できる。
