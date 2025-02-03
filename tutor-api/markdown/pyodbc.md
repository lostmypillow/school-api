### Overview

Typically, pyodbc is installed like any other Python package by running:

~~~
pip install pyodbc
~~~

from a Windows DOS prompt or Unix shell, but don't forget the pre-requisites described below. See the pip [documentation](https://pip.pypa.io/en/latest/user_guide.html "pip user guide") for more details about the pip utility. As always when installing modules, you should consider using [Python virtual environments](https://realpython.com/python-virtual-environments-a-primer/).

However, if you want to install pyodbc directly from a [binary wheel](https://realpython.com/python-wheels/), you can download them from the [Python Package Index](https://pypi.org/project/pyodbc/#files) (PyPi) and install with `pip install your-wheel-file.whl`. Wheels for older versions of pyodbc can also be found there.

### Installing on Windows

Try `pip install pyodbc` first. This should "just work" in the vast majority of cases. `pip` will download the correct pyodbc wheel for your PC/Python set up and install it.

If for some reason you need to build pyodbc from source — e.g., if `pip install pyodbc` downloads a source distribution like "pyodbc-4.0.35.tar.gz" instead of a pre-built wheel (.whl) file — then make sure you have the appropriate C++ compiler on your PC. Look [here](https://github.com/mkleehammer/pyodbc/wiki/Building-pyodbc-from-source#windows) for details on that.

### Installing on MacOSX

Binary wheels for MacOSX are [published](https://pypi.org/project/pyodbc/#files) for most Python versions and for both Intel and ARM processors (pyodbc v5.1.0 onwards).  However, before installing pyodbc make sure you have already installed a driver manager.  pyodbc does not provide a driver manager.  The recommended driver manager on Macs is [unixODBC](http://www.unixodbc.org/) so typically, pyodbc on MacOSX would be installed as follows:

~~~
brew install unixodbc
pip install pyodbc
~~~

In a conda environment, use `conda install unixodbc` instead of `brew install unixodbc`.

To install pre-v5.1.0 pyodbc on ARM64 Macs, try compiling from the source distribution:

~~~
brew install unixodbc
pip install --no-binary=pyodbc pyodbc
~~~

### Installing on Linux

Starting with pyodbc 4.0.35, Linux wheels are available from PyPI. However, they do not include their own copies of the unixODBC library files (because that caused [problems](https://github.com/mkleehammer/pyodbc/issues/1082)), so if pip installs pyodbc from those wheel files then unixODBC must be installed separately.

That is, if you `pip install pyodbc` and receive this error when you try to `import pyodbc`

```
$ python
Python 3.10.6 (main, Nov  2 2022, 18:53:38) [GCC 11.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import pyodbc
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: libodbc.so.2: cannot open shared object file: No such file or directory
```

then install unixODBC. For example, on Ubuntu that would be

```
$ sudo apt install unixodbc
```

The following are the older instructions for previous versions of pyodbc where it was installed from the source distribution (sdist). They may be helpful if you are using a distribution that is not compatible with the 4.0.35+ wheels (e.g., Oracle Linux 8.5).

#### Alpine Linux

~~~
apk add python3 python3-dev g++ unixodbc-dev
python3 -m ensurepip
pip3 install --user pyodbc
~~~

#### Amazon Linux 2

Amazon Linux 2 is similar to Red Hat and CentOS

~~~
sudo yum install gcc-c++ python3-devel unixODBC-devel
# replace <release_num> with the current release
sudo ln -s /usr/libexec/gcc/x86_64-amazon-linux/<release_num>/cc1plus /usr/bin/
pip3 install --user pyodbc
~~~

#### Azure Databricks

https://docs.microsoft.com/en-us/azure/databricks/kb/libraries/install-pyodbc-on-cluster

#### CentOS 7

From a clean minimal install of CentOS 7, the following steps were required:

###### Python 2
~~~
sudo yum install epel-release
sudo yum install python-pip gcc-c++ python-devel unixODBC-devel
pip install --user pyodbc
~~~

###### Python 3
~~~
sudo yum install epel-release
sudo yum install python3-pip gcc-c++ python3-devel unixODBC-devel
pip3 install --user pyodbc
~~~

#### Debian Stretch

Similar to Ubuntu, you need to install `unixodbc-dev`, but you will also need to install `gcc` and `g++`. Note `gcc` package is automatically installed when installing `g++`

~~~
apt-get update
apt-get install g++ unixodbc-dev
pip install --user pyodbc
~~~

#### Fedora 27

~~~
sudo dnf install redhat-rpm-config gcc-c++ python3-devel unixODBC-devel
pip3 install --user pyodbc
~~~

#### OpenSUSE

Similar to Fedora, the following packages were required after a clean install of OpenSUSE Leap 42.3

~~~
sudo zypper install gcc-c++ python3-devel python3-pip unixODBC-devel
pip3 install --user pyodbc
~~~

#### Oracle Linux 8.5

The following packages were required after a clean install of Oracle Linux 8.5

~~~
sudo dnf install gcc-c++ python3-devel unixODBC-devel
pip3 install --user pyodbc
~~~
