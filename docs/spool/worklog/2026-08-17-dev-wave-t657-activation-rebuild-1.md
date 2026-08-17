---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t657-activation-rebuild
seq: 1
title: [T-657] 活性化の立て直しは所有の衝突で実装せず、旧 branch を保全して破棄した (docs のみ、branch worktree-dev-wave-t657-activation-rebuild)
---

## 本文

ユーザー指示は「未着地 11 commit の `worktree-dev-wave-t657-t660-g2-activation` を破棄し、
現行 main の `reseal_protocol()` で立て直す」だった。**破棄は実施し、立て直しは実装しない。**

**実装しない根拠は技術的不能ではなく所有の衝突である。** 立て直しの実体 (versioned 床値
protocol の実発行と live consumer の配線) は、別 wave `dev-wave-t1255-floor-freeze` が
同日同時刻に稼働して所有していた。実測 2 点 — 09:22 に locked worktree と段 3 敵対子 2 本の
走行を `pgrep` で確認、12:26 に同 worktree が前進 (`9dcae82f`) しなお稼働中。allocation 上も
配線 = [T-419] (3) / [T-1214]、実発行 = [T-1255] である。先取りすると固定 legacy path と
versioned resolver の二重 authority が生じ、resolver が count=0 / count=2 で fail-closed する。

**親の主張 3 件が段 3 の敵対検証で覆った。** いずれも親が対ユーザー説明または brief で
断定していたものであり、棄却 finding として記録する。

1. 「create-only なので取り消せない」は誤り。`os.link()` は同一 path 上書きを防ぐだけで unlink は
   禁じていない。commit 前なら削除して出し直せる。親は本 wave の不変条件をこの誤解の上に置いていた。
2. 「追加のみだから履歴不変条件と衝突しない」は言い過ぎ。versioned artifact は `FROZEN_MANIFEST` の
   対象外で、履歴不変検査が効くのは ratified closure に入ったときだけ。正確には
   「衝突しない」ではなく「まだ検査対象ですらない」。
3. 「2026-08-09 裁定パッケージの A/B/C 3 択は全て失効した」は不正確。D444 の supersede は Q2 の
   束縛張り替えに限定され Q3 は残る。B は依然不許可、A は未失効、C も自動承認ではない。
   失効したのは選択肢ではなく「既存 bytes を書き換えるしかない」という前提のほうである。

**S1 単独 land が構造的に失敗することを実測前に確定した。** resolver は現行 contract 一致を
exact 1 件要求するため g2 activation 後に g2 protocol が無いと count=0 になる。加えて
`campaign.lock` が contract hash と activation tuple を束縛するため既存 g1 campaign は resume 拒否、
certified acceptance は `E1-stale` へ落ちる。安全な最小単位は「配線 commit」+「S1/S2 atomic commit」の
2 段で、配備には走行中 campaign の停止と全 process 再起動が要る。

**次 wave への最重要の申し送りは配線の実装方法である。** 単純な path 置換は admission を弱める —
legacy anchor は HEAD の 100644 blob から読むのに対し versioned namespace は working tree から読み、
job の clean check は `output/` を全除外するため、未 commit の canonical file が resolver authority に
なり得る。必要なのは path 置換ではなく、選ばれた record について HEAD の exact blob 存在と bytes 一致を
admission / driver / holdout の 3 境界で検査することである。

**旧 branch の破棄前に設計資産 2 件を保全した。** 段 3 レンズ B が「ref 削除だけでは失われる」と
名指しした [T-660] の変異台帳 (検出力 5/5 の実証) と 2026-08-09 の裁定パッケージを
`output/insights/2026-08-17_t657-activation-rebuild/preserved-t657-t660/` へ退避した。
実行可能 script (`reissue_floor_protocol.sh`) は退避していない — [T-1255] が実凍結を AI 実行可能な
形へ設計変更中であり、旧 script を迂回経路として残すべきでないためである。

工数は codex 子 3 本 (plan 1、consult 2、いずれも reasoning=max、read-only)。実装子は起動していない。
受入全走は行っていない (docs のみの wave であり、実装面の差分がゼロのため)。

## 次の一手差分

### 見送り追記

- [T-660] 2026-08-17 に旧 branch `worktree-dev-wave-t657-t660-g2-activation` を破棄した際、変異台帳 (検出力 5/5) を `output/insights/2026-08-17_t657-activation-rebuild/preserved-t657-t660/` へ保全した。再訪時は同 path を一次資料とする。
