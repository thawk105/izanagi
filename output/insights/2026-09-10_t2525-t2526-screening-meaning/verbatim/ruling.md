# 段4裁定・plan v2
- D1859/D1936項19どおり実装する。plan.mdは以下の縮小を優先したv2として採用。
- consult両者の追加case拒否不要はreal・採用。screeningに新しい宣言整合gateを足さず、既存のMeaningWitnessDeclaration転送だけにする。共通gateの未確立扱いを変えない。
- create-only専用の新設test/変異は不要。writerは変更せず既存被覆を用いる。basename据置による旧上書き懸念はv2 slug分離によりrefuted。
- helper抽出はbackoff_sweep内だけ。既存のmapping key/type/physical検証を保ち、期待bitsはfloat(physical)。同じintentを外側gateとscreened callerで使う。
- s1_direct_comparison/paper_story_a2_certificationは現行物理literal 5/10/2と10/5の一致を確認。未使用の高域対応を追加しない。
- T2418のみscale/spec_slug/trial/report schemaをv2。meaning_witness_status=driver_declared_static_backoff_physical_us。JSON/DAT/config一致。旧v1 fallbackなし。共通gate・格子・正式系列変更なし。
- 受理: raw3000/physical1000の既存観測一致はgreen。拒否: raw1000/physical1000の既存意味不一致はred。無宣言乱択を勝手にstatic化しない。
- 親baseline: main98a3d7c9eと同一checkoutで対象3file 108 passed (7.00s)。最初の2走は各98 passed/10 failed、祖先.gitによるtmp誤配置。専用TMPDIR=/work/1/SFC/tanab/test-tmp-t2525-t2526で解消。製品/検査を変更していない。
- 裁定inboxにはT2525/T2526の追加入力なし。旧凍結hashの既存不一致は本題に含めない。

## 変異事前登録
- M1 screening最終meaning呼出で宣言をNoneに戻す。green意味状態と不一致redの消失を検出。
- M2 helperのfloat(physical)をfloat(raw)へ置換。raw3000/physical1000正例がredへ変わることを検出。
- M3 evaluate_candidate→gateの宣言転送を落とす。公開APIの実gate検査が検出。
- M4 stock checkout分岐の宣言転送を落とす。他macro stock比較を含むgenomeとBACKOFF_FIXED正値で検出。
- M5 backoff screened callerの候補宣言を落とす。caller spyに加えて実意味検査のgreenを確認。外側gateの拒否をkill根拠にしない。
- M6 T2418 v2 identityをv1へ戻す。実discoveryで旧campaignを拾う変化を検出。
- M7 T2418 statusを旧未確立へ戻す。config/JSON/DAT出力内容の変化。これは受理gate killとは別のmetadata回帰検出として記録する。
- 各置換は一意、統合commitの隔離scratchで実施。baseline緑必須。期待失敗nodeは実装後のprobeで確定して本走を再登録する。新しいharnessなし。
