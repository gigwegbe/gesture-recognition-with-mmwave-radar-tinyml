# Requirements

- [x] Miniconda - *Miniforge aarch64 for Raspberry Pi 4* - *[Link](https://github.com/conda-forge/miniforge#download)*
    ```bash
    # installing miniconda for Raspberry Pi 4 (aarch64)
    $ sudo wget -c https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
    $ sudo chmod 744 Miniforge3-Linux-aarch64.sh
    $ ./Miniforge3-Linux-aarch64.sh
    ```
- [x] pip v22.3.1
- [x] Python3 v3.9.15
- [x] NumPy v1.23.5
- [ ] Pandas v
- [ ] PySerial v
- [x] Tensorflow v2.11.0
- [x] QtBase5-dev *[Link](https://stackoverflow.com/a/71019962)*
- [x] PyQt-builder v1.14.0 *- this installs SIP v6.7.5*
- [ ] PyQt v5.15.7 *[Link1](https://github.com/pypa/pip/issues/11286#issuecomment-1193156043)* *[link2](https://github.com/pypa/pip/issues/11286#issuecomment-1195615499)*
    ```bash
    # draft
    $ sudo wget -c <pyqt-sip download link>
    $ tar <archive name>
    $ cd <top level dir>
    $ python3 setup.py OR $ python3 sip-install
    ```
- [x] Tarball v0.0.7
- [x] PyQtGraph v0.13.1
