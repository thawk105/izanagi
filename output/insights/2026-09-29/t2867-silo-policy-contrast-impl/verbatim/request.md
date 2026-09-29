/dev-wave の引数 (2026-09-29、ユーザー直接発話、逐語):

[T-2867] silo-function-policy 軸の生成器対照 (4 arm = LLM×C++・LLM×IR・random×IR・進化×IR、D2272 項 4)
  の実装と生死確認を進める。事前登録の草稿は docs/silo-policy-generator-contrast-preregistration.md
  (D2263、未発効)。実装は output/insights/2026-09-27/t2867-silo-policy-contrast-draft/ の §5 で、Codex author (D95)
  が行う。中身は、政策 driver の系列ごとの campaign identity・停止規則の切り離し・機械生成 IR の口・stock と静的 10
  µs の口・初期点・同時検査の key・job body、G_rand と (1+1) 進化の生成器、系列制御と起動器、LLM の round tool
  と親の指示文、report。段階 F の生死確認 (C++ 形・IR 形の実 LLM 1 iteration、機械生成 IR の 1 評価) の job Elapse
  で、草稿 §11.3 の見積りを取り直す。発効と系列数 (n = 12 か 10) はユーザーが決めるので、発効束 (草稿 §12)
  を埋めた見積りを返して止める。並走する [T-2865] は起動時点の detached checkout で走るので、本 wave の land
  は影響しない。検査と生死確認の job 合計が 2 node 時間以上なら、見積りを示してユーザー確認後に投入。規律 2・3
  は不変。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
