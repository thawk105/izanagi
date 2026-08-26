---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1901-env-coincidence-reaudit
seq: 1
title: 環境の偶然を assert する検査 250 行を全数分類し、走査述語を commit 済みコードにする (コード + docs、branch worktree-dev-wave-t1901-env-coincidence-reaudit)
---

## 本文

`5d0c898c4` 時点の候補 250 行 / 66 file を全数分類した。内訳は H 206、D 16、C 14、T 14、
F 0、判定不能 0。前 wave の暫定 class があった 155 行のうち 17 行 (11.0%) を覆し、
暫定 H 153 行のうち 16 行 (10.5%) が非 H へ動いた。

**前 wave の抽出監査 (5 件中 3 件 = 60% が非 H) からの外挿は誤差が大きかった。**
系統的な偏りは実在するが、全数では 10.5% である。5 件の標本から族全体の誤分類率を
外挿してはならない。

**F は 0 件だった。** 候補は 10 行あったが、いずれも F の class 定義にある
「上限との余裕がその床で決まっている」を満たさない。床と上限の比は最小でも 100 倍で、
D1055 が根拠にした実例 (比 1.0015、余裕 15 ミリ秒) とは桁が違う。
「見つからなかった」ではなく「調べた上で不在」である。詳細は {{D:f-materiality}}。

**前 wave が「確認できた誤分類」として記録した 4 件のうち 2 件は、訂正自体が誤りだった。**
`test_check_ai_provenance.py:6359` と `test_run_tests_preflight.py:2049` は T ではなく H である。
`wait(1)` は mock の `side_effect` 内の test-local `Event` で、`1` は production へ到達しない。
前 wave の敵対レビューは H 偏りを直そうとして逆方向へ振れていた。詳細は {{F:overcorrected-h-bias}}。

段 3 の敵対相談が停止条件級の所見を 3 件出し、裁定前に是正した。

1. **wave 中に local main が 40 commit 進んでいた。** 段 3 の子が独立に検出した。
   ff-only で `5d0c898c4` へ揃え、全派生資料を再生成した。移動 anchor は 8 件。
2. **段 2 プランの行番号規則が誤りだった。** 親が非循環に検証し、v1 の base `b0c1a8bd` で
   `ast.Call.lineno` 規則は 260/260 を完全再現、引数値 `lineno` 規則は 163/260 と実測した。
3. **親の control の抽出が説明より狭かった。** keyword 形 `wait(timeout=N)` と比較形 `== 0` が
   漏れており、修正版は 38 行を拾う (旧 24 行)。

親は当初 control 1 を「戻り値が消費される行は H の定義上ありえない」という hard reject として
使う予定だったが、段 3 が現物で反証した。上限が failure recovery だけを bound する fail-fast
guard で、性質が別の assertion にあることは実在する。**要反証の合図へ降格し、代わりに
H と書く行へ「性質を担う別 assertion の file:line を名指しする」義務を課した。**
立証責任を下げるのでなく上げる方向で解決した。

段 6 の実装レビューが gate の穴を 2 件検出し、fix で塞いだ。どちらも放置すると母集合が
変わる (250 行 → 231 行、250 行 → 248 行)。変異 `MUT-T1901-P2-EXCLUDES-JOIN` は
是正前に全 12 node を通過していた。

分類の検出力は 2 段で測った。H と判定した 28 行に同数の非 H 行を decoy として混ぜ、
class を隠して別の子へ再分類させたところ **H 主張の 26/28 (93%) が独立に再現**した。
非 H 側は 18/28 (64%) で、こちらの方が不安定だった。食い違った 18 行は決着子が現物で決めた。

工数は codex 子 21 本 (plan 1、consult 2、分類 14、review 5、author 2、fix 1)。
author の 1 本目は成果物に `## 総括` の見出しが無く F43 で弾かれたが、
**親の prompt に見出し要求が欠けていたのが原因**で、子は 2 file を書き終えていた。
2 本目は仕様違反なしで file を書き換えなかった。

変異本走は 3 回目で成功した。1 回目は親が変異走行中に成果物を worktree へ書き
(DW-M05 違反)、2 回目は前回の `--attempt-out` を消していなかった。どちらも harness が
fail-closed で正しく止めた。詳細は {{F:parent-dirtied-tree-during-mutation}}。

## 次の一手差分

### 完了

- [T-1901] 候補 250 行を全数分類し、走査述語を `tools/scan_env_coincidence.py` として
  commit 済みコードにした。F は不在、判定不能 0。台帳を再アンカーした。
  remaining: none
  base: c1d830d1d13ba9f35400d5caa11fba9d8f21cb9dc6adff33b18b5b109a767b2b

### 更新

- [T-1902] **P2・更新**: 稼働 wave 所有で次 wave 送りにした行のうち、land 済み 4 wave 分は
  [T-1901] が吸収した。**残るのは `dev-wave-t1629-ratification-broker` と
  `dev-wave-b10-overthrottle-grid` が所有する 5 行だけ**である。分類 JSON では
  `observation_only` を立てている。所有 wave の land 後に走査器を当て直して再分類する。
  base: d17620bbd804c1373283019af567a22d91e65f0ef6c00421c31acc5d86c73fad

- [T-1904] **P2・ユーザー裁定待ち・更新**: 静的 gate を置くかの裁定は未決のまま。ただし
  [T-1901] が走査述語を commit 済みコードにしたので、**「登録 gate にしかならない」という
  却下理由のうち再現性の部分は解消した**。走査器は gate ではなく producer であり、
  repo 実データの件数を pin する test は置いていない。裁定の前提が変わった点を添えて再提示する。
  base: 38a4b7fbe2fa9feb3b42617624580ba8b0b1d7b4c741825e75064bf261c28bce

### 新規

- {{T:env-coincidence-self-deadline-family}} **P2・新規**: 述語の 6 つ目の盲点
  (`deadline = time.monotonic() + N` に続く poll ループ、`5d0c898c4` 時点で 29 site) を
  走査対象に加えるかを決める。加えるなら走査器へ述語を足し、母集合を再定義する。
  加えないなら「述語の限界」に留める理由を書く。現状は台帳へ限界として記録しただけである。

- {{T:wave-midflight-main-recheck}} **P2・新規・ユーザー裁定待ち**: wave 中に local main が
  進む量は無視できない。本 wave では段 2〜3 の約 40 分で 40 commit 進み、8 anchor が移動した。
  気づいたのは段 3 の子であって親ではない。入口は着手前と受入直前に main を見るよう定めるが、
  **段 5 の実装子 dispatch 直前に main を見る機械的な発火点が無い。** 段構成に関わる変更なので
  実装せず裁定へ返す。案は (a) 段 5 preflight の条件 dispatch へ「main 乖離の再測」を足す、
  (b) `check_wave_startup.py` に `--mode midflight` を足して段 5 直前に走らせる、
  (c) 現状どおり親の規律に委ねる。

- {{T:f-materiality-constant}} **P2・新規**: F の materiality 判定に要る定数 `R`
  (または許容 jitter `J`) を裁定する。[T-1901] は candidate と床/上限の比までを機械で出せる
  ことを示したが、境界値は D1055 の実例 1 件では決められない。実例をもう数件集めるか、
  裁定で定数を置くかを決める。
