# pip install pandas openpyxl

import pandas as pd
import yaml

files = ["a.txt", "b.py", "c.go", "d.yaml", "e.txt", "f.c", "g.cpp"]

def get_data(df):
    return df.to_dict(orient='records')

def has_mode(value, mode):
    return not pd.isna(value) and int(value) == mode

def has_read(value):
    # A digit of 4, 5, 6, or 7 means the read bit is set.
    if pd.isna(value):
        return False

    mode = f"{int(value):03d}"
    for digit in mode:
        if int(digit) & 4:
            return True
    return False

def users_with_777_for_all_files(data):
    results = []
    for user in data:
        for file in files:
            if not has_mode(user[file], 777):
                break
        else:
            results.append(user['USERID'])
    return results

def users_with_777_for_at_least_one_file(data):
    results = []
    for user in data:
        for file in files:
            if has_mode(user[file], 777):
                results.append(user['USERID'])
                break
    return results

def users_with_444_for_all_files(data):
    results = []
    for user in data:
        for file in files:
            if not has_mode(user[file], 444):
                break
        else:
            results.append(user['USERID'])
    return results

def users_with_444_for_at_least_one_file(data):
    results = []
    for user in data:
        for file in files:
            if has_mode(user[file], 444):
                results.append(user['USERID'])
                break
    return results

def users_with_read_for_at_least_one_file(data):
    results = []
    for user in data:
        for file in files:
            if has_read(user[file]):
                results.append(user['USERID'])
                break
    return results

def users_with_no_permissions(data):
    results = []
    for user in data:
        for file in files:
            if not pd.isna(user[file]):
                break
        else:
            results.append(user['USERID'])
    return results

def hashmap_results(data):
    hashmap = {}
    for user in data:
        permissions = {}
        for file in files:
            if not pd.isna(user[file]):
                permissions[file] = int(user[file])
        if len(permissions) >= 2:
            hashmap[user['USERID']] = permissions
    return hashmap

def export_hashmap_to_yaml(hashmap):
    with open('E4/hashmap.yaml', 'w') as file:
        yaml.dump(hashmap, file)

def print_results(data):
    print("Number of users with 777 for all files: ", len(users_with_777_for_all_files(data)))
    print("Number of users with 777 for at least one file: ", len(users_with_777_for_at_least_one_file(data)))
    print("Number of users with 444 for all files: ", len(users_with_444_for_all_files(data)))
    print("Number of users with 444 for at least one file: ", len(users_with_444_for_at_least_one_file(data)))
    print("Number of users with read for at least one file: ", len(users_with_read_for_at_least_one_file(data)))
    print("Number of users with no permissions: ", len(users_with_no_permissions(data)))

if __name__ == "__main__":
    # Read the Excel file
    df = pd.read_excel('E4/data.xlsx')

    data = get_data(df)
    print_results(data)

    hashmap = hashmap_results(data)
    export_hashmap_to_yaml(hashmap)

    print("Hashmap exported to hashmap.yaml")