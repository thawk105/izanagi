# 敵対レビュー所見と親の裁定 — [T-118] provider neutral tree の lifecycle

敵対子は 4 本 (段 3 = レンズ A/B、段 6 = レンズ C/D)、焦点再レビュー 1 本。
**段 3・段 6 の 4 本はすべて NO-GO。** 焦点再レビューだけが GO。
逐語は各子の出力にあり、本書は所見と親の裁定を凍結する。

## 段 3 (プランと親 brief への攻撃)

### レンズ A = 正しさ境界 (NO-GO、BLOCKER 4)

| 所見 | 親の裁定 | 恒久対応 |
|---|---|---|
| 「production の未後始末は 4 箇所だけ」は反証された | **real (親の誤り)** | 算術 (25−4=21) も意味も誤り。残り 21 箇所は正常系だけ後始末し、少なくとも 3 箇所は例外経路で漏れる → T-280 へ |
| `resolve()` した削除先は TOCTOU で `artifact_root` へ差し替わりうる | **real** | 削除対象を `mkdtemp()` の生返値 (作成時 identity) に限定 + symlink 拒否 + 非交差 assert |
| `finalize + ignore_errors` は失敗後に再試行不能で、例外時は受理集合も変える | **real** | `close()` は送出しない・失敗は `cleanup_error` へ・**成功時だけ detach** |
| root guard の positive control は false-green | **real** | predicate 分離負例へ再設計 |
| 新設 gate が届く層は主張より狭い | **real** | 届かない層を guard docstring と worklog に明記 |
| 「失敗時 forensic を残す」と owner の無条件 close が矛盾 | **real (親の誤り)** | (P2) の理由を既存 pin へ差し替え |
| 5,626 件は production campaign の実測でなく test が踏んだ値 | **real** | 実行 provenance を worklog で限定 |
| (P3) の「常に cache miss」は導出できない | **real (親の誤り)** | 結論維持・理由を `patchharness` の lock scope へ差し替え |
| pytest の機械拒否は Codex 面に存在しない | **real** | 実装子 prompt で明示禁止 (`AGENTS.md:31` が正本) |

### レンズ B = 到達性・実効性・scope 誠実性 (NO-GO、BLOCKER 2)

| 所見 | 親の裁定 | 恒久対応 |
|---|---|---|
| 5,626 個の実行主体は pytest であり、この scope で T-118 は閉じられない | **real** | **T-118 を閉じない。「部分解消・未完」で記録**し、後続を新 ID (T-280〜T-282) で採番 |
| guard の root positive control は非独立で root assert 削除変異が生存する | **real** (レンズ A と独立に同一欠陥へ到達) | predicate 分離負例 |
| (P3) の receipt memo 因果は成立しない | **real** | 上記のとおり理由差し替え |
| projected provider の明示 close は第 3 production file を必須 scope にしない限り未到達 | **real** | `p3_autonomous_workload_trial.py` を必須 scope へ |
| 既存の generic temp leak guard は無い (二重実装ではない) | **real (nit)** | T-282 へ |

## 段 6 (実装への攻撃)

### レンズ C = 裁定忠実性・code motion 等価性 (NO-GO、BLOCKER 1 / major 2)

- **code motion は等価**と確認された。`run_trial` 本体を `_finish_trial` へ切り出す 167+/112− の
  移動について、移動前 HEAD と現行を **AST 比較して一致**。`status`、report field 順、
  `journal.append` の件数・順序、捕捉する例外型に差はない
- 既存 pin 3 箇所は行番号移動のみで assert 不変 (旧 557 → 900、569-574 → 912、653-659 → 1000)
- BLOCKER: artifact 負例が predicate 分離になっていない (`rmtree` + bytes 空の二重擾乱)
- major: projected guard に負例が皆無 / B5 docstring が実態と矛盾 (再試行は到達済み)

### レンズ D = テストの歯 (NO-GO、BLOCKER 3 / major 2)

- **M7 と M14 は殺せない**と判定
  - M7: finalizer を先に登録するので、明示 cleanup を消しても failed owner の破棄時に
    fallback が同じ root を消す。テストは最終的な path 不在しか見ておらず**両者を区別できない**
  - M14: artifact assert を削除すると `resolve(strict=True)` が `FileNotFoundError` を投げ、
    赤の理由を artifact predicate へ一意帰属できない
- **変異 M2/M3/M6 を当てると guard test 自身が system temp を漏らす** (失敗経路に `finally` が無く、
  root は `tmp_path` の外にある)。**変異本走が T-118 の残留を自ら増やす**
- major: M16 の非交差 assert が実削除引数に束縛されていない (close 前 snapshot のため) /
  projected guard の root/artifact/bytes に負例なし

### 親の独自所見 (F7)

`_remove_neutral_root` が `artifact_root` を `resolve(strict=True)` するため、artifact_root が
外部から消えていると**後始末が不発になり neutral root が残る**。後始末が目的の関数が、
後始末と無関係な事前条件で不発になってはならない → `strict=False` 化 + 両方向を pin。

## fix と焦点再レビュー

所見 7 件 (F1〜F7) を**単一 fix 単位**で処理した。単一化の理由: 全件が同じ 2 つの test file の
guard helper と共有の負例設計に触れ、分割すると同一 helper への競合編集になる (`DW-S06-B`)。

焦点再レビューは 9 所見すべて `closed`、`partial` / `regressed` ゼロ、M1〜M16 すべて
期待方向へ殺せると判定し **GO**。その後の変異本走 (16/16 KILLED、canonical 一致 16/16) が
静的判定を実測で裏取りした。

## refuted (親が採らなかったもの)

なし。段 3・段 6 の real 判定に対する反証は成立しなかった。ただし**親の brief の主張 6 件が
子によって反証された**方向の refuted があり、それらは `s4-adjudication-plan-v2.md` §0 の訂正表に
凍結してある。
