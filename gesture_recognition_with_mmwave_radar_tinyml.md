## Requirements

- [x] Miniconda - *Miniforge aarch64 for Raspberry Pi 4* - *[Link](https://github.com/conda-forge/miniforge#download)*
    ```bash
    # installing miniconda for Raspberry Pi 4 (aarch64)
    $ sudo wget -c https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
    $ sudo chmod 744 Miniforge3-Linux-aarch64.sh
    $ ./Miniforge3-Linux-aarch64.sh
    
    # creating a virtual environment using conda called pi4
    $ conda create -n pi4 python=3.9
    $ conda activate pi4
    $ conda list
    $ conda update conda
    ```
- [x] pip v22.3.1
    ```bash
    $ pip install pip
    ```
- [x] NumPy v1.23.5
    ```bash
    $ pip install numpy
    ```
- [x] Pandas v1.5.2
    ```bash
    $ pip install pandas
    ```
- [x] PySerial v3.5
    ```bash
    $ pip install pyserial
    ```
- [x] Tensorflow v2.11.0
    ```bash
    $ pip install tensorflow
    ```
- [x] QtBase5-dev *[Link](https://stackoverflow.com/a/71019962)*
    ```bash
    $ sudo apt-get install qtbase5-dev
    ```
- [x] PyQt-builder v1.14.0 *- this installs SIP v6.7.5*
    ```bash
    $ pip install PyQt-builder
    ```
- [x] PyQt v5.15.7 *[Link1](https://github.com/pypa/pip/issues/11286#issuecomment-1193156043)* *[link2](https://github.com/pypa/pip/issues/11286#issuecomment-1195615499)*
    ```bash
    # installing pyQt5 using (L)GPL License
    $ sudo wget -c https://files.pythonhosted.org/packages/e1/57/2023316578646e1adab903caab714708422f83a57f97eb34a5d13510f4e1/PyQt5-5.15.7.tar.gz
    $ tar -xf PyQt5-5.15.7.tar.gz
    $ cd PyQt5-5.15.7/
    $ sip-install
    # This is gonna take a while ... circa thirty minutes on Raspberry Pi 4
    # installing pyQt5-sip
    $ pip install pyQt5-sip
    ```
- [x] PyQtGraph v0.13.1
    ```bash
    $ pip install pyqtgraph
    ```
