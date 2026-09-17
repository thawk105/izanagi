---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-land-turn-ticket
seq: 1
title: main land の進行保証を道具に入れた — 受入 lease と別の順番票、lock-busy で監査・fold gate の証拠を捨てない二層予算、control-plane 観測の非接触、cleanup の対象限定撤去 (コード + テスト + docs、branch worktree-dev-wave-land-turn-ticket、変異 matrix = baseline PASSED・負例 19/19 KILLED 期待 node 完全一致・等価 M0 と冗長 gate 対照 M7b SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「main land の進行保証を道具に入れる。着手直前の local main から fresh worktree を作り、新規 T は
  worklog fragment の placeholder (slug land-turn-ticket) で採番する。実装 3 点: (1) 受入 lease とは別の land 順番票、(2) 証拠保持、
  (3) cleanup 非接触。テストは既存の fake clock + 実 flock fixture を拡張し決定的スケジュールで示す。改訂する決定は
  D432/D1996、D109/D702。D254・D662・D1393 は変えない。実装面は Codex author (D95)、規律 2 は緩めない。OCC 再検証・
  lease 再設計・汎用 read-set 解析・仮想リスク向け gate や台帳の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/land-turn-ticket/README.md`。設計判断は {{D:land-turn-ticket}}、
  失敗の型は {{F:land-storm-lock-busy}}。実装 commit `ec6af3d0f` (Codex author、4 file)。
- **旧 tree の負例を決定的 schedule で再現した。** base abc7085ae の container に新 harness だけを重ね、policy `storm-e`
  (13 本、20 秒間隔到着、in-lock 240 秒、監査 430 秒、gate 130 秒、rc=11 は 120 秒後に再投入、fake 76 分) で着地 0・main
  不変・監査 18 回・終端 151 回 (全 rc=11、最終 initial 12 / post-provenance 1)。in-lock 30〜200 秒の policy では旧 tree でも
  1 本着地するので、嵐の本体は「lock 内作業 > 180 秒の累積予算 + 到着率 > 処理率」であり、D1996 が直した混同とは別の穴。
- **新 tree の同 policy は着地 1・監査 1。** ただし独立 branch の stale-main request が保持 seq で先頭を交互に占め、後続 10 本が
  3600 秒の順番期限で lock-busy になる飢餓を親の probe が出し、段 6 で「grant を消費して終端した request は seq を保ちつつ
  order を待ち手の後ろへ回す」補正を裁定した (D の rc 別処理表)。
- **親の裁定誤り 2 件を段 6 で訂正した。** (a) 非ゼロ provenance の即終端を「非 retryable」と書いたが既存 verifier は
  violation rc だけ非 retryable (infra / signal / timeout は retryable) で、既存 test 2 本の期待が正。(b) fix 子への「報告して
  止める」を全体停止と読ませて 1 巡を空費した (fix-2 未編集)。
- **実機依存を親の probe が 2 件出した。** Lustre (`/work`, `/home`) は `renameat2(RENAME_NOREPLACE)` が EINVAL で、fix 子の
  journal 公開が本番で常に停止する形だった → `os.link` + unlink (実 `.git` dir で EEXIST / nlink 2→1 を確認) へ。poll ごとの
  registry 保存 (fsync 37 ms) は runner 外で 8 本の正例 node を 270 秒にしていた → 変更時だけ保存。
- 段 3・段 6 の所見と裁定は insight の `verbatim/`。段 6 レビュー 4 本 (U1 A/B、U2 A/B) + 焦点再レビュー 1 本の must-fix
  は全部閉じた (U1: R1〜R4・N1・B1〜B5、h′ の runner digest 静的化; U2: A1 基準 snapshot、B1 journal 原子公開、link 後停止の再入)。
- 実走: land 単独 360 passed / 1 skipped / 19.3 秒 (login)、cleanup 単独 143 passed / 8.0 秒 (login)、consumer 18 file 2130 passed /
  4 skipped / 123 秒 (計算ノード)。受入全走は docs commit 後の最終 tip に land 前に 1 回 (結果は land の受領証)。
- **変異 matrix (container worktree、`run_tests.py` 2 file、probe と本走で各 22 run = baseline + 21 変異、計算ノード dispatch)。**
  probe 走 (4,088 秒) で観測 node を集めてから本走 (1,711 秒)。本走は baseline PASSED (698 秒)、負例 19 件 (M1〜M6、M7a、M8〜M14)
  すべて KILLED で期待 node と観測 node が完全一致 (matching 21/21)、等価変異 M0 (comment) と冗長 gate 対照 M7b は SURVIVED、
  MISMATCH 0、TIMEOUT 0、全 anchor 1 箇所。M7a (provenance 後の fingerprint 比較) は SURVIVED 対照の予測に反して既存 test 5 本が
  殺したので生きた gate として KILLED 期待へ再登録した。専属 killer: M3 TTL 判定 → `live_owner_is_not_expired`、M4b/M4c1/M4c2/M9
  → `mutation_rechecks_owner[...]`、M12 引渡しの非原子化 → `red_head_hands_over_atomically`、M13 → `red_provenance_fails_fast`、
  M14 order 非回転 → `stale_head_rotates_behind_waiters`。
- scope 外で残る (裁定パッケージ候補、insight に列挙): 元 request 不在の fold 途中 state を他 wave が自動復旧する主体、
  生存 hang の先頭を止める監督主体、fold 子 process の lock fd 非継承、lease を land 待機全体へ広げる契約、新 receipt でも
  順位を引き継ぐ契約、共有 admin 一覧の完全非接触化。
- 段 8 (自己改善): 候補 2 件を契約で裁定。(a) 編集面重複検査を sha256 比較 (他 worktree で git を走らせない) にする手順は、
  L1 (+135 bytes で 10,625 超) と DW-O20 (+120 bytes で単節 1,000 超) の予算に入らず、D782 の手順 (安全義務の削減は不可、
  独立例は本 wave と t2647 の 2 で 3 未満、上限引き上げは不要) で収容せず記録のみ。(b) fix prompt の「報告して止める」が
  全体停止と読まれた件は 1 件のみで F 化しない。
- 工数: codex 子 20 本 (plan 1、consult 2、author 2、review 5 (焦点再レビュー 1 込み)、fix 10 (U1 7・U2 3)、全段 `gpt-6-astra` / `medium`)。
  親の実測: 焦点走 12 (login 10・計算ノード 2)、probe (旧 tree 2 走・新 tree 6 走・Lustre 2 件・fsync 1 件)、変異 2 走 (計算ノード
  44 run)、provenance full 1 本、受入は land 前に 1 回。

## 次の一手差分

### 新規

- {{T:land-turn-ticket}} **P2・裁定パッケージ**: land 順番票の残余 6 件 (他 wave による fold 途中 state の自動復旧主体、生存 hang
  の先頭を止める監督主体、fold 子 process の lock fd 非継承、lease を land 待機全体へ広げる契約、新 receipt でも順位を引き継ぐ
  契約、共有 admin 一覧の完全非接触化) を {{D:land-turn-ticket}} の前提の外として裁定へ返す。混在期 (順番票を知らない旧
  driver) の観測: `lock-busy` の reason に `waiting for land turn` が無いものが本件の型。
