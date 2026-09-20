# [T-2807] B-8 事前登録 v1 の発効 (D2194 項 1) と、校正 → 本走 → 3 値判定の記録

- wave: `worktree-dev-wave-t2807-b8-effective` (背景 job、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-effective/`)
- 起点 local main: `5efd69367` (開始 gate rc=0) → 段 3 前に `21641fee7` へ ff-only (差分は dev-wave 手順書・worklog の docs と fold だけ。事前登録・patch・verifier・pin は不変)
- 依頼: D2194 項 1 (第 27 回 /rulings、ユーザー「推奨通り」2026-09-21 00:5x JST) — 事前登録 v1 を案 A の発効束で発効し、校正 3 job → 規則が決める extime で本走 6 job → 3 値判定 → results 稿と論文ストーリーへ
- 前段: 発効前試走と発効束 draft は `output/insights/2026-09-20/t2807-b8-prerun/README.md` (§7.1 = 発効束の全項目の表)
- 実装面 (repo 内) の差分 0。runner v5 は repo へ入れない (D95、前 wave の job dir に保全、sha256 で同定)

---

## 1. 発効の記録

**事前登録 v1 (`docs/b8-final-candidate-longrun-verify-preregistration.md`、raw sha256
`6ccb18c73b80ba42031f1373d48baa2e3fe441e0370a208836a6d75a9504f7c5`、51,974 bytes) は、本 README と
`verbatim/b8-effective-bundle.json` を追加した commit (以下「発効 commit」) で発効した。** 発効 commit の hash は
自己参照を避けて本 README 初版には書かず、後続の記録 commit で本節末尾に追記する (事前登録 §0)。

| 項目 | 値 |
|---|---|
| 決定 | D2194 項 1 (択 (a) 承認)。関連 = D2186 項 1 (段階認可)、D2190 (runner v5 と発効束 draft) |
| 承認の日付 | 2026-09-21 (ユーザー発話「推奨通り」00:5x JST、第 27 回 /rulings の索引 14 項への一括回答) |
| 承認の対象 | 承認時に提示された snapshot = main `285477c0052819e272e390d798f6442658075866` 内の試走 insight §7.1・発効束 draft・事前登録 v1 と、それらの実値 |
| 承認を記録した commit | rulings commit `3016f22eec17ac839fd4db0a0798f7e441f99bff` (2026-09-21 01:03:47 JST、裁定の記録)。D 番号 D2194 を振った fold = `2afb3976822dc0e3d8591c139f6ab607278b9276` |
| 対象の択 | 案 A (S-1 最終候補の系側 gate 構成。g_rl = balanced / read-heavy、g_rt = write-heavy、24 verify) |
| 発効束 JSON (runner の `--bundle`) | `verbatim/b8-effective-bundle.json`。draft (`output/insights/2026-09-20/t2807-b8-prerun/verbatim/b8-effective-bundle.draft.json`、sha256 `6063d5d8b45c0bcd405296f9f99ca2989f894a7054bf91ef0248e45f4a5d7ae6`) の実験構成の値を不変で写し、`status` だけを `effective` に置換し、`effective` 節 (決定・日付・承認の対象と記録 commit・draft の出所・校正 walltime・verifier hard timeout) を足した。sha256 `059536a7359406182c622172354207e147ad2811ba0b4d9286982778b3807c1b` |
| 発効束の他の項目 (JSON 外) | 前 wave insight §7.1 の表のとおり — 環境 (Pegasus gen_S、1 job 1 node、単独性検査は runner が bench・verifier 直前)、configure argv 全文 (試走 record `bindings.configure_argv`)、校正 walltime 03:30:00 の根拠 (上限式 ≈ 10,347 s ≤ 12,600 s、D2160 校正最大 Elapse 4063 S × 3 = 12,189 s。上限式は setup+hydrate+build の事後検査 2400 s を含む見積式で、厳密な上限保証ではない)、既知結果台帳の差分 (試走 6 record)。値は変えていない。**保全先と空き容量は本 wave の現在値を §3 に書く** (前 wave の「81 TB」は転記しない) |
| runner | v5 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430` (2103 行)、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py` (repo 外) |

### 1.1 発効直前の検算 (親、login、HEAD `21641fee7`)

`probe/check_bundle_at_head.py` (job dir、読むだけ) で、draft の値と HEAD の実体を照合した。全 15 項目一致 (NG 0):
submodule gitlink = pin `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`pin.CURRENT_PIN` = `e9e477c`、patch sha256 `31316713…`、
事前登録 sha256 `6ccb18c7…`、verifier module 9 file の sha256 (余分な `*.py` 無し)、`pipeline.py` sha256 `472cc7a2…`。
発効版 JSON (sha256 `059536a7…807c1b`) は runner v5 の `load_bundle` に受理され、同 JSON に対しても同じ 15 項目が一致した。runner の `validate_bundle` は `status` と承認情報を検査しないので、校正・本走の launcher は固定 checkout 内のこの tracked path を `--bundle` に固定し、`summarize` には `--accept-ruling-sha` と `--accept-bundle-sha` を各 1 値で渡す (段 3 相談の注意、新しい gate は足さない)。

## 2. 論文ストーリー §8 B-8 の仕分け (2) の限定 (D2186 項 1 (2))

D2186 項 1 (2) は、事前登録 §3.2 の定義 (「種を変えた N 反復」= N 個の独立な bench process をそれぞれ新しい OS process
として起動し、各 process の各 worker thread が `std::random_device` から自己シードすること。seed 値は記録しない) を
B-8 の「種を変えた」の要件として認め、論文ストーリー §8 の仕分け (2) 「数値 seed・乱数列の独立性は記録できない」とは
不一致なので、発効時に仕分けを「独立 process の自己シード」へ改める限定を明記すると定めた。

**発効後の B-8 の仕分け (2):「種を変えた」は独立 process の自己シードで満たす。** 各 verify が記録するのは rep-id・bench の
PID・開始時刻 (wall clock と monotonic)・argv 全文・node 名・binary の sha256・source identity・trace の byte 数 / 行数 /
commit witness であり、seed 値は記録しない (CCBench に seed の flag は無く、seed 注入は要件にしない — 候補の identity が
変わり、検証対象が headline の候補でなくなる)。**限定:** 独立性は操作的仮定で、`std::random_device` の実装は測っていない。
同じ 32 bit 値の再出現は検査できない。「異なる乱数列であることを検証した」とは書かない (事前登録 §3.4)。

- 論文ストーリーの日付版は凍結物 (「書いた後は更新しない」) なので、2026-09-21 版以前の §8 の文は書き換えない。
  限定は腐らない入口 `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」へ積み、次に作られる版が
  本文へ取り込む。
- この限定は D2160 の検証相 (採用候補 2 genome、extime 3 s) の仕分けを変えない。検証相は対象 (1) と長さ (3) が要件と
  違うので、仕分け (2) が改まっても B-8 には数えない。
- **発効は、校正・本走・判定が済んだことを意味しない。**

## 3. 校正 (段 A)

(校正の投入後に追記する)

## 4. 本走 (段 B)

(校正の summarize が `stage_B_allowed` を返した場合に追記する)

## 5. 3 値判定

(未)

## 6. 限定

(判定後に書く)
