# Benchmarking and Evaluating current PDF Extraction Tools #

This project is about benchmarking and evaluating existing PDF extraction tools on their semantic abilities to extract the *body texts* from PDF documents, especially from *scientific articles*.
It provides (1) a benchmark generator, (2) a ready-to-use benchmark and (3) an extensive evaluation, with meaningful evaluation criteria.

## The Benchmark Generator
+ constructs high-quality benchmarks from *TeX source files*.
+ identifies the following 16 *semantic units*: 
    <span style="color:#555">title, author, affiliation, date, abstract, heading, paragraph of the body text, formula, figure, table, caption, listing-item, footnote, acknowledgements, references, appendix</span>
+ serializes desired semantic units to *plain text*, *XML* or *JSON* format.

For more details and usage, see [`benchmark-generator/`](https://github.com/ckorzen/arxiv-benchmark/tree/master/benchmark-generator).


## The Benchmark
+ consists of *12,099 ground truth files* and *12,099 PDF files* of scientific articles, randomly selected from [*arXiv.org*](https://arxiv.org/).
Each ground truth file contains the *title*, the *headings* and the *body text paragraphs* of a particular scientific article.
+ was generated using the benchmark generated above.

For more details and usage, see [`benchmark/`](https://github.com/ckorzen/arxiv-benchmark/tree/master/benchmark).

## The Evaluation
+ assessed the following 13 PDF extraction tools:
[pdftotext](https://poppler.freedesktop.org/), [pdftohtml](https://poppler.freedesktop.org/), [pdftoxml](https://sourceforge.net/projects/pdf2xml/), [PdfBox](https://github.com/apache/pdfbox), [pdf2xml](https://bitbucket.org/tiedemann/pdf2xml/), [ParsCit](https://github.com/knmnyn/ParsCit), [LA-PdfText](https://github.com/BMKEG/lapdftext), [PdfMiner](http://www.unixuser.org/~euske/python/pdfminer/index.html), [pdfXtk](https://github.com/tamirhassan/pdfxtk), [pdf-extract](https://github.com/CrossRef/pdfextract), [PDFExtract](https://github.com/elacin/PDFExtract), [Grobid](https://github.com/kermitt2/grobid), [Icecite](https://github.com/ckorzen/icecite).

For more details and usage, see [`evaluation/`](https://github.com/ckorzen/arxiv-benchmark/tree/master/evaluation).