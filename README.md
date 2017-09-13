# uproot

uproot (or &mu;proot, for "micro-Python ROOT") is a demonstration of how little is needed to read data from a ROOT file. Only about a thousand lines of Python code are needed to convert ROOT TTree data into Numpy arrays.

It is important to note that uproot is _not_ maintained by the [ROOT project team](https://root.cern/) and it is _not_ a fully featured ROOT replacement. Think of it as a file format library, analogous to h5py, parquet-python, or PyFITS.

uproot has the following dependencies:

   * Python 2.7 or 3.4+ (Python 2.6 _might_ work, but it's untested)
   * Numpy 1.4+
   * 




uproot has no dependencies other than Python and Numpy— and the [LZMA](https://pypi.python.org/pypi/backports.lzma) and [LZ4](https://pypi.python.org/pypi/lz4) libraries if you read ROOT files with these compression options enabled (you would be prompted with instructions if this is the case; note that Python 3.3+ has LZMA support built-in). You do not need to have the C++ version of ROOT installed to use uproot.

It is important to note that uproot is _not_ maintained by the [ROOT project team](https://root.cern/), and it is _not_ a fully featured ROOT replacement. It is a file format library, intended to make ROOT files accessible in environments where it is difficult to deploy ROOT. Compare to h5py, which only reads HDF5 files, or parquet-python, which only reads Parquet files.

uproot is just ROOT I/O.

## Scope

The primary goal of uproot is to present data from ROOT files as Numpy arrays, making them accessible to any scientific Python projects based on Numpy (i.e. all of them). Reading and decompression are lazy, so uproot benefits from the same selective reading as ROOT— you only have to wait for the branches you're interested in. Since most of the time is spent loading data from disk/network, decompression, and Numpy/Numba calculations, uproot can be as fast as reading your ROOT file in C++.

[**TODO:** performance plots]

## Status and goals

uproot currently has the following features:

   * reading flat TTrees;
   * reading TTrees containing structured objects (fully split);
   * memory mapped files or standard files;
   * uncompressed, ZLIB, LZMA, LZ4;
   * read/decompress TBaskets in parallel;

and the following are planned:

   * reading "leaf list" and fixed-sized leaf arrays as Numpy recarrays and multidimensional shapes;
   * writing flat TTrees (not structrued and not from the same file as reading);
   * reading a few basic types of non-TTree objects, relelvant for analysis, such as histograms and graphs;
   * import-on-demand connections to Pandas, Keras, TensorFlow, PySpark, etc.;
   * remotely access files through XRootD's Python interface;
   * conveniences for dealing with large sets of files (TChain equivalent).

## Acknowledgements

Conversations with Philippe Canal were essential for context, finding my way through 20 years of living codebase. Brian Bockelman's BulkIO additions to C++ ROOT also helped to clarify the distinction between I/O and interface. Also, Sebastien Binet's [go-hep](https://github.com/go-hep/hep) provided a clean implementation to ~~pillage~~ replicate.
