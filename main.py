import os
import subprocess
import shlex
import shutil
import sys
import sqlite3
import requests
import json
import argparse
import threading
from alive_progress import alive_bar

GIT_URL = "https://github.com/nomi-sec/PoC-in-GitHub"
FOLDER_NAME = "PoCInGithub"
BASE_PATH = ""
DATABASE = "pocdatabase.db"

THREADS = []
RUN_EVENT = None

def get_data_from_db()-> dict:
    """
    return all rows from the database
    """

    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    data = {}
    cursor.execute("SELECT DISTINCT year FROM pocs ORDER BY year ASC")
    years = cursor.fetchall()
    for year in years:
        cursor.execute("SELECT * FROM pocs WHERE year=? ORDER BY year ASC",year)
        rows = cursor.fetchall()
        data[year[0]] = rows

    db.close()
    return data

def save_year_to_db(cve_pocs: list):
    """
    save poc data to database
    """

    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    for poc in cve_pocs:
        try:
            cursor.execute("INSERT INTO pocs VALUES(?,?,?,?,?,?,?)",poc)
        except sqlite3.IntegrityError:
            pass
    db.commit()
    db.close()

def save_data(data: dict):
    """
    save data to database
    for each poc, save year, cveid, author and url
    """

    for year in data:
        cve_pocs = []
        for cve in data[year]:
            for poc in data[year][cve]:
                author = poc["owner"]["login"]
                name = poc["name"]
                description = poc["description"]
                url = poc["html_url"].replace('\\','')
                pocid = year+cve+author+name
                cve_pocs.append((year,cve,author,name,description,url,pocid))
        save_year_to_db(cve_pocs)

def parse_folders()-> dict:
    """
    parse FOLDER_NAME folder to retrieve content of all json file
    return dict item with years as key and array of CVE for each year
    """
    data = {}

    dirs = sorted(set(os.listdir(BASE_PATH + FOLDER_NAME)))
    if "README.md" in dirs:
        dirs.remove("README.md")
    if ".git" in dirs:
        dirs.remove(".git")
    for year in dirs:
        data[year] = {}
        for cve in os.listdir(f"{BASE_PATH + FOLDER_NAME}/{year}"):
            cveid = cve.replace('.json','')
            with open(f"{BASE_PATH + FOLDER_NAME}/{year}/{cve}","r",encoding="utf-8") as file:
                json_data = json.load(file)
                data[year][cveid] = json_data
        print(f"For year {year}, found {len(data[year])} CVE")

    return data

def init_db():
    """
    initialize sqlite database
    create table
    """
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pocs(
        year TEXT,
        cveid TEXT,
        author TEXT,
        name TEXT,
        description TEXT,
        url TEXT,
        id TEXT NOT NULL PRIMARY KEY
    )""")
    db.commit()
    db.close()

def clone_pocs_from_year(pocs: list, bar):
    """
    clone pocs from year
    pocs is the list of pocs to clone
    bar is the pogress bar object
    """

    for row in pocs:

        if RUN_EVENT.is_set():
            return

        year, cveid, author, name, url = row[0], row[1], row[2], row[3], row[5]

        if not os.path.exists(f"{BASE_PATH}data/{year}"):
            os.mkdir(f"{BASE_PATH}data/{year}")
        if not os.path.exists(f"{BASE_PATH}data/{year}/{cveid}"):
            os.mkdir(f"{BASE_PATH}data/{year}/{cveid}")

        file_name = (f"{BASE_PATH}data/{year}/{cveid}/{cveid}_{author}_{name}.zip")

        print(f"Downloading PoC for {cveid} by {author}")
        r = requests.get(url+"/archive/refs/heads/master.zip",stream=True)
        if r.status_code == 200:
            with open(file_name,"wb") as file:
                for chunk in r.iter_content(chunk_size=128):
                    file.write(chunk)
        else:
            print(f"Error Downloading PoC for {cveid} by {author}")
            print(f"{r.status_code}: {r.text}")
        bar()

def update_pocs(from_init=False):
    """
    parse database and download PoCs not already downloaded
    if from_init is True, skip git pull of the repo
    """

    global THREADS, RUN_EVENT

    if not os.path.exists(BASE_PATH + FOLDER_NAME):
        print(f"No {FOLDER_NAME} folder found in path {BASE_PATH},\nuse -b to build project or specify path to poc base folder with -p")
        sys.exit(1)

    if not from_init:
        folder_name = BASE_PATH + FOLDER_NAME
        folder_name = folder_name.replace(' ', '\\ ')
        os.system(f"cd {folder_name}; git pull")

    if not os.path.exists(f"{BASE_PATH}data/"):
        os.mkdir(f"{BASE_PATH}data")

    data = get_data_from_db()
    to_clone = {}
    total = 0

    for year in data:
        to_clone[year] = []
        for row in data[year]:
            year,cveid,author,name = row[0], row[1], row[2], row[3]
            file_name = (f"{BASE_PATH}data/{year}/{cveid}/{cveid}_{author}_{name}.zip")
            if not os.path.exists(file_name):
                to_clone[year].append(row)
                total += 1

    if total == 0:
        print("No new PoC to download found, have a good day :)")
        sys.exit(0)
    else:
        RUN_EVENT = threading.Event()
        with alive_bar(total) as bar:
            for year in to_clone:
                thread = threading.Thread(target=clone_pocs_from_year, args=(to_clone[year],bar))
                THREADS.append(thread)
                thread.start()

            for thread in THREADS:
                thread.join()

def init():
    """
    initialize project by cloning it and downloading all PoC
    """

    # init sqlite database
    init_db()

    # remove folder if it exists
    if os.path.exists(BASE_PATH+FOLDER_NAME):
        shutil.rmtree(BASE_PATH+FOLDER_NAME)

    folder_name = BASE_PATH+FOLDER_NAME
    folder_name = folder_name.replace(' ','\\ ')
    os.system(f"git clone {GIT_URL} {folder_name}")
    data = parse_folders()

    # save data to database
    save_data(data)

    # download pocs
    update_pocs(from_init=True)

def main():
    """
    main function
    """

    global BASE_PATH

    show_help= True

    parser = argparse.ArgumentParser(description="Project management utility")

    parser.add_argument('-b', dest="build", action='store_true', help='Build the project')
    parser.add_argument('-u', dest="update", action='store_true', help='Update PoCbase')
    parser.add_argument('-s', dest="search", action='store_true', help='Search by CVE ID')
    parser.add_argument('-p', nargs="?", metavar="path", const="path", dest="path", help="Path to the directory where you want to store PoCs")
    args = parser.parse_args()

    if args.path:
        if not os.path.exists(args.path):
            print(f"Error, given path {args.path} doesn't exists")
            sys.exit(1)
        BASE_PATH = args.path
        if not BASE_PATH.endswith('/'):
            BASE_PATH += '/'

    if args.build:
        show_help=False
        init()

    if args.update:
        show_help=False
        update_pocs()

    if show_help:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Terminating all threads, please wait...")
        if len(THREADS) > 0 and RUN_EVENT != None:
            RUN_EVENT.set()
            for thread in THREADS:
                thread.join()
        sys.exit(1)
