# Web で確認した外部条件 (2026-09-22 08:5x JST 取得、WebFetch の抜粋要約。逐語は tool 出力の引用部)

## VLDB 2027 (PVLDB Vol.20) submission guidelines — https://www.vldb.org/2027/submission-guidelines.html
- "Authors must submit supplemental material, such as code, data, and other implementation artifacts used to produce the results reported in the paper."
- "Authors should place the supplemental material in a publicly accessible archival repository and provide a URL during the submission process."
- 受理される置き場: "standard openly accessible file sharing services with well-understood privacy policies and permanence guarantees, e.g., a public GitHub repository." 個人 web サイトは不可 ("Personal websites are not acceptable.")
- EA&B: "Experiment, Analysis & Benchmark Papers are required to make available all experimental data and related software (there are no excuses); and submit their experiments for reproducibility evaluation by the PVLDB Reproducibility Committee."
- 時期: "For PVLDB volume 20, already the initial submission must include a link to the full reproducibility package of all experiments, data, and artifacts with meaningful instructions on how to run the experiments."
- 容量・形式の指定: 取得した本文には無い (WebFetch の要約で言及なし)。匿名性 (double/single blind) も両ページで言及なし。

## VLDB 2027 call for research track — https://vldb.org/2027/call-for-research-track.html
- EA&B: "The core contribution of such papers are often insights into workloads and reusable artifacts such as benchmark suites or traces."
- 匿名性の記述: 取得した本文には無い。

## Zenodo — https://help.zenodo.org/docs/deposit/manage-files/
- "You can upload up to a 100 files and a total volume of 50GB (50,000,000,000 bytes)."
- "20+ files: We recommend that you package them in a ZIP archive"
## Zenodo — https://help.zenodo.org/docs/deposit/manage-quota/
- "Each record comes with a default storage quota of 50GB"
- "you also have an additional allowance of up to 150GB that can be distributed across your uploads as needed"
- 料金の記述: 無し。
- 1 レコードの一回限り増枠 (最大 200 GB) は Web 検索結果の要約 (二次) にだけ現れ、公式 URL https://help.zenodo.org/docs/deposit/manage-files/quota-increase は 404。**未確認**として扱う。

## GitHub — https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- "GitHub blocks files larger than 100 MiB."
- "If you attempt to add or update a file that is larger than 50 MiB, you will receive a warning from Git."
- "We recommend repositories remain small, ideally less than 1 GB, and less than 5 GB is strongly recommended."
- release asset / LFS の上限値: 取得した本文には具体値なし。
