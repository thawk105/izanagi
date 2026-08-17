# [T-657] 活性化の立て直し — 所有の衝突により実装せず、旧 branch を保全して破棄した wave の逐語

2026-08-17 / branch `worktree-dev-wave-t657-activation-rebuild` / base `865a589a` / 実装差分ゼロ

## 依頼と結論

ユーザー指示は「未着地 11 commit の `worktree-dev-wave-t657-t660-g2-activation` を**破棄**し、
現行 main の `reseal_protocol()` で**立て直す**」であった。

**破棄は実施した。立て直しは実施しない。**
阻んだのは技術的不能ではなく **所有の衝突**である。立て直しの実体 (versioned 床値 protocol の
実発行と live consumer の配線) は、別 wave `dev-wave-t1255-floor-freeze` が**同日同時刻に稼働して
所有していた** (段 4 §裁定に実測 2 点)。allocation 上も配線 = [T-419] (3) / [T-1214]、
実発行 = [T-1255] である。

先取りすると固定 legacy path と versioned resolver の二重 authority が生じ、
resolver が count=0 / count=2 で fail-closed する。

## 立て直しが「reseal を呼ぶだけ」でない理由

親は当初「現行 main の `reseal_protocol()` を呼べば済む」と見立てた。段 2・段 3 がこれを覆した。

| 段階 | 判定器側 | 実 driver 側 | 結果 |
|---|---|---|---|
| 現在 | legacy g1 を exact 1 件選択 | legacy g1 | 一致 |
| S1 (活性化) のみ | g2 protocol が 0 件 | legacy g1 | admission が fail-closed |
| S1 → S2 (発行) | versioned g2 を選択 | legacy g1 | **authority 分裂** |
| 配線 → S1 → S2 | versioned g2 | 同じ versioned g2 | 安全な最終状態 |

さらに S1 単独は床値 admission だけでなく `campaign.lock` の resume と certified acceptance
(`E1-stale`) まで巻き込む。安全な最小単位は「配線 commit」+「S1/S2 atomic commit」の 2 段で、
配備には走行中 campaign の停止と全 process 再起動が要る。

## 撤回した親の主張 3 件

段 3 の敵対検証が親 brief と親の対ユーザー説明を覆した。記録として残す。

1. **「create-only なので取り消せない」は誤り。** `os.link()` は同一 path 上書きを防ぐだけで
   unlink は禁じていない。commit 前なら削除して出し直せる。
2. **「追加のみだから履歴不変条件と衝突しない」は言い過ぎ。** versioned artifact は
   `FROZEN_MANIFEST` の対象外で、履歴不変検査が効くのは ratified closure に入ったときだけ。
   正確には「衝突しない」ではなく「まだ検査対象ですらない」。
3. **「2026-08-09 裁定パッケージの A/B/C 3 択は全て失効した」は不正確。**
   D444 の supersede は Q2 の束縛張り替えに限定され Q3 は残る。B は依然不許可、A は未失効、
   C も自動承認ではない。失効したのは選択肢ではなく、「既存 bytes を書き換えるしかない」という
   **前提**である (D444 が create-only の versioned 経路を開いたため)。

## 旧 branch の扱い

`worktree-dev-wave-t657-t660-g2-activation` (未着地 11 commit、tip `74cceee5`) を破棄した。
worktree 残骸は無く、ref 削除のみで足りることを実測して確認した。

破棄前に、段 3 レンズ B が「ref 削除だけでは失われる設計資産」と名指しした 2 件を
`preserved-t657-t660/` へ退避した。

| path | 内容 |
|---|---|
| `preserved-t657-t660/package.md` | 2026-08-09 の裁定パッケージ (A/B/C の 3 択と撤回経緯)。**上記 3 の限定つきで現行有効** |
| `preserved-t657-t660/mutation-ledger-a.json` | [T-660] 末尾巻き戻し検査の変異台帳 A |
| `preserved-t657-t660/mutation-ledger-b.json` | [T-660] 同 B。検出力 5/5 の実証記録 |

実行可能 script (`reissue_floor_protocol.sh`) は**退避しない**。[T-1255] が実凍結を AI 実行可能な
形へ設計変更中であり、旧 script を迂回経路として残すべきでないためである。

## ファイル

| path | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。provisional 前提 P1〜P4 を含む |
| `verbatim/s2-plan.md` | 段 2 プラン (codex plan、read-only、reasoning=max)。先行 blocker を発見 |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A (sol)。不可逆性と正しさ境界。所見 10 件 |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B (luna)。列挙の網羅性と所有境界。所見 14 件 |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (親)。所見 17 件の real/refuted と申し送り |
| `preserved-t657-t660/` | 旧 branch から退避した設計資産 (上表) |

## 段 8 自己改善 — 裁定へ返す候補 1 件

**`DW-S01` の実編集計測義務と凍結境界が衝突する。** `DW-S01` は「コード変更を伴う前提は
monkeypatch でなく実編集・即時復元で測る」「段 5 へ遅らせない」と命じるが、入口の凍結境界は
「親は実装面を直接編集せず」と定める。本 wave の前提 (activation record を置いたときの fallout)
は機械設定 = 実装面であり、親は実編集で測れなかった。

親は `DW-S01` 末尾の「実編集不能なら拒否事実と模擬との差を書く」に従い、判定器 library を
直接呼ぶ経路 (模擬ではなく本物の判定器) で受理性だけを実測し、brief (P4) に限界を明示した。
段 3 レンズ A の所見 10 が、この実測から「実装後も緑」を一般化できないことを独立に確認している。

**実装しない。** 段構成と実装子権限の境界に関わるため `DW-S08` に従い裁定パッケージへ送る。
docs 予算が 3 層とも満杯であることも、本 wave では入口・reference の編集を選ばない理由である。

論点: 親が実装面を「計測のため一時的に書いて即復元する」ことを凍結境界の例外として認めるか、
認めないなら `DW-S01` の実編集義務を実装面の外へ限定する明文を置くか。

## 次 wave への申し送り (要点)

最重要は**配線の実装方法**である。単純な path 置換は admission を弱める —
legacy anchor は HEAD の 100644 blob から読むのに対し versioned namespace は working tree から
読み、job の clean check は `output/` を全除外するため、未 commit の canonical file が
resolver authority になり得る。必要なのは path 置換ではなく、選ばれた record について
HEAD の exact blob 存在と bytes 一致を admission / driver / holdout の 3 境界で検査することである。

残りの申し送りは `verbatim/s4-adjudication.md` の末尾節。
