---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t886-rollout-fastpath
seq: 1
title: rollout 探索を SHA pin 付き label だけ名前 glob へ短絡した — fixture 1 回分が 20.8s から 0.10s、認可外の再試行は段 6 で閉じた (コード + docs、変異 16/16 KILLED、branch worktree-dev-wave-t886-rollout-fastpath)
---

## 本文

- **ユーザー裁定 (2026-08-12 第 2 束) T-886 = (a) の実装。** SHA pin を持つ label に限り
  名前 glob の fast path、pin 無しの呼出元は全走査維持、fast path 後の SHA 照合は必須のまま。
  正本は `output/insights/2026-08-12_module-fixture-cost/verbatim/ruling-package.md` Q1。
- **起動時の重複検査 (ユーザー指示)。** 稼働中の受入ボトルネック wave が同 file を編集していたため、
  hunk 粒度で非重複を実測してから着手した (先方 `_filesystem_file_set` :1035-1050 対
  本項 `_find_rollout` :282 周辺)。先方は本 wave の段 6 中に land し、merge は競合ゼロで通った。
  **先方 handoff は「本 wave の land 後が安全」と所有を主張していたが、peer データとして記録し
  ユーザー裁定を優先した。結果として実害なし。**
- **親が撤回した主張が計 6 件ある。** 段 4 で 5 件、段 6 で 1 件。撤回の逐語は
  `output/insights/2026-08-12_t886-rollout-fastpath/verbatim/`。最も重いのは効果の機序で、
  裁定パッケージの「比例走査の除去」も、親が段 4 で置いた「metadata walk の係数削減」も
  **どちらも誤り**だった。narrow な `rglob` も同じ tree を最後まで歩くので walk 費用は不変で、
  消えているのは無関係 rollout の open / stream / parse である。残る比例項は walk (5.5 µs/file)。
- **受理集合の認可範囲を親が段 1 で狭く書き誤った。** 「拡大は重複だけ」と書いたが、fast path は
  非候補 file を開かないため**未捕捉例外も観測しなくなる**。段 3 の敵対レンズ 2 本が独立に反例を
  構成し、うち 1 本が「名前 glob を採る以上は回避不能」と論証した。先行 wave の Q3 で
  ユーザーが同方向を「認める」で確定済みであることを根拠に認可範囲内と裁定した。
  **ユーザーが不同意なら revert できるよう実装を単独 commit に保った。**
- **段 6 で未認可の拡大を 1 件閉じた。** 段 5 実装は fast attempt 全体を一様に捕捉しており、
  候補自身の内容照合例外まで飲んで読み直していた (= 一過性失敗の再試行)。
  例外の扱いを 3 区画へ分けて閉じた ({{D:fastpath-three-exception-regions}})。
- **敵対レビューが最も危険な穴を見つけた。** 既定経路だけ pin を外す条件付き配線の変異が、
  新規テストを全部通り抜けていた。配線テストが `verify=False` しか渡していなかったためで、
  **改善がゼロになるのに全部緑になる**状態だった。両値へ parameterize して閉じた。
- 変異は round 1 を probe として明示し (10 KILLED / 6 MISMATCH、**missing はゼロ**)、
  観測から完全集合を再導出した round 2 が本走で **16/16 KILLED**。probe の ledger も insight に残す。
- 変異登録で near miss を 1 件出した ({{F:mutation-placed-where-target-path-never-reaches}})。
- **scope 外の real 所見 2 件を裁定へ返す** (下記 新規)。いずれも本 wave では触っていない。

## 次の一手差分

### 完了

- [T-886] `_find_rollout` の全履歴走査を pin 付き label で短絡した。fixture 1 インスタンス分の
  5 呼出が 20.82s → 0.10s (実 corpus 2,973 file / 2.62GB、順序 counterbalance 2 走、
  返り path は 5 label とも全走査と一致)。変異 16/16 KILLED。
  remaining: none
  base: 51e091597ecc9e560ef0359ae9bcb61ce28f582966410277895ec34b3f009ad5

### 新規

- {{T:thread-id-rejects-parent-sessions}} **P1・新規**: `_find_rollout` の pin 無し経路が、
  subagent を産んだ親 session を `RC_SESSION` で拒否する。述語が `id` と `session_id` の
  いずれか一致なので、親 id で引くと親本体 + 全子 rollout がヒットするため。
  **実 corpus に該当 id が 2 件実在** (2 file / 4 file、いずれも subagent または fork)。
  receipt 検証経路では refusal reason に積まれるため、codex 子が subagent を産むと
  正当な作業を拒否しうる。T-886 の裁定が pin 無し経路の全走査維持を明示しているため未着手。
- {{T:scan-session-rows-full-corpus-parse}} **P2・新規**: `_scan_session_rows` が
  全 corpus の全行を parse する。現在はテストが実 corpus を渡していないため律速ではないが、
  渡した瞬間に `_find_rollout` の旧経路より重くなる。
- {{T:rollout-lookup-true-proportionality}} **P2・新規**: 比例項の真の除去
  (session-id 索引または直接解決可能な path 契約)。本 wave は係数を下げただけで
  walk の線形項は残る。敵対レンズが「現案を採るなら主張を係数削減に限定せよ」と指摘した。
