# PoC on Github downloader

This script download all PoC registered in the very good repo '[PoC-in-Github]'(ttps://github.com/nomi-sec/PoC-in-GitHub) by *nomi-sec*

## How to use :
(it should work on Windows if git-cli is installed)
```shell
git clone https://github.com/Theophile-Wemaere/poc-on-github-downloader
cd poc-on-github-downloader
pip install -r requirements.txt
```

Help menu :
```shell
$ python main.py --help
usage: main.py [-h] [-b] [-u] [-s] [-p [path]]

CVE PoC downloader

options:
  -h, --help  show this help message and exit
  -b          Build the project
  -u          Update PoCbase
  -s          Search by CVE ID
  -p [path]   Path to the directory where you want to store PoCs
```

#### Buidling the project :

This option clone the PoC-in-Github repo, populate the database and download all PoC:
```shell
python3 main.py -b
```

Optional argument: `-p /path/to/folder` if you want to store the PoCs in another folder (like an external disks)

Example :
```shell
python3 main.py -b -p /run/media/HDD/PoCs/

# PoCs will be stored in the /run/media/HDD/PoCs/data/
```

> [!WARNING]
> At the time of 19/10/2024, the global PoCs folder take ~ 96G of storage and 50min to download

#### Updating the project :

To update the PoC-in-Github repository and download newly added pocs :
```shell
python3 main.py -u
# if you used -p during building, you need to specify it else it won't work
python3 main.py -u -p /run/media/HDD/PoCs
```

#### Searching by CVE ID :

To search available PoCs from the database 
```shell
python3 main.py -s
# same thing if you specified another folder during installation
python3 main.py -s -p /run/media/HDD/PoCs
```

Example :
```shell
$ python3 main.py -s -p /run/media/HDD/PoCs

Enter the CVE ID you want to search for (CVE-XXXX-XXXXXX) : CVE-2017-0144

Found 7 PoCs :

eternal_scanner, by peterpt
Github link : https://github.com/peterpt/eternal_scanner
About: An internet scanner for exploit CVE-2017-0144 (Eternal Blue) & CVE-2017-0145 (Eternal Romance)
Path on disk : /run/media/HDD/PoCs/data/2017/CVE-2017-0144/CVE-2017-0144_peterpt_eternal_scanner.zip

eternalblue, by kimocoder
Github link : https://github.com/kimocoder/eternalblue
About: CVE-2017-0144
Path on disk : /run/media/HDD/PoCs/data/2017/CVE-2017-0144/CVE-2017-0144_kimocoder_eternalblue.zip

< SNIP >
```