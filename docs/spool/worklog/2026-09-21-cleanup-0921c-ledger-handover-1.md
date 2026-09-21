---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: cleanup-0921c-ledger-handover
seq: 1
title: /cleanup-branches (2026-09-21 13:34〜13:47 JST) の引き渡しを起票した — 未記帳 7 object の記帳と掃除手順の改善候補 3 件の routing を AI 手番の T にした (docs のみ、実装面 0 行、branch worktree-cleanup-0921c-ledger-handover)
---

## 本文

- `/cleanup-branches` を 1 回実行した (13:34〜13:47 JST)。branch 6 本を削除 (`-d` 2 本 = `tmp-check`・T-2344 の wave branch、
  `-D` 4 本 = `author-login-check-probe` 系 3 本・`dev-wave-t2812-probe-author`) し、T-2344 の worktree 1 本を F26 の手順で撤去した
  (amend 前の版が reflog に残り、段 9 の自己撤去が rc=20 で拒否されて残っていたもの)。巻き添え 0。証跡は repo 外の
  `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260921c-rescue/` (bundle・rescue gate の JSON 2 本・削除直前の再確認と撤去の log)。
- 掃除の final は救出 triage と台帳転記を「ユーザーへお任せ」と書いた。ユーザーの是正 (逐語):
  「私はpushしかやらない。だからあなたが仕訳や転記をお願いしたいならdev-wavetタスクとして登録しておくべきだね」。
  cleanup 実行中は command §0 で fragment を書けないため、final の後に本 branch を切って起票した。
  ユーザー手番は push だけであり、AI 側の後続作業は T として起票する。
- 前回の掃除 (同日 07:49 JST の b 回) の `-D` で生じた未記帳 3 object も起票されないまま残っていた
  (c 回の `--ledger-check` が `unledgered_commits` 3 件として通知)。同じ引き渡し漏れなので同じ T にまとめた。
- 掃除の final で「判断が必要」と書いた改善候補 (worktree の撤去経路) も、ユーザーへの問いではなく routing の T にした。
- 工数: codex 子 0。受入全走は本 fragment を含む tip で 1 回投入する (land の着地が緑の証拠)。

## 次の一手差分

### 新規

- {{T:cleanup-0921bc-unledgered-objects}} **P3・新規 → 記帳の実行手番 (AI)**: 同日 2 回の `/cleanup-branches` の `-D` と撤去で
  到達不能になった未記帳 7 object を、`docs/unreachable-object-ledger.md` の「追記と状態遷移」どおり `pending` で追記する
  (台帳の schema と rescue gate は変えない。[T-2829] の 248 件とは別集合)。
  b 回 (07:49 JST) の 3 件 = `f1a1e8eb003cee1d02db90f56f485a28832f78e1` `a028857a6fafe3f8a4e8c366d2493b175ffc4603`
  `ed461aa4fd55547b6398c3c2df2cf8d6b7c2bdf9` (author-t2817-probe 系の tip。
  `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260921b-rescue/deleted-branches.bundle`、sha256
  `1c9ef7f83bc11360a9848471ccbf95a16c1cee63ff138b0b13461f4e322dc68c`、16 heads に退避済み)。
  c 回 (13:45 JST) の 4 件 = `c626b527d2791f49b9af8cf86ce56055794f67d2` `df916199dbf5c1f8b07ed9ecf5963d4c920f3e3e`
  `c84ab8c711e4abea6c1c1fff565da0a4cf89fdda` (author-login-check-probe 系。
  `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260921c-rescue/deleted-branches.bundle`、sha256
  `57d6c97f656a4bcf75c96b1380ee078cc7ffc8986d6f0a02504ac11919fc3636`、`git bundle verify` rc 0) と
  `b3de31e09ed06321d881fdb704878be99198dded` (T-2344 の amend 前の reflog 専用版。bundle に入れられない。後継 `ae0764eae` が main に在り、
  38 file 中 33 が同一・2 件は fold 済み fragment・3 件は着地版が後の修正を含む差と file 単位で照合済み)。
  着手時に `python3 tools/audit_dangling_commits.py --offrepo-scan full --offrepo-root /work/1/SFC/tanab/dev-wave-jobs` を単独実行して
  repo 外の同一実体を確かめ (救出 triage)、`resolution_note` の材料にする。`--ledger-check` を候補なしで取り直し、未記帳が 0 に
  なったことを確かめて閉じる。解決 (`accepted-loss` / `rescued`) は [T-2829] と同じく /rulings へ返す。
  喪失の下界: c 回の loose 3 件は 2026-10-05 以降、packed の `c626b527d` は判定時点 (conservative floor)。材料は c 回 dir の
  `rescue-gate.json` / `rescue-gate-2.json` (いずれも rc 2 = 他 wave の自己撤去による root 移動と着地判定 indeterminate)。
- {{T:cleanup-0921c-self-improvement-routing}} **P4・新規 → routing 手番 (AI、dev-wave)**: 2026-09-21 c 回の
  `/cleanup-branches` final が挙げた改善候補 3 件を `docs/skill-self-improvement.md` の routing で振り分ける。
  (1) 持ち主の wave が完了し clean・非施錠・退避可能な Codex author 木でも、HEAD が main に無いと §2 に撤去経路が無い
  (実測 2 本: `author-lease-gate-wait-probe` = entry 1789、`.codex/worktrees/t2812-probe-author` = entry 1790。
  branch の `-D` と同じ条件で木を畳む経路を足すかの判断を含む。近接 = [T-2828])。
  (2) rescue gate の rc 2 に再走の打ち切り目安が無い (稼働 wave の自己撤去で `root-snapshot-moved` が再発し、probe 専用
  commit の `one-or-more-states-unproven` は子予算 40 秒でも残る。近接 = [T-2749])。
  (3) wave が作る一時 ref (`git fetch . main:refs/heads/tmp-check`) が所有不明 branch として残る
  (今回は会話記録の grep で持ち主を特定した)。`.claude/commands/cleanup-branches.md` は whole-file sha256 で pin されているので、
  command 本文を変える場合は `tools/check_docs.py` の pin 同期 (Codex author) と byte 予算を先に確かめる。
