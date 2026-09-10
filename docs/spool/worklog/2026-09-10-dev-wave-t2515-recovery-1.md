---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2515-recovery
seq: 1
title: [T-2515] 現行mainの後続修正を保ち、rr5/rr95投入対応と失敗実測だけを回収する
---

## 本文

- 指定tip `559bcbc29cfa27412f103b608e8ac708dcfae6b9` を照合し、merge途中の既存worktreeに触れず、
  `e618883c2` から専用worktreeを作った。T-1851 D2とT-2417の現在の所有を確認し、対象4実装fileとの重複は0。
- 主目的は既存の本体実装と失敗実測の回収だけ。fixture共有化、旧spoolの裁定fragment、新規測定、
  patch materialize、receipt schema拡張は含めない。失敗の一次資料は
  `output/insights/2026-09-10_t2515-rr95-rr5-calibration/README.md`。
- **rr95/rr5のaccepted calibrationは未取得。** 当時の拒否は記録のまま残す。作業中にD1936が着地し、
  不要BACKOFF指定の整合撤去とT-2579のfixture共有化は裁定済みとなったが、今回の明示scopeへ追加しなかった。
- planと相談で、後続T-2535のproduction関数harnessとtoolchain抽出境界の接続修正が必要と判明した。
  M5/M6の正規化変異が後続offline検査で再拒否されるmaskも除き、M8は選定済みPythonと裸Pythonを
  既存実起動fixtureで区別した。T-2535/T-2536の既存修正は維持した。
- 独立レビュー2本はGO、must-fix 0。古いコメントと冗長PATH代入は挙動に影響せず、追加fixをしなかった。
- 親の関連7file個別走は **1379 passed / 4 skipped / 0 failed**。変更2fileの単独走は70件と69件。
  Codex agent検査・docs検査はrc=0。anchor `35a740cd4` の全史provenanceは9425件・新規違反なしで、
  既存台帳へ分離された違反を含む全履歴を無違反とは呼ばない。
- 実装前の7file並列走は7件赤（既存CMakeの5秒timeoutとfloor診断index）。calibration単独は非再現。
  floor単独直列は親rc=0だがfork子の例外が同logに出たため、これを全緑証拠にせず、8並列の別走で143passedを確認した。
  2回のpytest終端後にown scopeへ孤児processが残り、F846の観測どおりrunnerが待った。
  PPID1・cwd・scopeを照合してそのprocessだけTERMし、元のrunner終了コードを回収した。
- 関連走のcompute投入2本は、予定開始が13:18 JSTだったためQUE中に親dispatcherを止め、
  正規cleanupのqdel成功とorphan hold削除を確認した。rc=16をテスト結果へ数えていない。
- authorは実装を作成したが、最終メッセージのH2不足で採用検査が赤になった。
  原稿と赤を保存し、報告形式だけを再提出してrc=0を確認した。実装はD95のCodex author、親は実装面を直接編集していない。
  子のpytestはsandbox内dispatch preflightで未起動のため、親の実走で検証した。
- 子はplan1、consult2、実装author1、報告再提出1、review2の計7本。新しいwaveは起動していない。
- 変異はD842/D1358の既存mutation taskで各wrapperを1 jobへ束ねた。probeは989985.nqsv、
  本走は989993.nqsv（会計Elapse217秒/218秒）。本走8/8 KILLED・期待node完全一致・rc=0。
  M7はdocs整合pinで、実装に関わる7件と区別する。初回probeの8 MISMATCHも保存した。
  M5/M6はrc=0対期待2、M8は実起動rc97を観測。M8の期待8nodeはprobeから機械生成した。
- 束ね変異の初回2投入は、同一Pythonの絶対path要求とwalltimeのHH:MM:SS要求で起動前に拒否された。
  両方のlogを残し、正規argvへ直して再投入した。検査や関門は変更していない。

## 次の一手差分

### carry

- [T-2515]
