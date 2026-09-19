# 段4裁定・plan v2

plan/consult 2本を読了。D2148項4をそのまま実装する。新しい裁定による範囲変更なし。

- P1はrealな未検証事項。production build_target(phase1)をpristine stagingから通す。
- study headerのIMPL guardで既存C++ testが壊れる所見はreal。
  テスト削除・除外案は不採用。既存SS2PL_STUDY_LOCK_TESTINGの明示test seamで宣言を見せる
  最小修正を優先し、IMPL=0/1双方の既存テスト内容とproductionのIMPL guardを保存する。
  単一定義のtarget別IMPL=1案はIMPL=0 test被覆を変えるため採らない。
- deadline所見はreal。新しいwatchdogや共有helper変更は加えず、既存_run_checkedによる
  cc/c++/cmakeの--version観測で既存manifest schemaへ供給する局所接続を許す。
  helper configure/targetの正整数timeoutの合計は既存stage残時間内とし、終了後も既存check。
  timeoutの新規一般化・状態管理・新gateは作らない。
- 旧binary buildは計器比較のためには不要という削減を採用。旧全target TUの実前処理で比較する。
- 専用staging複製を使う。controlsのSは既存どおり拒否。phase1だけが正例。
- 受理禁止: gate登録簿target/companion、stock_comparison、require_condition_gate_family、
  validate_abort_counter_ownership、INERT_DECLARED_DIFFERENCESの変更。通る正例はphase1の4非既定値。

## 変異事前登録
M1 helper削除: pristineでconfig.h不在によりphase1 buildが拒否される。後置との重複は削る。
M2 study条件include復活: phase1 IMPL supplyがdependency-closure-driftで拒否。
M3 transaction WFG条件include復活: phase1 WFG supplyがdependency-closure-driftで拒否。
M4 DLR marker分岐復活: phase1 DLR supplyがcompile-command-driftで拒否。
M5 publish_wait実呼出し1箇所削除: 旧/新計器保存比較が不一致。gate killとは数えない。
M6 wfg.cc無条件追加: WFG=0既存不在検査が拒否。
単一箇所・独立pristine入力で実施する。実装後にexact anchorと失敗nodeを確定し、maskを再評価する。

## 規模・所有
author1単位。productionはrunnerと既存patchだけ、関連テストは既存SS2PL testへ最小追加。
必要な実build検証を100行以内の使い捨てpytest probeへ置いてよい。親がrun_tests.py経由で実行し、
probeは実行後job dirへ退避、repoには逐語.mdとしてのみ記録。複雑な独自harnessは作らない。
コード・テストはauthor、docs/統合/変異全走/受入/commitは親。既存期待値は変更しない。
